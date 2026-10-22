"""Actual current-skin blink, with native surface-bound lash/wet-line deformation.
No analytic lid cap, closing plate, foreign hair or hidden-head control is used.
"""
from pathlib import Path
import bpy,numpy as np,json,math,time,datetime,importlib.util
from mathutils import Vector
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0144-current-skin-blink';S=R/'engine/assets/characters/female-next/source';SRC=S/'r0139-source/aevrynd-female-next-r0139-a-native-lid-follow.blend';OUT=S/'r0144-source/aevrynd-female-next-r0144-a-current-skin-blink.blend'
sp=importlib.util.spec_from_file_location('r144native','D:/Download/Aevrynd/scripts/character-next/build-female-next-r0139-native-lid-follow.py');h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h);a=h.a;a.b.u.v.E=E
PROPS={'L':'AFN144_Blink_L','R':'AFN144_Blink_R'}
def save(n,x):
 (E/n).write_bytes((json.dumps(x,indent=2,default=lambda q:q.tolist() if isinstance(q,np.ndarray) else q.item() if isinstance(q,np.generic) else str(q))+'\n').encode())
def attr(data,name,t,x):
 p=data.attributes.new(name,t,'POINT');p.data.foreach_set('vector' if t=='FLOAT_VECTOR' else 'value',np.asarray(x,dtype='i4' if t=='INT' else 'f4').ravel())
def group(name):
 ng=bpy.data.node_groups.new(name,'GeometryNodeTree');ng.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');ng.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry');return ng,ng.nodes,ng.links
def first_modifier(ob,name,ng):
 md=ob.modifiers.new(name,'NODES');md.node_group=ng;bpy.context.view_layer.objects.active=ob
 for _ in range(len(ob.modifiers)-1):bpy.ops.object.modifier_move_up(modifier=md.name)
 return ob.modifiers[name]
def make_blink_group(centres,axes):
 ng,N,L=group('AFN144_ACTUAL_CURRENT_SKIN_ANGULAR_BLINK');inp=N.new('NodeGroupInput');out=N.new('NodeGroupOutput');pos=N.new('GeometryNodeInputPosition');current=pos.outputs['Position'];sockets={}
 for side in ['L','R']:
  socket=ng.interface.new_socket(name='Blink '+side,in_out='INPUT',socket_type='NodeSocketFloat');socket.min_value=0.;socket.max_value=1.;sockets[side]=socket.identifier
  ang=N.new('GeometryNodeInputNamedAttribute');ang.data_type='FLOAT';ang.inputs['Name'].default_value='AFN144_Angle_'+side;mult=N.new('ShaderNodeMath');mult.operation='MULTIPLY';L.new(ang.outputs['Attribute'],mult.inputs[0]);L.new(inp.outputs['Blink '+side],mult.inputs[1]);rot=N.new('ShaderNodeVectorRotate');rot.rotation_type='AXIS_ANGLE';rot.inputs['Center'].default_value=centres[side];rot.inputs['Axis'].default_value=axes[side];L.new(current,rot.inputs['Vector']);L.new(mult.outputs[0],rot.inputs['Angle']);current=rot.outputs['Vector']
 setp=N.new('GeometryNodeSetPosition');L.new(inp.outputs['Geometry'],setp.inputs['Geometry']);L.new(current,setp.inputs['Position']);L.new(setp.outputs['Geometry'],out.inputs['Geometry']);return ng,sockets
def drive(md,sockets,rig):
 for side,socket in sockets.items():
  md[socket]=0.;fc=md.driver_add('["'+socket+'"]');d=fc.driver;d.type='SCRIPTED';v=d.variables.new();v.name='blink';v.type='SINGLE_PROP';v.targets[0].id=rig;v.targets[0].data_path='["'+PROPS[side]+'"]';d.expression='blink'
