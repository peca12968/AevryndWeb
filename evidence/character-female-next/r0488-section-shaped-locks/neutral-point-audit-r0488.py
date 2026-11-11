"""Check every saved curve point against the complete neutral skin mesh."""
from pathlib import Path
import json
import runpy
from time import perf_counter

import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
author = runpy.run_path(str(ROOT / 'author-r0488.py'))


def summarize(gaps, centers, positions, ids, first, last):
    window = gaps[:, first:last]
    deepest = np.unravel_index(window.argmin(), window.shape)
    curve, relative_point = map(int, deepest)
    point = first + relative_point
    negative = window < 0
    return dict(points=int(window.size), negativeRadiusAdjustedGap=int(negative.sum()),
                negativeCenterGap=int((centers[:, first:last] < 0).sum()),
                curvesWithNegativeGap=int(negative.any(axis=1).sum()),
                minimumSignedGapMetres=float(gaps[curve, point]),
                worstCurveID=int(ids[curve]), worstPointIndex=point,
                worstPositionMetres=positions[curve, point].tolist())


def main():
    proof = author['read_json'](ROOT / 'construction-receipt.json')
    source = Path(proof['source']['path'])
    assert author['digest'](source) == proof['source']['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False, use_scripts=False)
    fixture = bpy.data.objects[author['BODY']]
    tree = author['skin_tree'](fixture)
    # Evaluate one groom at a time to keep only that groom in the viewport dependency graph.
    for obj in bpy.context.scene.objects:
        if obj.type == 'CURVES':
            obj.hide_set(True)
    report = dict(source=proof['source'], pose='archived complete neutral woman', skin=fixture.name,
                  method='Every evaluated hair control point, nearest oriented skin triangle, signed center distance less stored strand radius.',
                  scope='Includes bound root, first five points after root, and all remaining points as separate windows.',
                  unverified=['complete swept curve segments', 'hair self-contact', 'dynamic contact', 'clothing contact'],
                  results={})
    output = ROOT / 'all-neutral-point-contact.json'
    assert not output.exists()
    for name, variant in proof['variants'].items():
        start = perf_counter()
        obj = bpy.data.objects[variant['object']]
        obj.hide_set(False)
        bpy.context.view_layer.update()
        evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
        positions = author['read_positions'](evaluated)
        assert author['geometry_hash'](positions) == variant['positionHash']
        ids = author['get_curve_ids'](evaluated)
        radii = np.empty(positions.shape[:2], dtype='f4')
        evaluated.data.attributes['radius'].data.foreach_get('value', radii.ravel())
        distances = np.empty(positions.shape[:2], dtype='f4')
        for index, row in enumerate(positions):
            for point, coordinates in enumerate(row):
                position = Vector(coordinates)
                closest, normal, _, distance = tree.find_nearest(position)
                sign = 1 if (position - closest).dot(normal) >= 0 else -1
                distances[index, point] = distance * sign
            if index and index % 5000 == 0:
                print('R488_ALL_POINTS', name, index, len(positions), flush=True)
        gaps = distances - radii
        report['results'][name] = dict(all=summarize(gaps, distances, positions, ids, 0, 80),
            boundRoots=summarize(gaps, distances, positions, ids, 0, 1),
            firstFiveAfterRoot=summarize(gaps, distances, positions, ids, 1, 6),
            freePoints=summarize(gaps, distances, positions, ids, 6, 80),
            elapsedSeconds=perf_counter()-start)
        output.write_bytes(json.dumps(report, indent=2).encode('utf-8'))
        print('R488_ALL_POINTS_FINISHED', name, report['results'][name]['all'], flush=True)
        obj.hide_set(True)
    assert author['digest'](source) == proof['source']['sha256']


if __name__ == '__main__':
    main()
