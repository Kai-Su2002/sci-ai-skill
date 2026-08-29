from pathlib import Path
import argparse
import json
from jsonschema import Draft202012Validator


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def native_group(item_type):
    kind = str(item_type or "").upper()
    if "BACKGROUND" in kind:
        return "02_BACKGROUND"
    if kind in {"PATH", "ARROW", "DASHED_FRAME", "CIRCUIT"}:
        return "07_PATHS_ARROWS"
    if kind in {"EFFECT", "GLOW", "SHADOW", "ATMOSPHERE"}:
        return "08_EFFECTS"
    if kind == "TEXT":
        return "09_TEXT"
    return "10_FINISHING"


def find_validated_manifest(root):
    matches = list((root / "02_component_handoff" / "VALIDATED").rglob("component_manifest.json"))
    if len(matches) != 1:
        raise SystemExit(f"需要且只能有一个已验证 component_manifest.json，当前找到 {len(matches)} 个。")
    return matches[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("project_root")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    project = load(root / "01_spec" / "project_manifest.json")
    manifest_path = find_validated_manifest(root)
    manifest = load(manifest_path)
    canvas = project.get("canvas") or project.get("output_canvas")
    if not canvas:
        raise SystemExit("project_manifest.json 缺少 canvas/output_canvas。")
    references = [p for p in (root / "00_reference").glob("reference_master.*") if p.is_file()]
    if len(references) != 1:
        raise SystemExit(f"00_reference 中需要且只能有一个 reference_master.*，当前 {len(references)} 个。")

    layers = [
        {"layer_id": "REF_NORMAL", "layer_type": "reference", "group": "99_REFERENCE_OVERLAY", "name": "REF_NORMAL_35", "verification_required": True},
        {"layer_id": "REF_DIFFERENCE", "layer_type": "reference", "group": "99_REFERENCE_OVERLAY", "name": "REF_DIFFERENCE", "verification_required": True},
    ]

    for item in manifest.get("photoshop_reference_extractions", []):
        layers.append({
            "layer_id": item["id"],
            "layer_type": "reference_extraction",
            "group": item.get("photoshop_target_group") or "04_REFERENCE_EXTRACTIONS",
            "name": f"EXTRACT_{item['id']}_{item.get('name', '')}",
            "placement_expected_bounds": item["target_bbox"],
            "extraction_spec": {
                "method": item["extraction_method"],
                "path_points": item["path_points"],
                "edge_treatment": item["edge_treatment"],
                "fallback_route": item["fallback_route"],
                "eligibility": item["eligibility"],
            },
            "source_provenance": item["source_provenance"],
            "verification_required": True,
        })

    for item in manifest.get("photoshop_native_elements", []):
        item_id = item.get("id") or item.get("element_id")
        if not item_id:
            raise SystemExit("photoshop_native_elements 中存在缺少 id 的项目。")
        layers.append({
            "layer_id": item_id,
            "layer_type": "photoshop_native",
            "native_type": str(item.get("type", "")).upper(),
            "group": item.get("photoshop_target_group") or native_group(item.get("type")),
            "name": item.get("name") or item_id,
            "description": item.get("description", ""),
            "build_spec": item.get("build_spec"),
            "verification_required": True,
        })

    for component in manifest.get("components", []):
        if component.get("status") != "APPROVED":
            continue
        component_id = component["component_id"]
        source_content_bbox = component.get("source_content_bbox")
        target_bbox = component.get("target_bbox")
        if source_content_bbox is None or target_bbox is None:
            raise SystemExit(f"{component_id} 缺少 source_content_bbox/target_bbox，禁止自动居中猜测。")
        source_matches = list(manifest_path.parent.rglob(component.get("file_name", "")))
        if len(source_matches) != 1:
            raise SystemExit(f"{component_id}: 组件文件应有且只有一个，当前 {len(source_matches)} 个。")
        canvas_mode = component.get("canvas_mode")
        if canvas_mode != "ASSET_CROP":
            raise SystemExit(f"{component_id}: canvas_mode 必须为 ASSET_CROP。")
        from PIL import Image
        with Image.open(source_matches[0]) as source_image:
            pixel_width, pixel_height = source_image.size
        source_width = source_content_bbox[2] - source_content_bbox[0]
        source_height = source_content_bbox[3] - source_content_bbox[1]
        target_width = target_bbox[2] - target_bbox[0]
        target_height = target_bbox[3] - target_bbox[1]
        if component.get("allow_warp") is True:
            scale_x = target_width / source_width
            scale_y = target_height / source_height
            expected_bounds = target_bbox
            scale_mode = "FREE_TRANSFORM_TO_TARGET"
        else:
            scale_x = scale_y = min(target_width / source_width, target_height / source_height)
            placed_width = source_width * scale_x
            placed_height = source_height * scale_y
            left = target_bbox[0] + (target_width - placed_width) / 2
            top = target_bbox[1] + (target_height - placed_height) / 2
            expected_bounds = [left, top, left + placed_width, top + placed_height]
            scale_mode = "UNIFORM_FIT_TARGET_BBOX"
        translate_x = expected_bounds[0] - source_content_bbox[0] * scale_x
        translate_y = expected_bounds[1] - source_content_bbox[1] * scale_y
        tool_layer_bounds = [
            translate_x,
            translate_y,
            translate_x + pixel_width * scale_x,
            translate_y + pixel_height * scale_y,
        ]
        transform_extra=component.get("transform") or {}
        mask_plan=component.get("mask") or {"enabled":False,"feather":0,"density":100,"invert":False}
        if mask_plan.get("enabled") and mask_plan.get("file_name"):
            mask_matches=list(manifest_path.parent.rglob(mask_plan["file_name"]))
            if len(mask_matches)!=1: raise SystemExit(f"{component_id}: mask 文件应有且只有一个，当前 {len(mask_matches)} 个。")
            mask_plan=dict(mask_plan); mask_plan["source_file"]=str(mask_matches[0].resolve())
        provenance=component.get("source_provenance") or {}
        if not provenance: raise SystemExit(f"{component_id}: 缺少 source_provenance。")
        layers.append({
            "layer_id": component_id,
            "layer_type": "component",
            "group": component.get("photoshop_target_group") or "05_COMPONENTS_MAIN",
            "name": f"COMP_{component_id}_{component.get('name', '')}",
            "source_component_id": component_id,
            "source_file": str(source_matches[0].resolve()),
            "canvas_mode": canvas_mode,
            "source_content_bbox": source_content_bbox,
            "source_pixel_size": [pixel_width, pixel_height],
            "target_bbox": target_bbox,
            "transform_plan": {
                "scale_mode": scale_mode,
                "scale_x": scale_x,
                "scale_y": scale_y,
                "translate_x": translate_x,
                "translate_y": translate_y,
                "rotation": float(transform_extra.get("rotation",0)),
                "skew_x": float(transform_extra.get("skew_x",0)),
                "skew_y": float(transform_extra.get("skew_y",0)),
                "perspective_x": float(transform_extra.get("perspective_x",0)),
                "perspective_y": float(transform_extra.get("perspective_y",0)),
            },
            "placement_expected_bounds": expected_bounds,
            "tool_target_layer_bounds": tool_layer_bounds,
            "allow_scale": True,
            "allow_warp": component.get("allow_warp"),
            "import_mode": "SMART_OBJECT",
            "mask_plan": mask_plan,
            "source_provenance": provenance,
            "z_order": component.get("z_order"),
            "verification_required": True,
        })

    output = {
        "canvas": canvas,
        "font_assets": manifest.get("font_assets", []),
        "reference_overlay": {
            "source_file": str(references[0].resolve()),
            "group": "99_REFERENCE_OVERLAY",
            "normal_opacity": 35,
            "difference_copy": True,
            "must_hide_for_final_qa": True,
        },
        "layers": layers,
        "rules": {
            "forbid_reference_tiles": True,
            "require_verified_increment_each_step": True,
            "max_no_progress_cycles": 2,
        },
    }
    schema=load(Path(__file__).resolve().parents[1]/"schemas"/"build_manifest.schema.json")
    errors=list(Draft202012Validator(schema).iter_errors(output))
    if errors: raise SystemExit("build_manifest schema 失败: "+"; ".join(error.message for error in errors))
    path = root / "04_photoshop" / "manifests" / "build_manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(path)


if __name__ == "__main__":
    main()
