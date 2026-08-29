from mcp.server.fastmcp import FastMCP
import photoshop_com as ps

mcp = FastMCP("photoshop-production")

@mcp.tool()
def ps_health(): return ps.health()

@mcp.tool()
def ps_list_fonts(): return ps.list_fonts()

@mcp.tool()
def ps_create_document(width_px:int,height_px:int,resolution:int,name:str): return ps.create_document(width_px,height_px,resolution,name)

@mcp.tool()
def ps_place_image(file_path:str): return ps.place_image(file_path)

@mcp.tool()
def ps_place_smart_object(file_path:str,name:str): return ps.place_smart_object(file_path,name)

@mcp.tool()
def ps_transform_layer(layer_id:str,x:float,y:float,width:float,height:float): return ps.transform_layer(layer_id,x,y,width,height)

@mcp.tool()
def ps_transform_layer_advanced(layer_id:str,x:float,y:float,width:float,height:float,rotation:float=0,skew_x:float=0,skew_y:float=0,perspective_x:float=0,perspective_y:float=0):
    return ps.transform_layer_advanced(layer_id,x,y,width,height,rotation,skew_x,skew_y,perspective_x,perspective_y)

@mcp.tool()
def ps_apply_layer_mask(layer_id:str,mask_file:str='',feather:float=0,density:float=100,invert:bool=False):
    return ps.apply_layer_mask(layer_id,mask_file,feather,density,invert)

@mcp.tool()
def ps_create_text(text:str,x:float,y:float,font_size:float): return ps.create_text(text,x,y,font_size)

@mcp.tool()
def ps_execute_jsx(script:str,operation_label:str): return ps.execute_jsx(script,operation_label)

@mcp.tool()
def ps_get_state(): return ps.get_state()

@mcp.tool()
def ps_save_psd(output_path:str): return ps.save_psd(output_path)

@mcp.tool()
def ps_export_png(output_path:str): return ps.export_png(output_path)

@mcp.tool()
def ps_close_document(save_changes:bool=False): return ps.close_document(save_changes)

if __name__ == "__main__": mcp.run(transport="stdio")
