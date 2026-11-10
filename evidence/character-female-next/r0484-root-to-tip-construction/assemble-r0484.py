"""Selectively recover the actual current woman and original spatial hair reference."""
from pathlib import Path
from runpy import run_path
from hashlib import file_digest,sha256
import json
import numpy as np
import bpy
from mathutils import Matrix
ROOT=Path(__file__).resolve().parent
R480=ROOT.parent/'r0480-lock-clearance-projection'
R482=ROOT.parent/'r0482-global-groom-separation'
DEST=ROOT/'female-next-r0484-current-woman-construction-base-UNACCEPTED.blend'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return file_digest(f,'sha256').hexdigest()

def main():
    assert not DEST.exists()
    proof=read(R480/'source-receipt.json');mapping=read(ROOT/'actual-component-map.json')
    assert sha(Path(proof['source']['path']))==proof['source']['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(R482/'female-next-r0482-global-groom-UNACCEPTED.blend'),load_ui=False,use_scripts=False)
    scene=bpy.context.scene
    for tag in ('base','A'):
        bpy.data.objects.remove(bpy.data.objects[f'R482 complete groom | {tag}'],do_unlink=True)
    hair=bpy.data.objects['R482 complete groom | B'];hair.name='R484 complete hair | control'
    hair.hide_render=False;hair.hide_set(False)
    fixture=bpy.data.objects['R482 archived complete neutral skin'];fixture.hide_render=True;fixture.hide_set(True)
    for o in list(scene.objects):
        if o.type in ('LIGHT','CAMERA'):bpy.data.objects.remove(o,do_unlink=True)
    wanted=[mapping['names'][k] for k in ('skin','eye','cornea','gaze')]+[mapping['rig'],mapping['wet']['A'],mapping['lashes']['A'],
        'AFN126_ORIGINAL_Hair_Hair_0','Aevrynd Key','Aevrynd Fill','Aevrynd Rim','Aevrynd R976 Review Camera']
    with bpy.data.libraries.load(proof['source']['path'],link=False) as (source,target):
        assert all(n in source.objects for n in wanted)
        target.objects=wanted;world_names=list(source.worlds);target.worlds=world_names
    loaded=list(target.objects)
    for obj in list(bpy.data.objects):
        if obj not in scene.objects.values() and (obj in loaded or obj.type in ('EMPTY','ARMATURE')):
            scene.collection.objects.link(obj)
    reference=bpy.data.objects['AFN126_ORIGINAL_Hair_Hair_0'];reference.hide_render=True;reference.hide_set(True)
    visible=[mapping['names'][k] for k in ('skin','eye','cornea')]+[mapping['wet']['A'],mapping['lashes']['A']]
    for name in visible:
        obj=bpy.data.objects[name];obj.hide_render=False;obj.hide_set(False)
    assert len(target.worlds)==1,world_names
    scene.world=target.worlds[0]
    scene.camera=bpy.data.objects['Aevrynd R976 Review Camera']
    scene.frame_set(1);scene.render.threads_mode='FIXED';scene.render.threads=4
    a=run_path(str(R480/'author-r0480.py'));skin=bpy.data.objects[mapping['names']['skin']]
    evaluated=a['probe']['u'].evaluated(skin)
    stamps=[a['groom'].arr_sha(v) for v in evaluated]
    expected=read(R480/'render-B-face.json')['skinStamp']
    assert stamps==expected,(stamps,expected)
    mesh=reference.data
    v=np.empty((len(mesh.vertices),3),dtype='f4');mesh.vertices.foreach_get('co',v.ravel())
    w=np.asarray(reference.matrix_world,dtype='f8');world=v@w[:3,:3].T+w[:3,3]
    triangles=np.asarray([p.vertices[:] for p in mesh.polygons],dtype='i4')
    original=np.load(ROOT/'reference/AFN126_ORIGINAL_Hair_Hair_0-original-geometry.npz',allow_pickle=False)
    assert world.shape==original['world'].shape
    error=float(np.linalg.norm(world-original['world'],axis=1).max()*1000.)
    assert error<.001,error
    mesh.calc_loop_triangles();uv=mesh.uv_layers.active
    uv_values=np.empty((len(uv.data),2),dtype='f4');uv.data.foreach_get('uv',uv_values.ravel())
    loop_ids=np.asarray([p.loop_indices[:] for p in mesh.polygons],dtype='i4')
    np.savez_compressed(ROOT/'same-woman-reference-hair.npz',world=world.astype('f4'),triangles=triangles,
        uv=uv_values[loop_ids],worldMatrix=w)
    # Keep the original mesh as an explicitly hidden reference, never as a covering layer.
    bpy.ops.wm.save_as_mainfile(filepath=str(DEST),compress=True,copy=True)
    record=dict(source=dict(path=str(DEST),bytes=DEST.stat().st_size,sha256=sha(DEST)),parent=proof['source'],
        completeSkinHashesExactlyMatchR480=stamps,visibleComponents=visible,
        sceneObjects=[dict(name=o.name,type=o.type,hideRender=o.hide_render) for o in scene.objects],
        originalHairReferenceMaxWorldErrorMm=error,referenceVertices=len(v),referenceTriangles=len(triangles),
        world=scene.world.name,meshReferenceNotRendered=True,geometryOrMaterialPromotion=False)
    (ROOT/'assembled-source-receipt.json').write_bytes(json.dumps(record,indent=2).encode('utf8'))
    print(json.dumps(record,indent=2),flush=True)

if __name__=='__main__':main()
