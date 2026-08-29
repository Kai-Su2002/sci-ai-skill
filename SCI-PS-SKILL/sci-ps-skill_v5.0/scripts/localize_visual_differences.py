from pathlib import Path
import argparse, json, hashlib
from collections import deque
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageStat

def load(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def flatten(layers):
    out=[]
    for layer in layers or []:
        out.append(layer)
        out.extend(flatten(layer.get('children')))
    return out

def bounds(layer):
    b=layer.get('bounds')
    if isinstance(b,dict): return [b.get('left',b.get('x')),b.get('top',b.get('y')),b.get('right',b.get('x',0)+b.get('width',0)),b.get('bottom',b.get('y',0)+b.get('height',0))]
    return None

def overlap(a,b):
    x=max(0,min(a[2],b[2])-max(a[0],b[0])); y=max(0,min(a[3],b[3])-max(a[1],b[1]))
    return x*y

def regions(mask,min_area):
    w,h=mask.size; px=mask.load(); seen=set(); result=[]
    for y in range(h):
        for x in range(w):
            if not px[x,y] or (x,y) in seen: continue
            q=deque([(x,y)]);seen.add((x,y));xs=[];ys=[]
            while q:
                cx,cy=q.popleft();xs.append(cx);ys.append(cy)
                for nx,ny in ((cx-1,cy),(cx+1,cy),(cx,cy-1),(cx,cy+1)):
                    if 0<=nx<w and 0<=ny<h and px[nx,ny] and (nx,ny) not in seen: seen.add((nx,ny));q.append((nx,ny))
            if len(xs)>=min_area: result.append([min(xs),min(ys),max(xs)+1,max(ys)+1,len(xs)])
    return sorted(result,key=lambda r:r[4],reverse=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('project_root');p.add_argument('reference');p.add_argument('rendered');p.add_argument('--threshold',type=int,default=8);p.add_argument('--min-area',type=int,default=16);a=p.parse_args()
    root=Path(a.project_root).resolve(); rp=Path(a.reference).resolve(); op=Path(a.rendered).resolve()
    ref=Image.open(rp).convert('RGBA'); out=Image.open(op).convert('RGBA')
    if ref.size!=out.size: raise SystemExit('reference/rendered size mismatch')
    diff=ImageChops.difference(ref,out).convert('RGB'); gray=diff.convert('L')
    mask=gray.point(lambda v:255 if v>a.threshold else 0).filter(ImageFilter.MaxFilter(3))
    state_path=root/'04_photoshop/qa/photoshop_state.json'; state=load(state_path) if state_path.exists() else {'layers':[]}
    layers=[x for x in flatten(state.get('layers')) if x.get('visibility') is not False and bounds(x)]
    found=[]
    for i,r in enumerate(regions(mask,a.min_area),1):
        box=r[:4]; crop_diff=diff.crop(box); crop_ref=ref.crop(box).convert('RGB'); crop_out=out.crop(box).convert('RGB')
        dmean=sum(ImageStat.Stat(crop_diff).mean)/3; rb=ImageStat.Stat(crop_ref).mean; ob=ImageStat.Stat(crop_out).mean
        candidates=sorted(((overlap(box,bounds(x)),x.get('name')) for x in layers),reverse=True)
        candidates=[name for score,name in candidates if score>0][:5]
        category='COLOR_TONE'
        if dmean>50: category='GEOMETRY_OR_MISSING'
        elif abs(sum(rb)/3-sum(ob)/3)>12: category='BRIGHTNESS_CONTRAST'
        target=candidates[0] if len(candidates)==1 else None
        found.append({'id':f'DIFF_{i:04d}','bbox':box,'area_px':r[4],'mean_error':round(dmean,4),'category':category,
                      'candidate_layers':candidates,'target_layer':target,'auto_applicable':bool(target and category=='BRIGHTNESS_CONTRAST'),
                      'suggested_correction':{'action':'BRIGHTNESS_CONTRAST' if category=='BRIGHTNESS_CONTRAST' else 'MANUAL_LAYER_DIAGNOSIS_REQUIRED',
                        'parameters':{'brightness':round((sum(rb)-sum(ob))/3,2),'contrast':0} if category=='BRIGHTNESS_CONTRAST' else {}}})
    heat=Image.new('RGBA',ref.size,(0,0,0,0)); draw=ImageDraw.Draw(heat)
    for item in found: draw.rectangle(item['bbox'],outline=(255,0,0,255),width=2);draw.text((item['bbox'][0]+2,item['bbox'][1]+2),item['id'],fill=(255,255,0,255))
    heat_path=root/'04_photoshop/qa/difference_regions.png';heat_path.parent.mkdir(parents=True,exist_ok=True);heat.save(heat_path)
    report={'version':1,'reference_sha256':sha(rp),'rendered_sha256':sha(op),'threshold':a.threshold,'regions':found,
            'unresolved_count':len(found),'automatic_corrections':[x for x in found if x['auto_applicable']]}
    path=root/'04_photoshop/qa/difference_localization.json';path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(path)
    if found: raise SystemExit(2)
if __name__=='__main__': main()
