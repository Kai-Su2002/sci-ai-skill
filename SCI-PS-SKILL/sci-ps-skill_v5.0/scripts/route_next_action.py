from pathlib import Path
import argparse,json

ROUTES={
"CAPABILITY_PRECHECK":"RUN_STRICT_CAPABILITY_PRECHECK","CAPABILITY_BOOTSTRAP":"INSTALL_PRODUCTION_MCP","PROJECT_INIT":"COLLECT_PROJECT_SPEC","UNIVERSAL_IMAGE2_WEB_HANDOFF":"PREPARE_WEB_HANDOFF","WAIT_IMAGE2_HANDOFF":"WAIT_FOR_COMPONENT_HANDOFF_ZIP","COMPONENT_PACKAGE_VALIDATION":"VALIDATE_COMPONENT_HANDOFF","PHOTOSHOP_BUILD_PRECHECK":"GENERATE_BUILD_AND_ACTION_QUEUE","PHOTOSHOP_REAL_BUILD":"EXECUTE_MCP_ACTION_QUEUE","BUILD_QA":"RUN_EVIDENCE_QA","TRANSPARENT_ASSET_EXPORT":"EXPORT_AND_VALIDATE_TRANSPARENT_ASSETS","USER_REVIEW":"REQUEST_USER_REVIEW","REVISION":"APPLY_REQUESTED_REVISION","FINAL_EXPORT":"EXPORT_FINAL_FILES","DONE":"NONE"}

def main():
    p=argparse.ArgumentParser(); p.add_argument('project_root'); args=p.parse_args(); path=Path(args.project_root)/'.visual_recon/project_state.json'; state=json.loads(path.read_text(encoding='utf-8'))
    expected=ROUTES.get(state.get('state'))
    if not expected: raise SystemExit('unknown state: '+str(state.get('state')))
    if state.get('state') in {'TRANSPARENT_ASSET_EXPORT','USER_REVIEW','FINAL_EXPORT','DONE'} and not (state.get('final_visual_match') is True or state.get('final_user_directed_result') is True):
        raise SystemExit('illegal state: transparent export/review/delivery requires a validated final result flag')
    if state.get('state') in {'USER_REVIEW','FINAL_EXPORT','DONE'} and state.get('transparent_asset_library_validated') is not True:
        raise SystemExit('illegal state: USER_REVIEW/FINAL_EXPORT/DONE requires a validated transparent asset library')
    if state.get('final_user_directed_result') is True and not str(state.get('user_directed_approval_quote','')).strip():
        raise SystemExit('final_user_directed_result requires user_directed_approval_quote')
    if state.get('next_action') not in {expected,'BUILD_LOOP_DETECTED','REPAIR_COMPONENT_HANDOFF','RESOLVE_VISUAL_DIFFERENCES'}: raise SystemExit(f"illegal next_action {state.get('next_action')} for state {state.get('state')}; expected {expected}")
    print(json.dumps({'state':state['state'],'state_status':state.get('state_status'),'next_action':state.get('next_action'),'legal':True},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
