"""Minimum independent actual finite-fibre source/ID/edit/reset and body witnesses."""
from pathlib import Path
import bpy,numpy as np,json,datetime,time,importlib.util
from mathutils import Vector
from mathutils.bvhtree import BVHTree
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');E=C/'evidence/character-female-next/r0175-rooted-volume-streamlines';sp=importlib.util.spec_from_file_location('r175verify',C/'scripts/character-next/build-female-next-r0175-rooted-volume-streamlines.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;h=m.h;cw=m.m.curveworld;timing=json.loads((E/'before.json').read_text());b=json.loads((E/'a-build-summary.json').read_text());tick=time.time();reference=None
def save(n,x):(E/n).write_bytes((json.dumps(x,indent=2)+'\n').encode())
for tag,path,digest in [('input',timing['source'],timing['sourceSha256']),('candidate',b['engineAlias'],b['sha256'])]:
 assert a.a.sha(Path(path))==digest;bpy.ops.wm.open_mainfile(filepath=path);s=bpy.context.scene;s.frame_set(1);bpy.data.objects[a.FIXED[1]].material_slots[0].link='DATA';bpy.context.view_layer.update();names=a.FIXED+a.MOVING;raw={n:a.rawsig(bpy.data.objects[n]) for n in names};poses=[]
 for frame in range(1,50):
  s.frame_set(frame);bpy.context.view_layer.update();poses.append({'frame':frame,'worldHashes':{n:[a.a.hasharray(x) for x in a.geometry(bpy.data.objects[n])] for n in names}})
 if tag=='input':reference=raw;poseReference=poses;continue
 assert raw==reference and poses==poseReference;s.frame_set(1);bpy.context.view_layer.update();skin=bpy.data.objects[b['actualSkin']];hair=bpy.data.objects[b['actualHair']];z=np.load(E/'rooted-volume-fibre-root-lineage.npz');P,offset=cw(hair);N=len(offset);assert N==10191 and len(P)==N*33
 def ids():
  ev=hair.evaluated_get(bpy.context.evaluated_depsgraph_get());return h.arr(ev.data.attributes['AFN175_BIRTH_ID'].data,'value',N,dtype='i4')
 birth=ids();assert np.array_equal(birth,np.arange(N));W,T=a.geometry(skin);wanted=(W[z['rootTriangles']]*z['rootBarycentric'][:,:,None]).sum(1);rootError=float(np.linalg.norm(P[offset]-wanted,axis=1).max());hair.update_tag();bpy.context.view_layer.update();reeval=float(np.linalg.norm(cw(hair)[0]-P,axis=1).max());pi=3367*33+8;co=hair.data.position_data[pi].vector.copy();hair.data.position_data[pi].vector=co+Vector((.001,0,0));hair.data.update_tag();hair.update_tag();bpy.context.view_layer.update();changed,_=cw(hair);delta=np.linalg.norm(changed-P,axis=1);move=float(delta.max());affected=int((delta>3e-6).sum());rootEditMove=float(delta[offset].max());stableIDs=bool(np.array_equal(birth,ids()));hair.data.position_data[pi].vector=co;hair.data.update_tag();hair.update_tag();bpy.context.view_layer.update();restore=float(np.linalg.norm(cw(hair)[0]-P,axis=1).max());linked=skin.data;skin.data=linked.copy();vi=int(z['rootTriangles'][0,0]);coSkin=skin.data.vertices[vi].co.copy();skin.data.vertices[vi].co=coSkin+Vector((0,0,.001));skin.data.update();skin.update_tag(refresh={'DATA'});bpy.context.view_layer.update();changed,_=cw(hair);W1,_=a.geometry(skin);wanted1=(W1[z['rootTriangles']]*z['rootBarycentric'][:,:,None]).sum(1);skinMove=float(np.linalg.norm(changed-P,axis=1).max());skinRootError=float(np.linalg.norm(changed[offset]-wanted1,axis=1).max());skin.data=linked;skin.update_tag(refresh={'DATA'});bpy.context.view_layer.update();skinRestore=float(np.linalg.norm(cw(hair)[0]-P,axis=1).max());assert np.array_equal(birth,ids())
 tree=BVHTree.FromPolygons(W.tolist(),T.tolist(),all_triangles=True);witness=[];inspected=0
 for ci in np.linspace(0,N-1,128,dtype=int):
  inspected+=1;end=offset[ci+1] if ci+1<N else len(P);path=P[offset[ci]:end]
  for j,(p,q) in enumerate(zip(path[:-1],path[1:])):
   d=q-p;length=float(np.linalg.norm(d))
   if length<1e-12:continue
   hit,no,fi,dist=tree.ray_cast(Vector(p),Vector(d/length),length)
   if hit is not None and dist>1e-5 and dist<length-1e-5:witness.append({'birthID':int(ci),'controlSegment':j,'bodyTriangle':int(fi),'worldPoint':list(hit),'interiorDistanceM':float(dist),'segmentLengthM':length})
   if len(witness)>=8:break
  if len(witness)>=8:break
 save('actual-rooted-fibre-body-domain-witnesses.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sourceSHA256':b['sha256'],'nativeCurves':N,'nativePoints':len(P),'allPhysicalRootPositionMaximumErrorM':rootError,'sampledNativeCurvesForBodyChords':inspected,'strongControlChordBodyWitnesses':witness,'notExactRenderedFiniteSplineOrGlobalContactCount':True,'globalSignedMinimumM':None,'finiteSelfContinuousNaturalHairRuntimeUnaccepted':True})
 deps=[]
 for lib in bpy.data.libraries:
  p=Path(bpy.path.abspath(lib.filepath)).resolve();assert p.is_file();deps.append({'kind':'library','file':str(p),'sha256':a.a.sha(p)})
 for im in bpy.data.images:
  if im.source=='FILE' and not im.packed_file and im.filepath:
   p=Path(bpy.path.abspath(im.filepath,library=im.library)).resolve();assert p.is_file();deps.append({'kind':'texture','file':str(p),'sha256':a.a.sha(p)})
 unique={d['sha256'] for d in deps};required=json.loads((E.parent/'r0158-shared-native-skin/workspace-storage-provenance.json').read_text())['dependencyFiles'];assert all(d['sha256'] in unique for d in required);gates={'fixedRootPositions':rootError<3e-6,'unchangedReevaluation':reeval<3e-6,'actualInteriorPointEdit':affected>0 and move>1e-5,'editRootsFixed':rootEditMove<3e-6,'pointRestore':restore<3e-6,'skinRootsAttached':skinRootError<3e-6,'skinRestore':skinRestore<3e-6,'actualBirthIDsPreserved':stableIDs}
 save('independent-rooted-volume-fibre-readback.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':b['output'],'engineAliasReopened':b['engineAlias'],'sha256':b['sha256'],'allSevenOriginalRawMeshesUVAnd49EvaluatedGazePosesEqual':True,'49OriginalPoseHashes':poses,'actualNativeCurves':N,'actualPoints':len(P),'allPhysicalRootPositionMaximumErrorM':rootError,'unchangedReevaluationMaximumM':reeval,'actualNativeEditedBirthID':3367,'actualNativePointIndexWithinCurve':8,'nativePoint1mmEditMaximumDisplayedMovementM':move,'nativePointEditAffectedDisplayedPoints':affected,'nativePointEditRootMaximumMovementM':rootEditMove,'nativePointEditRestoreM':restore,'nativeSkin1mmLocalEditMaximumDisplayedMovementM':skinMove,'nativeSkinEditedRootMaximumErrorM':skinRootError,'nativeSkinEditRestoreM':skinRestore,'numericalSourceEditingGates':{k:bool(v) for k,v in gates.items()},'allNumericalSourceEditingGatesPassed':bool(all(gates.values())),'onlyScopedDataEditingNotCompleteNaturalGroomAction':True,'originalReferenceLineFieldNotClaimedToBeOriginalFolliclesOrExactRenderedOccupancy':True,'dependencies':deps,'uniqueDependencyFileHashCount':len(unique),'seconds':time.time()-tick});assert a.a.sha(Path(b['output']))==b['sha256']
print('R175_INDEPENDENT_ACTUAL_ROOTED_FIBRE_IDS_EDIT_RESTORE_BODY_DOMAINS_DONE',time.time()-tick,flush=True)
