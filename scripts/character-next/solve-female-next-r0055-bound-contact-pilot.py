"""Bounded static guide contact repair preserving the authored rest flow.

Actual anatomical scalp triangles supply new follicles and provenance. All
free paths retain the affine authored rest shape; smooth displacement is
projected against the actual body. This is static authoring, not calibrated
rod dynamics or continuous collision proof. One fixed solver, no sweeps.
"""
from pathlib import Path
import bpy,importlib.util,numpy as np,json,time
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sp=importlib.util.spec_from_file_location('bound55',Path(__file__).with_name('build-female-next-r0055-authored-bob.py'))
k=importlib.util.module_from_spec(sp);sp.loader.exec_module(k)
b=k.b;f=k.f;E=k.E;SRC=b.S/'aevrynd-female-next-r0055-b-landmark-bob-registration.blend'
OUT=b.S/'aevrynd-female-next-r0055-d-bound-contact-bob-pilot.blend'

def save(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def resample(P,n):
    result=[]
    for p in P:
        s=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))];assert np.all(np.diff(s)>1e-7)
        result.append(np.array([np.interp(np.linspace(0,s[-1],n),s,p[:,j]) for j in range(3)]).T)
    return np.array(result)

def closest_barycentric(q,A):
    # Recompute the closest point in float64 on the exact body triangle;
    # BVH's float32 foot can fall just beyond a small triangle edge.
    st=np.linalg.lstsq(np.column_stack((A[1]-A[0],A[2]-A[0])),q-A[0],rcond=None)[0]
    bc=np.r_[1-st.sum(),st];candidates=[]
    if bc.min()>=0:candidates.append(bc)
    for i,j in ((0,1),(1,2),(2,0)):
        edge=A[j]-A[i];t=float(np.clip(np.dot(q-A[i],edge)/np.dot(edge,edge),0,1));w=np.zeros(3);w[i]=1-t;w[j]=t;candidates.append(w)
    return min(candidates,key=lambda w:np.linalg.norm(w@A-q))

