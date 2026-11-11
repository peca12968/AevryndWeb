"""Replay the saved grooms, audit the crown controls and capture fixed views."""
from pathlib import Path
import json
import runpy
from time import perf_counter

import bpy
import numpy as np
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parent
author = runpy.run_path(str(ROOT / 'author-r0489.py'))
read_json = author['read_json']
write_json = author['write_json']
digest = author['digest']
positions = author['positions']
array_hash = author['array_hash']
read_attribute = author['read_attribute']
set_positions = author['set_positions']
create_bank = author['create_bank']


def evaluated_hash(obj):
    bpy.context.view_layer.update()
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    return array_hash(positions(evaluated))


def fixed_fields(data):
    return {attr.name: array_hash(read_attribute(data, attr.name)) for attr in data.attributes
            if attr.name not in ('position', 'AEVRYND_CROWN_JOIN_POINT')}


def signed_gap(point, tree):
    nearest, normal, _, distance = tree.find_nearest(point)
    return distance if (point - nearest).dot(normal) >= 0 else -distance


def ray_counts(point, tree):
    result = []
    for axis in ((.34, .91, .23), (-.37, .19, .91), (.81, -.49, .33)):
        direction = Vector(axis).normalized()
        origin = point.copy()
        crossings = 0
        for _ in range(32):
            hit, _, _, _ = tree.ray_cast(origin, direction, .75)
            if hit is None:
                break
            crossings += 1
            origin = hit + direction * .000002
        result.append(crossings)
    return result


def crown_contact(banks, radii, ids, tree, end):
    result = {}
    known = int(np.flatnonzero(ids == 5535)[0])
    for label, bank in banks.items():
        gap = np.empty((len(bank), end), dtype='f4')
        for row, curve in enumerate(bank):
            for index in range(end):
                gap[row, index] = signed_gap(Vector(curve[index]), tree) - radii[row, index]
        windows = {}
        for name, first, last in (('root', 0, 1), ('firstFiveAfterRoot', 1, 6), ('laterUpperControls', 6, end)):
            section = gap[:, first:last]
            row, point = np.unravel_index(section.argmin(), section.shape)
            point += first
            negative = section < 0
            windows[name] = dict(samples=int(section.size), negativeRadiusAdjustedGap=int(negative.sum()),
                minimumSignedGapMetres=float(gap[row, point]), worstCurveID=int(ids[row]), worstPointIndex=int(point),
                worstPositionMetres=bank[row, point].tolist(), worstCenterRayCrossings=ray_counts(Vector(bank[row, point]), tree))
        result[label] = dict(windows=windows, curve5535=[dict(pointIndex=index, signedGapMetres=float(gap[known, index]),
            centerRayCrossings=ray_counts(Vector(bank[known, index]), tree)) for index in range(6)])
        print('R489_CONTACT', label, windows['firstFiveAfterRoot'], flush=True)
    return dict(pose='archived complete neutral woman', model='actual neutral skin BVH',
                scope=f'All 24,831 strands at control indices 0 through {end-1}. Nearest oriented triangle minus stored radius. Independent rays at the minimum and curve 5535.',
                unverified=['swept curve segments', 'hair self-contact', 'free lengths beyond sampled controls', 'dynamic and clothing contact'], results=result)


