"""Reopen actual complete character; verify actual display hair, not guides.

All free capsules vs rendered body/optics. Original neutral/closed geometry,
facial fibres, skin/materials/stage must remain exact. Hair/hair, tie/fibre and
continuous motion are expressly not certified by this rest-pose check.
"""
from pathlib import Path
import bpy,numpy as np,json,time,hashlib,importlib.util
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sp=importlib.util.spec_from_file_location('groom61verify',Path(__file__).with_name('build-female-next-r0061-surface-flow-groom.py'));g=importlib.util.module_from_spec(sp);sp.loader.exec_module(g)
k=g.k;v59=k.v59

def digest(x):return hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()
def mesh_signature(o):
    keys={p.name:digest(np.array([v.co[:] for v in p.data],dtype='f4')) for p in o.data.shape_keys.key_blocks}
    return {'native':k.b.mesh_signature(o.data),'keys':keys,'matrix':np.array(o.matrix_world).tolist(),'materials':[k.f.v.v32.material_signature(m) for m in o.data.materials]}
def read_hair(o):
    d=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;P=np.empty(len(d.position_data)*3,'f4');d.position_data.foreach_get('vector',P);rr=np.empty(len(d.position_data),'f4');d.attributes['radius'].data.foreach_get('value',rr);counts=np.array([c.points_length for c in d.curves]);assert np.all(counts==224)
    return P.reshape(-1,224,3),rr.reshape(-1,224)
def raise_subdivision():
    for o in bpy.data.objects:
        if o.type=='MESH':
            for md in o.modifiers:
                if md.type=='SUBSURF':md.levels=md.render_levels

def main():
    tick=time.time();ref=json.loads((g.E/'b-fibres-build-summary.json').read_text());out=Path(ref['output']);assert g.sha(out)==ref['outputSha256'];names=list(json.loads((g.E.parent/'r0060-ocular-assembly/b-build-summary.json').read_text())['visibleComponents'].values())
    bpy.ops.wm.open_mainfile(filepath=str(g.SRC));stage=k.f.v.stage();base={n:mesh_signature(bpy.data.objects[n]) for n in names};facial={n:v59.native_curves(bpy.data.objects[n]) for n in ('AFN57_NATIVE_LASHES','AFN57_NATIVE_BROWS')};raise_subdivision();poses={}
    for frame in (1,21):
        bpy.context.scene.frame_set(frame);bpy.context.view_layer.update();poses[frame]={n:digest(k.mesh(bpy.data.objects[n])['V']) for n in names}
    bpy.ops.wm.open_mainfile(filepath=str(out));assert k.f.v.stage()==stage;assert base=={n:mesh_signature(bpy.data.objects[n]) for n in names};assert facial=={n:v59.native_curves(bpy.data.objects[n]) for n in facial};raise_subdivision()
    for frame in (1,21):
        bpy.context.scene.frame_set(frame);bpy.context.view_layer.update();assert poses[frame]=={n:digest(k.mesh(bpy.data.objects[n])['V']) for n in names}
    bpy.context.scene.frame_set(1);bpy.context.view_layer.update();actual=bpy.data.objects['AFN61_SCALP_ATTACHED_PONYTAIL_FIBRES'];Q,rr=read_hair(actual);raw=np.load(g.E/'b-fibres-authoring.npz');assert np.array_equal(Q,raw['positions']) and np.array_equal(rr,raw['radii']);assert np.array_equal(np.array(actual.matrix_world),np.eye(4));assert np.isfinite(Q).all() and (rr>0).all()
    images=[]
    for im in bpy.data.images:
        if im.source=='FILE':
            p=Path(bpy.path.abspath(im.filepath));assert im.filepath.startswith('//') and p.exists();images.append(str(p))
    assert len(images)==15
    parts=[k.mesh(bpy.data.objects[n]) for n in names];V,T,mi,fi=k.join(parts);tri=V[T];tree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True)
    body=parts[4];rootTri=raw['rootTriangles'];sourcePoints=np.einsum('ij,ijk->ik',raw['rootBarycentric'],body['V'][body['T'][rootTri]]);rootError=np.linalg.norm(Q[:,0]-sourcePoints,axis=1);assert rootError.max()<1e-6
    g.save('b-reopen-functional-verification.json',{'source':str(out),'sha256':g.sha(out),'actualCurves':len(Q),'actualPoints':int(Q.size//3),'actualPolylineSegments':len(Q)*(Q.shape[1]-1),'maximumRadiusM':float(rr.max()),'originalFiveComponentsNativeKeysUVMaterialsMatrixExact':True,'originalNeutralClosedRenderPositionsExact':True,'originalNativeFacialFibresExact':True,'stageExact':True,'relativeTexturesLoaded':len(images),'actualPositionsAndRadiiMatchAuthoring':True,'maximumRestFollicleLineageErrorM':float(rootError.max()),'rootBindingScope':'Exact recorded rest render-triangle+barycentric attachment; no deforming scalp follower or physical hair rig yet.','fullCharacterOrRuntimeAcceptance':False})
    print('R61_REOPEN_FUNCTION_PASS',len(Q),time.time()-tick,flush=True)
    result=k.f.flowcheck.check(Q[:,1:],rr[:,1:],tree,tri,roots=True)
    result.update(source=str(out),sha256=g.sha(out),exactRootLineageMaximumErrorM=float(rootError.max()),anatomicalFirstSegmentsExcluded=len(Q),allOtherSegmentsTested=True,scope='Actual saved editable POLY fibre capsules against all five render-level body/optical components at neutral. Exact follicle-centre-to-first-free-point segments are anatomical root joins only. No other body region excluded.',notCertified='First follicle join thickness, hair/hair, tie/fibre, physical scalp following, head/cloth motion, continuous sweeps and runtime.',seconds=time.time()-tick)
    g.save('b-actual-fibre-contact-verification.json',result);print('R61_ACTUAL_CONTACT',result['status'],result['unqualifiedSegments'],len(result['rootFailures']),time.time()-tick,flush=True)
if __name__=='__main__':main()
