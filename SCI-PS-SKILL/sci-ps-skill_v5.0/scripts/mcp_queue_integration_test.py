from pathlib import Path
import argparse,json,subprocess,sys,tempfile
from PIL import Image

HERE=Path(__file__).resolve().parent

def main():
    p=argparse.ArgumentParser(); p.add_argument('--mcp-python',required=True); p.add_argument('--server',required=True); args=p.parse_args()
    with tempfile.TemporaryDirectory(prefix='visual_recon_queue_') as temp:
        root=Path(temp)/'queue_test'; (root/'04_photoshop/manifests').mkdir(parents=True); (root/'05_output/psd').mkdir(parents=True); (root/'05_output/review').mkdir(parents=True); (root/'06_logs').mkdir(parents=True)
        ref=root/'ref.png'; comp=root/'comp.png'; Image.new('RGBA',(100,100),(30,40,50,255)).save(ref); Image.new('RGBA',(20,20),(200,80,20,255)).save(comp)
        manifest={'canvas':{'width':100,'height':100,'resolution':72},'reference_overlay':{'source_file':str(ref)},'layers':[{'layer_id':'c1','layer_type':'component','group':'05_COMPONENTS_MAIN','name':'COMP_c1','source_file':str(comp),'tool_target_layer_bounds':[10,10,30,30],'placement_expected_bounds':[10,10,30,30]},{'layer_id':'n1','layer_type':'photoshop_native','native_type':'RECTANGLE','group':'07_PATHS_ARROWS','name':'NATIVE_RECT','build_spec':{'bbox':[40,40,60,60],'opacity':100,'blend_mode':'NORMAL','parameters':{'fill_color':'#ffffff'}}}]}
        (root/'04_photoshop/manifests/build_manifest.json').write_text(json.dumps(manifest),encoding='utf-8')
        subprocess.run([sys.executable,str(HERE/'generate_mcp_action_queue.py'),str(root)],check=True)
        subprocess.run([args.mcp_python,str(HERE/'execute_mcp_action_queue.py'),str(root),'--python',args.mcp_python,'--server',args.server],check=True)
        log=json.loads((root/'06_logs/mcp_execution_log.json').read_text(encoding='utf-8'))
        if not log.get('completed') or not (root/'05_output/psd/queue_test.psd').is_file() or not (root/'05_output/review/queue_test.png').is_file(): raise RuntimeError('queue output verification failed')
        backend=str(Path(args.server).parent)
        subprocess.run([args.mcp_python,'-c',f"import sys;sys.path.insert(0,r'{backend}');import photoshop_com;photoshop_com.close_document(False)"],check=True)
        subprocess.run([args.mcp_python,str(Path(args.server).parent/'mcp_stdio_integration_test.py'),'--python',args.mcp_python,'--server',args.server],check=True,stdout=subprocess.DEVNULL)
    print('MCP_ACTION_QUEUE_INTEGRATION=PASS')
if __name__=='__main__':main()
