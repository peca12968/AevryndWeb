"""Native inward socket contact constraints, preserving eyeballs and topology.

Use complete actual eyeball support (no fitted-sphere collider). One connected
native inward-wall region per eye is detected from measured crossing seeds.
Each wall quad gets a separating support plane. Dykstra projections find the
minimum per-vertex adjustment satisfying incident wall planes. This is a static
structural candidate, not a physical lid solver or blink qualification.
"""
import bpy,importlib.util,json,sys,time
import numpy as np
from pathlib import Path
from collections import deque,defaultdict
from mathutils import Vector
from mathutils.bvhtree import BVHTree
spec=importlib.util.spec_from_file_location('b28',Path(__file__).with_name('build-female-next-r0028-cc0-foundation.py'));b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
E=b.R/'Evidence/character-female-next/r0029-native-eye-interface';E.mkdir(parents=True,exist_ok=True)
SRC=b.OUT;OUT=b.S/'aevrynd-female-next-r0029-a-native-eye-interface.blend'
def save(n,x):(E/n).write_text(json.dumps(x,indent=2)+'\n',encoding='utf8')
def read(n):return json.loads((E/n).read_text(encoding='utf8'))
def signature(o):return {'mesh':b.mesh_signature(o.data),'matrix':b.matrix(o.matrix_world)}
def render(label):
    states=[(o,list(o.location),list(o.rotation_euler),list(o.scale)) for o in bpy.context.scene.objects if o.type=='LIGHT']
    b.render(label)
    # Restore original transform components exactly. Matrix assignment can
    # round Euler decomposition and subtly change the next saved-light pass.
    for o,loc,rot,scale in states:o.location=loc;o.rotation_euler=rot;o.scale=scale
    bpy.context.view_layer.update()
def project(p,constraints):
    q=p.copy();errors=[np.zeros(3) for _ in constraints]
    for step in range(120):
        old=q.copy()
        for k,(n,h) in enumerate(constraints):
            y=q+errors[k];q=y+max(0.,h-n@y)*n;errors[k]=y-q
        if np.linalg.norm(q-old)<1e-12 and max(h-n@q for n,h in constraints)<1e-11:break
    residual=max(h-n@q for n,h in constraints);assert residual<1e-9
    return q,step+1
