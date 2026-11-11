"""Part the temporal groom around the measured left and right ears."""
from pathlib import Path
import runpy

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parent
PARENT = ROOT.parent / 'r0493-ear-nape-flow'
SOURCE = PARENT / 'female-next-r0493-ear-nape-flow-UNACCEPTED.blend'
DEST = ROOT / 'female-next-r0494-pinna-parting-UNACCEPTED.blend'
parent_author = runpy.run_path(str(PARENT / 'author-r0493.py'))
previous = parent_author['previous']
spatial = parent_author['spatial']
foundation = parent_author['foundation']
digest = parent_author['digest']
read_json = parent_author['read_json']
write_json = parent_author['write_json']
array_hash = parent_author['array_hash']
read_attribute = parent_author['read_attribute']
positions = parent_author['positions']
set_positions = parent_author['set_positions']
smooth = parent_author['smooth']
BODY = parent_author['BODY']
CONTROL = 'R493 complete hair | staggered'
POINTS = 80
RAILS = np.linspace(0, 1, 4)
FAMILIES = ('temple', 'over-ear', 'rear')

# X offsets refer to outer pinna, Y offsets to pinna centre, Z offsets to pinna top.
# Each family has its own entry and release path. Four native rails describe the
# inner/outer limits and intermediate silhouettes in each family.
TEMPLE = (
    ((-4,-16,66),(12,-18,33),(10,-18,-4),(8,-22,-48),(-4,-10,-104)),
    ((-2,-32,70),(15,-36,35),(13,-30,-7),(10,-25,-49),(-1,-13,-93)),
    ((-5,-49,73),(12,-53,36),(13,-48,-7),(11,-40,-48),(-5,-27,-113)),
    ((-11,-68,76),(9,-73,38),(12,-63,-8),(9,-52,-49),(-7,-39,-109)),
)
BRIDGE = (
    ((-5,-18,69),(12,-3,40),(13,20,13),(7,28,-32),(-7,26,-105)),
    ((-9,-11,70),(8,2,43),(10,23,16),(6,35,-35),(-11,38,-113)),
    ((-12,0,74),(6,15,39),(9,34,11),(5,39,-36),(-13,43,-99)),
    ((-16,11,72),(3,29,34),(7,40,7),(-2,49,-42),(-18,49,-111)),
)
REAR = (
    ((-7,4,58),(8,22,31),(10,22,-9),(4,23,-48),(-8,24,-93)),
    ((-10,14,61),(6,29,29),(9,31,-9),(0,34,-47),(-10,29,-112)),
    ((-13,24,63),(3,38,29),(5,41,-9),(-2,42,-47),(-15,38,-102)),
    ((-19,34,62),(-2,45,28),(-1,54,-9),(-9,61,-48),(-22,54,-117)),
)


def measure_ears(skin):
    vertices = np.empty((len(skin.data.vertices), 3), dtype='f4')
    skin.data.vertices.foreach_get('co', vertices.ravel())
    ears = []
    for sign in (-1, 1):
        selected = vertices[(sign * vertices[:, 0] > .0752) & (vertices[:, 2] > 1.405)
                            & (vertices[:, 2] < 1.482) & (abs(vertices[:, 1]) < .055)]
        assert len(selected) > 200
        ears.append(dict(outer=float((sign * selected[:, 0]).max()), front=float(selected[:, 1].min()),
                         back=float(selected[:, 1].max()), bottom=float(selected[:, 2].min()),
                         top=float(selected[:, 2].max()), vertexCount=len(selected)))
    return ears


