from pathlib import Path
import argparse, shutil, json

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('project_root'); args=ap.parse_args(); root=Path(args.project_root).resolve()
    refs=[p for p in (root/'00_reference').iterdir() if p.is_file()]
    if len(refs)!=1: raise SystemExit(f'00_reference 中应有且只有一个主参考图，当前 {len(refs)} 个。')
    src=refs[0]; outbound=root/'02_component_handoff/OUTBOUND'; dst=outbound/('reference_master'+src.suffix.lower()); outbound.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
    prompt_src=Path(__file__).resolve().parents[1]/'templates/UNIVERSAL_IMAGE_COMPONENT_EXTRACTION_PROMPT_ZH_V2.md'
    prompt_dst=outbound/'UNIVERSAL_IMAGE_COMPONENT_EXTRACTION_PROMPT_ZH_V2.md'
    if not prompt_src.exists(): raise SystemExit(f'缺少网页版通用提示词: {prompt_src}')
    shutil.copy2(prompt_src,prompt_dst)
    spec=root/'01_spec/project_manifest.json'
    data=json.loads(spec.read_text(encoding='utf-8')) if spec.exists() else {'project_name':root.name}
    data['reference_file']=dst.name; spec.parent.mkdir(parents=True,exist_ok=True); spec.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    state_path=root/'.visual_recon/project_state.json'
    if state_path.exists():
        state=json.loads(state_path.read_text(encoding='utf-8')); state['web_handoff_prepared']=True; state['state']='WAIT_IMAGE2_HANDOFF'; state['state_status']='WAITING_USER'; state['last_completed_state']='UNIVERSAL_IMAGE2_WEB_HANDOFF'; state['next_action']='WAIT_FOR_COMPONENT_HANDOFF_ZIP'; state_path.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'reference':str(dst),'prompt':str(prompt_dst)},ensure_ascii=False,indent=2))
if __name__=='__main__': main()
