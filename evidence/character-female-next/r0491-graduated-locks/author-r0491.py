"""Build complete layered lock routes without changing the bound strand set."""
from pathlib import Path
import runpy

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parent
PARENT = ROOT.parent / 'r0490-spatial-lock-routes'
SOURCE = PARENT / 'female-next-r0490-spatial-lock-routes-UNACCEPTED.blend'
DEST = ROOT / 'female-next-r0491-graduated-locks-UNACCEPTED.blend'
previous = runpy.run_path(str(PARENT / 'author-r0490.py'))
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
CONTROL = 'R490 complete hair | swept'
POINTS = 80
INNER_OWNERS = tuple(range(3, 12))

# Authored in head-local millimetres. The top and lower layers overlap in depth.
OUTER = [
    [(-55,-104,1544),(-78,-104,1504),(-91,-80,1454),(-86,-67,1403),(-73,-62,1355)],
    [(-70,-84,1536),(-90,-82,1494),(-100,-64,1443),(-91,-43,1393),(-75,-38,1338)],
    [(-81,-54,1532),(-97,-49,1494),(-103,-33,1446),(-94,-13,1400),(-77,-6,1344)],
    [(-81,-23,1528),(-92,-3,1493),(-99,13,1446),(-82,29,1401),(-69,26,1345)],
    [(-69,12,1532),(-83,29,1492),(-87,44,1446),(-70,54,1397),(-59,48,1337)],
    [(-54,31,1533),(-65,48,1490),(-66,60,1444),(-56,66,1394),(-46,58,1344)],
    [(-33,43,1536),(-39,58,1495),(-39,71,1450),(-29,75,1403),(-23,62,1334)],
    [(-4,48,1532),(-2,65,1490),(1,72,1444),(8,77,1396),(2,62,1335)],
    [(25,44,1533),(31,60,1491),(36,68,1448),(38,74,1401),(21,61,1343)],
    [(48,32,1533),(61,48,1489),(67,59,1446),(54,65,1397),(43,55,1340)],
    [(68,13,1534),(82,31,1491),(90,43,1448),(82,51,1404),(63,48,1350)],
    [(77,-13,1529),(91,4,1493),(101,18,1447),(88,32,1403),(72,25,1349)],
    [(82,-36,1532),(95,-26,1493),(100,-9,1445),(90,11,1399),(76,2,1348)],
    [(77,-68,1536),(94,-59,1499),(98,-42,1451),(90,-31,1405),(75,-32,1357)],
    [(67,-91,1538),(87,-86,1501),(96,-66,1459),(87,-51,1412),(73,-54,1362)],
]

# B changes the shape and extent of the front sweep as separate sculptural paths.
SIDE_SWEEP = {
    0: [(-43,-109,1551),(-69,-112,1516),(-90,-96,1469),(-100,-78,1419),(-84,-68,1347)],
    1: [(-62,-95,1542),(-83,-92,1500),(-100,-77,1450),(-100,-49,1401),(-83,-38,1332)],
    2: [(-76,-62,1538),(-94,-57,1501),(-105,-39,1450),(-101,-12,1401),(-80,-2,1340)],
    11: [(78,-12,1527),(89,8,1495),(99,26,1451),(83,40,1407),(67,32,1355)],
    12: [(80,-35,1530),(92,-20,1494),(101,-2,1452),(91,25,1406),(72,25,1353)],
    13: [(74,-62,1534),(90,-46,1495),(101,-24,1456),(93,5,1406),(73,2,1356)],
    14: [(67,-84,1542),(87,-70,1504),(100,-44,1455),(94,-19,1410),(76,-20,1358)],
}

