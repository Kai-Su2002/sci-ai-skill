from pathlib import Path
import argparse,json,shutil

def main():
    p=argparse.ArgumentParser(); p.add_argument('project_root'); p.add_argument('--user-approval',required=True); args=p.parse_args(); root=Path(args.project_root).resolve()
    qa=json.loads((root/'04_photoshop/qa/final_qa_validation.json').read_text(encoding='utf-8'))
    if qa.get('final_qa_validated') is not True: raise SystemExit('final QA 未通过')
    assets_path=root/'05_output/transparent_elements/transparent_elements_manifest.json'
    if not assets_path.exists() or json.loads(assets_path.read_text(encoding='utf-8')).get('validated') is not True: raise SystemExit('统一透明元素资产库未验证通过')
    if not args.user_approval.strip(): raise SystemExit('缺少用户验收原文')
    psds=list((root/'05_output/psd').glob('*.psd')); pngs=list((root/'05_output/review').glob('*.png'))
    if len(psds)!=1 or len(pngs)!=1: raise SystemExit('PSD/review PNG 必须各有且只有一个')
    final=root/'05_output/final'; final.mkdir(parents=True,exist_ok=True); shutil.copy2(psds[0],final/psds[0].name); shutil.copy2(pngs[0],final/pngs[0].name)
    state_path=root/'.visual_recon/project_state.json'; state=json.loads(state_path.read_text(encoding='utf-8')); state.update({'state':'DONE','state_status':'PASS','last_completed_state':'FINAL_EXPORT','next_action':'NONE','user_review_approval':args.user_approval}); state_path.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'delivered':True,'psd':str(final/psds[0].name),'png':str(final/pngs[0].name),'transparent_elements':str(root/'05_output/transparent_elements')},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
