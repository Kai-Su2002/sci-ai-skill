from pathlib import Path
import argparse, json

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('project_root'); args=ap.parse_args()
    p=Path(args.project_root)/'.visual_recon/project_state.json'
    if not p.exists(): raise SystemExit('未找到 project_state.json；应先 init_project。')
    s=json.loads(p.read_text(encoding='utf-8'))
    s['skill_version']='5.0'
    s.setdefault('reference_production_route',{'dominant_style':'UNCLASSIFIED','vector_tool_asked':False,'vector_tool_available':False,'fallback_for_non_native_elements':'IMAGE2'})
    s.setdefault('revision_policy',{'locked_categories':[],'deferred_categories':[],'active_scope':None})
    s.setdefault('processed_commands',{})
    s.setdefault('final_user_directed_result',False)
    s.setdefault('transparent_asset_library_validated',False)
    build=s.setdefault('photoshop_build',{}); build.setdefault('verified_layer_count',0); build.setdefault('verified_component_placement_count',0); build.setdefault('no_progress_cycles',0); build.setdefault('last_photoshop_state_hash',None)
    if s.get('state') in {'TRANSPARENT_ASSET_EXPORT','USER_REVIEW','FINAL_EXPORT','DONE'} and not (s.get('final_visual_match') is True or s.get('final_user_directed_result') is True):
        s['state']='BUILD_QA'; s['state_status']='BLOCKED'; s['next_action']='RESOLVE_VISUAL_DIFFERENCES'
    elif s.get('state') in {'USER_REVIEW','FINAL_EXPORT','DONE'} and s.get('transparent_asset_library_validated') is not True:
        s['state']='TRANSPARENT_ASSET_EXPORT'; s['state_status']='PENDING'; s['next_action']='EXPORT_AND_VALIDATE_TRANSPARENT_ASSETS'
    p.write_text(json.dumps(s,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'skill_version':s.get('skill_version'),'state':s.get('state'),'state_status':s.get('state_status'),'last_completed_state':s.get('last_completed_state'),'next_action':s.get('next_action'),'capability':s.get('capability',{}),'reference_production_route':s.get('reference_production_route',{}),'web_handoff_prepared':s.get('web_handoff_prepared',False),'component_handoff_validated':s.get('component_handoff_validated',False),'revision_policy':s.get('revision_policy',{}),'photoshop_build':s.get('photoshop_build',{}),'final_visual_match':s.get('final_visual_match',False),'final_user_directed_result':s.get('final_user_directed_result',False)},ensure_ascii=False,indent=2))
if __name__=='__main__': main()
