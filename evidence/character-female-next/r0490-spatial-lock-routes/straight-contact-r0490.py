"""Bound neutral skin clearance between controls for a swept linear strand proxy."""
from pathlib import Path
import runpy

import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
author = runpy.run_path(str(ROOT / 'author-r0490.py'))
probe = runpy.run_path(str(ROOT.parent / 'r0489-crown-attachment-flow/preview-r0489.py'))
NUMERIC_ALLOWANCE = .000002
MAX_SPLITS = 8


def leaf_bound(a, b, ga, gb, ra, rb):
    return .5 * (ga + gb - (b-a).length - abs(rb-ra)) - NUMERIC_ALLOWANCE


def verify_span(tree, a, b, ga, gb, ra, rb, depth=0):
    lower = leaf_bound(a, b, ga, gb, ra, rb)
    if lower > 0:
        return lower, 0, None
    middle = (a+b)*.5
    radius = (ra+rb)*.5
    gap = tree.find_nearest(middle)[3] - radius
    if gap <= 0 or depth == MAX_SPLITS:
        return None, 1, dict(positionMetres=list(middle), gapMetres=gap,
                             reason='contact' if gap <= 0 else 'bound_not_resolved')
    left, left_checks, issue = verify_span(tree, a, middle, ga, gap, ra, radius, depth+1)
    if issue:
        return None, left_checks+1, issue
    right, right_checks, issue = verify_span(tree, middle, b, gap, gb, radius, rb, depth+1)
    return (None if issue else min(left, right)), left_checks+right_checks+1, issue


def main():
    proof = author['read_json'](ROOT / 'construction-receipt.json')
    source = Path(proof['source']['path'])
    assert author['digest'](source) == proof['source']['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False, use_scripts=False)
    control = bpy.data.objects[proof['controlObject']]
    selected = proof['variants']['swept']
    obj = bpy.data.objects[selected['object']]
    body = bpy.data.objects[author['BODY']]
    _, tree, _ = author['foundation']['binding_frame'](control, body, author['positions'](control)[:, 0])
    for candidate in bpy.context.scene.objects:
        if candidate.type == 'CURVES':
            candidate.hide_set(candidate != obj)
    bpy.context.view_layer.update()
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    positions = author['positions'](evaluated)
    assert author['array_hash'](positions) == selected['positionHash']
    radii = author['read_attribute'](evaluated.data, 'radius').reshape(positions.shape[:2])
    ids = author['read_attribute'](evaluated.data, 'AFN409_CURVE_ID')

    gaps = np.empty(positions.shape[:2], dtype='f8')
    roots_outside = 0
    for row, path in enumerate(positions):
        roots_outside += int(not any(count % 2 for count in probe['ray_counts'](Vector(path[0]), tree)))
        for column, point in enumerate(path):
            gaps[row, column] = tree.find_nearest(Vector(point))[3] - radii[row, column]
    lengths = np.linalg.norm(positions[:, 1:].astype('f8') - positions[:, :-1], axis=2)
    slopes = np.abs(radii[:, 1:].astype('f8') - radii[:, :-1])
    bounds = .5 * (gaps[:, 1:] + gaps[:, :-1] - lengths - slopes) - NUMERIC_ALLOWANCE
    uncertain = np.argwhere(bounds <= 0)
    direct = int(bounds.size-len(uncertain))
    minimum_bound = float(bounds[bounds > 0].min())
    tests = 0
    mid_contacts = 0
    unresolved = 0
    first_failures = []
    for row, column in uncertain:
        a, b = map(Vector, positions[row, column:column+2])
        ra, rb = map(float, radii[row, column:column+2])
        bound, count, issue = verify_span(tree, a, b, gaps[row, column], gaps[row, column+1], ra, rb)
        tests += count
        if issue:
            if issue['reason'] == 'contact':
                mid_contacts += 1
            else:
                unresolved += 1
            if len(first_failures) < 12:
                first_failures.append(dict(curveID=int(ids[row]), startPointIndex=int(column), **issue))
        else:
            minimum_bound = min(minimum_bound, bound)
    result = dict(source=proof['source'], variant='swept', pose='archived complete neutral woman',
        model='Straight spans between native control points, sweeping spheres with linearly interpolated stored radii.',
        method='Lower bound from the 1-Lipschitz unsigned triangle distance and the radius change. Subdivide spans when needed.',
        numericAllowanceMetres=NUMERIC_ALLOWANCE, maximumSubdivisionDepth=MAX_SPLITS,
        controls=int(gaps.size), rootCentersWithAllEvenParity=roots_outside, rootCenters=len(ids),
        minimumEndpointGapMetres=float(gaps.min()), endpointContacts=int((gaps <= 0).sum()),
        spans=int(bounds.size), certifiedDirect=direct, certifiedAfterSubdivision=int(len(uncertain))-mid_contacts-unresolved,
        sampledMidpointContacts=mid_contacts, unresolvedSpans=unresolved, midpointQueries=tests,
        minimumLowerBoundOnCertifiedSpansMetres=minimum_bound, firstFailures=first_failures,
        limitations=['The authored or rendered interpolant can deviate from its chords', 'No hair self-contact',
                     'No garment contact or continuous motion'])
    assert author['digest'](source) == proof['source']['sha256']
    author['write_json'](ROOT / 'straight-contact.json', result)
    print('R490_STRAIGHT_CONTACT', result, flush=True)


if __name__ == '__main__':
    main()
