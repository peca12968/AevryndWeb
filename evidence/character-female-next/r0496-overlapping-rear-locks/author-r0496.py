"""Reshape posterior strands into editable locks with overlapping cross-sections."""
from pathlib import Path
import runpy

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parent
PARENT = ROOT.parent / 'r0495-local-ear-tuck'
SOURCE = PARENT / 'female-next-r0495-local-ear-tuck-UNACCEPTED.blend'
DEST = ROOT / 'female-next-r0496-overlapping-rear-locks-UNACCEPTED.blend'
previous = runpy.run_path(str(PARENT / 'author-r0495.py'))
foundation = previous['foundation']
spatial = previous['spatial']
digest = previous['digest']
read_json = previous['read_json']
write_json = previous['write_json']
array_hash = previous['array_hash']
read_attribute = previous['read_attribute']
positions = previous['positions']
set_positions = previous['set_positions']
smooth = previous['smooth']
measure_ears = previous['measure_ears']
BODY = previous['BODY']
CONTROL = 'R495 complete hair | tucked'
POINTS = 80
HEIGHTS = np.array([1.526, 1.488, 1.451, 1.411, 1.365, 1.325])
EDGES = np.array([-.071, -.056, -.040, -.024, -.010, .005, .021, .038, .055, .071])
LOCKS = len(EDGES) - 1

# Each row describes a distinct shaping direction and tip height in millimetres.
# The paired underlayer is routed across staggered section boundaries in B.
LEAN = np.array([-2,-5,4,-3,5,8,-5,3,2], dtype='f8')
ROLL = np.array([2,-2,4,1,-2,2,4,-1,2], dtype='f8')
TIPS = np.array([6,-5,9,-8,3,13,-2,7,-3], dtype='f8')


def crossing_at(coords, height):
    z = coords[:, :, 2]
    crosses = (z[:, :-1] >= height) & (z[:, 1:] < height)
    last = np.where(crosses, np.arange(POINTS - 1), -1).max(axis=1)
    closest = abs(z - height).argmin(axis=1)
    row = np.arange(len(coords))
    safe = np.maximum(last, 0)
    a, b = coords[row, safe], coords[row, safe + 1]
    fraction = np.clip((a[:, 2] - height) / np.maximum(a[:, 2] - b[:, 2], 1e-8), 0, 1)
    position = np.where((last >= 0)[:, None], a + (b - a) * fraction[:, None], coords[row, closest])
    return position, np.where(last >= 0, last, closest).astype('i4')


def assign(base, owner, label):
    arrival, anchor = crossing_at(base, HEIGHTS[2])
    root = base[:, 0]
    azimuth = abs(np.arctan2(root[:, 0], root[:, 1] + .033))
    weight = (1 - smooth((azimuth - .78) / .30)) * smooth((arrival[:, 1] - .039) / .016)
    weight *= 1 - smooth((abs(arrival[:, 0]) - .061) / .017)
    lower = owner >= 15
    if label == 'separate':
        weight[lower] = 0
    sector = np.searchsorted(EDGES[1:-1], arrival[:, 0] - .006 * lower, side='right')
    group = sector + LOCKS * lower
    group[weight == 0] = -1
    return arrival, np.where(weight > 0, anchor, 0), weight.astype('f4'), group.astype('i4')


