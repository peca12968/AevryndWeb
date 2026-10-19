"""Subdivision-aware support constraints, not a radial-margin parameter sweep.

Extract native Catmull-Clark response weights from a verified local topology
halo. Solve free native cavity displacements against actual rendered facet
planes and both original optical endpoints. Final full-surface tests remain
independent; the 80um anatomical stand-off never changes.
"""
from pathlib import Path
from collections import defaultdict
import bpy,numpy as np,json,time,importlib.util
sp=importlib.util.spec_from_file_location('assembly60solve',Path(__file__).with_name('build-female-next-r0060-cavity-repair.py'));k=importlib.util.module_from_spec(sp);sp.loader.exec_module(k)
b=k.b;f=k.f;E=k.E;OUT=b.S/'aevrynd-female-next-r0060-b-limit-surface-assembly-study.blend'
def save(n,x):k.save(n,x)
def native_pose(o):
    result=np.array([p.co[:] for p in o.data.shape_keys.reference_key.data],dtype='f4');base=result.copy()
    for key in o.data.shape_keys.key_blocks[1:]:
        if key.value:result+=(np.array([p.co[:] for p in key.data],dtype='f4')-base)*key.value
    return result
def evaluated(o,faceIDs=None):
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();p=np.empty(len(me.vertices)*3,dtype='f4');me.vertices.foreach_get('co',p);p=p.reshape(-1,3)
    if faceIDs is None:ev.to_mesh_clear();return p
    ids=np.empty(len(me.polygons),dtype='i4');me.attributes['AFN60_NativeFaceID'].data.foreach_get('value',ids);indices=np.empty(len(me.loops),dtype='i4');me.loops.foreach_get('vertex_index',indices);counts=np.empty(len(me.polygons),dtype='i4');me.polygons.foreach_get('loop_total',counts);assert np.all(counts==4);chosen=np.flatnonzero(np.isin(ids,faceIDs));chosen=chosen[np.argsort(ids[chosen],kind='stable')];corners=indices.reshape(-1,4)[chosen];q=p[corners].copy();ev.to_mesh_clear();return p,q,corners
def local_halo(body,P,faceids,freeOriginal):
    mesh=body.data;allFI=np.array([p.value for p in mesh.attributes['AFN60_NativeFaceID'].data],dtype='i4');faces=[list(p.vertices) for p in mesh.polygons];edgeFaces=defaultdict(list)
    for i,face in enumerate(faces):
        for aa,bb in zip(face,face[1:]+face[:1]):edgeFaces[tuple(sorted((aa,bb)))].append(i)
    adjacency=defaultdict(set)
    for ff in edgeFaces.values():
        for i in ff:adjacency[i].update(ff)
    selected=set(np.flatnonzero(np.isin(allFI,faceids)).tolist());front=set(selected)
    for _ in range(8):
        nxt=set(j for i in front for j in adjacency[i])-selected;selected.update(nxt);front=nxt
    fs=sorted(selected);used=np.unique([v for i in fs for v in faces[i]]);inv=np.full(len(P),-1,dtype='i4');inv[used]=np.arange(len(used));data=bpy.data.meshes.new('AFN60_JACOBIAN_LOCAL_HALO');data.from_pydata(P[used].tolist(),[],[inv[faces[i]].tolist() for i in fs]);data.update();data.attributes.new('AFN60_NativeFaceID','INT','FACE').data.foreach_set('value',allFI[fs]);obj=bpy.data.objects.new(data.name,data);bpy.context.scene.collection.objects.link(obj);obj.hide_render=True;sub=obj.modifiers.new('SameSourceSubdivision','SUBSURF');sub.levels=sub.render_levels=2
    originalIDs=np.array([p.value for p in mesh.attributes['AFN60_NativeVertexID'].data],dtype='i4');sourceToLocal={int(originalIDs[i]):int(inv[i]) for i in used};free=np.array([sourceToLocal[int(i)] for i in freeOriginal],dtype='i4');return obj,used,free,len(fs)
