"""One real native Add/Comb operation in Blender's own window context.
No external desktop helper, arbitrary free-path style or asset transplant.
"""
from pathlib import Path
import bpy,json,numpy as np,math,time,datetime,traceback
from mathutils import Vector,Quaternion
from bpy_extras.view3d_utils import location_3d_to_region_2d
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0149-native-scalp-sculpt';SRC=R/'engine/assets/characters/female-next/source/r0139-source/aevrynd-female-next-r0139-a-native-lid-follow.blend'
state={};tick=time.time()
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=str)+'\n',encoding='utf-8')
def geometry():
 d=state['hair'].data;P=np.empty((len(d.points),3),'f4');d.position_data.foreach_get('vector',P.ravel());return P
def context():return bpy.context.temp_override(window=state['win'],area=state['area'],region=state['region'])
def activate(name):
 settings=bpy.context.scene.tool_settings.curves_sculpt
 if not settings.is_property_readonly('brush'):settings.brush=state['brushes'][name]
 else:
  with context():bpy.ops.brush.asset_activate(asset_library_type='LOCAL',relative_asset_identifier='Brush/'+state['brushes'][name].name)
 return settings.brush
def stroke(p0,p1):
 props={p.identifier for p in bpy.types.OperatorStrokeElement.bl_rna.properties};events=[]
 for i in range(8):
  t=i/7;mouse=(float(p0.x*(1-t)+p1.x*t),float(p0.y*(1-t)+p1.y*t));row={'name':'stroke','mouse':mouse,'mouse_event':mouse,'location':(0.,0.,0.),'pressure':1.,'size':45.,'time':t*.4,'is_start':i==0,'pen_flip':False,'x_tilt':0.,'y_tilt':0.};events.append({k:v for k,v in row.items() if k in props})
 with context():return list(bpy.ops.sculpt_curves.brush_stroke(stroke=events))
def finish():
 try:
  hair=state['hair'];P=geometry();save('native-add-comb-capability.json',{'source':str(SRC),'nativeWindowContext':True,'actualSkin':state['skin'].name,'actualHairComponent':hair.name,'surface':hair.data.surface.name,'surfaceUV':hair.data.surface_uv_map,'nativeCurveCount':len(hair.data.curves),'nativePointCount':len(P),'addResult':state.get('addResult'),'combResult':state.get('combResult'),'combMaximumPointMovementM':state.get('combMove'),'pointsFinite':bool(np.isfinite(P).all()),'attributes':[(x.name,x.domain,x.data_type) for x in hair.data.attributes],'componentOnlyNotCompleteWomanOrAppearanceGain':True,'seconds':time.time()-tick})
  np.savez_compressed(E/'native-add-comb-capability-points.npz',positions=P)
  surface=hair.data.surface;hair.data.surface=None
  bpy.data.libraries.write(str(E/'native-add-comb-component.blend'),{hair},fake_user=True)
  hair.data.surface=surface
  with context():
   bpy.context.scene.render.filepath=str(E/'native-add-comb-viewport.png');bpy.ops.render.opengl(write_still=True,view_context=True)
  print('R149_REAL_NATIVE_ADD_COMB_CAPABILITY_COMPONENT_DONE',len(hair.data.curves),len(P),state.get('combMove'),flush=True)
 except Exception:save('native-capability-failure.json',{'traceback':traceback.format_exc(),'phase':'finish','seconds':time.time()-tick})
 bpy.ops.wm.quit_blender();return None
def comb():
 try:
  hair=state['hair'];assert len(hair.data.curves)>0,'Native Add did not place any actual scalp curves';before=geometry();brush=activate('Comb');brush.size=80;brush.strength=1.;rv=state['area'].spaces.active.region_3d;region=state['region'];p0=location_3d_to_region_2d(region,rv,Vector((0.,-.045,1.572)));p1=location_3d_to_region_2d(region,rv,Vector((-.055,-.045,1.49)));state['combResult']=stroke(p0,p1);bpy.context.view_layer.update();after=geometry();state['combMove']=float(np.linalg.norm(after-before,axis=1).max());assert state['combMove']>1e-6,'Comb actual points did not move';state['area'].tag_redraw();bpy.app.timers.register(finish,first_interval=.5)
 except Exception:save('native-capability-failure.json',{'traceback':traceback.format_exc(),'phase':'comb','seconds':time.time()-tick});bpy.ops.wm.quit_blender()
 return None
