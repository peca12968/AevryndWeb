"""Build two editable ear-to-nape arrangements on the archived r492 root set."""
from pathlib import Path
import runpy

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parent
PARENT = ROOT.parent / 'r0492-posterior-loft'
SOURCE = PARENT / 'female-next-r0492-posterior-loft-UNACCEPTED.blend'
DEST = ROOT / 'female-next-r0493-ear-nape-flow-UNACCEPTED.blend'
previous = runpy.run_path(str(PARENT / 'author-r0492.py'))
spatial = previous['spatial']
foundation = previous['foundation']
digest = previous['digest']
read_json = previous['read_json']
write_json = previous['write_json']
array_hash = previous['array_hash']
read_attribute = previous['read_attribute']
positions = previous['positions']
set_positions = previous['set_positions']
smooth = previous['smooth']
BODY = previous['BODY']
CONTROL = 'R492 complete hair | crossfall'
POINTS = 80
SECTORS = (.71, .94, 1.15, 1.36, 1.57, 1.78, 1.99, 2.21, 2.44)

# From nape to temple. Stations in millimetres, in the actual neutral head frame.
# Two upper lanes cross behind the pinna at different heights and turn at different depths.
UPPER = (
    ((66,23,1533),(79,39,1495),(84,51,1450),(75,55,1408),(61,50,1348)),
    ((73,12,1536),(85,31,1498),(91,43,1450),(75,47,1409),(68,45,1364)),
    ((78,0,1536),(91,24,1498),(95,33,1454),(87,36,1416),(73,33,1354)),
    ((83,-13,1535),(95,10,1499),(96,21,1453),(82,22,1411),(75,27,1369)),
    ((84,-29,1536),(98,-6,1499),(96,10,1458),(89,12,1419),(75,17,1362)),
    ((85,-47,1539),(98,-24,1501),(97,-1,1463),(93,4,1425),(82,11,1376)),
    ((83,-64,1541),(97,-43,1503),(101,-16,1460),(92,-13,1418),(82,-5,1365)),
    ((78,-81,1545),(91,-68,1507),(100,-44,1458),(91,-39,1418),(81,-24,1375)),
    ((68,-99,1545),(85,-90,1506),(94,-75,1455),(91,-61,1407),(76,-48,1350)),
)

# Short paths emerge underneath at separate positions rather than sharing the outer silhouette.
LOWER = (
    ((64,26,1518),(74,34,1485),(77,45,1450),(68,50,1411),(56,44,1366)),
    ((72,12,1520),(80,26,1485),(82,35,1449),(71,42,1413),(63,38,1376)),
    ((76,0,1522),(84,17,1487),(86,26,1450),(77,30,1411),(65,28,1363)),
    ((78,-13,1524),(87,4,1488),(88,15,1452),(77,25,1413),(69,24,1381)),
    ((79,-29,1525),(89,-8,1490),(90,7,1453),(80,15,1416),(70,16,1377)),
    ((80,-45,1526),(91,-23,1490),(92,-1,1452),(83,9,1413),(69,10,1365)),
    ((80,-61,1528),(93,-40,1490),(91,-16,1451),(82,-8,1415),(74,-1,1378)),
    ((76,-79,1530),(89,-64,1493),(91,-40,1451),(84,-27,1414),(75,-15,1368)),
    ((64,-97,1531),(81,-88,1494),(90,-66,1450),(83,-55,1413),(75,-43,1372)),
)

# B uses a second sequence of bends, with a temple arc above a lower crossing.
# Offsets are per rail and applied to three lower stations with independent envelopes.
LOWER_ARCS = np.array([
    [0,0,0], [1,4,-8], [3,-5,8], [-2,5,-7], [1,-4,10],
    [2,-8,-8], [4,-9,5], [-3,3,-11], [0,0,0],
], dtype='f8')