def make_guide(scene, ears, label):
    data = bpy.data.curves.new(f'R494 pinna guide families | {label}', 'CURVE')
    data.dimensions = '3D'
    for side, ear in enumerate(ears):
        sign = 2 * side - 1
        centre = (ear['front'] + ear['back']) / 2
        width = ear['back'] - ear['front']
        for family, template in enumerate((TEMPLE, BRIDGE, REAR)):
            routes = np.array(template, dtype='f8') / 1000
            if label == 'tuck':
                if family == 0:
                    routes[:, 2:, 1] += np.array([[-1,-1,3],[0,0,6],[1,4,11],[0,0,0]]) * .001
                    routes[:, 4, 2] += np.array([8,9,4,0]) * .001
                elif family == 1:
                    routes[:, 1:3, 2] += np.array([.005,.003])
                    routes[:, 2:, 1] += np.array([.002,.005,.007])
                else:
                    routes[:, 3:, 1] -= np.array([.001,.004])
            routes[:, :, 0] = sign * (ear['outer'] + routes[:, :, 0])
            routes[:, :, 1] += centre
            routes[:, :, 2] += ear['top']
            # Keep the nearest rails off the actual pinna width as it varies by side.
            if family == 0:
                routes[:, 2:4, 1] = np.minimum(routes[:, 2:4, 1], ear['front'] - .004)
            else:
                routes[:, 2:, 1] = np.maximum(routes[:, 2:, 1], centre + width / 2 + .005)
            if side == 1:
                routes[:, 4, 2] += np.array([0, 4, -3, 2]) * .001
            for route in routes:
                spline = data.splines.new('POLY')
                spline.points.add(len(route) - 1)
                for point, xyz in zip(spline.points, route):
                    point.co = (*tuple(xyz), 1)
    guide = bpy.data.objects.new(data.name, data)
    scene.collection.objects.link(guide)
    guide['aevrynd_pinna_layout'] = label
    guide['aevrynd_pinna_front_metres'] = [ear['front'] for ear in ears]
    guide['aevrynd_pinna_back_metres'] = [ear['back'] for ear in ears]
    guide['aevrynd_pinna_top_metres'] = [ear['top'] for ear in ears]
    guide.hide_render = True
    guide.hide_set(True)
    return guide


def route_ownership(roots, guide):
    sides = (roots[:, 0] >= 0).astype('i4')
    front = np.asarray(guide['aevrynd_pinna_front_metres'])[sides]
    back = np.asarray(guide['aevrynd_pinna_back_metres'])[sides]
    top = np.asarray(guide['aevrynd_pinna_top_metres'])[sides]
    height = roots[:, 2] - top
    tucked = guide['aevrynd_pinna_layout'] == 'tuck'
    # The two layouts have different root partings and overhead populations.
    part = front + (.009 if tucked else .017) - (.023 if tucked else .013) * smooth((height - .025) / .067)
    temple = roots[:, 1] < part
    over = (height > (.027 if tucked else .048)) & (roots[:, 1] < back + .028)
    family = np.where(temple, 0, np.where(over, 1, 2))
    u_temple = np.clip((part - roots[:, 1]) / .072, 0, 1)
    u_over = np.clip(.68 * (roots[:, 1] - part) / .052 + .32 * (height - .020) / .090, 0, 1)
    u_rear = np.clip((roots[:, 1] - part) / .077, 0, 1)
    return sides * 3 + family, np.where(temple, u_temple, np.where(over, u_over, u_rear))


