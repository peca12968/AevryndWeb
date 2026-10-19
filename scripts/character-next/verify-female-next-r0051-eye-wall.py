"""Independently reopen and verify actual complete posterior-wall repair scope."""
from pathlib import Path
import bpy, importlib.util, numpy as np, json, time, sys
from mathutils import Vector
sp=importlib.util.spec_from_file_location('build51',Path(__file__).with_name('build-female-next-r0051-eye-wall.py'))
k=importlib.util.module_from_spec(sp);sp.loader.exec_module(k)
a=k.a;b=k.b;f=k.f;E=k.E
PREFIX='b' if '--variant-b' in sys.argv else 'a'
if PREFIX=='b':k.OUT=b.S/'aevrynd-female-next-r0051-b-rebased-eye-wall.blend'

def save(name,value):k.save(PREFIX+'-'+name,value)

def self_pair_set(P,T,moved,tree):
    _,pairs=a.selfcheck.changed_self(P,T,moved,tree)
    return {(int(x),int(y)) for x,y in pairs if a.exact.intersections(P[T[x]],P[T[y]])}

def main():
    tick=time.time();build=json.loads((E/(PREFIX+'-build-summary.json')).read_text())
    assert b.sha(k.OUT)==build['outputSha256'] and b.sha(k.SRC)==build['sourceSha256']
    bpy.ops.wm.open_mainfile(filepath=str(k.SRC));before=f.state();VB,TB=b.evaluated(bpy.data.objects[b.BODY],True)
    oldNative=b.mesh_signature(bpy.data.objects[b.BODY].data)
    oldLoops=np.array([p.vertices[:] for p in bpy.data.objects[b.BODY].data.polygons],dtype=object).tolist()
    bpy.ops.wm.open_mainfile(filepath=str(k.OUT));after=f.state();body=bpy.data.objects[b.BODY]
    assert all(after[key]==before[key] for key in ('materials','skinFields','curves','stage'))
    assert all(after['meshes'][n]==row for n,row in before['meshes'].items() if n!=b.BODY)
    assert b.mesh_signature(body.data)['uv']==oldNative['uv']
    assert [p.vertices[:] for p in body.data.polygons]==oldLoops
    V,T=b.evaluated(body,True);assert V.shape==VB.shape and T.shape==TB.shape
    moved=np.linalg.norm(V-VB,axis=1)>1e-9;changed=np.any(moved[T],axis=1)|np.any(T!=TB,axis=1)
    full=a.selfcheck.tree(V,T);patch=a.selfcheck.tree(V,T[changed]);results={
        'source':str(k.OUT),'sourceSha256':b.sha(k.OUT),
        'base':str(k.SRC),'baseSha256':b.sha(k.SRC),
        'nativeConnectivityAndUVExact':True,'materialsSkinFieldsCurvesStageOtherMeshesExact':True,
        'fullBodyVertices':len(V),'fullBodyTriangles':len(T),
        'changedBodyVertices':int(moved.sum()),'changedTriangles':int(changed.sum()),
        'changedBoundsM':[V[moved].min(0).tolist(),V[moved].max(0).tolist()],
        'status':'RUNNING'}
    save('verification-progress.json',results)
    eyeSelf=k.k.check(V,T);results['fullOcularRegionsSelf']=eyeSelf
    globalChangedSelf=a.changed_self(V,T,moved,full);results['changedRegionAgainstCompleteBodySelf']=globalChangedSelf
    print('R51_FULL_SELF',eyeSelf['actualSelfPairs'],globalChangedSelf['actualNonAdjacentPairs'],flush=True)
    optics={}
    for side in ('L','R'):
        for part in ('Sclera','Cornea','Iris','Pupil'):
            name=f'AFN30_{side}_{part}';P,U=b.evaluated(bpy.data.objects[name],True);tree=a.selfcheck.tree(P,U)
            row=a.actual_pairs(V,T,P,U,full.overlap(tree));anchor=a.selfcheck.parity(full,P.mean(0))
            if anchor['classification']=='unresolved':
                wind=f.flowcheck.module('winding51','verify-female-next-r0030-eye-optics.py')
                fallback=wind.winding_classification(V,T,P.mean(0))
                anchor={'classification':fallback['classification'],'fiveRayResult':anchor,'fullFloat64SolidAngle':fallback}
            row['anchorAgainstBody']=anchor;optics[name]=row
    results['fixedOptics']=optics
    # Native Reshape also introduces measured float rounding elsewhere. Compare
    # actual source/candidate contacts by stable quad IDs; do not call inherited
    # unrelated failures a whole-body pass or discard them from the report.
    unchangedOtherSelf=False
    if PREFIX=='b' and globalChangedSelf['actualNonAdjacentPairs']:
        beforeTree=a.selfcheck.tree(VB,TB)
        oldPairs=self_pair_set(VB,TB,moved,beforeTree);newPairs=self_pair_set(V,T,moved,full)
        oldQuads={tuple(sorted((x//2,y//2))) for x,y in oldPairs}
        newQuads={tuple(sorted((x//2,y//2))) for x,y in newPairs}
        newFeaturePairs=newQuads-oldQuads
        unchangedOtherSelf=not newFeaturePairs
        results['inheritedOtherBodySelfContacts']={
            'sourceTrianglePairs':len(oldPairs),'candidateTrianglePairs':len(newPairs),
            'sourceQuadPairs':len(oldQuads),'candidateQuadPairs':len(newQuads),
            'newIntersectingQuadPairs':len(newFeaturePairs),'newQuadPairExamples':sorted(newFeaturePairs)[:30],
            'removedIntersectingQuadPairs':len(oldQuads-newQuads),
            'scope':'Full ordered evaluated quad topology is stable; triangle diagonals may differ. Existing nonocular source failures remain failures, not a new full-body contact pass. Only absence of newly intersecting quad features can be stated.'}
    good=eyeSelf['actualSelfPairs']==0 and (globalChangedSelf['actualNonAdjacentPairs']==0 or unchangedOtherSelf) and all(
        row['actualSurfaceIntersectionPairs']==0 and row['anchorAgainstBody']['classification']=='outside' for row in optics.values())
    save('verification-progress.json',results)
    if not good:
        results.update(status='FAIL_FULL_BODY_SELF_OR_OPTICS_STOP',seconds=time.time()-tick)
        save('saved-static-verification.json',results);print('R51_VERIFY_STOP',results['status'],flush=True);return
    records=json.loads((b.R/'Evidence/character-female-next/r0037-eye-margin/c-review-tissue-bindings.json').read_text())
    tissue={}
    for rec in records['patches']:
        name=rec['object'];P,U=b.evaluated(bpy.data.objects[name],True)
        ids=np.array(sorted(set(rec['facesSourceBodyTriangle'])),dtype='i4');ids=ids[ids>=0]
        assert np.array_equal(T[ids],TB[ids]),'Support triangle lineage changed'
        expected=np.array([np.array(row['weights'])@V[row['indices']] for row in rec['nodes']])
        err=float(np.linalg.norm(P[:rec['baseNodeCount']]-expected,axis=1).max())
        contact=a.exact.body_attachment(bpy.data.objects[name],P,U,full,V,T,rec)
        tissue[name]={'baseBarycentricErrorM':err,'sourceTriangleLineageExact':True,'actualBodyAttachment':contact}
        good=good and err<1e-6 and contact['unqualifiedNonAttachmentPairs']==0
        print('R51_TISSUE',name,err,contact['unqualifiedNonAttachmentPairs'],flush=True)
    results['wetTissueBodyJoins']=tissue;save('verification-progress.json',results)
    # Fixed actual closed lash meshes against the entire changed body surface.
    # Unchanged pairs inherit only their previous explicitly stated scope.
    lashes={}
    for name in before['meshes']:
        if not name.endswith('_Lashes'):continue
        P,U=b.evaluated(bpy.data.objects[name],True);tree=a.selfcheck.tree(P,U)
        row=a.actual_pairs(V,T[changed],P,U,patch.overlap(tree));lashes[name]=row
        good=good and row['actualSurfaceIntersectionPairs']==0
    results['unchangedLashesAgainstCompleteChangedBodySurface']=lashes
    # Physical finite scalp/brow capsules, not only roots or guide points.
    both=np.concatenate((VB[TB[changed]].reshape(-1,3),V[T[changed]].reshape(-1,3)));lo=both.min(0);hi=both.max(0)
    curves={};triangles=None
    for name in before['curves']:
        o=bpy.data.objects[name];P,rr=a.v.hair_arrays(o);mx=np.array(o.matrix_world)
        P=P.astype('f8')@mx[:3,:3].T+mx[:3,3];rr=rr.astype('f8')*np.linalg.norm(mx[:3,:3],ord=2)
        if PREFIX=='b':
            if triangles is None:triangles=V[T]
            print('R51_FULL_CURVE_BODY_START',name,len(P),flush=True)
            row=f.flowcheck.check(P,rr,full,triangles)
            curves[name]=row;good=good and row['unqualifiedSegments']==0 and not row['rootFailures']
            results['originalScalpAndBrowChangedBodyUpdate']=curves;save('verification-progress.json',results)
            continue
        rad=np.maximum(rr[:,:-1],rr[:,1:])+1e-6
        seglo=np.minimum(P[:,:-1],P[:,1:])-rad[...,None];seghi=np.maximum(P[:,:-1],P[:,1:])+rad[...,None]
        separation=np.maximum(lo-seghi,seglo-hi).max(2);ids=np.argwhere(separation<=0);bad=[]
        if len(ids) and triangles is None:triangles=V[T]
        for ci,j in ids:
            A,B=P[ci,j],P[ci,j+1];d0=full.find_nearest(Vector(A))[3];d1=full.find_nearest(Vector(B))[3]
            gap,method=f.flowcheck.cap.segment_test(A,B,d0,d1,float(max(rr[ci,j],rr[ci,j+1])),full,triangles)
            if gap<=0:bad.append({'curve':int(ci),'segment':int(j),'gapLowerBoundM':float(gap),'method':method})
        row={'curves':len(P),'completeFiniteSegments':int(separation.size),'aabbExcluded':int((separation>0).sum()),
             'directSegments':len(ids),'unqualifiedSegments':len(bad),'failures':bad[:20],
             'minimumPositiveAabbAxisSeparationBoundM':float(separation[separation>0].min()) if np.any(separation>0) else None,
             'scope':'Changed-body-region update only; same original point/radius/world geometry. Axis bound is not an exact global signed minimum. No new hair-self or dynamic qualification.'}
        curves[name]=row;good=good and not bad
    results['originalScalpAndBrowChangedBodyUpdate']=curves
    domain=bpy.data.objects['AFN48_ANATOMICAL_SCALP_DOMAIN']
    ids=np.array([r.value for r in domain.data.attributes['AFN48_BodyTriangle'].data],dtype='i4')
    assert np.array_equal(T[ids],TB[ids])
    results['r48ScalpDomainTriangleMaximumDeviationM']=float(np.linalg.norm(V[T[ids]]-VB[TB[ids]],axis=2).max())
    results['r48ScalpDomainScope']='Prior source domain retained as research; triangle index lineage exact, actual rounding deviation reported. No new scalp-authoring acceptance.'
    area=np.linalg.norm(np.cross(V[T[changed,1]]-V[T[changed,0]],V[T[changed,2]]-V[T[changed,0]]),axis=1)*.5
    results['affectedTriangleMinimumAreaM2']=float(area.min());good=good and np.isfinite(V).all() and np.all(area>1e-14)
    results.update(status='PASS_OCULAR_REPAIR_SCOPE_OTHER_SOURCE_SELF_FAILURES_REMAIN' if good and unchangedOtherSelf else ('PASS_STATED_STATIC_POSTERIOR_REPAIR_SCOPE' if good else 'FAIL_ATTACHMENT_OR_CURVE_UPDATE'),
                   seconds=time.time()-tick,
                   limits=['Neutral actual meshes only; no blink/gaze/expression or skeletal rig acceptance',
                           'Original topology inherited; full-body self contacts outside ocular/changed regions were not newly tested',
                           'Source tissue joins distinguished by exact triangle/barycentric lineage at original1um allowance',
                           'No global signed minimum-distance claim; surface pairs and containment anchors have stated coverage',
                           'No clothes, oral animation, hair-self/natural dynamics or continuous motion qualification',
                           'No runtime/LOD/CPU/GPU/memory or complete appearance-score promotion'])
    save('saved-static-verification.json',results)
    print('R51_STATIC_VERIFICATION',results['status'],time.time()-tick,flush=True)

if __name__=='__main__':main()
