"""Bend the existing temporal fall around the ear with a local, editable release."""
from pathlib import Path
import runpy

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parent
PARENT = ROOT.parent / 'r0493-ear-nape-flow'
SOURCE = PARENT / 'female-next-r0493-ear-nape-flow-UNACCEPTED.blend'
DEST = ROOT / 'female-next-r0495-local-ear-tuck-UNACCEPTED.blend'
previous = runpy.run_path(str(ROOT.parent / 'r0494-pinna-parting/author-r0494.py'))
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
measure_ears = previous['measure_ears']
BODY = previous['BODY']
CONTROL = 'R493 complete hair | staggered'
POINTS = 80

# X and Y are offsets from the outer pinna and its sagittal centre, respectively.
# Z uses the ear top. Each path turns locally and releases below the lobe.
BEHIND = ((8,0,31),(11,11,10),(8,20,-12),(3,19,-38),(-7,8,-80))
AHEAD = ((8,0,31),(11,-11,9),(9,-18,-12),(5,-17,-38),(-7,-7,-80))


def make_guide(scene, ears, label):
    data = bpy.data.curves.new(f'R495 local ear arcs | {label}', 'CURVE')
    data.dimensions = '3D'
    for side, ear in enumerate(ears):
        sign = 2 * side - 1
        centre = (ear['front'] + ear['back']) / 2
        for route in (AHEAD, BEHIND):
            xyz = np.asarray(route, dtype='f8') / 1000
            if label == 'tucked' and side == 1:
                xyz[1:4, 1] *= .83
            xyz[:, 0] = sign * (ear['outer'] + xyz[:, 0])
            xyz[:, 1] += centre
            xyz[:, 2] += ear['top']
            spline = data.splines.new('POLY')
            spline.points.add(len(xyz) - 1)
            for point, coordinates in zip(spline.points, xyz):
                point.co = (*tuple(coordinates), 1)
    guide = bpy.data.objects.new(data.name, data)
    scene.collection.objects.link(guide)
    guide['aevrynd_ear_tuck_layout'] = label
    for key in ('outer', 'front', 'back', 'bottom', 'top'):
        guide[f'aevrynd_pinna_{key}_metres'] = [ear[key] for ear in ears]
    guide.hide_render = True
    guide.hide_set(True)
    return guide


def generate(base, ids, guide):
    stations = np.array([[point.co[:3] for point in spline.points] for spline in guide.data.splines], dtype='f8')
    assert stations.shape == (4, 5, 3)
    ears = {key: np.asarray(guide[f'aevrynd_pinna_{key}_metres']) for key in ('outer', 'front', 'back', 'bottom', 'top')}
    two_way = guide['aevrynd_ear_tuck_layout'] == 'divided'
    sides = (base[:, 0, 0] >= 0).astype('i4')
    random = ((ids.astype('u8') * np.uint64(2654435761)) & np.uint64(0xffffffff)).astype('f8') / 4294967296
    result = base.copy()
    weights = np.zeros(len(base), dtype='f4')
    anchors = np.zeros(len(base), dtype='i4')
    groups = np.full(len(base), -1, dtype='i4')
    age = smooth(np.arange(POINTS) / 9)
    geometry = []
    for side in range(2):
        sign = 2 * side - 1
        front, back, bottom, top, outer = (ears[key][side] for key in ('front', 'back', 'bottom', 'top', 'outer'))
        centre_y, centre_z = (front + back) / 2, (top + bottom) / 2
        rows = np.flatnonzero(sides == side)
        current = base[rows].astype('f8')
        z = current[:, :, 2]
        before = (z[:, :-1] >= centre_z) & (z[:, 1:] < centre_z)
        last_crossing = np.where(before, np.arange(POINTS - 1), -1).max(axis=1)
        indices = np.arange(len(rows))
        lower = np.maximum(last_crossing, 0)
        a, b = current[indices, lower], current[indices, lower + 1]
        portion = np.clip((a[:, 2] - centre_z) / np.maximum(a[:, 2] - b[:, 2], 1e-8), 0, 1)
        mid = a + (b - a) * portion[:, None]
        influence = smooth((mid[:, 1] - (front - .012)) / .014) * smooth(((back + .022) - mid[:, 1]) / .020)
        influence *= smooth((sign * mid[:, 0] - (outer - .017)) / .012)
        influence[last_crossing < 0] = 0
        if two_way:
            goes_back = mid[:, 1] >= centre_y - .002 + (random[rows] - .5) * .006
        else:
            goes_back = np.ones(len(rows), dtype=bool)
            # Leave the foremost part of the temple fall as a connected front lock.
            influence *= smooth((mid[:, 1] - (front - .005)) / .016)
        weights[rows] = influence
        anchors[rows[influence > 0]] = lower[influence > 0]
        aperture = smooth((top + .028 - z) / .031) * smooth((z - (bottom - .039)) / .039)
        for branch in range(2):
            active = (influence > 0) & (goes_back == bool(branch))
            group = side * 2 + branch
            groups[rows[active]] = group
            if not active.any():
                continue
            route, _, _, _ = spatial['dense_route'](stations[group])
            sample_height = z[active]
            guide_x = np.interp(sample_height, route[::-1, 2], route[::-1, 0])
            guide_y = np.interp(sample_height, route[::-1, 2], route[::-1, 1])
            coord = current[active].copy()
            relative = mid[active, 1] - centre_y
            deviation = .29 * relative + .006 * (random[rows[active]] - .5)
            delta_y = np.clip(guide_y + deviation[:, None] - coord[:, :, 1], -.032, .041)
            bend = influence[active, None] * aperture[active] * age[None, :]
            coord[:, :, 1] += bend * delta_y
            coord[:, :, 0] += .17 * bend * (guide_x - coord[:, :, 0])
            result[rows[active]] = coord.astype('f4')
        band = (z >= bottom) & (z <= top)
        def profile_proxy(coords):
            return int(np.count_nonzero(band & (sign * coords[:, :, 0] > outer)
                                        & (coords[:, :, 1] > front) & (coords[:, :, 1] < back)))
        protected = (z >= top + .028) | (z <= bottom - .039)
        assert np.array_equal(result[rows][protected], base[rows][protected])
        geometry.append(dict(side=side, protectedControls=int(protected.sum()), baselineProfileProxy=profile_proxy(current),
                             candidateProfileProxy=profile_proxy(result[rows])))
    assert np.isfinite(result).all() and np.array_equal(result[:, 0], base[:, 0])
    assert np.array_equal(result[weights == 0], base[weights == 0])
    return result, weights, anchors, groups, dict(profileProxy=geometry)


