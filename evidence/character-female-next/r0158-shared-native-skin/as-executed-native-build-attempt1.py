"""One native Skin with explicit shared indices and actual raw edit delta.
All source faces remain; only the536 semantically identified duplicate boundary
pairs coalesce. Pose construction remains an explicit source, not an accepted
blink/finite-contact/runtime claim.
"""
from pathlib import Path
import bpy,numpy as np,json,datetime,time,importlib.util,collections
R=Path('D:/Download/Aevrynd');C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');M=C/'assets-source/aevrynd-character/female-next';E=C/'evidence/character-female-next/r0158-shared-native-skin';OUT=M/'r0158-source/aevrynd-female-next-r0158-a-shared-native-skin.blend'
sp=importlib.util.spec_from_file_location('r158base',R/'scripts/character-next/build-female-next-r0157-outer-lid-retopology.py');h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h);a=h.a
def save(n,x):(E/n).write_bytes((json.dumps(x,indent=2,default=lambda x:x.tolist() if isinstance(x,np.ndarray) else x.item() if isinstance(x,np.generic) else str(x))+'\n').encode())
def arr(data,prop,N,k=1,dtype='f4'):
 out=np.empty((N,k) if k!=1 else N,dtype);data.foreach_get(prop,out.ravel());return out
def position_graph(skin,source):
 g,n,L=h.group('AFN158_SHARED_NATIVE_SKIN_POSE_AND_REAL_EDIT_DELTA');inp=n.new('NodeGroupInput');out=n.new('NodeGroupOutput');position=n.new('GeometryNodeInputPosition').outputs[0];pose=h.sample(n,L,h.info(n,source),position,h.named(n,'AFN158_POSE_SOURCE_VERTEX','INT'),'FLOAT_VECTOR');delta=h.vec(n,L,'SUBTRACT',position,h.named(n,'AFN158_EDIT_REST_POSITION','FLOAT_VECTOR'));target=h.vec(n,L,'ADD',pose,delta);setp=n.new('GeometryNodeSetPosition');L.new(inp.outputs['Geometry'],setp.inputs['Geometry']);L.new(target,setp.inputs['Position']);L.new(setp.outputs['Geometry'],out.inputs['Geometry']);skin.modifiers.new('AFN158_ACTUAL_SHARED_SKIN_POSE_AND_VERTEX_EDIT','NODES').node_group=g
