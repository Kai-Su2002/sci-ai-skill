from pathlib import Path
import argparse,re,shutil,subprocess,sys,venv

def main():
    p=argparse.ArgumentParser(); p.add_argument('--codex-home',default=str(Path.home()/'.codex')); args=p.parse_args(); src=Path(__file__).resolve().parents[1]; home=Path(args.codex_home).resolve(); dest=home/'skills'/src.name; runtime=home/'mcp'/'photoshop-production'; py=runtime/'.venv'/'Scripts'/'python.exe'
    subprocess.run([sys.executable,str(src/'scripts/verify_package.py')],check=True)
    if src != dest:
        if dest.exists(): shutil.rmtree(dest)
        shutil.copytree(src,dest,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    elif not (dest/'SKILL.md').is_file():
        raise RuntimeError('目标目录缺少 SKILL.md，拒绝继续安装')
    runtime.mkdir(parents=True,exist_ok=True)
    if not py.exists(): venv.EnvBuilder(with_pip=True).create(runtime/'.venv')
    subprocess.run([str(py),'-m','pip','install','-r',str(dest/'bootstrap/photoshop_mcp/requirements.txt')],check=True)
    cfg=home/'config.toml'; text=cfg.read_text(encoding='utf-8') if cfg.exists() else ''
    backup=cfg.with_suffix('.toml.backup_visual_recon'); backup.write_text(text,encoding='utf-8')
    text=re.sub(r'(?ms)^\[mcp_servers\.photoshop-mcp-production\]\s*.*?(?=^\[|\Z)','',text).rstrip()
    section=f"\n\n[mcp_servers.photoshop-mcp-production]\ncommand = '{str(py)}'\nargs = ['{str(dest/'bootstrap/photoshop_mcp/server.py')}']\n"
    cfg.parent.mkdir(parents=True,exist_ok=True); cfg.write_text(text+section,encoding='utf-8')
    print(f'INSTALLED_SKILL={dest}\nMCP_PYTHON={py}\nCONFIG={cfg}\nRESTART_CODEX_REQUIRED=YES')
if __name__=='__main__':main()
