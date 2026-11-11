"""Blend existing posterior fibres across adjacent lock edges while retaining their interiors."""
from pathlib import Path
import runpy

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parent
PARENT = ROOT.parent / 'r0495-local-ear-tuck'
SOURCE = PARENT / 'female-next-r0495-local-ear-tuck-UNACCEPTED.blend'
DEST = ROOT / 'female-next-r0497-feathered-rear-locks-UNACCEPTED.blend'
previous = runpy.run_path(str(ROOT.parent / 'r0496-overlapping-rear-locks/author-r0496.py'))
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
CONTROL = previous['CONTROL']
POINTS = previous['POINTS']
HEIGHTS = previous['HEIGHTS']
EDGES = previous['EDGES']
LOCKS = previous['LOCKS']


def make_guide(scene, label, base, owner):
    parent_layout = 'separate' if label == 'feathered' else 'woven'
    guide = previous['make_guide'](scene, parent_layout, base, owner)
    guide.name = f'R497 rear lock axes | {label}'
    guide.data.name = guide.name
    guide['aevrynd_edge_blend_layout'] = label
    return guide


def edge_ownership(arrival, group, supported):
    sections = np.maximum(group, 0) % LOCKS
    inner = group >= LOCKS
    x = arrival[:, 0] - .006 * inner
    left, right = EDGES[sections], EDGES[sections + 1]
    left_distance, right_distance = x - left, right - x
    use_left = (left_distance <= right_distance) & (sections > 0)
    use_right = (~use_left) & (sections < LOCKS - 1)
    candidate = np.where(use_left, group - 1, group + 1)
    distance = np.where(use_left, left_distance, right_distance)
    width = (right - left) * (.46 if supported else .34)
    active = (group >= 0) & (use_left | use_right) & (distance >= 0) & (distance < width)
    share = np.where(active, .5 * (1 - smooth(distance / width)), 0)
    share = share.astype('f4')
    neighbor = np.where(share > 0, candidate, -1).astype('i4')
    assert np.all((neighbor[share > 0] // LOCKS) == (group[share > 0] // LOCKS))
    return neighbor, share


def shape_target(strand, arrival_x, random, lock, axis, reference_path, guide_path, woven):
    section, lower = lock % LOCKS, lock >= LOCKS
    z = strand[:, :, 2]
    heights = reference_path[::-1, 2]
    reference_x = np.interp(z, heights, reference_path[::-1, 0])
    reference_y = np.interp(z, heights, reference_path[::-1, 1])
    centre_x = np.interp(z, heights, guide_path[::-1, 0])
    centre_y = np.interp(z, heights, guide_path[::-1, 1])
    centre_z = np.interp(z, heights, guide_path[::-1, 2]) + z - np.clip(z, HEIGHTS[-1], HEIGHTS[0])
    lane_width = (EDGES[section + 1] - EDGES[section]) / 2
    lane = np.clip((arrival_x - axis[2, 0]) / lane_width, -1, 1)
    oval = np.sqrt(np.maximum(0, 1 - lane ** 2))[:, None]
    overlap = (1.15 if lower else 1.08) * (strand[:, :, 0] - reference_x)
    depth = (.55 if lower else .71) * (strand[:, :, 1] - reference_y)
    swell = (.0027 if lower else .0063) * (oval - .52)
    swell *= .81 + .16 * np.cos(section * 1.78)
    swell = swell * (.58 + .42 * smooth((1.505 - z) / .056))
    if woven:
        overlap += (.0030 if lower else -.0025) * oval * smooth((1.459 - z) / .063)
    depth += swell + .0014 * (random[:, None] - .5)
    return np.stack((centre_x + overlap, centre_y + depth, centre_z), axis=2)


def generate(base, ids, owner, guide):
    parent_layout = guide['aevrynd_rear_lock_layout']
    supported = guide['aevrynd_edge_blend_layout'] == 'supported'
    arrival, anchor, weight, group = previous['assign'](base, owner, parent_layout)
    neighbor, share = edge_ownership(arrival, group, supported)
    reference = np.asarray(guide['aevrynd_measured_rear_axes']).reshape(-1, len(HEIGHTS), 3)
    assert len(reference) == len(guide.data.splines)
    random = ((ids.astype('u8') * np.uint64(2654435761)) & np.uint64(0xffffffff)).astype('f8') / 4294967296
    guides = [np.array([point.co[:3] for point in spline.points], dtype='f8') for spline in guide.data.splines]
    paths = [(spatial['dense_route'](old)[0], spatial['dense_route'](new)[0]) for old, new in zip(reference, guides)]
    result = base.copy()
    root_ramp = smooth(np.arange(POINTS)[None, :] / 12)
    for lock in range(len(paths)):
        rows = np.flatnonzero(group == lock)
        strand = base[rows].astype('f8')
        target = shape_target(strand, arrival[rows, 0], random[rows], lock, reference[lock], *paths[lock], supported)
        for adjacent in np.unique(neighbor[rows][neighbor[rows] >= 0]):
            edge = np.flatnonzero(neighbor[rows] == adjacent)
            shared_rows = rows[edge]
            adjacent_target = shape_target(strand[edge], arrival[shared_rows, 0], random[shared_rows], adjacent,
                                           reference[adjacent], *paths[adjacent], supported)
            blend = share[shared_rows, None, None]
            combined = target[edge] + blend * (adjacent_target - target[edge])
            if supported:
                # Retain part of the measured coverage at the centre of a shared strip.
                support = .52 * (4 * blend * (1 - blend)) ** 2
                combined += support * (strand[edge] - combined)
            target[edge] = combined
        onset = smooth((1.516 - strand[:, :, 2]) / .050) * root_ramp
        shaped = strand + (weight[rows, None] * onset)[:, :, None] * (target - strand)
        result[rows] = shaped.astype('f4')
    assert np.isfinite(result).all() and np.array_equal(result[:, 0], base[:, 0])
    assert np.array_equal(result[weight == 0], base[weight == 0])
    protected = base[:, :, 2] >= 1.516
    assert np.array_equal(result[protected], base[protected])
    stats = dict(protectedUpperControls=int(protected.sum()), blendedStrands=int((share > 0).sum()),
                 interiorStrands=int(((group >= 0) & (share == 0)).sum()), maximumNeighborWeight=float(share.max()))
    return result, weight, anchor, group, neighbor, share, stats


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
    for label in ('feathered', 'supported'):
        guide = make_guide(scene, label, base, owner)
        bank, weights, joins, groups, neighbors, shares, local = generate(base, ids, owner, guide)
        obj = control.copy()
        obj.data = control.data.copy()
        obj.name = f'R497 complete hair | {label}'
        obj.data.name = f'R497 feathered rear locks | {label}'
        scene.collection.objects.link(obj)
        set_positions(obj, bank)
        for key, kind, values in (('AEVRYND_REAR_BLEND_WEIGHT', 'FLOAT', weights),
                                  ('AEVRYND_REAR_BLEND_JOIN', 'INT', joins),
                                  ('AEVRYND_REAR_BLEND_GROUP', 'INT', groups),
                                  ('AEVRYND_REAR_BLEND_NEIGHBOR', 'INT', neighbors),
                                  ('AEVRYND_REAR_BLEND_NEIGHBOR_WEIGHT', 'FLOAT', shares)):
            obj.data.attributes.new(key, kind, 'CURVE').data.foreach_set('value', values)
        obj['Aevrynd_Guide_Object'] = guide.name
        variants[label] = dict(object=obj.name, guideObject=guide.name, guideSplines=len(guide.data.splines), positionHash=array_hash(bank),
            weightHash=array_hash(weights), joinHash=array_hash(joins), groupHash=array_hash(groups),
            neighborHash=array_hash(neighbors), neighborWeightHash=array_hash(shares), groupCounts=np.bincount(groups + 1).tolist(), changedStrands=int(np.any(bank != base, axis=(1, 2)).sum()), **local)
    active = bpy.data.objects[variants['supported']['object']]
    for obj in scene.objects:
        if obj.type == 'CURVES':
            obj.hide_render = obj != active
            obj.hide_set(obj != active)
    bpy.ops.object.select_all(action='DESELECT')
    active.select_set(True)
    bpy.context.view_layer.objects.active = active
    bpy.data.texts.new('Aevrynd_R497_Feathered_Rear_Locks').write(
        'Two complete unaccepted grooms with editable rear lock axes and original ear and crown geometry. Original roots and strand identities are preserved.\n')
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 4
    bpy.ops.wm.save_as_mainfile(filepath=str(DEST), compress=True, copy=True)
    assert digest(SOURCE) == parent['source']['sha256']
    write_json(ROOT / 'construction-receipt.json', dict(source=dict(path=str(DEST), sha256=digest(DEST), bytes=DEST.stat().st_size),
        parent=parent['source'], controlObject=control.name, controlPositionHash=array_hash(base), rootHash=array_hash(base[:, 0]),
        bindingMaximumErrorMetres=error, strands=len(base), pointsPerStrand=POINTS, defaultVisible='supported', variants=variants,
        pinnae=ears, historicalBanksInParent=omitted))
    print('R497_SOURCE', str(DEST), flush=True)


if __name__ == '__main__':
    main()
