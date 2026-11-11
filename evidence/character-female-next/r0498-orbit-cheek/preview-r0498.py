"""Reopen the saved facial controls and capture matched neutral and blink views."""
from math import cos, radians, sin
from pathlib import Path
from runpy import run_path
from time import perf_counter

import bpy
import numpy as np
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parent
author = run_path(str(ROOT / 'author-r0498.py'))
read_json, write_json, digest, array_hash = (author[key] for key in ('read_json', 'write_json', 'digest', 'array_hash'))
KEY_NAMES, PHASES = author['KEY_NAMES'], author['PHASES']
LAYERS = ('AFN126_ORIGINAL_Eye_Eye_0', 'AFN126_ORIGINAL_EyeScleraReflect_EyeScleraReflect_0',
          'R458 A | Full-gaze lower tear menisci', 'R461 A | Shaft relief')
VIEWS = (('portrait-front', 0., 0.), ('portrait-oblique', 32., 0.), ('portrait-profile', -82., 0.),
         ('half-blink', 32., .5), ('closed-blink', 0., 1.), ('rear-oblique', None, 0.), ('full-body', None, 0.))


def activate(scene, body, gaze, label, phase, weight=1.):
    for mode, name in KEY_NAMES.items():
        body.data.shape_keys.key_blocks[name].value = weight if label == mode else 0.
    author['blink'](scene, gaze, phase)


def view_setup(scene, name, angle):
    if angle is None:
        shot = read_json(ROOT.parent / f'r0470-independent-posterior-locks/shot-A-{name}.json')['shot']
        scene.camera.matrix_world = Matrix(shot['camera'])
        scene.camera.data.type = shot['cameraType']
        scene.camera.data.lens = shot['lens']
        scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = shot['resolution']
        scene.cycles.samples = shot['samples']
        scene.cycles.seed = shot['seed']
        scene.cycles.use_denoising = shot['denoising']
    else:
        direction = radians(angle)
        focus = Vector((0., -.082, 1.471))
        position = focus + Vector((.47 * sin(direction), -.47 * cos(direction), .019))
        rotation = (focus - position).to_track_quat('-Z', 'Y')
        scene.camera.matrix_world = Matrix.Translation(position) @ rotation.to_matrix().to_4x4()
        scene.camera.data.type = 'PERSP'
        scene.camera.data.lens = 65.
        scene.render.resolution_x = scene.render.resolution_y = 640
        scene.render.resolution_percentage = 100
        scene.cycles.samples = 20
        scene.cycles.seed = 448
        scene.cycles.use_denoising = True


def capture(scene, body, gaze, source, evaluation):
    progress = ROOT / 'preview-progress.json'
    renders = read_json(progress) if progress.exists() else {}
    if renders:
        for label, row in renders.items():
            assert row['sourceSha256'] == source['sha256'] and digest(Path(row['path'])) == row['sha256']
    render_config = read_json(ROOT.parent / 'r0477-hair-shader-isolation/material-probe.json')['view']
    scene.view_settings.view_transform = render_config['transform']
    scene.view_settings.look = render_config['look']
    scene.view_settings.exposure = render_config['exposure']
    scene.render.use_persistent_data = False
    for key, value in render_config['cycles'].items():
        setattr(scene.cycles, key, value)
    for name, angle, phase in VIEWS:
        for label in ('control', *KEY_NAMES):
            if f'{label}:{name}' in renders:
                continue
            activate(scene, body, gaze, label, phase)
            view_setup(scene, name, angle)
            current = array_hash(author['evaluated'](body))
            assert current == evaluation[str(phase)][label]['skinHash']
            path = ROOT / f'{label}-{name}.png'
            if path.exists():
                path.rename(path.with_name(f'{path.stem}-interrupted.png'))
            scene.render.filepath = str(path)
            start = perf_counter()
            bpy.ops.render.render(write_still=True)
            renders[f'{label}:{name}'] = dict(sourceSha256=source['sha256'], path=str(path), sha256=digest(path),
                view=name, blink=phase, camera=[list(row) for row in scene.camera.matrix_world], lens=scene.camera.data.lens,
                cameraType=scene.camera.data.type, exposure=scene.view_settings.exposure, samples=scene.cycles.samples,
                skinHash=current, seconds=perf_counter()-start)
            write_json(progress, renders)
            print('R498_PREVIEW', label, name, flush=True)
    return renders


