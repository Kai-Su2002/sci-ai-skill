from pathlib import Path
import argparse
import hashlib
import json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("project_root")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    queue_path = root / "04_photoshop/manifests/transparent_asset_export_queue.json"
    queue = json.loads(queue_path.read_text(encoding="utf-8"))
    output_dir = root / "05_output/transparent_elements"
    issues, assets = [], []
    try:
        from PIL import Image
    except Exception as exc:
        raise SystemExit(f"缺少 Pillow，无法验证透明元素: {exc}")
    expected = queue.get("expected_assets", [])
    for item in expected:
        path = output_dir / item["file_name"]
        if not path.is_file():
            issues.append(f"缺少透明元素: {item['file_name']}")
            continue
        try:
            with Image.open(path) as image:
                image.load()
                if image.format != "PNG" or "A" not in image.getbands():
                    issues.append(f"{path.name}: 不是带 Alpha 的 PNG")
                    continue
                extrema = image.getchannel("A").getextrema()
                if extrema in ((0, 0), (255, 255)):
                    issues.append(f"{path.name}: Alpha 不可用，必须同时包含透明与可见像素")
                    continue
                size = list(image.size)
        except Exception as exc:
            issues.append(f"{path.name}: PNG 无法解码: {exc}")
            continue
        assets.append({**item, "pixel_size": size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    actual_pngs = {p.name for p in output_dir.glob("*.png")}
    expected_pngs = {x["file_name"] for x in expected}
    if actual_pngs != expected_pngs:
        issues.append("transparent_elements 中 PNG 集合与导出清单不一致")
    result = {"validated": not issues, "expected_count": len(expected), "validated_count": len(assets), "issues": issues, "assets": assets}
    manifest_path = output_dir / "transparent_elements_manifest.json"
    manifest_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    state_path = root / ".visual_recon/project_state.json"
    if state_path.exists():
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["transparent_asset_library_validated"] = not issues
        state["state"] = "USER_REVIEW" if not issues else "TRANSPARENT_ASSET_EXPORT"
        state["state_status"] = "PASS" if not issues else "BLOCKED"
        state["last_completed_state"] = "TRANSPARENT_ASSET_EXPORT" if not issues else state.get("last_completed_state")
        state["next_action"] = "REQUEST_USER_REVIEW" if not issues else "EXPORT_AND_VALIDATE_TRANSPARENT_ASSETS"
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if issues:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
