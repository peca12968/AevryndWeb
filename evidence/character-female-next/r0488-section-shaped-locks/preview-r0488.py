"""Reopen and replay the authored locks, then capture matched complete views."""
from pathlib import Path
from hashlib import sha256
import json
import runpy
from time import perf_counter

import bpy
import numpy as np
from mathutils import Matrix

ROOT = Path(__file__).resolve().parent
author = runpy.run_path(str(ROOT / 'author-r0488.py'))
previous = runpy.run_path(str(ROOT.parent / 'r0487-continuous-posterior-groom/preview-r0487.py'))
read_json = author['read_json']
digest = author['digest']
read_positions = author['read_positions']
set_positions = author['set_positions']
geometry_hash = author['geometry_hash']
attribute_values = previous['attribute_values']
evaluated_hash = previous['evaluated_hash']


def write_record(name, record):
    (ROOT / name).write_bytes(json.dumps(record, indent=2).encode('utf-8'))


def fixed_attributes(obj):
    generated = {'position', 'AEVRYND_LOCK_ID', 'AEVRYND_PRIMARY_GUIDE'}
    return {attribute.name: sha256(attribute_values(attribute).tobytes()).hexdigest()
            for attribute in obj.data.attributes if attribute.name not in generated}


def verify_edit(carrier, roots, curve_ids, atlas, original, lock_ids):
    """Edit one saved station and replay it against the evaluated displayed strands."""
    property_name = 'Aevrynd_Lock_Stations'
    layout_text = carrier[property_name]
    adjusted = json.loads(layout_text)
    lock = 5
    adjusted[lock][3] += .004
    carrier[property_name] = json.dumps(adjusted)
    edited, owners = author['construct'](roots, curve_ids, json.loads(carrier[property_name]), atlas)
    assert np.array_equal(owners, lock_ids) and np.array_equal(edited[:, 0], roots)
    changed = np.any(edited != original, axis=(1, 2))
    assert int(changed.sum()) > 0 and np.all(lock_ids[changed] == lock)
    set_positions(carrier, edited)
    changed_hash = evaluated_hash(carrier)
    assert changed_hash == geometry_hash(edited) and changed_hash != geometry_hash(original)
    carrier[property_name] = layout_text
    restored, _ = author['construct'](roots, curve_ids, json.loads(carrier[property_name]), atlas)
    set_positions(carrier, restored)
    assert evaluated_hash(carrier) == geometry_hash(original)
    return dict(editedStation=lock, crestDeltaMetres=.004, changedStrands=int(changed.sum()),
                evaluatedEditHash=changed_hash, restoredHash=geometry_hash(restored), operationPersisted=False)


