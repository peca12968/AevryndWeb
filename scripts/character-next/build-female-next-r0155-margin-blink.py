"""Second structural method: real margin-driven angular field on original meshes."""
from pathlib import Path
import bpy,numpy as np,json,datetime,time,math,importlib.util
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0155-native-blink';S=R/'engine/assets/characters/female-next/source';SRC=S/'r0153-source/aevrynd-female-next-r0153-a-current-hairline.blend';OUT=S/'r0155-source/aevrynd-female-next-r0155-b-margin-blink.blend'
sp=importlib.util.spec_from_file_location('r155fieldbase',Path(__file__).with_name('build-female-next-r0139-native-lid-follow.py'));h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h);a=h.a;a.b.u.v.E=E
def save(n,x):(E/n).write_bytes((json.dumps(x,indent=2,ensure_ascii=False,default=lambda x:x.tolist() if isinstance(x,np.ndarray) else x.item() if isinstance(x,np.generic) else str(x))+'\n').encode())
def geo(names):return {n:[a.a.hasharray(x) for x in a.geometry(bpy.data.objects[n])] for n in names}
def helper(name,arrays):
 N=len(next(iter(arrays.values())));d=bpy.data.meshes.new(name+'_DATA');d.from_pydata(np.zeros((N,3)).tolist(),[],[]);o=bpy.data.objects.new(name,d);bpy.context.scene.collection.objects.link(o);o.hide_render=True;o.hide_set(True)
 for key,v in arrays.items():
  v=np.asarray(v);kind='FLOAT_VECTOR' if v.ndim==2 else 'INT' if v.dtype.kind in 'iu' else 'FLOAT';prop='vector' if v.ndim==2 else 'value';d.attributes.new(key,kind,'POINT').data.foreach_set(prop,v.astype('i4' if kind=='INT' else 'f4').ravel())
 return o
