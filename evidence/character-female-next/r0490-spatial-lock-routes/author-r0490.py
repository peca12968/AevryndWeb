"""Build two complete grooms from editable 3D lock routes and original roots."""
from pathlib import Path
import json
import runpy

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parent
PARENT = ROOT.parent / 'r0489-crown-attachment-flow'
SOURCE = PARENT / 'female-next-r0489-crown-attachment-flow-UNACCEPTED.blend'
DEST = ROOT / 'female-next-r0490-spatial-lock-routes-UNACCEPTED.blend'
foundation = runpy.run_path(str(PARENT / 'author-r0489.py'))
digest = foundation['digest']
read_json = foundation['read_json']
write_json = foundation['write_json']
array_hash = foundation['array_hash']
read_attribute = foundation['read_attribute']
positions = foundation['positions']
set_positions = foundation['set_positions']
normalized = foundation['normalized']
tangent_to = foundation['tangent_to']
smooth = foundation['smooth']
CONTROL = foundation['CONTROL']
BODY = foundation['BODY']
POINTS = 80

# Each path is entered in head-local millimetres, from upper route to tip.
# These are authored spatial stations, not a constant-height radial shell.
ROUTES = [
    (-124, 17, [(-77,-77,1537),(-93,-74,1500),(-104,-63,1451),(-91,-50,1406),(-73,-65,1361)]),
    (-107, 18, [(-82,-62,1528),(-101,-61,1489),(-105,-46,1438),(-95,-35,1390),(-83,-48,1338)]),
    (-91, 18, [(-82,-38,1531),(-99,-32,1494),(-104,-20,1450),(-104,-2,1409),(-81,-10,1350)]),
    (-75, 19, [(-80,-13,1525),(-96,1,1485),(-106,17,1440),(-88,30,1394),(-77,34,1340)]),
    (-58, 18, [(-70,12,1533),(-85,37,1493),(-91,51,1450),(-77,65,1405),(-63,64,1344)]),
    (-39, 20, [(-53,34,1532),(-65,58,1486),(-64,74,1439),(-46,87,1399),(-48,77,1334)]),
    (-20, 19, [(-29,47,1536),(-35,64,1493),(-31,88,1449),(-24,91,1400),(-25,77,1344)]),
    (0, 21, [(0,50,1530),(4,70,1490),(9,85,1441),(-3,96,1398),(3,79,1335)]),
    (20, 20, [(27,46,1534),(34,64,1494),(44,83,1451),(29,94,1404),(20,77,1340)]),
    (39, 19, [(49,37,1530),(66,56,1487),(68,75,1442),(56,80,1397),(49,70,1341)]),
    (58, 19, [(70,15,1535),(85,33,1491),(90,56,1449),(86,65,1402),(69,58,1351)]),
    (75, 18, [(78,-9,1529),(98,2,1488),(107,16,1444),(97,33,1400),(81,26,1341)]),
    (91, 18, [(84,-34,1530),(100,-30,1493),(103,-12,1453),(103,1,1403),(81,4,1347)]),
    (107, 17, [(83,-57,1535),(95,-62,1496),(104,-50,1443),(95,-36,1396),(83,-36,1343)]),
    (124, 16, [(73,-81,1540),(89,-78,1499),(97,-62,1457),(90,-51,1411),(77,-54,1362)]),
]

# A second authored direction for each lower route, with asymmetry across the face.
# The last three stations change independently and the upper two keep their crown access.
LOWER_SWEPT = [
    [(-103,-56,1455),(-95,-29,1407),(-79,-23,1342)],
    [(-110,-39,1440),(-99,-15,1390),(-83,-1,1335)],
    [(-109,-14,1448),(-97,12,1399),(-79,21,1343)],
    [(-107,22,1445),(-92,45,1396),(-72,45,1346)],
    [(-95,48,1454),(-83,74,1405),(-58,70,1340)],
    [(-71,78,1444),(-53,93,1394),(-39,80,1329)],
    [(-41,91,1455),(-33,98,1407),(-12,80,1343)],
    [(-5,91,1443),(7,99,1395),(13,82,1332)],
    [(38,89,1453),(41,94,1403),(31,77,1346)],
    [(69,77,1441),(68,85,1394),(52,66,1340)],
    [(93,51,1451),(90,59,1403),(77,46,1353)],
    [(107,13,1444),(103,28,1396),(92,15,1346)],
    [(108,-21,1451),(111,-9,1403),(92,-14,1341)],
    [(100,-61,1445),(107,-51,1399),(90,-49,1356)],
    [(94,-79,1454),(98,-67,1406),(82,-66,1370)],
]


