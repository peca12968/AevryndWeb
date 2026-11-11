"""Author two editable orbital-to-malar shape keys on the displayed rigged skin."""
from pathlib import Path
from runpy import run_path

import bpy
import numpy as np
from mathutils.kdtree import KDTree

ROOT = Path(__file__).resolve().parent
PARENT = ROOT.parent / 'r0497-feathered-rear-locks'
SOURCE = PARENT / 'female-next-r0497-feathered-rear-locks-UNACCEPTED.blend'
DEST = ROOT / 'female-next-r0498-orbit-cheek-UNACCEPTED.blend'
prior = run_path(str(PARENT / 'author-r0497.py'))
read_json, write_json, digest, array_hash = (prior[key] for key in ('read_json', 'write_json', 'digest', 'array_hash'))
BODY = 'AFN126_COMPLETE_WOMAN_BODY_AND_ARTIST_HEAD'
GAZE = 'AFN138_ACTUAL_CURRENT_GAZE_RIG'
BLINK = 'R448_Blink'
PHASES = (0.0, .5, 1.0)
KEY_NAMES = {'malar': 'R498 A | Malar support', 'orbital': 'R498 B | Orbit and cheek transition'}


def xyz(data, field='co'):
    result = np.empty((len(data), 3), dtype='f4')
    data.foreach_get(field, result.ravel())
    return result


def evaluated(obj):
    current = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    return xyz(current.data.vertices)


def blink(scene, rig, phase):
    rig[BLINK] = phase
    rig.update_tag()
    scene.frame_set(1)
    bpy.context.view_layer.update()


def protection(body, scene, gaze, scalp, hair):
    basis = xyz(body.data.shape_keys.reference_key.data)
    motion = np.zeros(len(basis), dtype=bool)
    for key in body.data.shape_keys.key_blocks:
        if 'blink' in key.name.lower() or 'lid clearance' in key.name.lower():
            motion |= np.linalg.norm(xyz(key.data) - basis, axis=1) > .000045
    captures = []
    for phase in PHASES:
        blink(scene, gaze, phase)
        captures.append(evaluated(body))
    assert np.max(np.linalg.norm(captures[-1] - captures[0], axis=1)) > .002
    for capture in captures[1:]:
        motion |= np.linalg.norm(capture - captures[0], axis=1) > .000045
    blink(scene, gaze, 0.)

    scalp.data.calc_loop_triangles()
    triangles = np.empty((len(scalp.data.loop_triangles), 3), dtype='i4')
    scalp.data.loop_triangles.foreach_get('vertices', triangles.ravel())
    face_ids = prior['read_attribute'](hair.data, 'AFN409_SKIN_TRIANGLE_ID')
    scalp_ids = np.unique(triangles[face_ids])
    assert len(scalp.data.vertices) == len(body.data.vertices)
    scalp_xyz = xyz(scalp.data.vertices)[scalp_ids]
    scalp_difference = float(np.linalg.norm(scalp_xyz - captures[0][scalp_ids], axis=1).max())
    assert scalp_difference < .001, scalp_difference
    guarded = motion.copy()
    guarded[scalp_ids] = True
    triangles = mesh_winding(body)
    material_index = np.empty(len(body.data.loop_triangles), dtype='i4')
    body.data.loop_triangles.foreach_get('material_index', material_index)
    skin_materials = [index for index, mat in enumerate(body.data.materials)
                      if mat and ('skin' in mat.name.lower() or 'neck' in mat.name.lower())]
    non_skin = np.unique(triangles[~np.isin(material_index, skin_materials)])
    guarded[non_skin] = True
    assert guarded.any()
    return basis, captures, motion, guarded, scalp_ids, scalp_difference


