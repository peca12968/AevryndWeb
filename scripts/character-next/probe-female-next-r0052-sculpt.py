"""Probe actual native sculpt operator/brush context without saving geometry."""
from pathlib import Path
import bpy,importlib.util,json,time
sp=importlib.util.spec_from_file_location('native52',Path(__file__).with_name('inspect-female-next-r0052-native-groom.py'))
k=importlib.util.module_from_spec(sp);sp.loader.exec_module(k)

def props(rna):
    rows={}
    for p in rna.properties:
        row={'type':p.type,'readonly':p.is_readonly}
        if p.type=='ENUM':row['items']=[v.identifier for v in p.enum_items]
        rows[p.identifier]=row
    return rows

def main():
    bpy.ops.wm.open_mainfile(filepath=str(k.SRC));o=bpy.data.objects['AFN33_C_BODY_BOUND_FIBRES'];o.hide_set(False)
    for ob in bpy.context.view_layer.objects:ob.select_set(False)
    o.select_set(True);bpy.context.view_layer.objects.active=o;o.data.surface=bpy.data.objects[k.b.BODY]
    o.data.surface_uv_map=o.data.surface.data.uv_layers[0].name
    lib=Path(r'D:\SteamLibrary\steamapps\common\Blender\5.2\datafiles\assets\brushes\essentials_brushes-curve_sculpt.blend')
    with bpy.data.libraries.load(str(lib),link=False) as (src,dst):names=src.brushes[:]
    bpy.ops.object.mode_set(mode='SCULPT_CURVES')
    brushName=next(n for n in names if 'Comb' in n)
    result=bpy.ops.brush.asset_activate(asset_library_type='ESSENTIALS',relative_asset_identifier='brushes/essentials_brushes-curve_sculpt.blend/Brush/'+brushName)
    settings=bpy.context.scene.tool_settings.curves_sculpt;brush=settings.brush
    rows={'brushNames':names,'activatedBrush':brushName,'activation':list(result),
          'brushProps':props(brush.bl_rna),'curvesBrushProps':props(brush.curves_sculpt_settings.bl_rna),
          'strokeOperator':props(bpy.ops.sculpt_curves.brush_stroke.get_rna_type()),
          'screen':bpy.context.screen.name if bpy.context.screen else None,
          'areas':[(a.type,[(r.type,r.width,r.height) for r in a.regions]) for a in bpy.context.screen.areas] if bpy.context.screen else None,
          'window':str(bpy.context.window),'mode':bpy.context.mode}
    k.save('native-sculpt-context.json',rows)
    print('R52_NATIVE_SCULPT',brushName,result,'brushfields',list(rows['curvesBrushProps']),'areas',rows['areas'],flush=True)

if __name__=='__main__':main()