def add():
 try:
  brush=activate('Add');brush.size=45;brush.strength=1.;settings=brush.curves_sculpt_settings;keys={p.identifier for p in settings.bl_rna.properties};config={'curve_length':.12,'points_per_curve':16,'minimum_distance':.004,'density_add_attempts':50,'add_amount':8}
  for k,v in config.items():
   if k in keys:setattr(settings,k,v)
  save('native-brush-capability-rna.json',{'brushes':state['brushNames'],'activeAddBrush':brush.name,'curveSettings':{p.identifier:str(getattr(settings,p.identifier)) for p in settings.bl_rna.properties if p.identifier!='rna_type'},'operatorProperties':list(bpy.ops.sculpt_curves.brush_stroke.get_rna_type().properties.keys()),'windowRegion':[state['region'].width,state['region'].height]})
  rv=state['area'].spaces.active.region_3d;p=location_3d_to_region_2d(state['region'],rv,Vector((0.,-.045,1.572)));assert p is not None;state['addResult']=stroke(p,p+Vector((12.,0.)));bpy.context.view_layer.update();save('first-actual-native-add-geometry.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originalStartedUTC':'2026-10-22T03:46:45+00:00','curves':len(state['hair'].data.curves),'points':len(state['hair'].data.points),'surface':state['skin'].name,'nativeOperator':'sculpt_curves.brush_stroke'});state['area'].tag_redraw();bpy.app.timers.register(comb,first_interval=.5)
 except Exception:save('native-capability-failure.json',{'traceback':traceback.format_exc(),'phase':'add','seconds':time.time()-tick});bpy.ops.wm.quit_blender()
 return None
def setup():
 try:
  bpy.ops.wm.open_mainfile(filepath=str(SRC),load_ui=False);scene=bpy.context.scene;scene.frame_set(1);scene.render.threads_mode='FIXED';scene.render.threads=4;skin=bpy.data.objects['AFN126_COMPLETE_WOMAN_BODY_AND_ARTIST_HEAD']
  for o in bpy.data.objects:o.hide_set(o!=skin)
  bpy.ops.object.select_all(action='DESELECT');skin.select_set(True);bpy.context.view_layer.objects.active=skin
  win=bpy.context.window_manager.windows[0];area=next(a for a in win.screen.areas if a.type=='VIEW_3D');region=next(r for r in area.regions if r.type=='WINDOW');state.update(win=win,area=area,region=region,skin=skin)
  data=bpy.data.hair_curves.new('AFN149_NATIVE_SCALP_CURVES_DATA');hair=bpy.data.objects.new('AFN149_NATIVE_SCALP_CURVES',data);scene.collection.objects.link(hair);hair.matrix_world=skin.matrix_world.copy();skin.select_set(False);hair.select_set(True);bpy.context.view_layer.objects.active=hair;
  hair.name='AFN149_NATIVE_ADD_COMB_CAPABILITY';hair.data.surface=skin;hair.data.surface_uv_map='AngelicaOriginalUV';state['hair']=hair
  with context():bpy.ops.object.mode_set(mode='SCULPT_CURVES')
  with bpy.data.libraries.load('D:/SteamLibrary/steamapps/common/Blender/5.2/datafiles/assets/brushes/essentials_brushes-curve_sculpt.blend',link=False) as (src,dst):
   state['brushNames']=list(src.brushes);assert 'Add' in src.brushes and 'Comb' in src.brushes;dst.brushes=['Add','Comb']
  state['brushes']=dict(zip(['Add','Comb'],dst.brushes))
  rv=area.spaces.active.region_3d;rv.view_perspective='ORTHO';rv.view_rotation=Quaternion((1,0,0),math.radians(65));rv.view_location=Vector((0.,-.025,1.535));rv.view_distance=.35;area.spaces.active.shading.type='SOLID';area.tag_redraw();save('native-capability-window-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originalStartedUTC':'2026-10-22T03:46:45+00:00','actualSkin':skin.name,'surfaceUV':hair.data.surface_uv_map,'nativeContextRegion':[region.width,region.height],'brushNames':state['brushNames']});bpy.app.timers.register(add,first_interval=.7)
 except Exception:save('native-capability-failure.json',{'traceback':traceback.format_exc(),'phase':'setup','seconds':time.time()-tick});bpy.ops.wm.quit_blender()
 return None
bpy.app.timers.register(setup,first_interval=.5)