def smooth(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def field(q):
    return smooth(1 - q) ** 1.15


def sculpt(neutral, guarded, label):
    x, y, z = neutral.astype('f8').T
    u = abs(x)
    front = smooth((-y - .081) / .023) * smooth((z - 1.418) / .014)
    front *= smooth((u - .015) / .013) * (1 - smooth((u - .059) / .009))
    front *= 1 - smooth((z - 1.479) / .009)
    if label == 'malar':
        support = field(((u - .044) / .027) ** 2 + ((z - 1.452) / .034) ** 2)
        forward = .0036 * support
        outward = .00085 * support
        vertical = .0006 * support
    else:
        crest = 1.453 + .35 * (u - .041)
        support = field(((u - .042) / .029) ** 2 + ((z - crest) / .030) ** 2)
        orbit = field(((u - .041) / .024) ** 2 + ((z - 1.478) / .017) ** 2)
        side = field(((u - .055) / .018) ** 2 + ((z - 1.435) / .021) ** 2)
        forward = .0042 * support - .0015 * orbit - .00085 * side
        outward = .00110 * support - .00050 * side
        vertical = .0009 * support - .0003 * orbit
    active = np.flatnonzero(front > 0)
    ids = np.flatnonzero(guarded)
    tree = KDTree(len(ids))
    for index in ids:
        tree.insert(neutral[index], int(index))
    tree.balance()
    distances = np.array([tree.find(neutral[index])[2] for index in active])
    front[active] *= smooth((distances - .0030) / .015)
    front[guarded] = 0
    front *= np.where(x > 0, 1.0, .90)
    displacement = front[:, None] * np.stack((np.sign(x) * outward, -forward, vertical), axis=1)
    assert np.isfinite(displacement).all() and not np.any(displacement[guarded])
    return displacement.astype('f4')


def mesh_winding(body):
    body.data.calc_loop_triangles()
    triangles = np.empty((len(body.data.loop_triangles), 3), dtype='i4')
    body.data.loop_triangles.foreach_get('vertices', triangles.ravel())
    return triangles


def triangle_metrics(base, changed, triangles):
    mask = np.any(np.any(base != changed, axis=1)[triangles], axis=1)
    tri = triangles[mask]
    a, b = base[tri].astype('f8'), changed[tri].astype('f8')
    na = np.cross(a[:, 1] - a[:, 0], a[:, 2] - a[:, 0])
    nb = np.cross(b[:, 1] - b[:, 0], b[:, 2] - b[:, 0])
    magnitude = np.linalg.norm(na, axis=1)
    valid = magnitude > 1e-10
    dot = np.sum(na[valid] * nb[valid], axis=1)
    ratios = np.linalg.norm(nb[valid], axis=1) / magnitude[valid]
    stats = dict(editedTriangles=int(mask.sum()), nondegenerateTriangles=int(valid.sum()), minimumAreaRatio=float(ratios.min()),
                 maximumAreaRatio=float(ratios.max()), reversedTriangles=int((dot <= 0).sum()))
    small = ratios < .5
    stats['trianglesBelowHalfArea'] = int(small.sum())
    stats['belowHalfAreaOriginalAreaMaxMm2'] = float(magnitude[valid][small].max() * 5e5) if small.any() else 0.
    return stats


def constrain_triangle_orientation(base, displacement, triangles):
    moved = np.any(displacement != 0, axis=1)
    affected = triangles[moved[triangles].any(axis=1)]
    points = base[affected].astype('f8')
    offsets = displacement[affected].astype('f8')
    e1, e2 = points[:, 1] - points[:, 0], points[:, 2] - points[:, 0]
    d1, d2 = offsets[:, 1] - offsets[:, 0], offsets[:, 2] - offsets[:, 0]
    n0 = np.cross(e1, e2)
    magnitude = np.einsum('ij,ij->i', n0, n0)
    valid = magnitude > 1e-20
    linear = np.einsum('ij,ij->i', n0[valid], (np.cross(d1, e2) + np.cross(e1, d2))[valid]) / magnitude[valid]
    quadratic = np.einsum('ij,ij->i', n0[valid], np.cross(d1, d2)[valid]) / magnitude[valid]
    factor = 1.0
    for b, c in zip(linear, quadratic):
        if abs(c) < 1e-12:
            root = -.82 / b if b < 0 else 2.
            if 0 < root <= factor:
                factor = .98 * root
            continue
        discriminant = b * b - 4 * c * .82
        if discriminant >= 0:
            root = np.sqrt(discriminant)
            for candidate in ((-b - root) / (2 * c), (-b + root) / (2 * c)):
                if 0 < candidate <= factor:
                    factor = .98 * candidate
    return base + (displacement * factor).astype('f4'), factor


def main():
    parent = read_json(PARENT / 'construction-receipt.json')
    assert not DEST.exists() and digest(SOURCE) == parent['source']['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE), load_ui=False, use_scripts=False)
    scene = bpy.context.scene
    body, gaze, scalp = (bpy.data.objects[name] for name in (BODY, GAZE, prior['BODY']))
    hair = bpy.data.objects[parent['variants']['supported']['object']]
    assert not body.hide_render and not hair.hide_render and scalp.hide_render
    assert array_hash(prior['positions'](hair)) == parent['variants']['supported']['positionHash']
    initial_phase = float(gaze[BLINK])
    basis, captures, motion, guarded, scalp_ids, scalp_difference = protection(body, scene, gaze, scalp, hair)
    triangles = mesh_winding(body)
    keys = body.data.shape_keys.key_blocks
    variants = {}
    for label, name in KEY_NAMES.items():
        candidate, scale = constrain_triangle_orientation(basis, sculpt(basis, guarded, label), triangles)
        strain = triangle_metrics(basis, candidate, triangles)
        assert strain['reversedTriangles'] == 0, (label, strain)
        assert np.array_equal(candidate[guarded], basis[guarded])
        delta = np.linalg.norm(candidate - basis, axis=1)
        assert delta.max() > .002 and int((delta > .00001).sum()) > 500
        key = body.shape_key_add(name=name, from_mix=False)
        key.relative_key = body.data.shape_keys.reference_key
        key.data.foreach_set('co', candidate.ravel())
        key.slider_min, key.slider_max, key.value = 0., 1., 0.
        variants[label] = dict(key=name, coordinateHash=array_hash(candidate), changedVertices=int((delta > 0).sum()),
                               maximumLocalDisplacementMetres=float(delta.max()), orientationLimitScale=scale, **strain)
    keys[KEY_NAMES['orbital']].value = 1.
    blink(scene, gaze, initial_phase)
    bpy.ops.object.select_all(action='DESELECT')
    body.select_set(True)
    bpy.context.view_layer.objects.active = body
    body.active_shape_key_index = keys.find(KEY_NAMES['orbital'])
    bpy.ops.wm.save_as_mainfile(filepath=str(DEST), compress=True, copy=True)
    assert digest(SOURCE) == parent['source']['sha256']
    write_json(ROOT / 'construction-receipt.json', dict(source=dict(path=str(DEST), sha256=digest(DEST), bytes=DEST.stat().st_size),
        parent=parent['source'], body=BODY, gaze=GAZE, blinkProperty=BLINK, defaultVisible='orbital', variants=variants,
        frame=1, savedBlink=initial_phase, basisHash=array_hash(basis), topologyHash=array_hash(triangles),
        guardedVertices=int(guarded.sum()), protectedLidVertices=int(motion.sum()), protectedScalpVertices=len(scalp_ids),
        proxyToDisplayedScalpMaximumMetres=scalp_difference, protectedIndexHash=array_hash(np.flatnonzero(guarded)),
        hair=dict(object=hair.name, positionHash=parent['variants']['supported']['positionHash'])))
    print('R498_SOURCE', str(DEST), flush=True)


if __name__ == '__main__':
    main()
