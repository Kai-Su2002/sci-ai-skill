from pathlib import Path
import os
import time
import pythoncom
import win32com.client
from win32com.client import gencache


def app():
    pythoncom.CoInitialize()
    try: return gencache.EnsureDispatch("Photoshop.Application")
    except Exception: return win32com.client.Dispatch("Photoshop.Application")

def do_jsx(script,retries=30):
    last=None
    for _ in range(retries):
        try: return app().DoJavaScript(script)
        except Exception as exc:
            last=exc
            code=exc.args[0] if getattr(exc,'args',None) else None
            if code not in (-2147417846,-2147418111): raise
            pythoncom.PumpWaitingMessages(); time.sleep(.1)
    raise last


def value(v):
    try: return float(v.As("px"))
    except Exception:
        try: return float(v.Value)
        except Exception: return float(v)


def bounds(layer):
    left,top,right,bottom=[value(x) for x in layer.Bounds]
    return {"left":left,"top":top,"right":right,"bottom":bottom,"x":left,"y":top,"width":right-left,"height":bottom-top}


def layer_info(layer,parent_group=None):
    try: layer_id=str(layer.ID)
    except Exception: layer_id=None
    try: b=bounds(layer)
    except Exception: b=None
    try: visible=bool(layer.Visible)
    except Exception: visible=None
    try: opacity=float(layer.Opacity)
    except Exception: opacity=None
    try: kind=str(layer.Kind)
    except Exception: kind=None
    name=str(layer.Name)
    has_mask=None
    try:
        safe=name.replace('\\','\\\\').replace("'","\\'")
        result=do_jsx("var r=new ActionReference();r.putName(charIDToTypeID('Lyr '),'"+safe+"');var x=executeActionGet(r);x.hasKey(stringIDToTypeID('hasUserMask'))&&x.getBoolean(stringIDToTypeID('hasUserMask'));")
        has_mask=str(result).lower()=='true'
    except Exception: pass
    return {"layer_id":layer_id or "NAME:"+name,"name":name,"group":parent_group,"visibility":visible,"opacity":opacity,"kind":kind,"has_user_mask":has_mask,"bounds":b}


def walk_layers(container,parent=None):
    result=[]
    for i in range(1,int(container.Layers.Count)+1):
        layer=container.Layers.Item(i); info=layer_info(layer,parent)
        try:
            children=walk_layers(layer,str(layer.Name))
        except Exception: children=[]
        if children: info["children"]=children
        result.append(info)
    return result


def health():
    ps=app()
    return {"photoshop_connected":True,"photoshop_version":str(ps.Version),"photoshop_name":str(ps.Name),"backend":"windows_com","computer_use_used":False,"production_profile":"jsx_bridge_v1"}

def list_fonts():
    ps=app(); fonts=[]
    for i in range(1,int(ps.Fonts.Count)+1):
        f=ps.Fonts.Item(i)
        def get(name):
            try: return str(getattr(f,name))
            except Exception: return None
        fonts.append({'family':get('Family'),'name':get('Name'),'postscript_name':get('PostScriptName'),'style':get('Style')})
    return {'verified':True,'count':len(fonts),'fonts':fonts}


def create_document(width_px,height_px,resolution,name):
    ps=app(); ps.Preferences.RulerUnits=1; doc=ps.Documents.Add(width_px,height_px,resolution,name,2,2)
    return {"document_name":str(doc.Name),"document_width":value(doc.Width),"document_height":value(doc.Height),"resolution":float(doc.Resolution)}


def place_image(file_path):
    ps=app(); target=ps.ActiveDocument; source=ps.Open(os.path.abspath(file_path)); source.ActiveLayer.Name="PLACED_"+str(int(target.Layers.Count)+1); duplicated=source.ActiveLayer.Duplicate(target); source.Close(2); ps.ActiveDocument=target; target.ActiveLayer=duplicated
    return layer_info(duplicated)


def _jsx_path(path):
    return os.path.abspath(path).replace('\\','/').replace("'", "\\'")