def make_guide(scene, label):
    data = bpy.data.curves.new(f'R490 editable spatial stations | {label}', 'CURVE')
    data.dimensions = '3D'
    for index, (_, _, row) in enumerate(ROUTES):
        route = row if label == 'waves' else row[:2] + LOWER_SWEPT[index]
        spline = data.splines.new('POLY')
        spline.points.add(len(route) - 1)
        for point, xyz in zip(spline.points, route):
            point.co = (*(np.asarray(xyz) / 1000), 1)
    obj = bpy.data.objects.new(data.name, data)
    scene.collection.objects.link(obj)
    obj['aevrynd_section_directions_deg'] = [row[0] for row in ROUTES]
    obj['aevrynd_section_halfwidth_mm'] = [row[1] for row in ROUTES]
    obj['aevrynd_part_m'] = .010 if label == 'waves' else -.006
    obj.hide_render = True
    obj.hide_set(True)
    return obj


def read_guide(obj):
    stations = np.array([[point.co[:3] for point in spline.points] for spline in obj.data.splines], dtype='f8')
    angles = np.radians(np.asarray(obj['aevrynd_section_directions_deg'], dtype='f8'))
    widths = np.asarray(obj['aevrynd_section_halfwidth_mm'], dtype='f8') / 1000
    return stations, angles, widths, float(obj['aevrynd_part_m'])


def dense_route(stations):
    tangents = np.gradient(stations, axis=0)
    t = np.linspace(0, 1, 65)[:, None]
    t2, t3 = t * t, t * t * t
    segments = []
    for index in range(len(stations) - 1):
        points = ((2*t3-3*t2+1)*stations[index] + (t3-2*t2+t)*tangents[index]
                  + (-2*t3+3*t2)*stations[index+1] + (t3-t2)*tangents[index+1])
        segments.append(points if not index else points[1:])
    points = np.concatenate(segments)
    assert np.all(np.diff(points[:, 2]) < 0)
    distance = np.r_[0, np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))]
    direction = normalized(np.gradient(points, axis=0))
    outward = normalized(np.column_stack((points[:, 0], points[:, 1] + .033, np.zeros(len(points)))))
    across = normalized(np.cross(direction, outward))
    depth = normalized(np.cross(across, direction))
    return points, distance, across, depth


def sample(distance, values, query):
    return np.stack([np.interp(query, distance, values[:, axis]) for axis in range(3)], axis=-1)


def membership(roots, angles, part):
    azimuth = np.arctan2(roots[:, 0], roots[:, 1] + .033)
    front = abs(azimuth) > 2.48
    azimuth -= (front & (azimuth > 0) & (roots[:, 0] < part)) * (2*np.pi)
    azimuth += (front & (azimuth < 0) & (roots[:, 0] >= part)) * (2*np.pi)
    absolute = abs(azimuth)
    destination = np.sign(azimuth)*np.where(absolute > 1.75, 1.75 + .29*(absolute - 1.75), absolute)
    owner = abs(destination[:, None] - angles).argmin(axis=1).astype('i4')
    nearest_spacing = np.gradient(angles)[owner]
    lane = np.clip(2 * (destination - angles[owner])/nearest_spacing, -1, 1)
    return owner, lane


def surface_splice(root, normals, free, joins, crest):
    """Start in the exact attachment frame and match the free-route tangent."""
    row = np.arange(len(root))
    end = free[row, joins]
    chord = end - root
    length = np.linalg.norm(chord, axis=1)
    forward = normalized(tangent_to(chord, normals))
    out = forward * (1.11 * length)[:, None] + normals * .006
    exit_direction = normalized(free[row, joins + 1] - end)
    end_slope = exit_direction * length[:, None]
    for index in range(1, int(joins.max())):
        active = index < joins
        t = (index / joins[active])[:, None]
        t2, t3 = t*t, t*t*t
        point = ((2*t3-3*t2+1)*root[active] + (t3-2*t2+t)*out[active]
                 + (-2*t3+3*t2)*end[active] + (t3-t2)*end_slope[active])
        free[active, index] = point + (np.sin(np.pi*t)**2) * crest[active, None] * normals[active]
    free[:, 0] = root
    return free


