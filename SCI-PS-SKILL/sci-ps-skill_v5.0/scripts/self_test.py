from pathlib import Path
import json
import subprocess
import sys
import tempfile
import zipfile
import hashlib
from PIL import Image


HERE=Path(__file__).resolve().parent


def run(name,*args,expected=0):
    result=subprocess.run([sys.executable,str(HERE/name),*map(str,args)],capture_output=True,text=True)
    if result.returncode!=expected:
        raise RuntimeError(f"{name} exit={result.returncode}, expected={expected}\n{result.stdout}\n{result.stderr}")


def main():
    with tempfile.TemporaryDirectory(prefix="visual_recon_selftest_") as temp:
        root=Path(temp)/"project"
        run("init_project.py",root,"--name","selftest")
        ref=root/"00_reference"/"reference_master.png"; Image.new("RGBA",(100,100),(20,30,40,255)).save(ref)
        run("create_project_manifest.py",root)
        source=Path(temp)/"handoff"; (source/"components").mkdir(parents=True)
        component=Image.new("RGBA",(20,30),(0,0,0,0))
        for x in range(2,18):
            for y in range(3,27): component.putpixel((x,y),(200,100,50,255))
        component.save(source/"components"/"c1.png")
        manifest={"image_type":"poster","content_semantic_lock":True,"user_semantic_confirmation":True,"semantic_confirmation_evidence":{"user_response":"确认语义清单正确，继续拆分","confirmed_after_analysis":True},"components":[{"component_id":"c1","name":"subject","file_name":"c1.png","batch":1,"status":"APPROVED","photoshop_target_group":"05_COMPONENTS_MAIN","canvas_mode":"ASSET_CROP","target_bbox":[10,20,42,68],"transparent":True,"alpha_verified":True,"allow_scale":True,"allow_warp":False,"hidden_region_completed":True,"reconstruction_confidence":1,"source_provenance":{"mode":"IMAGE2_RECONSTRUCTION","exact_source_available":False,"fallback_reason":"self test"}}],"photoshop_reference_extractions":[],"photoshop_native_elements":[{"id":"n1","type":"RECTANGLE","name":"NATIVE_RECT","photoshop_target_group":"07_PATHS_ARROWS","build_spec":{"bbox":[1,1,9,9],"opacity":100,"blend_mode":"NORMAL","parameters":{"fill_color":"#ffffff","stroke_color":"#ffffff","stroke_width":0,"corner_radius":0}}}]}
        manifest["photoshop_reference_extractions"]=[{"id":"e1","name":"clear-arrow","photoshop_target_group":"04_REFERENCE_EXTRACTIONS","status":"APPROVED","target_bbox":[50,10,80,30],"extraction_method":"PEN_PATH_POLYGON","path_points":[[50,10],[80,20],[50,30]],"edge_treatment":{"feather_px":0.5,"contract_px":0,"defringe_px":1},"eligibility":{"complete_contour_visible":True,"materially_unoccluded":True,"sufficient_resolution":True,"background_separable":True,"no_neighbor_contamination":True,"evidence":"self-test clear contour"},"fallback_route":"PHOTOSHOP_NATIVE","source_provenance":{"mode":"REFERENCE_EXTRACTION","exact_source_available":True,"source_file":"reference_master.png","source_sha256":hashlib.sha256(ref.read_bytes()).hexdigest()}}]
        (source/"component_manifest.json").write_text(json.dumps(manifest),encoding="utf-8")
        batch={"all_components_complete":True,"components":[{"component_id":"c1","status":"APPROVED"}],"batches":[{"batch_id":1,"status":"COMPLETED"}]}
        (source/"COMPONENT_BATCH_STATE.json").write_text(json.dumps(batch),encoding="utf-8")
        (source/"COMPONENT_QA_REPORT.md").write_text("component c1 APPROVED; alpha verified",encoding="utf-8")
        (source/"CODEX_COMPONENT_HANDOFF.md").write_text("Photoshop reads component_manifest.json and target_bbox.",encoding="utf-8")
        (source/"PHOTOSHOP_RECONSTRUCTION_MASTER_PROMPT_ZH.md").write_text("图层顺序：自底向上。逐层对比参考图，检查遮挡、蒙版、阴影、光效、虚化与整体调色，完成最终验收。",encoding="utf-8")
        inbox=root/"02_component_handoff"/"INBOX"/"COMPONENT_HANDOFF.zip"
        with zipfile.ZipFile(inbox,"w") as archive:
            for path in source.rglob("*"):
                if path.is_file(): archive.write(path,path.relative_to(source))
        run("validate_component_handoff.py",root)
        run("generate_build_manifest.py",root)
        run("generate_mcp_action_queue.py",root)
        build=json.loads((root/"04_photoshop/manifests/build_manifest.json").read_text(encoding="utf-8"))
        layer=next(x for x in build["layers"] if x.get("source_component_id")=="c1")
        if layer["placement_expected_bounds"]!=[10,20,42,68] or layer["tool_target_layer_bounds"]!=[6,14,46,74]:
            raise RuntimeError(f"transparent-padding transform mismatch: {layer}")
        extraction=next(x for x in build["layers"] if x.get("layer_type")=="reference_extraction")
        if extraction["layer_id"]!="e1": raise RuntimeError("reference extraction missing from build manifest")
        queue=json.loads((root/"04_photoshop/manifests/mcp_action_queue.json").read_text(encoding="utf-8"))
        extract_seq=next(x["sequence"] for x in queue["actions"] if x.get("expected_name")=="EXTRACT_e1_clear-arrow")
        component_seq=next(x["sequence"] for x in queue["actions"] if x.get("expected_name")=="COMP_c1_subject")
        if extract_seq>=component_seq: raise RuntimeError("reference extraction must run before component placement")
        state={"layers":[{"name":"99_REFERENCE_OVERLAY","children":[{"name":"REF_NORMAL_35","visibility":False},{"name":"REF_DIFFERENCE","visibility":False}]},{"name":"04_REFERENCE_EXTRACTIONS","children":[{"name":"EXTRACT_e1_clear-arrow","visibility":True,"bounds":{"left":50,"top":10,"right":80,"bottom":30}}]},{"name":"05_COMPONENTS_MAIN","children":[{"name":"COMP_c1_subject","visibility":True,"bounds":{"left":6,"top":14,"right":46,"bottom":74}}]},{"name":"07_PATHS_ARROWS","children":[{"name":"NATIVE_RECT","visibility":True,"bounds":{"left":1,"top":1,"right":9,"bottom":9}}]}]}
        state_path=root/"04_photoshop/qa/state.json"; state_path.parent.mkdir(parents=True,exist_ok=True); state_path.write_text(json.dumps(state),encoding="utf-8")
        run("verify_photoshop_build_state.py",root,state_path,"--final")
        rendered=root/"04_photoshop/qa/rendered.png"; Image.open(ref).save(rendered)
        report={"normal_overlay_checked":True,"difference_checked":True,"target_size_checked":True,"zoom_100_checked":True,"zoom_200_400_checked":True,"reference_overlay_hidden":True,"pixel_evidence_sha256":"","mismatches":[],"final_visual_match":True,"final_user_directed_result":False,"user_directed_approval_quote":"","approved_deviation_scope":"","review_summary":"Exact self-test match"}
        (root/"04_photoshop/qa/VISUAL_DIFFERENCE_REPORT.json").write_text(json.dumps(report),encoding="utf-8")
        run("compare_rendered_output.py",root,ref,rendered)
        run("validate_final_qa.py",root)
        run("generate_transparent_asset_export_queue.py",root)
        asset_queue=json.loads((root/"04_photoshop/manifests/transparent_asset_export_queue.json").read_text(encoding="utf-8"))
        asset_dir=root/"05_output/transparent_elements"
        for item in asset_queue["expected_assets"]:
            asset=Image.new("RGBA",(12,12),(0,0,0,0))
            for x in range(2,10):
                for y in range(2,10): asset.putpixel((x,y),(100,150,200,255))
            asset.save(asset_dir/item["file_name"])
        run("validate_transparent_asset_library.py",root)
        tampered=Image.open(rendered).convert("RGBA"); tampered.putpixel((0,0),(255,0,0,255)); tampered.save(rendered)
        run("validate_final_qa.py",root,expected=2)
        run("route_next_action.py",root)
        run("validate_state_consistency.py",root)
        native_root=Path(temp)/"native_only"; run("init_project.py",native_root,"--name","native-only")
        Image.new("RGBA",(80,60),(245,245,245,255)).save(native_root/"00_reference/reference_master.png"); run("create_project_manifest.py",native_root)
        native_source=Path(temp)/"native_handoff"; native_source.mkdir()
        native_manifest={"image_type":"flat_vector","content_semantic_lock":True,"user_semantic_confirmation":True,"semantic_confirmation_evidence":{"user_response":"确认全部由 Photoshop 原生制作","confirmed_after_analysis":True},"components":[],"photoshop_reference_extractions":[],"photoshop_native_elements":[{"id":"n1","type":"RECTANGLE","name":"ONLY_NATIVE","photoshop_target_group":"07_PATHS_ARROWS","build_spec":{"bbox":[5,5,50,40],"opacity":100,"blend_mode":"NORMAL","parameters":{"fill_color":"#abcdef","stroke_color":"#123456","stroke_width":1,"corner_radius":4}}}]}
        (native_source/"component_manifest.json").write_text(json.dumps(native_manifest),encoding="utf-8")
        (native_source/"COMPONENT_BATCH_STATE.json").write_text(json.dumps({"all_components_complete":True,"components":[],"batches":[]}),encoding="utf-8")
        (native_source/"COMPONENT_QA_REPORT.md").write_text("PHOTOSHOP_NATIVE elements APPROVED",encoding="utf-8")
        (native_source/"CODEX_COMPONENT_HANDOFF.md").write_text("Photoshop reads component_manifest.json and photoshop_native_elements.",encoding="utf-8")
        (native_source/"PHOTOSHOP_RECONSTRUCTION_MASTER_PROMPT_ZH.md").write_text("图层顺序：自底向上。逐层对比参考图，检查遮挡、蒙版、阴影、光效、虚化与整体调色，完成最终验收。",encoding="utf-8")
        native_inbox=native_root/"02_component_handoff/INBOX/COMPONENT_HANDOFF.zip"
        with zipfile.ZipFile(native_inbox,"w") as archive:
            for path in native_source.rglob("*"):
                if path.is_file(): archive.write(path,path.relative_to(native_source))
        run("validate_component_handoff.py",native_root); run("generate_build_manifest.py",native_root); run("generate_mcp_action_queue.py",native_root); run("route_next_action.py",native_root)
        native_qa=native_root/"04_photoshop/qa/final_qa_validation.json"; native_qa.parent.mkdir(parents=True,exist_ok=True); native_qa.write_text(json.dumps({"final_qa_validated":True}),encoding="utf-8")
        run("generate_transparent_asset_export_queue.py",native_root)
        empty_queue=json.loads((native_root/"04_photoshop/manifests/transparent_asset_export_queue.json").read_text(encoding="utf-8"))
        if empty_queue["actions"] or empty_queue["expected_assets"]: raise RuntimeError("native-only project must produce an empty transparent asset queue")
    print("SELF_TEST=PASS")


if __name__=="__main__": main()