def attach_group(ob,proxy,tri,bc,local):
 for j in range(3):attr(ob.data,'AFN144_SkinVertex'+str(j),'INT',tri[:,j])
 attr(ob.data,'AFN144_SkinBary','FLOAT_VECTOR',bc);attr(ob.data,'AFN144_RootLocal','FLOAT_VECTOR',local)
 ng,N,L=group('AFN144_BLINK_SURFACE_ATTACHMENT_'+ob.name);inp=N.new('NodeGroupInput');out=N.new('NodeGroupOutput');info=N.new('GeometryNodeObjectInfo');info.transform_space='RELATIVE';info.inputs['Object'].default_value=proxy;pos=N.new('GeometryNodeInputPosition')
 def named(n,t='FLOAT_VECTOR'):
  q=N.new('GeometryNodeInputNamedAttribute');q.data_type=t;q.inputs['Name'].default_value=n;return q.outputs['Attribute']
 def vec(op,x,y=None):
  q=N.new('ShaderNodeVectorMath');q.operation=op;L.new(x,q.inputs[0])
  if y is not None:L.new(y,q.inputs[1])
  return q.outputs['Vector']
 def scale(x,v):
  q=N.new('ShaderNodeVectorMath');q.operation='SCALE';L.new(x,q.inputs[0]);L.new(v,q.inputs['Scale']);return q.outputs['Vector']
 V=[]
 for j in range(3):
  q=N.new('GeometryNodeSampleIndex');q.data_type='FLOAT_VECTOR';q.domain='POINT';L.new(info.outputs['Geometry'],q.inputs['Geometry']);L.new(pos.outputs['Position'],q.inputs['Value']);L.new(named('AFN144_SkinVertex'+str(j),'INT'),q.inputs['Index']);V.append(q.outputs['Value'])
 x=vec('NORMALIZE',vec('SUBTRACT',V[1],V[0]));z=vec('NORMALIZE',vec('CROSS_PRODUCT',vec('SUBTRACT',V[1],V[0]),vec('SUBTRACT',V[2],V[0])));y=vec('CROSS_PRODUCT',z,x);bary=N.new('ShaderNodeSeparateXYZ');L.new(named('AFN144_SkinBary'),bary.inputs[0]);root=vec('ADD',vec('ADD',scale(V[0],bary.outputs[0]),scale(V[1],bary.outputs[1])),scale(V[2],bary.outputs[2]));lp=N.new('ShaderNodeSeparateXYZ');L.new(named('AFN144_RootLocal'),lp.inputs[0]);p=vec('ADD',root,vec('ADD',vec('ADD',scale(x,lp.outputs[0]),scale(y,lp.outputs[1])),scale(z,lp.outputs[2])));sp=N.new('GeometryNodeSetPosition');L.new(inp.outputs['Geometry'],sp.inputs['Geometry']);L.new(p,sp.inputs['Position']);L.new(sp.outputs['Geometry'],out.inputs['Geometry']);return first_modifier(ob,'AFN144_CURRENT_SKIN_BLINK_ATTACHMENT',ng)
