"""Author the upper locks in their attached three-dimensional scalp frames."""
from hashlib import file_digest, sha256
from pathlib import Path
import json

import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parent
PARENT = ROOT.parent / 'r0488-section-shaped-locks'
SOURCE = PARENT / 'female-next-r0488-shaped-lock-layouts-UNACCEPTED.blend'
DEST = ROOT / 'female-next-r0489-crown-attachment-flow-UNACCEPTED.blend'
CONTROL = 'R488 complete hair | bob'
BODY = 'R482 archived complete neutral skin'
POINTS = 80
SETTINGS = {
    'sweep': dict(joinLow=12, joinHigh=22, handle=.92, crest=.0063, partGuide=.33, back=.42, roll=.085),
    'lift': dict(joinLow=13, joinHigh=25, handle=1.14, crest=.0104, partGuide=.53, back=.76, roll=.155),
}


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write_json(path, payload):
    path.write_bytes(json.dumps(payload, indent=2).encode('utf-8'))


def digest(path):
    with path.open('rb') as stream:
        return file_digest(stream, 'sha256').hexdigest()


def array_hash(data):
    return sha256(data.tobytes()).hexdigest()


def read_attribute(data, name):
    attr = data.attributes[name]
    width = {'FLOAT_VECTOR': 3, 'FLOAT2': 2}.get(attr.data_type, 1)
    dtype = 'i4' if attr.data_type == 'INT' else 'f4'
    shape = (len(attr.data), width) if width > 1 else (len(attr.data),)
    output = np.empty(shape, dtype=dtype)
    attr.data.foreach_get('vector' if width > 1 else 'value', output.ravel())
    return output


def positions(obj):
    result = np.empty((len(obj.data.curves), POINTS, 3), dtype='f4')
    obj.data.position_data.foreach_get('vector', result.ravel())
    return result


def set_positions(obj, coordinates):
    obj.data.position_data.foreach_set('vector', coordinates.ravel())
    obj.data.update_tag()
    obj.update_tag()


def normalized(values):
    length = np.linalg.norm(values, axis=-1, keepdims=True)
    return values / np.maximum(length, 1e-12)


def tangent_to(values, normals):
    return values - normals * (values * normals).sum(axis=1, keepdims=True)


def smooth(t):
    value = np.clip(t, 0, 1)
    return value * value * (3 - 2 * value)


def binding_frame(control, skin, root):
    mesh = skin.data
    mesh.calc_loop_triangles()
    vertices = np.empty((len(mesh.vertices), 3), dtype='f4')
    normals = np.empty_like(vertices)
    triangles = np.empty((len(mesh.loop_triangles), 3), dtype='i4')
    mesh.vertices.foreach_get('co', vertices.ravel())
    mesh.vertices.foreach_get('normal', normals.ravel())
    mesh.loop_triangles.foreach_get('vertices', triangles.ravel())
    face = read_attribute(control.data, 'AFN409_SKIN_TRIANGLE_ID')
    weights = read_attribute(control.data, 'AFN409_SKIN_BARYCENTRIC').astype('f8')
    offset = read_attribute(control.data, 'AEVRYND_ROOT_OFFSET_LOCAL').astype('f8')
    assert np.all((face >= 0) & (face < len(triangles)))
    indices = triangles[face]
    attached = vertices[indices].astype('f8')
    u = normalized(attached[:, 1] - attached[:, 0])
    n = normalized(np.cross(u, attached[:, 2] - attached[:, 0]))
    v = np.cross(n, u)
    surface = (attached * weights[:, :, None]).sum(1)
    reconstructed = surface + u * offset[:, 0, None] + v * offset[:, 1, None] + n * offset[:, 2, None]
    binding_error = float(np.linalg.norm(reconstructed - root, axis=1).max())
    assert binding_error < 8e-7, binding_error
    smoothed = normalized((normals[indices].astype('f8') * weights[:, :, None]).sum(1))
    smoothed = np.where(((smoothed * n).sum(1) > .45)[:, None], smoothed, n)
    tree = BVHTree.FromPolygons(vertices.tolist(), triangles.tolist(), all_triangles=True)
    return smoothed, tree, binding_error


def departure_shape(base, normals, lock_ids, settings):
    root = base[:, 0].astype('f8')
    high = smooth((root[:, 2] - 1.480) / .081)
    join = np.rint(settings['joinLow'] + (settings['joinHigh'] - settings['joinLow']) * high).astype('i4')
    row = np.arange(len(root))
    end = base[row, join].astype('f8')
    chord = end - root
    distance = np.linalg.norm(chord, axis=1)
    assert float(distance.min()) > .004
    forward = normalized(tangent_to(chord, normals))
    part_x = .009 + .004 * smooth((root[:, 1] + .095) / .055)
    side = np.tanh((root[:, 0] - part_x) / .009)
    preference = np.column_stack((side, np.full(len(root), settings['back']), np.zeros(len(root))))
    preference = normalized(tangent_to(preference, normals))
    agreement = (forward * preference).sum(1)
    bias = settings['partGuide'] * high * smooth((agreement + .45) / .85)
    tangent = normalized(forward * (1 - bias[:, None]) + preference * bias[:, None])
    binormal = normalized(np.cross(normals, tangent))
    exit_direction = normalized(base[row, join + 1].astype('f8') - base[row, join - 1])
    slope = distance[:, None] * settings['handle'] * tangent + (.0038 + .003 * high)[:, None] * normals
    exit_slope = distance[:, None] * exit_direction
    # Locks have separate but overlapping crest positions around the crown.
    lock_phase = lock_ids * .91 + root[:, 1] * 31.0
    lift = settings['crest'] * (.14 + .86 * high) * (.83 + .17 * np.sin(lock_phase))
    lift *= (1 + .17 * side)
    twist = settings['roll'] * distance * high * np.sin(lock_phase + .9)
    result = base.copy()
    for index in range(1, int(join.max())):
        active = index < join
        t = index / join[active].astype('f8')
        t2, t3 = t * t, t * t * t
        hermite = ((2 * t3 - 3 * t2 + 1)[:, None] * root[active]
                   + (t3 - 2 * t2 + t)[:, None] * slope[active]
                   + (-2 * t3 + 3 * t2)[:, None] * end[active]
                   + (t3 - t2)[:, None] * exit_slope[active])
        envelope = np.sin(np.pi * t) ** 2
        hermite += (envelope * lift[active])[:, None] * normals[active]
        hermite += (envelope * twist[active] * (1 - .7 * t))[:, None] * binormal[active]
        result[active, index] = hermite.astype('f4')
    return result, join


