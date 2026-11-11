"""Audit all evaluated neutral strand controls and recheck every signed warning."""
from pathlib import Path
import runpy
from time import perf_counter

import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
author = runpy.run_path(str(ROOT / 'author-r0490.py'))
probe = runpy.run_path(str(ROOT.parent / 'r0489-crown-attachment-flow/preview-r0489.py'))


def location(index, value, coordinates, ids):
    row, point = map(int, index)
    return dict(curveID=int(ids[row]), pointIndex=point, signedGapMetres=float(value),
                positionMetres=coordinates[row, point].tolist())


def audit(coordinates, radii, ids, tree):
    centers = np.empty(coordinates.shape[:2], dtype='f4')
    for row, curve in enumerate(coordinates):
        for index, coordinate in enumerate(curve):
            centers[row, index] = probe['signed_gap'](Vector(coordinate), tree)
    oriented = centers - radii
    row, point = np.unravel_index(oriented.argmin(), oriented.shape)
    oriented_minimum = location((row, point), oriented[row, point], coordinates, ids)
    warnings = np.argwhere(oriented < 0)
    confirmed_inside = 0
    confirmed_radius_contact = 0
    disagreed_outside = 0
    mixed = 0
    worst_confirmed = None
    parity_gap = oriented.copy()
    for row, point in warnings:
        rays = probe['ray_counts'](Vector(coordinates[row, point]), tree)
        parity = [crossings % 2 for crossings in rays]
        if all(parity):
            confirmed_inside += 1
            gap = -abs(float(centers[row, point])) - float(radii[row, point])
        elif not any(parity):
            gap = abs(float(centers[row, point])) - float(radii[row, point])
            if gap < 0:
                confirmed_radius_contact += 1
            else:
                disagreed_outside += 1
        else:
            mixed += 1
            continue
        parity_gap[row, point] = gap
        if gap < 0 and (worst_confirmed is None or gap < worst_confirmed['signedGapMetres']):
            worst_confirmed = location((row, point), gap, coordinates, ids) | dict(rayCrossings=rays)
    row, point = np.unravel_index(parity_gap.argmin(), parity_gap.shape)
    return dict(controls=int(oriented.size), negativeOrientedGap=int(len(warnings)), orientedMinimum=oriented_minimum,
        warningRecheck=dict(insideCenters=confirmed_inside, outsideRadiusOverlap=confirmed_radius_contact,
            outsideAndClear=disagreed_outside, mixedParity=mixed), worstRayCorroboratedContact=worst_confirmed,
        minimumAfterWarningRecheck=location((row, point), parity_gap[row, point], coordinates, ids))


def main():
    proof = author['read_json'](ROOT / 'construction-receipt.json')
    source = Path(proof['source']['path'])
    assert author['digest'](source) == proof['source']['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False, use_scripts=False)
    control = bpy.data.objects[proof['controlObject']]
    body = bpy.data.objects[author['BODY']]
    _, tree, _ = author['foundation']['binding_frame'](control, body, author['positions'](control)[:, 0])
    for obj in bpy.context.scene.objects:
        if obj.type == 'CURVES':
            obj.hide_set(True)
    output = ROOT / 'neutral-contact.json'
    assert not output.exists()
    report = dict(source=proof['source'], pose='archived complete neutral woman', skin=body.name,
        method='Every evaluated control on each new groom. Nearest oriented skin triangle minus stored radius, with three directed ray parity checks for each negative warning.',
        limitations=['Positive nearest-normal results were not ray-classified', 'No swept segments or hair self-contact', 'No dynamic or garment contact'],
        results={})
    for label, variant in proof['variants'].items():
        start = perf_counter()
        obj = bpy.data.objects[variant['object']]
        obj.hide_set(False)
        bpy.context.view_layer.update()
        evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
        bank = author['positions'](evaluated)
        assert author['array_hash'](bank) == variant['positionHash']
        radii = author['read_attribute'](evaluated.data, 'radius').reshape(bank.shape[:2])
        ids = author['read_attribute'](evaluated.data, 'AFN409_CURVE_ID')
        result = audit(bank, radii, ids, tree)
        result['elapsedSeconds'] = perf_counter()-start
        report['results'][label] = result
        author['write_json'](output, report)
        print('R490_NEUTRAL_POINTS', label, result, flush=True)
        obj.hide_set(True)
    assert author['digest'](source) == proof['source']['sha256']


if __name__ == '__main__':
    main()