def main():
 tick=time.time();assert not OUT.exists();bpy.ops.wm.open_mainfile(filepath=str(SRC));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update();first_record={'UTC':'2026-10-22T00:36:01.864090+00:00'};save('repaired-current-skin-blink-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originalStartedUTC':'2026-10-22T00:27:30+00:00','action':'Author nonlinear angular blink on actual displayed current Skin from source-native upper/lower margins and true optical centres; real lashes/wet line attach to the same blink surface before retained r139 gaze deformation. No source/hidden-head closing caps or imported asset.'})
 protected=a.a.protected();skin=bpy.data.objects[h.SKIN];rig=bpy.data.objects['AFN138_ACTUAL_CURRENT_GAZE_RIG'];names=a.FIXED+a.MOVING;baseline={n:a.geometry(bpy.data.objects[n]) for n in names};raw={n:a.rawsig(bpy.data.objects[n]) for n in names};W,T=baseline[h.SKIN];M=np.array(skin.matrix_world);metric=M[:3,:3].T@M[:3,:3];assert np.max(abs(metric-np.eye(3)*metric[0,0]))<1e-8;inv=np.linalg.inv(M);data=skin.data;old= json.loads((E.parent/'r0139-native-lid-follow/native-lid-follow-construction.json').read_text('utf-8'));edges=np.unique(np.sort(np.concatenate([T[:,[0,1]],T[:,[1,2]],T[:,[2,0]]]),axis=1),axis=0);g=h.graph(W,edges);centres={};axes={};records={};allAngles={}
 gazeAction=rig.animation_data.action;gazeSlot=rig.animation_data.action_slot;rig.animation_data.action=None
 for n in a.bone_names().values():rig.pose.bones[n].rotation_euler=(0,0,0)
 for side in ['L','R']:
  bone=rig.data.bones[a.bone_names()[side]];B=np.array(rig.matrix_world@bone.matrix_local);C=B[:3,3];R0=B[:3,:3];R0/=np.linalg.norm(R0,axis=0)[None,:];centres[side]=(inv@np.r_[C,1])[:3];axis=inv[:3,:3]@R0[:,0];axes[side]=axis/np.linalg.norm(axis)
  chains={k:np.array(old['actualSourceNativeDomains'][side+'_'+k]['actualSkinSeedIds'],dtype='i4') for k in ['UPPER','LOWER']};coords={k:(W[v]-C)@R0 for k,v in chains.items()};angles={k:np.unwrap(np.arctan2(v[:,2],v[:,1])) for k,v in coords.items()};sorts={k:np.argsort(v[:,0]) for k,v in coords.items()}
  def theta(kind,x):
   s=sorts[kind];return np.interp(x,coords[kind][s,0],angles[kind][s])
  delta=np.zeros(len(W));distances={};owners={}
  for kind,support in [('UPPER',.012),('LOWER',.008)]:distances[kind],owners[kind]=h.geodesic(g,chains[kind],support)
  for kind,support,other in [('UPPER',.012,'LOWER'),('LOWER',.008,'UPPER')]:
   use=np.isfinite(distances[kind]) & (distances[kind]<=distances[other]);ids=np.flatnonzero(use);owner=owners[kind][ids];x=coords[kind][owner,0];target=.2*theta('UPPER',x)+.8*theta('LOWER',x);turn=target-theta(kind,x);t=np.clip(1-distances[kind][ids]/support,0,1);fade=t*t*(3-2*t);delta[ids]=turn*fade
  attr(data,'AFN144_Angle_'+side,'FLOAT',delta);allAngles[side]=delta;rig[PROPS[side]]=0.;rig.id_properties_ui(PROPS[side]).update(min=0.,max=1.,soft_min=0.,soft_max=1.,description='Actual current displayed eyelid blink; unaccepted until full motion/closure/contact review.')
  records[side]={'bone':bone.name,'actualOpticalCentreWorld':C,'axisWorld':R0[:,0],'nativeMarginIds':chains,'nativeMarginCoordinatesInOpticalFrame':coords,'nativeMarginPolarAnglesRadians':angles,'closureSeam':'0.2*upperAngle(x)+0.8*lowerAngle(x) from actual native source margins, nonlinear angular interpolation. Initial anatomical construction, not accepted calibration.','affectedSkinVertices':int(np.count_nonzero(delta)),'authoredAngleRangeDegrees':np.degrees([delta.min(),delta.max()])}
 ng,sockets=make_blink_group(centres,axes);md=first_modifier(skin,'AFN144_ACTUAL_DISPLAYED_SKIN_BLINK',ng);drive(md,sockets,rig)
 proxy=bpy.data.objects.new('AFN144_PRE_GAZE_BLINK_SURFACE_HELPER',skin.data);scene.collection.objects.link(proxy);proxy.matrix_world=skin.matrix_world.copy();proxy.hide_render=True;proxy.hide_set(True);drive(first_modifier(proxy,'AFN144_SAME_BLINK_BEFORE_GAZE',ng),sockets,rig);proxy['scope']='Hidden intermediate only for pre-gaze attachment evaluation. Actual displayed Skin has its own identical native blink modifier; proxy is not improvement evidence.'
 attachments={}
 for name in h.ATTACH:
  ob=bpy.data.objects[name];V=baseline[name][0];A=np.array(ob.matrix_world);ai=np.linalg.inv(A);localW=W@ai[:3,:3].T+ai[:3,3];localV=V@ai[:3,:3].T+ai[:3,3];ids=np.zeros((len(V),3),dtype='i4');bc=np.zeros((len(V),3));lp=np.zeros_like(V)
  for rec in old['actualAttachments'][name]['anchors']:
   pts=np.array(rec['vertices'],dtype='i4');tri=np.array(rec['skinTriangleVertices'],dtype='i4');weights=np.array(rec['barycentric']);B=localW[tri];x=B[1]-B[0];x/=np.linalg.norm(x);z=np.cross(B[1]-B[0],B[2]-B[0]);z/=np.linalg.norm(z);y=np.cross(z,x);basis=np.column_stack([x,y,z]);root=weights@B;ids[pts]=tri;bc[pts]=weights;lp[pts]=(localV[pts]-root)@basis
  attach_group(ob,proxy,ids,bc,lp);attachments[name]={'actualVertices':len(V),'sourceAnchorRecord':'r139 native-lid-follow-construction.json','order':'Same actual blink surface first; original r139 armature gaze afterwards. No double application of gaze.','notFiniteContactProof':True}
 bpy.context.view_layer.update();neutral={n:float(np.linalg.norm(a.geometry(bpy.data.objects[n])[0]-baseline[n][0],axis=1).max()) for n in names};assert max(neutral.values())<2e-6,neutral
 for n in names:assert a.rawsig(bpy.data.objects[n])==raw[n],n
 assert a.a.protected()==protected
 demo=bpy.data.actions.new('AFN144_ACTUAL_CURRENT_SKIN_BLINK_DEMO');rig.animation_data.action=demo
 for f,value in [(1,0.),(5,.5),(9,1.),(13,.5),(17,0.)]:
  for p in PROPS.values():rig[p]=value;rig.keyframe_insert(data_path='["'+p+'"]',frame=f)
 rig['AFN144_priorGazeAction']=gazeAction.name;rig['AFN144_scope']='New actual-current skin blink and surface-following lashes/wet line. Recorded neutral fixed-head/neutral-eye construction only, unaccepted pending actual complete closure/intermediates/restoration and related surface evidence. Prior gaze action retained unchanged.';scene.frame_start=1;scene.frame_end=17;scene.render.fps=24;scene.frame_set(1);rig.update_tag();bpy.context.view_layer.update();bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=False)
 np.savez_compressed(E/'actual-current-blink-lineage.npz',skinWorld=W,skinTriangles=T,leftAngles=allAngles['L'],rightAngles=allAngles['R']);save('current-skin-blink-construction.json',{'actualSkin':skin.name,'actualRig':rig.name,'actualControllers':PROPS,'originalGazeAction':gazeAction.name,'newBlinkDemoAction':demo.name,'actualNativeDomains':records,'actualAttachments':attachments,'hiddenPreGazeSurfaceHelper':proxy.name,'actualDisplayedSkinAlsoHasOwnBlinkModifier':True,'neutralActualGeometryErrorsM':neutral,'numericEvaluationBoundNotContactToleranceM':2e-6,'originalRawMeshTopologyUVAndOriginalMaterialsRetained':True,'noAnalyticClosingCapOrPlateOrHiddenHeadControl':True,'appearanceFunctionContactRuntimeAccepted':False,'secondsBeforePreview':time.time()-tick})
 save('a-build-summary.json',{'source':str(SRC),'output':str(OUT),'sha256':a.a.sha(OUT),'bytes':OUT.stat().st_size,'actualSkin':skin.name,'actualRig':rig.name,'actualControllers':PROPS,'originalGazeAction':gazeAction.name,'newBlinkDemoAction':demo.name,'completeAppearanceOperationContactRuntimeUnaccepted':True,'oneCompleteCandidate':True,'secondsBeforePreview':time.time()-tick});views=[]
 for view in ['face','body-face','profile','oblique','back']:views.append(a.b.u.v.image('a-current-skin-blink',view));save('a-view-controls.json',views)
 motion=[]
 for f in [5,9,13,17]:
  scene.frame_set(f);bpy.context.view_layer.update()
  for v in ['face','body-face']:
   row=a.b.u.v.image('blink-%03d'%f,v);row['actualBlink']={s:float(rig[p]) for s,p in PROPS.items()};motion.append(row);save('actual-blink-motion-controls.json',motion)
 scene.frame_set(9);bpy.context.view_layer.update();save('actual-closed-profile-control.json',a.b.u.v.image('closed-blink','profile'));scene.frame_set(1);bpy.context.view_layer.update();assert a.a.protected()==protected;print('R144_ACTUAL_CURRENT_SKIN_BLINK_COMPLETE_HEAD_BODY_MOTION_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