def make_guide(scene, label):
    data = bpy.data.curves.new(f'R493 ear-to-nape stations | {label}', 'CURVE')
    data.dimensions = '3D'
    for sign in (-1, 1):
        for depth, template in enumerate((UPPER, LOWER)):
            routes = np.array(template, dtype='f8')
            if label == 'staggered':
                routes[:, 2] += .65 * LOWER_ARCS * (1 if depth == 0 else -.45)
                routes[:, 3] += LOWER_ARCS * (1 if depth == 0 else -.7)
                routes[:, 4] += LOWER_ARCS * (-.65 if depth == 0 else .55)
            if sign > 0:
                routes[:, 2:, 1] += np.array([0, -3, -6, -5, -2, 2, 4, 2, 0])[:, None]
                routes[:, 4, 2] += np.array([0, 2, -3, 4, -4, 4, -3, 3, 0])
            routes[:, :, 0] *= sign
            for route in routes:
                spline = data.splines.new('POLY')
                spline.points.add(len(route) - 1)
                for point, xyz in zip(spline.points, route):
                    point.co = (*tuple(xyz / 1000), 1)
    guide = bpy.data.objects.new(data.name, data)
    scene.collection.objects.link(guide)
    guide['aevrynd_ear_nape_layout'] = label
    guide['aevrynd_ear_nape_sector_rad'] = SECTORS
    guide.hide_render = True
    guide.hide_set(True)
    return guide


def generate(base, normals, ids, radii, owner, tree, guide):
    stations = np.array([[point.co[:3] for point in spline.points] for spline in guide.data.splines], dtype='f8')
    angles = np.array(guide['aevrynd_ear_nape_sector_rad'])
    assert stations.shape == (4 * len(angles), 5, 3)
    root = base[:, 0].astype('f8')
    angle = np.arctan2(root[:, 0], root[:, 1] + .033)
    absolute = abs(angle)
    weight = smooth((absolute - .77) / .36) * (1 - smooth((absolute - 2.02) / .43))
    noise = ((ids.astype('u8') * np.uint64(2654435761)) & np.uint64(0xffffffff)).astype('f8') / 4294967296
    # The underlayer receives low temporal roots and the existing inner bank.
    inner = (owner >= 15) | ((root[:, 2] < 1.508) & (absolute > 1.09))
    result = base.copy()
    join_points = np.zeros(len(base), dtype='i4')
    route_group = np.full(len(base), -1, dtype='i4')
    phase = np.arange(POINTS)[None, :]
    for side in range(2):
        for depth in range(2):
            group = side * 2 + depth
            routes = stations[group * len(angles):(group + 1) * len(angles)]
            field, slopes, length = previous['build_field'](routes, angles)
            members = np.flatnonzero((angle >= 0) == bool(side))
            members = members[(inner[members] == bool(depth)) & (weight[members] > 0)]
            route_group[members] = group
            for start_index in range(0, len(members), 640):
                rows = members[start_index:start_index + 640]
                route_angle = absolute[rows]
                random = noise[rows]
                attached = root[rows]
                path_length = np.interp(route_angle, angles, length)
                nearest = abs(route_angle[:, None] - angles).argmin(1)
                entry = np.empty(len(rows))
                for index in np.unique(nearest):
                    selected = nearest == index
                    entry[selected] = np.interp(attached[selected, 2] - .024, field[index, ::-1, 2], np.linspace(1, 0, len(field[index])))
                entry = np.maximum(entry, (.006 + .011 * random) / path_length)
                # Stagger the strand tips within each independently authored arc.
                finish = 1 - (.003 + .014 * random + .005 * np.cos(21 * route_angle) ** 2) / path_length
                entry = np.minimum(entry, finish - .035 / path_length)
                first = previous['field_sample'](field, slopes, angles, route_angle, entry)
                crown = np.linalg.norm(first - attached, axis=1)
                joins = np.clip(np.rint(79 * crown / (crown + (finish - entry) * path_length)), 10, 43).astype('i4')
                t = np.clip((phase - joins[:, None]) / (79 - joins[:, None]), 0, 1)
                along = entry[:, None] + t * (finish - entry)[:, None]
                # Cross each local rail gradually toward the nape. Underlayers lag the upper arc.
                drift = -(0.073 if depth == 0 else .030) * np.sin(np.pi * along * .82)
                routed = route_angle[:, None] + drift
                free = previous['field_sample'](field, slopes, angles, routed, along)
                normal = foundation['normalized'](np.stack((free[:, :, 0], free[:, :, 1] + .033, np.zeros_like(along)), axis=2))
                rib = np.cos(routed * 35 - along * (5.0 if depth == 0 else 3.0))
                relief = (.0016 * rib + .0022 * (random[:, None] - .5)) * np.sin(np.pi * along) ** 2
                free += normal * relief[:, :, None]
                crest = .0019 + .0037 * smooth((attached[:, 2] - 1.458) / .109)
                shape = spatial['surface_splice'](attached, normals[rows], free, joins, crest)
                result[rows] = (base[rows] + weight[rows, None, None] * (shape - base[rows])).astype('f4')
                join_points[rows] = joins
    local = foundation['constrain_upper_shape'](result, np.where(weight > 0, join_points + 4, 0), radii, tree)
    assert np.isfinite(result).all() and np.array_equal(result[:, 0], base[:, 0])
    assert np.array_equal(result[weight == 0], base[weight == 0])
    assert np.all(route_group[weight > 0] >= 0)
    return result, weight.astype('f4'), join_points, route_group, local


