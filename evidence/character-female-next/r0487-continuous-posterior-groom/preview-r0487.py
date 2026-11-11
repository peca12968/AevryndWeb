"""Independently reopen the grooms, exercise a guide, and render the same carrier."""
from pathlib import Path
from hashlib import sha256
import json
import runpy
from time import perf_counter

import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parent
author = runpy.run_path(str(ROOT / 'author-r0487.py'))
plan = author['plan']
read_positions = author['read_positions']
set_positions = author['set_positions']
blend_roots = author['blend_roots']
position_hash = author['positions_hash']


def attribute_values(attribute):
    widths = {'FLOAT_VECTOR': 3, 'FLOAT2': 2}
    width = widths.get(attribute.data_type, 1)
    dtype = 'i4' if attribute.data_type == 'INT' else 'f4'
    values = np.empty((len(attribute.data), width), dtype=dtype)
    attribute.data.foreach_get('vector' if width > 1 else 'value', values.ravel())
    return values


def compare_binding(obj):
    return {attribute.name: sha256(attribute_values(attribute).tobytes()).hexdigest()
            for attribute in obj.data.attributes
            if attribute.name not in ('position', 'AEVRYND_SCALP_REGION', 'AEVRYND_PRIMARY_GUIDE')}


def evaluated_hash(obj):
    bpy.context.view_layer.update()
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    return position_hash(read_positions(evaluated))


def inspect_guide_operation(carrier, guide, roots, owners, weights, original):
    before = read_positions(guide)
    guide_index = 103
    moved = before.copy()
    moved[guide_index, 16:56, 1] += .003 * np.sin(np.linspace(0, np.pi, 40)).astype('f4')
    set_positions(guide, moved)
    geometry = blend_roots(roots, read_positions(guide), owners, weights)
    set_positions(carrier, geometry)
    edited = evaluated_hash(carrier)
    assert edited == position_hash(geometry) and edited != position_hash(original)
    assert np.array_equal(geometry[:, 0], roots)
    changed = np.any(geometry != original, axis=(1, 2))
    assert int(changed.sum()) > 0 and not np.any(changed & ~(owners == guide_index).any(axis=1))
    set_positions(guide, before)
    restored = blend_roots(roots, read_positions(guide), owners, weights)
    set_positions(carrier, restored)
    assert evaluated_hash(carrier) == position_hash(original)
    return dict(guideIndex=guide_index, maxGuideDisplacementMetres=.003, changedChildCurves=int(changed.sum()),
                evaluatedEditHash=edited, restoredEvaluatedHash=position_hash(restored), persisted=False)


def sample_contact(banks, skin, radii, ids):
    mesh = skin.data
    tree = BVHTree.FromPolygons([vertex.co[:] for vertex in mesh.vertices],
                               [face.vertices[:] for face in mesh.polygons], all_triangles=True)
    results = {}
    # Compare identical curve/point indices selected by the union of the anatomical windows.
    # This is a neutral vertex/point probe and does not certify swept strand segments.
    indices = np.arange(0, len(ids), 5)
    point_indices = np.arange(6, 80, 3)
    probes = {tag: positions[indices[:, None], point_indices] for tag, positions in banks.items()}
    for zone in ('ear', 'posterior'):
        union = np.zeros((len(indices), len(point_indices)), dtype=bool)
        for points in probes.values():
            x, y, z = points.transpose(2, 0, 1)
            if zone == 'ear':
                mask = (abs(x) > .054) & (y > -.045) & (y < .018) & (z > 1.408) & (z < 1.483)
            else:
                mask = (abs(x) < .022) & (y > .028) & (z > 1.34) & (z < 1.535)
            union |= mask
        rows, cols = np.nonzero(union)
        assert len(rows) > 0
        radius = radii[indices[rows], point_indices[cols]]
        results[zone] = {}
        for tag, points in probes.items():
            xyz = points[rows, cols]
            signed = np.empty(len(xyz))
            for index, point in enumerate(xyz):
                position = Vector(point)
                closest, normal, _, distance = tree.find_nearest(position)
                signed[index] = distance if (position - closest).dot(normal) >= 0 else -distance
            gap = signed - radius
            worst = int(gap.argmin())
            results[zone][tag] = dict(samples=len(xyz), negativeGapSamples=int((gap < 0).sum()),
                negativeCenterSamples=int((signed < 0).sum()), minimumSignedGapMetres=float(gap[worst]),
                worstCurveID=int(ids[indices[rows[worst]]]), worstPoint=int(point_indices[cols[worst]]),
                worstXYZMetres=xyz[worst].tolist())
    return dict(reference=skin.name, pose='archived neutral', contactCoverage='Selected points, nearest oriented triangle, signed center distance less radius. The same candidate-union point indices are compared in each region.',
                skinSegments='unverified', hairSelfContact='unverified', dynamicContinuousContact='unverified', results=results)


