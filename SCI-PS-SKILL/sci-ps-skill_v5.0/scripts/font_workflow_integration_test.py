from pathlib import Path
import json,subprocess,sys,tempfile

HERE=Path(__file__).resolve().parent
def main():
    with tempfile.TemporaryDirectory(prefix='font_workflow_') as tmp:
        root=Path(tmp)/'project';validated=root/'02_component_handoff/VALIDATED/pkg';validated.mkdir(parents=True)
        manifest={'font_assets':[{'font_id':'F001','file_name':'font.ttf','license_file':'LICENSE.txt','family_name':'Test Family','postscript_name':'TestFamily-Regular','source_url':'https://example.invalid/font','license_name':'Test License','sha256':'0'*64,'user_approved_download':True,'user_approval_quote':'同意测试'}]}
        (validated/'component_manifest.json').write_text(json.dumps(manifest),encoding='utf-8')
        inventory={'verified':True,'fonts':[{'postscript_name':'TestFamily-Regular'}]};inv=root/'inventory.json';inv.write_text(json.dumps(inventory),encoding='utf-8')
        subprocess.run([sys.executable,str(HERE/'verify_project_fonts.py'),str(root),'--font-inventory-json',str(inv)],check=True)
        denied=subprocess.run([sys.executable,str(HERE/'install_project_fonts.py'),str(root)],capture_output=True,text=True)
        if denied.returncode==0 or '--user-approved-install' not in (denied.stdout+denied.stderr): raise RuntimeError('font installation approval gate failed')
    print('FONT_WORKFLOW_INTEGRATION=PASS')
if __name__=='__main__':main()