def main():
    parent = read_json(PARENT / 'construction-receipt.json')
    assert not DEST.exists() and digest(SOURCE) == parent['source']['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE), load_ui=False, use_scripts=False)
    scene = bpy.context.scene
    control = bpy.data.objects[CONTROL]
    base = positions(control)
    assert array_hash(base) == parent['variants']['staggered']['positionHash']
    keep_guide = parent['variants']['staggered']['guideObject']
    omitted = []
    for obj in list(scene.objects):
        if (obj.type == 'CURVES' and obj != control) or (obj.type == 'CURVE' and obj.name.startswith(('R492 native posterior rails', 'R493 ear-to-nape stations')) and obj.name != keep_guide):
            omitted.append(obj.name)
            data = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if not data.users:
                bank = bpy.data.hair_curves if isinstance(data, bpy.types.Curves) else bpy.data.curves
                bank.remove(data)
    ids = read_attribute(control.data, 'AFN409_CURVE_ID')
    _, _, error = foundation['binding_frame'](control, bpy.data.objects[BODY], base[:, 0])
    ears = measure_ears(bpy.data.objects[BODY])
    variants = {}
    for label in ('tucked', 'divided'):
        guide = make_guide(scene, ears, label)
        bank, weights, joins, groups, local = generate(base, ids, guide)
        obj = control.copy()
        obj.data = control.data.copy()
        obj.name = f'R495 complete hair | {label}'
        obj.data.name = f'R495 locally tucked strands | {label}'
        scene.collection.objects.link(obj)
        set_positions(obj, bank)
        for key, kind, values in (('AEVRYND_EAR_TUCK_WEIGHT', 'FLOAT', weights),
                                  ('AEVRYND_EAR_TUCK_JOIN', 'INT', joins),
                                  ('AEVRYND_EAR_TUCK_GROUP', 'INT', groups)):
            obj.data.attributes.new(key, kind, 'CURVE').data.foreach_set('value', values)
        obj['Aevrynd_Guide_Object'] = guide.name
        variants[label] = dict(object=obj.name, guideObject=guide.name, positionHash=array_hash(bank),
            weightHash=array_hash(weights), joinHash=array_hash(joins), groupHash=array_hash(groups),
            groupCounts=np.bincount(groups + 1).tolist(), changedStrands=int(np.any(bank != base, axis=(1, 2)).sum()), **local)
    active = bpy.data.objects[variants['tucked']['object']]
    for obj in scene.objects:
        if obj.type == 'CURVES':
            obj.hide_render = obj != active
            obj.hide_set(obj != active)
    bpy.ops.object.select_all(action='DESELECT')
    active.select_set(True)
    bpy.context.view_layer.objects.active = active
    bpy.data.texts.new('Aevrynd_R495_Local_Ear_Tuck').write(
        'Two complete unaccepted grooms with editable local ear arcs and intact upper and lower overlap. Original roots and strand identities are preserved.\n')
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 4
    bpy.ops.wm.save_as_mainfile(filepath=str(DEST), compress=True, copy=True)
    assert digest(SOURCE) == parent['source']['sha256']
    write_json(ROOT / 'construction-receipt.json', dict(source=dict(path=str(DEST), sha256=digest(DEST), bytes=DEST.stat().st_size),
        parent=parent['source'], controlObject=control.name, controlPositionHash=array_hash(base), rootHash=array_hash(base[:, 0]),
        bindingMaximumErrorMetres=error, strands=len(base), pointsPerStrand=POINTS, defaultVisible='tucked', variants=variants,
        guideSplinesPerVariant=4, pinnae=ears, historicalBanksInParent=omitted))
    print('R495_SOURCE', str(DEST), flush=True)


if __name__ == '__main__':
    main()