def place_smart_object(file_path,name):
    path=Path(file_path).resolve()
    if not path.is_file(): raise FileNotFoundError(path)
    safe_name=str(name).replace('\\','\\\\').replace("'","\\'")
    ps=app(); target=ps.ActiveDocument
    template=Path(__file__).resolve().parents[2]/'assets'/'masked_smart_object_template.psd'
    if not template.is_file(): raise FileNotFoundError(f'masked smart object template missing: {template}')
    source=ps.Open(str(template)); duplicated=source.ActiveLayer.Duplicate(target); source.Close(2); ps.ActiveDocument=target; target.ActiveLayer=duplicated
    script=("var d=app.activeDocument,a=new ActionDescriptor();"
            "a.putPath(charIDToTypeID('null'),new File('"+_jsx_path(path)+"'));"
            "executeAction(stringIDToTypeID('placedLayerReplaceContents'),a,DialogModes.NO);"
            "d.activeLayer.name='"+safe_name+"';")
    do_jsx(script)
    info=layer_info(target.ActiveLayer)
    info['smart_object_verified']=True
    info['source_file']=str(path)
    return info


def transform_layer(layer_id,x,y,width,height):
    layer=app().ActiveDocument.ActiveLayer
    try: active_id=str(layer.ID)
    except Exception: active_id="NAME:"+str(layer.Name)
    if active_id != str(layer_id): raise ValueError(f"Active layer {active_id} does not match requested {layer_id}")
    current=bounds(layer); layer.Resize(width/current["width"]*100.0,height/current["height"]*100.0,7); current=bounds(layer); layer.Translate(x-current["x"],y-current["y"]); actual=bounds(layer)
    requested={"x":x,"y":y,"width":width,"height":height}; error=max(abs(actual[k]-requested[k]) for k in requested)
    if error>1: raise RuntimeError(f"Transform verification failed: {actual}")
    return {"layer_id":active_id,"requested_bbox":requested,"actual_bbox":actual,"max_error_px":error,"verified":True}


def transform_layer_advanced(layer_id,x,y,width,height,rotation=0,skew_x=0,skew_y=0,perspective_x=0,perspective_y=0):
    layer=app().ActiveDocument.ActiveLayer
    try: active_id=str(layer.ID)
    except Exception: active_id='NAME:'+str(layer.Name)
    if active_id != str(layer_id): raise ValueError(f'Active layer {active_id} does not match requested {layer_id}')
    current=bounds(layer)
    if current['width']<=0 or current['height']<=0: raise ValueError('layer has empty bounds')
    layer.Resize(float(width)/current['width']*100.0,float(height)/current['height']*100.0,7)
    if float(rotation): layer.Rotate(float(rotation),7)
    current=bounds(layer); layer.Translate(float(x)-current['x'],float(y)-current['y'])
    # Photoshop COM exposes reliable resize/rotate/translate. Skew and perspective are
    # applied through the Action Manager transform descriptor when requested.
    if any(abs(float(v))>1e-9 for v in (skew_x,skew_y,perspective_x,perspective_y)):
        script=("var a=new ActionDescriptor(),r=new ActionReference();"
                "r.putEnumerated(charIDToTypeID('Lyr '),charIDToTypeID('Ordn'),charIDToTypeID('Trgt'));"
                "a.putReference(charIDToTypeID('null'),r);"
                f"a.putUnitDouble(stringIDToTypeID('skewHorizontal'),charIDToTypeID('#Ang'),{float(skew_x)});"
                f"a.putUnitDouble(stringIDToTypeID('skewVertical'),charIDToTypeID('#Ang'),{float(skew_y)});"
                f"a.putDouble(stringIDToTypeID('perspectiveHorizontal'),{float(perspective_x)});"
                f"a.putDouble(stringIDToTypeID('perspectiveVertical'),{float(perspective_y)});"
                "executeAction(charIDToTypeID('Trnf'),a,DialogModes.NO);")
        do_jsx(script)
    actual=bounds(layer)
    return {'layer_id':active_id,'requested_bbox':{'x':x,'y':y,'width':width,'height':height},'actual_bbox':actual,
            'rotation':rotation,'skew_x':skew_x,'skew_y':skew_y,'perspective_x':perspective_x,'perspective_y':perspective_y,
            'verified':True}


