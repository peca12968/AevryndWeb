"""Exercise the editable Blender routes and render the same evaluated carrier."""
from pathlib import Path
import runpy
from time import perf_counter

import bpy
import numpy as np
from mathutils import Matrix

ROOT = Path(__file__).resolve().parent
author = runpy.run_path(str(ROOT / 'author-r0494.py'))
reference = runpy.run_path(str(ROOT.parent / 'r0489-crown-attachment-flow/preview-r0489.py'))
read_json = author['read_json']
write_json = author['write_json']
digest = author['digest']
positions = author['positions']
set_positions = author['set_positions']
array_hash = author['array_hash']
read_attribute = author['read_attribute']
evaluated_hash = reference['evaluated_hash']
generate = author['generate']


def fixed_fields(data):
    generated = {'position', 'AEVRYND_PINNA_PART_WEIGHT', 'AEVRYND_PINNA_PART_JOIN', 'AEVRYND_PINNA_PART_GROUP'}
    return {attr.name: array_hash(read_attribute(data, attr.name)) for attr in data.attributes if attr.name not in generated}


def render_views(scene, carrier, banks, recovered=None):
    view = read_json(ROOT.parent / 'r0477-hair-shader-isolation/material-probe.json')['view']
    scene.view_settings.view_transform = view['transform']
    scene.view_settings.look = view['look']
    scene.view_settings.exposure = view['exposure']
    scene.render.use_persistent_data = False
    for key, value in view['cycles'].items():
        setattr(scene.cycles, key, value)
    renders = {} if recovered is None else dict(recovered)
    for angle in ('opposite-profile', 'mirror-profile', 'face', 'rear-oblique', 'posterior-detail', 'full-body'):
        source_angle = 'opposite-profile' if angle == 'mirror-profile' else angle
        shot = read_json(ROOT.parent / f'r0470-independent-posterior-locks/shot-A-{source_angle}.json')['shot']
        camera = Matrix(shot['camera'])
        if angle == 'mirror-profile':
            mirror_x = Matrix.Diagonal((-1, 1, 1, 1))
            camera = mirror_x @ camera @ mirror_x
        scene.camera.matrix_world = camera
        scene.camera.data.type = shot['cameraType']
        scene.camera.data.lens = shot['lens']
        scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = shot['resolution']
        scene.cycles.samples = shot['samples']
        scene.cycles.seed = shot['seed']
        scene.cycles.use_denoising = shot['denoising']
        for label, bank in banks.items():
            key = f'{label}:{angle}'
            if key in renders:
                continue
            set_positions(carrier, bank)
            current = evaluated_hash(carrier)
            assert current == array_hash(bank)
            output = ROOT / f'{label}-{angle}.png'
            assert not output.exists()
            scene.render.filepath = str(output)
            start = perf_counter()
            bpy.ops.render.render(write_still=True)
            renders[key] = dict(path=str(output), sha256=digest(output), seconds=perf_counter()-start,
                evaluatedPositionHash=current, camera=[list(row) for row in camera], lens=shot['lens'], exposure=view['exposure'],
                seed=shot['seed'], samples=shot['samples'], carrier=carrier.name)
            write_json(ROOT / 'preview-progress.json', renders)
            print('R494_PREVIEW', label, angle, flush=True)
    return renders


def remove_hidden_banks(scene, carrier):
    # Retain only the same visible carrier in this temporary rendering process.
    for obj in list(scene.objects):
        if obj.type == 'CURVES' and obj != carrier:
            assert obj.hide_render
            data = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if not data.users:
                bpy.data.hair_curves.remove(data)


def resume_missing():
    construction = read_json(ROOT / 'construction-receipt.json')
    source = Path(construction['source']['path'])
    proof = read_json(ROOT / 'reopen-verification.json')
    assert digest(source) == construction['source']['sha256'] == proof['source']['sha256']
    assert (ROOT / 'crown-contact.json').is_file()
    bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False, use_scripts=False)
    scene = bpy.context.scene
    control = bpy.data.objects[construction['controlObject']]
    carrier = bpy.data.objects[construction['variants']['tuck']['object']]
    banks = {'control': positions(control)}
    assert array_hash(banks['control']) == construction['controlPositionHash']
    for label, info in construction['variants'].items():
        banks[label] = positions(bpy.data.objects[info['object']])
        assert array_hash(banks[label]) == info['positionHash']
    remove_hidden_banks(scene, carrier)
    recovered = read_json(ROOT / 'preview-progress.json')
    assert recovered
    for key, row in recovered.items():
        label, _ = key.split(':', 1)
        assert row['evaluatedPositionHash'] == array_hash(banks[label])
        assert digest(Path(row['path'])) == row['sha256']
    renders = render_views(scene, carrier, banks, recovered)
    assert digest(source) == construction['source']['sha256']
    write_json(ROOT / 'preview-receipt.json', dict(source=construction['source'], renders=renders,
        sameRenderCarrier=True, sourceUnchanged=True, recoveredCompletedFrames=len(recovered)))