def make_guide(scene, label, base, owner):
    _, _, _, group = assign(base, owner, label)
    count = LOCKS if label == 'separate' else 2 * LOCKS
    data = bpy.data.curves.new(f'R496 shaped rear lock axes | {label}', 'CURVE')
    data.dimensions = '3D'
    reference = []
    for lock in range(count):
        section, lower = lock % LOCKS, lock >= LOCKS
        selected = base[group == lock]
        assert len(selected) >= 5, (lock, label, len(selected))
        samples = np.array([np.median(crossing_at(selected, z)[0], axis=0) for z in HEIGHTS], dtype='f8')
        samples[:, 2] = HEIGHTS
        reference.append(samples)
        route = samples.copy()
        lean = LEAN[section] * .001 * (-.65 if lower else 1)
        roll = ROLL[section] * .001 * (-.5 if lower else 1)
        if label == 'woven':
            lean += (.004 if section % 3 == 1 else -.0025) * (-.78 if lower else 1)
            roll += (-.002 if lower else .001)
        route[:, 0] += lean * np.array([0,.34,.82,1,.58,.20])
        route[:, 1] += roll * np.array([0,.32,.82,1,.62,.20])
        route[:, 2] += TIPS[section] * .001 * np.array([0,0,0,.16,.65,1]) * (.45 if lower else 1)
        spline = data.splines.new('POLY')
        spline.points.add(len(route) - 1)
        for point, xyz in zip(spline.points, route):
            point.co = (*tuple(xyz), 1)
    guide = bpy.data.objects.new(data.name, data)
    scene.collection.objects.link(guide)
    guide['aevrynd_rear_lock_layout'] = label
    guide['aevrynd_measured_rear_axes'] = np.array(reference).ravel().tolist()
    guide.hide_render = True
    guide.hide_set(True)
    return guide


def generate(base, ids, owner, guide):
    label = guide['aevrynd_rear_lock_layout']
    arrival, anchor, weight, group = assign(base, owner, label)
    reference = np.asarray(guide['aevrynd_measured_rear_axes']).reshape(-1, len(HEIGHTS), 3)
    assert len(reference) == len(guide.data.splines)
    random = ((ids.astype('u8') * np.uint64(2654435761)) & np.uint64(0xffffffff)).astype('f8') / 4294967296
    result = base.copy()
    for lock, spline in enumerate(guide.data.splines):
        rows = np.flatnonzero(group == lock)
        section, lower = lock % LOCKS, lock >= LOCKS
        route = np.array([point.co[:3] for point in spline.points], dtype='f8')
        guide_path, _, _, _ = spatial['dense_route'](route)
        reference_path, _, _, _ = spatial['dense_route'](reference[lock])
        assert len(guide_path) == len(reference_path)
        strand = base[rows].astype('f8')
        z = strand[:, :, 2]
        reference_x = np.interp(z, reference_path[::-1, 2], reference_path[::-1, 0])
        reference_y = np.interp(z, reference_path[::-1, 2], reference_path[::-1, 1])
        centre_x = np.interp(z, reference_path[::-1, 2], guide_path[::-1, 0])
        centre_y = np.interp(z, reference_path[::-1, 2], guide_path[::-1, 1])
        centre_z = np.interp(z, reference_path[::-1, 2], guide_path[::-1, 2])
        centre_z += z - np.clip(z, HEIGHTS[-1], HEIGHTS[0])
        lane_width = (EDGES[section + 1] - EDGES[section]) / 2
        lane = (arrival[rows, 0] - reference[lock, 2, 0]) / lane_width
        lane = np.clip(lane, -1, 1)
        oval = np.sqrt(np.maximum(0, 1 - lane ** 2))[:, None]
        overlap = (1.15 if lower else 1.08) * (strand[:, :, 0] - reference_x)
        depth = (.55 if lower else .71) * (strand[:, :, 1] - reference_y)
        swell = (.0027 if lower else .0063) * (oval - .52)
        swell *= .81 + .16 * np.cos(section * 1.78)
        swell = swell * (.58 + .42 * smooth((1.505 - z) / .056))
        if label == 'woven':
            overlap += (.0030 if lower else -.0025) * oval * smooth((1.459 - z) / .063)
        depth += swell + .0014 * (random[rows, None] - .5)
        target = np.stack((centre_x + overlap, centre_y + depth, centre_z), axis=2)
        onset = smooth((1.516 - z) / .050) * smooth(np.arange(POINTS)[None, :] / 12)
        shaped = strand + (weight[rows, None] * onset)[:, :, None] * (target - strand)
        result[rows] = shaped.astype('f4')
    assert np.isfinite(result).all() and np.array_equal(result[:, 0], base[:, 0])
    assert np.array_equal(result[weight == 0], base[weight == 0])
    assert np.array_equal(result[base[:, :, 2] >= 1.516], base[base[:, :, 2] >= 1.516])
    return result, weight, anchor, group, dict(protectedUpperControls=int((base[:, :, 2] >= 1.516).sum()))