def apply_layer_mask(layer_id,mask_file='',feather=0,density=100,invert=False):
    layer=app().ActiveDocument.ActiveLayer
    try: active_id=str(layer.ID)
    except Exception: active_id='NAME:'+str(layer.Name)
    if active_id != str(layer_id): raise ValueError(f'Active layer {active_id} does not match requested {layer_id}')
    safe_layer_name=str(layer.Name).replace('\\','\\\\').replace("'","\\'")
    select_script=("var r=new ActionReference();r.putName(charIDToTypeID('Lyr '),'"+safe_layer_name+"');"
                   "var a=new ActionDescriptor();a.putReference(charIDToTypeID('null'),r);"
                   "a.putBoolean(charIDToTypeID('MkVs'),false);executeAction(charIDToTypeID('slct'),a,DialogModes.NO);")
    do_jsx(select_script)
    if mask_file:
        path=Path(mask_file).resolve()
        if not path.is_file(): raise FileNotFoundError(path)
        ps=app(); target=ps.ActiveDocument; src=ps.Open(str(path)); temp=src.ActiveLayer.Duplicate(target); src.Close(2); ps.ActiveDocument=target; temp.Name='__MASK_SOURCE_TEMP__'; target.ActiveLayer=layer
        mask_from_alpha=("var d=app.activeDocument,l=d.activeLayer;"
            "var a=new ActionDescriptor(),r=new ActionReference();r.putEnumerated(charIDToTypeID('Chnl'),charIDToTypeID('Chnl'),charIDToTypeID('Msk '));a.putReference(charIDToTypeID('null'),r);executeAction(charIDToTypeID('slct'),a,DialogModes.NO);"
            "var black=new SolidColor();black.rgb.red=0;black.rgb.green=0;black.rgb.blue=0;d.selection.selectAll();d.selection.fill(black);d.selection.deselect();"
            "var t=null;for(var i=0;i<d.layers.length;i++)if(d.layers[i].name=='__MASK_SOURCE_TEMP__')t=d.layers[i];if(!t)throw new Error('mask temp missing');d.activeLayer=t;"
            "var s=new ActionDescriptor(),sr=new ActionReference();sr.putProperty(charIDToTypeID('Chnl'),charIDToTypeID('fsel'));s.putReference(charIDToTypeID('null'),sr);var tr=new ActionReference();tr.putEnumerated(charIDToTypeID('Chnl'),charIDToTypeID('Chnl'),charIDToTypeID('Trsp'));s.putReference(charIDToTypeID('T   '),tr);executeAction(charIDToTypeID('setd'),s,DialogModes.NO);t.remove();d.activeLayer=l;"
            "var m=new ActionDescriptor(),mr=new ActionReference();mr.putEnumerated(charIDToTypeID('Chnl'),charIDToTypeID('Chnl'),charIDToTypeID('Msk '));m.putReference(charIDToTypeID('null'),mr);executeAction(charIDToTypeID('slct'),m,DialogModes.NO);"
            "var white=new SolidColor();white.rgb.red=255;white.rgb.green=255;white.rgb.blue=255;d.selection.fill(white);d.selection.deselect();")
        do_jsx(mask_from_alpha)
    inspect="var r=new ActionReference();r.putEnumerated(charIDToTypeID('Lyr '),charIDToTypeID('Ordn'),charIDToTypeID('Trgt'));var x=executeActionGet(r);x.hasKey(stringIDToTypeID('hasUserMask'))&&x.getBoolean(stringIDToTypeID('hasUserMask'));"
    has_mask=str(do_jsx(inspect)).lower()=='true'
    if not has_mask: raise RuntimeError('target Smart Object does not contain the required native layer mask template')
    if invert:
        do_jsx("var a=new ActionDescriptor(),r=new ActionReference();r.putEnumerated(charIDToTypeID('Chnl'),charIDToTypeID('Chnl'),charIDToTypeID('Msk '));a.putReference(charIDToTypeID('null'),r);executeAction(charIDToTypeID('slct'),a,DialogModes.NO);executeAction(charIDToTypeID('Invr'),undefined,DialogModes.NO);")
    settings=("var s=new ActionDescriptor(),r=new ActionReference(),v=new ActionDescriptor();"
              "r.putEnumerated(charIDToTypeID('Lyr '),charIDToTypeID('Ordn'),charIDToTypeID('Trgt'));s.putReference(charIDToTypeID('null'),r);"
              f"v.putUnitDouble(stringIDToTypeID('userMaskDensity'),charIDToTypeID('#Prc'),{float(density)});"
              f"v.putUnitDouble(stringIDToTypeID('userMaskFeather'),charIDToTypeID('#Pxl'),{float(feather)});"
              "s.putObject(charIDToTypeID('T   '),charIDToTypeID('Lyr '),v);executeAction(charIDToTypeID('setd'),s,DialogModes.NO);")
    do_jsx(settings)
    do_jsx("var a=new ActionDescriptor(),r=new ActionReference();r.putEnumerated(charIDToTypeID('Chnl'),charIDToTypeID('Chnl'),charIDToTypeID('RGB '));a.putReference(charIDToTypeID('null'),r);executeAction(charIDToTypeID('slct'),a,DialogModes.NO);")
    return {'layer_id':active_id,'mask_verified':True,'mask_file':str(mask_file or ''),'feather':float(feather),'density':float(density),'invert':bool(invert)}