def graph(ob,table,rig,skin=None):
 g=bpy.data.node_groups.new('AFN155_'+ob.name+'_ANGULAR_BLINK','GeometryNodeTree');g.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');g.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry');n=g.nodes;L=g.links;inp=n.new('NodeGroupInput');out=n.new('NodeGroupOutput');idx=n.new('GeometryNodeInputIndex');pos=n.new('GeometryNodeInputPosition');info=n.new('GeometryNodeObjectInfo');info.transform_space='RELATIVE';info.inputs['Object'].default_value=table
 def field(name,kind='FLOAT'):
  attr=n.new('GeometryNodeInputNamedAttribute');attr.data_type=kind;attr.inputs['Name'].default_value=name;x=n.new('GeometryNodeSampleIndex');x.data_type=kind;x.domain='POINT';L.new(info.outputs['Geometry'],x.inputs['Geometry']);L.new(attr.outputs['Attribute'],x.inputs['Value']);L.new(idx.outputs[0],x.inputs['Index']);return x.outputs['Value']
 def scalar(op,x,y):
  z=n.new('ShaderNodeMath');z.operation=op;L.new(x,z.inputs[0]);L.new(y,z.inputs[1]);return z.outputs[0]
 def vector(op,*values):
  z=n.new('ShaderNodeVectorMath');z.operation=op
  for k,v in enumerate(values):L.new(v,z.inputs[k])
  return z.outputs[0]
 def scale(v,t):
  z=n.new('ShaderNodeVectorMath');z.operation='SCALE';L.new(v,z.inputs[0]);L.new(t,z.inputs['Scale']);return z.outputs[0]
 values=[]
 for side in ['L','R']:
  x=n.new('ShaderNodeValue');fc=x.outputs[0].driver_add('default_value');fc.driver.type='SCRIPTED';v=fc.driver.variables.new();v.name='blink';v.type='SINGLE_PROP';v.targets[0].id=rig;v.targets[0].data_path='["blink_'+side+'"]';fc.driver.expression='blink';values.append(x.outputs[0])
 choose=n.new('GeometryNodeSwitch');choose.input_type='FLOAT';L.new(field('AFN155_SIDE','INT'),choose.inputs['Switch']);L.new(values[0],choose.inputs['False']);L.new(values[1],choose.inputs['True']);blink=choose.outputs[0];angle=scalar('MULTIPLY',field('AFN155_ANGLE'),blink);active=scalar('MULTIPLY',field('AFN155_ACTIVE'),blink);selection=n.new('ShaderNodeMath');selection.operation='GREATER_THAN';L.new(active,selection.inputs[0]);selection.inputs[1].default_value=0.
 rot=n.new('ShaderNodeVectorRotate');rot.rotation_type='AXIS_ANGLE';rot.inputs['Axis'].default_value=(1,0,0);L.new(angle,rot.inputs['Angle'])
 if skin is None:
  center=field('AFN155_CENTER','FLOAT_VECTOR');L.new(pos.outputs[0],rot.inputs['Vector']);L.new(center,rot.inputs['Center']);relative=vector('SUBTRACT',rot.outputs[0],center);dot=n.new('ShaderNodeVectorMath');dot.operation='DOT_PRODUCT';L.new(relative,dot.inputs[0]);dot.inputs[1].default_value=(1,0,0);axis=n.new('ShaderNodeCombineXYZ');L.new(dot.outputs['Value'],axis.inputs['X']);radial=vector('NORMALIZE',vector('SUBTRACT',relative,axis.outputs[0]));target=vector('ADD',rot.outputs[0],scale(radial,scalar('MULTIPLY',field('AFN155_RADIAL'),blink)))
 else:
  si=n.new('GeometryNodeObjectInfo');si.transform_space='RELATIVE';si.inputs['Object'].default_value=skin;bc=n.new('ShaderNodeSeparateXYZ');L.new(field('AFN155_BC','FLOAT_VECTOR'),bc.inputs[0]);parts=[]
  for k in range(3):
   sample=n.new('GeometryNodeSampleIndex');sample.data_type='FLOAT_VECTOR';sample.domain='POINT';L.new(si.outputs['Geometry'],sample.inputs['Geometry']);L.new(pos.outputs[0],sample.inputs['Value']);L.new(field('AFN155_V'+str(k),'INT'),sample.inputs['Index']);parts.append(scale(sample.outputs['Value'],bc.outputs[k]))
  root=vector('ADD',vector('ADD',parts[0],parts[1]),parts[2]);L.new(field('AFN155_OFFSET','FLOAT_VECTOR'),rot.inputs['Vector']);target=vector('ADD',root,rot.outputs[0])
 setp=n.new('GeometryNodeSetPosition');L.new(inp.outputs['Geometry'],setp.inputs['Geometry']);L.new(selection.outputs[0],setp.inputs['Selection']);L.new(target,setp.inputs['Position']);L.new(setp.outputs['Geometry'],out.inputs['Geometry']);ob.modifiers.new('AFN155_ACTUAL_CURRENT_MARGIN_BLINK','NODES').node_group=g