def main():
    parent = read_json(PARENT / 'construction-receipt.json')
    assert not DEST.exists() and digest(SOURCE) == parent['source']['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE), load_ui=False, use_scripts=False)
    scene = bpy.context.scene
    control = bpy.data.objects[CONTROL]
    base = positions(control)
    assert array_hash(base) == parent['variants']['tucked']['positionHash']
    keep_guide = parent['variants']['tucked']['guideObject']
    omitted = []
    for obj in list(scene.objects):
        if (obj.type == 'CURVES' and obj != control) or (obj.type == 'CURVE' and obj.name.startswith(('R493 ear-to-nape stations', 'R495 local ear arcs')) and obj.name != keep_guide):
            omitted.append(obj.name)
            data = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if not data.users:
                bank = bpy.data.hair_curves if isinstance(data, bpy.types.Curves) else bpy.data.curves
                bank.remove(data)
    ids = read_attribute(control.data, 'AFN409_CURVE_ID')
    _, _, error = foundation['binding_frame'](control, bpy.data.objects[BODY], base[:, 0])
    owner = read_attribute(control.data, 'AEVRYND_SPATIAL_LOCK_ID')
    ears = measure_ears(bpy.data.objects[BODY])
    variants = {}
    for label in ('separate', 'woven'):
        guide = make_guide(scene, label, base, owner)
        bank, weights, joins, groups, local = generate(base, ids, owner, guide)
        obj = control.copy()
        obj.data = control.data.copy()
        obj.name = f'R496 complete hair | {label}'
        obj.data.name = f'R496 overlapping rear locks | {label}'
        scene.collection.objects.link(obj)
        set_positions(obj, bank)
        for key, kind, values in (('AEVRYND_REAR_LOCK_WEIGHT', 'FLOAT', weights),
                                  ('AEVRYND_REAR_LOCK_JOIN', 'INT', joins),
                                  ('AEVRYND_REAR_LOCK_GROUP', 'INT', groups)):
            obj.data.attributes.new(key, kind, 'CURVE').data.foreach_set('value', values)
        obj['Aevrynd_Guide_Object'] = guide.name
        variants[label] = dict(object=obj.name, guideObject=guide.name, guideSplines=len(guide.data.splines), positionHash=array_hash(bank),
            weightHash=array_hash(weights), joinHash=array_hash(joins), groupHash=array_hash(groups),
            groupCounts=np.bincount(groups + 1).tolist(), changedStrands=int(np.any(bank != base, axis=(1, 2)).sum()), **local)
    active = bpy.data.objects[variants['woven']['object']]
    for obj in scene.objects:
        if obj.type == 'CURVES':
            obj.hide_render = obj != active
            obj.hide_set(obj != active)
    bpy.ops.object.select_all(action='DESELECT')
    active.select_set(True)
    bpy.context.view_layer.objects.active = active
    bpy.data.texts.new('Aevrynd_R496_Overlapping_Rear_Locks').write(
        'Two complete unaccepted grooms with editable rear lock axes and original ear and crown geometry. Original roots and strand identities are preserved.\n')
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 4
    bpy.ops.wm.save_as_mainfile(filepath=str(DEST), compress=True, copy=True)
    assert digest(SOURCE) == parent['source']['sha256']
    write_json(ROOT / 'construction-receipt.json', dict(source=dict(path=str(DEST), sha256=digest(DEST), bytes=DEST.stat().st_size),
        parent=parent['source'], controlObject=control.name, controlPositionHash=array_hash(base), rootHash=array_hash(base[:, 0]),
        bindingMaximumErrorMetres=error, strands=len(base), pointsPerStrand=POINTS, defaultVisible='woven', variants=variants,
        pinnae=ears, historicalBanksInParent=omitted))
    print('R496_SOURCE', str(DEST), flush=True)


if __name__ == '__main__':
    main()
