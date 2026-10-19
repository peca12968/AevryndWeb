"""Independent reopening, root/UV binding, and full finite master contacts.

Static 64-master scope only. No children, thick diagnostic radii, continuous
motion, clothing, or engine claim follows from this report.
"""
from pathlib import Path
import bpy,importlib.util,numpy as np,json,time,sys
from mathutils.bvhtree import BVHTree
sp=importlib.util.spec_from_file_location('read53',Path(__file__).with_name('build-female-next-r0053-scalp-foundation.py'))
k=importlib.util.module_from_spec(sp);sp.loader.exec_module(k)
b=k.b;f=k.f;E=k.E
PREFIX=(('grown-fixed-pilot' if '--pilot' in sys.argv else 'grown-fixed') if '--corrected-route' in sys.argv else ('grown-pilot' if '--pilot' in sys.argv else 'grown')) if '--short-grow' in sys.argv else 'primary'

def main():
    tick=time.time();build=json.loads((E/(PREFIX+'-build-summary.json')).read_text())
    source=Path(build['output']);assert b.sha(source)==build['outputSha256']
    bpy.ops.wm.open_mainfile(filepath=str(k.SRC));before=f.state()
    bpy.ops.wm.open_mainfile(filepath=str(source));after=f.state()
    assert all(before[key]==after[key] for key in ('meshes','materials','skinFields','stage'))
    assert all(after['curves'][name]==row for name,row in before['curves'].items())
    o=bpy.data.objects[k.NAME];P,R=f.v.hair_arrays(o)
    assert np.isfinite(P).all() and np.isfinite(R).all()
    EP,ER=f.v.hair_arrays(o.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    data=np.load(E/'refined-foundation-data.npz')
    assert np.array_equal(P[:,0],data['initialPaths'][:,0].astype('f4'))
    assert np.array_equal(R,data['radii'].astype('f4'))
    assert np.array_equal(P,EP) and np.array_equal(R,ER)
    assert all(value.value==1 for value in o.data.attributes['curve_type'].data)
    inherited=build.get('inheritedVerifiedCurveIndices',[])
    inheritedExact=None
    if inherited:
        retained=np.load(E/'grown-fixed-pilot-native-data.npz')
        inheritedExact=bool(np.array_equal(P[inherited],retained['after'][inherited]))
        assert inheritedExact
    assert o.data.surface.name==b.BODY and o.data.attributes['surface_uv_coordinate'].data_type=='FLOAT2'
    V,T=b.evaluated(bpy.data.objects[b.BODY],True)
    foundation=json.loads((E/'refined-foundation-build.json').read_text())
    foot=[];expected=[]
    for binding in foundation['rootBindings']:
        ti=binding['bodyTriangle'];assert T[ti].tolist()==binding['bodyVertices']
        p=np.array(binding['barycentric'])@V[T[ti]];foot.append(p)
        expected.append(p+np.array(binding['normal'])*binding['rootOffsetM'])
    rootError=np.linalg.norm(P[:,0]-expected,axis=1)
    assert rootError.max()<1e-7
    # Verify native UV coordinates against the actual evaluated triangle loops.
    deps=bpy.context.evaluated_depsgraph_get();ev=bpy.data.objects[b.BODY].evaluated_get(deps)
    mesh=ev.to_mesh(preserve_all_data_layers=True,depsgraph=deps);mesh.calc_loop_triangles()
    uv=mesh.uv_layers[0];uvExpected=[]
    for binding in foundation['rootBindings']:
        loops=mesh.loop_triangles[binding['bodyTriangle']].loops
        coords=np.array([list(uv.data[i].uv) for i in loops])
        uvExpected.append(np.array(binding['barycentric'])@coords)
    ev.to_mesh_clear()
    storedUV=np.array([list(v.vector) for v in o.data.attributes['surface_uv_coordinate'].data])
    uvError=float(np.max(np.abs(storedUV-uvExpected)))
    # UV is FLOAT2, including UDIM coordinates above 1. Compare its expected
    # float32 representation exactly; an absolute1e-7 rejects valid rounding.
    uvPassed=bool(np.array_equal(storedUV.astype('f4'),np.array(uvExpected,dtype='f4')))
    print('R53_SURFACE_UV',uvError,storedUV[:3].tolist(),np.array(uvExpected)[:3].tolist(),flush=True)
    idsAuthored=np.array(build.get('authoredCurveIndices',list(range(len(P)))),dtype='i4')
    testedP=P[idsAuthored].astype('f8');testedR=R[idsAuthored].astype('f8')
    tree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True)
    if '--readback-only' in sys.argv:
        from mathutils import Vector
        tri=V[T];rootStates=[];rootGaps=[]
        for ci,root in enumerate(P[:,0].astype('f8')):
            rootStates.append(f.flowcheck.cap.solid.classify(tree,tri,Vector(root)))
            rootGaps.append(tree.find_nearest(Vector(root))[3]-float(R[ci,0]))
        segmentLengths=np.linalg.norm(np.diff(testedP,axis=1),axis=2)
        result={'source':str(source),'sourceSha256':b.sha(source),'status':'REOPENED_AUTHORING_DATA_ONLY_FULL_STYLE_VISUALLY_REJECTED',
            'reopened':True,'bodyOtherMeshesSkinMaterialsStageAndOriginalCurvesExact':True,
            'nativeVsEvaluatedPositionsAndRadiiExact':True,'rootPositionsAndRadiiExact':True,
            'curveCount':len(P),'pointsPerCurve':P.shape[1],'curveType':'POLY',
            'actualBarycentricRootMaximumErrorM':float(rootError.max()),'nativeSurfaceUVType':'FLOAT2',
            'surfaceUVExactlyExpectedFloat32':uvPassed,'maximumDoubleToStoredUVRoundingError':uvError,
            'inheritedSixExact':inheritedExact,'inheritedVerifiedCurveIndices':inherited,
            'rootClassificationCounts':{value:rootStates.count(value) for value in set(rootStates)},
            'minimumSampledRootCapsuleSurfaceGapM':float(min(rootGaps)),
            'segmentLengthRangeM':[float(segmentLengths.min()),float(segmentLengths.max())],
            'segmentsBelowOneMicron':int((segmentLengths<1e-6).sum()),
            'full64FinitePathsSelfOtherOpticsAndDynamics':'NOT_RUN_AFTER_COMPLETE_FORM_VISUAL_REJECTION',
            'retention':'Anatomical scalp/root authoring and corrected native sampling workflow only; rejected full hair shape is not an accepted groom.',
            'seconds':time.time()-tick}
        assert uvPassed and all(state=='outside' for state in rootStates) and min(rootGaps)>1e-6
        k.save(PREFIX+'-saved-readback.json',result)
        print('R53_AUTHORING_ONLY_READBACK',result['curveCount'],result['segmentLengthRangeM'],flush=True)
        return
    body=f.flowcheck.check(testedP,testedR,tree,V[T])
    print('R53_FULL_MASTER_BODY',body['status'],body['unqualifiedSegments'],flush=True)
    ss=importlib.util.spec_from_file_location('self53',Path(__file__).with_name('solve-female-next-r0036-brow-contacts.py'))
    solver=importlib.util.module_from_spec(ss);ss.loader.exec_module(solver);solver.controls()
    ids,gap,_,_=solver.contacts(testedP,testedR,1e-6)
    selfContact={'scope':'All nonadjacent finite master capsules, max endpoint radius; adjacent segments of one curve excluded by construction.',
        'candidatePairs':len(ids),'overlapsBeyondNumericalAllowance':int((gap < -1e-6).sum()),
        'withinOneMicronOrOverlapping':int((gap<=1e-6).sum()),
        'minimumCandidateCapsuleGapM':float(gap.min()) if len(gap) else None,
        'failurePairs':ids[gap < -1e-6][:80].tolist(),'numericalAllowanceM':1e-6}
    external={'status':'NOT_TESTED_PENDING_BODY_AND_VISUAL_DECISION'}
    if '--other-meshes' in sys.argv and body['status']=='PASS_TESTED_STATIC_CAPSULES' and selfContact['overlapsBeyondNumericalAllowance']==0:
        rows={}
        names=sorted(o.name for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render and o.name.startswith(('AFN30_','AFN37_')))
        assert len(names)==18,('Unexpected optical/wet/lash mesh set',names)
        for name in names:
            X,F=b.evaluated(bpy.data.objects[name],True)
            tb=BVHTree.FromPolygons(X.tolist(),F.tolist(),all_triangles=True)
            contact=f.flowcheck.check(testedP,testedR,tb,X[F],roots=False)
            rootOutside=np.any((testedP[:,0]<X.min(0))|(testedP[:,0]>X.max(0)),axis=1)
            contact['everyRootExteriorByActualMeshAABB']=bool(rootOutside.all())
            rows[name]=contact
            print('R53_EXTERNAL',name,contact['unqualifiedSegments'],rootOutside.all(),flush=True)
        # Existing native brow fibres are different from the wet/lash meshes.
        # Test actual evaluated segment capsules, not a resampled proxy.
        browA=[];browB=[];browR=[];browNames=[]
        for ob in bpy.context.scene.objects:
            if ob.type=='CURVES' and not ob.hide_render and ob.name!=k.NAME:
                BP,BR=f.v.hair_arrays(ob.evaluated_get(deps));mx=np.array(ob.matrix_world)
                BP=BP.astype('f8')@mx[:3,:3].T+mx[:3,3];BR=BR.astype('f8')*np.linalg.norm(mx[:3,:3],ord=2)
                browA.append(BP[:,:-1].reshape(-1,3));browB.append(BP[:,1:].reshape(-1,3))
                browR.append(np.maximum(BR[:,:-1],BR[:,1:]).ravel());browNames.append(ob.name)
        assert len(browNames)==2,('Unexpected native brow objects',browNames)
        BA=np.concatenate(browA);BB=np.concatenate(browB);RB=np.concatenate(browR)
        blo=np.minimum(BA,BB)-RB[:,None];bhi=np.maximum(BA,BB)+RB[:,None]
        MA=testedP[:,:-1].reshape(-1,3);MB=testedP[:,1:].reshape(-1,3);MR=np.maximum(testedR[:,:-1],testedR[:,1:]).ravel()
        mlo=np.minimum(MA,MB)-MR[:,None];mhi=np.maximum(MA,MB)+MR[:,None]
        aggregateCandidates=np.flatnonzero(np.all((mhi+1e-6>=blo.min(0))&(mlo-1e-6<=bhi.max(0)),axis=1))
        pairs=0;overlaps=0;within=0;minimum=None;failures=[]
        for si in aggregateCandidates:
            bi=np.flatnonzero(np.all((bhi+1e-6>=mlo[si])&(blo-1e-6<=mhi[si]),axis=1))
            if not len(bi):continue
            distances,_,_=solver.distances(np.broadcast_to(MA[si],(len(bi),3)),np.broadcast_to(MB[si],(len(bi),3)),BA[bi],BB[bi])
            gap=distances-MR[si]-RB[bi];pairs+=len(bi);overlaps+=int((gap < -1e-6).sum());within+=int((gap<=1e-6).sum())
            minimum=float(gap.min()) if minimum is None else min(minimum,float(gap.min()))
            failures.extend([int(si),int(bi[j]),float(gap[j])] for j in np.flatnonzero(gap<=1e-6)[:20])
        brow={'objects':browNames,'actualBrowSegments':len(BA),'newMasterSegments':len(MA),
            'aggregateAABBCandidateMasterSegments':len(aggregateCandidates),'actualFiniteCandidatePairs':pairs,
            'overlapsBeyondNumericalAllowance':overlaps,'withinOneMicronOrOverlapping':within,
            'minimumCandidateCapsuleGapM':minimum,'failureSamples':failures[:80],
            'method':'Actual evaluated finite capsules, conservative expanded AABB broad phase, exact finite-segment distance refinement; no resampling.',
            'numericalAllowanceM':1e-6}
        external={'status':'PASS_TESTED_STATIC_EXTERNAL_SCOPE' if all(r['unqualifiedSegments']==0 and r['everyRootExteriorByActualMeshAABB'] for r in rows.values()) and within==0 else 'FAIL_OR_UNRESOLVED',
                  'actualOpticalWetLashMeshes':rows,'actualNativeBrowCapsules':brow}
    ratios=np.linalg.norm(np.diff(P,axis=1),axis=2).sum(1)/np.linalg.norm(np.diff(data['initialPaths'],axis=1),axis=2).sum(1)
    result={'source':str(source),'sourceSha256':b.sha(source),'status':'STATIC_MASTER_SCOPE_ONLY',
        'reopened':True,'bodyOtherMeshesSkinMaterialsStageAndOriginalCurvesExact':True,
        'actualNativeVsEvaluatedPositionsAndRadiiExact':True,'rootPositionsAndRadiiRetained':True,
        'curveType':'POLY','inheritedVerifiedCurveIndices':inherited,'inheritedVerifiedCurvesExact':inheritedExact,
        'actualBodyBarycentricRootMaximumErrorM':float(rootError.max()),'nativeSurfaceUVType':'FLOAT2',
        'surfaceUVMap':o.data.surface_uv_map,'actualSurfaceUVMaximumError':uvError,'surfaceUVBindingMatchesActualFoot':uvPassed,
        'surfaceUVTest':'Exact float32 expected barycentric UV, not relaxed absolute tolerance',
        'storedUV':storedUV.tolist(),'actualFootUV':np.array(uvExpected).tolist(),
        'curveCount':len(P),'authoredAndContactTestedCurveIndices':idsAuthored.tolist(),
        'pointsPerCurve':P.shape[1],'actualPhysicalRadiusRangeM':[float(R.min()),float(R.max())],
        'arcLengthRatioRange':[float(ratios.min()),float(ratios.max())],
        'testedSegmentLengthRangeM':[float(np.linalg.norm(np.diff(testedP,axis=1),axis=2).min()),float(np.linalg.norm(np.diff(testedP,axis=1),axis=2).max())],
        'testedSegmentsBelowOneMicron':int((np.linalg.norm(np.diff(testedP,axis=1),axis=2)<1e-6).sum()),
        'actualFiniteBodyCapsules':body,'actualFiniteMasterSelfCapsules':selfContact,
        'otherOpticalWetLashMeshesAndBrows':external,
        'denseChildrenHairDynamicsContinuousAndRuntime':'NOT_ACCEPTED',
        'thickDiagnosticExcluded':True,'externalLibraries':[lib.filepath for lib in bpy.data.libraries],
        'seconds':time.time()-tick}
    k.save(PREFIX+'-saved-static-verification.json',result)
    print('R53_REOPEN',result['curveCount'],selfContact['overlapsBeyondNumericalAllowance'],flush=True)

if __name__=='__main__':main()