def main():
    construction = read_json(ROOT / 'construction-receipt.json')
    source = Path(construction['source']['path'])
    assert digest(source) == construction['source']['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False, use_scripts=False)
    scene = bpy.context.scene
    control = bpy.data.objects[construction['controlObject']]
    carrier = bpy.data.objects[construction['variants']['sweep']['object']]
    base = positions(control)
    assert array_hash(base) == construction['controlPositionHash']
    normals, tree, binding_error = author['binding_frame'](control, bpy.data.objects[author['BODY']], base[:, 0])
    fixed = fixed_fields(control.data)
    lock_ids = read_attribute(control.data, 'AEVRYND_LOCK_ID')
    radii = read_attribute(control.data, 'radius').reshape(len(base), 80)
    ids = read_attribute(control.data, 'AFN409_CURVE_ID')
    settings_key = 'Aevrynd_Crown_Departure_Settings'
    banks = {'control': base}
    replay = {}
    for label, info in construction['variants'].items():
        obj = bpy.data.objects[info['object']]
        data, join, _ = create_bank(base, normals, lock_ids, radii, tree, json.loads(obj[settings_key]))
        assert np.array_equal(data, positions(obj)) and array_hash(data) == info['positionHash']
        assert np.array_equal(join, read_attribute(obj.data, 'AEVRYND_CROWN_JOIN_POINT'))
        assert fixed_fields(obj.data) == fixed and list(obj.data.materials) == list(control.data.materials)
        banks[label] = data
        replay[label] = dict(positionHash=info['positionHash'], joinHash=array_hash(join), exact=True)
    for obj in scene.objects:
        if obj.type == 'CURVES':
            obj.hide_set(obj != carrier)
            obj.hide_render = obj != carrier
    assert evaluated_hash(carrier) == array_hash(banks['sweep'])

    original_settings = carrier[settings_key]
    trial_settings = json.loads(original_settings)
    trial_settings['crest'] += .002
    carrier[settings_key] = json.dumps(trial_settings)
    edited, _, _ = create_bank(base, normals, lock_ids, radii, tree, json.loads(carrier[settings_key]))
    set_positions(carrier, edited)
    edited_hash = evaluated_hash(carrier)
    assert edited_hash == array_hash(edited) and edited_hash != array_hash(banks['sweep'])
    assert np.array_equal(edited[:, 0], base[:, 0])
    carrier[settings_key] = original_settings
    set_positions(carrier, banks['sweep'])
    restored = evaluated_hash(carrier)
    assert restored == array_hash(banks['sweep'])
    deps = dict(libraries=[item.filepath for item in bpy.data.libraries],
                externalImages=[item.filepath for item in bpy.data.images if item.source == 'FILE' and not item.packed_file])
    assert not any(deps.values())
    meshes = [obj for obj in scene.objects if obj.type == 'MESH']
    for obj in meshes:
        obj.data.calc_loop_triangles()
    stats = dict(sceneObjects=len(scene.objects), vertices=sum(len(obj.data.vertices) for obj in meshes),
        triangles=sum(len(obj.data.loop_triangles) for obj in meshes),
        bones=sum(len(obj.data.bones) for obj in scene.objects if obj.type == 'ARMATURE'),
        morphs=sum(len(obj.data.shape_keys.key_blocks) - 1 for obj in meshes if obj.data.shape_keys),
        materials=len(bpy.data.materials), images=len(bpy.data.images), strands=len(base), points=len(base)*80)
    write_json(ROOT / 'reopen-verification.json', dict(source=construction['source'], replay=replay,
        fixedAttributeHashes=fixed, bindingMaximumErrorMetres=binding_error, dependencies=deps, stats=stats,
        operation=dict(crestDeltaMetres=.002, evaluatedEditHash=edited_hash, restoredHash=restored,
            changedStrands=int(np.any(edited != banks['sweep'], axis=(1, 2)).sum()), sourceWrite=False)))
    del edited
    end = max(row['joinRange'][1] for row in construction['variants'].values()) + 1
    write_json(ROOT / 'crown-contact.json', crown_contact(banks, radii, ids, tree, end))

    view = read_json(ROOT.parent / 'r0477-hair-shader-isolation/material-probe.json')['view']
    scene.view_settings.view_transform = view['transform']
    scene.view_settings.look = view['look']
    scene.view_settings.exposure = view['exposure']
    scene.render.use_persistent_data = False
    for key, value in view['cycles'].items():
        setattr(scene.cycles, key, value)
    renders = {}
    for angle in ('face', 'rear-oblique', 'opposite-profile', 'posterior-detail', 'full-body'):
        shot = read_json(ROOT.parent / f'r0470-independent-posterior-locks/shot-A-{angle}.json')['shot']
        scene.camera.matrix_world = Matrix(shot['camera'])
        scene.camera.data.type = shot['cameraType']
        scene.camera.data.lens = shot['lens']
        scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = shot['resolution']
        scene.cycles.samples = shot['samples']
        scene.cycles.seed = shot['seed']
        scene.cycles.use_denoising = shot['denoising']
        for label, bank in banks.items():
            set_positions(carrier, bank)
            current = evaluated_hash(carrier)
            assert current == array_hash(bank)
            output = ROOT / f'{label}-{angle}.png'
            assert not output.exists()
            scene.render.filepath = str(output)
            start = perf_counter()
            bpy.ops.render.render(write_still=True)
            renders[f'{label}:{angle}'] = dict(path=str(output), sha256=digest(output), seconds=perf_counter()-start,
                evaluatedPositionHash=current, camera=shot['camera'], lens=shot['lens'], exposure=view['exposure'],
                seed=shot['seed'], samples=shot['samples'], carrier=carrier.name)
            print('R489_PREVIEW', label, angle, flush=True)
    assert digest(source) == construction['source']['sha256']
    write_json(ROOT / 'preview-receipt.json', dict(source=construction['source'], renders=renders,
        sameRenderCarrier=True, sourceUnchanged=True))


if __name__ == '__main__':
    main()
