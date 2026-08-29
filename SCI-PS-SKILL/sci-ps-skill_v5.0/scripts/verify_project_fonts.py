from pathlib import Path
import argparse,json

def main():
    p=argparse.ArgumentParser();p.add_argument('project_root');p.add_argument('--font-inventory-json',required=True);a=p.parse_args()
    root=Path(a.project_root).resolve();matches=list((root/'02_component_handoff/VALIDATED').rglob('component_manifest.json'))
    if len(matches)!=1: raise SystemExit(f'需要且只能有一个已验证 component_manifest.json，当前 {len(matches)} 个。')
    manifest=json.loads(matches[0].read_text(encoding='utf-8'));required={x['postscript_name'] for x in manifest.get('font_assets',[])}
    inventory=json.loads(Path(a.font_inventory_json).read_text(encoding='utf-8'));available={x.get('postscript_name') for x in inventory.get('fonts',[])}
    missing=sorted(required-available);result={'verified':not missing,'required_postscript_names':sorted(required),'missing_postscript_names':missing}
    path=root/'06_logs/font_availability.json';path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False,indent=2))
    if missing: raise SystemExit(2)
if __name__=='__main__':main()
