"""Second r88 construction: actual subdivision-aware inner-lining support.
Reuse established interpolation solve at unchanged80um stand-off; neutral only.
All actual displayed surfaces still need independent testing, including the rim.
"""
from pathlib import Path
from collections import defaultdict
import bpy,numpy as np,json,hashlib,importlib.util,time
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(r'D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0088-lid-aperture';OUT=S/'aevrynd-female-next-r0088-b-supported-lid-aperture.blend'
sp=importlib.util.spec_from_file_location('r88author',Path(__file__).with_name('build-female-next-r0088-lid-aperture.py'));k=importlib.util.module_from_spec(sp);sp.loader.exec_module(k);m=k.m;q=m.q;v=k.v;v.E=E
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x):(E/n).write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
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
def solve_neutral(body,report,side,originalNativeIDs,record):
    tick=time.time();freeIDs=np.array(report['interiorSourceVertexIDs'],dtype='i4');faceIDs=np.array(sorted(set(report['originalPatchFaces'])-set(record['replacementLiningNativeFaces'])),dtype='i4');bpy.context.scene.frame_set(1);bpy.context.view_layer.update();P=native_pose(body);_,Q0,_=evaluated(body,faceIDs);positive=side=='Left';eye=bpy.data.objects['AFN60_'+('L' if positive else 'R')+'_EYE_OUTER_SHELL_APPROX'];iris=bpy.data.objects['AFN60_'+('L' if positive else 'R')+'_IRIS_PUPIL_SURFACE'];opt0=np.concatenate((evaluated(eye),evaluated(iris)));C=(evaluated(eye).min(0)+evaluated(eye).max(0))*.5
    Q1=Q0.copy();opt=opt0.astype('f8')
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
    result=np.zeros((len(P),3),dtype='f8');result[bodyFree]=D*x[:,None];row={'sourceNativeFreeVertexIDs':freeIDs.tolist(),'sourceCoreFaceIDs':faceIDs.tolist(),'nativeVariables':len(free),'actualRenderCornerConstraints':len(rhs),'localHaloNativeFaces':haloFaces,'localHaloMaximumActualSurfaceErrorM':haloError,'nativeResponsePerturbationMaximumErrorM':responseError,'maximumSupportResidualLocalM':finalResidual,'physicalStandOffWorldM':.00008,'maximumAdditionalNativeDisplacementWorldM':float(x.max()*scale),'iterations':iterations,'neutralOnlyOpticalSupport':True,'responseMatrixMinimum':float(A.min()),'seconds':time.time()-tick,'scope':'Native subdivision response and original facet support constraints for cavity core only. Actual all-tissue/optical, rim and self surfaces must be independently retested.'};helperData=helper.data;bpy.data.objects.remove(helper,do_unlink=True);bpy.data.meshes.remove(helperData);return result,row
def main():
 tick=time.time();a=json.loads((E/'a-build-summary.json').read_text());parent=Path(a['output']);assert not OUT.exists() and sha(parent)==a['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(parent));s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();body=bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING'];ctrl=bpy.data.objects[a['control']];reference=json.loads((E.parent/'r0060-ocular-assembly/b-build-summary.json').read_text());nativeIDs=q.arr(body.data.attributes['AFN60_NativeVertexID'].data,'value',len(body.data.vertices),dtype='i4');line=np.load(E/'a-native-aperture-lineage.npz');arrays={n:line[n].copy() for n in line.files};reports={}
 for label,side in (('Left','L'),('Right','R')):
  addition,row=solve_neutral(body,reference['nativeInteriorCorrections'][label],label,nativeIDs,reference);world=addition@np.array(body.matrix_world)[:3,:3].T;name,local=k.sculpt_key(body,'AFN88_'+side+'_LINING_LIMIT_SUPPORT',world,ctrl,side);arrays[side+'_liningSupportLocalDelta']=local;reports[side]=dict(row,shapeKey=name);save('b-support-progress.json',reports);bpy.context.view_layer.update()
 # Refit the same lash frames to the repaired actual displayed skin; no strand thinning.
 skin=bpy.data.objects['AFN74_SKIN_AND_EXISTING_OCULAR_LINING'];actual=m.rig.k.mesh(skin);V1=actual['V'];V0=arrays['sourceSkinNeutralWorld'];T0=arrays['sourceSkinTriangles'];assert np.array_equal(actual['T'],T0);H0=arrays['sourceHelperNeutralWorld'];tree=BVHTree.FromPolygons(V0.tolist(),T0.tolist(),all_triangles=True);curves=bpy.data.objects['AFN57_NATIVE_LASHES'];counts=np.array([c.points_length for c in curves.data.curves]);starts=np.r_[0,np.cumsum(counts)[:-1]];newDelta={side:np.zeros_like(H0) for side in ('L','R')};bindings=[]
 for ci,(st,n) in enumerate(zip(starts,counts)):
  st=int(st);n=int(n);root=H0[st];co,_,face,gap=tree.find_nearest(Vector(root));tri=T0[face];bc=m.rig.base.bary(np.array(co),V0[tri]);A0=bc@V0[tri];A1=bc@V1[tri];rot=k.frame(V1[tri])@k.frame(V0[tri]).T;Q=(H0[st:st+n]-A0)@rot.T+A1;side='L' if root[0]>0 else 'R';newDelta[side][st:st+n]=Q-H0[st:st+n];bindings.append({'curve':ci,'side':side,'triangle':tri.tolist(),'barycentric':bc.tolist(),'sourceRootDistanceM':float(gap),'rootWorldMoveM':float(np.linalg.norm(Q[0]-root))})
 helper=bpy.data.objects['AFN59_LASHES_NATIVE_POINT_POSES'];basis=q.arr(helper.data.shape_keys.key_blocks[0].data,'co',len(helper.data.vertices),3);inv=np.linalg.inv(np.array(helper.matrix_world)[:3,:3])
 for side in ('L','R'):
  dd=newDelta[side]@inv.T;helper.data.shape_keys.key_blocks['AFN88_'+side+'_REST_LASH_FRAMES'].data.foreach_set('co',(basis+dd).astype('f4').ravel());arrays[side+'_lashHelperLocalDelta']=dd;arrays[side+'_lashHelperWorldDelta']=newDelta[side]
 arrays['authoredSkinNeutralWorld']=V1;np.savez_compressed(E/'b-native-aperture-lineage.npz',**arrays);save('b-lash-root-bindings.json',bindings);s.frame_set(1);bpy.context.view_layer.update();m.rig.shade.settings();s.render.hair_subdiv=3;m.rig.k.b.camera('face');s.camera.data.lens=85;s['AFN88_scope']='Explicit native lid arcs plus subdivision-aware anatomical inner support,80um existing stand-off; actual neutral and intermediate finite contact remain unaccepted.';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True);summary=dict(a);summary.update(output=str(OUT),outputSha256=sha(OUT),outputBytes=OUT.stat().st_size,parentSource=str(parent),parentSourceSha256=sha(parent),supportConstruction=reports,method='Native rest aperture with actual subdivision support reconstruction, not a coefficient/radius/clearance sweep.',secondsBeforePreview=time.time()-tick);save('b-build-summary.json',summary);rows=[]
 for view in ('face','body-face','oblique'):rows.append(v.image('b-supported',view));save('b-pilot-controls.json',rows)
 print('R88_SUPPORTED_NATIVE_APERTURE_PILOT_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
