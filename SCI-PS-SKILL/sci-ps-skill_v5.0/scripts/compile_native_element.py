import json,math

SUPPORTED={"TEXT","RECTANGLE","ELLIPSE","LINE","ARROW","CURVED_ARROW","SOLID_BACKGROUND","GLOW","SHADOW","BLUR","GRADIENT_LINEAR","GRADIENT_RADIAL","ADJUSTMENT_LEVELS","ADJUSTMENT_HUE_SATURATION","ADJUSTMENT_BRIGHTNESS_CONTRAST","COMPLEX_PATH","VECTOR_SHAPE"}

def q(value): return json.dumps(str(value),ensure_ascii=False)

def rgb(value):
    value=str(value).lstrip("#")
    if len(value)!=6: raise ValueError("color must be #RRGGBB")
    return tuple(int(value[i:i+2],16) for i in (0,2,4))

def find_layer_script(name):
    return f"function F(c,n){{for(var i=0;i<c.layers.length;i++){{var z=c.layers[i];if(z.name==n)return z;try{{var r=F(z,n);if(r)return r;}}catch(e){{}}}}return null;}}var src=F(d,{q(name)});if(!src)throw new Error('source layer missing');"

def color_script(color,var="c"):
    r,g,b=rgb(color); return f"var {var}=new SolidColor();{var}.rgb.red={r};{var}.rgb.green={g};{var}.rgb.blue={b};"

