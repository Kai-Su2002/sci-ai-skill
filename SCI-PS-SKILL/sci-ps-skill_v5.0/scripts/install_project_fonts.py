from pathlib import Path
import argparse,ctypes,hashlib,json,os,shutil,sys

def main():
    p=argparse.ArgumentParser();p.add_argument('project_root');p.add_argument('--user-approved-install',action='store_true');a=p.parse_args()
    if not a.user_approved_install: raise SystemExit('必须先向用户展示字体来源和许可证，并获得明确同意；随后传入 --user-approved-install。')
    if os.name!='nt': raise SystemExit('字体安装仅支持 Windows。')
    root=Path(a.project_root).resolve();matches=list((root/'02_component_handoff/VALIDATED').rglob('component_manifest.json'))
    if len(matches)!=1: raise SystemExit(f'需要且只能有一个已验证 component_manifest.json，当前 {len(matches)} 个。')
    manifest=json.loads(matches[0].read_text(encoding='utf-8'));fonts=manifest.get('font_assets',[])
    if not fonts: print(json.dumps({'installed':[],'photoshop_restart_required':False},ensure_ascii=False));return
    target=Path(os.environ['LOCALAPPDATA'])/'Microsoft'/'Windows'/'Fonts';target.mkdir(parents=True,exist_ok=True)
    import winreg
    installed=[]
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER,r'Software\Microsoft\Windows NT\CurrentVersion\Fonts') as key:
        for item in fonts:
            source_matches=list(matches[0].parent.rglob(item['file_name']))
            if len(source_matches)!=1: raise SystemExit(f"{item['font_id']}: 字体文件应有且只有一个")
            source=source_matches[0];data=source.read_bytes();actual=hashlib.sha256(data).hexdigest()
            if actual.lower()!=item['sha256'].lower(): raise SystemExit(f"{item['font_id']}: SHA-256 不匹配")
            dest=target/source.name
            if dest.exists() and hashlib.sha256(dest.read_bytes()).hexdigest()!=actual: raise SystemExit(f'{dest} 已存在不同内容，拒绝覆盖')
            if not dest.exists(): shutil.copy2(source,dest)
            label=f"{item['family_name']} (TrueType)";winreg.SetValueEx(key,label,0,winreg.REG_SZ,str(dest))
            ctypes.windll.gdi32.AddFontResourceExW(str(dest),0x10,0)
            installed.append({'font_id':item['font_id'],'path':str(dest),'postscript_name':item['postscript_name'],'sha256':actual})
    HWND_BROADCAST=0xffff;WM_FONTCHANGE=0x001D;ctypes.windll.user32.SendMessageTimeoutW(HWND_BROADCAST,WM_FONTCHANGE,0,0,0x0002,1000,None)
    log=root/'06_logs/font_installation.json';log.parent.mkdir(parents=True,exist_ok=True);log.write_text(json.dumps({'installed':installed,'photoshop_restart_required':True},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'installed':installed,'photoshop_restart_required':True,'next_action':'重启或刷新 Photoshop 后调用 ps_list_fonts 验证全部 postscript_name'},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
