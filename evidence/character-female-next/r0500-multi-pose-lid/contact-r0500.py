"""Check changed outer-lid patches against the original rig over sampled blinks."""
from pathlib import Path
from runpy import run_path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parent
stage = run_path(str(ROOT / 'author-r0500.py'))
prior_contact = run_path(str(ROOT.parent / 'r0498-orbit-cheek/contact-r0498.py'))
author, previous = stage['author'], stage['previous']
read_json, write_json, digest = (stage[key] for key in ('read_json', 'write_json', 'digest'))
mesh_data, tree, snapshot = (prior_contact[key] for key in ('mesh_data', 'tree', 'snapshot'))
probe = run_path(str(ROOT.parent / 'r0499-lid-fold/probe-r0499.py'))


def fold_witness(scene, body):
    previous['view_setup'](scene, 'portrait-front', 0.)
    evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    rays = probe['pixels'](scene, evaluated.data)
    by_pixel = {tuple(row['pixel']): row for row in rays}
    steps = []
    for x in (204, 212, 428, 436):
        for y in (337, 342, 347):
            a, b = by_pixel[(x, y)], by_pixel[(x, y + 5)]
            angle = np.degrees(np.arccos(np.clip(np.dot(a['normal'], b['normal']), -1, 1)))
            steps.append(dict(pixel=[x, y], nextPixel=[x, y+5], angleDegrees=float(angle),
                              beforeVertices=a['vertices'], afterVertices=b['vertices']))
    return steps


def projected_witness(mesh, pairs):
    coords, triangles, polygon = mesh
    if not pairs:
        return None
    face_ids = {index for pair in pairs for index in pair}
    faces = {index: triangles[polygon == index] for index in face_ids}
    gaps = []
    for pair in pairs:
        a, b = pair
        values = [stage['best_axis'](coords[first], coords[second])[1]
                  for first in faces[a] for second in faces[b]]
        gaps.append(dict(polygons=pair, minimumSeparatingAxisProjectionMetres=min(values)))
    return dict(pairs=gaps, minimumSeparatingAxisProjectionMetres=min(row['minimumSeparatingAxisProjectionMetres'] for row in gaps))


def main():
    proof = read_json(ROOT / 'construction-receipt.json')
    source = Path(proof['source']['path'])
    assert digest(source) == proof['source']['sha256']
    old_witness = read_json(ROOT.parent / 'r0499-lid-fold/failure-witness.json')
    assert old_witness['source'] == proof['rejectedDesign']
    pairs_at_pose = {}
    for state, row in old_witness['polygonCentroids'].items():
        pose = state.rsplit(':', 1)[0]
        pairs_at_pose.setdefault(pose, set()).update(tuple(poly['id'] for poly in pair['polygons']) for pair in row['witnesses'])
    bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False, use_scripts=False)
    scene = bpy.context.scene
    body, gaze = (bpy.data.objects[proof[name]] for name in ('body', 'gaze'))
    layers = {name: bpy.data.objects[name] for name in previous['LAYERS']}
    basis = author['xyz'](body.data.shape_keys.reference_key.data)
    masks = {label: np.any(author['xyz'](body.data.shape_keys.key_blocks[name].data) != basis, axis=1)
             for label, name in stage['KEY_NAMES'].items()}
    tests = [(1., step / 24) for step in range(25)] + [(37., phase) for phase in (.5, .72, .82, .86, .905, .92, .94, .97, .985, 1.)]
    tests += [(frame, phase) for frame in (36.5, 36.75) for phase in (.86, .94, 1.)]
    progress = ROOT / 'contact-progress.json'
    recorded = read_json(progress) if progress.exists() else dict(source=proof['source'], states={})
    assert recorded['source'] == proof['source']
    states = recorded['states']
    for frame, phase in tests:
        state = f'{frame:g}:{phase:g}'
        if state in states:
            continue
        stage['activate'](scene, gaze, 'control', phase, frame)
        reference = mesh_data(body)
        witness = {'control': fold_witness(scene, body)} if frame == 1. and phase == 1. else None
        fixtures = {}
        layer_reference = {}
        for name, layer in layers.items():
            coords, triangles, polygons = mesh_data(layer)
            fixtures[name] = tree(coords, triangles), polygons
            layer_reference[name] = coords
        results = {}
        for label, mask in masks.items():
            stage['activate'](scene, gaze, label, phase, frame)
            candidate = mesh_data(body)
            if witness is not None:
                witness[label] = fold_witness(scene, body)
            assert np.array_equal(candidate[0][~mask], reference[0][~mask])
            layer_delta = {}
            candidate_fixtures = dict(fixtures)
            for name, layer in layers.items():
                coords, triangles, polygons = mesh_data(layer)
                layer_delta[name] = float(np.linalg.norm(coords-layer_reference[name], axis=1).max())
                if layer_delta[name]:
                    candidate_fixtures[name] = tree(coords, triangles), polygons
            if np.array_equal(candidate[0], reference[0]):
                assert not any(layer_delta.values())
                results[label] = dict(exactBaselineAtThisPose=True, layerDeltaMetres=layer_delta)
                continue
            old_self, old = snapshot(reference, mask, fixtures)
            new_self, new = snapshot(candidate, mask, candidate_fixtures)
            layer_results = {}
            for name in layers:
                before, after = old[name]['pairs'], new[name]['pairs']
                layer_results[name] = dict(baselinePairs=len(before), candidatePairs=len(after),
                    newPairs=sorted(after-before), removedPairs=sorted(before-after),
                    closestMovedVertex=new[name]['closestMovedVertex'])
            results[label] = dict(exactBaselineAtThisPose=False, baselineSelfPairs=len(old_self), candidateSelfPairs=len(new_self),
                newSkinSelfPairs=sorted(new_self-old_self), removedSkinSelfPairs=sorted(old_self-new_self), layers=layer_results,
                layerDeltaMetres=layer_delta, evaluatedWinding=author['triangle_metrics'](reference[0], candidate[0], reference[1]))
            if state in pairs_at_pose:
                results[label]['r499KnownPairProjections'] = projected_witness(candidate, sorted(pairs_at_pose[state]))
        states[state] = results
        if witness is not None:
            recorded['fixedFrontalNormalSteps'] = witness
        write_json(progress, recorded)
        print('R500_LID_CONTACT', state, {label: None if row['exactBaselineAtThisPose'] else (
            len(row['newSkinSelfPairs']), sum(len(layer['newPairs']) for layer in row['layers'].values()))
            for label, row in results.items()}, flush=True)
    assert digest(source) == proof['source']['sha256']
    recorded['scope'] = ('25 held blink values at frame 1, ten at frame 37 and six at frames 36.5 and 36.75. '
                         'Evaluated skin patch versus full skin and four ocular layer meshes. '
                         'New pairs use source polygon IDs. Shared-vertex self pairs are excluded. '
                         'Nearest moved vertices give unsigned point samples.')
    write_json(ROOT / 'facial-contact.json', recorded)


if __name__ == '__main__':
    main()
