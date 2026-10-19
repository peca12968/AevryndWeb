"""Independent reopened integrated source, root lineage and native-fibre check."""
import bpy,importlib.util,json,time,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
spec=importlib.util.spec_from_file_location('f33',Path(__file__).with_name('build-female-next-r0033-bob-fibres.py'));f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f);g=f.g
v32=g.module('v32','verify-female-next-r0032-registered-skin.py')

def stage():
    s=bpy.context.scene
    return {'config':g.b.config(s),'lights':[(o.name,list(o.location),list(o.rotation_euler),list(o.scale),o.data.energy,list(o.data.color)) for o in s.objects if o.type=='LIGHT']}

def materials(names):
    return {name:[v32.material_signature(m) if m else None for m in bpy.data.objects[name].data.materials] for name in names}

def main():
    start=time.time();c=f.c;c.configure();report=json.loads((g.E/'c-fibre-build-verification.json').read_text());path=Path(report['output']);assert g.b.sha(path)==report['outputSha256']
    bpy.ops.wm.open_mainfile(filepath=str(g.SRC));names=[o.name for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render];original={n:g.signature(bpy.data.objects[n]) for n in names};original_material=materials(names);original_stage=stage()
    bpy.ops.wm.open_mainfile(filepath=str(path));actual={n:g.signature(bpy.data.objects[n]) for n in names};assert actual==original and materials(names)==original_material and stage()==original_stage
    native=[o for o in bpy.context.scene.objects if o.type=='CURVES' and not o.hide_render];assert len(native)==1;o=native[0];d=o.data;assert not o.modifiers and o.parent==bpy.data.objects[g.b.BODY]
    local,radii=f.arrays(d);cache_path=g.b.S/'aevrynd-female-next-r0033-c-bob-fibres.npz';cache=np.load(cache_path)
    assert np.array_equal(local,cache['positions']) and np.array_equal(radii,cache['radii']);assert np.isfinite(local).all() and np.isfinite(radii).all() and radii.min()>0
    assert len(d.curves)==12000 and len(d.points)==12000*128 and all(x.value==1 for x in d.attributes['curve_type'].data)
    matrix=np.array(o.matrix_world,dtype='f8');P=local.astype('f8')@matrix[:3,:3].T+matrix[:3,3];r=radii.astype('f8')*np.linalg.norm(matrix[:3,:3],ord=2)
    body=bpy.data.objects[g.b.BODY];V,T=g.b.evaluated(body,True);tri=V[T];tree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True)
    root_tri=tri[cache['rootTriangles']];root_bary=cache['rootBarycentric'];skin=np.einsum('ni,nij->nj',root_bary,root_tri)
    normals=np.cross(root_tri[:,1]-root_tri[:,0],root_tri[:,2]-root_tri[:,0]);normals/=np.linalg.norm(normals,axis=1)[:,None];target=skin+normals*.00018
    errors=np.linalg.norm(P[:,0]-target,axis=1);assert errors.max()<1e-6,errors.max();assert np.max(abs(root_bary.sum(1)-1))<1e-10
    guide_indices=cache['guideIndices'];guide_weights=cache['guideWeights'];parts=cache['parts'];assert np.all(guide_indices>=0) and np.all(guide_indices<108);assert np.max(abs(guide_weights.sum(1)-1))<1e-6 and guide_weights.min()>=0
    assert np.all(guide_indices[parts<0]<54) and np.all(guide_indices[parts>0]>=54)
    audit=g.check(P,r,tree,tri);g.save('c-reopened-all-fibre-body-contact.json',audit)
    optics={};hair_min=P.min(1)-r.max(1)[:,None];hair_max=P.max(1)+r.max(1)[:,None]
    # Per-curve capsule AABBs avoid millions of irrelevant optic queries while
    # certifying the entire finite curve, not just sampled points.
    for name in names:
        if name==g.b.BODY:continue
        v,t=g.b.evaluated(bpy.data.objects[name],True);sep=np.maximum(v.min(0)-hair_max,hair_min-v.max(0));separated=np.maximum(sep,0).max(1)>1e-6;rootsep=np.maximum(v.min(0)-P[:,0]-r[:,0,None],P[:,0]-r[:,0,None]-v.max(0));root_outside=np.maximum(rootsep,0).max(1)>1e-6
        assert root_outside.all(),(name,'root in optical AABB')
        ids=np.flatnonzero(~separated);row={'completeCurveAABBSeparated':int(separated.sum()),'remainingCurves':len(ids),'allRootsOutsideOpticalAABB':True}
        if len(ids):row['remainingCapsules']=g.check(P[ids],r[ids],BVHTree.FromPolygons(v.tolist(),t.tolist(),all_triangles=True),v[t],roots=False)
        optics[name]=row
    g.save('c-reopened-optical-contact.json',optics)
    assert not bpy.data.libraries and not bpy.data.texts
    before=json.loads((g.E/'before-renders.json').read_text())['rows'];after=json.loads((g.E/'c-fibres-renders.json').read_text())['rows'];keys=('view','light','cameraMatrix','lens','resolution','engine','viewTransform','look','exposure','gamma','lights','world');matched=all({k:a[k] for k in keys}=={k:b[k] for k in keys} for a,b in zip(before,after));assert len(before)==len(after)==6 and matched
    g.b.E=g.E;g.b.camera('face');bpy.context.scene.render.filepath=str(g.E/'c-reopened-face.png');bpy.ops.render.render(write_still=True)
    result={'status':'PASS_REOPENED_STATIC_SCOPE' if audit['status']=='PASS_TESTED_STATIC_CAPSULES' and all(x.get('remainingCapsules',{}).get('status','PASS_TESTED_STATIC_CAPSULES')=='PASS_TESTED_STATIC_CAPSULES' for x in optics.values()) else 'FAIL_OR_UNRESOLVED','output':str(path),'outputSha256':g.b.sha(path),'cache':str(cache_path),'cacheSha256':g.b.sha(cache_path),'nineOriginalVisibleMeshesAndUVExact':actual,'allSourceSkinAndOpticalMaterialsExact':True,'stageAndLightingExact':True,'sixMatchedRenderConditionsExact':True,'allNativeFibrePositionsRadiiExactlyMatchCache':True,'curves':len(d.curves),'points':len(d.points),'worldMatrix':matrix.tolist(),'positionsSha256':hashlib.sha256(local.tobytes()).hexdigest(),'radiiSha256':hashlib.sha256(radii.tobytes()).hexdigest(),'rootBindingMaximumErrorM':float(errors.max()),'allRootsActualBodyTriangleBound':True,'samePartGuideLineage':True,'bodyContact':audit,'opticalContact':optics,'externalLibraries':0,'textBlocks':0,'seconds':time.time()-start,'limits':['Neutral static body/optical capsule tests only.','Hair/hair contact and self collision not tested.','No rig, continuous head motion, wind, simulation, cloth, export, LOD, engine/performance or whole-character acceptance.','Groom appearance must be judged separately from these contact/structure results.']};g.save('c-saved-fibre-verification.json',result);print('R33_REOPENED_DONE',result['status'],time.time()-start,flush=True)

if __name__=='__main__':main()
