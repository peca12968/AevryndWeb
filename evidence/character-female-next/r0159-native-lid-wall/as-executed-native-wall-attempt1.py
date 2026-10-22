"""Rebuild actual cavity topology and rigid margin frames on same woman."""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,collections,datetime,time,math
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');R=Path('D:/Download/Aevrynd');E=C/'evidence/character-female-next/r0159-native-lid-wall';OUT=C/'assets-source/aevrynd-character/female-next/r0159-source/aevrynd-female-next-r0159-a-native-lid-wall.blend'
sp=importlib.util.spec_from_file_location('r159author',C/'scripts/character-next/build-female-next-r0158-shared-native-skin.py');h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h);h.E=E;a=h.a;g=h.h
def attr(mesh,name,values,domain='POINT'):
 vector=values.ndim==2;typ='FLOAT_VECTOR' if vector else 'INT' if values.dtype.kind in 'iu' else 'FLOAT';at=mesh.attributes.new(name,typ,domain);at.data.foreach_set('vector' if vector else 'value',values.astype('i4' if typ=='INT' else 'f4').ravel())
def graph(skin,source):
 tree,n,L=g.group('AFN159_CONNECTED_NATIVE_WALL_DOMAIN_POSE_AND_RAW_EDIT');inp=n.new('NodeGroupInput');out=n.new('NodeGroupOutput');pos=n.new('GeometryNodeInputPosition').outputs[0];sample=g.sample(n,L,g.info(n,source),pos,g.named(n,'AFN159_SOURCE_INDEX','INT'),'FLOAT_VECTOR');delta=g.vec(n,L,'SUBTRACT',sample,g.named(n,'AFN159_SOURCE_REST','FLOAT_VECTOR'));target=g.vec(n,L,'ADD',pos,g.scale(n,L,delta,g.named(n,'AFN159_POSE_INFLUENCE')));p=n.new('GeometryNodeSetPosition');L.new(inp.outputs['Geometry'],p.inputs['Geometry']);L.new(target,p.inputs['Position']);L.new(p.outputs['Geometry'],out.inputs['Geometry']);skin.modifiers.new('AFN159_ACTUAL_NATIVE_WALL_AND_INPUT_EDIT','NODES').node_group=tree
def lash_graph(ob,table,skin):
 tree,n,L=g.group('AFN159_'+ob.name+'_ORTHONORMAL_ACTUAL_MARGIN_FRAME');inp=n.new('NodeGroupInput');out=n.new('NodeGroupOutput');idx=n.new('GeometryNodeInputIndex').outputs[0];tableGeo=g.info(n,table);skinGeo=g.info(n,skin);pos=n.new('GeometryNodeInputPosition').outputs[0]
 def read(name,typ='FLOAT'):return g.sample(n,L,tableGeo,g.named(n,name,typ),idx,typ)
 def point(index):return g.sample(n,L,skinGeo,pos,index,'FLOAT_VECTOR')
 bc=n.new('ShaderNodeSeparateXYZ');L.new(read('AFN155_BC','FLOAT_VECTOR'),bc.inputs[0]);root=None
 for k in range(3):
  part=g.scale(n,L,point(read('AFN155_V'+str(k),'INT')),bc.outputs[k]);root=part if root is None else g.vec(n,L,'ADD',root,part)
 tangent=g.vec(n,L,'NORMALIZE',g.vec(n,L,'SUBTRACT',point(read('AFN159_T1','INT')),point(read('AFN159_T0','INT'))));arm=g.vec(n,L,'SUBTRACT',point(read('AFN159_DEPTH','INT')),root);normal=g.vec(n,L,'NORMALIZE',g.vec(n,L,'CROSS_PRODUCT',tangent,arm));depth=g.vec(n,L,'NORMALIZE',g.vec(n,L,'CROSS_PRODUCT',normal,tangent));local=n.new('ShaderNodeSeparateXYZ');L.new(read('AFN159_LOCAL_OFFSET','FLOAT_VECTOR'),local.inputs[0]);offset=None
 for k,axis in enumerate([tangent,depth,normal]):
  part=g.scale(n,L,axis,local.outputs[k]);offset=part if offset is None else g.vec(n,L,'ADD',offset,part)
 target=g.vec(n,L,'ADD',root,offset);p=n.new('GeometryNodeSetPosition');L.new(inp.outputs['Geometry'],p.inputs['Geometry']);L.new(read('AFN155_ACTIVE'),p.inputs['Selection']);L.new(target,p.inputs['Position']);L.new(p.outputs['Geometry'],out.inputs['Geometry']);ob.modifiers.new('AFN159_ACTUAL_MARGIN_RIGID_ATTACHMENT','NODES').node_group=tree
