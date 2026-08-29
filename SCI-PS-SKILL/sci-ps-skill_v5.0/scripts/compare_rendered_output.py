from pathlib import Path
import argparse
import hashlib
import json
from PIL import Image, ImageChops, ImageStat


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("project_root")
    parser.add_argument("reference_png")
    parser.add_argument("rendered_png")
    parser.add_argument("--mae-threshold", type=float, default=0.0)
    parser.add_argument("--mismatch-ratio-threshold", type=float, default=0.0)
    args=parser.parse_args()
    root=Path(args.project_root).resolve(); ref_path=Path(args.reference_png).resolve(); out_path=Path(args.rendered_png).resolve()
    ref=Image.open(ref_path).convert("RGBA"); out=Image.open(out_path).convert("RGBA")
    issues=[]
    if ref.size != out.size:
        issues.append(f"尺寸不一致: reference={ref.size}, rendered={out.size}")
        metrics={"mae": None, "max_channel_error": None, "mismatch_pixel_ratio": None}
    else:
        diff=ImageChops.difference(ref,out)
        stat=ImageStat.Stat(diff)
        mae=sum(stat.mean)/len(stat.mean)
        extrema=diff.getextrema(); max_error=max(x[1] for x in extrema)
        mismatch=sum(1 for pixel in diff.getdata() if any(pixel))/float(ref.width*ref.height)
        metrics={"mae":mae,"max_channel_error":max_error,"mismatch_pixel_ratio":mismatch}
        if mae > args.mae_threshold: issues.append(f"MAE {mae:.6f} 超过阈值 {args.mae_threshold}")
        if mismatch > args.mismatch_ratio_threshold: issues.append(f"差异像素比例 {mismatch:.8f} 超过阈值 {args.mismatch_ratio_threshold}")
        diff_path=root/"04_photoshop"/"qa"/"pixel_difference.png"; diff_path.parent.mkdir(parents=True,exist_ok=True); diff.save(diff_path)
    evidence={"evidence_version":1,"reference_path":str(ref_path),"rendered_path":str(out_path),"reference_sha256":sha256(ref_path),"rendered_sha256":sha256(out_path),"reference_size":list(ref.size),"rendered_size":list(out.size),"thresholds":{"mae":args.mae_threshold,"mismatch_pixel_ratio":args.mismatch_ratio_threshold},"metrics":metrics,"pixel_comparison_passed":not issues,"issues":issues}
    path=root/"04_photoshop"/"qa"/"pixel_comparison_evidence.json"; path.write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding="utf-8")
    report_path=root/"04_photoshop"/"qa"/"VISUAL_DIFFERENCE_REPORT.json"
    if report_path.exists():
        report=json.loads(report_path.read_text(encoding="utf-8")); report["pixel_evidence_sha256"]=sha256(path); report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(evidence,ensure_ascii=False,indent=2))
    if issues: raise SystemExit(2)


if __name__ == "__main__": main()
