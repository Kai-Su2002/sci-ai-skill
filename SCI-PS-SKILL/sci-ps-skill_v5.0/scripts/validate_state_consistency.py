from pathlib import Path
import argparse, json

DELIVERY_STATES = {'TRANSPARENT_ASSET_EXPORT','USER_REVIEW','FINAL_EXPORT','DONE'}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('project_root'); args=ap.parse_args()
    path=Path(args.project_root).resolve()/'.visual_recon/project_state.json'
    if not path.exists(): raise SystemExit('未找到 project_state.json')
    state=json.loads(path.read_text(encoding='utf-8')); issues=[]
    visual=state.get('final_visual_match') is True
    adapted=state.get('final_user_directed_result') is True
    if state.get('state') in DELIVERY_STATES and not (visual or adapted):
        issues.append('交付相关状态需要 final_visual_match 或 final_user_directed_result 为 true')
    if state.get('state') in {'USER_REVIEW','FINAL_EXPORT','DONE'} and state.get('transparent_asset_library_validated') is not True:
        issues.append('用户审阅与最终交付前需要透明元素资产库验证通过')
    if adapted and not str(state.get('user_directed_approval_quote','')).strip():
        issues.append('final_user_directed_result 缺少 user_directed_approval_quote')
    if visual and adapted:
        issues.append('精确匹配与用户定向改编不可同时作为当前最终结论')
    build=state.get('photoshop_build') or {}
    for key in ('verified_layer_count','verified_component_placement_count','no_progress_cycles'):
        if int(build.get(key,0) or 0)<0: issues.append(f'{key} 不得为负数')
    result={'valid':not issues,'issues':issues,'state':state.get('state'),'next_action':state.get('next_action')}
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if issues: raise SystemExit(2)

if __name__=='__main__': main()
