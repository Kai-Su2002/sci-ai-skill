from pathlib import Path
import argparse
import json
import re


def jsx(value):
    return json.dumps(str(value), ensure_ascii=False)


def safe_name(value):
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", str(value)).strip("._")
    return value or "element"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("project_root")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    qa = json.loads((root / "04_photoshop/qa/final_qa_validation.json").read_text(encoding="utf-8"))
    if qa.get("final_qa_validated") is not True:
        raise SystemExit("final QA 未通过，禁止导出透明元素资产库")
    manifest_path = root / "04_photoshop/manifests/build_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    output_dir = root / "05_output/transparent_elements"
    output_dir.mkdir(parents=True, exist_ok=True)
    for stale in list(output_dir.glob("*.png")) + [output_dir / "transparent_elements_manifest.json"]:
        if stale.is_file():
            stale.unlink()
    actions = []
    expected = []
    for layer in manifest.get("layers", []):
        kind = layer.get("layer_type")
        if kind not in {"component", "reference_extraction"}:
            continue
        provenance = layer.get("source_provenance", {})
        prefix = "IMAGE2" if kind == "component" and provenance.get("mode") == "IMAGE2_RECONSTRUCTION" else ("EXTRACT" if kind == "reference_extraction" else "ASSET")
        filename = f"{prefix}_{safe_name(layer['layer_id'])}_{safe_name(layer['name'])}.png"
        output_path = (output_dir / filename).resolve()
        script = (
            "var src=app.activeDocument;function find(items,n){for(var i=0;i<items.length;i++){var x=items[i];"
            "if(x.name==n)return x;if(x.typename=='LayerSet'){var y=find(x.layers,n);if(y)return y;}}return null;}"
            f"var l=find(src.layers,{jsx(layer['name'])});if(!l)throw new Error('asset layer missing');"
            "var b=l.bounds,L=b[0].as('px'),T=b[1].as('px'),R=b[2].as('px'),B=b[3].as('px');"
            "var W=Math.max(3,Math.ceil(R-L)+2),H=Math.max(3,Math.ceil(B-T)+2);"
            "var tmp=app.documents.add(W,H,src.resolution,'TRANSPARENT_ELEMENT',NewDocumentMode.RGB,DocumentFill.TRANSPARENT);"
            "app.activeDocument=src;var dup=l.duplicate(tmp,ElementPlacement.PLACEATBEGINNING);app.activeDocument=tmp;dup.visible=true;"
            "var db=dup.bounds,DL=db[0].as('px'),DT=db[1].as('px');dup.translate(1-DL,1-DT);"
            f"var opt=new PNGSaveOptions();tmp.saveAs(new File({jsx(output_path)}),opt,true,Extension.LOWERCASE);"
            "tmp.close(SaveOptions.DONOTSAVECHANGES);app.activeDocument=src;"
        )
        actions.append({"sequence": len(actions) + 1, "tool": "ps_execute_jsx", "args": {"script": script, "operation_label": f"export transparent asset {filename}"}, "verify_with": "ps_get_state"})
        expected.append({"layer_id": layer["layer_id"], "layer_name": layer["name"], "source_class": kind, "file_name": filename, "source_provenance": provenance})
    queue = {"manifest": str(manifest_path), "fail_closed": True, "asset_output_dir": str(output_dir), "expected_assets": expected, "actions": actions}
    path = root / "04_photoshop/manifests/transparent_asset_export_queue.json"
    path.write_text(json.dumps(queue, ensure_ascii=False, indent=2), encoding="utf-8")
    print(path)


if __name__ == "__main__":
    main()