def compile_native(layer):
    kind=str(layer.get("native_type") or layer.get("type") or "").upper()
    spec=layer.get("build_spec") or {}; bbox=spec.get("bbox"); params=spec.get("parameters") or {}
    if kind not in SUPPORTED: raise ValueError(f"unsupported native type: {kind}")
    if not isinstance(bbox,list) or len(bbox)!=4: raise ValueError("native bbox required")
    name=q(layer["name"]); group=q(layer["group"]); opacity=float(spec["opacity"]); blend=q(spec["blend_mode"])
    common=f"l.name={name};l.opacity={opacity};try{{l.blendMode=BlendMode[{blend}.toUpperCase()];}}catch(e){{}}var g=null;for(var i=0;i<d.layerSets.length;i++)if(d.layerSets[i].name=={group})g=d.layerSets[i];if(!g){{g=d.layerSets.add();g.name={group};}}if(l.parent!=g)l.move(g,ElementPlacement.INSIDE);"
    if kind=="TEXT":
        color=rgb(params["color"]); text=q(params["text"]); font=q(params["font"]); size=float(params["font_size"]); x,y=bbox[0],bbox[1]
        align=str(params.get("alignment","LEFT")).upper(); tracking=float(params.get("tracking",0)); leading=float(params.get("leading",size*1.2))
        direction=str(params.get("direction","HORIZONTAL")).upper(); anti=str(params.get("anti_alias","SHARP")).upper(); hscale=float(params.get("horizontal_scale",100)); vscale=float(params.get("vertical_scale",100)); baseline=float(params.get("baseline_shift",0)); faux_bold=str(bool(params.get("faux_bold",False))).lower(); faux_italic=str(bool(params.get("faux_italic",False))).lower()
        box=params.get("text_box")
        body=f"var d=app.activeDocument,l=d.artLayers.add();l.kind=LayerKind.TEXT;var t=l.textItem;t.contents={text};t.position=[{x},{y}];t.size={size};t.font={font};t.tracking={tracking};t.useAutoLeading=false;t.leading={leading};try{{t.justification=Justification.{align};}}catch(e){{}}try{{t.direction=Direction.{direction};}}catch(e){{}}try{{t.antiAliasMethod=AntiAlias.{anti};}}catch(e){{}}try{{t.horizontalScale={hscale};t.verticalScale={vscale};t.baselineShift={baseline};t.fauxBold={faux_bold};t.fauxItalic={faux_italic};}}catch(e){{}}var c=new SolidColor();c.rgb.red={color[0]};c.rgb.green={color[1]};c.rgb.blue={color[2]};t.color=c;"
        if isinstance(box,list) and len(box)==2: body+=f"try{{t.kind=TextType.PARAGRAPHTEXT;t.width={float(box[0])};t.height={float(box[1])};}}catch(e){{}}"
    elif kind in {"GLOW","SHADOW","BLUR"}:
        source=params["source_layer"]; radius=float(params["radius"]); dx=float(params.get("offset_x",0)); dy=float(params.get("offset_y",0))
        body="var d=app.activeDocument;"+find_layer_script(source)+"var l=src.duplicate();d.activeLayer=l;try{l.rasterize(RasterizeType.ENTIRELAYER);}catch(e){}l.applyGaussianBlur("+str(radius)+");"
        if kind in {"GLOW","SHADOW"} and params.get("color"):
            body+=color_script(params["color"])+"d.activeLayer=l;d.selection.selectAll();d.selection.fill(c,ColorBlendMode.NORMAL,100,true);d.selection.deselect();"
        if dx or dy: body+=f"l.translate({dx},{dy});"
    elif kind in {"ADJUSTMENT_LEVELS","ADJUSTMENT_HUE_SATURATION","ADJUSTMENT_BRIGHTNESS_CONTRAST"}:
        body="var d=app.activeDocument;"
        if kind=="ADJUSTMENT_LEVELS":
            ib=int(params.get('input_black',0)); iw=int(params.get('input_white',255)); gamma=float(params.get('gamma',1.0)); ob=int(params.get('output_black',0)); ow=int(params.get('output_white',255))
            body+=f"var a=new ActionDescriptor(),r=new ActionReference(),u=new ActionDescriptor(),t=new ActionDescriptor(),ad=new ActionList(),lv=new ActionDescriptor(),ch=new ActionReference(),inp=new ActionList(),outp=new ActionList();r.putClass(stringIDToTypeID('adjustmentLayer'));a.putReference(charIDToTypeID('null'),r);ch.putEnumerated(charIDToTypeID('Chnl'),charIDToTypeID('Chnl'),charIDToTypeID('Cmps'));lv.putReference(charIDToTypeID('Chnl'),ch);inp.putInteger({ib});inp.putInteger({iw});lv.putList(charIDToTypeID('Inpt'),inp);lv.putDouble(charIDToTypeID('Gmm '),{gamma});outp.putInteger({ob});outp.putInteger({ow});lv.putList(charIDToTypeID('Otpt'),outp);ad.putObject(charIDToTypeID('LvlA'),lv);t.putList(charIDToTypeID('Adjs'),ad);u.putObject(charIDToTypeID('Type'),charIDToTypeID('Lvls'),t);a.putObject(charIDToTypeID('Usng'),stringIDToTypeID('adjustmentLayer'),u);executeAction(charIDToTypeID('Mk  '),a,DialogModes.NO);var l=d.activeLayer;l.grouped={str(bool(params.get('clipped',False))).lower()};"
        else:
            event="hueSaturation" if kind=="ADJUSTMENT_HUE_SATURATION" else "brightnessEvent"
            values=(f"t.putInteger(stringIDToTypeID('hue'),{int(params.get('hue',0))});t.putInteger(stringIDToTypeID('saturation'),{int(params.get('saturation',0))});t.putInteger(stringIDToTypeID('lightness'),{int(params.get('lightness',0))});" if kind=="ADJUSTMENT_HUE_SATURATION" else f"t.putInteger(stringIDToTypeID('brightness'),{int(params.get('brightness',0))});t.putInteger(stringIDToTypeID('contrast'),{int(params.get('contrast',0))});")
            body+=f"var a=new ActionDescriptor(),r=new ActionReference(),u=new ActionDescriptor(),t=new ActionDescriptor();r.putClass(stringIDToTypeID('adjustmentLayer'));a.putReference(charIDToTypeID('null'),r);{values}u.putObject(charIDToTypeID('Type'),stringIDToTypeID('{event}'),t);a.putObject(charIDToTypeID('Usng'),stringIDToTypeID('adjustmentLayer'),u);executeAction(charIDToTypeID('Mk  '),a,DialogModes.NO);var l=d.activeLayer;l.grouped={str(bool(params.get('clipped',False))).lower()};"
    elif kind in {"GRADIENT_LINEAR","GRADIENT_RADIAL"}:
        c1=rgb(params["start_color"]); c2=rgb(params["end_color"]); left,top,right,bottom=map(float,bbox); steps=max(8,min(128,int(params.get("steps",64))))
        body="var d=app.activeDocument,l=d.artLayers.add();"
        for i in range(steps):
            t=i/(steps-1); col=tuple(round(c1[j]*(1-t)+c2[j]*t) for j in range(3)); body+=f"var c=new SolidColor();c.rgb.red={col[0]};c.rgb.green={col[1]};c.rgb.blue={col[2]};"
            if kind=="GRADIENT_LINEAR":
                y1=top+(bottom-top)*i/steps; y2=top+(bottom-top)*(i+1)/steps; body+=f"d.selection.select([[{left},{y1}],[{right},{y1}],[{right},{y2}],[{left},{y2}]]);d.selection.fill(c);"
            else:
                inset=(i/steps)*.5; x1=left+(right-left)*inset; x2=right-(right-left)*inset; y1=top+(bottom-top)*inset; y2=bottom-(bottom-top)*inset
                body+=f"var a=new ActionDescriptor(),r=new ActionReference(),e=new ActionDescriptor();r.putProperty(charIDToTypeID('Chnl'),charIDToTypeID('fsel'));a.putReference(charIDToTypeID('null'),r);e.putUnitDouble(charIDToTypeID('Top '),charIDToTypeID('#Pxl'),{y1});e.putUnitDouble(charIDToTypeID('Left'),charIDToTypeID('#Pxl'),{x1});e.putUnitDouble(charIDToTypeID('Btom'),charIDToTypeID('#Pxl'),{y2});e.putUnitDouble(charIDToTypeID('Rght'),charIDToTypeID('#Pxl'),{x2});a.putObject(charIDToTypeID('T   '),charIDToTypeID('Elps'),e);executeAction(charIDToTypeID('setd'),a,DialogModes.NO);d.selection.fill(c);"
        body+="d.selection.deselect();"
    elif kind in {"COMPLEX_PATH","CURVED_ARROW","VECTOR_SHAPE"}:
        points=params["points"]; color=params["stroke_color"]; width=float(params["stroke_width"]); closed="true" if params.get("closed") else "false"
        if len(points)<2: raise ValueError("complex path requires at least two points")
        path_name=str(layer['name'])+'_PATH'; body="var d=app.activeDocument,spi=new SubPathInfo(),pp=[];"
        body+=f"spi.closed={closed};spi.operation=ShapeOperation.SHAPEADD;"
        for p in points:
            a=p['anchor']; left=p.get('left',a); right=p.get('right',a)
            body+=f"var q=new PathPointInfo();q.kind=PointKind.SMOOTHPOINT;q.anchor=[{float(a[0])},{float(a[1])}];q.leftDirection=[{float(left[0])},{float(left[1])}];q.rightDirection=[{float(right[0])},{float(right[1])}];pp.push(q);"
        body+=f"spi.entireSubPath=pp;var pth=d.pathItems.add({q(path_name)},[spi]);var l=d.artLayers.add();"+color_script(color)+"app.foregroundColor=c;d.activeLayer=l;pth.strokePath(ToolType.BRUSH);"
        if kind=="VECTOR_SHAPE" and params.get("fill_color"):
            body+=color_script(params["fill_color"],"fc")+"pth.makeSelection(0,true,SelectionType.REPLACE);d.selection.fill(fc);d.selection.deselect();"
        if kind=="CURVED_ARROW":
            end=points[-1]["anchor"]; prev=points[-1].get("left") or points[-2]["anchor"]; dx=float(end[0])-float(prev[0]);dy=float(end[1])-float(prev[1]);ln=math.hypot(dx,dy)
            if ln<=0: raise ValueError("curved arrow tangent invalid")
            ux,uy=dx/ln,dy/ln; hs=float(params.get("head_size",max(width*4,8))); bx=float(end[0])-ux*hs;by=float(end[1])-uy*hs;hx=-uy*hs*.55;hy=ux*hs*.55
            poly=[[end[0],end[1]],[bx+hx,by+hy],[bx-hx,by-hy]];pts=",".join(f"[{p[0]},{p[1]}]" for p in poly);body+=f"d.selection.select([{pts}]);d.selection.fill(c);d.selection.deselect();"
    elif kind in {"RECTANGLE","ELLIPSE","SOLID_BACKGROUND"}:
        color=rgb(params["fill_color"]); left,top,right,bottom=bbox
        select=("d.selection.select([[{0},{1}],[{2},{1}],[{2},{3}],[{0},{3}]])".format(left,top,right,bottom) if kind!="ELLIPSE" else f"var a=new ActionDescriptor(),r=new ActionReference(),e=new ActionDescriptor();r.putProperty(charIDToTypeID('Chnl'),charIDToTypeID('fsel'));a.putReference(charIDToTypeID('null'),r);e.putUnitDouble(charIDToTypeID('Top '),charIDToTypeID('#Pxl'),{top});e.putUnitDouble(charIDToTypeID('Left'),charIDToTypeID('#Pxl'),{left});e.putUnitDouble(charIDToTypeID('Btom'),charIDToTypeID('#Pxl'),{bottom});e.putUnitDouble(charIDToTypeID('Rght'),charIDToTypeID('#Pxl'),{right});a.putObject(charIDToTypeID('T   '),charIDToTypeID('Elps'),e);executeAction(charIDToTypeID('setd'),a,DialogModes.NO)")
        body=f"var d=app.activeDocument,l=d.artLayers.add();var c=new SolidColor();c.rgb.red={color[0]};c.rgb.green={color[1]};c.rgb.blue={color[2]};{select};d.selection.fill(c);d.selection.deselect();"
    else:
        points=params.get("points"); color=rgb(params["stroke_color"]); width=float(params["stroke_width"])
        if not isinstance(points,list) or len(points)<2: raise ValueError("line/arrow points required")
        x1,y1=map(float,points[0]); x2,y2=map(float,points[-1]); dx=x2-x1; dy=y2-y1; length=math.hypot(dx,dy)
        if length<=0 or width<=0: raise ValueError("line geometry invalid")
        nx=-dy/length*width/2; ny=dx/length*width/2
        polygon=[[x1+nx,y1+ny],[x2+nx,y2+ny],[x2-nx,y2-ny],[x1-nx,y1-ny]]
        if kind=="ARROW":
            head=float(params.get("head_size",max(width*4,8))); ux=dx/length; uy=dy/length; bx=x2-ux*head; by=y2-uy*head; hx=-uy*head*.55; hy=ux*head*.55
            polygon=[[x1+nx,y1+ny],[bx+nx,by+ny],[bx+hx,by+hy],[x2,y2],[bx-hx,by-hy],[bx-nx,by-ny],[x1-nx,y1-ny]]
        pts=",".join(f"[{p[0]},{p[1]}]" for p in polygon)
        body=f"var d=app.activeDocument,l=d.artLayers.add();var c=new SolidColor();c.rgb.red={color[0]};c.rgb.green={color[1]};c.rgb.blue={color[2]};d.selection.select([{pts}]);d.selection.fill(c);d.selection.deselect();"
    return body+common
