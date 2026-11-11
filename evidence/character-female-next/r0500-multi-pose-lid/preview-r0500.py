"""Verify the native corrective switch and render matched blink views."""
from pathlib import Path
from runpy import run_path
from time import perf_counter

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parent
stage = run_path(str(ROOT / 'author-r0500.py'))
author, previous = stage['author'], stage['previous']
read_json, write_json, digest, array_hash = (stage[key] for key in ('read_json', 'write_json', 'digest', 'array_hash'))
KEY_NAMES, MODES = (stage[key] for key in ('KEY_NAMES', 'MODES'))
activate = stage['activate']
VIEWS = (('turned-macro', 'portrait-front', 0., 1., True), ('turned-closing', 'portrait-front', 0., .92, True),
         ('closed-macro', 'portrait-front', 0., 1., True), ('closing-macro', 'portrait-front', 0., .82, True),
         ('closed-oblique', 'portrait-oblique', 32., 1., False), ('open', 'portrait-front', 0., 0., False),
         ('half-blink', 'portrait-oblique', 32., .5, False), ('closed-profile', 'portrait-profile', -82., 1., False),
         ('rear-oblique', 'rear-oblique', None, 0., False), ('full-body', 'full-body', None, 0., False))


def capture(scene, body, gaze, source, evaluation, head0, rig):
    progress = ROOT / 'preview-progress.json'
    renders = read_json(progress) if progress.exists() else {}
    for row in renders.values():
        assert row['sourceSha256'] == source['sha256'] and digest(Path(row['path'])) == row['sha256']
    recovered = len(renders)
    config = read_json(ROOT.parent / 'r0477-hair-shader-isolation/material-probe.json')['view']
    scene.view_settings.view_transform = config['transform']
    scene.view_settings.look = config['look']
    scene.view_settings.exposure = config['exposure']
    for key, value in config['cycles'].items():
        setattr(scene.cycles, key, value)
    scene.render.use_persistent_data = False
    for name, view, angle, phase, crop in VIEWS:
        for label in MODES:
            key = f'{label}:{name}'
            if key in renders:
                continue
            frame = 37. if name.startswith('turned-') else 1.
            activate(scene, gaze, label, phase, frame)
            previous['view_setup'](scene, view, angle)
            if frame == 37.:
                head = rig.matrix_world @ rig.pose.bones['Head'].matrix
                scene.camera.matrix_world = head @ head0.inverted() @ scene.camera.matrix_world
            render = scene.render
            render.use_border = render.use_crop_to_border = crop
            if crop:
                render.resolution_x = render.resolution_y = 960
                render.border_min_x, render.border_max_x = .235, .765
                render.border_min_y, render.border_max_y = (.345 if frame == 37. else .365), .565
            skin_hash = array_hash(author['evaluated'](body))
            assert skin_hash == evaluation[f'{frame:g}:{phase:g}'][label]['skinHash']
            path = ROOT / f'{label}-{name}.png'
            if path.exists():
                orphan = path.with_name(f'{path.stem}-interrupted.png')
                assert not orphan.exists()
                path.rename(orphan)
            render.filepath = str(path)
            start = perf_counter()
            bpy.ops.render.render(write_still=True)
            renders[key] = dict(sourceSha256=source['sha256'], path=str(path), sha256=digest(path),
                phase=phase, frame=scene.frame_current, camera=[list(row) for row in scene.camera.matrix_world],
                lens=scene.camera.data.lens, exposure=scene.view_settings.exposure, crop=crop,
                skinHash=skin_hash, seconds=perf_counter()-start)
            write_json(progress, renders)
            print('R500_PREVIEW', label, name, flush=True)
    return renders, recovered