def main():
    proof = read_json(ROOT / 'construction-receipt.json')
    source = Path(proof['source']['path'])
    atlas_file = Path(proof['atlas']['path'])
    assert digest(source) == proof['source']['sha256'] and digest(atlas_file) == proof['atlas']['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False, use_scripts=False)
    scene = bpy.context.scene
    scene.render.use_persistent_data = False
    control = bpy.data.objects[proof['controlObject']]
    carrier = bpy.data.objects[proof['variants']['layers']['object']]
    banks = {'control': read_positions(control)}
    roots = banks['control'][:, 0].copy()
    curve_ids = author['get_curve_ids'](control)
    fields = fixed_attributes(control)
    with np.load(atlas_file, allow_pickle=False) as archive:
        atlas = tuple(archive[key] for key in ('heights', 'angles', 'radius'))
    reproduction = {}
    for name, variant in proof['variants'].items():
        obj = bpy.data.objects[variant['object']]
        positions = read_positions(obj)
        layout = json.loads(obj['Aevrynd_Lock_Stations'])
        replay, owners = author['construct'](roots, curve_ids, layout, atlas)
        stored_owners = attribute_values(obj.data.attributes['AEVRYND_LOCK_ID']).ravel()
        assert np.array_equal(replay, positions) and np.array_equal(owners, stored_owners)
        assert np.array_equal(positions[:, 0], roots) and np.isfinite(positions).all()
        assert geometry_hash(positions) == variant['positionHash'] and fixed_attributes(obj) == fields
        assert list(obj.data.materials) == list(control.data.materials)
        guide = bpy.data.objects[variant['guideObject']]
        witness_ids = attribute_values(guide.data.attributes['AEVRYND_SOURCE_CURVE_ID']).ravel()
        mapping = {int(curve_id): index for index, curve_id in enumerate(curve_ids)}
        witness_indices = [mapping[int(curve_id)] for curve_id in witness_ids]
        assert np.array_equal(read_positions(guide), positions[witness_indices])
        reproduction[name] = dict(replayBitIdentical=True, witnessCurvesVerified=len(witness_ids),
            positionHash=variant['positionHash'], materials=[material.name for material in obj.data.materials])
        banks[name] = positions

    for obj in scene.objects:
        if obj.type == 'CURVES':
            obj.hide_render = obj != carrier
            obj.hide_set(obj != carrier)
    assert evaluated_hash(carrier) == geometry_hash(banks['layers'])
    active_owners = attribute_values(carrier.data.attributes['AEVRYND_LOCK_ID']).ravel()
    operation = verify_edit(carrier, roots, curve_ids, atlas, banks['layers'], active_owners)
    dependencies = dict(libraries=[library.filepath for library in bpy.data.libraries],
                        images=[image.filepath for image in bpy.data.images if image.source == 'FILE' and not image.packed_file])
    assert not any(dependencies.values())
    meshes = [obj for obj in scene.objects if obj.type == 'MESH']
    for obj in meshes:
        obj.data.calc_loop_triangles()
    stats = dict(sceneObjects=len(scene.objects), meshVertices=sum(len(obj.data.vertices) for obj in meshes),
        meshTriangles=sum(len(obj.data.loop_triangles) for obj in meshes),
        bones=sum(len(obj.data.bones) for obj in scene.objects if obj.type == 'ARMATURE'),
        morphs=sum(len(obj.data.shape_keys.key_blocks) - 1 for obj in meshes if obj.data.shape_keys),
        materials=len(bpy.data.materials), images=len(bpy.data.images),
        curvesPerVariant=len(roots), pointsPerVariant=len(roots) * 80)
    write_record('reopen-verification.json', dict(source=proof['source'], rootHash=geometry_hash(roots),
        rootAndBindingMatch=True, fixedAttributeHashes=fields, replay=reproduction, evaluatedOperation=operation,
        dependencies=dependencies, stats=stats, engineCPUSeconds=None, engineGPUSeconds=None, engineMemoryBytes=None))

    radii = attribute_values(control.data.attributes['radius']).reshape(len(roots), 80)
    contact = previous['sample_contact'](banks, bpy.data.objects[author['BODY']], radii, curve_ids)
    write_record('neutral-contact-probe.json', contact)
    reference = read_json(ROOT.parent / 'r0477-hair-shader-isolation/material-probe.json')['view']
    scene.view_settings.view_transform = reference['transform']
    scene.view_settings.look = reference['look']
    scene.view_settings.exposure = reference['exposure']
    for key, value in reference['cycles'].items():
        setattr(scene.cycles, key, value)
    renders = {}
    for view in ('face', 'rear-oblique', 'opposite-profile', 'posterior-detail', 'full-body'):
        shot = read_json(ROOT.parent / f'r0470-independent-posterior-locks/shot-A-{view}.json')['shot']
        scene.camera.matrix_world = Matrix(shot['camera'])
        scene.camera.data.type = shot['cameraType']
        scene.camera.data.lens = shot['lens']
        scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = shot['resolution']
        scene.cycles.samples = shot['samples']
        scene.cycles.seed = shot['seed']
        scene.cycles.use_denoising = shot['denoising']
        for name, positions in banks.items():
            set_positions(carrier, positions)
            assert evaluated_hash(carrier) == geometry_hash(positions)
            output = ROOT / f'{name}-{view}.png'
            assert not output.exists()
            scene.render.filepath = str(output)
            start = perf_counter()
            bpy.ops.render.render(write_still=True)
            renders[f'{name}:{view}'] = dict(path=str(output), sha256=digest(output), seconds=perf_counter()-start,
                evaluatedPositionHash=geometry_hash(positions), camera=shot['camera'], lens=shot['lens'],
                exposure=scene.view_settings.exposure, seed=shot['seed'], samples=shot['samples'], carrier=carrier.name)
            write_record('preview-progress.json', renders)
            print('R488_PREVIEW', name, view, flush=True)
    assert digest(source) == proof['source']['sha256']
    write_record('preview-receipt.json', dict(source=proof['source'], renders=renders, sameRenderCarrier=True, sourceUnchanged=True))


if __name__ == '__main__':
    main()
