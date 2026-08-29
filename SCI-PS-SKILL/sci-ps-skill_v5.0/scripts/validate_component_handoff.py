from pathlib import Path
import argparse
import json
import shutil
import zipfile
import hashlib
from jsonschema import Draft202012Validator


REQUIRED_HANDOFF_FILES = {
    "component_manifest.json",
    "COMPONENT_BATCH_STATE.json",
    "COMPONENT_QA_REPORT.md",
    "CODEX_COMPONENT_HANDOFF.md",
    "PHOTOSHOP_RECONSTRUCTION_MASTER_PROMPT_ZH.md",
}
FORBIDDEN_COMPONENT_STATES = {"PENDING", "GENERATING", "REVISION_REQUIRED", "TEMPORARY", "QA_PASSED", "APPROVED_COMPONENT"}
MAX_FILES = 500
MAX_UNCOMPRESSED_BYTES = 2 * 1024 * 1024 * 1024
MAX_SINGLE_FILE_BYTES = 512 * 1024 * 1024


def safe_extract(archive, destination):
    destination = destination.resolve()
    members = archive.infolist()
    if len(members) > MAX_FILES:
        raise RuntimeError(f"ZIP 文件数超过限制: {len(members)} > {MAX_FILES}")
    if sum(x.file_size for x in members) > MAX_UNCOMPRESSED_BYTES:
        raise RuntimeError("ZIP 解压后总大小超过 2 GiB 限制")
    for member in members:
        if member.file_size > MAX_SINGLE_FILE_BYTES:
            raise RuntimeError(f"ZIP 单文件超过 512 MiB: {member.filename}")
        target = (destination / member.filename).resolve()
        if destination not in target.parents and target != destination:
            raise RuntimeError("ZIP 路径穿越被拒绝")
    archive.extractall(destination)


def exactly_one(root, filename, issues):
    matches = list(root.rglob(filename))
    if len(matches) != 1:
        issues.append(f"{filename}: 应有且只有一个，当前 {len(matches)} 个")
        return None
    return matches[0]


