import bpy,json,math,numpy as np
from mathutils import Vector,Quaternion
from bpy_extras.view3d_utils import location_3d_to_region_2d
path='D:/SteamLibrary/steamapps/common/Blender/5.2/datafiles/assets/brushes/essentials_brushes-curve_sculpt.blend'
with bpy.data.libraries.load(path,link=False) as (s,d):print('NATIVE_BRUSH_ASSETS',s.brushes,flush=True)
d=bpy.data.hair_curves.new('ActualNativeCombTest');d.add_curves([17]*5);P=np.array([[i*.025,0,j*.025] for i in range(5) for j in range(17)],'f4');d.position_data.foreach_set('vector',P.ravel());o=bpy.data.objects.new('ActualNativeCombTest',d);bpy.context.scene.collection.objects.link(o)
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.mode_set(mode='SCULPT_CURVES')
area=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D');reg=next(r for r in area.regions if r.type=='WINDOW');rv=area.spaces.active.region_3d;rv.view_rotation=Quaternion((1,0,0),math.pi/2);rv.view_location=Vector((.05,0,.2));rv.view_distance=1.;rv.view_perspective='ORTHO';rv.update()
with bpy.context.temp_override(area=area,region=reg):
 print('ACTIVATE',bpy.ops.brush.asset_activate(asset_library_type='ESSENTIALS',relative_asset_identifier='brushes/essentials_brushes-curve_sculpt.blend/Brush/Comb'),flush=True)
 st=bpy.context.tool_settings.curves_sculpt;br=st.brush;br.size=200;br.strength=1.
 print('CURVE_SETTINGS',[(p.identifier,p.type) for p in st.bl_rna.properties],flush=True)
 print('BRUSH',br.name,[(p.identifier,p.type) for p in br.curves_sculpt_settings.bl_rna.properties],flush=True)
 print('REGION',reg.width,reg.height,'POLL',bpy.ops.sculpt_curves.brush_stroke.poll(),flush=True)
 a=location_3d_to_region_2d(reg,rv,Vector((.05,0,.2)));b=location_3d_to_region_2d(reg,rv,Vector((.25,0,.3)))
 print('PROJECTION',list(a),list(b),flush=True)
 strokes=[{'mouse':tuple(a.lerp(b,t)), 'pressure':1.,'size':200,'time':i*.03,'is_start':i==0,'location':(.05,0,.2),'mouse_event':tuple(a.lerp(b,t)),'x_tilt':0.,'y_tilt':0.} for i,t in enumerate(np.linspace(0,1,10))]
 print('STROKE',bpy.ops.sculpt_curves.brush_stroke(stroke=strokes),flush=True)
 out=np.empty(P.shape,'f4');d.position_data.foreach_get('vector',out.ravel());print('ACTUAL_NATIVE_COMB_MAX_DELTA',float(np.linalg.norm(out-P,axis=1).max()),flush=True)
 print('NATIVE_CURVE_COMB_TEST_COMPLETE',flush=True)
