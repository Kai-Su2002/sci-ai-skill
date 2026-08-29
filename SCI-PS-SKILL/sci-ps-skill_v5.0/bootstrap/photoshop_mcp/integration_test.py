from pathlib import Path
import json
import tempfile
from PIL import Image
import photoshop_com as ps


def flatten(items):
    for item in items:
        yield item
        yield from flatten(item.get("children",[]))


def main():
    name="VISUAL_RECON_PRODUCTION_MCP_TEST"
    created=False
    try:
        with tempfile.TemporaryDirectory(prefix="photoshop_mcp_test_") as temp:
            root=Path(temp); source=root/"source.png"; Image.new("RGBA",(40,30),(10,120,220,255)).save(source)
            health=ps.health(); ps.create_document(120,90,72,name); created=True
            placed=ps.place_image(str(source)); transformed=ps.transform_layer(placed["layer_id"],10,15,60,45)
            ps.create_text("MCP TEST",8,80,10)
            ps.execute_jsx("var d=app.activeDocument;var g=d.layerSets.add();g.name='TEST_GROUP';var l=d.artLayers.add();l.name='HIDDEN_TEST';l.visible=false;l.move(g,ElementPlacement.INSIDE);","group and visibility test")
            state=ps.get_state(); flat=list(flatten(state["layers"]))
            if not any(x.get("name")=="HIDDEN_TEST" and x.get("visibility") is False and x.get("group")=="TEST_GROUP" for x in flat): raise RuntimeError("recursive group/visibility state failed")
            png=ps.export_png(str(root/"export.png")); psd=ps.save_psd(str(root/"test.psd"))
            if health.get("production_profile")!="jsx_bridge_v1" or transformed.get("verified") is not True or png.get("verified") is not True or psd.get("verified") is not True: raise RuntimeError("production integration assertions failed")
            print(json.dumps({"PHOTOSHOP_PRODUCTION_INTEGRATION":"PASS","photoshop_version":health.get("photoshop_version"),"recursive_state":True,"transform":True,"png_export":True,"psd_save":True},ensure_ascii=False))
    finally:
        if created:
            try: ps.app().DoJavaScript(f"if(app.documents.length&&app.activeDocument.name.indexOf('{name}')===0)app.activeDocument.close(SaveOptions.DONOTSAVECHANGES);")
            except Exception: pass


if __name__=="__main__": main()