def main():
 tick=time.time();assert not OUT.exists();bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();skin=bpy.data.objects[h.SKIN];assert np.max(abs(np.array(skin.matrix_world)-np.eye(4)))<1e-7;bpy.data.objects['AFN153_ACTUAL_CURRENT_SCALP_SHORT_HAIRLINE'].hide_render=True;bpy.data.objects['AFN153_ACTUAL_CURRENT_SCALP_SHORT_HAIRLINE'].hide_set(True);rig=bpy.data.objects['AFN138_ACTUAL_CURRENT_GAZE_RIG'];names=a.FIXED+a.MOVING;neutral=geo(names);raw={n:a.rawsig(bpy.data.objects[n]) for n in names};V,T=a.geometry(skin);construction=json.loads((E.parent/'r0139-native-lid-follow/native-lid-follow-construction.json').read_text());edges=np.unique(np.sort(np.concatenate([T[:,[0,1]],T[:,[1,2]],T[:,[2,0]]]),axis=1),axis=0);g=h.graph(V,edges);N=len(V);alpha=np.zeros(N);radial=np.zeros(N);centers=np.zeros((N,3));sideIds=np.zeros(N,'i4');rows=[]
 for side in ['L','R']:
  center=np.array(rig.matrix_world@rig.data.bones[a.bone_names()[side]].head_local);ids={kind:np.array(construction['actualSourceNativeDomains'][side+'_'+kind]['actualSkinSeedIds']) for kind in ['UPPER','LOWER']};curves={};dists={};owners={};fades={}
  for kind,support in [('UPPER',.012),('LOWER',.008)]:
   points=V[ids[kind]];order=np.argsort(points[:,0]);p=points[order];delta=p-center;theta=np.arctan2(delta[:,2],-delta[:,1]);radius=np.linalg.norm(delta[:,1:],axis=1);curves[kind]=(p[:,0],theta,radius);d,o=h.geodesic(g,ids[kind],support);dists[kind]=d;owners[kind]=o;t=np.clip(1-d/support,0,1);fades[kind]=np.where(np.isfinite(d),t*t*(3-2*t),0.)
  valid=np.flatnonzero(np.isfinite(dists['UPPER'])|np.isfinite(dists['LOWER']));du=dists['UPPER'][valid];dl=dists['LOWER'][valid];ownership=np.where(~np.isfinite(dl),1.,np.where(~np.isfinite(du),0.,dl/np.maximum(du+dl,1e-12)));ownership=np.nan_to_num(ownership,nan=.5);ownership=ownership*ownership*(3-2*ownership);sa=np.zeros(len(valid));sr=np.zeros(len(valid));targets={}
  for kind,own in [('UPPER',ownership),('LOWER',1-ownership)]:
   ok=np.isfinite(dists[kind][valid]);owner=owners[kind][valid[ok]];margin=V[ids[kind][owner]];x=margin[:,0];tu=np.interp(x,*curves['UPPER'][:2]);tl=np.interp(x,*curves['LOWER'][:2]);ru=np.interp(x,curves['UPPER'][0],curves['UPPER'][2]);rl=np.interp(x,curves['LOWER'][0],curves['LOWER'][2]);targetTheta=tl+.2*(tu-tl);targetRadius=np.maximum(ru,rl);originalTheta=np.arctan2(margin[:,2]-center[2],-(margin[:,1]-center[1]));originalRadius=np.linalg.norm(margin[:,1:]-center[1:],axis=1);fade=fades[kind][valid[ok]]*own[ok];sa[ok]+=(originalTheta-targetTheta)*fade;sr[ok]+=np.maximum(targetRadius-originalRadius,0)*fade;targets[kind]={'marginIds':ids[kind],'closureSeam':'Lower margin plus0.2 of angular opening, fixed engineering/artistic endpoint; not physiological calibration.','allMarginsRetained':True}
  alpha[valid]=sa;radial[valid]=sr;centers[valid]=center;sideIds[valid]=int(side=='R');rows.append({'side':side,'affectedVertices':len(valid),'maximumAngularChangeDegrees':float(np.rad2deg(abs(sa)).max()),'maximumOutwardRadialChangeM':float(sr.max()),'targets':targets})
 for side in ['L','R']:rig['blink_'+side]=0.;rig.id_properties_ui('blink_'+side).update(min=0.,max=1.)
 active=(abs(alpha)+radial>1e-12).astype('f4');arrays={'AFN155_ANGLE':alpha,'AFN155_RADIAL':radial,'AFN155_CENTER':centers,'AFN155_SIDE':sideIds,'AFN155_ACTIVE':active};table=helper('AFN155_CURRENT_SKIN_BLINK_FIELD',arrays);graph(skin,table,rig);attachmentRows=[]
 for name in h.ATTACH:
  ob=bpy.data.objects[name];P,F=a.geometry(ob);N=len(P);aa=np.zeros(N);ss=np.zeros(N,'i4');bc=np.zeros((N,3));idx=np.zeros((N,3),'i4');offset=np.zeros((N,3));on=np.zeros(N)
  for anchor in construction['actualAttachments'][name]['anchors']:
   ids=np.array(anchor['vertices']);tri=np.array(anchor['skinTriangleVertices']);bary=np.array(anchor['barycentric']);idx[ids]=tri;bc[ids]=bary;aa[ids]=float(bary@alpha[tri]);ss[ids]=int(float(anchor['rootWorld'][0])<0);offset[ids]=P[ids]-(bary@V[tri]);on[ids]=float(abs(aa[ids][0])+float(bary@radial[tri])>1e-12)
  arr={'AFN155_ANGLE':aa,'AFN155_SIDE':ss,'AFN155_ACTIVE':on,'AFN155_BC':bc,'AFN155_OFFSET':offset,**{'AFN155_V'+str(k):idx[:,k] for k in range(3)}};tab=helper('AFN155_'+name+'_BLINK_ATTACHMENT',arr);graph(ob,tab,rig,skin);attachmentRows.append({'object':name,'actualSkinTriangleAnchors':len(construction['actualAttachments'][name]['anchors']),'activeVertices':int(on.sum())})
 rig.update_tag();bpy.context.view_layer.update();assert neutral==geo(names) and raw=={n:a.rawsig(bpy.data.objects[n]) for n in names};save('direct-current-margin-blink-authoring-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originalStartedUTC':'2026-10-22T07:33:30+00:00','oneOriginalRoundTwoStructuralSavedStates':True,'originalPlannedOneCandidatePreserved':True,'changedPremise':'A fixed lid-bone endpoint does not close the true margin; substantial eye white remains. B rebuilds per-vertex actual margin closure and anatomical ownership with geodesic fade and a common seam, on original topology. Angular rather than linear chord interpolation; no source caps, extra closure mesh or angle sweep.','actualSkin':skin.name,'nativeGeometryFields':rows,'actualLashWetAttachments':attachmentRows,'neutralExactAndOriginalRawMeshUVRetained':True,'operationContactRuntimeNotAccepted':True})
 old=rig.animation_data.action;old.use_fake_user=True;rig.animation_data.action=None
 for n in a.bone_names().values():rig.pose.bones[n].rotation_euler=(0,0,0)
 for frame,value in [(1,0.),(6,0.),(9,.5),(11,1.),(13,1.),(16,.5),(20,0.),(24,0.)]:
  for prop in ['blink_L','blink_R']:rig[prop]=value;rig.keyframe_insert(data_path='["'+prop+'"]',frame=frame)
 action=rig.animation_data.action;action.name='AFN155_ACTUAL_MARGIN_BLINK_DEMO';action.use_fake_user=True
 for layer in action.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for key in fc.keyframe_points:key.interpolation='BEZIER';key.handle_left_type=key.handle_right_type='AUTO_CLAMPED'
 s.frame_start=1;s.frame_end=24;s.render.fps=24;s.frame_set(1);bpy.context.view_layer.update();assert neutral==geo(names);bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=True);assert sum(p.stat().st_size for p in OUT.parent.glob('*.blend'))<1500000
 save('b-build-summary.json',{'source':str(SRC),'sourceSha256':a.a.sha(SRC),'output':str(OUT),'sha256':a.a.sha(OUT),'bytes':OUT.stat().st_size,'actualRig':rig.name,'actualSkin':skin.name,'blinkAction':action.name,'originalGazeAction':old.name,'nativeHelperFieldObjects':[o.name for o in bpy.data.objects if o.name.startswith('AFN155_')],'newCompleteUsableOperationAccepted':False,'originalStartedUTC':'2026-10-22T07:33:30+00:00','originalFirstPreviewDeadlineUTC':'2026-10-22T08:03:30+00:00','secondStructuralStateNoRoundClockReset':True})
 np.savez_compressed(E/'current-margin-blink-authoring.npz',angle=alpha,radial=radial,center=centers,side=sideIds,active=active)
 s.frame_set(11);bpy.context.view_layer.update();views=[]
 for view in ['face','body-face','oblique']:views.append(a.b.u.v.image('b-margin-blink-closed',view));save('b-closed-view-controls.json',views)
 clip=[]
 for frame in [9,24]:
  s.frame_set(frame);bpy.context.view_layer.update();a.b.u.v.m.rig.shade.settings();a.b.u.v.m.rig.k.b.camera('face');s.camera.data.lens=85;s.render.resolution_x=s.render.resolution_y=320;s.cycles.samples=8;s.render.hair_subdiv=3;s.render.filepath=str(E/('actual-b-margin-blink-frame-%02d.png'%frame));bpy.context.view_layer.update();bpy.ops.render.render(write_still=True);clip.append({'frame':frame,'file':s.render.filepath,'blink_L':rig['blink_L'],'blink_R':rig['blink_R'],'actualSkinHash':a.a.hasharray(a.geometry(skin)[0]),'resolution':320,'samples':8,'seed':s.cycles.seed,'exposure':s.view_settings.exposure,'camera':np.array(s.camera.matrix_world).tolist()});save('b-actual-blink-clip-controls.json',clip)
 s.frame_set(1);bpy.context.view_layer.update();assert neutral==geo(names);print('R155_COMPLETE_MARGIN_BLINK_WOMAN_HEAD_BODY_ACTION_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
