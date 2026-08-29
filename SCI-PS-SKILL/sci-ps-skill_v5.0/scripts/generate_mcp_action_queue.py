from pathlib import Path
import argparse
import json
from compile_native_element import compile_native


def jsx_string(value):
    return json.dumps(str(value), ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("project_root")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    manifest_path = root / "04_photoshop" / "manifests" / "build_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    actions = []
    canvas = manifest["canvas"]
    width = canvas.get("width") or canvas[0]
    height = canvas.get("height") or canvas[1]
    resolution = canvas.get("resolution", 72) if isinstance(canvas, dict) else 72
    actions.append({"sequence": 1, "tool": "ps_create_document", "args": {"width_px": width, "height_px": height, "resolution": resolution, "name": root.name}, "verify_with": "ps_get_state"})
    sequence = 2
    reference=manifest["reference_overlay"]["source_file"]
    for name, opacity, blend in (("REF_NORMAL_35",35,"BlendMode.NORMAL"),("REF_DIFFERENCE",100,"BlendMode.DIFFERENCE")):
        actions.append({"sequence":sequence,"tool":"ps_place_image","args":{"file_path":reference},"verify_with":"ps_get_state"}); sequence+=1
        script=f"var d=app.activeDocument,l=d.activeLayer;l.name={jsx_string(name)};l.opacity={opacity};l.blendMode={blend};var g=null;for(var i=0;i<d.layerSets.length;i++){{if(d.layerSets[i].name=='99_REFERENCE_OVERLAY')g=d.layerSets[i];}}if(!g){{g=d.layerSets.add();g.name='99_REFERENCE_OVERLAY';}}if(l.parent!=g)l.move(g,ElementPlacement.INSIDE);"
        actions.append({"sequence":sequence,"tool":"ps_execute_jsx","args":{"script":script,"operation_label":f"configure {name}"},"verify_with":"ps_get_state"}); sequence+=1
    for layer in [x for x in manifest.get("layers", []) if x.get("layer_type") == "reference_extraction"]:
        spec = layer["extraction_spec"]
        points = spec["path_points"]
        edge = spec["edge_treatment"]
        point_js = ",".join(f"[{float(p[0])},{float(p[1])}]" for p in points)
        script = (
            "var d=app.activeDocument,src=null;"
            "for(var i=0;i<d.layerSets.length;i++){if(d.layerSets[i].name=='99_REFERENCE_OVERLAY'){"
            "for(var j=0;j<d.layerSets[i].artLayers.length;j++)if(d.layerSets[i].artLayers[j].name=='REF_NORMAL_35')src=d.layerSets[i].artLayers[j];}}"
            "if(!src)throw new Error('REF_NORMAL_35 missing');var oldOpacity=src.opacity;src.visible=true;src.opacity=100;d.activeLayer=src;"
            f"var pts=[{point_js}];d.selection.select(pts,SelectionType.REPLACE,{float(edge.get('feather_px',0))},true);"
            f"if({float(edge.get('contract_px',0))}>0)d.selection.contract({float(edge.get('contract_px',0))});"
            "d.selection.copy();var l=d.paste();"
            f"l.name={jsx_string(layer['name'])};"
            f"if({float(edge.get('defringe_px',0))}>0)l.applyDefringe({float(edge.get('defringe_px',0))});"
            f"var g=null;for(var k=0;k<d.layerSets.length;k++)if(d.layerSets[k].name=={jsx_string(layer['group'])})g=d.layerSets[k];"
            f"if(!g){{g=d.layerSets.add();g.name={jsx_string(layer['group'])};}}if(l.parent!=g)l.move(g,ElementPlacement.INSIDE);src.opacity=oldOpacity;d.selection.deselect();"
        )
        actions.append({"sequence":sequence,"tool":"ps_execute_jsx","args":{"script":script,"operation_label":f"extract reference element {layer['name']}"},"expected_name":layer["name"],"verify_with":"ps_get_state"}); sequence+=1
    for layer in manifest.get("layers", []):
        if layer.get("layer_type") != "component":
            continue
        bounds = layer["tool_target_layer_bounds"]
        actions.append({"sequence": sequence, "tool": "ps_place_smart_object", "args": {"file_path": layer["source_file"],"name":layer["name"]}, "expected_name": layer["name"], "verify_with": "ps_get_state"})
        sequence += 1
        plan=layer.get("transform_plan") or {}
        actions.append({"sequence": sequence, "tool": "ps_transform_layer_advanced", "args_from_previous_layer": True, "args": {"x": bounds[0], "y": bounds[1], "width": bounds[2]-bounds[0], "height": bounds[3]-bounds[1],"rotation":plan.get("rotation",0),"skew_x":plan.get("skew_x",0),"skew_y":plan.get("skew_y",0),"perspective_x":plan.get("perspective_x",0),"perspective_y":plan.get("perspective_y",0)}, "content_expected_bounds": layer["placement_expected_bounds"], "verify_with": "ps_get_state"})
        sequence += 1
        mask=layer.get("mask_plan") or {}
        if mask.get("enabled"):
            actions.append({"sequence":sequence,"tool":"ps_apply_layer_mask","args_from_previous_layer":True,"args":{"mask_file":mask.get("source_file",""),"feather":mask.get("feather",0),"density":mask.get("density",100),"invert":mask.get("invert",False)},"verify_with":"ps_get_state"})
            sequence+=1
        name=layer["name"]; group=layer["group"]
        script=f"var d=app.activeDocument,l=d.activeLayer;l.name={jsx_string(name)};var g=null;for(var i=0;i<d.layerSets.length;i++){{if(d.layerSets[i].name=={jsx_string(group)})g=d.layerSets[i];}}if(!g){{g=d.layerSets.add();g.name={jsx_string(group)};}}if(l.parent!=g)l.move(g,ElementPlacement.INSIDE);"
        actions.append({"sequence":sequence,"tool":"ps_execute_jsx","args":{"script":script,"operation_label":f"name and group {name}"},"verify_with":"ps_get_state"})
        sequence += 1
    for layer in [x for x in manifest.get("layers",[]) if x.get("layer_type")=="photoshop_native"]:
        script=compile_native(layer)
        actions.append({"sequence":sequence,"tool":"ps_execute_jsx","args":{"script":script,"operation_label":f"build native {layer['name']}"},"expected_name":layer["name"],"verify_with":"ps_get_state"}); sequence+=1
    actions.append({"sequence":sequence,"tool":"ps_execute_jsx","args":{"script":"var g=null;for(var i=0;i<app.activeDocument.layerSets.length;i++)if(app.activeDocument.layerSets[i].name=='99_REFERENCE_OVERLAY')g=app.activeDocument.layerSets[i];if(!g)throw new Error('reference overlay missing');g.visible=false;","operation_label":"hide reference overlay"},"verify_with":"ps_get_state"}); sequence+=1
    actions.append({"sequence":sequence,"tool":"ps_save_psd","args":{"output_path":str((root/'05_output/psd'/f'{root.name}.psd').resolve())},"verify_result":True}); sequence+=1
    actions.append({"sequence":sequence,"tool":"ps_export_png","args":{"output_path":str((root/'05_output/review'/f'{root.name}.png').resolve())},"verify_result":True})
    output = {"manifest": str(manifest_path), "fail_closed": True, "actions": actions}
    path = root / "04_photoshop" / "manifests" / "mcp_action_queue.json"
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    state_path=root/'.visual_recon/project_state.json'
    if state_path.exists():
        state=json.loads(state_path.read_text(encoding='utf-8')); state['state']='PHOTOSHOP_REAL_BUILD'; state['state_status']='PENDING'; state['last_completed_state']='PHOTOSHOP_BUILD_PRECHECK'; state['next_action']='EXECUTE_MCP_ACTION_QUEUE'; state_path.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
    print(path)


if __name__ == "__main__":
    main()