def main():
    proof = read_json(ROOT / 'construction-receipt.json')
    source = Path(proof['source']['path'])
    assert digest(source) == proof['source']['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False, use_scripts=False)
    scene = bpy.context.scene
    body, gaze = (bpy.data.objects[proof[name]] for name in ('body', 'gaze'))
    scalp = bpy.data.objects[author['prior']['BODY']]
    hair = bpy.data.objects[proof['hair']['object']]
    keys = body.data.shape_keys.key_blocks
    assert not body.hide_render and not hair.hide_render and keys[KEY_NAMES['orbital']].value == 1.
    for label, name in KEY_NAMES.items():
        assert array_hash(author['xyz'](keys[name].data)) == proof['variants'][label]['coordinateHash']
        keys[name].value = 0.
    basis, _, motion, guarded, scalp_ids, _ = author['protection'](body, scene, gaze, scalp, hair)
    assert array_hash(basis) == proof['basisHash'] and array_hash(author['mesh_winding'](body)) == proof['topologyHash']
    assert array_hash(np.flatnonzero(guarded)) == proof['protectedIndexHash']
    hair_hash = array_hash(author['prior']['positions'](hair))
    assert hair_hash == proof['hair']['positionHash']
    layers = {name: bpy.data.objects[name] for name in LAYERS}
    evaluations = {}
    for phase in PHASES:
        activate(scene, body, gaze, 'control', phase)
        reference = author['evaluated'](body)
        baseline_layers = {name: author['evaluated'](obj) for name, obj in layers.items()}
        state = {'control': dict(skinHash=array_hash(reference), layerHashes={name: array_hash(value) for name, value in baseline_layers.items()})}
        for label in KEY_NAMES:
            activate(scene, body, gaze, label, phase)
            positions = author['evaluated'](body)
            distance = np.linalg.norm(positions - reference, axis=1)
            assert float(distance[guarded].max()) < 1e-7 and float(distance.max()) > .002
            layer_result = {}
            for name, obj in layers.items():
                current = author['evaluated'](obj)
                layer_result[name] = dict(hash=array_hash(current), maxChangeMetres=float(np.linalg.norm(current-baseline_layers[name], axis=1).max()))
            state[label] = dict(skinHash=array_hash(positions), maximumDeltaMetres=float(distance.max()),
                editedVertices=int(np.count_nonzero(distance)), maximumGuardedChangeMetres=float(distance[guarded].max()),
                maximumLidChangeMetres=float(distance[motion].max()), maximumScalpChangeMetres=float(distance[scalp_ids].max()), layers=layer_result)
        evaluations[str(phase)] = state

    activate(scene, body, gaze, 'orbital', 0.)
    original = author['evaluated'](body)
    activate(scene, body, gaze, 'orbital', 0., .55)
    edited = author['evaluated'](body)
    activate(scene, body, gaze, 'orbital', 0.)
    restored = author['evaluated'](body)
    assert np.count_nonzero(np.any(edited != original, axis=1)) > 500 and np.array_equal(restored, original)
    assert array_hash(author['prior']['positions'](hair)) == hair_hash
    dependencies = dict(libraries=[item.filepath for item in bpy.data.libraries],
        externalImages=[item.filepath for item in bpy.data.images if item.source == 'FILE' and not item.packed_file])
    assert not any(dependencies.values())
    meshes = [obj for obj in scene.objects if obj.type == 'MESH']
    for obj in meshes:
        obj.data.calc_loop_triangles()
    stats = dict(vertices=sum(len(obj.data.vertices) for obj in meshes), triangles=sum(len(obj.data.loop_triangles) for obj in meshes),
        bones=sum(len(obj.data.bones) for obj in scene.objects if obj.type == 'ARMATURE'),
        morphs=sum(len(obj.data.shape_keys.key_blocks)-1 for obj in meshes if obj.data.shape_keys),
        materials=len(bpy.data.materials), images=len(bpy.data.images), strands=len(hair.data.curves), hairPoints=len(hair.data.points))
    write_json(ROOT / 'reopen-verification.json', dict(source=proof['source'], evaluated=evaluations,
        dependencies=dependencies, stats=stats, activeHairPositionHash=hair_hash, operation=dict(key=KEY_NAMES['orbital'],
        temporaryWeight=.55, changedVertices=int(np.any(edited != original, axis=1).sum()), editedHash=array_hash(edited),
        restoredHash=array_hash(restored), sourceWrite=False)))
    for obj in list(scene.objects):
        if obj.type == 'CURVES' and obj != hair and obj.hide_render:
            data = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if not data.users:
                bpy.data.hair_curves.remove(data)
    renders = capture(scene, body, gaze, proof['source'], evaluations)
    assert digest(source) == proof['source']['sha256']
    write_json(ROOT / 'preview-receipt.json', dict(source=proof['source'], renders=renders, sourceUnchanged=True))


if __name__ == '__main__':
    main()
