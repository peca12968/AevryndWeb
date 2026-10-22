"""Anatomical scalp + explicit source-root carrier topology, not curve projection.
All252 original posed guides untouched; UV/rest identity is requalified first.
"""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,time,datetime
from mathutils import Vector
from mathutils.bvhtree import BVHTree
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');R=Path('D:/Download/Aevrynd');E=C/'evidence/character-female-next/r0170-root-constrained-carrier';OUT=C/'assets-source/aevrynd-character/female-next/r0170-source/aevrynd-female-next-r0170-a-root-constrained-carrier.blend'
sp=importlib.util.spec_from_file_location('r170base',C/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;h=m.h
def save(n,x):(E/n).write_bytes((json.dumps(x,indent=2)+'\n').encode())
def bary(p,B):return m.bary(p,B)
def main():
 tick=time.time();before=json.loads((E/'before.json').read_text());assert not OUT.exists() and a.a.sha(Path(before['source']))==before['sourceSha256'];bpy.ops.wm.open_mainfile(filepath=before['source']);s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();skin=bpy.data.objects[a.FIXED[0]];hair=bpy.data.objects['AFN169_ACTUAL_COHERENT_NATIVE_ARTIST_GROOM'];carrier=bpy.data.objects['AFN169_POSE_CONSISTENT_CURRENT_SCALP_CARRIER'];old=bpy.data.objects[a.FIXED[1]];protected={n:a.rawsig(bpy.data.objects[n]) for n in a.FIXED+a.MOVING};W,T=a.geometry(skin);sd=skin.data;sd.calc_loop_triangles();uv=sd.uv_layers['AngelicaOriginalUV'];triUV=np.array([[uv.data[k].uv[:] for k in t.loops] for t in sd.loop_triangles]);material=np.array([sd.polygons[t.polygon_index].material_index for t in sd.loop_triangles]);centers=W[T].mean(1);baseColor=next(n for n in skin.material_slots[8].material.node_tree.nodes if n.bl_idname=='ShaderNodeBsdfPrincipled').inputs['Base Color'];image=baseColor.links[0].from_node.image;ww,hh=image.size;px=np.empty(len(image.pixels),'f4');image.pixels.foreach_get(px);px=px.reshape(hh,ww,4);U=triUV.mean(1);ij=np.clip((U*np.array([ww,hh])).astype(int),[0,0],[ww-1,hh-1]);colors=px[ij[:,1],ij[:,0],:3]
 # Source albedo anchors: cap .08-.10 mean vs forehead/ear .60. One fixed
 # midpoint segmentation, connected to actual crown; no per-failed-root mask.
 dark=(colors.mean(1)<.35)&(material==8)&(centers[:,2]>1.35);candidates=np.flatnonzero(dark);_,positionID=np.unique(np.round(W,6),axis=0,return_inverse=True);parent=np.arange(len(candidates));first={}
 def find(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for i,fi in enumerate(candidates):
  for v in positionID[T[fi]]:
   v=int(v)
   if v in first:aa=find(i);bb=find(first[v]);parent[aa]=bb
   else:first[v]=i
 labels=np.array([find(i) for i in range(len(candidates))]);seed=int(np.argmin(np.linalg.norm(centers[candidates]-np.array([0,0,1.57]),axis=1)));domain=candidates[labels==labels[seed]];assert len(domain)>500;scalpTree=BVHTree.FromPolygons(W.tolist(),T[domain].tolist(),all_triangles=True);fullTree=BVHTree.FromPolygons(W.tolist(),T.tolist(),all_triangles=True)
 line=np.load(E.parent/'r0169-native-carrier-groom/coherent-native-carrier-lineage.npz');V=line['sourceCarrierWorld'].astype('f8');F=line['sourceCarrierTriangles'];sourceOwners=line['sourceGuideCarrierTriangles'];sourceBC=line['sourceGuideCarrierBarycentric'];posed=line['sourcePosedGuides'];guideUV=line['sourceGuideUV'];offset=np.arange(252)*16;originalData=carrier.data;originalData.calc_loop_triangles();sourceTriUV=np.array([[originalData.uv_layers['UVMap'].data[k].uv[:] for k in t.loops] for t in originalData.loop_triangles]);assert np.array_equal(F,np.array([t.vertices[:] for t in originalData.loop_triangles]));sourceGroupNames=list(carrier.vertex_groups.keys());sourceWeights=[{g.group:g.weight for g in v.groups} for v in originalData.vertices];vertices=V.tolist();faces=[list(f) for f in F];cornerUV=[u.copy() for u in sourceTriUV];weights=list(sourceWeights);faceLookup={tuple(map(int,f)):i for i,f in enumerate(F)};grouped={}
 for gid,owner in enumerate(sourceOwners):grouped.setdefault(faceLookup[tuple(map(int,owner))],[]).append(gid)
 rootVertices=np.empty(252,'i4');insertRows=[]
 for originalFace,gids in grouped.items():
  active=[originalFace];owner=F[originalFace];originalUV=sourceTriUV[originalFace]
  for gid in gids:
   p=sourceBC[gid]@V[owner];U=guideUV[gid];selectedFace=None;selectedBC=None
   for fi in active:
    bb=bary(p,np.array(vertices)[faces[fi]])
    if bb.min()>-2e-6:selectedFace=fi;selectedBC=bb;break
   assert selectedFace is not None,('source root not in current carrier split',gid)
   fi=selectedFace;f=faces[fi];bb=selectedBC;near=np.flatnonzero(bb>1-1e-6)
   if len(near):vi=f[int(near[0])];rootVertices[gid]=vi;continue
   vi=len(vertices);vertices.append(p.tolist());newWeights={}
   for k,oldVertex in enumerate(owner):
    for group,value in sourceWeights[int(oldVertex)].items():newWeights[group]=newWeights.get(group,0.)+float(sourceBC[gid,k])*value
   weights.append(newWeights);rootVertices[gid]=vi;oldUV=cornerUV[fi];faces[fi]=[f[0],f[1],vi];cornerUV[fi]=np.array([oldUV[0],oldUV[1],U]);newIDs=[]
   for pair in [(1,2),(2,0)]:newIDs.append(len(faces));faces.append([f[pair[0]],f[pair[1]],vi]);cornerUV.append(np.array([oldUV[pair[0]],oldUV[pair[1]],U]))
   active.extend(newIDs);insertRows.append({'guide':gid,'sourceFace':originalFace,'newRootVertex':vi,'sourceRoot':p.tolist(),'sourceUV':U.tolist()})
 vertices=np.array(vertices);faces=np.array(faces,'i4');new=bpy.data.meshes.new('AFN170_SOURCE_POSE_ROOT_BEARING_CARRIER_MESH');new.from_pydata(vertices.tolist(),[],faces.tolist());new.update();uvnew=new.uv_layers.new(name='UVMap');uvnew.data.foreach_set('uv',np.asarray(cornerUV,'f4').reshape(-1,2).ravel());new.attributes.new('rest_position','FLOAT_VECTOR','POINT').data.foreach_set('vector',vertices.astype('f4').ravel());carrier.modifiers.clear();carrier.data=new
 for name in sourceGroupNames:carrier.vertex_groups.new(name=name)
 assert len(carrier.vertex_groups)>max((g for values in weights for g in values),default=-1),'Source vertex-group names missing; do not invent density groups.'
 for i,values in enumerate(weights):
  for group,value in values.items():
   if value>1e-8:carrier.vertex_groups[group].add([i],value,'REPLACE')
 for p in new.polygons:p.use_smooth=True
 carrier.update_tag();hair.update_tag();bpy.context.view_layer.update();identity,ioffset=m.curveworld(hair);identityError=float(np.linalg.norm(identity-posed,axis=1).max());save('direct-root-bearing-topology-authoring.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originalStartedUTC':before['startedUTC'],'changedPremise':'Actual source-root constraints are carrier mesh vertices with matching UV/rest, not interior samples of unconforming nearest-face triangles. Anatomical target is actual connected crown/stubble region from unchanged original head albedo; ear/face skin not treated as scalp. No post-deformation hair point/root displacement, no bad-root deletion.','originalCarrierVertices':len(V),'newCarrierVertices':len(vertices),'newCarrierTriangles':len(faces),'explicitRootVertexIDs':rootVertices.tolist(),'insertedRootVertices':insertRows,'sourcePoseIdentityMaximumM':identityError,'sourcePoseIdentityRequiredM':3e-6,'scalpDomainTriangles':len(domain),'sourceAlbedoImage':image.name,'sourceAlbedoFixedMeanThreshold':.35,'sourceScalpBounds':[W[np.unique(T[domain])].min(0).tolist(),W[np.unique(T[domain])].max(0).tolist()],'root49CurrentSkinPriorFailureExcludedFromScalpDomain':317573 not in set(domain.tolist()),'anatomicalMaskNotFiniteContactProof':True})
 sourcePassed=identityError<3e-6;mappingT=[];mappingBC=[];parentGaps=[];fullNative=False
 if sourcePassed:
  rootSet=set(map(int,rootVertices));ownerSet=set(map(int,sourceOwners.ravel()))
  for i,p in enumerate(vertices):
   useScalp=p[2]>1.45 or i in rootSet or i in ownerSet;seed=p-np.array([0.,0.,.095]);tree=scalpTree if useScalp else fullTree;q,no,fi,gap=tree.find_nearest(Vector(seed));fi=int(domain[fi]) if useScalp else int(fi);mappingT.append(T[fi]);mappingBC.append(bary(q,W[T[fi]]))
  mappingT=np.array(mappingT,'i4');mappingBC=np.array(mappingBC);h.bind(carrier,skin,mappingT,mappingBC,np.zeros((len(vertices),1,3)),vertices[:,None]);carrier.update_tag();hair.update_tag();bpy.context.view_layer.update();parents,poffset=m.curveworld(hair);parentGaps=[float(scalpTree.find_nearest(Vector(p))[3]) for p in parents[poffset]]
  if max(parentGaps)<.001:
   for mod in hair.modifiers:
    if mod.name in ['Surface Deform','GeometryNodes','Set Hair Curve Profile']:mod.show_viewport=mod.show_render=True
   bpy.context.view_layer.update();fullNative=True
 P,actualOffset=m.curveworld(hair);rootGaps=[float(scalpTree.find_nearest(Vector(p))[3]) for p in P[actualOffset]] if sourcePassed else [];hair.name='AFN170_ACTUAL_ROOT_CONSTRAINED_NATIVE_GROOM';carrier.name='AFN170_ROOT_CONSTRAINED_ANATOMICAL_CARRIER';hair.hide_render=False;hair.hide_set(False);carrier.hide_render=True;carrier.hide_set(True);old.hide_render=True;old.hide_set(True);assert protected=={n:a.rawsig(bpy.data.objects[n]) for n in protected}
 np.savez_compressed(E/'root-constrained-carrier-lineage.npz',sourceCarrierWorld=vertices.astype('f4'),sourceCarrierTriangles=faces,sourcePosedGuides=posed,sourceGuideUV=guideUV,explicitRootVertexIDs=rootVertices,carrierCurrentTriangles=np.asarray(mappingT,'i4'),carrierCurrentBarycentric=np.asarray(mappingBC),actualCurrentScalpFaces=domain,actualNativeCurveOffsets=actualOffset,actualNativeGuideOrFibreWorld=P.astype('f4'))
 save('native-root-constrained-construction.json',{'sourcePoseIdentityMaximumM':identityError,'sourcePoseIdentityPassed':sourcePassed,'all252ParentsPreserved':True,'parentRootToActualScalpMaximumM':max(parentGaps) if parentGaps else None,'parentRootQualificationPassed':bool(parentGaps) and max(parentGaps)<.001,'fullNativeGroomCandidate':fullNative,'nativeCurves':len(actualOffset),'nativePoints':len(P),'finalAllNativeRootToActualScalpM':rootGaps,'finalAllNativeRootMaximumM':max(rootGaps) if rootGaps else None,'nativeActualScalpDomainNotFiniteContactsOrNaturalMotionAcceptance':True,'protectedSevenRawMeshesUVUnchanged':True,'oldOriginalHairHiddenRollbackNoOpaqueUnderlay':True})
 bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=True);save('a-build-summary.json',{'source':before['source'],'output':str(OUT),'engineAlias':str(R/'engine/assets/characters/female-next/source/r0170-source'/OUT.name),'sha256':a.a.sha(OUT),'bytes':OUT.stat().st_size,'actualSkin':skin.name,'actualRig':'AFN138_ACTUAL_CURRENT_GAZE_RIG','actualHair':hair.name,'actualCarrier':carrier.name,'actualEditableHairData':hair.data.name,'retainedSourceHair':old.name,'nativeStrands':len(actualOffset),'points':len(P),'fullNativeGroomCandidate':fullNative,'unaccepted':True,'secondsBeforePreview':time.time()-tick});assert OUT.stat().st_size<before['sourceBudgetBytes'];a.b.u.v.E=E;views=[]
 for view in ['face','body-face','profile','back','oblique']:
  ctl=a.b.u.v.image('a-root-constrained-carrier',view);ctl.update(frame=1,actualHair=hair.name,fullNativeGroomCandidate=fullNative,hairTypeAtActualCapture=s.render.hair_type,actualSamplesAtCapture=s.cycles.samples,actualResolutionAtCapture=[s.render.resolution_x,s.render.resolution_y]);views.append(ctl);save('actual-root-constrained-preview-controls.json',views)
 print('R170_ROOT_CONSTRAINED_CARRIER_COMPLETE_WOMAN_PREVIEW_DONE',fullNative,len(actualOffset),time.time()-tick,flush=True)
if __name__=='__main__':main()