def main():
    proof = read_json(ROOT / 'construction-receipt.json')
    source = Path(proof['source']['path'])
    assert digest(source) == proof['source']['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False, use_scripts=False)
    scene = bpy.context.scene
    body, gaze = (bpy.data.objects[proof[name]] for name in ('body', 'gaze'))
    hair = bpy.data.objects[proof['hair']['object']]
    assert int(gaze[proof['layoutProperty']]) == 2 and float(gaze[proof['blinkProperty']]) == 0.
    keys = body.data.shape_keys.key_blocks
    basis = author['xyz'](body.data.shape_keys.reference_key.data)
    assert array_hash(basis) == proof['basisHash']
    assert array_hash(author['mesh_winding'](body)) == proof['topologyHash']
    assert array_hash(author['xyz'](keys[previous['KEY_NAMES']['orbital']].data)) == proof['cheekCoordinateHash']
    assert keys[previous['KEY_NAMES']['orbital']].value == 1.
    assert array_hash(author['prior']['positions'](hair)) == proof['hair']['positionHash']
    layers = {name: bpy.data.objects[name] for name in previous['LAYERS']}
    masks = {}
    for mode, name in KEY_NAMES.items():
        positions = author['xyz'](keys[name].data)
        assert array_hash(positions) == proof['variants'][mode]['coordinateHash']
        masks[mode] = np.any(positions != basis, axis=1)
    evaluation = {}
    tested = [(1., p) for p in (0., .5, .82, 1.)] + [(37., p) for p in (.92, 1.)]
    for frame, phase in tested:
        activate(scene, gaze, 'control', phase, frame)
        base = author['evaluated'](body)
        layer_positions = {name: author['evaluated'](obj) for name, obj in layers.items()}
        state = dict(control=dict(skinHash=array_hash(base)))
        for mode in KEY_NAMES:
            activate(scene, gaze, mode, phase, frame)
            target = author['evaluated'](body)
            moved = np.linalg.norm(target-base, axis=1)
            assert not moved[~masks[mode]].any()
            assert bool(moved.any()) == (phase > .54)
            changes = {name: float(np.linalg.norm(author['evaluated'](obj)-layer_positions[name], axis=1).max())
                       for name, obj in layers.items()}
            state[mode] = dict(skinHash=array_hash(target), maximumPatchDisplacementMetres=float(moved.max()),
                               driverWeight=float(keys[KEY_NAMES[mode]].value), layerDeltaMetres=changes)
        evaluation[f'{frame:g}:{phase:g}'] = state

    activate(scene, gaze, 'separated', 1.)
    original = author['evaluated'](body)
    activate(scene, gaze, 'control', 1.)
    edited = author['evaluated'](body)
    activate(scene, gaze, 'separated', 1.)
    restored = author['evaluated'](body)
    assert not np.array_equal(edited, original) and np.array_equal(restored, original)
    deps = dict(libraries=[item.filepath for item in bpy.data.libraries],
        externalImages=[item.filepath for item in bpy.data.images if item.source == 'FILE' and not item.packed_file])
    assert not any(deps.values())
    meshes = [obj for obj in scene.objects if obj.type == 'MESH']
    for obj in meshes:
        obj.data.calc_loop_triangles()
    stats = dict(vertices=sum(len(obj.data.vertices) for obj in meshes), triangles=sum(len(obj.data.loop_triangles) for obj in meshes),
        bones=sum(len(obj.data.bones) for obj in scene.objects if obj.type == 'ARMATURE'),
        morphs=sum(len(obj.data.shape_keys.key_blocks)-1 for obj in meshes if obj.data.shape_keys),
        materials=len(bpy.data.materials), images=len(bpy.data.images), strands=len(hair.data.curves), hairPoints=len(hair.data.points))
    write_json(ROOT / 'reopen-verification.json', dict(source=proof['source'], evaluated=evaluation, dependencies=deps, stats=stats,
        operation=dict(property=proof['layoutProperty'], position=1., editedMode='control', restoredMode='separated',
        changedVertices=int(np.any(edited != original, axis=1).sum()), editedHash=array_hash(edited),
        restoredHash=array_hash(restored), sourceWrite=False)))
    for obj in list(scene.objects):
        if obj.type == 'CURVES' and obj != hair and obj.hide_render:
            data = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if not data.users:
                bpy.data.hair_curves.remove(data)
    activate(scene, gaze, 'control', 0., 1.)
    rig = bpy.data.objects['AFN69_BODY_CONTROLS']
    head0 = (rig.matrix_world @ rig.pose.bones['Head'].matrix).copy()
    renders, recovered = capture(scene, body, gaze, proof['source'], evaluation, head0, rig)
    assert digest(source) == proof['source']['sha256']
    write_json(ROOT / 'preview-receipt.json', dict(source=proof['source'], renders=renders, recoveredCompletedFrames=recovered, sourceUnchanged=True))


if __name__ == '__main__':
    main()
