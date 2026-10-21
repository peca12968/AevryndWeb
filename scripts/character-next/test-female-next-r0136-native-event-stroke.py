"""Bounded native Blender event-loop Comb capability test, not a character round."""
import bpy,numpy as np,math,traceback,json
from mathutils import Vector,Quaternion
from bpy_extras.view3d_utils import location_3d_to_region_2d
from pathlib import Path
E=Path('D:/Download/Aevrynd/Evidence/character-female-next/r0136-native-curve-combing');state={}
def timer():
 try:
  if not state:
   d=bpy.data.hair_curves.new('ActualEventCombTest');d.add_curves([17]*5);P=np.array([[i*.025,0,j*.025] for i in range(5) for j in range(17)],'f4');d.position_data.foreach_set('vector',P.ravel());o=bpy.data.objects.new('ActualEventCombTest',d);bpy.context.scene.collection.objects.link(o);bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.context.view_layer.update();bpy.ops.object.mode_set(mode='SCULPT_CURVES');win=bpy.context.window;area=next(a for a in win.screen.areas if a.type=='VIEW_3D');reg=next(r for r in area.regions if r.type=='WINDOW');rv=area.spaces.active.region_3d;rv.view_rotation=Quaternion((1,0,0),math.pi/2);rv.view_location=Vector((.05,0,.2));rv.view_distance=1.;rv.view_perspective='ORTHO';rv.update()
   with bpy.context.temp_override(window=win,area=area,region=reg):
    print('ACTIVATE',bpy.ops.brush.asset_activate(asset_library_type='ESSENTIALS',relative_asset_identifier='brushes/essentials_brushes-curve_sculpt.blend/Brush/Comb'),flush=True);st=bpy.context.tool_settings.curves_sculpt;st.unified_paint_settings.use_unified_size=False;st.brush.size=500;st.brush.strength=1.;A=location_3d_to_region_2d(reg,rv,Vector((.05,0,.20)));B=location_3d_to_region_2d(reg,rv,Vector((.25,0,.30)));print('TOOL',bpy.context.workspace.tools.from_space_view3d_mode('SCULPT_CURVES',create=False).idname,flush=True)
   state.update(d=d,o=o,P=P,win=win,area=area,reg=reg,A=A,B=B,i=0);win.event_simulate(type='MOUSEMOVE',value='NOTHING',x=int(reg.x+A.x),y=int(reg.y+A.y));return .1
  i=state['i'];win=state['win'];reg=state['reg'];A=state['A'];B=state['B']
  if i==0:
   with bpy.context.temp_override(window=win,area=state['area'],region=reg):print('INVOKE',bpy.ops.sculpt_curves.brush_stroke('INVOKE_DEFAULT'),flush=True)
   win.event_simulate(type='LEFTMOUSE',value='PRESS',x=int(reg.x+A.x),y=int(reg.y+A.y))
  elif i<=10:
   xy=A.lerp(B,i/10);win.event_simulate(type='MOUSEMOVE',value='NOTHING',x=int(reg.x+xy.x),y=int(reg.y+xy.y))
  elif i==11:win.event_simulate(type='LEFTMOUSE',value='RELEASE',x=int(reg.x+B.x),y=int(reg.y+B.y))
  else:
   out=np.empty(state['P'].shape,'f4');state['d'].position_data.foreach_get('vector',out.ravel());delta=float(np.linalg.norm(out-state['P'],axis=1).max());result={'actualNativeEventCombDeltaMaxM':delta,'nativeEventLoopWorks':delta>1e-5};(E/'native-event-comb-test.json').write_text(json.dumps(result,indent=2)+'\n');print('NATIVE_EVENT_COMB_DONE',result,flush=True);bpy.ops.wm.quit_blender();return None
  state['i']+=1;return .06
 except:
  traceback.print_exc();bpy.ops.wm.quit_blender();return None
bpy.app.timers.register(timer,first_interval=.5)
