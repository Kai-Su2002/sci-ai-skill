from pathlib import Path
import argparse
import json
from PIL import Image


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("project_root")
    parser.add_argument("--width",type=int)
    parser.add_argument("--height",type=int)
    parser.add_argument("--resolution",type=int,default=72)
    parser.add_argument("--copy",default="")
    parser.add_argument("--fonts",nargs="*",default=[])
    parser.add_argument("--logos",nargs="*",default=[])
    args=parser.parse_args(); root=Path(args.project_root).resolve()
    refs=[p for p in (root/"00_reference").glob("reference_master.*") if p.is_file()]
    if len(refs)!=1: raise SystemExit(f"需要且只能有一个 reference_master.*，当前 {len(refs)} 个")
    with Image.open(refs[0]) as image: rw,rh=image.size
    width=args.width or rw; height=args.height or rh
    if width<=0 or height<=0 or args.resolution<=0: raise SystemExit("画布尺寸和分辨率必须为正数")
    data={"reference_file":str(refs[0].resolve()),"reference_size":{"width":rw,"height":rh},"canvas":{"width":width,"height":height,"resolution":args.resolution},"final_copy":args.copy,"fonts":args.fonts,"logos":args.logos,"spec_confirmed":True}
    path=root/"01_spec"/"project_manifest.json"; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    state_path=root/'.visual_recon/project_state.json'
    if state_path.exists():
        state=json.loads(state_path.read_text(encoding='utf-8')); state['state']='UNIVERSAL_IMAGE2_WEB_HANDOFF'; state['state_status']='PENDING'; state['last_completed_state']='PROJECT_INIT'; state['next_action']='PREPARE_WEB_HANDOFF'; state_path.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
    print(path)


if __name__=="__main__": main()