def generate(base, normals, ids, radii, tree, guide):
    stations, angles, widths, part = read_guide(guide)
    roots = base[:, 0].astype('f8')
    owner, lanes = membership(roots, angles, part)
    result = np.empty_like(base)
    joins = np.empty(len(base), dtype='i4')
    noise = ((ids.astype('u8') * np.uint64(2654435761)) & np.uint64(0xffffffff)).astype('f8') / 4294967296
    phase = np.arange(POINTS)[None, :]
    for section, route in enumerate(stations):
        rows = np.flatnonzero(owner == section)
        assert len(rows)
        points, arc, across, depth = dense_route(route)
        root = roots[rows]
        lane = lanes[rows]
        random = noise[rows]
        height = smooth((root[:, 2] - 1.455) / .111)
        # Entry occurs lower on the authored route for low scalp roots.
        height_entry = np.interp(root[:, 2] - .026, points[::-1, 2], arc[::-1])
        start = np.maximum(height_entry, .005 + .013 * random + .006 * abs(lane))
        finish = arc[-1] - (.003 + .009*abs(lane) + .015*random + .010*(1-height))
        start = np.minimum(start, finish - .032)
        assert np.all(start >= 0)
        center = sample(arc, points, start)
        upper = np.linalg.norm(center-root, axis=1)
        join = np.clip(np.rint(79*upper / (upper + finish-start)), 11, 42).astype('i4')
        progress = np.clip((phase-join[:, None]) / (79-join[:, None]), 0, 1)
        distance = start[:, None] + progress * (finish-start)[:, None]
        center = sample(arc, points, distance)
        tangent_across = sample(arc, across, distance)
        tangent_depth = sample(arc, depth, distance)
        along = distance / arc[-1]
        # Open overlapping locks with depth and edge taper, independent of strand radius.
        width = widths[section] * (1 - .54 * smooth((along-.58)/.42))
        cross_section = lane[:, None] * width + (.0024*np.sin(2*np.pi*along + section*.67))
        ridge = (1-lane[:, None]**2)*(.003+.005*np.sin(np.pi*along)**2)
        elevation = (.008*(height-.5)+.006*(random-.5))[:, None]
        free = center + tangent_across*cross_section[:, :, None] + tangent_depth*(ridge+elevation)[:, :, None]
        crest = (.0018 + .0045*height) * (1 + .14*np.sin(section*.83 + lane))
        result[rows] = surface_splice(root, normals[rows], free, join, crest).astype('f4')
        joins[rows] = join
    local = foundation['constrain_upper_shape'](result, np.minimum(joins+4, 79), radii, tree)
    assert np.isfinite(result).all() and np.array_equal(result[:, 0], base[:, 0])
    return result, owner, joins, local


def main():
    parent = read_json(PARENT / 'continuation.json')
    receipt = read_json(PARENT / 'construction-receipt.json')
    assert not DEST.exists() and digest(SOURCE) == parent['source']['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE), load_ui=False, use_scripts=False)
    scene = bpy.context.scene
    control = bpy.data.objects[CONTROL]
    previous_banks = []
    for obj in list(scene.objects):
        if obj.type == 'CURVES' and obj != control:
            previous_banks.append(obj.name)
            data = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if not data.users:
                bpy.data.hair_curves.remove(data)
    base = positions(control)
    assert array_hash(base) == receipt['controlPositionHash']
    ids = read_attribute(control.data, 'AFN409_CURVE_ID')
    radii = read_attribute(control.data, 'radius').reshape(len(base), POINTS)
    normals, tree, error = foundation['binding_frame'](control, bpy.data.objects[BODY], base[:, 0])
    variants = {}
    for label in ('waves', 'swept'):
        guide = make_guide(scene, label)
        bank, owner, join, local = generate(base, normals, ids, radii, tree, guide)
        obj = control.copy()
        obj.data = control.data.copy()
        obj.name = f'R490 complete hair | {label}'
        obj.data.name = f'R490 spatial section strands | {label}'
        scene.collection.objects.link(obj)
        set_positions(obj, bank)
        for key, values in (('AEVRYND_SPATIAL_LOCK_ID', owner), ('AEVRYND_SPATIAL_JOIN_POINT', join)):
            obj.data.attributes.new(key, 'INT', 'CURVE').data.foreach_set('value', values)
        obj['Aevrynd_Guide_Object'] = guide.name
        variants[label] = dict(object=obj.name, guideObject=guide.name, guideStations=read_guide(guide)[0].tolist(),
            positionHash=array_hash(bank), ownershipHash=array_hash(owner), joinHash=array_hash(join),
            strandsByLock=np.bincount(owner).tolist(), joinRange=[int(join.min()), int(join.max())],
            changedTips=int(np.any(bank[:, -1] != base[:, -1], axis=1).sum()), **local)
    active = bpy.data.objects[variants['waves']['object']]
    for obj in scene.objects:
        if obj.type == 'CURVES':
            obj.hide_render = obj != active
            obj.hide_set(obj != active)
    bpy.ops.object.select_all(action='DESELECT')
    active.select_set(True)
    bpy.context.view_layer.objects.active = active
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 4
    bpy.data.texts.new('Aevrynd_R490_Spatial_Locks').write(
        'Two independent full rest grooms. Edit the hidden R490 spatial station objects in Blender. '
        'The author script consumes their native spline controls. The original bound strand identities are retained.\n')
    bpy.ops.wm.save_as_mainfile(filepath=str(DEST), compress=True, copy=True)
    assert digest(SOURCE) == parent['source']['sha256']
    write_json(ROOT / 'construction-receipt.json', dict(source=dict(path=str(DEST), sha256=digest(DEST), bytes=DEST.stat().st_size),
        parent=parent['source'], controlObject=control.name, controlPositionHash=array_hash(base),
        bindingMaximumErrorMetres=error, rootHash=array_hash(base[:, 0]), strands=len(base), pointsPerStrand=POINTS,
        defaultVisible='waves', variants=variants, historicalBanksInParent=previous_banks))
    print('R490_SOURCE', str(DEST), flush=True)


if __name__ == '__main__':
    main()
