from pathlib import Path
import argparse, json

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('project_root'); ap.add_argument('--verification-json',required=True); args=ap.parse_args()
    verification=json.loads(Path(args.verification_json).read_text(encoding='utf-8'))
    if verification.get('verified') is not True: raise SystemExit('build state verification 未通过，禁止更新已验证进度')
    layers=int(verification.get('actual_named_count',0)); placements=int(verification.get('verified_component_placement_count',0))
    p=Path(args.project_root)/'.visual_recon/project_state.json'; s=json.loads(p.read_text(encoding='utf-8')); b=s.setdefault('photoshop_build',{})
    oldl=b.get('verified_layer_count',0); oldp=b.get('verified_component_placement_count',0)
    if layers<=oldl and placements<=oldp: b['no_progress_cycles']=b.get('no_progress_cycles',0)+1
    else: b['no_progress_cycles']=0
    b['verified_layer_count']=layers; b['verified_component_placement_count']=placements
    b['last_photoshop_state_hash']=verification.get('state_sha256')
    if b['no_progress_cycles']>=2: s['state_status']='PAUSED'; s['next_action']='BUILD_LOOP_DETECTED'; b['build_loop_detected']=True
    p.write_text(json.dumps(s,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(b,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
