from pathlib import Path
import argparse,asyncio,json,tempfile
from PIL import Image

async def main_async(args):
    from mcp import ClientSession,StdioServerParameters
    from mcp.client.stdio import stdio_client
    name='VISUAL_RECON_MCP_STDIO_TEST'
    with tempfile.TemporaryDirectory(prefix='visual_recon_mcp_') as temp:
        root=Path(temp); source=root/'source.png'; Image.new('RGBA',(40,30),(20,100,220,255)).save(source)
        params=StdioServerParameters(command=args.python,args=[args.server])
        async with stdio_client(params) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize(); tools={x.name for x in (await session.list_tools()).tools}
                required={'ps_health','ps_list_fonts','ps_create_document','ps_place_image','ps_place_smart_object','ps_transform_layer','ps_transform_layer_advanced','ps_apply_layer_mask','ps_create_text','ps_execute_jsx','ps_get_state','ps_save_psd','ps_export_png','ps_close_document'}
                if not required<=tools: raise RuntimeError('missing '+str(required-tools))
                async def call(name,values):
                    result=await session.call_tool(name,values)
                    if result.isError: raise RuntimeError(str(result.content))
                    text=next(x.text for x in result.content if hasattr(x,'text')); return json.loads(text)
                health=await call('ps_health',{}); await call('ps_create_document',{'width_px':120,'height_px':90,'resolution':72,'name':name}); placed=await call('ps_place_smart_object',{'file_path':str(source),'name':'SMART_COMPONENT'}); transformed=await call('ps_transform_layer_advanced',{'layer_id':placed['layer_id'],'x':10,'y':15,'width':60,'height':45,'rotation':5}); masked=await call('ps_apply_layer_mask',{'layer_id':placed['layer_id'],'feather':1,'density':95,'invert':False}); await call('ps_create_text',{'text':'MCP STDIO','x':8,'y':80,'font_size':10}); await call('ps_execute_jsx',{'script':"var g=app.activeDocument.layerSets.add();g.name='MCP_GROUP';var l=app.activeDocument.artLayers.add();l.name='MCP_HIDDEN';l.visible=false;l.move(g,ElementPlacement.INSIDE);",'operation_label':'recursive state test'}); state=await call('ps_get_state',{}); png=await call('ps_export_png',{'output_path':str(root/'out.png')}); psd=await call('ps_save_psd',{'output_path':str(root/'out.psd')}); await call('ps_close_document',{'save_changes':False})
                flat=[]
                def walk(items):
                    for x in items: flat.append(x); walk(x.get('children',[]))
                walk(state['layers'])
                ok=health.get('photoshop_connected') and placed.get('smart_object_verified') and transformed.get('verified') and masked.get('mask_verified') and png.get('verified') and psd.get('verified') and any(x.get('name')=='MCP_HIDDEN' and x.get('visibility') is False for x in flat)
                if not ok: raise RuntimeError('stdio assertions failed')
                print(json.dumps({'MCP_STDIO_INTEGRATION':'PASS','tools':sorted(tools),'photoshop_version':health.get('photoshop_version')},ensure_ascii=False))

def main():
    p=argparse.ArgumentParser(); p.add_argument('--python',required=True); p.add_argument('--server',required=True); asyncio.run(main_async(p.parse_args()))
if __name__=='__main__':main()