def main():
 tick=time.time();assert not OUT.exists();before=json.loads((E/'before.json').read_text());bpy.ops.wm.open_mainfile(filepath=before['source']);s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();skin=bpy.data.objects['AFN126_COMPLETE_WOMAN_BODY_AND_ARTIST_HEAD'];rig=bpy.data.objects['AFN138_ACTUAL_CURRENT_GAZE_RIG'];V,T=a.geometry(skin);old=skin.data;source=skin.copy();source.name='AFN159_PRE_WALL_NATIVE_POSE_REFERENCE';s.collection.objects.link(source);source.hide_render=True;source.hide_set(True);faces={f.index:list(f.vertices) for f in old.polygons if f.material_index==0};touch=collections.defaultdict(list)
 for fi,f in faces.items():
  for vi in f:touch[vi].append(fi)
 def component(seed):
  domain={seed};queue=[seed]
  while queue:
   fi=queue.pop()
   for vi in faces[fi]:
    for other in touch[vi]:
     if other not in domain:domain.add(other);queue.append(other)
  return domain
 domains=[component(187115)];center=V[faces[187115]].mean(0);center[0]*=-1;other=min((fi for fi in faces if V[faces[fi],0].mean()>0),key=lambda fi:np.linalg.norm(V[faces[fi]].mean(0)-center));domains.append(component(other));assert not domains[0]&domains[1];removed=set.union(*domains);P=V.tolist();sourceIndex=list(range(len(V)));sourceRest=V.tolist();influence=[1.]*len(V);newFaces=[];newUV=[];regions=[];firstRows=[];eyeV=np.concatenate([a.geometry(bpy.data.objects[n])[0] for n in a.MOVING]);rows=16
 for domain in domains:
  edges=collections.Counter(tuple(sorted((u,v))) for fi in domain for u,v in zip(faces[fi],faces[fi][1:]+faces[fi][:1]));adj=collections.defaultdict(list)
  for (u,v),count in edges.items():
   if count==1:adj[u].append(v);adj[v].append(u)
  assert all(len(x)==2 for x in adj.values());first=min(adj);loop=[first];prev=None;cur=first
  while True:
   nxt=next(v for v in adj[cur] if v!=prev)
   if nxt==first:break
   loop.append(nxt);prev,cur=cur,nxt
  assert len(loop)==len(adj);sign=np.sign(V[loop,0].mean());eye=eyeV[eyeV[:,0]*sign>0];bone=rig.data.bones['AFN138_EYE_'+('L' if sign>0 else 'R')];center=np.array(bone.head_local);radius=float(np.linalg.norm(eye-center,axis=1).max())+.00025;B=V[loop];D=B-center;r0=np.linalg.norm(D,axis=1);polar=np.arccos(np.clip(D[:,1]/r0,-1,1));azimuth=D.copy();azimuth[:,1]=0;azimuth/=np.linalg.norm(azimuth,axis=1)[:,None];rings=[loop];startFace=len(newFaces)
  for j in range(1,rows):
   t=j/rows;theta=polar*(1-t);blend=min(1,t/.15);blend=blend*blend*(3-2*blend);rad=r0*(1-blend)+radius*blend;dirs=azimuth*np.sin(theta)[:,None];dirs[:,1]=np.cos(theta);points=center+rad[:,None]*dirs;ring=[]
   for k,p in enumerate(points):ring.append(len(P));P.append(p.tolist());sourceIndex.append(loop[k]);sourceRest.append(V[loop[k]].tolist());influence.append(max(0,1-t/.5)**2)
   rings.append(ring)
   for k in range(len(loop)):
    nxt=(k+1)%len(loop);newFaces.append([rings[-2][k],rings[-2][nxt],ring[nxt],ring[k]]);newUV.append([[k/len(loop),(j-1)/rows],[nxt/len(loop),(j-1)/rows],[nxt/len(loop),t],[k/len(loop),t]])
  pole=len(P);P.append((center+np.array([0,radius,0])).tolist());sourceIndex.append(loop[0]);sourceRest.append(V[loop[0]].tolist());influence.append(0.)
  for k in range(len(loop)):
   nxt=(k+1)%len(loop);newFaces.append([rings[-1][k],rings[-1][nxt],pole]);newUV.append([[k/len(loop),(rows-1)/rows],[nxt/len(loop),(rows-1)/rows],[.5,1.]])
  # Match winding against actual retained perimeter faces.
  u,v=loop[:2];retained=[f for f in old.polygons if f.index not in removed and u in f.vertices and v in f.vertices];assert len(retained)==1;ids=list(retained[0].vertices);same=any(x==u and y==v for x,y in zip(ids,ids[1:]+ids[:1]))
  if same:
   for fi in range(startFace,len(newFaces)):newFaces[fi].reverse();newUV[fi].reverse()
  firstRows.append((np.array(loop,'i4'),np.array(rings[1],'i4')));regions.append({'side':'L' if sign>0 else 'R','originalFacesReplaced':len(domain),'boundaryVertices':len(loop),'newWallFaces':len(newFaces)-startFace,'center':center.tolist(),'maxActualOcularRadiusPlus250umM':radius,'structuredDepthRings':rows,'deepLiningBlinkDisplacementZeroAfterHalfDepth':True})
 keep=[f.index for f in old.polygons if f.index not in removed];oldLoopOrder=[li for fi in keep for li in range(old.polygons[fi].loop_start,old.polygons[fi].loop_start+old.polygons[fi].loop_total)];F=[list(old.polygons[fi].vertices) for fi in keep]+newFaces;mesh=bpy.data.meshes.new('AFN159_NATIVE_CONNECTED_MARGIN_AND_DEPTH_WALL');mesh.from_pydata(P,[],F);mesh.update()
 for mat in old.materials:mesh.materials.append(mat if mat else next(m for m in old.materials if m))
 for i,mat in enumerate(old.materials):
  if mat is None:mesh.materials[i]=None
 for i,f in enumerate(mesh.polygons):f.material_index=old.polygons[keep[i]].material_index if i<len(keep) else 0;f.use_smooth=True if i>=len(keep) else old.polygons[keep[i]].use_smooth
 added=len(P)-len(V);uvAdded=np.concatenate([np.array(x,'f4') for x in newUV])
 for uv in old.uv_layers:
  values=h.arr(uv.data,'uv',len(uv.data),2);dest=mesh.uv_layers.new(name=uv.name);dest.data.foreach_set('uv',np.concatenate([values[oldLoopOrder],uvAdded]).ravel());dest.active_render=uv.active_render;dest.active_clone=uv.active_clone
 mesh.uv_layers.active_index=old.uv_layers.active_index
 for name in ['AFN113_NATIVE_COLOR_WEIGHT','AFN126_NECK_BLEND']:
  val=h.arr(old.attributes[name].data,'value',len(V));attr(mesh,name,np.r_[val,val[np.array(sourceIndex[len(V):])]])
 normal=h.arr(old.corner_normals,'vector',len(old.loops),3);mesh.normals_split_custom_set(np.concatenate([normal[oldLoopOrder],np.zeros((len(uvAdded),3))]).tolist());attr(mesh,'AFN159_SOURCE_INDEX',np.array(sourceIndex,'i4'));attr(mesh,'AFN159_SOURCE_REST',np.array(sourceRest,'f4'));attr(mesh,'AFN159_POSE_INFLUENCE',np.array(influence,'f4'));skin.modifiers.clear();skin.data=mesh;graph(skin,source);bpy.context.view_layer.update();NV,NT=a.geometry(skin);assert np.array_equal(NV[:len(V)],V);h.save('direct-wall-topology-authoring-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originalStartedUTC':before['startedUTC'],'actualNativeSkin':skin.name,'replacedOriginalWallFaces':len(removed),'newStructuredWallFaces':len(newFaces),'oldAllSkinVertices':len(V),'newAllSkinVertices':len(NV),'retainedOriginalPositionsExact':True,'actualConstruction':regions,'changedFailedPremise':'Old146 posterior-only fix lacked current157 outer tissue and158 shared native boundary; this source replaces full irregular wall topology, changes its deformation domain, and derives rigid fibre frames from real new depth rows rather than old156 triangle shear.','materialsLightingPaletteUnchanged':True})
 attachment=[]
 for name in a.FIXED[2:4]:
  ob=bpy.data.objects[name];previous=next(m for m in ob.modifiers if m.type=='NODES');table=next(n.inputs['Object'].default_value for n in previous.node_group.nodes if n.bl_idname=='GeometryNodeObjectInfo' and 'ATTACHMENT' in n.inputs['Object'].default_value.name);ob.modifiers.remove(previous);W,_=a.geometry(ob);N=len(W);active=h.arr(table.data.attributes['AFN155_ACTIVE'].data,'value',N);bc=h.arr(table.data.attributes['AFN155_BC'].data,'vector',N,3);ids=np.column_stack([h.arr(table.data.attributes['AFN155_V'+str(k)].data,'value',N,dtype='i4') for k in range(3)]);roots=(NV[ids]*bc[:,:,None]).sum(1);t0=np.zeros(N,'i4');t1=t0.copy();depth=t0.copy();offset=np.zeros((N,3),'f4');minimum=1.
  for row in np.flatnonzero(active>.5):
   loop,deep=firstRows[0] if roots[row,0]<0 else firstRows[1];k=int(np.linalg.norm(NV[loop]-roots[row],axis=1).argmin());t0[row]=loop[(k-2)%len(loop)];t1[row]=loop[(k+2)%len(loop)];depth[row]=deep[k];X=NV[t1[row]]-NV[t0[row]];X/=np.linalg.norm(X);arm=NV[depth[row]]-roots[row];Z=np.cross(X,arm);length=np.linalg.norm(Z);assert length>1e-8;minimum=min(minimum,float(length));Z/=length;Y=np.cross(Z,X);offset[row]=np.array([np.dot(W[row]-roots[row],axis) for axis in [X,Y,Z]])
  for key,val in [('AFN159_T0',t0),('AFN159_T1',t1),('AFN159_DEPTH',depth),('AFN159_LOCAL_OFFSET',offset)]:attr(table.data,key,val)
  table.data.update();lash_graph(ob,table,skin);bpy.context.view_layer.update();error=float(np.linalg.norm(a.geometry(ob)[0]-W,axis=1).max());assert error<2e-7;attachment.append({'object':name,'activeVertices':int((active>.5).sum()),'restPreservationMaximumM':error,'minimumActualDepthFrameArmM':minimum,'rigidOrthonormalFrameFromActualNewMarginAndDepth':True})
 h.save('native-wall-and-margin-frame-construction.json',{'regions':regions,'removedActualWallFaceIds':sorted(removed),'retainedOldFaceToNewFace':dict(enumerate(keep)),'newWallFirstPolygon':len(keep),'newWallFaceCount':len(newFaces),'newSkinVertices':len(NV),'actualAttachmentConstruction':attachment,'noNewCoverShellOrGlobalPushOrReducedAction':True,'actualOriginalWallReplacedNotExcludedFromTesting':True,'gazeWholeFiniteContactUnaccepted':True});np.savez_compressed(E/'new-wall-source-map.npz',retainedOldFaces=np.array(keep,'i4'),sourceIndex=np.array(sourceIndex,'i4'),newWallFaces=np.arange(len(keep),len(F),dtype='i4'));s.frame_set(1);bpy.context.view_layer.update();bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=True);h.save('a-build-summary.json',{'source':before['source'],'output':str(OUT),'engineAlias':str(R/'engine/assets/characters/female-next/source/r0159-source'/OUT.name),'sha256':a.a.sha(OUT),'bytes':OUT.stat().st_size,'actualSkin':skin.name,'actualRig':rig.name,'actualPoseSource':source.name,'actualNativeVertices':len(NV),'originalGazeAction':'AFN138_NATIVE_CURRENT_GAZE_DEMO','blinkAction':rig.animation_data.action.name,'unaccepted':True,'secondsBeforePreview':time.time()-tick});assert OUT.stat().st_size<before['sourceBudgetBytes'];a.b.u.v.E=E;views=[]
 for frame,view,tag in [(11,'face','a-wall-closed'),(11,'body-face','a-wall-closed'),(1,'face','a-wall-neutral'),(9,'face','a-wall-half')]:
  s.frame_set(frame);bpy.context.view_layer.update();_=a.geometry(skin)
  for name in a.FIXED[2:4]:_=a.geometry(bpy.data.objects[name])
  control=a.b.u.v.image(tag,view);control.update(frame=frame,blink=[float(rig[k]) for k in ['blink_L','blink_R']]);views.append(control);h.save('actual-wall-preview-controls.json',views)
 s.frame_set(1);bpy.context.view_layer.update();print('R159_COMPLETE_NATIVE_WALL_AND_MARGIN_FRAME_HEAD_BODY_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