def constrain_upper_shape(coordinates, join, radii, tree):
    """Use the measured skin only where a new upper control falls inside its margin."""
    changed = 0
    maximum = 0.0
    for index in range(1, int(join.max())):
        for row in np.flatnonzero(index < join):
            point = Vector(coordinates[row, index])
            required = float(radii[row, index]) + .00012
            initial = point.copy()
            for _ in range(3):
                nearest, normal, _, distance = tree.find_nearest(point)
                signed = distance if (point - nearest).dot(normal) >= 0 else -distance
                if signed >= required:
                    break
                point = nearest + normal * (required + .00002)
            delta = (point - initial).length
            if delta:
                coordinates[row, index] = point[:]
                changed += 1
                maximum = max(maximum, delta)
    return dict(locallyConstrainedControls=changed, maximumLocalCorrectionMetres=maximum)


def create_bank(base, normals, lock_ids, radii, tree, settings):
    coordinates, join = departure_shape(base, normals, lock_ids, settings)
    local = constrain_upper_shape(coordinates, join, radii, tree)
    assert np.isfinite(coordinates).all() and np.array_equal(coordinates[:, 0], base[:, 0])
    after_join = np.arange(POINTS)[None] >= join[:, None]
    assert np.array_equal(coordinates[after_join], base[after_join])
    return coordinates, join, local


def main():
    parent = read_json(PARENT / 'continuation.json')
    assert not DEST.exists() and digest(SOURCE) == parent['source']['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE), load_ui=False, use_scripts=False)
    control = bpy.data.objects[CONTROL]
    skin = bpy.data.objects[BODY]
    assert control.matrix_world == Matrix.Identity(4) and skin.matrix_world == Matrix.Identity(4)
    # Historical alternatives stay in the immutable parent and its verified Git LFS archive.
    removed = []
    for obj in list(bpy.context.scene.objects):
        if obj.type == 'CURVES' and obj != control:
            removed.append(obj.name)
            data = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if not data.users:
                bpy.data.hair_curves.remove(data)
    control.hide_set(False)
    base = positions(control)
    expected = read_json(PARENT / 'construction-receipt.json')['variants']['bob']['positionHash']
    assert array_hash(base) == expected
    normals, tree, error = binding_frame(control, skin, base[:, 0])
    radii = read_attribute(control.data, 'radius').reshape(len(base), POINTS)
    lock_ids = read_attribute(control.data, 'AEVRYND_LOCK_ID')
    ids = read_attribute(control.data, 'AFN409_CURVE_ID')
    known = int(np.flatnonzero(ids == 5535)[0])
    variants = {}
    scene = bpy.context.scene
    for name, settings in SETTINGS.items():
        bank, join, local = create_bank(base, normals, lock_ids, radii, tree, settings)
        obj = control.copy()
        obj.data = control.data.copy()
        obj.name = f'R489 complete hair | {name}'
        obj.data.name = f'R489 full rest strands | {name}'
        scene.collection.objects.link(obj)
        set_positions(obj, bank)
        obj['Aevrynd_Crown_Departure_Settings'] = json.dumps(settings)
        attr = obj.data.attributes.new('AEVRYND_CROWN_JOIN_POINT', 'INT', 'CURVE')
        attr.data.foreach_set('value', join)
        variants[name] = dict(object=obj.name, positionHash=array_hash(bank), joinHash=array_hash(join),
            curve5535=bank[known, :6].tolist(), joinRange=[int(join.min()), int(join.max())], **local)
    active = bpy.data.objects[variants['sweep']['object']]
    for obj in scene.objects:
        if obj.type == 'CURVES':
            obj.hide_render = obj != active
            obj.hide_set(obj != active)
    bpy.ops.object.select_all(action='DESELECT')
    active.select_set(True)
    bpy.context.view_layer.objects.active = active
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 4
    bpy.data.texts.new('Aevrynd_R489_Crown_Departure').write(
        'Two unaccepted complete rest grooms. The upper routes use exact triangle attachment frames. '
        'R488 A is included for comparison. Earlier hidden alternatives are preserved in the parent archive.\n')
    bpy.ops.wm.save_as_mainfile(filepath=str(DEST), compress=True, copy=True)
    assert digest(SOURCE) == parent['source']['sha256']
    receipt = dict(source=dict(path=str(DEST), sha256=digest(DEST), bytes=DEST.stat().st_size),
        parent=parent['source'], controlObject=control.name, controlPositionHash=expected,
        rootHash=array_hash(base[:, 0]), bindingMaximumErrorMetres=error, strands=len(base),
        pointsPerStrand=POINTS, variants=variants, defaultVisible='sweep',
        historicalCurvesInParent=removed)
    write_json(ROOT / 'construction-receipt.json', receipt)
    print('R489_SOURCE', receipt['source'], flush=True)


if __name__ == '__main__':
    main()