def solve_eye(body,report,side,originalNativeIDs,record):
    tick=time.time();freeIDs=np.array(report['interiorSourceVertexIDs'],dtype='i4');faceIDs=np.array(sorted(set(report['originalPatchFaces'])-set(record['replacementLiningNativeFaces'])),dtype='i4');bpy.context.scene.frame_set(1);bpy.context.view_layer.update();P=native_pose(body);_,Q0,_=evaluated(body,faceIDs);positive=side=='Left';eye=bpy.data.objects['AFN60_'+('L' if positive else 'R')+'_EYE_OUTER_SHELL_APPROX'];iris=bpy.data.objects['AFN60_'+('L' if positive else 'R')+'_IRIS_PUPIL_SURFACE'];opt0=np.concatenate((evaluated(eye),evaluated(iris)));C=(evaluated(eye).min(0)+evaluated(eye).max(0))*.5
    bpy.context.scene.frame_set(21);bpy.context.view_layer.update();_,Q1,_=evaluated(body,faceIDs);opt1=np.concatenate((evaluated(eye),evaluated(iris)));opt=np.concatenate((opt0,opt1)).astype('f8');bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
    helper,used,free,haloFaces=local_halo(body,P,report['originalPatchFaces'],freeIDs);bpy.context.view_layer.update();_,localQ,corners=evaluated(helper,faceIDs);haloError=float(np.linalg.norm(localQ-Q0,axis=2).max());assert haloError<1e-6,('Local topology halo is not equivalent',side,haloError)
    indices=corners.ravel();W=np.empty((len(indices),len(free)),dtype='f4');zero=np.zeros((len(used),3),dtype='f4')
    for start in range(0,len(free),3):
        coords=zero.copy()
        for axis,j in enumerate(range(start,min(start+3,len(free)))):coords[free[j],axis]=1.
        helper.data.vertices.foreach_set('co',coords.ravel());helper.data.update();helper.update_tag();bpy.context.view_layer.update();evaluatedP=evaluated(helper)
        for axis,j in enumerate(range(start,min(start+3,len(free)))):W[:,j]=evaluatedP[indices,axis]
        if start%60==0:print('R60_NATIVE_SUBDIVISION_WEIGHTS',side,start,len(free),flush=True)
    assert np.isfinite(W).all() and W.min()>-1e-7
    lookup={int(v):i for i,v in enumerate(originalNativeIDs)};bodyFree=np.array([lookup[int(v)] for v in freeIDs],dtype='i4');D=P[bodyFree].astype('f8')-C;D/=np.linalg.norm(D,axis=1)[:,None]
    # Verify the extracted native interpolation response with one known vector
    # perturbation, independently of the later constraint solve.
    trial=np.linspace(.00003,.00009,len(free));coords=P[used].copy();coords[free]+=(D*trial[:,None]).astype('f4');helper.data.vertices.foreach_set('co',coords.ravel());helper.data.update();helper.update_tag();bpy.context.view_layer.update();actual=evaluated(helper)[indices].reshape(-1,4,3);predicted=localQ.astype('f8')+(W@(D*trial[:,None])).reshape(-1,4,3);responseError=float(np.linalg.norm(actual-predicted,axis=2).max());assert responseError<1e-6,('Invalid source subdivision response',side,responseError)
    normals=Q0.astype('f8').mean(1)-C;normals/=np.linalg.norm(normals,axis=1)[:,None];scale=float(np.linalg.norm(np.array(body.matrix_world)[:3,:3],ord=2));gap=.00008/scale;support=[]
    for start in range(0,len(normals),256):support.extend((opt@normals[start:start+256].T).max(0).tolist())
    support=np.array(support)+gap;N=np.repeat(normals,4,axis=0);base=np.minimum(np.einsum('ij,ij->i',Q0.reshape(-1,3),N),np.einsum('ij,ij->i',Q1.reshape(-1,3),N));rhs=support.repeat(4)-base;A=W.astype('f8')*(N@D.T);del W
    norm2=np.einsum('ij,ij->i',A,A);impossible=(norm2<1e-18)&(rhs>1e-8);assert not impossible.any(),('Fixed-boundary support conflict',side,int(impossible.sum()))
    x=np.zeros(len(free));iterations=0
    for it in range(3000):
        residual=rhs-A@x;j=int(np.argmax(residual));maximum=float(residual[j])
        if maximum<=2e-9:break
        assert norm2[j]>1e-18; x=np.maximum(0,x+A[j]*(maximum+2e-9)/norm2[j]);iterations=it+1
    finalResidual=float((rhs-A@x).max());assert finalResidual<=1e-8,('Support solve not converged',side,finalResidual,iterations);assert x.max()*scale<.003,('Implausibly large corrective displacement',side,float(x.max()*scale))
    result=np.zeros((len(P),3),dtype='f8');result[bodyFree]=D*x[:,None];row={'sourceNativeFreeVertexIDs':freeIDs.tolist(),'sourceCoreFaceIDs':faceIDs.tolist(),'nativeVariables':len(free),'actualRenderCornerConstraints':len(rhs),'localHaloNativeFaces':haloFaces,'localHaloMaximumActualSurfaceErrorM':haloError,'nativeResponsePerturbationMaximumErrorM':responseError,'maximumSupportResidualLocalM':finalResidual,'physicalStandOffWorldM':.00008,'maximumAdditionalNativeDisplacementWorldM':float(x.max()*scale),'iterations':iterations,'allOriginalEndpointsOpticsSupportUnion':True,'responseMatrixMinimum':float(A.min()),'seconds':time.time()-tick,'scope':'Native subdivision response and original facet support constraints for cavity core only. Actual all-tissue/optical, rim and self surfaces must be independently retested.'};helperData=helper.data;bpy.data.objects.remove(helper,do_unlink=True);bpy.data.meshes.remove(helperData);return result,row