def main():
    proof = plan.read_json(ROOT / 'construction-receipt.json')
    source = Path(proof['source']['path'])
    assert plan.sha(source) == proof['source']['sha256']
    assert plan.sha(ROOT / 'guide-ownership.npz') == proof['ownerSHA256']
    bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False, use_scripts=False)
    scene = bpy.context.scene
    scene.render.use_persistent_data = False
    control = bpy.data.objects[proof['controlObject']]
    carrier = bpy.data.objects[proof['variants']['sweep']['object']]
    original = read_positions(control)
    roots = original[:, 0].copy()
    ownership = np.load(ROOT / 'guide-ownership.npz', allow_pickle=False)
    owners, weights = ownership['owners'], ownership['weights']
    ids = author['curve_ids'](control)
    assert np.array_equal(ids, ownership['curveIDs'])
    fields = compare_binding(control)
    banks = {'control': original}
    replay = {}
    for mode, variant in proof['variants'].items():
        obj = bpy.data.objects[variant['object']]
        guide = bpy.data.objects[variant['guideObject']]
        positions = read_positions(obj)
        assert compare_binding(obj) == fields and list(obj.data.materials) == list(control.data.materials)
        assert np.isfinite(positions).all() and np.array_equal(positions[:, 0], roots)
        assert position_hash(positions) == variant['positionHash']
        guide_positions = read_positions(guide)
        assert position_hash(guide_positions) == variant['guideHash']
        regenerated = blend_roots(roots, guide_positions, owners, weights)
        assert np.array_equal(positions, regenerated)
        banks[mode] = positions
        replay[mode] = dict(positionHash=position_hash(positions), guideHash=position_hash(guide_positions),
                            replayBitIdentical=True, shaderNames=[material.name for material in obj.data.materials])

    for obj in bpy.data.objects:
        if obj.type == 'CURVES':
            obj.hide_render = True
            obj.hide_set(True)
    carrier.hide_render = False
    carrier.hide_set(False)
    assert evaluated_hash(carrier) == proof['variants']['sweep']['positionHash']
    guide = bpy.data.objects[proof['variants']['sweep']['guideObject']]
    operation = inspect_guide_operation(carrier, guide, roots, owners, weights, banks['sweep'])
    radii = attribute_values(control.data.attributes['radius']).reshape(24831, 80)
    contact = sample_contact(banks, bpy.data.objects['R482 archived complete neutral skin'], radii, ids)
    (ROOT / 'neutral-contact-probe.json').write_text(json.dumps(contact, indent=2), encoding='utf-8')
    dependencies = dict(libraries=[library.filepath for library in bpy.data.libraries],
                        images=[image.filepath for image in bpy.data.images if image.source == 'FILE' and not image.packed_file])
    assert not any(dependencies.values())
    mesh_objects = [obj for obj in scene.objects if obj.type == 'MESH']
    for obj in mesh_objects:
        obj.data.calc_loop_triangles()
    stats = dict(sceneObjects=len(scene.objects), meshVertices=sum(len(obj.data.vertices) for obj in mesh_objects),
        meshTriangles=sum(len(obj.data.loop_triangles) for obj in mesh_objects),
        armatureBones=sum(len(obj.data.bones) for obj in scene.objects if obj.type == 'ARMATURE'),
        shapeKeys=sum(len(obj.data.shape_keys.key_blocks) - 1 for obj in mesh_objects if obj.data.shape_keys),
        materials=len(bpy.data.materials), images=len(bpy.data.images), hairCurves=24831,
        hairPoints=1986480, guidesPerVariant=proof['guideCount'])
    verification = dict(source=proof['source'], rootsBitIdentical=True, preservedAttributeHashes=fields,
        replay=replay, evaluatedOperation=operation, dependencies=dependencies, stats=stats,
        finiteCollisionStatus='UNVERIFIED', sampledContact='neutral-contact-probe.json', animation='UNVERIFIED',
        engineCPUSeconds=None, engineGPUSeconds=None, engineMemoryBytes=None)
    (ROOT / 'reopen-verification.json').write_text(json.dumps(verification, indent=2), encoding='utf-8')

    reference = plan.read_json(ROOT.parent / 'r0477-hair-shader-isolation/material-probe.json')['view']
    scene.view_settings.view_transform = reference['transform']
    scene.view_settings.look = reference['look']
    scene.view_settings.exposure = reference['exposure']
    for key, value in reference['cycles'].items():
        setattr(scene.cycles, key, value)
    renders = {}
    for view in ('face', 'rear-oblique', 'opposite-profile', 'posterior-detail', 'full-body'):
        shot = plan.read_json(ROOT.parent / f'r0470-independent-posterior-locks/shot-A-{view}.json')['shot']
        scene.camera.matrix_world = Matrix(shot['camera'])
        scene.camera.data.type = shot['cameraType']
        scene.camera.data.lens = shot['lens']
        scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = shot['resolution']
        scene.cycles.samples = shot['samples']
        scene.cycles.seed = shot['seed']
        scene.cycles.use_denoising = shot['denoising']
        for tag, bank in banks.items():
            set_positions(carrier, bank)
            bank_hash = position_hash(bank)
            assert evaluated_hash(carrier) == bank_hash
            output = ROOT / f'{tag}-{view}.png'
            assert not output.exists()
            scene.render.filepath = str(output)
            start = perf_counter()
            bpy.ops.render.render(write_still=True)
            renders[f'{tag}:{view}'] = dict(path=str(output), sha256=plan.sha(output), seconds=perf_counter()-start,
                camera=shot['camera'], lens=shot['lens'], exposure=scene.view_settings.exposure, samples=scene.cycles.samples,
                seed=scene.cycles.seed, evaluatedPositionHash=bank_hash, carrier=carrier.name)
            (ROOT / 'preview-progress.json').write_text(json.dumps(renders, indent=2), encoding='utf-8')
            print('R487_PREVIEW', tag, view, flush=True)
    assert plan.sha(source) == proof['source']['sha256']
    receipt = dict(source=proof['source'], renders=renders, sourceUnchanged=True, sameRenderCarrier=True)
    (ROOT / 'preview-receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