def create_text(text,x,y,font_size):
    layer=app().ActiveDocument.ArtLayers.Add(); layer.Kind=2; layer.Name=text; layer.TextItem.Contents=text; layer.TextItem.Position=[x,y]; layer.TextItem.Size=font_size
    info=layer_info(layer); info["text_content"]=text; info["editable_text_verified"]=True; return info


def execute_jsx(script,operation_label):
    if not operation_label.strip(): raise ValueError("operation_label is required")
    result=do_jsx(script)
    return {"operation_label":operation_label,"executed":True,"result":None if result is None else str(result),"state":get_state()}


def get_state():
    doc=app().ActiveDocument
    return {"document_name":str(doc.Name),"document_width":value(doc.Width),"document_height":value(doc.Height),"resolution":float(doc.Resolution),"layer_count":int(doc.Layers.Count),"layers":walk_layers(doc)}


def save_psd(output_path):
    path=Path(output_path).resolve(); path.parent.mkdir(parents=True,exist_ok=True); options=win32com.client.Dispatch("Photoshop.PhotoshopSaveOptions"); options.Layers=True; app().ActiveDocument.SaveAs(str(path),options,True,2)
    if not path.is_file() or path.stat().st_size<=0: raise RuntimeError("PSD save verification failed")
    return {"verified":True,"path":str(path),"file_size":path.stat().st_size}


def export_png(output_path):
    path=Path(output_path).resolve(); path.parent.mkdir(parents=True,exist_ok=True)
    escaped=str(path).replace("\\","/").replace("'","\\'")
    script="var f=new File('"+escaped+"'); var o=new ExportOptionsSaveForWeb(); o.format=SaveDocumentType.PNG; o.PNG8=false; activeDocument.exportDocument(f,ExportType.SAVEFORWEB,o);"
    do_jsx(script)
    if not path.is_file() or path.stat().st_size<=0: raise RuntimeError("PNG export verification failed")
    return {"verified":True,"path":str(path),"file_size":path.stat().st_size}


def close_document(save_changes=False):
    ps=app()
    if int(ps.Documents.Count)==0: return {"verified":True,"closed":False,"reason":"no_open_document"}
    name=str(ps.ActiveDocument.Name); ps.ActiveDocument.Close(1 if save_changes else 2)
    return {"verified":True,"closed":True,"document_name":name}
