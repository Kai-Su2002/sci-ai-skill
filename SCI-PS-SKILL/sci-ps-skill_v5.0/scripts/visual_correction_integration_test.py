from pathlib import Path
import json,subprocess,sys,tempfile
from PIL import Image,ImageDraw

HERE=Path(__file__).resolve().parent
def main():
    with tempfile.TemporaryDirectory(prefix='visual_correction_') as tmp:
        root=Path(tmp)/'project';qa=root/'04_photoshop/qa';mf=root/'04_photoshop/manifests';qa.mkdir(parents=True);mf.mkdir(parents=True)
        ref=Image.new('RGBA',(80,60),(30,30,30,255));out=ref.copy();ImageDraw.Draw(out).rectangle((20,15,49,39),fill=(80,80,80,255))
        rp=root/'ref.png';op=root/'out.png';ref.save(rp);out.save(op)
        state={'layers':[{'name':'TARGET_LAYER','visibility':True,'bounds':{'left':20,'top':15,'right':50,'bottom':40}}]}
        (qa/'photoshop_state.json').write_text(json.dumps(state),encoding='utf-8')
        result=subprocess.run([sys.executable,str(HERE/'localize_visual_differences.py'),str(root),str(rp),str(op),'--threshold','4'],capture_output=True,text=True)
        if result.returncode!=2: raise RuntimeError(result.stdout+result.stderr)
        localized=json.loads((qa/'difference_localization.json').read_text(encoding='utf-8'))
        if not localized['regions'] or localized['regions'][0]['candidate_layers'][0]!='TARGET_LAYER': raise RuntimeError('difference was not mapped to target layer')
        subprocess.run([sys.executable,str(HERE/'generate_correction_queue.py'),str(root)],check=True)
        queue=json.loads((mf/'correction_action_queue.json').read_text(encoding='utf-8'))
        if not queue['actions'] or queue['actions'][0]['tool']!='ps_execute_jsx' or not queue['requires_recompare']: raise RuntimeError('correction queue incomplete')
        same=root/'same.png';ref.save(same)
        subprocess.run([sys.executable,str(HERE/'localize_visual_differences.py'),str(root),str(rp),str(same),'--threshold','0'],check=True)
        clean=json.loads((qa/'difference_localization.json').read_text(encoding='utf-8'))
        if clean['unresolved_count']!=0: raise RuntimeError('clean comparison did not converge')
    print('VISUAL_CORRECTION_INTEGRATION=PASS')
if __name__=='__main__':main()
