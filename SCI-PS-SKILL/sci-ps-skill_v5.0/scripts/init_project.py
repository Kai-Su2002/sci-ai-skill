from pathlib import Path
import argparse, json, shutil

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('project_root'); ap.add_argument('--name',default='visual_reconstruction_project'); args=ap.parse_args()
    root=Path(args.project_root).resolve()
    dirs=['00_reference','01_spec','02_component_handoff/OUTBOUND','02_component_handoff/INBOX','02_component_handoff/VALIDATED','03_components/approved','03_components/temporary','03_components/rejected','04_photoshop/manifests','04_photoshop/scripts','04_photoshop/qa','05_output/psd','05_output/review','05_output/final','05_output/transparent_elements','06_logs','.visual_recon/checkpoints']
    for d in dirs:(root/d).mkdir(parents=True,exist_ok=True)
    state=root/'.visual_recon/project_state.json'
    if not state.exists():
        data={'skill_version':'5.0','project_name':args.name,'state':'CAPABILITY_PRECHECK','state_status':'PENDING','last_completed_state':None,'next_action':'RUN_STRICT_CAPABILITY_PRECHECK','capability':{},'web_handoff_prepared':False,'component_handoff_validated':False,'transparent_asset_library_validated':False,'reference_production_route':{'dominant_style':'UNCLASSIFIED','vector_tool_asked':False,'vector_tool_available':False,'fallback_for_non_native_elements':'IMAGE2'},'revision_policy':{'locked_categories':[],'deferred_categories':[],'active_scope':None},'processed_commands':{},'photoshop_build':{'verified_layer_count':0,'verified_component_placement_count':0,'no_progress_cycles':0,'last_photoshop_state_hash':None},'final_visual_match':False,'final_user_directed_result':False,'checkpoints':[]}
        state.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    print(state)
if __name__=='__main__':main()
