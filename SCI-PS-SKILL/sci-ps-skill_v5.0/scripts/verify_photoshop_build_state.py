from pathlib import Path
import argparse
import json
import hashlib


def normalize_bounds(value):
    if isinstance(value, list) and len(value) == 4:
        return [float(x) for x in value]
    if isinstance(value, dict):
        keys = ("left", "top", "right", "bottom")
        if all(key in value for key in keys):
            return [float(value[key]) for key in keys]
    return None


def close_bounds(actual, expected, tolerance):
    return actual is not None and expected is not None and all(abs(a - e) <= tolerance for a, e in zip(actual, expected))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("project_root")
    parser.add_argument("state_json", help="ps_get_state 导出的 JSON 文件")
    parser.add_argument("--tolerance", type=float, default=1.0)
    parser.add_argument("--final", action="store_true", help="最终检查时强制参考图层隐藏")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    manifest = json.loads((root / "04_photoshop" / "manifests" / "build_manifest.json").read_text(encoding="utf-8"))
    state = json.loads(Path(args.state_json).read_text(encoding="utf-8"))
    actual = {}
    duplicate_names = []

    def walk(items, parent_group=None):
        for item in items or []:
            if not isinstance(item, dict):
                continue
            name = item.get("name")
            item_group = item.get("group") or item.get("parent_group") or parent_group
            if name:
                if name in actual: duplicate_names.append(name)
                actual[name] = {"bounds": normalize_bounds(item.get("bounds")), "group": item_group, "raw": item}
            child_parent = name if item.get("children") or item.get("layers") else item_group
            walk(item.get("children") or item.get("layers"), child_parent)

    walk(state.get("layers", []))
    issues = []
    if duplicate_names:
        issues.append("Photoshop 状态存在重复图层名: "+", ".join(sorted(set(duplicate_names))))
    verified_placements = 0
    for expected in [x for x in manifest.get("layers", []) if x.get("verification_required")]:
        name = expected.get("name")
        found = actual.get(name)
        if not found:
            issues.append(f"{name}: 图层不存在")
            continue
        expected_group = expected.get("group")
        if expected_group and found.get("group") != expected_group:
            issues.append(f"{name}: 图层组错误，实际 {found.get('group')}，期望 {expected_group}")
        target_bounds = expected.get("tool_target_layer_bounds")
        if expected.get("layer_type") == "component":
            if not close_bounds(found.get("bounds"), target_bounds, args.tolerance):
                issues.append(f"{name}: bounds 未验证，实际 {found.get('bounds')}，期望 {target_bounds}，容差 {args.tolerance}px")
            else:
                verified_placements += 1
    reference_names = {"REF_NORMAL_35", "REF_DIFFERENCE"}
    reference_overlay_hidden = all(
        name in actual and actual[name]["raw"].get("visibility") is False
        for name in reference_names
    )
    if args.final and not reference_overlay_hidden:
        issues.append("最终检查要求 REF_NORMAL_35 与 REF_DIFFERENCE 均真实存在且 visibility=false")

    result = {
        "verified": not issues,
        "expected_count": len([x for x in manifest.get("layers", []) if x.get("verification_required")]),
        "actual_named_count": len(actual),
        "verified_component_placement_count": verified_placements,
        "reference_overlay_hidden": reference_overlay_hidden,
        "state_sha256": hashlib.sha256(Path(args.state_json).read_bytes()).hexdigest(),
        "tolerance_px": args.tolerance,
        "issues": issues,
    }
    output = root / "04_photoshop" / "qa" / "build_state_verification.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if issues:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
