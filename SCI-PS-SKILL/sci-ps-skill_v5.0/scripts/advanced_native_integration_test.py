from pathlib import Path
import argparse,json,subprocess,tempfile,sys
from PIL import Image

HERE=Path(__file__).resolve().parent
def native(i,t,name,bbox,params,group='08_EFFECTS'):
    return {'layer_id':i,'layer_type':'photoshop_native','native_type':t,'group':group,'name':name,'build_spec':{'bbox':bbox,'opacity':100,'blend_mode':'NORMAL','parameters':params}}
def main():
    p=argparse.ArgumentParser();p.add_argument('--mcp-python',required=True);p.add_argument('--server',required=True);a=p.parse_args()
    with tempfile.TemporaryDirectory(prefix='advanced_native_') as temp:
        root=Path(temp)/'advanced';(root/'04_photoshop/manifests').mkdir(parents=True);(root/'05_output/psd').mkdir(parents=True);(root/'05_output/review').mkdir(parents=True);(root/'06_logs').mkdir(parents=True)
        ref=root/'ref.png';base=root/'base.png';mask=root/'mask.png';Image.new('RGBA',(240,180),(15,20,30,255)).save(ref);Image.new('RGBA',(50,40),(40,180,240,255)).save(base);m=Image.new('RGBA',(50,40),(255,255,255,0));m.paste((255,255,255,255),(5,5,45,35));m.save(mask)
        layers=[{'layer_id':'base','layer_type':'component','group':'05_COMPONENTS_MAIN','name':'COMP_BASE','source_file':str(base),'tool_target_layer_bounds':[80,60,130,100],'placement_expected_bounds':[80,60,130,100],'transform_plan':{'rotation':4,'skew_x':2,'skew_y':0,'perspective_x':1,'perspective_y':0},'mask_plan':{'enabled':True,'source_file':str(mask),'feather':1,'density':96,'invert':False}}]
        layers += [
          native('g1','GLOW','FX_GLOW',[70,50,140,110],{'source_layer':'COMP_BASE','radius':8,'color':'#40c0ff'}),native('s1','SHADOW','FX_SHADOW',[70,50,140,110],{'source_layer':'COMP_BASE','radius':5,'color':'#000000','offset_x':6,'offset_y':8}),native('b1','BLUR','FX_BLUR',[70,50,140,110],{'source_layer':'COMP_BASE','radius':2}),
          native('gl','GRADIENT_LINEAR','BG_LINEAR',[0,0,60,180],{'start_color':'#102040','end_color':'#4080c0','steps':16},'02_BACKGROUND'),native('gr','GRADIENT_RADIAL','BG_RADIAL',[150,20,230,100],{'start_color':'#ffffff','end_color':'#204080','steps':12},'02_BACKGROUND'),
          native('al','ADJUSTMENT_LEVELS','ADJ_LEVELS',[0,0,240,180],{'input_black':5,'input_white':245,'gamma':1.05,'output_black':0,'output_white':255,'clipped':False},'10_FINISHING'),native('ah','ADJUSTMENT_HUE_SATURATION','ADJ_HUE',[0,0,240,180],{'hue':3,'saturation':5,'lightness':0,'clipped':False},'10_FINISHING'),native('ab','ADJUSTMENT_BRIGHTNESS_CONTRAST','ADJ_BC',[0,0,240,180],{'brightness':2,'contrast':4,'clipped':False},'10_FINISHING'),
          native('cp','COMPLEX_PATH','PATH_BEZIER',[20,120,220,170],{'stroke_color':'#ffffff','stroke_width':3,'closed':False,'points':[{'anchor':[20,150],'right':[60,110]},{'anchor':[120,140],'left':[80,170],'right':[160,110]},{'anchor':[220,150],'left':[180,180]}]},'07_PATHS_ARROWS'),
          native('ca','CURVED_ARROW','PATH_CURVED_ARROW',[20,90,220,140],{'stroke_color':'#ffffff','stroke_width':3,'head_size':12,'closed':False,'points':[{'anchor':[20,120],'right':[70,70]},{'anchor':[130,110],'left':[90,150],'right':[170,70]},{'anchor':[220,100],'left':[180,140]}]},'07_PATHS_ARROWS'),
          native('tx','TEXT','TEXT_ADVANCED',[60,20,180,50],{'text':'Advanced','font':'ArialMT','font_size':18,'color':'#ffffff','alignment':'CENTER','tracking':50,'leading':22,'anti_alias':'SHARP','horizontal_scale':105,'vertical_scale':98,'baseline_shift':1,'faux_bold':True,'faux_italic':False,'text_box':[120,40]},'09_TEXT')]
        manifest={'canvas':{'width':240,'height':180,'resolution':72},'reference_overlay':{'source_file':str(ref)},'layers':layers};(root/'04_photoshop/manifests/build_manifest.json').write_text(json.dumps(manifest),encoding='utf-8')
        subprocess.run([sys.executable,str(HERE/'generate_mcp_action_queue.py'),str(root)],check=True);subprocess.run([a.mcp_python,str(HERE/'execute_mcp_action_queue.py'),str(root),'--python',a.mcp_python,'--server',a.server],check=True)
        log=json.loads((root/'06_logs/mcp_execution_log.json').read_text(encoding='utf-8')); names={x.get('name') for e in log['actions'] for x in ((e.get('state') or {}).get('layers') or [])}
        if not log.get('completed') or not (root/'05_output/psd/advanced.psd').is_file():raise RuntimeError('advanced queue incomplete')
        backend=str(Path(a.server).parent)
        probe=("import sys,json;sys.path.insert(0,r'"+backend+"');import photoshop_com as p;"
               "s=p.get_state();flat=[];"
               "exec(\"def w(xs):\\n for x in xs:\\n  flat.append(x);w(x.get('children',[]))\\nw(s['layers'])\");"
               "assert any(x.get('name')=='COMP_BASE' and x.get('has_user_mask') is True for x in flat);"
               "r=p.execute_jsx(\"var ok=app.activeDocument.pathItems.getByName('PATH_BEZIER_PATH')!=null&&app.activeDocument.pathItems.getByName('PATH_CURVED_ARROW_PATH')!=null;ok;\",'verify retained paths');"
               "assert r['result']=='true';p.close_document(False);print('PHOTOSHOP_STRUCTURE_ASSERTIONS=PASS')")
        subprocess.run([a.mcp_python,'-c',probe],check=True)
    print('ADVANCED_NATIVE_INTEGRATION=PASS')
if __name__=='__main__':main()
