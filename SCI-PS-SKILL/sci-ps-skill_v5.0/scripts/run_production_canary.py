from pathlib import Path
import argparse, asyncio, hashlib, json, tempfile
from PIL import Image, ImageDraw

def parse_result(result):
    texts=[x.text for x in result.content if hasattr(x,'text')]
    if getattr(result,'isError',False): raise RuntimeError(str(texts))
    for value in texts:
        try: return json.loads(value)
        except Exception: pass
    return {'text':texts}

async def main_async(args):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    root=Path(args.project_root).resolve(); out=root/'.visual_recon/production_canary.json'; out.parent.mkdir(parents=True,exist_ok=True)
    checks={k:False for k in ('document_created','group_created','smart_object_placed','transform_verified','text_created','mask_applied','jsx_executed','psd_saved','png_exported','export_hash_verified','document_closed_without_save')}
    params=StdioServerParameters(command=args.python,args=[args.server])
    with tempfile.TemporaryDirectory(prefix='photoshop_production_canary_') as temp:
        temp=Path(temp); component=temp/'component.png'; mask=temp/'mask.png'; psd=temp/'canary.psd'; png=temp/'canary.png'
        Image.new('RGBA',(32,32),(40,150,240,255)).save(component)
        m=Image.new('RGBA',(32,32),(0,0,0,0)); ImageDraw.Draw(m).ellipse((2,2,29,29),fill=(255,255,255,255)); m.save(mask)
        async with stdio_client(params) as streams:
          async with ClientSession(*streams) as session:
            await session.initialize(); available={x.name for x in (await session.list_tools()).tools}
            required={'ps_health','ps_create_document','ps_place_smart_object','ps_transform_layer_advanced','ps_apply_layer_mask','ps_create_text','ps_execute_jsx','ps_get_state','ps_save_psd','ps_export_png','ps_close_document'}
            missing=sorted(required-available)
            if missing: raise RuntimeError('canary missing tools: '+', '.join(missing))
            health=parse_result(await session.call_tool('ps_health',{}))
            created_here=False
            try:
                created=parse_result(await session.call_tool('ps_create_document',{'width_px':96,'height_px':96,'resolution':72,'name':'MCP_PRODUCTION_CANARY'})); checks['document_created']=created.get('document_width')==96 and created.get('document_height')==96; created_here=checks['document_created']
                parse_result(await session.call_tool('ps_execute_jsx',{'script':"var d=app.activeDocument,g=d.layerSets.add();g.name='CANARY_GROUP';",'operation_label':'create canary group'})); checks['group_created']=True
                placed=parse_result(await session.call_tool('ps_place_smart_object',{'file_path':str(component),'name':'CANARY_SMART_OBJECT'})); layer_id=placed.get('layer_id'); checks['smart_object_placed']=bool(layer_id and placed.get('smart_object_verified'))
                transformed=parse_result(await session.call_tool('ps_transform_layer_advanced',{'layer_id':layer_id,'x':20,'y':20,'width':40,'height':40,'rotation':5})); checks['transform_verified']=transformed.get('verified') is True
                masked=parse_result(await session.call_tool('ps_apply_layer_mask',{'layer_id':layer_id,'mask_file':str(mask),'feather':1,'density':90,'invert':False})); checks['mask_applied']=masked.get('mask_verified') is True
                text=parse_result(await session.call_tool('ps_create_text',{'text':'Aa','x':8,'y':16,'font_size':10})); checks['text_created']=bool(text.get('layer_id'))
                parse_result(await session.call_tool('ps_execute_jsx',{'script':"var d=app.activeDocument,l=d.artLayers.add();l.name='CANARY_GLOW';l.blendMode=BlendMode.SCREEN;l.opacity=25;",'operation_label':'create canary visual effect'})); checks['jsx_executed']=True
                saved=parse_result(await session.call_tool('ps_save_psd',{'output_path':str(psd)})); checks['psd_saved']=saved.get('verified') is True and psd.is_file()
                exported=parse_result(await session.call_tool('ps_export_png',{'output_path':str(png)})); checks['png_exported']=exported.get('verified') is True and png.is_file()
                with Image.open(png) as im: size_ok=im.size==(96,96)
                checks['export_hash_verified']=size_ok and len(hashlib.sha256(png.read_bytes()).hexdigest())==64 and png.stat().st_size>0
                state=parse_result(await session.call_tool('ps_get_state',{}))
                names=[]
                def walk(items):
                    for item in items or []: names.append(item.get('name')); walk(item.get('children') or item.get('layers'))
                walk(state.get('layers',[]))
                if not {'CANARY_GROUP','CANARY_SMART_OBJECT','CANARY_GLOW'} <= set(names): raise RuntimeError('canary state readback missing expected layers')
            finally:
                if created_here:
                    closed=parse_result(await session.call_tool('ps_close_document',{'save_changes':False})); checks['document_closed_without_save']=closed.get('closed') is True
    inventory_hash=hashlib.sha256(json.dumps(sorted(available),ensure_ascii=False,separators=(',',':')).encode('utf-8')).hexdigest()
    checks.update({'photoshop_version':health.get('photoshop_version'),'mcp_server_id':str(Path(args.server).resolve()),'tool_inventory_sha256':inventory_hash,'skill_version':'5.0','production_canary_passed':all(v is True for k,v in checks.items() if k not in {'photoshop_version','mcp_server_id','tool_inventory_sha256','skill_version','production_canary_passed'})})
    out.write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
    (out.parent/'tool_inventory.json').write_text(json.dumps({'tools':sorted(available)},ensure_ascii=False,indent=2),encoding='utf-8')
    (out.parent/'ps_health.json').write_text(json.dumps(health,ensure_ascii=False,indent=2),encoding='utf-8')
    print(out)
    if checks['production_canary_passed'] is not True: raise SystemExit(2)

def main():
    p=argparse.ArgumentParser(); p.add_argument('project_root'); p.add_argument('--python',required=True); p.add_argument('--server',required=True); asyncio.run(main_async(p.parse_args()))

if __name__=='__main__': main()
