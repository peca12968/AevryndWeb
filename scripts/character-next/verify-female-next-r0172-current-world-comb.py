"""Minimal independent displayed guide editing/restoration and failed body domains."""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,time,datetime
from mathutils import Vector
from mathutils.bvhtree import BVHTree
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');E=C/'evidence/character-female-next/r0172-current-world-comb'
sp=importlib.util.spec_from_file_location('r172verify',C/'scripts/character-next/build-female-next-r0172-current-world-comb.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;h=m.h;cw=m.m.curveworld;tick=time.time();timing=json.loads((E/'before.json').read_text());b=json.loads((E/'a-build-summary.json').read_text())
def save(n,x):(E/n).write_bytes((json.dumps(x,indent=2)+'\n').encode())
reference=None;poseReference=None
for tag,path,digest in [('input',timing['source'],timing['sourceSha256']),('candidate',b['engineAlias'],b['sha256'])]:
    assert a.a.sha(Path(path))==digest;bpy.ops.wm.open_mainfile(filepath=path);s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();names=a.FIXED+a.MOVING;raw={n:a.rawsig(bpy.data.objects[n]) for n in names};poses=[]
    for frame in range(1,50):
        s.frame_set(frame);bpy.context.view_layer.update();poses.append({'frame':frame,'worldHashes':{n:[a.a.hasharray(x) for x in a.geometry(bpy.data.objects[n])] for n in names}})
    if tag=='input':reference=raw;poseReference=poses;continue
    assert raw==reference and poses==poseReference;s.frame_set(1);bpy.context.view_layer.update();skin=bpy.data.objects[b['actualSkin']];hair=bpy.data.objects[b['actualHair']];go=bpy.data.objects[b['actualGuides']];line=np.load(E/'current-world-comb-lineage.npz');rest,offset=cw(hair);N=len(offset);W,T=a.geometry(skin);tree=BVHTree.FromPolygons(W.tolist(),T.tolist(),all_triangles=True)
    def birthIDs():
        ev=hair.evaluated_get(bpy.context.evaluated_depsgraph_get());return h.arr(ev.data.attributes['AFN172_BIRTH_ID'].data,'value',N,dtype='i4')
    ids=birthIDs();assert np.array_equal(ids,np.arange(N));wanted=(W[line['fixedRootTriangles']]*line['fixedRootBarycentric'][:,:,None]).sum(1);rootError=float(np.linalg.norm(rest[offset]-wanted,axis=1).max());guideWorld,goff=cw(go);assert np.max(np.linalg.norm(guideWorld-line['guideWorld'].reshape(-1,3),axis=1))<3e-6
    go.update_tag();hair.update_tag();bpy.context.view_layer.update();again,off2=cw(hair);reeval=float(np.linalg.norm(again-rest,axis=1).max());assert np.array_equal(offset,off2) and np.array_equal(ids,birthIDs())
    a.b.u.v.E=E;controls=[]
    def capture(tag):
        c=a.b.u.v.image(tag,'face');c.update(actualHair=hair.name,frame=1,hairTypeAtActualCapture=s.render.hair_type,actualSamplesAtCapture=s.cycles.samples,actualResolutionAtCapture=[s.render.resolution_x,s.render.resolution_y]);controls.append(c);save('actual-edit-restore-preview-controls.json',controls)
    capture('operation-before')
    pi=61*16+8;original=go.data.position_data[pi].vector.copy();go.data.position_data[pi].vector=original+Vector((.006,0,0));go.data.update_tag();go.update_tag();hair.update_tag();bpy.context.view_layer.update();changed,editOff=cw(hair);delta=np.linalg.norm(changed-rest,axis=1);editMove=float(delta.max());affected=int((delta>3e-6).sum());editRoots=float(delta[offset].max());editIDs=bool(np.array_equal(ids,birthIDs()) and np.array_equal(offset,editOff));capture('operation-guide61-comb6mm')
    go.data.position_data[pi].vector=original;go.data.update_tag();go.update_tag();hair.update_tag();bpy.context.view_layer.update();restored,_=cw(hair);guideRestore=float(np.linalg.norm(restored-rest,axis=1).max());capture('operation-restored')
    linked=skin.data;skin.data=linked.copy();vi=int(line['fixedRootTriangles'][0,0]);originalSkin=skin.data.vertices[vi].co.copy();skin.data.vertices[vi].co=originalSkin+Vector((0,0,.001));skin.data.update();skin.update_tag(refresh={'DATA'});bpy.context.view_layer.update();skinChanged,_=cw(hair);W1,_=a.geometry(skin);wanted1=(W1[line['fixedRootTriangles']]*line['fixedRootBarycentric'][:,:,None]).sum(1);skinRootError=float(np.linalg.norm(skinChanged[offset]-wanted1,axis=1).max());skinMove=float(np.linalg.norm(skinChanged-rest,axis=1).max());skin.data=linked;skin.update_tag(refresh={'DATA'});bpy.context.view_layer.update();skinRestore=float(np.linalg.norm(cw(hair)[0]-rest,axis=1).max());skinIDs=bool(np.array_equal(ids,birthIDs()))
    witnesses=[];inspected=0
    for ci in np.linspace(0,N-1,128,dtype=int):
        inspected+=1;end=offset[ci+1] if ci+1<N else len(rest);path=rest[offset[ci]:end]
        for j,(p,q) in enumerate(zip(path[:-1],path[1:])):
            d=q-p;length=float(np.linalg.norm(d))
            if length<1e-12:continue
            hit,no,fi,dist=tree.ray_cast(Vector(p),Vector(d/length),length)
            if hit is not None and dist>1e-5 and dist<length-1e-5:witnesses.append({'birthID':int(ci),'controlSegment':j,'bodyTriangle':int(fi),'worldPoint':list(hit),'interiorDistanceM':float(dist),'segmentLengthM':length})
            if len(witnesses)>=8:break
        if len(witnesses)>=8:break
    save('actual-birth-correspondence-and-body-failures.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sourceSHA256':b['sha256'],'nativeCurves':N,'nativePoints':len(rest),'actualBirthIDsPreservedAtReevaluationGuideEditAndSkinProbe':bool(editIDs and skinIDs),'fixedRawCurveTopologyNoRandomGeneratorOrOutputIndexOverwrite':True,'unchangedReevaluationMaximumM':reeval,'allRootPositionMaximumErrorM':rootError,'sampledNativeCurvesForBodyChords':inspected,'strongControlChordBodyWitnesses':witnesses,'notExactRenderedFiniteSplineOrGlobalContactCount':True,'globalSignedMinimumM':None,'finiteSelfContinuousNaturalHairRuntimeUnaccepted':True})
    deps=[]
    for lib in bpy.data.libraries:
        p=Path(bpy.path.abspath(lib.filepath)).resolve();assert p.is_file();deps.append({'kind':'library','file':str(p),'sha256':a.a.sha(p)})
    for im in bpy.data.images:
        if im.source=='FILE' and not im.packed_file and im.filepath:
            p=Path(bpy.path.abspath(im.filepath,library=im.library)).resolve();assert p.is_file();deps.append({'kind':'texture','file':str(p),'sha256':a.a.sha(p)})
    unique={x['sha256'] for x in deps};required=json.loads((E.parent/'r0158-shared-native-skin/workspace-storage-provenance.json').read_text())['dependencyFiles'];assert all(x['sha256'] in unique for x in required)
    gates={'reevaluation':reeval<3e-6,'guideEditAffectsActualDisplayedHair':affected>0 and editMove>1e-5,'guideEditRootFixed':editRoots<3e-6,'guideRestore':guideRestore<3e-6,'skinRootAttachment':skinRootError<3e-6,'skinRestore':skinRestore<3e-6,'persistentActualBirthIDs':editIDs and skinIDs}
    save('independent-current-world-comb-readback.json',{'source':b['output'],'engineAliasReopened':b['engineAlias'],'sha256':b['sha256'],'protectedSevenRawMeshesUVAnd49OriginalEvaluatedGazePosesEqual':True,'49OriginalPoseHashes':poses,'current252GuideRestWorldMatchesSavedConstruction':True,'nativeCurves':N,'nativePoints':len(rest),'allRootPositionMaximumErrorM':rootError,'unchangedReevaluationMaximumM':reeval,'actualGuideEdited':61,'actualGuidePointEdited':8,'actualNativeGuideEditDeltaM':[.006,0,0],'nativeGuideEditMaximumDisplayedMovementM':editMove,'nativeGuideEditAffectedDisplayedPoints':affected,'nativeGuideEditRootMovementM':editRoots,'nativeGuideEditRestoreM':guideRestore,'nativeSkin1mmEditMaximumDisplayedMovementM':skinMove,'nativeSkinEditedAllRootErrorM':skinRootError,'nativeSkinRestoreM':skinRestore,'numericalEditingGates':{k:bool(v) for k,v in gates.items()},'allNumericalEditingGatesPassed':bool(all(gates.values())),'actualGuideOperationIntermediateAndRestoreCaptures':str(E/'actual-edit-restore-preview-controls.json'),'completeGroomOperationNotAdoptedDueRejectedLookAndRelatedContactUnaccepted':True,'dependencies':deps,'uniqueDependencyFileHashCount':len(unique),'seconds':time.time()-tick})
    assert a.a.sha(Path(b['output']))==b['sha256']
print('R172_INDEPENDENT_ACTUAL_FIXED_BIRTH_GUIDE_EDIT_RESTORE_AND_BODY_DOMAINS_DONE',time.time()-tick,flush=True)
