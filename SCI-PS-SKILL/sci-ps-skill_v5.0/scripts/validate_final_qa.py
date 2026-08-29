from pathlib import Path
import argparse
import json
import hashlib
from jsonschema import Draft202012Validator


REQUIRED_TRUE = [
    "normal_overlay_checked",
    "difference_checked",
    "target_size_checked",
    "zoom_100_checked",
    "zoom_200_400_checked",
    "reference_overlay_hidden",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("project_root")
    parser.add_argument("--mode", choices=("fidelity","adaptation"), default="fidelity")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    report_path = root / "04_photoshop" / "qa" / "VISUAL_DIFFERENCE_REPORT.json"
    build_check_path = root / "04_photoshop" / "qa" / "build_state_verification.json"
    pixel_evidence_path = root / "04_photoshop" / "qa" / "pixel_comparison_evidence.json"
    issues = []
    if not report_path.exists():
        raise SystemExit(f"缺少 {report_path}")
    if not build_check_path.exists():
        raise SystemExit(f"缺少 {build_check_path}")
    if not pixel_evidence_path.exists():
        raise SystemExit(f"缺少 {pixel_evidence_path}")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    build_check = json.loads(build_check_path.read_text(encoding="utf-8"))
    pixel_evidence = json.loads(pixel_evidence_path.read_text(encoding="utf-8"))
    schema_path=Path(__file__).resolve().parents[1]/"schemas"/"visual_difference_report.schema.json"
    schema=json.loads(schema_path.read_text(encoding="utf-8"))
    for error in Draft202012Validator(schema).iter_errors(report):
        issues.append("VISUAL_DIFFERENCE_REPORT schema: "+"/".join(str(x) for x in error.path)+": "+error.message)
    if build_check.get("verified") is not True:
        issues.append("Photoshop build state 尚未验证通过")
    if build_check.get("reference_overlay_hidden") is not True:
        issues.append("Photoshop 状态没有证明参考图层已隐藏")
    if args.mode == "fidelity" and pixel_evidence.get("pixel_comparison_passed") is not True:
        issues.append("真实导出图像素比较未通过")
    thresholds=pixel_evidence.get("thresholds",{})
    if any(float(thresholds.get(key,0) or 0)>0 for key in ("mae","mismatch_pixel_ratio")):
        if report.get("tolerance_approved_by_user") is not True or not str(report.get("tolerance_approval_quote","")).strip():
            issues.append("使用了非零视觉容差，但缺少用户明确批准记录")
    for label in ("reference", "rendered"):
        path_value=pixel_evidence.get(f"{label}_path")
        expected_hash=pixel_evidence.get(f"{label}_sha256")
        path=Path(path_value) if path_value else None
        if not path or not path.is_file():
            issues.append(f"像素证据中的 {label}_path 不存在")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != expected_hash:
            issues.append(f"像素证据中的 {label} 文件哈希已变化，必须重新比较")
    for key in REQUIRED_TRUE:
        if report.get(key) is not True:
            issues.append(f"VISUAL_DIFFERENCE_REPORT: {key} 不是 true")
    if args.mode == "fidelity":
        if report.get("final_visual_match") is not True or report.get("final_user_directed_result") is not False:
            issues.append("fidelity 模式必须 final_visual_match=true 且 final_user_directed_result=false")
    else:
        if report.get("final_visual_match") is not False or report.get("final_user_directed_result") is not True:
            issues.append("adaptation 模式必须 final_visual_match=false 且 final_user_directed_result=true")
        if not str(report.get("user_directed_approval_quote","")).strip() or not str(report.get("approved_deviation_scope","")).strip():
            issues.append("adaptation 模式缺少用户批准原文或允许偏离范围")
    if not str(report.get("review_summary", "")).strip():
        issues.append("VISUAL_DIFFERENCE_REPORT: review_summary 为空")
    for mismatch in report.get("mismatches", []):
        if mismatch.get("status") != "RESOLVED":
            issues.append(f"差异 {mismatch.get('id', 'UNKNOWN')} 尚未解决")
        if not mismatch.get("description") or not mismatch.get("correction"):
            issues.append(f"差异 {mismatch.get('id', 'UNKNOWN')} 缺少描述或修正记录")
    if report.get("pixel_evidence_sha256") != hashlib.sha256(pixel_evidence_path.read_bytes()).hexdigest():
        issues.append("VISUAL_DIFFERENCE_REPORT 未绑定当前 pixel_comparison_evidence.json 哈希")
    result = {"final_qa_validated": not issues, "issues": issues, "report": str(report_path), "pixel_evidence": str(pixel_evidence_path)}
    output = root / "04_photoshop" / "qa" / "final_qa_validation.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    state_path = root / ".visual_recon" / "project_state.json"
    if state_path.exists():
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["final_visual_match"] = not issues and args.mode == "fidelity"
        state["final_user_directed_result"] = not issues and args.mode == "adaptation"
        if args.mode == "adaptation" and not issues:
            state["user_directed_approval_quote"] = report.get("user_directed_approval_quote")
        state["transparent_asset_library_validated"] = False
        state["state"] = "TRANSPARENT_ASSET_EXPORT" if not issues else "BUILD_QA"
        state["state_status"] = "PENDING" if not issues else "BLOCKED"
        state["last_completed_state"] = "BUILD_QA" if not issues else state.get("last_completed_state")
        state["next_action"] = "EXPORT_AND_VALIDATE_TRANSPARENT_ASSETS" if not issues else "RESOLVE_VISUAL_DIFFERENCES"
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if issues:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
