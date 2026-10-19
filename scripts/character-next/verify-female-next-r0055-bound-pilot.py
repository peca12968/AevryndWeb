"""Independently reopen the exact bound pilot and verify its stated scope."""
from pathlib import Path
import bpy,importlib.util,numpy as np,json,time
from mathutils import Vector
sp=importlib.util.spec_from_file_location('read55',Path(__file__).with_name('solve-female-next-r0055-bound-contact-pilot.py'))
k=importlib.util.module_from_spec(sp);sp.loader.exec_module(k)
b=k.b;f=k.f;E=k.E

def main():
    tick=time.time();report=json.loads((E/'d-build-summary.json').read_text());p=Path(report['output']);assert b.sha(p)==report['outputSha256']
    bpy.ops.wm.open_mainfile(filepath=str(k.k.SRC));before=f.state()
    bpy.ops.wm.open_mainfile(filepath=str(p));after=f.state();assert all(after[x]==before[x] for x in ('meshes','materials','skinFields','stage'))
    assert all(after['curves'][name]==row for name,row in before['curves'].items() if name!='AFN55_CC0_AUTHORED_BOB_GUIDES')
    ob=bpy.data.objects['AFN55_BOUND_CONTACT_BOB_GUIDES'];P,R=f.v.hair_arrays(ob);EP,ER=f.v.hair_arrays(ob.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    data=np.load(E/'d-bound-guide-data.npz');assert np.array_equal(P,data['positions']) and np.array_equal(R,data['radii'])
    assert np.array_equal(P,EP) and np.array_equal(R,ER) and np.isfinite(P).all() and np.isfinite(R).all()
    assert ob.data.attributes['surface_uv_coordinate'].data_type=='FLOAT2' and ob.data.surface.name==b.BODY
    V,T=b.evaluated(bpy.data.objects[b.BODY],True);bindings=json.loads((E/'d-root-bindings.json').read_text())['bindings'];expected=[];expectedUV=[]
    body=bpy.data.objects[b.BODY];ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh(preserve_all_data_layers=True,depsgraph=bpy.context.evaluated_depsgraph_get());mesh.calc_loop_triangles()
    for binding in bindings:
        ti=binding['bodyTriangle'];assert T[ti].tolist()==binding['bodyVertices'];bc=np.array(binding['barycentric']);assert bc.min()>=0 and abs(bc.sum()-1)<1e-12
        expected.append(bc@V[T[ti]]+np.array(binding['normal'])*binding['offsetM'])
        expectedUV.append(bc@np.array([mesh.uv_layers[0].data[x].uv[:] for x in mesh.loop_triangles[ti].loops]))
    ev.to_mesh_clear();rootError=np.linalg.norm(P[:,0]-expected,axis=1);assert rootError.max()<1e-7
    storedUV=np.array([x.vector[:] for x in ob.data.attributes['surface_uv_coordinate'].data],dtype='f4');assert np.array_equal(storedUV,np.array(expectedUV,dtype='f4'))
    contact=json.loads((E/'d-static-body-capsules.json').read_text());selfContact={'status':'NOT_RUN_BEFORE_BODY_PASS'}
    if contact['status']=='PASS_TESTED_STATIC_CAPSULES':
        sp2=importlib.util.spec_from_file_location('pairs55',Path(__file__).with_name('solve-female-next-r0036-brow-contacts.py'));solver=importlib.util.module_from_spec(sp2);sp2.loader.exec_module(solver);solver.controls()
        ids,gap,_,_=solver.contacts(P.astype('f8'),R.astype('f8'),1e-6)
        selfContact={'status':'PASS_TESTED_STATIC_MASTER_PAIRS' if not np.any(gap < -1e-6) else 'FAIL_STATIC_MASTER_PAIRS',
            'candidatePairs':len(ids),'overlapsBeyondOneMicron':int((gap < -1e-6).sum()),'minimumCandidateGapM':float(gap.min()) if len(gap) else None,
            'failurePairs':ids[gap < -1e-6][:80].tolist(),'scope':'All nonadjacent finite248master capsules only; max endpoint radius,1um numeric allowance. No children, other optics/clothing or motion proof.'}
    k.save('d-reopened-verification.json',{'source':str(p),'sourceSha256':b.sha(p),'reopened':True,'originalBodyOtherMeshesSkinMaterialsStageAndOriginalHairDataExact':True,
        'nativeStoredAndEvaluatedPositionsRadiiExact':True,'guides':len(P),'pointsPerGuide':P.shape[1],'actualBodyBarycentricRootMaximumErrorM':float(rootError.max()),
        'actualBodySourceUVFloat32ExactlyMatches':True,'segmentLengthRangeM':[float(np.linalg.norm(np.diff(P,axis=1),axis=2).min()),float(np.linalg.norm(np.diff(P,axis=1),axis=2).max())],
        'bodyCapsules':contact,'masterSelfCapsules':selfContact,'otherMeshDynamicsContinuousRuntime':'NOT_TESTED','seconds':time.time()-tick})
    print('R55_REOPENED',contact['status'],selfContact['status'],time.time()-tick,flush=True)

if __name__=='__main__':main()