def main():
    tick=time.time();report=json.loads((E/'b-build-summary.json').read_text());assert b.sha(SRC)==report['outputSha256']
    bpy.ops.wm.open_mainfile(filepath=str(SRC));before=f.state();original=bpy.data.objects['AFN55_CC0_AUTHORED_BOB_GUIDES']
    Q,rr=f.v.hair_arrays(original);body=bpy.data.objects[b.BODY];V,T=b.evaluated(body,True);tri=V[T]
    tree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True)
    domain=bpy.data.objects['AFN53_ANATOMICAL_SCALP'];SV,ST=b.evaluated(domain,True);scalp=BVHTree.FromPolygons(SV.tolist(),ST.tolist(),all_triangles=True)
    actualIds=np.array([x.value for x in domain.data.attributes['AFN53_BodyTriangle'].data],dtype='i4')
    bindings=[];roots=[];errors=[];uvs=[];bvhFootDifferences=[]
    ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh(preserve_all_data_layers=True,depsgraph=bpy.context.evaluated_depsgraph_get());mesh.calc_loop_triangles()
    for q in Q[:,0]:
        foot,normal,index,distance=scalp.find_nearest(Vector(q));ti=int(actualIds[index]);A=tri[ti]
        assert np.max(np.abs(np.sort(SV[ST[index]],axis=0)-np.sort(A,axis=0)))<1e-7,'Scalp/body triangle identity mismatch'
        bc=closest_barycentric(q.astype('f8'),A)
        bvhFootDifferences.append(float(np.linalg.norm(bc@A-np.array(foot))))
        n=np.cross(A[1]-A[0],A[2]-A[0]);n/=np.linalg.norm(n);root=bc@A+n*.00018
        assert f.flowcheck.cap.solid.classify(tree,tri,Vector(root))=='outside'
        loops=mesh.loop_triangles[ti].loops;uvs.append(bc@np.array([mesh.uv_layers[0].data[i].uv[:] for i in loops]))
        roots.append(root);errors.append(float(np.linalg.norm(bc@A-q)));bindings.append({'bodyTriangle':ti,'bodyVertices':T[ti].tolist(),'barycentric':bc.tolist(),'normal':n.tolist(),'offsetM':.00018,'registrationDistanceM':errors[-1]})
    ev.to_mesh_clear();roots=np.array(roots);N=64;rest=resample(Q.astype('f8'),N)
    u=np.linspace(0,1,N);rest+=(roots-rest[:,0])[:,None]*(1-u[None,:,None])**2;rest[:,0]=roots
    P=rest.copy();R=np.broadcast_to(np.linspace(.000055,.000009,N),(len(P),N)).copy();history=[]
    # Bounded projected smoothing of the displacement from the authored rest.
    # Five-ray/solid-angle classification, not nearest-normal sign inference.
    for iteration in range(24):
        delta=P-rest;nextDelta=delta.copy();nextDelta[:,1:-1]=.25*delta[:,:-2]+.5*delta[:,1:-1]+.25*delta[:,2:]
        P=rest+.985*nextDelta;P[:,0]=roots;projected=0;insideCount=0
        for ci in range(len(P)):
            for j in range(1,N):
                hit,normal,ti,distance=tree.find_nearest(Vector(P[ci,j]));required=R[ci,j]+.00015
                if distance>.012:continue
                state=f.flowcheck.cap.solid.classify(tree,tri,Vector(P[ci,j]))
                if state not in ('outside','inside'):raise RuntimeError(('Unresolved point classification',ci,j,state))
                if state=='inside' or distance<required:
                    n=np.cross(tri[ti,1]-tri[ti,0],tri[ti,2]-tri[ti,0]);n/=np.linalg.norm(n)
                    P[ci,j]=np.array(hit)+n*required;projected+=1;insideCount+=state=='inside'
        history.append({'iteration':iteration,'projectedPoints':projected,'insidePointsBeforeProjection':insideCount})
        if iteration%4==0:print('R55_STATIC_SOLVE',iteration,projected,insideCount,flush=True)
    P=P.astype('f4');R=R.astype('f4');assert np.isfinite(P).all()
    displacement=np.linalg.norm(P-rest,axis=2);assert displacement.max()<.025,'Repair exceeds bounded local scope'
    d=original.data.copy();d.name='AFN55_BOUND_CONTACT_BOB_GUIDES';d.resize_curves([N]*len(P));d.position_data.foreach_set('vector',P.ravel());d.attributes['radius'].data.foreach_set('value',R.ravel())
    d.surface=body;d.surface_uv_map=body.data.uv_layers[0].name
    attr=d.attributes.new('surface_uv_coordinate','FLOAT2','CURVE');attr.data.foreach_set('vector',np.array(uvs,dtype='f4').ravel())
    ob=bpy.data.objects.new(d.name,d);bpy.context.scene.collection.objects.link(ob);original.hide_render=True;original.hide_set(True)
    ob['scope']='248source-authored guides, new actual anatomical scalp/barycentric/UV follicles, bounded local static contact repair. No children, self/continuous dynamics or runtime accepted.'
    after=f.state();assert all(after[x]==before[x] for x in ('meshes','materials','skinFields','stage'))
    assert all(after['curves'][name]==row for name,row in before['curves'].items() if name!=original.name)
    np.savez_compressed(E/'d-bound-guide-data.npz',positions=P,radii=R,roots=roots,rest=rest,sourceUV=np.array(uvs,dtype='f4'))
    save('d-root-bindings.json',{'bindings':bindings,'scope':'New actual scalp follicles on the BVH-selected anatomical domain triangle, recomputed with float64 constrained barycentrics. Domain/anatomy held fixed, never chosen by a failed segment clearance. No exact global nearest-distance claim.','registrationDistanceRangeM':[min(errors),max(errors)],'maximumBvhFloat32FootVsConstrainedDoubleFootDifferenceM':max(bvhFootDifferences)})
    b.camera('face');bpy.context.scene.camera.data.lens=85;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    save('d-build-summary.json',{'source':str(SRC),'sourceSha256':b.sha(SRC),'output':str(OUT),'outputSha256':b.sha(OUT),
        'guideCount':len(P),'pointsPerGuide':N,'rootBinding':'ACTUAL_SCALP_BODY_BARYCENTRIC_FLOAT2_UV',
        'rootRegistrationDistanceRangeM':[min(errors),max(errors)],'maximumFreeCorrectionFromRootAdjustedRestM':float(displacement.max()),
        'solverHistory':history,'iterations':24,'scope':'One static source-flow-preserving local guide contact pilot. Not rod dynamics.','originalBodySkinOtherGeometryMaterialsStageUnchanged':True})
    f.E=E;f.render('d-actual-fibres',('face','oblique','profile'));k.k.k.k.k.a.i.ch.review.extras('d-actual-fibres',E)
    d.attributes['radius'].data.foreach_set('value',np.full_like(R,.0005).ravel());bpy.context.view_layer.update()
    f.render('d-path-diagnostic',('face','oblique','profile'));k.k.k.k.k.a.i.ch.review.extras('d-path-diagnostic',E)
    d.attributes['radius'].data.foreach_set('value',R.ravel());bpy.context.view_layer.update()
    contact=f.flowcheck.check(P.astype('f8'),R.astype('f8'),tree,tri,roots=True);save('d-static-body-capsules.json',contact)
    print('R55_BOUND_PILOT_READY',contact['status'],contact['unqualifiedSegments'],time.time()-tick,flush=True)

if __name__=='__main__':main()