INNER = [
    [(-75,-7,1510),(-85,9,1477),(-91,23,1444),(-74,32,1409),(-66,28,1362)],
    [(-66,13,1517),(-75,27,1484),(-78,41,1450),(-65,49,1411),(-55,45,1363)],
    [(-48,34,1519),(-58,45,1485),(-57,54,1450),(-44,61,1412),(-38,51,1365)],
    [(-28,44,1521),(-33,54,1487),(-34,62,1450),(-24,65,1412),(-20,56,1360)],
    [(-1,50,1519),(-3,58,1485),(3,63,1451),(3,68,1411),(-3,59,1362)],
    [(23,44,1520),(28,54,1484),(31,61,1449),(28,66,1411),(20,56,1363)],
    [(46,33,1517),(56,44,1486),(56,52,1452),(47,59,1414),(38,52,1365)],
    [(64,14,1516),(74,28,1484),(80,41,1450),(69,49,1410),(54,44,1362)],
    [(73,-9,1512),(86,6,1481),(92,23,1449),(75,36,1411),(63,32,1364)],
]


def make_guide(scene, label):
    data = bpy.data.curves.new(f'R491 native layer guides | {label}', 'CURVE')
    data.dimensions = '3D'
    outer = [SIDE_SWEEP.get(index, route) if label == 'diagonal' else route
             for index, route in enumerate(OUTER)]
    for route in outer + INNER:
        spline = data.splines.new('POLY')
        spline.points.add(len(route) - 1)
        for point, xyz in zip(spline.points, route):
            point.co = (*(np.array(xyz)/1000), 1)
    guide = bpy.data.objects.new(data.name, data)
    scene.collection.objects.link(guide)
    guide['aevrynd_section_directions_deg'] = [row[0] for row in previous['ROUTES']]
    guide['aevrynd_section_halfwidth_mm'] = [14,15,16,17,17,17,18,18,17,17,17,16,16,15,14] + [12,13,13,14,14,14,13,13,12]
    guide['aevrynd_part_m'] = .010 if label == 'graduated' else .019
    guide.hide_render = True
    guide.hide_set(True)
    return guide


def generate(base, normals, ids, radii, tree, guide):
    routes, angles, widths, part = previous['read_guide'](guide)
    root = base[:, 0].astype('f8')
    owner, lanes = previous['membership'](root, angles, part)
    noise = ((ids.astype('u8') * np.uint64(2654435761)) & np.uint64(0xffffffff)).astype('f8')/4294967296
    inner_probability = 1-smooth((root[:,2] - 1.487)/.033)
    tucked = np.isin(owner, INNER_OWNERS) & (noise < inner_probability)
    owner[tucked] = len(OUTER) + owner[tucked] - INNER_OWNERS[0]
    bank = np.empty_like(base)
    joins = np.empty(len(base), dtype='i4')
    phase = np.arange(POINTS)[None,:]
    for section, route in enumerate(routes):
        rows = np.flatnonzero(owner == section)
        assert len(rows), section
        center, arc, across, depth = previous['dense_route'](route)
        attached = root[rows]
        lane = lanes[rows]
        random = noise[rows]
        inner = section >= len(OUTER)
        start = np.maximum(np.interp(attached[:,2] - .023, center[::-1,2], arc[::-1]), .006 + .015*random)
        finish = arc[-1] - (.002 + .011*abs(lane) + .014*random)
        start = np.minimum(start, finish - .025)
        assert np.all(start >= 0)
        delta = previous['sample'](arc, center, start) - attached
        upper = np.linalg.norm(delta, axis=1)
        join = np.clip(np.rint(79*upper/(upper+finish-start)), 11, 44).astype('i4')
        progress = np.clip((phase-join[:,None])/(79-join[:,None]), 0, 1)
        distance = start[:,None] + progress*(finish-start)[:,None]
        along = distance/arc[-1]
        sweep = previous['sample'](arc, center, distance)
        width = widths[section]*(1-.52*smooth((along-.51)/.49))
        cross = lane[:,None]*width + .0018*np.sin(2*np.pi*along+section*.81)
        ridge = (1-lane[:,None]**2)*(.0017+.0035*np.sin(np.pi*along)**2)
        ridge += (.0038*(random-.45))[:,None]
        if inner:
            ridge *= .72
        sweep += previous['sample'](arc, across, distance)*cross[:,:,None]
        sweep += previous['sample'](arc, depth, distance)*ridge[:,:,None]
        crest = (.0019+.0041*smooth((attached[:,2]-1.455)/.111))*(1+.12*np.sin(section*.94+lane))
        bank[rows] = previous['surface_splice'](attached, normals[rows], sweep, join, crest).astype('f4')
        joins[rows] = join
    local = foundation['constrain_upper_shape'](bank, np.minimum(joins+4, 79), radii, tree)
    assert np.isfinite(bank).all() and np.array_equal(bank[:,0], base[:,0])
    return bank, owner, joins, local


