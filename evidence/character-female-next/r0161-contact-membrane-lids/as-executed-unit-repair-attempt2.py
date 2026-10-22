"""One verified unit-premise repair, same original round and intended gaps.
Original A requested sub-mm settings were clamped to1mm. Lab scale100 converts
all actual geometry/length settings and returns evaluated positions to metres.
No claim of physiologically calibrated constitutive material or safe contacts.
"""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,time,datetime
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');R=Path('D:/Download/Aevrynd');E=C/'evidence/character-female-next/r0161-contact-membrane-lids';OUT=C/'assets-source/aevrynd-character/female-next/r0161-source/aevrynd-female-next-r0161-b-unit-corrected-membrane.blend';K=100.
sp=importlib.util.spec_from_file_location('r161units',C/'scripts/character-next/build-female-next-r0161-contact-membrane-lids.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;h=m.h;g=m.g
def main():
 tick=time.time();assert not OUT.exists();b=json.loads((E/'a-build-summary.json').read_text());assert a.a.sha(Path(b['output']))==b['sha256'];bpy.ops.wm.open_mainfile(filepath=b['engineAlias']);s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();skin=bpy.data.objects[b['actualSkin']];reference=bpy.data.objects[b['actualPoseSource']];rig=bpy.data.objects[b['actualRig']];oldHelper=bpy.data.objects['AFN161_CONTACT_MEMBRANE_AUTHORING'];N=len(oldHelper.data.vertices);ids=h.arr(oldHelper.data.attributes['AFN161_SOURCE_VERTEX'].data,'value',N,dtype='i4');pins=h.arr(oldHelper.data.attributes['AFN161_PIN'].data,'value',N,dtype='i4');P=a.geometry(reference)[0][ids];F=np.array([list(f.vertices) for f in oldHelper.data.polygons],'i4');nativeBaseline={n:a.geometry(bpy.data.objects[n])[0] for n in a.FIXED+a.MOVING}
 # Reuse immutable complete A Mesh data through a normal relative library.
 # Local objects/controls/node groups remain editable; no failed look adopted.
 meshes=[d for d in bpy.data.meshes if d.library is None];names=[d.name for d in meshes]
 with bpy.data.libraries.load(b['output'],link=True) as (src,dst):dst.meshes=names
 linked=dict(zip(names,dst.meshes));replaced=[]
 for ob in list(bpy.data.objects):
  if ob.type=='MESH' and ob.data in meshes:
   old=ob.data;ob.data=linked[old.name];replaced.append({'object':ob.name,'linkedImmutableMesh':old.name})
 for d in meshes:
  if d.users==0:bpy.data.meshes.remove(d)
 membrane=m.meshob('AFN161B_LAB_CONTACT_MEMBRANE',P*K,F);m.attr(membrane.data,'AFN161_PIN',pins);m.attr(membrane.data,'AFN161_SOURCE_VERTEX',ids);m.pin_graph(membrane,reference);tree=membrane.modifiers[0].node_group;p=next(n for n in tree.nodes if n.bl_idname=='GeometryNodeSetPosition');sourceSocket=p.inputs['Position'].links[0].from_socket;scale=tree.nodes.new('ShaderNodeVectorMath');scale.operation='SCALE';scale.inputs['Scale'].default_value=K;tree.links.new(sourceSocket,scale.inputs[0]);tree.links.new(scale.outputs[0],p.inputs['Position']);vg=membrane.vertex_groups.new(name='AFN161B_TRUE_MARGIN_PINS');vg.add(np.flatnonzero(pins).tolist(),1.,'REPLACE');cloth=membrane.modifiers.new('AFN161B_NATIVE_FACE_CONTACT_UNIT_LAB','CLOTH');cs=cloth.settings;cc=cloth.collision_settings
 for key,value in [('quality',12),('mass',.001),('tension_stiffness',30.),('compression_stiffness',30.),('shear_stiffness',15.),('bending_stiffness',1.),('vertex_group_mass',vg.name),('use_dynamic_mesh',False)]:setattr(cs,key,value)
 cs.effector_weights.gravity=0.;cc.use_collision=True;cc.collision_quality=8;cc.distance_min=.0002*K;cc.use_self_collision=True;cc.self_distance_min=.00015*K;cloth.point_cache.frame_start=1;cloth.point_cache.frame_end=24;colliders=[]
 for name in a.MOVING:
  W,T=a.geometry(bpy.data.objects[name]);collider=m.meshob('AFN161B_LAB_'+name,W*K,T);collider.modifiers.new('AFN161B_EXACT_SCALED_OCULAR_COLLIDER','COLLISION');bpy.context.view_layer.update();collider.collision.thickness_outer=.0001*K;collider.collision.thickness_inner=.0001*K;colliders.append({'original':name,'labObject':collider.name,'sameTriangles':len(T),'fullActualVerticesScaled':True,'physicalOuterM':collider.collision.thickness_outer/K,'physicalInnerM':collider.collision.thickness_inner/K})
 physical={'distanceMinM':cc.distance_min/K,'selfDistanceMinM':cc.self_distance_min/K};assert abs(physical['distanceMinM']-.0002)<1e-10 and abs(physical['selfDistanceMinM']-.00015)<1e-10;m.save('unit-corrected-membrane-authoring-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originalStartedUTC':'2026-10-22T18:53:17+00:00','sameOriginalRoundSecondSavedState':True,'AFullSourceUnchanged':b,'verifiedChangedPremise':'A actual RNA clamped distance/self distance/collider thickness to1mm. Convert all lab geometry and lengths by100, return captured geometry to metres. No parameter sweep or reduced eye/blink/action.','lengthScale':K,'actualPhysicalContactSettings':physical,'actualColliders':colliders,'materialCalibrationNotClaimed':True,'compactSourceUsesImmutableACompleteMeshes':replaced,'compactnessNotCharacterImprovement':True});steps=[];stats=[]
 for frame in range(1,25):
  s.frame_set(frame);bpy.context.view_layer.update();W,T=a.geometry(membrane);W/=K;assert len(W)==N and np.isfinite(W).all();steps.append(W.astype('f4'));displacement=float(np.linalg.norm(W-P,axis=1).max());pinTarget=a.geometry(reference)[0][ids[pins>0]];pinError=float(np.linalg.norm(W[pins>0]-pinTarget,axis=1).max());stats.append({'frame':frame,'actualMetreDisplacementMaximum':displacement,'actualPinErrorM':pinError,'blink':[float(rig[k]) for k in ['blink_L','blink_R']]});m.save('unit-corrected-simulation-progress.json',stats);print('R161B_ACTUAL_UNIT_LAB_FRAME',frame,displacement,pinError,flush=True);assert displacement<.1,'Unit-corrected membrane unstable; no clamp'
 np.savez_compressed(E/'unit-corrected-membrane-states.npz',frames=np.arange(1,25),positions=np.array(steps),globalSkinVertexIds=ids,triangles=F);cloth.show_viewport=cloth.show_render=False;membrane.hide_set(True);baked=m.meshob('AFN161B_ACTUAL_UNIT_CORRECTED_WALL_STATES',steps[0],F);baked.shape_key_add(name='Basis')
 for i in range(1,24):
  key=baked.shape_key_add(name='AFN161B_CONTACT_FRAME_%02d'%(i+1));key.data.foreach_set('co',steps[i].ravel())
  for frame,value in [(i,0.),(i+1,1.),(i+2,0.)]:key.value=value;key.keyframe_insert(data_path='value',frame=frame)
 for layer in baked.data.shape_keys.animation_data.action.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for key in fc.keyframe_points:key.interpolation='LINEAR'
 group=next(mod.node_group for mod in skin.modifiers if mod.type=='NODES');oldBaked=bpy.data.objects[b['actualWallCorrectives']]
 for node in group.nodes:
  if node.bl_idname=='GeometryNodeObjectInfo' and node.inputs['Object'].default_value==oldBaked:node.inputs['Object'].default_value=baked
 s.frame_set(1);bpy.context.view_layer.update();neutral={n:float(np.linalg.norm(a.geometry(bpy.data.objects[n])[0]-nativeBaseline[n],axis=1).max()) for n in nativeBaseline};m.save('unit-corrected-neutral-geometry-readback.json',{'actualDifferencesM':neutral,'explicitFrame1ResetNotNaturalSettle':True});assert max(neutral.values())<2e-7;assert a.a.sha(Path(b['output']))==b['sha256'];m.save('unit-corrected-source-construction.json',{'actualSkin':skin.name,'actualNewWallCorrectives':baked.name,'original624NgonsAlreadyReplacedBy2728FixedActualTriangles':True,'AOriginalMeshLibraryPreserved':b['output'],'actualPhysicalContactSettings':physical,'simulationLastFrameNotAssumedRestored':stats[-1],'noFullAppearanceFunctionContactRuntimeAcceptance':True});bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=True);record=dict(b,source=b['output'],output=str(OUT),engineAlias=str(R/'engine/assets/characters/female-next/source/r0161-source'/OUT.name),sha256=a.a.sha(OUT),bytes=OUT.stat().st_size,actualWallCorrectives=baked.name,sameOriginalRoundSecondSavedState=True,compactDependencySourceA=b['output']);m.save('b-build-summary.json',record);assert OUT.stat().st_size+Path(b['output']).stat().st_size<42000000;a.b.u.v.E=E;views=[]
 for frame,view,tag in [(11,'face','b-unit-contact-lids-closed'),(11,'body-face','b-unit-contact-lids-closed'),(1,'face','b-unit-contact-lids-neutral'),(9,'face','b-unit-contact-lids-half')]:
  s.frame_set(frame);bpy.context.view_layer.update();_=a.geometry(skin)
  for name in a.FIXED[2:4]:_=a.geometry(bpy.data.objects[name])
  control=a.b.u.v.image(tag,view);control.update(frame=frame,blink=[float(rig[k]) for k in ['blink_L','blink_R']]);views.append(control);m.save('b-actual-preview-controls.json',views)
 s.frame_set(1);bpy.context.view_layer.update();print('R161B_UNIT_CORRECTED_SAME_CANDIDATE_COMPLETE_HEAD_BODY_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
