"""Reopen integrated B; reuse exact same-body proof and test rebuilt interfaces."""
from pathlib import Path
import bpy,importlib.util,numpy as np,json,time
sp=importlib.util.spec_from_file_location('int51',Path(__file__).with_name('integrate-female-next-r0051-eye-wall.py'))
k=importlib.util.module_from_spec(sp);sp.loader.exec_module(k)
a=k.a;b=k.b;f=k.f;E=k.E

def containment(V,T,tree,point):
    row=a.selfcheck.parity(tree,point)
    if row['classification']=='unresolved':
        wind=f.flowcheck.module('integratedWinding51','verify-female-next-r0030-eye-optics.py')
        exact=wind.winding_classification(V,T,point)
        return {'classification':exact['classification'],'fiveRayResult':row,'float64SolidAngleFallback':exact}
    return row

def main():
    tick=time.time();build=json.loads((E/'b-integrated-build-summary.json').read_text())
    assert b.sha(k.k.OUT)==build['sourceSha256'] and b.sha(k.OUT)==build['outputSha256']
    bodyProof=json.loads((E/'b-saved-static-verification.json').read_text())
    assert bodyProof['sourceSha256']==build['sourceSha256']
    assert bodyProof['fullOcularRegionsSelf']['actualSelfPairs']==0
    assert bodyProof['inheritedOtherBodySelfContacts']['newIntersectingQuadPairs']==0
    assert all(r['actualSurfaceIntersectionPairs']==0 and r['anchorAgainstBody']['classification']=='outside' for r in bodyProof['fixedOptics'].values())
    assert all(r['unqualifiedSegments']==0 and not r['rootFailures'] for r in bodyProof['originalScalpAndBrowChangedBodyUpdate'].values())
    bpy.ops.wm.open_mainfile(filepath=str(k.k.OUT));before=f.state()
    bpy.ops.wm.open_mainfile(filepath=str(k.OUT));after=f.state()
    names=[r['object'] for r in build['reboundTissues']]
    assert all(after[key]==before[key] for key in ('materials','skinFields','curves','stage'))
    assert all(after['meshes'][n]==row for n,row in before['meshes'].items() if n not in names)
    V,T=b.evaluated(bpy.data.objects[b.BODY],True);full=a.selfcheck.tree(V,T)
    records=json.loads((b.R/'Evidence/character-female-next/r0037-eye-margin/c-review-tissue-bindings.json').read_text())
    results={'source':str(k.OUT),'sourceSha256':b.sha(k.OUT),'status':'RUNNING',
        'bodyGeometryExactFromProvedB':True,'bodyProofSource':str(E/'b-saved-static-verification.json'),
        'bodyProofSha256':b.sha(E/'b-saved-static-verification.json'),
        'ocularSelfPairs':0,'fixedOpticalSurfacePairs':0,'newOtherBodyIntersectingQuadPairs':0,
        'existingOtherBodySurfaceSelfPairs':bodyProof['changedRegionAgainstCompleteBodySelf']['actualNonAdjacentPairs'],
        'sourceOtherBodyFailuresRemainUnaccepted':True,
        'originalHairBodyCapsules':bodyProof['originalScalpAndBrowChangedBodyUpdate'],
        'materialsSkinFieldsHairStageExact':True}
    optics={n:b.evaluated(bpy.data.objects[n],True) for n in before['meshes'] if n.startswith('AFN30_')}
    tissue={};meshData={};good=True
    for rec in records['patches']:
        name=rec['object'];P,U=b.evaluated(bpy.data.objects[name],True);tree=a.selfcheck.tree(P,U)
        expected=np.array([np.array(row['weights'])@V[row['indices']] for row in rec['nodes']])
        err=float(np.linalg.norm(P[:rec['baseNodeCount']]-expected,axis=1).max())
        join=a.exact.body_attachment(bpy.data.objects[name],P,U,full,V,T,rec)
        own=a.meshself(P,U,tree);cross={}
        for other,(Q,W) in optics.items():
            otherTree=a.selfcheck.tree(Q,W);cross[other]=a.actual_pairs(P,U,Q,W,tree.overlap(otherTree))
        # A known nonzero-height tissue column supplies an actual interior anchor.
        jj=int(np.argmax(np.linalg.norm(P[rec['topVertices']]-P[:rec['baseNodeCount']],axis=1)))
        anchor=(P[jj]+P[rec['topVertices'][jj]])*.5
        meshData[name]=(P,U,tree,anchor)
        tissue[name]={'baseBarycentricErrorM':err,'originalInterfaceToleranceM':1e-6,
                      'actualBodyAttachment':join,'actualClosedMeshSelf':own,'optics':cross}
        good=good and err<1e-6 and join['unqualifiedNonAttachmentPairs']==0 and own['actualSurfaceIntersectionPairs']==0 and all(r['actualSurfaceIntersectionPairs']==0 for r in cross.values())
        print('R51_INTEGRATED_JOIN',name,err,join['unqualifiedNonAttachmentPairs'],own['actualSurfaceIntersectionPairs'],flush=True)
        results['rebuiltWetTissues']=tissue
        k.k.k.save('b-integrated-verification-progress.json',results)
    lashNames=[n for n in before['meshes'] if n.endswith('_Lashes')]
    between={}
    for i,name in enumerate(names):
        P,U,tree,anchor=meshData[name]
        for other in names[i+1:]+lashNames:
            if other in meshData:Q,W,qt,_=meshData[other]
            else:Q,W=b.evaluated(bpy.data.objects[other],True);qt=a.selfcheck.tree(Q,W)
            row=a.actual_pairs(P,U,Q,W,tree.overlap(qt))
            state=containment(Q,W,qt,anchor);row['tissueAnchorAgainstOther']=state
            # All independent lash solids need their own containment anchors.
            if other in lashNames:
                anchors=np.array([Q[j*258+16*8:j*258+17*8].mean(0) for j in range(len(Q)//258)])
                anchorRows=[containment(P,U,tree,point) for point in anchors]
                states=[r['classification'] for r in anchorRows]
                row['allLashComponentAnchorStates']={s:states.count(s) for s in set(states)}
                row['solidAngleFallbacks']=[{'component':j,'result':r} for j,r in enumerate(anchorRows) if 'float64SolidAngleFallback' in r]
                good=good and all(s=='outside' for s in states)
            between[name+' / '+other]=row
            good=good and row['actualSurfaceIntersectionPairs']==0 and state['classification']=='outside'
    results['actualWetWetAndWetLashPairs']=between
    curves={}
    for name in before['curves']:
        o=bpy.data.objects[name];P,rr=a.v.hair_arrays(o);mx=np.array(o.matrix_world)
        P=P.astype('f8')@mx[:3,:3].T+mx[:3,3];rr=rr.astype('f8')*np.linalg.norm(mx[:3,:3],ord=2)
        rad=np.maximum(rr[:,:-1],rr[:,1:])+1e-6;lo=np.minimum(P[:,:-1],P[:,1:])-rad[...,None];hi=np.maximum(P[:,:-1],P[:,1:])+rad[...,None]
        rows={}
        for other,(Q,W,qt,_) in meshData.items():
            sep=np.maximum(Q.min(0)-hi,lo-Q.max(0)).max(2);ids=np.argwhere(sep<=0);bad=[]
            triangles=Q[W] if len(ids) else None
            for ci,j in ids:
                A,B=P[ci,j],P[ci,j+1];d0=qt.find_nearest(Vector(A))[3];d1=qt.find_nearest(Vector(B))[3]
                gap,method=f.flowcheck.cap.segment_test(A,B,d0,d1,float(max(rr[ci,j],rr[ci,j+1])),qt,triangles)
                if gap<=0:bad.append({'curve':int(ci),'segment':int(j),'gapLowerBoundM':float(gap),'method':method})
            rows[other]={'completeFiniteSegments':int(sep.size),'aabbExcluded':int((sep>0).sum()),'directSegments':len(ids),'unqualifiedSegments':len(bad),'failureSamples':bad[:20]}
            good=good and not bad
        curves[name]=rows
    results['originalHairAgainstAllRebuiltWetMeshes']=curves
    results.update(status='PASS_STATED_OCULAR_REPAIR_AND_REBOUND_INTERFACES_NOT_FULL_CHARACTER' if good else 'FAIL_INTEGRATED_INTERFACES',
        seconds=time.time()-tick,
        limits=['Neutral ocular and rebuilt-interface scope only; existing nonocular self contacts still fail',
                'Surface pairs/anchors/capsule lower bounds are not exact global signed minimum distances',
                'No blink/gaze/rig, natural hair/self/continuous motion, clothing or complete oral function acceptance',
                'No Aevrynd runtime, LOD, CPU/GPU/memory acceptance or appearance-score promotion'])
    k.k.k.save('b-integrated-static-verification.json',results)
    print('R51_INTEGRATED_VERIFICATION',results['status'],time.time()-tick,flush=True)

if __name__=='__main__':main()
