"""Recheck the deepest departure and free-length findings against the mesh."""
from pathlib import Path
import json
import runpy

import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
author = runpy.run_path(str(ROOT / 'author-r0488.py'))


def ray_crossings(tree, origin, direction):
    cursor = origin.copy()
    count = 0
    while count < 32:
        hit, _, _, _ = tree.ray_cast(cursor, direction, .75)
        if hit is None:
            return count
        count += 1
        cursor = hit + direction * .000002
    raise RuntimeError('Too many surface intersections')


def main():
    proof = author['read_json'](ROOT / 'construction-receipt.json')
    audit = author['read_json'](ROOT / 'all-neutral-point-contact.json')
    source = Path(proof['source']['path'])
    assert author['digest'](source) == proof['source']['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False, use_scripts=False)
    tree = author['skin_tree'](bpy.data.objects[author['BODY']])
    with np.load(proof['atlas']['path'], allow_pickle=False) as data:
        atlas = tuple(data[key] for key in ('heights', 'angles', 'radius'))
    directions = [Vector(value).normalized() for value in ((.34,.91,.23), (-.37,.19,.91), (.81,-.49,.33))]
    findings = {}
    center_y = author['CENTER_Y']
    for mode, variant in proof['variants'].items():
        obj = bpy.data.objects[variant['object']]
        points = author['read_positions'](obj)
        assert author['geometry_hash'](points) == variant['positionHash']
        ids = author['get_curve_ids'](obj)
        findings[mode] = {}
        for domain in ('firstFiveAfterRoot', 'freePoints'):
            previous = audit['results'][mode][domain]
            index = int(np.flatnonzero(ids == previous['worstCurveID'])[0])
            point_index = previous['worstPointIndex']
            point = Vector(points[index, point_index])
            hit, normal, triangle, distance = tree.find_nearest(point)
            ray_counts = [ray_crossings(tree, point, direction) for direction in directions]
            radius = float(np.hypot(point.x, point.y - center_y))
            azimuth = float(np.arctan2(point.x, point.y - center_y))
            radial = Vector((np.sin(azimuth), np.cos(azimuth), 0))
            axis = Vector((0, center_y, point.z))
            hit_exact, _, _, depth = tree.ray_cast(axis + radial * .150, -radial, .150)
            floor = float(author['interpolate_skin'](*atlas, np.array([point.z]), np.array([azimuth]))[0])
            findings[mode][domain] = dict(curveID=int(ids[index]), pointIndex=point_index,
                positionMetres=list(point), nearbyControlPointsMetres=points[index, max(0, point_index-2):point_index+3].tolist(),
                nearestSkinPointMetres=list(hit), nearestTriangle=triangle,
                nearestOrientedCenterDistanceMetres=distance if (point-hit).dot(normal) >= 0 else -distance,
                independentRayCrossings=ray_counts, allRaysOdd=all(count % 2 == 1 for count in ray_counts),
                strandRadialCoordinateMetres=radius, interpolatedAtlasRadiusMetres=floor,
                exactRadialSkinMetres=.150-depth if hit_exact is not None else None)
    result = dict(source=proof['source'], findings=findings,
        method='Reopen, exact nearest triangle, and three independent directed ray parity probes at four specific controls. '
               'Radial atlas values are compared to a new ray on the exact neutral mesh.')
    (ROOT / 'contact-localization.json').write_bytes(json.dumps(result, indent=2).encode('utf-8'))
    for mode, domains in findings.items():
        for label, item in domains.items():
            print('R488_CONTACT_LOCALIZED', mode, label, item['independentRayCrossings'],
                  item['interpolatedAtlasRadiusMetres'], item['exactRadialSkinMetres'], flush=True)


if __name__ == '__main__':
    main()