def generate(base, normals, ids, radii, owner, tree, guide):
    stations = np.array([[point.co[:3] for point in spline.points] for spline in guide.data.splines], dtype='f8')
    assert stations.shape == (6 * len(RAILS), 5, 3)
    roots = base[:, 0].astype('f8')
    theta = abs(np.arctan2(roots[:, 0], roots[:, 1] + .033))
    weight = smooth((theta - .81) / .32) * (1 - smooth((theta - 2.18) / .29))
    groups, spread = route_ownership(roots, guide)
    groups[weight == 0] = -1
    seed = ((ids.astype('u8') * np.uint64(2654435761)) & np.uint64(0xffffffff)).astype('f8') / 4294967296
    result = base.copy()
    joins = np.zeros(len(base), dtype='i4')
    phase = np.arange(POINTS)[None, :]
    for group in range(6):
        routes = stations[group * len(RAILS):(group + 1) * len(RAILS)]
        field, slopes, path_lengths = previous['build_field'](routes, RAILS)
        members = np.flatnonzero(groups == group)
        for start in range(0, len(members), 640):
            rows = members[start:start + 640]
            attached = roots[rows]
            random = seed[rows]
            u = np.clip(spread[rows] + (random - .5) * .075, 0, 1)
            length = np.interp(u, RAILS, path_lengths)
            nearest = abs(u[:, None] - RAILS).argmin(1)
            entry = np.empty(len(rows))
            for index in np.unique(nearest):
                selected = nearest == index
                entry[selected] = np.interp(attached[selected, 2] - .020, field[index, ::-1, 2],
                                            np.linspace(1, 0, len(field[index])))
            entry = np.maximum(entry, (.005 + .008 * random) / length)
            finish = 1 - (.004 + .014 * random + .006 * (owner[rows] >= 15)) / length
            entry = np.minimum(entry, finish - .032 / length)
            start_point = previous['field_sample'](field, slopes, RAILS, u, entry)
            approach = np.linalg.norm(start_point - attached, axis=1)
            join = np.clip(np.rint(79 * approach / (approach + (finish - entry) * length)), 10, 44).astype('i4')
            along = entry[:, None] + (finish - entry)[:, None] * np.clip((phase - join[:, None]) / (79 - join[:, None]), 0, 1)
            free = previous['field_sample'](field, slopes, RAILS, u[:, None] + np.zeros_like(along), along)
            # Small depth differences preserve the two inherited layers without an ear envelope.
            interior = np.where(owner[rows] >= 15, -.0022, .0008)
            free[:, :, 0] += np.sign(attached[:, 0, None]) * (interior + .0028 * (random - .5))[:, None] * np.sin(np.pi * along) ** 2
            crest = .002 + .0037 * smooth((attached[:, 2] - 1.45) / .113)
            free = spatial['surface_splice'](attached, normals[rows], free, join, crest)
            result[rows] = (base[rows] + weight[rows, None, None] * (free - base[rows])).astype('f4')
            joins[rows] = join
    local = foundation['constrain_upper_shape'](result, np.where(weight > 0, joins + 4, 0), radii, tree)
    assert np.isfinite(result).all() and np.array_equal(result[:, 0], base[:, 0])
    assert np.array_equal(result[weight == 0], base[weight == 0])
    return result, weight.astype('f4'), joins, groups.astype('i4'), local


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
    radii = read_attribute(control.data, 'radius').reshape(len(base), POINTS)
    owner = read_attribute(control.data, 'AEVRYND_SPATIAL_LOCK_ID')
    normals, tree, error = foundation['binding_frame'](control, bpy.data.objects[BODY], base[:, 0])
    ears = measure_ears(bpy.data.objects[BODY])
    variants = {}
    for label in ('drape', 'tuck'):
        guide = make_guide(scene, ears, label)
        bank, weights, joins, groups, local = generate(base, normals, ids, radii, owner, tree, guide)
        obj = control.copy()
        obj.data = control.data.copy()
        obj.name = f'R494 complete hair | {label}'
        obj.data.name = f'R494 pinna-parted strands | {label}'
        scene.collection.objects.link(obj)
        set_positions(obj, bank)
        for key, kind, values in (('AEVRYND_PINNA_PART_WEIGHT', 'FLOAT', weights),
                                  ('AEVRYND_PINNA_PART_JOIN', 'INT', joins),
                                  ('AEVRYND_PINNA_PART_GROUP', 'INT', groups)):
            obj.data.attributes.new(key, kind, 'CURVE').data.foreach_set('value', values)
        obj['Aevrynd_Guide_Object'] = guide.name
        variants[label] = dict(object=obj.name, guideObject=guide.name, positionHash=array_hash(bank),
            weightHash=array_hash(weights), joinHash=array_hash(joins), groupHash=array_hash(groups),
            groupCounts=np.bincount(groups + 1).tolist(), changedStrands=int(np.any(bank != base, axis=(1, 2)).sum()), **local)
    active = bpy.data.objects[variants['tuck']['object']]
    for obj in scene.objects:
        if obj.type == 'CURVES':
            obj.hide_render = obj != active
            obj.hide_set(obj != active)
    bpy.ops.object.select_all(action='DESELECT')
    active.select_set(True)
    bpy.context.view_layer.objects.active = active
    bpy.data.texts.new('Aevrynd_R494_Pinna_Parting').write(
        'Two complete unaccepted grooms with separate editable temple, overhead and rear guide families. Original roots and strand identities are preserved.\n')
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 4
    bpy.ops.wm.save_as_mainfile(filepath=str(DEST), compress=True, copy=True)
    assert digest(SOURCE) == parent['source']['sha256']
    write_json(ROOT / 'construction-receipt.json', dict(source=dict(path=str(DEST), sha256=digest(DEST), bytes=DEST.stat().st_size),
        parent=parent['source'], controlObject=control.name, controlPositionHash=array_hash(base), rootHash=array_hash(base[:, 0]),
        bindingMaximumErrorMetres=error, strands=len(base), pointsPerStrand=POINTS, defaultVisible='tuck', variants=variants,
        guideSplinesPerVariant=6 * len(RAILS), pinnae=ears, guideFamilies=FAMILIES, historicalBanksInParent=omitted))
    print('R494_SOURCE', str(DEST), flush=True)


if __name__ == '__main__':
    main()
