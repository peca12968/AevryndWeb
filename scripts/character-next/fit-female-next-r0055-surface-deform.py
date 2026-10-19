"""One native whole-surface deformation of the pinned authored guide pilot.

Bind all original guide vertices to the donor skin surface with Blender's
Surface Deform. Deform that entire surface onto the target's actual skin.
This tests a coherent surface cage instead of independently transporting
each root frame or projecting every free hair point. It is not contact proof.
"""
from pathlib import Path
import bpy,importlib.util,numpy as np,json,time
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sp=importlib.util.spec_from_file_location('surface55',Path(__file__).with_name('build-female-next-r0055-authored-bob.py'))
k=importlib.util.module_from_spec(sp);sp.loader.exec_module(k)
b=k.b;f=k.f;E=k.E;SRC=b.S/'aevrynd-female-next-r0055-b-landmark-bob-registration.blend'
OUT=b.S/'aevrynd-female-next-r0055-c-surface-deformed-bob-pilot.blend'

def save(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def main():
    tick=time.time();report=json.loads((E/'b-build-summary.json').read_text());assert b.sha(SRC)==report['outputSha256']
    bpy.ops.wm.open_mainfile(filepath=str(SRC));before=f.state();original=bpy.data.objects['AFN55_CC0_AUTHORED_BOB_GUIDES']
    Q,R=f.v.hair_arrays(original);data=np.load(E/'donor-native-body.npz');T=data['headSkinTriangles'];used,inv=np.unique(T,return_inverse=True)
    scale=np.array(report['wholeHeadScale']);shift=np.array(report['wholeHeadTranslationM']);C=data['vertices'][used]*scale+shift
    mesh=bpy.data.meshes.new('AFN55_SOURCE_SKIN_BIND_CAGE');mesh.from_pydata(C.tolist(),[],inv.reshape(-1,3).tolist());mesh.update()
    cage=bpy.data.objects.new(mesh.name,mesh);bpy.context.scene.collection.objects.link(cage)
    hairmesh=bpy.data.meshes.new('AFN55_NATIVE_SURFACE_BIND_VERTICES');hairmesh.from_pydata(Q.reshape(-1,3).tolist(),[],[]);hairmesh.update()
    carrier=bpy.data.objects.new(hairmesh.name,hairmesh);bpy.context.scene.collection.objects.link(carrier)
    modifier=carrier.modifiers.new('AFN55_NATIVE_SURFACE_DEFORM','SURFACE_DEFORM');modifier.target=cage
    bpy.context.view_layer.objects.active=carrier;carrier.select_set(True)
    bpy.ops.object.surfacedeform_bind(modifier=modifier.name);assert modifier.is_bound,'Native surface binding failed'
    V,T=b.evaluated(bpy.data.objects[b.BODY],True);tree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True)
    fitted=np.array([tree.find_nearest(Vector(p))[0] for p in C],dtype='f4')
    mesh.vertices.foreach_set('co',fitted.ravel());mesh.update();bpy.context.view_layer.update()
    ev=carrier.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();P=np.array([v.co[:] for v in m.vertices],dtype='f4').reshape(Q.shape);ev.to_mesh_clear()
    assert np.isfinite(P).all();np.savez_compressed(E/'c-native-surface-deformation.npz',cageBefore=C,cageAfter=fitted,cageTriangles=inv.reshape(-1,3),positions=P,radii=R)
    d=original.data.copy();d.name='AFN55_SURFACE_DEFORMED_BOB_GUIDES';d.position_data.foreach_set('vector',P.ravel())
    ob=bpy.data.objects.new(d.name,d);bpy.context.scene.collection.objects.link(ob)
    ob['scope']='Native whole-surface deformation pilot, not individually root-frame transfer. Physical root binding, all contacts, dynamics and runtime unqualified.'
    original.hide_render=True;original.hide_set(True)
    for obj in (cage,carrier):obj.hide_render=True;obj.hide_set(True);obj['aevrynd_layer']='HIDDEN_AUTHORING_BIND_DATA_NOT_RUNTIME'
    after=f.state();assert all(after[x]==before[x] for x in ('meshes','materials','skinFields','stage'))
    assert all(after['curves'][name]==row for name,row in before['curves'].items() if name!=original.name)
    b.camera('face');bpy.context.scene.camera.data.lens=85;bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    save('c-build-summary.json',{'source':str(SRC),'sourceSha256':b.sha(SRC),'output':str(OUT),'outputSha256':b.sha(OUT),
        'method':'Native whole-head Surface Deform binding; target cage fit to actual body. No child interpolation, root-frame transport or old hair route.',
        'bound':bool(modifier.is_bound),'cageVertices':len(C),'cageTriangles':len(inv)//3,'guideCount':len(P),'pointsPerGuide':P.shape[1],
        'nativePositionsExact':bool(np.array_equal(P,f.v.hair_arrays(ob)[0])),'originalBodyAndOtherVisibleMeshesSkinStageUnchanged':True,
        'rootBinding':'NOT_YET_BODY_BARYCENTRIC_BOUND','contact':'PENDING_ACTUAL_FINITE_CAPSULE_TEST'})
    f.E=E;f.render('c-actual-fibres',('face','oblique','profile'));k.k.k.k.k.a.i.ch.review.extras('c-actual-fibres',E)
    d.attributes['radius'].data.foreach_set('value',np.full_like(R,.0005).ravel());bpy.context.view_layer.update()
    f.render('c-path-diagnostic',('face','oblique','profile'));k.k.k.k.k.a.i.ch.review.extras('c-path-diagnostic',E)
    d.attributes['radius'].data.foreach_set('value',R.ravel());bpy.context.view_layer.update()
    contact=f.flowcheck.check(P.astype('f8'),R.astype('f8'),tree,V[T],roots=True);save('c-static-body-capsules.json',contact)
    print('R55_SURFACE_PILOT_READY',contact['status'],contact['unqualifiedSegments'],time.time()-tick,flush=True)

if __name__=='__main__':main()