def main():
 tick=time.time();assert not OUT.exists();b=json.loads((R/'Evidence/character-female-next/r0157-outer-lid-retopology/a-build-summary.json').read_text());bpy.ops.wm.open_mainfile(filepath=b['output']);s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();skin=bpy.data.objects[b['actualSkin']];rig=bpy.data.objects[b['actualRig']];patch=bpy.data.objects[b['actualPatch']];reference=bpy.data.objects['AFN157_PRE_RETOPOLOGY_NATIVE_BIND_REFERENCE'];assert np.max(abs(np.array(skin.matrix_world)-np.eye(4)))<1e-9;source=skin.copy();source.name='AFN158_R157_POSE_CONSTRUCTION_REFERENCE';s.collection.objects.link(source);source.hide_render=True;source.hide_set(False);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();ev=source.evaluated_get(dg);old=ev.to_mesh(preserve_all_data_layers=True,depsgraph=dg);V=arr(old.vertices,'co',len(old.vertices),3);F=[list(f.vertices) for f in old.polygons];lookup=collections.defaultdict(list)
 for i,p in enumerate(V):lookup[tuple(p)].append(i)
 oldRef=a.geometry(reference)[0];z=np.load(R/'Evidence/character-female-next/r0157-outer-lid-retopology/authored-outer-lid-patch.npz');boundary=z['originalBoundaryVertices'];representative=np.arange(len(V),'i4');pairRows=[];seen=set()
 for original in boundary:
  pair=lookup[tuple(oldRef[int(original)])];assert len(pair)==2 and not set(pair)&seen;seen.update(pair);keep,drop=sorted(pair);representative[drop]=keep;pairRows.append({'originalSourceVertex':int(original),'sourceOutputPair':pair,'retainedOutputVertex':keep})
 keep=np.flatnonzero(representative==np.arange(len(V)));compact=np.full(len(V),-1,'i4');compact[keep]=np.arange(len(keep));mapping=compact[representative];P=V[keep];newF=[mapping[f].tolist() for f in F];assert all(len(set(f))==len(f) for f in newF);assert len(V)-len(P)==536
 # Identify the actual contributing new lid triangles, not a guessed index range.
 PV,PT=a.geometry(patch);patchSignatures={tuple(sorted(tuple(PV[i]) for i in tri)) for tri in PT};patchFaces={f.index for f in old.polygons if len(f.vertices)==3 and tuple(sorted(tuple(V[i]) for i in f.vertices)) in patchSignatures};assert len(patchFaces)==len(PT)
 # Establish orientation of patch faces against retained native Skin, without
 # touching any retained body/cavity winding, UV correspondence or surface.
 edges=collections.defaultdict(list)
 for fi in patchFaces:
  f=newF[fi]
  for u,v in zip(f,f[1:]+f[:1]):edges[tuple(sorted((u,v)))].append((fi,1 if u<v else -1))
 flips={};queue=[]
 for fi,f in enumerate(newF):
  if fi in patchFaces:continue
  for u,v in zip(f,f[1:]+f[:1]):
   edge=tuple(sorted((u,v)))
   if edge in edges:
    sign=1 if u<v else -1
    for pi,ps in edges[edge]:
     want=ps==sign
     if pi in flips:assert flips[pi]==want,'Retained boundary orientation is inconsistent'
     else:flips[pi]=want;queue.append(pi)
 neighbours=collections.defaultdict(list)
 for edge,rows in edges.items():
  if len(rows)==2:
   (f0,s0),(f1,s1)=rows;neighbours[f0].append((f1,s0==s1));neighbours[f1].append((f0,s0==s1))
 while queue:
  fi=queue.pop()
  for other,opposite in neighbours[fi]:
   want=flips[fi]^opposite
   if other in flips:assert flips[other]==want,'Authored patch orientation is inconsistent'
   else:flips[other]=want;queue.append(other)
 assert set(flips)==patchFaces;loopOrder=[]
 for fi,f in enumerate(old.polygons):
  order=list(range(f.loop_start,f.loop_start+f.loop_total))
  if flips.get(fi,False):newF[fi].reverse();order.reverse()
  loopOrder.extend(order)
 loopOrder=np.array(loopOrder,'i4');oldUV={u.name:arr(u.data,'uv',len(u.data),2) for u in old.uv_layers};normal=arr(old.corner_normals,'vector',len(old.loops),3);normal=normal[loopOrder]
 for fi in patchFaces:
  f=old.polygons[fi];normal[f.loop_start:f.loop_start+f.loop_total]=0.
 materials=list(old.materials);matIndices=np.array([f.material_index for f in old.polygons]);smooth=np.array([f.use_smooth for f in old.polygons]);mesh=bpy.data.meshes.new('AFN158_ONE_NATIVE_SKIN_EXPLICIT_SHARED_BOUNDARIES');mesh.from_pydata(P.tolist(),[],newF);mesh.update()
 for i,mat in enumerate(materials):
  mesh.materials.append(mat if mat is not None else next(x for x in materials if x is not None))
  if mat is None:mesh.materials[i]=None
 for i,f in enumerate(mesh.polygons):f.material_index=int(matIndices[i]);f.use_smooth=bool(smooth[i])
 for name,data in oldUV.items():mesh.uv_layers.new(name=name).data.foreach_set('uv',data[loopOrder].ravel())
 mesh.normals_split_custom_set(normal.tolist());mesh.attributes.new('AFN158_POSE_SOURCE_VERTEX','INT','POINT').data.foreach_set('value',keep.astype('i4'));mesh.attributes.new('AFN158_EDIT_REST_POSITION','FLOAT_VECTOR','POINT').data.foreach_set('vector',P.ravel());save('direct-native-shared-skin-authoring-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originalStartedUTC':'2026-10-22T09:51:48+00:00','actualNativeMesh':mesh.name,'oldVertices':len(V),'newVertices':len(P),'explicitBoundaryPairs':len(pairRows),'allSourceFacesRetained':len(newF)==len(F),'sharedPairsUseKnownSourceBoundaryIdentityNotDistanceTolerance':True,'patchFacesOrientedAgainstRetainedBody':len(patchFaces),'patchFaceWindingCorrections':sum(flips.values()),'protectedBodyUVAndCornerNormalsRetained':True,'newPatchCornerNormalsAutomaticForNewPoseGeometry':True,'allKnownContactsRemainUnaccepted':True})
 # Preserve genuine existing deform-group data for authoring/export; the active
 # pose path is the explicit source-index map, not a hidden disabled Armature.
 names=[g.name for g in reference.vertex_groups];weights=np.zeros((len(oldRef),len(names)),'f4')
 for v in reference.data.vertices:
  for gr in v.groups:weights[v.index,gr.group]=gr.weight
 refLookup={tuple(p):i for i,p in enumerate(oldRef)};patchLookup={tuple(p):i for i,p in enumerate(PV)};newW=np.empty((len(P),len(names)),'f4');patchSources=z['sourceVertices'];patchBC=z['barycentric'];nativeCount=0
 for i,p in enumerate(P):
  key=tuple(p)
  if key in refLookup:newW[i]=weights[refLookup[key]];nativeCount+=1
  else:pi=patchLookup[key];newW[i]=patchBC[pi]@weights[patchSources[pi]]
 assert np.isfinite(newW).all() and (newW>=0).all();skin.modifiers.clear();skin.data=mesh;skin.vertex_groups.clear()
 for col,name in enumerate(names):
  gr=skin.vertex_groups.new(name=name);active=np.flatnonzero(newW[:,col]>0)
  for val in np.unique(newW[active,col]):gr.add(active[newW[active,col]==val].tolist(),float(val),'REPLACE')
 position_graph(skin,source);source.hide_set(True)
 # Rebind the real attachment sample indices to actual shared Skin vertices.
 patchToNative=[]
 for p in PV:
  ids=np.unique(mapping[lookup[tuple(p)]]);assert len(ids)==1;patchToNative.append(int(ids[0]))
 patchToNative=np.array(patchToNative,'i4');attachmentRows=[]
 for name in h.h.h.ATTACH:
  ob=bpy.data.objects[name];g=next(m.node_group for m in ob.modifiers if m.type=='NODES');table=next(n.inputs['Object'].default_value for n in g.nodes if n.bl_idname=='GeometryNodeObjectInfo' and n.inputs['Object'].default_value!=patch)
  for k in range(3):
   attr=table.data.attributes['AFN155_V'+str(k)];indices=arr(attr.data,'value',len(attr.data),dtype='i4');attr.data.foreach_set('value',patchToNative[indices])
  for node in g.nodes:
   if node.bl_idname=='GeometryNodeObjectInfo' and node.inputs['Object'].default_value==patch:node.inputs['Object'].default_value=skin
  table.data.update();attachmentRows.append({'object':name,'actualSampledSkin':skin.name,'oldPatchIndicesRemappedToSharedNativeSkin':True})
 ev.to_mesh_clear();bpy.context.view_layer.update();NV,NT=a.geometry(skin);assert len(NV)==len(P) and np.array_equal(NV,P);boundaryMap={row['originalSourceVertex']:int(mapping[row['retainedOutputVertex']]) for row in pairRows};loops=json.loads((R/'Evidence/character-female-next/r0157-outer-lid-retopology/actual-outer-lid-boundaries.json').read_text());boundaryEdges={tuple(sorted((boundaryMap[u],boundaryMap[v]))):0 for r in loops['reports'] for loop in r['loops'] for u,v in zip(loop['originalVertexIds'],loop['originalVertexIds'][1:]+loop['originalVertexIds'][:1])};balance={k:0 for k in boundaryEdges}
 for f in mesh.polygons:
  ids=list(f.vertices)
  for u,v in zip(ids,ids[1:]+ids[:1]):
   key=tuple(sorted((u,v)))
   if key in boundaryEdges:boundaryEdges[key]+=1;balance[key]+=1 if u<v else -1
 assert all(n==2 for n in boundaryEdges.values()) and all(n==0 for n in balance.values());save('shared-native-skin-construction.json',{'actualSkin':skin.name,'actualPoseConstructionSource':source.name,'oldVertexCount':len(V),'newNativeVertexCount':len(P),'allOriginalPolygonCountRetained':len(newF),'all536SourceBoundaryPairsActuallyShareNativeVertexIndices':True,'allSharedBoundaryEdgesHaveTwoOppositeDirectedIncidentFaces':True,'noDistanceWeldNoOmittedFacesNoContactToleranceChange':True,'actualAttachmentBindings':attachmentRows,'retainedNativeGroupNames':names,'originalGroupWeightsTransferredVertices':nativeCount,'newOuterVerticesBarycentricWeights':len(P)-nativeCount,'currentPosePath':'Actual original rig -> explicit preserved construction source -> shared native Skin source-index field plus raw input-position edit delta. New deform weights retained for future export, no new Armature/runtime acceptance claimed.','sourceShapeAndUVKept':True});np.savez_compressed(E/'explicit-shared-skin-lineage.npz',retainedSourceVertices=keep,sourceToNative=mapping,originalBoundaryVertices=np.array(list(boundaryMap),'i4'),nativeBoundaryVertices=np.array(list(boundaryMap.values()),'i4'),patchToNative=patchToNative)
 for lib in bpy.data.libraries:
  target=M/'r0152-source/aevrynd-female-next-r0152-a-layered-native-groom.blend';assert a.a.sha(target)=='6d14dcca0c0a3dc2a8be613d92377a663522dbb8d31a3f26ec894132723f1480';lib.filepath=str(target)
 bpy.context.view_layer.update();bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=True);save('a-build-summary.json',{'source':b['output'],'output':str(OUT),'engineAlias':str(R/'engine/assets/characters/female-next/source/r0158-source'/OUT.name),'sha256':a.a.sha(OUT),'bytes':OUT.stat().st_size,'actualSkin':skin.name,'actualRig':rig.name,'actualPoseSource':source.name,'actualNativeVertices':len(P),'originalGazeAction':b['originalGazeAction'],'blinkAction':rig.animation_data.action.name,'appearanceBlinkContactRuntimeNotAccepted':True,'secondsBeforePreview':time.time()-tick});a.b.u.v.E=E;views=[]
 for f,view,tag in [(11,'face','a-shared-closed'),(11,'body-face','a-shared-closed'),(1,'face','a-shared-neutral'),(9,'face','a-shared-half')]:
  s.frame_set(f);bpy.context.view_layer.update();_=a.geometry(skin)
  for name in h.h.h.ATTACH:_=a.geometry(bpy.data.objects[name])
  control=a.b.u.v.image(tag,view);control.update(frame=f,blink=[float(rig[x]) for x in ['blink_L','blink_R']]);views.append(control);save('actual-shared-skin-view-controls.json',views)
 s.frame_set(1);bpy.context.view_layer.update();print('R158_COMPLETE_NATIVE_SHARED_SKIN_HEAD_BODY_NEUTRAL_HALF_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
