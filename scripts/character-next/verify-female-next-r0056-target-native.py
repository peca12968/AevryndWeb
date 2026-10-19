"""Exact source reopening plus static scope checks after visual acceptance.

Use --readback-only when the actual complete form is rejected. Do not turn
native collision flags or point-only checks into a full contact assertion.
"""
from pathlib import Path
import bpy,importlib.util,numpy as np,json,time,sys
from mathutils.bvhtree import BVHTree
sp=importlib.util.spec_from_file_location('check56',Path(__file__).with_name('build-female-next-r0054-clump-volume.py'))
k=importlib.util.module_from_spec(sp);sp.loader.exec_module(k)
b=k.b;f=k.f;E=b.R/'Evidence/character-female-next/r0056-target-native-comb';TAG=sys.argv[sys.argv.index('--prefix')+1] if '--prefix' in sys.argv else 'a'
def save(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def main():
    tick=time.time();report=json.loads((E/(TAG+'-build-summary.json')).read_text());source=Path(report['output']);assert b.sha(source)==report['outputSha256']
    bpy.ops.wm.open_mainfile(filepath=str(k.SRC));before=f.state()
    bpy.ops.wm.open_mainfile(filepath=str(source));after=f.state();assert all(after[x]==before[x] for x in ('meshes','materials','skinFields','stage'))
    assert all(after['curves'][name]==row for name,row in before['curves'].items())
    ob=bpy.data.objects['AFN56_TARGET_NATIVE_MASTER_CURVES'];P,R=f.v.hair_arrays(ob);EP,ER=f.v.hair_arrays(ob.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    data=np.load(E/(TAG+'-native-guide-data.npz'));foundation=np.load(b.R/'Evidence/character-female-next/r0053-new-primary-groom/refined-foundation-data.npz')
    assert np.array_equal(P,data['positions']) and np.array_equal(R,data['radii']) and np.array_equal(P,EP) and np.array_equal(R,ER)
    indices=data['sourceCurveIndices'] if 'sourceCurveIndices' in data.files else np.arange(64)
    assert np.array_equal(P[:,0],foundation['initialPaths'][indices,0].astype('f4')) and np.array_equal(R,foundation['radii'][indices].astype('f4'))
    assert np.isfinite(P).all() and np.isfinite(R).all() and ob.data.surface.name==b.BODY and ob.data.attributes['surface_uv_coordinate'].data_type=='FLOAT2'
    bindings=json.loads((b.R/'Evidence/character-female-next/r0053-new-primary-groom/refined-foundation-build.json').read_text())['rootBindings']
    V,T=b.evaluated(bpy.data.objects[b.BODY],True);roots=[];uvs=[]
    ev=bpy.data.objects[b.BODY].evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh(preserve_all_data_layers=True,depsgraph=bpy.context.evaluated_depsgraph_get());mesh.calc_loop_triangles()
    for binding in [bindings[int(i)] for i in indices]:
        ti=binding['bodyTriangle'];assert T[ti].tolist()==binding['bodyVertices'];bc=np.array(binding['barycentric'])
        roots.append(bc@V[T[ti]]+np.array(binding['normal'])*binding['rootOffsetM'])
        uvs.append(bc@np.array([mesh.uv_layers[0].data[x].uv[:] for x in mesh.loop_triangles[ti].loops]))
    ev.to_mesh_clear();err=np.linalg.norm(P[:,0]-roots,axis=1);assert err.max()<1e-7
    stored=np.array([x.vector[:] for x in ob.data.attributes['surface_uv_coordinate'].data],dtype='f4');assert np.array_equal(stored,np.array(uvs,dtype='f4'))
    lengths=np.linalg.norm(np.diff(P.astype('f8'),axis=1),axis=2);originalLengths=np.linalg.norm(np.diff(data['before'].astype('f8'),axis=1),axis=2).sum(1)
    result={'source':str(source),'sourceSha256':b.sha(source),'reopened':True,'originalBodyOtherMeshesSkinMaterialsStageAndOriginalHairDataExact':True,
        'nativeStoredVsEvaluatedPositionsAndRadiiExact':True,'rootPositionsAndRadiiExact':True,'actualBodyBarycentricRootMaximumErrorM':float(err.max()),'actualBodyUVFloat32BitExact':True,
        'curveCount':len(P),'pointsPerCurve':P.shape[1],'segmentLengthRangeM':[float(lengths.min()),float(lengths.max())],
        'arclengthRatioRange':[float((lengths.sum(1)/originalLengths).min()),float((lengths.sum(1)/originalLengths).max())],
        'bodyCapsules':{'status':'NOT_RUN_AFTER_VISUAL_REJECTION'},'masterSelfCapsules':{'status':'NOT_RUN_AFTER_VISUAL_REJECTION'},'otherMeshesDynamicsRuntime':'NOT_ACCEPTED'}
    if '--readback-only' not in sys.argv:
        tree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True);contact=f.flowcheck.check(P.astype('f8'),R.astype('f8'),tree,V[T],roots=True);result['bodyCapsules']=contact
        if contact['status']=='PASS_TESTED_STATIC_CAPSULES':
            spec=importlib.util.spec_from_file_location('pairs56',Path(__file__).with_name('solve-female-next-r0036-brow-contacts.py'));solver=importlib.util.module_from_spec(spec);spec.loader.exec_module(solver);solver.controls()
            ids,gap,_,_=solver.contacts(P.astype('f8'),R.astype('f8'),1e-6)
            result['masterSelfCapsules']={'status':'PASS_TESTED_STATIC_MASTERS' if not np.any(gap < -1e-6) else 'FAIL_TESTED_STATIC_MASTERS','candidatePairs':len(ids),'overlapsBeyondOneMicron':int((gap < -1e-6).sum()),'minimumCandidateGapM':float(gap.min()) if len(gap) else None,'failurePairs':ids[gap < -1e-6][:80].tolist(),'scope':'All nonadjacent finite64master capsules only, max endpoint radius,1um numeric allowance. Not children or dynamics.'}
    result['seconds']=time.time()-tick;save(TAG+'-reopened-verification.json',result);print('R56_REOPENED',result['bodyCapsules']['status'],result['masterSelfCapsules']['status'],time.time()-tick,flush=True)

if __name__=='__main__':main()
