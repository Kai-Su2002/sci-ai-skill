from pathlib import Path
import argparse, hashlib, json, platform, sys

BASE_TOOLS = {
    "ps_health", "ps_create_document", "ps_place_image", "ps_transform_layer",
    "ps_create_text", "ps_get_state", "ps_save_psd", "ps_export_png", "ps_close_document",
}
PRODUCTION_EXTENSION_TOOLS = {"ps_place_smart_object", "ps_transform_layer_advanced", "ps_apply_layer_mask", "ps_list_fonts"}
ADVANCED_ALTERNATIVES = [
    {"ps_execute_jsx"},
    {
        "ps_create_group", "ps_set_layer_properties", "ps_move_layer",
        "ps_create_shape", "ps_apply_mask", "ps_apply_effect",
        "ps_create_adjustment", "ps_set_text_properties",
    },
]

def yn(v): return 'YES' if v else 'NO'

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('project_root')
    ap.add_argument('--tool-inventory-json', help='当前会话 MCP tools 名称数组或 {tools:[...]}')
    ap.add_argument('--health-json', help='当前会话 ps_health 的真实返回 JSON')
    ap.add_argument('--canary-json', help='真实 production canary 结果 JSON；必须证明临时文档、组、Smart Object、变换、文字、蒙版、JSX、PSD/PNG 输出与关闭全部通过')
    args=ap.parse_args(); root=Path(args.project_root).resolve()
    result={'windows':platform.system()=='Windows','python':sys.executable,'pywin32':False,'photoshop_com_available':False,'photoshop_version':None,'codex_config_found':False,'photoshop_mcp_configured':False,'codex_mcp_tools_visible':'UNKNOWN','ps_health':'UNKNOWN'}
    try:
        import win32com.client
        result['pywin32']=True
        if result['windows']:
            app=win32com.client.gencache.EnsureDispatch('Photoshop.Application')
            result['photoshop_com_available']=True
            try: result['photoshop_version']=str(app.Version)
            except Exception: pass
    except Exception as e: result['com_error']=repr(e)
    cfg=Path.home()/'.codex'/'config.toml'; result['codex_config_found']=cfg.exists()
    if cfg.exists():
        t=cfg.read_text(encoding='utf-8',errors='ignore').lower()
        result['photoshop_mcp_configured']=('photoshop-poc' in t or 'photoshop-mcp' in t or 'photoshop-control' in t)
    hist=[]
    for p in [root/'photoshop_mcp_poc/POC_REPORT.md', root/'POC_REPORT.md']:
        if p.exists(): hist.append(str(p))
    result['historical_poc_reports']=hist
    core=result['windows'] and result['pywin32'] and result['photoshop_com_available'] and result['photoshop_mcp_configured']
    result['precheck_static']='PASS' if core else 'FAIL'
    tools = set()
    if args.tool_inventory_json:
        raw=json.loads(Path(args.tool_inventory_json).read_text(encoding='utf-8'))
        values=raw.get('tools', []) if isinstance(raw, dict) else raw
        raw_names={str(x.get('name') if isinstance(x,dict) else x) for x in values}
        tools={name.rsplit('__',1)[-1] for name in raw_names}
        result['raw_tool_names']=sorted(raw_names)
        result['codex_mcp_tools_visible']=sorted(tools)
    health={}
    if args.health_json:
        health=json.loads(Path(args.health_json).read_text(encoding='utf-8'))
        result['ps_health']='PASS' if health.get('photoshop_connected') is True else 'FAIL'
        result['ps_health_result']=health
    required_tools=BASE_TOOLS|PRODUCTION_EXTENSION_TOOLS
    missing_base=sorted(required_tools-tools) if tools else sorted(required_tools)
    advanced_ok=any(group <= tools for group in ADVANCED_ALTERNATIVES)
    canary={}
    if args.canary_json:
        canary_path=Path(args.canary_json)
        canary=json.loads(canary_path.read_text(encoding='utf-8'))
        result['production_canary']=canary
        result['production_canary_sha256']=hashlib.sha256(canary_path.read_bytes()).hexdigest()
    required_canary_checks={'document_created','group_created','smart_object_placed','transform_verified','text_created','mask_applied','jsx_executed','psd_saved','png_exported','export_hash_verified','document_closed_without_save'}
    canary_missing=sorted(x for x in required_canary_checks if canary.get(x) is not True)
    inventory_hash=hashlib.sha256(json.dumps(sorted(tools),ensure_ascii=False,separators=(',',':')).encode('utf-8')).hexdigest() if tools else None
    canary_context_valid=(canary.get('production_canary_passed') is True and canary.get('skill_version')=='5.0'
                          and bool(canary.get('mcp_server_id')) and canary.get('tool_inventory_sha256')==inventory_hash
                          and str(canary.get('photoshop_version'))==str(health.get('photoshop_version')))
    result['required_canary_checks']=sorted(required_canary_checks)
    result['missing_canary_checks']=canary_missing
    result['tool_inventory_sha256']=inventory_hash
    result['canary_context_valid']=canary_context_valid
    result['required_base_tools']=sorted(required_tools)
    result['missing_base_tools']=missing_base
    result['advanced_control_available']=advanced_ok
    result['production_precheck']='PASS' if core and not missing_base and advanced_ok and result['ps_health']=='PASS' and not canary_missing and canary_context_valid else 'FAIL'
    out=root/'.visual_recon/capability_status.json'; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    state_path=root/'.visual_recon/project_state.json'
    if state_path.exists():
        state=json.loads(state_path.read_text(encoding='utf-8')); state['capability']=result
        passed=result['production_precheck']=='PASS'; state['state']='PROJECT_INIT' if passed else 'CAPABILITY_BOOTSTRAP'; state['state_status']='PASS' if passed else 'BLOCKED'; state['last_completed_state']='CAPABILITY_PRECHECK' if passed else state.get('last_completed_state'); state['next_action']='COLLECT_PROJECT_SPEC' if passed else 'INSTALL_PRODUCTION_MCP'
        state_path.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if result['production_precheck'] != 'PASS':
        print('\n生产能力预检未通过：不得进入 Photoshop 构建。必须提供真实 tool inventory、ps_health 与 production canary 结果，并补齐导出及高级编辑能力。')
        raise SystemExit(2)
if __name__=='__main__':main()