def main():
    tick=time.time();assert not OUT.exists();a=json.loads((E/'a-build-summary.json').read_text());src=Path(a['output']);assert b.sha(src)==a['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(src));body=bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING'];parts=[bpy.data.objects[a['visibleComponents'][str(i)]] for i in range(5)]
    for o in parts:
        for md in o.modifiers:
            if md.type=='SUBSURF':md.levels=md.render_levels
    nativeIDs=np.array([p.value for p in body.data.attributes['AFN60_NativeVertexID'].data],dtype='i4');delta=np.zeros((len(body.data.vertices),3),dtype='f8');reports={}
    for side,row in a['nativeInteriorCorrections'].items():addition,report=solve_eye(body,row,side,nativeIDs,a);delta+=addition;reports[side]=report;save('b-solve-progress.json',reports)
    key=body.data.shape_keys.key_blocks['AFN60_Cavity_Repair'];old=np.array([p.co[:] for p in key.data],dtype='f4');key.data.foreach_set('co',(old.astype('f8')+delta).astype('f4').ravel());body.data.update();np.savez_compressed(E/'b-limit-surface-correction.npz',nativeVertexIDs=nativeIDs,deltaLocal=delta,originalRepairKey=old,finalRepairKey=(old.astype('f8')+delta).astype('f4'))
    for o in parts:
        for md in o.modifiers:
            if md.type=='SUBSURF':md.levels=1
    k.k.set_frame(1);b.camera('face');bpy.context.scene.camera.data.lens=85;bpy.context.preferences.filepaths.save_version=0;bpy.context.scene['AFN60_status']='LIMIT_SURFACE_SUPPORT_ASSEMBLY_PENDING_ACTUAL_VERIFICATION';bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    summary=dict(a);summary.update(output=str(OUT),outputSha256=b.sha(OUT),parentSource=str(src),parentSourceSha256=b.sha(src),method='Native subdivision response constrained optical support solve on the already partitioned cavity. Same80um stand-off, fixed native rim, original optical surfaces/UV/materials/controls unchanged.',limitSurfaceSolve=reports,limitSurfaceCorrection=str(E/'b-limit-surface-correction.npz'),seconds=time.time()-tick,status='PENDING_ACTUAL_ENDPOINT_AND_APPEARANCE_VERIFICATION');save('b-build-summary.json',summary)
    for frame,label in ((1,'b-neutral'),(21,'b-closed')):
        k.k.set_frame(frame);f.E=E;f.render(label,('face','profile','oblique'));k.k.k.k.k.k.k.a.i.ch.review.extras(label,E)
    k.k.set_frame(1);print('R60_LIMIT_SURFACE_CANDIDATE',time.time()-tick,flush=True)
if __name__=='__main__':main()
