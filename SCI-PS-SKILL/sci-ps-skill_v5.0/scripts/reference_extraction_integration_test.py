from pathlib import Path
import argparse
import json
import subprocess
import sys
import tempfile
from PIL import Image, ImageDraw


HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mcp-python", required=True)
    parser.add_argument("--server", required=True)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="reference_extraction_") as temp:
        root = Path(temp) / "project"
        for folder in ("04_photoshop/manifests", "04_photoshop/qa", "05_output/psd", "05_output/review", "05_output/transparent_elements", "06_logs", ".visual_recon"):
            (root / folder).mkdir(parents=True, exist_ok=True)
        reference = root / "reference.png"
        component = root / "component.png"
        ref = Image.new("RGBA", (120, 80), (20, 30, 40, 255))
        ImageDraw.Draw(ref).polygon([(10, 10), (50, 30), (10, 50)], fill=(240, 80, 40, 255))
        ref.save(reference)
        comp = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
        ImageDraw.Draw(comp).ellipse((2, 2, 21, 21), fill=(50, 180, 240, 255))
        comp.save(component)
        manifest = {
            "canvas": {"width": 120, "height": 80, "resolution": 72},
            "reference_overlay": {"source_file": str(reference)},
            "layers": [
                {"layer_id": "REF_NORMAL", "layer_type": "reference", "group": "99_REFERENCE_OVERLAY", "name": "REF_NORMAL_35", "verification_required": True},
                {"layer_id": "REF_DIFFERENCE", "layer_type": "reference", "group": "99_REFERENCE_OVERLAY", "name": "REF_DIFFERENCE", "verification_required": True},
                {"layer_id": "e1", "layer_type": "reference_extraction", "group": "04_REFERENCE_EXTRACTIONS", "name": "EXTRACT_e1_triangle", "placement_expected_bounds": [10, 10, 50, 50], "extraction_spec": {"method": "PEN_PATH_POLYGON", "path_points": [[10, 10], [50, 30], [10, 50]], "edge_treatment": {"feather_px": 0, "contract_px": 0, "defringe_px": 0}, "fallback_route": "PHOTOSHOP_NATIVE", "eligibility": {}}, "source_provenance": {"mode": "REFERENCE_EXTRACTION"}, "verification_required": True},
                {"layer_id": "c1", "layer_type": "component", "group": "05_COMPONENTS_MAIN", "name": "COMP_c1_circle", "source_file": str(component), "tool_target_layer_bounds": [70, 20, 94, 44], "placement_expected_bounds": [72, 22, 92, 42], "transform_plan": {"rotation": 0, "skew_x": 0, "skew_y": 0, "perspective_x": 0, "perspective_y": 0}, "mask_plan": {"enabled": False}, "source_provenance": {"mode": "IMAGE2_RECONSTRUCTION"}, "verification_required": True},
            ],
        }
        (root / "04_photoshop/manifests/build_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        (root / "04_photoshop/qa/final_qa_validation.json").write_text(json.dumps({"final_qa_validated": True}), encoding="utf-8")
        (root / ".visual_recon/project_state.json").write_text(json.dumps({"state": "TRANSPARENT_ASSET_EXPORT", "state_status": "PENDING", "next_action": "EXPORT_AND_VALIDATE_TRANSPARENT_ASSETS", "final_visual_match": True, "final_user_directed_result": False, "transparent_asset_library_validated": False}), encoding="utf-8")
        subprocess.run([sys.executable, str(HERE / "generate_mcp_action_queue.py"), str(root)], check=True)
        subprocess.run([args.mcp_python, str(HERE / "execute_mcp_action_queue.py"), str(root), "--python", args.mcp_python, "--server", args.server], check=True)
        subprocess.run([sys.executable, str(HERE / "generate_transparent_asset_export_queue.py"), str(root)], check=True)
        export_queue = root / "04_photoshop/manifests/transparent_asset_export_queue.json"
        subprocess.run([args.mcp_python, str(HERE / "execute_mcp_action_queue.py"), str(root), "--python", args.mcp_python, "--server", args.server, "--queue-file", str(export_queue)], check=True)
        subprocess.run([sys.executable, str(HERE / "validate_transparent_asset_library.py"), str(root)], check=True)
        result = json.loads((root / "05_output/transparent_elements/transparent_elements_manifest.json").read_text(encoding="utf-8"))
        if not result.get("validated") or result.get("validated_count") != 2:
            raise RuntimeError("reference extraction transparent library integration failed")
        backend = str(Path(args.server).parent)
        subprocess.run([args.mcp_python, "-c", f"import sys;sys.path.insert(0,r'{backend}');import photoshop_com as p;p.close_document(False)"], check=True)
    print("REFERENCE_EXTRACTION_INTEGRATION=PASS")


if __name__ == "__main__":
    main()
