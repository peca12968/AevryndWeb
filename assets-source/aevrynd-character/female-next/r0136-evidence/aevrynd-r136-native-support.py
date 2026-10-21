import bpy,json,os
def props(rna):
 return {p.identifier:{'type':p.type,'enum':[(i.identifier,i.name) for i in p.enum_items] if p.type=='ENUM' else None} for p in rna.properties}
print('SUPPORT136',json.dumps({'background':bpy.app.background,'areas':[(a.type,len(a.regions)) for a in bpy.context.screen.areas],'sculptCurveOps':dir(bpy.ops.sculpt_curves),'stroke':props(bpy.ops.sculpt_curves.brush_stroke.get_rna_type()),'brushAsset':props(bpy.ops.brush.asset_activate.get_rna_type()),'mode':props(bpy.ops.object.mode_set.get_rna_type())['mode'],'toolsettings':[(p.identifier,p.type) for p in bpy.context.tool_settings.bl_rna.properties if 'curv' in p.identifier],'essentials':bpy.utils.resource_path('LOCAL')},default=str),flush=True)
path='D:/SteamLibrary/steamapps/common/Blender/5.2/datafiles/assets/brushes/essentials_brushes-curves_sculpt.blend'
if os.path.isfile(path):
 with bpy.data.libraries.load(path,link=False) as (s,d):print('NATIVE_CURVE_BRUSHES',s.brushes,flush=True)
if hasattr(bpy.context.tool_settings,'curves_sculpt'):print('CURVE_SETTINGS',props(bpy.context.tool_settings.curves_sculpt.bl_rna),flush=True)