def main():
    construction = read_json(ROOT / 'construction-receipt.json')
    source = Path(construction['source']['path'])
    assert digest(source) == construction['source']['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False, use_scripts=False)
    scene = bpy.context.scene
    control = bpy.data.objects[construction['controlObject']]
    carrier = bpy.data.objects[construction['variants']['tuck']['object']]
    base = positions(control)
    assert array_hash(base) == construction['controlPositionHash']
    assert author['measure_ears'](bpy.data.objects[author['BODY']]) == construction['pinnae']
    normals, tree, error = author['foundation']['binding_frame'](control, bpy.data.objects[author['BODY']], base[:, 0])
    ids = read_attribute(control.data, 'AFN409_CURVE_ID')
    radii = read_attribute(control.data, 'radius').reshape(len(base), 80)
    owner = read_attribute(control.data, 'AEVRYND_SPATIAL_LOCK_ID')
    fixed = fixed_fields(control.data)
    banks = {'control': base}
    replay = {}
    for label, info in construction['variants'].items():
        obj = bpy.data.objects[info['object']]
        guide = bpy.data.objects[info['guideObject']]
        assert obj['Aevrynd_Guide_Object'] == guide.name
        bank, weight, join, groups, _ = generate(base, normals, ids, radii, owner, tree, guide)
        assert np.array_equal(bank, positions(obj)) and array_hash(bank) == info['positionHash']
        assert np.array_equal(weight, read_attribute(obj.data, 'AEVRYND_PINNA_PART_WEIGHT')) and array_hash(weight) == info['weightHash']
        assert np.array_equal(join, read_attribute(obj.data, 'AEVRYND_PINNA_PART_JOIN')) and array_hash(join) == info['joinHash']
        assert np.array_equal(groups, read_attribute(obj.data, 'AEVRYND_PINNA_PART_GROUP')) and array_hash(groups) == info['groupHash']
        assert fixed_fields(obj.data) == fixed and list(obj.data.materials) == list(control.data.materials)
        assert obj.data.surface == control.data.surface
        banks[label] = bank
        replay[label] = dict(positionHash=array_hash(bank), ownershipHash=array_hash(owner), exact=True)

    for obj in scene.objects:
        if obj.type == 'CURVES':
            obj.hide_render = obj != carrier
            obj.hide_set(obj != carrier)
    assert evaluated_hash(carrier) == array_hash(banks['tuck'])
    guide = bpy.data.objects[construction['variants']['tuck']['guideObject']]
    slot = 5
    point = guide.data.splines[slot].points[2]
    original = point.co.copy()
    point.co.y += .005
    edited, edit_weight, _, edit_groups, _ = generate(base, normals, ids, radii, owner, tree, guide)
    set_positions(carrier, edited)
    after = evaluated_hash(carrier)
    changed = np.any(edited != banks['tuck'], axis=(1, 2))
    assert after == array_hash(edited) and changed.any() and np.all(edit_weight[changed] > 0) and np.all(edit_groups[changed] == 1)
    point.co = original
    restored, _, _, _, _ = generate(base, normals, ids, radii, owner, tree, guide)
    assert np.array_equal(restored, banks['tuck'])
    set_positions(carrier, restored)
    restored_hash = evaluated_hash(carrier)
    assert restored_hash == array_hash(banks['tuck'])
    del edited, restored

    deps = dict(libraries=[item.filepath for item in bpy.data.libraries],
                externalImages=[item.filepath for item in bpy.data.images if item.source == 'FILE' and not item.packed_file])
    assert not any(deps.values())
    meshes = [obj for obj in scene.objects if obj.type == 'MESH']
    for obj in meshes:
        obj.data.calc_loop_triangles()
    stats = dict(sceneObjects=len(scene.objects), vertices=sum(len(obj.data.vertices) for obj in meshes),
        triangles=sum(len(obj.data.loop_triangles) for obj in meshes),
        bones=sum(len(obj.data.bones) for obj in scene.objects if obj.type == 'ARMATURE'),
        morphs=sum(len(obj.data.shape_keys.key_blocks)-1 for obj in meshes if obj.data.shape_keys),
        materials=len(bpy.data.materials), images=len(bpy.data.images), strands=len(base), points=len(base)*80)
    write_json(ROOT / 'reopen-verification.json', dict(source=construction['source'], replay=replay,
        fixedAttributeHashes=fixed, bindingMaximumErrorMetres=error, dependencies=deps, stats=stats,
        operation=dict(guide=guide.name, routeIndex=slot, stationIndex=2, offsetYMetres=.005,
            changedStrands=int(changed.sum()), affectedOwnerSlots=np.unique(owner[changed]).tolist(), evaluatedEditHash=after, restoredHash=restored_hash, sourceWrite=False)))
    write_json(ROOT / 'crown-contact.json', reference['crown_contact'](banks, radii, ids, tree, 10))
    remove_hidden_banks(scene, carrier)
    renders = render_views(scene, carrier, banks)
    assert digest(source) == construction['source']['sha256']
    write_json(ROOT / 'preview-receipt.json', dict(source=construction['source'], renders=renders,
        sameRenderCarrier=True, sourceUnchanged=True))


if __name__ == '__main__':
    import os

    if os.environ.get('AEVRYND_R494_RESUME') == '1':
        resume_missing()
    else:
        main()