def main():
    receipt = read_json(PARENT / 'construction-receipt.json')
    assert not DEST.exists() and digest(SOURCE) == receipt['source']['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE), load_ui=False, use_scripts=False)
    scene = bpy.context.scene
    control = bpy.data.objects[CONTROL]
    base = positions(control)
    assert array_hash(base) == receipt['variants']['swept']['positionHash']
    omitted = []
    for obj in list(scene.objects):
        if (obj.type == 'CURVES' and obj != control) or obj.name.startswith('R490 editable spatial stations'):
            omitted.append(obj.name)
            data = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if not data.users:
                bank = bpy.data.hair_curves if isinstance(data, bpy.types.Curves) else bpy.data.curves
                bank.remove(data)
    ids = read_attribute(control.data, 'AFN409_CURVE_ID')
    radii = read_attribute(control.data, 'radius').reshape(len(base), POINTS)
    normals, tree, error = foundation['binding_frame'](control, bpy.data.objects[BODY], base[:,0])
    variants = {}
    for label in ('graduated','diagonal'):
        guide = make_guide(scene, label)
        bank, owner, join, local = generate(base, normals, ids, radii, tree, guide)
        obj = control.copy()
        obj.data = control.data.copy()
        obj.name = f'R491 complete hair | {label}'
        obj.data.name = f'R491 graduated strands | {label}'
        scene.collection.objects.link(obj)
        set_positions(obj, bank)
        for key, values in (('AEVRYND_SPATIAL_LOCK_ID', owner), ('AEVRYND_SPATIAL_JOIN_POINT', join)):
            obj.data.attributes[key].data.foreach_set('value', values)
        obj['Aevrynd_Guide_Object'] = guide.name
        variants[label] = dict(object=obj.name, guideObject=guide.name, positionHash=array_hash(bank),
            ownershipHash=array_hash(owner), joinHash=array_hash(join), strandsByLock=np.bincount(owner).tolist(),
            shorterLayerStrands=int((owner >= len(OUTER)).sum()), changedTips=int(np.any(bank[:,-1]!=base[:,-1], axis=1).sum()), **local)
    active = bpy.data.objects[variants['diagonal']['object']]
    for obj in scene.objects:
        if obj.type == 'CURVES':
            obj.hide_render = obj != active
            obj.hide_set(obj != active)
    bpy.ops.object.select_all(action='DESELECT')
    active.select_set(True)
    bpy.context.view_layer.objects.active = active
    bpy.data.texts.new('Aevrynd_R491_Graduated_Locks').write(
        'Two unaccepted rest layouts. Each has 15 outer routes and nine shorter inner routes. '
        'The native guide objects drive the generated strands. Earlier research banks are in the parent archive.\n')
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 4
    bpy.ops.wm.save_as_mainfile(filepath=str(DEST), compress=True, copy=True)
    assert digest(SOURCE) == receipt['source']['sha256']
    write_json(ROOT / 'construction-receipt.json', dict(source=dict(path=str(DEST), sha256=digest(DEST), bytes=DEST.stat().st_size),
        parent=receipt['source'], controlObject=control.name, controlPositionHash=array_hash(base),
        rootHash=array_hash(base[:,0]), bindingMaximumErrorMetres=error, strands=len(base), pointsPerStrand=POINTS,
        defaultVisible='diagonal', variants=variants, historicalBanksInParent=omitted))
    print('R491_SOURCE', str(DEST), flush=True)


if __name__ == '__main__':
    main()