def main():
    parent = read_json(PARENT / 'construction-receipt.json')
    assert not DEST.exists() and digest(SOURCE) == parent['source']['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE), load_ui=False, use_scripts=False)
    scene = bpy.context.scene
    control = bpy.data.objects[CONTROL]
    base = positions(control)
    assert array_hash(base) == parent['variants']['crossfall']['positionHash']
    keep_guide = parent['variants']['crossfall']['guideObject']
    omitted = []
    for obj in list(scene.objects):
        if (obj.type == 'CURVES' and obj != control) or (obj.type == 'CURVE' and obj.name.startswith(('R491 native layer guides', 'R492 native posterior rails')) and obj.name != keep_guide):
            omitted.append(obj.name)
            data = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if not data.users:
                bank = bpy.data.hair_curves if isinstance(data, bpy.types.Curves) else bpy.data.curves
                bank.remove(data)
    ids = read_attribute(control.data, 'AFN409_CURVE_ID')
    radii = read_attribute(control.data, 'radius').reshape(len(base), POINTS)
    owner = read_attribute(control.data, 'AEVRYND_SPATIAL_LOCK_ID')
    normals, tree, error = foundation['binding_frame'](control, bpy.data.objects[BODY], base[:, 0])
    variants = {}
    for label in ('overlap', 'staggered'):
        guide = make_guide(scene, label)
        bank, weights, joins, groups, local = generate(base, normals, ids, radii, owner, tree, guide)
        obj = control.copy()
        obj.data = control.data.copy()
        obj.name = f'R493 complete hair | {label}'
        obj.data.name = f'R493 ear-to-nape strands | {label}'
        scene.collection.objects.link(obj)
        set_positions(obj, bank)
        for key, kind, values in (('AEVRYND_EAR_NAPE_WEIGHT', 'FLOAT', weights),
                                  ('AEVRYND_EAR_NAPE_JOIN', 'INT', joins),
                                  ('AEVRYND_EAR_NAPE_GROUP', 'INT', groups)):
            obj.data.attributes.new(key, kind, 'CURVE').data.foreach_set('value', values)
        obj['Aevrynd_Guide_Object'] = guide.name
        variants[label] = dict(object=obj.name, guideObject=guide.name, positionHash=array_hash(bank),
            weightHash=array_hash(weights), joinHash=array_hash(joins), groupHash=array_hash(groups),
            groupCounts=np.bincount(groups + 1).tolist(), changedStrands=int(np.any(bank != base, axis=(1, 2)).sum()), **local)
    active = bpy.data.objects[variants['staggered']['object']]
    for obj in scene.objects:
        if obj.type == 'CURVES':
            obj.hide_render = obj != active
            obj.hide_set(obj != active)
    bpy.ops.object.select_all(action='DESELECT')
    active.select_set(True)
    bpy.context.view_layer.objects.active = active
    bpy.data.texts.new('Aevrynd_R493_Ear_Nape_Flow').write(
        'Two complete unaccepted grooms with separate editable upper and lower ear-to-nape rails. Original roots and strand identities are preserved.\n')
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 4
    bpy.ops.wm.save_as_mainfile(filepath=str(DEST), compress=True, copy=True)
    assert digest(SOURCE) == parent['source']['sha256']
    write_json(ROOT / 'construction-receipt.json', dict(source=dict(path=str(DEST), sha256=digest(DEST), bytes=DEST.stat().st_size),
        parent=parent['source'], controlObject=control.name, controlPositionHash=array_hash(base), rootHash=array_hash(base[:, 0]),
        bindingMaximumErrorMetres=error, strands=len(base), pointsPerStrand=POINTS, defaultVisible='staggered', variants=variants,
        guideSplinesPerVariant=4 * len(SECTORS), historicalBanksInParent=omitted))
    print('R493_SOURCE', str(DEST), flush=True)


if __name__ == '__main__':
    main()
