from pathlib import Path
import argparse,json

def js(v): return json.dumps(str(v),ensure_ascii=False)
def find(name): return "function F(c,n){for(var i=0;i<c.layers.length;i++){var z=c.layers[i];if(z.name==n)return z;try{var r=F(z,n);if(r)return r;}catch(e){}}return null;}var d=app.activeDocument,l=F(d,"+js(name)+");if(!l)throw new Error('target layer missing');d.activeLayer=l;"

def main():
    p=argparse.ArgumentParser();p.add_argument('project_root');a=p.parse_args();root=Path(a.project_root).resolve()
    report=json.loads((root/'04_photoshop/qa/difference_localization.json').read_text(encoding='utf-8')); actions=[];seq=1
    for item in report.get('automatic_corrections',[]):
        target=item.get('target_layer'); corr=item.get('suggested_correction') or {}; kind=corr.get('action'); params=corr.get('parameters') or {}
        if not target: continue
        if kind=='BRIGHTNESS_CONTRAST':
            b=max(-150,min(150,float(params.get('brightness',0))));c=max(-100,min(100,float(params.get('contrast',0))))
            script=find(target)+(f"var a=new ActionDescriptor(),r=new ActionReference(),u=new ActionDescriptor(),t=new ActionDescriptor();"
                "r.putClass(stringIDToTypeID('adjustmentLayer'));a.putReference(charIDToTypeID('null'),r);"
                f"t.putInteger(stringIDToTypeID('brightness'),{int(round(b))});t.putInteger(stringIDToTypeID('contrast'),{int(round(c))});"
                "u.putObject(charIDToTypeID('Type'),stringIDToTypeID('brightnessEvent'),t);a.putObject(charIDToTypeID('Usng'),stringIDToTypeID('adjustmentLayer'),u);"
                "executeAction(charIDToTypeID('Mk  '),a,DialogModes.NO);var z=d.activeLayer;z.name='AUTO_FIX_"+item['id']+"';z.grouped=true;")
        else: continue
        actions.append({'sequence':seq,'tool':'ps_execute_jsx','args':{'script':script,'operation_label':'auto correction '+item['id']},'verify_with':'ps_get_state','difference_id':item['id']});seq+=1
    output={'fail_closed':True,'source_report':str(root/'04_photoshop/qa/difference_localization.json'),'actions':actions,'requires_recompare':True}
    path=root/'04_photoshop/manifests/correction_action_queue.json';path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8');print(path)
if __name__=='__main__': main()