def main():
    expected='68aa031b5ef4ad3353129eeb9ac881ef7237ed840928e05bd0c4a6b6e32cba6c';assert b.sha(SRC)==expected
    save('round-contract.json',{'previousGoalTurn':'progress: independent r28 female geometry source and matched full-head renders saved/verified/pushed, actual eye wall crossings discovered.','source':str(SRC),'sourceSha256':expected,'hypothesis':'All measured body-eye crossing faces point toward the globe; the existing inward wall can be made contact-conforming without resizing/repositioning the eyes or changing exterior facial anatomy.','method':'Native inward-face connectivity seeded by actual coarse crossings, with actual eyeball support planes and minimum per-vertex halfspace correction. Preserve base topology/UV and existing Multires data.','candidateCount':1,'clearanceM':.00008,'reject':['Any coarse body-eye crossing after repair.','More than 2.5mm native vertex movement.','Full sculpt body-eye crossing, new changed-region self contact or visible rim/shape regression.'],'resourceCheckpointMinutes':45,'diagnosticBudgetMinutes':10,'limits':'One Blender/four threads; no shader/lighting changes, no eye shrink/translate, no blink, hair or engine claims.'})
    bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;b.E=E
    body=bpy.data.objects[b.BODY];mod=body.modifiers[0];original={o.name:signature(o) for o in s.objects if o.type=='MESH'};original_config=b.config(s)
    b.setup(s,original_config);render('before')
    before_high,before_tri=b.evaluated(body,True);mod.levels=0;bpy.context.view_layer.update();v,t=b.evaluated(body,True);assert len(v)==len(body.data.vertices);body.data.calc_loop_triangles();native_t=np.array([list(x.vertices) for x in body.data.loop_triangles]);assert np.array_equal(t,native_t)
    poly_idx=np.array([x.polygon_index for x in body.data.loop_triangles]);polys=[list(p.vertices) for p in body.data.polygons];centres=np.array([v[ids].mean(0) for ids in polys]);normals=np.array([list(body.matrix_world.to_3x3()@p.normal) for p in body.data.polygons]);normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-20)
    adj=defaultdict(set);edges=defaultdict(list)
    for i,ids in enumerate(polys):
        for a,c in zip(ids,ids[1:]+ids[:1]):edges[tuple(sorted((a,c)))].append(i)
    for fs in edges.values():
        for f in fs:adj[f].update(set(fs)-{f})
    tree=BVHTree.FromPolygons(v.tolist(),t.tolist(),all_triangles=True,epsilon=0.0);inspection=read('native-interface-inspection.json');constraints=defaultdict(list);regions={};margin=.00008
    for name,native in inspection['native'].items():
        eye=bpy.data.objects[name];p,pt=b.evaluated(eye,True);eyetree=BVHTree.FromPolygons(p.tolist(),pt.tolist(),all_triangles=True);pairs=tree.overlap(eyetree);seed=set(int(poly_idx[a]) for a,c in pairs);center=np.array(native['fittedSphereCenterM']);r=native['fittedMedianRadiusM'];delta=centres-center;distance=np.linalg.norm(delta,axis=1);cosine=np.einsum('ij,ij->i',normals,delta)/np.maximum(distance,1e-20)
        valid=set(np.flatnonzero((distance<1.7*r)&(cosine<-.2)));assert seed<=valid
        region=set(seed);queue=deque(seed)
        while queue:
            for n in adj[queue.popleft()]:
                if n in valid and n not in region:region.add(n);queue.append(n)
        touched=set();planes=[]
        for i in sorted(region):
            n=delta[i]/distance[i];h=float(np.max(p@n)+margin);planes.append({'polygon':i,'normal':n.tolist(),'offset':h})
            for vi in polys[i]:constraints[vi].append((n,h));touched.add(vi)
        regions[name]={'seedFaces':sorted(seed),'inwardWallFaces':sorted(region),'inwardWallVertices':sorted(touched),'planes':planes,'crossingTrianglePairsBefore':len(pairs),'normalTest':'Native wall face unit normal dot unit vector eye-center to face-center < -0.2; connected to actual crossing faces, within 1.7 median diagnostic radii. Sphere fit selects locality only, not clearance shape.','actualEyeVertexSupportClearanceM':margin}
    solved=v.copy();iterations=[]
    for vi,cs in constraints.items():solved[vi],steps=project(v[vi],cs);iterations.append(steps)
    displacement=np.linalg.norm(solved-v,axis=1);changed=np.flatnonzero(displacement>1e-10);maximum=float(displacement.max());assert maximum<.0025
    inv=body.matrix_world.inverted()
    for i in changed:body.data.vertices[int(i)].co=inv@Vector(solved[i].tolist())
    body.data.update();bpy.context.view_layer.update();coarse_v,coarse_t=b.evaluated(body,True);coarse_tree=BVHTree.FromPolygons(coarse_v.tolist(),coarse_t.tolist(),all_triangles=True);coarse={}
    for name in regions:
        p,pt=b.evaluated(bpy.data.objects[name],True);coarse[name]=len(coarse_tree.overlap(BVHTree.FromPolygons(p.tolist(),pt.tolist(),all_triangles=True)))
    save('coarse-feasibility.json',{'regions':regions,'changedNativeVertices':changed.tolist(),'nativeDisplacementMaximumM':maximum,'nativeDisplacementMeanChangedM':float(displacement[changed].mean()),'solverMaximumSweeps':max(iterations),'coarseBodyEyeTrianglePairs':coarse,'originalEyeSignatures':{n:original[n] for n in regions},'method':'Fixed support halfspaces of actual eyeball geometry; native inward wall quads only. Per-vertex least displacement via Dykstra, no eye changes, no cavity exclusions.','status':'PASS_COARSE_CONTACT' if not any(coarse.values()) else 'REJECT_COARSE_CONTACT','limits':'This coarse test does not imply full sculpt success or any animation/contact minimum.'})
    if any(coarse.values()):raise RuntimeError('Coarse feasibility rejected; stop before sculpt expansion and saved candidate.')
    mod.levels=mod.render_levels=mod.sculpt_levels=3;bpy.context.view_layer.update();after_high,after_tri=b.evaluated(body,True);assert np.array_equal(before_tri,after_tri)
    high_displacement=np.linalg.norm(after_high-before_high,axis=1);moved=np.flatnonzero(high_displacement>1e-9)
    np.savez_compressed(E/'native-correction-data.npz',baseBeforeWorld=v,baseAfterWorld=coarse_v,changedNativeVertices=changed,highBeforeWorld=before_high,highAfterWorld=after_high,triangles=after_tri)
    for name in regions:assert signature(bpy.data.objects[name])==original[name]
    assert b.mesh_signature(body.data)['uv']==original[b.BODY]['mesh']['uv'];assert len(body.data.vertices)==original[b.BODY]['mesh']['vertices'];assert b.config(s)==original_config
    s['AFN29_status']='NATIVE_SOCKET_CONTACT_REPAIR_STATIC_STUDY_UNVERIFIED';s['AFN29_clearanceM']=margin;b.camera('face');bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    save('build-verification.json',{'source':str(SRC),'sourceSha256':b.sha(SRC),'output':str(OUT),'outputSha256':b.sha(OUT),'nativeChangedVertices':changed.tolist(),'nativeMovementMaximumM':maximum,'highChangedVertices':len(moved),'highMovementMaximumM':float(high_displacement.max()),'highChangedBoundsM':{'min':after_high[moved].min(0).tolist(),'max':after_high[moved].max(0).tolist()},'baseTopologyUVPreserved':True,'originalSourceSignatures':original,'eyeGeometryAndTransformsExact':True,'lightingExposureMaterialsUnchanged':True,'coarseContact':coarse,'sculpt':'Multires level3 data retained; original sculpt displacements evaluated over corrected native cage. No remesh, smoothing pass, shader/eye geometry edits.','decision':'UNVERIFIED_STATIC_FUNCTIONAL_CANDIDATE_NO_APPEARANCE_SCORE'})
    render('after');print('R0029_BUILD_DONE',json.dumps({'changed':len(changed),'maximumM':maximum,'coarse':coarse}),flush=True)
if __name__=='__main__':main()
