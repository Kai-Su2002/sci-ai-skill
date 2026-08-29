from pathlib import Path
import argparse, asyncio, hashlib, json

MAX_INLINE_SCRIPT_BYTES = 512 * 1024

def compact_state(state):
    if not isinstance(state, dict): return state
    rows=[]
    def walk(items, parent=None):
        for item in items or []:
            if not isinstance(item,dict): continue
            rows.append({k:item.get(k) for k in ('layer_id','name','visibility','opacity','kind','bounds','has_user_mask') if k in item} | {'group':parent})
            walk(item.get('children') or item.get('layers'), item.get('layer_id') or item.get('name') or parent)
    walk(state.get('layers',[]))
    return {'document_name':state.get('document_name'),'document_width':state.get('document_width'),'document_height':state.get('document_height'),'layer_count':state.get('layer_count'),'layers':rows}

def classify_error(tool, detail):
    text=str(detail).lower()
    if 'bad request' in text: return 'REQUEST_PAYLOAD_OR_ARGUMENT_INVALID'
    if 'timeout' in text: return 'PHOTOSHOP_OR_MCP_TIMEOUT'
    if 'document' in text and ('active' in text or 'open' in text): return 'NO_ACTIVE_DOCUMENT'
    if 'layer' in text and ('not found' in text or 'missing' in text): return 'TARGET_LAYER_NOT_FOUND'
    return f'{tool.upper()}_FAILED'

async def execute(args):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    root=Path(args.project_root).resolve(); queue_path=Path(args.queue_file).resolve() if args.queue_file else root/'04_photoshop/manifests/mcp_action_queue.json'; queue=json.loads(queue_path.read_text(encoding='utf-8'))
    params=StdioServerParameters(command=args.python,args=[args.server])
    log=[]; previous=None
    log_name={'correction_action_queue.json':'correction_execution_log.json','transparent_asset_export_queue.json':'transparent_asset_export_log.json'}.get(queue_path.name,'mcp_execution_log.json')
    path=root/'06_logs'/log_name; path.parent.mkdir(parents=True,exist_ok=True)
    def persist(completed, error=None):
        payload={'completed':completed,'queue':str(queue_path),'actions':log}
        if error: payload['error']=error
        path.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
    try:
      async with stdio_client(params) as streams:
        async with ClientSession(*streams) as session:
            await session.initialize(); available={x.name for x in (await session.list_tools()).tools}
            required={x['tool'] for x in queue['actions']}
            missing=sorted(required-available)
            if missing: raise RuntimeError('MCP missing tools: '+', '.join(missing))
            for action in queue['actions']:
                call_args=dict(action.get('args') or {})
                if action['tool']=='ps_execute_jsx' and len(str(call_args.get('script','')).encode('utf-8'))>MAX_INLINE_SCRIPT_BYTES:
                    raise RuntimeError('JSX_REQUEST_TOO_LARGE: split the operation into smaller deterministic actions')
                if action.get('args_from_previous_layer'):
                    if not isinstance(previous,dict) or not previous.get('layer_id'): raise RuntimeError('previous layer_id missing')
                    call_args['layer_id']=previous['layer_id']
                try:
                    result=await session.call_tool(action['tool'],call_args)
                except Exception as exc:
                    raise RuntimeError(f"{classify_error(action['tool'],exc)}: {exc}") from exc
                texts=[x.text for x in result.content if hasattr(x,'text')]
                if getattr(result,'isError',False): raise RuntimeError(f"{action['tool']} failed: {texts}")
                parsed=None
                for value in texts:
                    try: parsed=json.loads(value); break
                    except Exception: pass
                previous=parsed or {'text':texts}
                entry={'sequence':action['sequence'],'tool':action['tool'],'args':call_args,'result':previous}
                if action.get('verify_with'):
                    state_result=await session.call_tool(action['verify_with'],{})
                    state_text=next((x.text for x in state_result.content if hasattr(x,'text')),None)
                    full_state=json.loads(state_text) if state_text else None
                    entry['state']=compact_state(full_state)
                log.append(entry)
                persist(False)
    except Exception as exc:
        persist(False, {'category':classify_error('mcp_action_queue',exc),'detail':str(exc),'completed_actions':len(log)})
        raise
    persist(True)
    final_state=next((x.get('state') for x in reversed(log) if x.get('state')),None)
    if final_state:
        state_out=root/'04_photoshop/qa/photoshop_state.json'; state_out.parent.mkdir(parents=True,exist_ok=True); state_out.write_text(json.dumps(final_state,ensure_ascii=False,indent=2),encoding='utf-8')
    project_state=root/'.visual_recon/project_state.json'
    if project_state.exists() and queue_path.name not in {'correction_action_queue.json','transparent_asset_export_queue.json'}:
        state=json.loads(project_state.read_text(encoding='utf-8')); build=state.setdefault('photoshop_build',{})
        rows=(final_state or {}).get('layers',[]); build['verified_layer_count']=len([x for x in rows if x.get('layer_id')]); build['verified_component_placement_count']=len([x for x in rows if str(x.get('name','')).startswith('COMP_')]); build['last_photoshop_state_hash']=hashlib.sha256(json.dumps(final_state or {},sort_keys=True,ensure_ascii=False).encode('utf-8')).hexdigest()
        state['state']='BUILD_QA'; state['state_status']='PENDING'; state['last_completed_state']='PHOTOSHOP_REAL_BUILD'; state['next_action']='RUN_EVIDENCE_QA'; project_state.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
    print(path)

def main():
    p=argparse.ArgumentParser(); p.add_argument('project_root'); p.add_argument('--python',required=True); p.add_argument('--server',required=True); p.add_argument('--queue-file'); asyncio.run(execute(p.parse_args()))
if __name__=='__main__': main()