def as_bbox(value):
    return isinstance(value, list) and len(value) == 4 and all(isinstance(x, (int, float)) for x in value) and value[2] > value[0] and value[3] > value[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("project_root")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    inbox = root / "02_component_handoff" / "INBOX" / "COMPONENT_HANDOFF.zip"
    validated = root / "02_component_handoff" / "VALIDATED"
    if not inbox.exists():
        raise SystemExit(f"未找到 {inbox}")
    package_sha256 = hashlib.sha256(inbox.read_bytes()).hexdigest()
    state_path = root / ".visual_recon" / "project_state.json"
    if state_path.exists():
        old_state = json.loads(state_path.read_text(encoding="utf-8"))
        if (old_state.get("component_handoff_validated") is True
                and old_state.get("component_handoff_sha256") == package_sha256
                and validated.exists()):
            print(json.dumps({"validated": True, "idempotent_resume": True, "package_sha256": package_sha256,
                              "next_action": old_state.get("next_action")}, ensure_ascii=False, indent=2))
            return
    try:
        from PIL import Image
    except Exception as exc:
        raise SystemExit(f"缺少 Pillow，无法执行强制 PNG/Alpha 验证: {exc}")

    if validated.exists():
        shutil.rmtree(validated)
    validated.mkdir(parents=True)
    with zipfile.ZipFile(inbox) as archive:
        safe_extract(archive, validated)

    issues = []
    located = {name: exactly_one(validated, name, issues) for name in REQUIRED_HANDOFF_FILES}
    for name, path in located.items():
        if path and path.stat().st_size == 0:
            issues.append(f"{name}: 文件为空")
    qa_path = located.get("COMPONENT_QA_REPORT.md")
    handoff_path = located.get("CODEX_COMPONENT_HANDOFF.md")
    master_prompt_path = located.get("PHOTOSHOP_RECONSTRUCTION_MASTER_PROMPT_ZH.md")
    qa_text=qa_path.read_text(encoding="utf-8",errors="ignore") if qa_path else ""
    handoff_text=handoff_path.read_text(encoding="utf-8",errors="ignore") if handoff_path else ""
    master_prompt_text=master_prompt_path.read_text(encoding="utf-8",errors="ignore") if master_prompt_path else ""
    manifest_path = located["component_manifest.json"]
    state_path = located["COMPONENT_BATCH_STATE.json"]
    if not manifest_path or not state_path:
        result = {"validated": False, "issues": issues}
        log_path = root / "06_logs" / "component_handoff_validation.json"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        raise SystemExit(2)

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        batch_state = json.loads(state_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"Manifest 或批次状态 JSON 无法解析: {exc}")
    schema_path=Path(__file__).resolve().parents[1]/"schemas"/"component_manifest.schema.json"
    schema=json.loads(schema_path.read_text(encoding="utf-8"))
    for error in Draft202012Validator(schema).iter_errors(manifest):
        issues.append("component_manifest schema: "+"/".join(str(x) for x in error.path)+": "+error.message)

    if batch_state.get("all_components_complete") is not True and batch_state.get("ALL_COMPONENTS_COMPLETE") is not True:
        issues.append("COMPONENT_BATCH_STATE.json: ALL_COMPONENTS_COMPLETE 不是 TRUE")
    state_components = batch_state.get("components", [])
    bad_states = [x.get("component_id") for x in state_components if str(x.get("status", "")).upper() in FORBIDDEN_COMPONENT_STATES]
    if bad_states:
        issues.append("批次状态仍包含未完成/非最终组件: " + ", ".join(str(x) for x in bad_states))
    for batch in batch_state.get("batches", []):
        if str(batch.get("status", "")).upper() != "COMPLETED":
            issues.append(f"{batch.get('batch_id', 'UNKNOWN_BATCH')}: status 不是 COMPLETED")

    components = manifest.get("components")
    if not isinstance(components, list):
        issues.append("component_manifest.json: components 必须是数组")
        components = []
    native = manifest.get("photoshop_native_elements")
    if not isinstance(native, list):
        issues.append("component_manifest.json: 缺少 photoshop_native_elements 数组")
        native = []
    extractions = manifest.get("photoshop_reference_extractions")
    if not isinstance(extractions, list):
        issues.append("component_manifest.json: 缺少 photoshop_reference_extractions 数组")
        extractions = []
    if not components and not native and not extractions:
        issues.append("component_manifest.json: components、photoshop_reference_extractions 与 photoshop_native_elements 不得同时为空")
    qa_markers=("APPROVED", "alpha", "component") if components else (("REFERENCE_EXTRACTION", "APPROVED") if extractions else ("PHOTOSHOP_NATIVE", "APPROVED"))
    for marker in qa_markers:
        if marker.lower() not in qa_text.lower(): issues.append(f"COMPONENT_QA_REPORT.md: 缺少实质字段 {marker}")
    handoff_markers=("component_manifest.json", "target_bbox", "Photoshop") if (components or extractions) else ("component_manifest.json", "photoshop_native_elements", "Photoshop")
    for marker in handoff_markers:
        if marker.lower() not in handoff_text.lower(): issues.append(f"CODEX_COMPONENT_HANDOFF.md: 缺少交接字段 {marker}")
    master_prompt_markers=("图层顺序", "逐层", "遮挡", "蒙版", "阴影", "光效", "虚化", "整体调色", "最终验收")
    for marker in master_prompt_markers:
        if marker.lower() not in master_prompt_text.lower(): issues.append(f"PHOTOSHOP_RECONSTRUCTION_MASTER_PROMPT_ZH.md: 缺少实质章节 {marker}")
    font_assets=manifest.get("font_assets",[])
    if not isinstance(font_assets,list):
        issues.append("component_manifest.json: font_assets 必须是数组")
        font_assets=[]
    if not str(manifest.get("image_type", "")).strip():
        issues.append("component_manifest.json: 缺少 image_type")
    if manifest.get("content_semantic_lock") is not True:
        issues.append("component_manifest.json: content_semantic_lock 不是 true")
    if manifest.get("user_semantic_confirmation") is not True:
        issues.append("component_manifest.json: user_semantic_confirmation 不是 true")
    confirmation=manifest.get("semantic_confirmation_evidence")
    if not isinstance(confirmation,dict) or not str(confirmation.get("user_response","")).strip() or confirmation.get("confirmed_after_analysis") is not True:
        issues.append("component_manifest.json: 缺少语义分析后用户明确确认的可审计记录")

    ids = []
    filenames = []
    extraction_ids = []
    reference_files = [p for p in (root / "00_reference").glob("reference_master.*") if p.is_file()]
    reference_sha256 = hashlib.sha256(reference_files[0].read_bytes()).hexdigest() if len(reference_files) == 1 else None
    reference_size = None
    if len(reference_files) == 1:
        try:
            with Image.open(reference_files[0]) as reference_image:
                reference_size = reference_image.size
        except Exception as exc:
            issues.append(f"reference_master 无法解码: {exc}")
    for item in extractions:
        extraction_id = item.get("id")
        extraction_ids.append(extraction_id)
        if not extraction_id:
            issues.append("photoshop_reference_extractions: 存在缺少 id 的项目")
        if item.get("status") != "APPROVED":
            issues.append(f"{extraction_id}: reference extraction 状态必须为 APPROVED")
        if not as_bbox(item.get("target_bbox")):
            issues.append(f"{extraction_id}: target_bbox 缺失或格式非法")
        points = item.get("path_points")
        if not isinstance(points, list) or len(points) < 3:
            issues.append(f"{extraction_id}: path_points 必须包含至少 3 个闭合路径点")
        elif not all(isinstance(p, list) and len(p) == 2 and all(isinstance(v, (int, float)) for v in p) for p in points):
            issues.append(f"{extraction_id}: path_points 坐标格式非法")
        else:
            xs, ys = [p[0] for p in points], [p[1] for p in points]
            path_bbox = [min(xs), min(ys), max(xs), max(ys)]
            if path_bbox[2] <= path_bbox[0] or path_bbox[3] <= path_bbox[1]:
                issues.append(f"{extraction_id}: path_points 形成的区域面积为零")
            if reference_size and (min(xs) < 0 or min(ys) < 0 or max(xs) > reference_size[0] or max(ys) > reference_size[1]):
                issues.append(f"{extraction_id}: path_points 超出参考图画布")
            target = item.get("target_bbox")
            if as_bbox(target) and any(abs(path_bbox[i] - target[i]) > 2 for i in range(4)):
                issues.append(f"{extraction_id}: path_points 外接框与 target_bbox 偏差超过 2 px")
        eligibility = item.get("eligibility") or {}
        for key in ("complete_contour_visible", "materially_unoccluded", "sufficient_resolution", "background_separable", "no_neighbor_contamination"):
            if eligibility.get(key) is not True:
                issues.append(f"{extraction_id}: 抠取资格 {key} 未通过")
        provenance = item.get("source_provenance") or {}
        if provenance.get("mode") != "REFERENCE_EXTRACTION" or provenance.get("exact_source_available") is not True:
            issues.append(f"{extraction_id}: source_provenance 必须是 REFERENCE_EXTRACTION 精确来源")
        if reference_sha256 is None:
            issues.append(f"{extraction_id}: 项目中无法唯一确定 reference_master.*")
        elif str(provenance.get("source_sha256", "")).lower() != reference_sha256:
            issues.append(f"{extraction_id}: source_sha256 与项目 reference_master 不一致")
        if item.get("rasterized_text_or_logo") is True:
            if item.get("editable_text") is not False or not str(item.get("rasterization_user_confirmation", "")).strip():
                issues.append(f"{extraction_id}: 栅格标题/字标/Logo 抠取必须标记 editable_text=false 并保存用户确认")
    for item in native:
        if not (item.get("id") or item.get("element_id")):
            issues.append("photoshop_native_elements: 存在缺少 id/element_id 的项目")
        if not item.get("type"):
            issues.append(f"{item.get('id', 'UNKNOWN_NATIVE')}: 缺少 type")

    for component in components:
        component_id = component.get("component_id")
        filename = component.get("file_name")
        ids.append(component_id)
        filenames.append(filename)
        if not component_id:
            issues.append("组件缺少 component_id")
        if component.get("status") != "APPROVED":
            issues.append(f"{component_id}: 最终 manifest 状态必须为 APPROVED，当前 {component.get('status')}")
        if not filename or Path(filename).name != filename:
            issues.append(f"{component_id}: file_name 必须是安全的纯文件名")
            continue
        if Path(filename).suffix.lower() != ".png":
            issues.append(f"{component_id}: 正式图片组件必须是 PNG")
        if not component.get("photoshop_target_group"):
            issues.append(f"{component_id}: 缺少 photoshop_target_group")
        if component.get("canvas_mode") != "ASSET_CROP":
            issues.append(f"{component_id}: canvas_mode 必须为 ASSET_CROP")
        if not as_bbox(component.get("target_bbox")):
            issues.append(f"{component_id}: target_bbox 缺失或格式非法")
        if component.get("transparent") is not True or component.get("alpha_verified") is not True:
            issues.append(f"{component_id}: transparent/alpha_verified 必须为 true")
        if component.get("allow_scale") is not True:
            issues.append(f"{component_id}: ASSET_CROP 的 allow_scale 必须为 true")
        for boolean_key in ("allow_warp", "hidden_region_completed"):
            if not isinstance(component.get(boolean_key), bool):
                issues.append(f"{component_id}: {boolean_key} 必须是 boolean")
        if component.get("reconstruction_confidence") is None:
            issues.append(f"{component_id}: 缺少 reconstruction_confidence")
        provenance=component.get("source_provenance")
        if not isinstance(provenance,dict):
            issues.append(f"{component_id}: 缺少 source_provenance")
        elif provenance.get("mode") == "IMAGE2_RECONSTRUCTION" and not str(provenance.get("fallback_reason","")).strip():
            issues.append(f"{component_id}: Image2 重建缺少 fallback_reason")
        if component.get("rasterized_text_or_logo") is True:
            if component.get("editable_text") is not False:
                issues.append(f"{component_id}: 栅格艺术字/字标/Logo 必须标记 editable_text=false")
            if not str(component.get("literal_text","")).strip() or not str(component.get("rasterization_user_confirmation","")).strip():
                issues.append(f"{component_id}: 栅格艺术字/字标/Logo 缺少 literal_text 或用户明确确认记录")
        matches = list(validated.rglob(filename))
        if len(matches) != 1:
            issues.append(f"{component_id}: 文件 {filename} 应有且只有一个，当前 {len(matches)} 个")
            continue
        try:
            with Image.open(matches[0]) as image:
                image.load()
                if image.format != "PNG":
                    issues.append(f"{component_id}: 文件内容不是 PNG")
                if "A" not in image.getbands():
                    issues.append(f"{component_id}: PNG 无 Alpha 通道")
                else:
                    alpha = image.getchannel("A")
                    extrema = alpha.getextrema()
                    if extrema == (255, 255):
                        issues.append(f"{component_id}: Alpha 全不透明，疑似假透明")
                    if extrema == (0, 0):
                        issues.append(f"{component_id}: Alpha 全透明，没有可用主体")
                    content_bbox = alpha.getbbox()
                    if content_bbox:
                        component["source_content_bbox"] = list(content_bbox)
            if isinstance(provenance,dict) and provenance.get("exact_source_available") is True:
                actual_hash=hashlib.sha256(matches[0].read_bytes()).hexdigest()
                if provenance.get("source_sha256","" ).lower()!=actual_hash:
                    issues.append(f"{component_id}: 精确来源 SHA-256 与组件文件不一致")
        except Exception as exc:
            issues.append(f"{component_id}: PNG 无法解码: {exc}")
        mask=component.get("mask") or {}
        if mask.get("enabled") and mask.get("file_name"):
            mask_matches=list(validated.rglob(mask["file_name"]))
            if len(mask_matches)!=1:
                issues.append(f"{component_id}: mask 文件 {mask['file_name']} 应有且只有一个，当前 {len(mask_matches)} 个")
            else:
                try:
                    with Image.open(mask_matches[0]) as image:
                        image.load()
                        if image.format!='PNG': issues.append(f"{component_id}: mask 文件内容不是 PNG")
                        if 'A' not in image.getbands() or image.getchannel('A').getextrema() in ((0,0),(255,255)):
                            issues.append(f"{component_id}: mask PNG 必须用非空且非全不透明 Alpha 表达蒙版范围")
                except Exception as exc: issues.append(f"{component_id}: mask PNG 无法解码: {exc}")

    if len(ids) != len(set(ids)):
        issues.append("component_manifest.json: component_id 存在重复")
    if len(filenames) != len(set(filenames)):
        issues.append("component_manifest.json: file_name 存在重复")
    if len(extraction_ids) != len(set(extraction_ids)):
        issues.append("photoshop_reference_extractions: id 存在重复")
    if set(x for x in extraction_ids if x) & set(x for x in ids if x):
        issues.append("reference extraction id 与 component_id 不得重复")
    font_ids=[];font_names=[]
    for font in font_assets:
        fid=font.get("font_id");fn=font.get("file_name");lic=font.get("license_file")
        font_ids.append(fid);font_names.append(fn)
        if not fid or not fn or not lic: continue
        font_matches=list(validated.rglob(fn));license_matches=list(validated.rglob(lic))
        if len(font_matches)!=1: issues.append(f"字体 {fid}: {fn} 应有且只有一个，当前 {len(font_matches)} 个")
        if len(license_matches)!=1: issues.append(f"字体 {fid}: 许可证 {lic} 应有且只有一个，当前 {len(license_matches)} 个")
        if len(font_matches)==1:
            data=font_matches[0].read_bytes()
            if len(data)>50*1024*1024: issues.append(f"字体 {fid}: 文件超过 50 MiB")
            if data[:4] not in (b'OTTO',b'\x00\x01\x00\x00',b'true',b'typ1'): issues.append(f"字体 {fid}: 文件头不是受支持的 TTF/OTF")
            if hashlib.sha256(data).hexdigest().lower()!=str(font.get("sha256","")).lower(): issues.append(f"字体 {fid}: SHA-256 不匹配")
        if len(license_matches)==1 and license_matches[0].stat().st_size==0: issues.append(f"字体 {fid}: 许可证文件为空")
    if len(font_ids)!=len(set(font_ids)): issues.append("font_assets: font_id 存在重复")
    if len(font_names)!=len(set(font_names)): issues.append("font_assets: file_name 存在重复")
    if components and not state_components:
        issues.append("COMPONENT_BATCH_STATE.json: 存在图片组件时 components 必须是非空数组")
    if components and not batch_state.get("batches"):
        issues.append("COMPONENT_BATCH_STATE.json: 存在图片组件时 batches 必须是非空数组")
    state_ids = {x.get("component_id") for x in state_components if x.get("component_id")}
    manifest_ids = {x for x in ids if x}
    if state_ids != manifest_ids:
        issues.append("COMPONENT_BATCH_STATE 与 component_manifest 的组件 ID 集合不一致")

    if not issues:
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    result = {"validated": not issues, "issues": issues, "manifest": str(manifest_path), "package_sha256": package_sha256}
    log_path = root / "06_logs" / "component_handoff_validation.json"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    project_state_path = root / ".visual_recon" / "project_state.json"
    if project_state_path.exists():
        project_state = json.loads(project_state_path.read_text(encoding="utf-8"))
        project_state["component_handoff_validated"] = not issues
        project_state["component_handoff_sha256"] = package_sha256 if not issues else None
        project_state["state"] = "PHOTOSHOP_BUILD_PRECHECK" if not issues else "COMPONENT_PACKAGE_VALIDATION"
        project_state["state_status"] = "PASS" if not issues else "BLOCKED"
        project_state["last_completed_state"] = "COMPONENT_PACKAGE_VALIDATION" if not issues else project_state.get("last_completed_state")
        project_state["next_action"] = "GENERATE_BUILD_AND_ACTION_QUEUE" if not issues else "REPAIR_COMPONENT_HANDOFF"
        project_state_path.write_text(json.dumps(project_state, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(result, ensure_ascii=False, indent=2))
    if issues:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
