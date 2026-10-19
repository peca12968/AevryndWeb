"""Independently reopen the portable foundation and test only stated scope."""
from pathlib import Path
import bpy,importlib.util,numpy as np,json,time,hashlib
from mathutils.bvhtree import BVHTree
sp=importlib.util.spec_from_file_location('verify57',Path(__file__).with_name('build-female-next-r0054-clump-volume.py'))
k=importlib.util.module_from_spec(sp);sp.loader.exec_module(k)
b=k.b;f=k.f;E=b.R/'Evidence/character-female-next/r0057-coherent-foundation';S=b.S
def save(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def shaarray(x):return hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()

def main():
    tick=time.time();report=json.loads((E/'d-build-summary.json').read_text());source=Path(report['output']);assert b.sha(source)==report['outputSha256']
    bpy.ops.wm.open_mainfile(filepath=str(source));body=bpy.data.objects['AFN57_CC0_COHERENT_FEMALE_BODY'];raw=np.load(E/'canonical-mesh-data.npz');data=np.load(E/'d-canonical-female-data.npz');face=np.load(E/'d-native-facial-hair.npz')
    P=np.array([v.co[:] for v in body.data.vertices],dtype='f4');F=np.array([v.co[:] for v in body.data.shape_keys.key_blocks['AFN57_Supplied_Female_Morph'].data],dtype='f4');uv=np.array([p.uv[:] for p in body.data.uv_layers['VitruvianUV.UDIM'].data],dtype='f4');corners=np.array([v for p in body.data.polygons for v in p.vertices],dtype='i4');mats=np.array([p.material_index for p in body.data.polygons],dtype='i4')
    assert np.array_equal(P,raw['canonical'].astype('f4')) and np.array_equal(F,raw['female'].astype('f4')) and np.array_equal(uv,raw['uv']) and np.array_equal(corners,raw['corners']) and np.array_equal(mats,raw['materials'])
    assert body.data.shape_keys.key_blocks['AFN57_Supplied_Female_Morph'].value==1 and np.array_equal(np.array(body.matrix_world),data['bodyMatrix'])
    facial=[]
    for label in ('lashes','brows'):
        o=bpy.data.objects['AFN57_NATIVE_'+label.upper()];counts=np.array([len(c.points) for c in o.data.curves],dtype='i4');q=np.array([p.vector[:] for p in o.data.position_data],dtype='f4');r=np.array([p.value for p in o.data.attributes['radius'].data],dtype='f4')
        assert np.array_equal(counts,face[label+'Counts']) and np.array_equal(q,face[label+'Positions']) and np.array_equal(r,face[label+'Radii']) and np.isfinite(q).all() and (r>0).all()
        facial.append({'object':o.name,'curves':len(counts),'points':len(q),'pointDataExact':True,'radiiExact':True,'worldMatrixExact':bool(np.array_equal(np.array(o.matrix_world),data['bodyMatrix']))})
    assert all(not o.particle_systems for o in bpy.context.scene.objects if o.type=='MESH')
    assert not any(m.type=='SURFACE_DEFORM' for o in bpy.context.scene.objects for m in o.modifiers)
    images=[]
    for image in bpy.data.images:
        if image.source not in ('FILE','TILED'):continue
        assert image.source=='FILE' and image.filepath.startswith('//'),('Nonportable image ID',image.name,image.source,image.filepath)
        p=Path(bpy.path.abspath(image.filepath));assert p.is_file();images.append({'name':image.name,'relativePath':image.filepath,'sha256':b.sha(p),'size':list(image.size)})
    assert len(images)==15 and not bpy.data.libraries
    hair=bpy.data.objects['AFN57_CANONICAL_BOB_GUIDES'];Q,R=f.v.hair_arrays(hair);assert np.array_equal(Q,data['hairFemale'].astype('f4'))
    # Viewport subdivision is raised only for this read-only verifier so the
    # extracted body triangles are the actual render-level geometry.
    for modifier in body.modifiers:
        if modifier.type=='SUBSURF':modifier.levels=modifier.render_levels
    bpy.context.view_layer.update();V,T=b.evaluated(body,True);tree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True);matrix=np.array(hair.matrix_world);world=Q.astype('f8')@matrix[:3,:3].T+matrix[:3,3];radius=R.astype('f8')*np.linalg.norm(matrix[:3,:3],ord=2)
    contact=f.flowcheck.check(world,radius,tree,V[T],roots=True)
    save('d-reopened-verification.json',{'source':str(source),'sourceSha256':b.sha(source),'reopened':True,'originalCanonicalTopologyBasisFemaleShapeAndUVExact':True,
        'nativeBodyVertices':len(P),'nativeBodyPolygons':len(body.data.polygons),'actualRenderBodyVertices':len(V),'actualRenderBodyTriangles':len(T),'bodyRenderPositionHash':shaarray(V),'bodyRenderTriangleHash':shaarray(T),
        'nativeFacialHair':facial,'headHairLocalPositionsExact':True,'headHairGuides':len(Q),'headHairPointsPerGuide':Q.shape[1],
        'legacyParticleSystems':0,'surfaceDeformModifiers':0,'externalLibraries':[],'requiredImages':images,
        'headHairActualFullStaticBodyCapsules':contact,'fullBodySelfFacialHairSelfTissueContactsRigDynamicsRuntime':'NOT_TESTED_NOT_ACCEPTED',
        'poseScope':'Original source A-pose, supplied female1, neutral face. Different arm rest pose from retained r51; no controlled same-pose whole-body superiority claim.',
        'seconds':time.time()-tick})
    print('R57_PORTABLE_REOPENED',len(V),len(T),contact['status'],contact['unqualifiedSegments'],len(contact['rootFailures']),time.time()-tick,flush=True)

if __name__=='__main__':main()
