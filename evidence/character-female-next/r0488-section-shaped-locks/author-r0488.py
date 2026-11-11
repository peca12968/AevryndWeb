"""Shape full locks in an anatomical chart, with explicit authored stations."""
from pathlib import Path
from hashlib import file_digest, sha256
import json

import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parent
PARENT = ROOT.parent / 'r0487-continuous-posterior-groom'
SOURCE = PARENT / 'female-next-r0487-posterior-and-ear-routes-UNACCEPTED.blend'
DEST = ROOT / 'female-next-r0488-shaped-lock-layouts-UNACCEPTED.blend'
CONTROL = 'R487 complete hair | sweep'
BODY = 'R482 archived complete neutral skin'
CENTER_Y = -.033
POINTS = 80
LEVELS = np.array([1.320, 1.350, 1.385, 1.420, 1.455, 1.488, 1.515, 1.545, 1.573])
RADII_SIDE = np.array([.083, .091, .093, .097, .097, .090, .075, .057, .006])
RADII_REAR = np.array([.083, .092, .095, .094, .093, .088, .078, .060, .006])

# Each row gives the lock's angle, middle turn, tip turn, crest relief and tip height.
# Angles are degrees. Relief and height are metres. The two layouts are authored
# independently so the stagger and fall direction can be compared at full density.
LAYOUTS = {
    'bob': [
        [-119, -9, 3, .006, 1.354], [-104, -4, 8, .005, 1.336],
        [-89, 6, 13, .006, 1.343], [-73, 8, 10, .004, 1.358],
        [-55, 4, -3, .005, 1.363], [-37, 3, -7, .004, 1.347],
        [-19, -3, -6, .005, 1.355], [-1, -4, 2, .004, 1.369],
        [17, 4, 7, .006, 1.350], [35, 7, 4, .004, 1.361],
        [52, 6, -2, .006, 1.345], [68, -4, -7, .005, 1.356],
        [84, -7, -12, .005, 1.365], [101, -8, -6, .005, 1.351],
        [116, -4, -14, .004, 1.365],
    ],
    'layers': [
        [-120, 6, -2, .006, 1.338], [-105, 10, 4, .007, 1.362],
        [-90, 11, 9, .008, 1.330], [-74, 8, 0, .006, 1.359],
        [-57, 2, -8, .006, 1.344], [-39, -5, -4, .008, 1.333],
        [-21, -8, -9, .006, 1.360], [-4, -4, -10, .005, 1.343],
        [14, 6, -2, .007, 1.333], [32, 9, 5, .006, 1.355],
        [49, 6, -5, .007, 1.341], [66, -2, -10, .005, 1.369],
        [82, -10, -12, .007, 1.351], [98, -13, -18, .006, 1.370],
        [113, -12, -22, .006, 1.379],
    ],
}


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def digest(path):
    with path.open('rb') as stream:
        return file_digest(stream, 'sha256').hexdigest()


def geometry_hash(positions):
    return sha256(positions.tobytes()).hexdigest()


def smooth(value):
    t = np.clip(value, 0.0, 1.0)
    return t * t * (3 - 2 * t)


def read_positions(obj):
    positions = np.empty((len(obj.data.curves), POINTS, 3), dtype='f4')
    obj.data.position_data.foreach_get('vector', positions.ravel())
    return positions


def set_positions(obj, positions):
    obj.data.position_data.foreach_set('vector', positions.ravel())
    obj.data.update_tag()
    obj.update_tag()


def get_curve_ids(obj):
    curve_ids = np.empty(len(obj.data.curves), dtype='i4')
    obj.data.attributes['AFN409_CURVE_ID'].data.foreach_get('value', curve_ids)
    return curve_ids


def skin_tree(obj):
    mesh = obj.data
    return BVHTree.FromPolygons([vertex.co[:] for vertex in mesh.vertices],
                                [face.vertices[:] for face in mesh.polygons], all_triangles=True)


def measure_skin(tree):
    """Measure exterior skin along horizontal rays in the aligned body frame."""
    heights = np.linspace(1.315, 1.575, 157)
    angles = np.linspace(-np.pi, np.pi, 241)
    radii = np.zeros((len(heights), len(angles)), dtype='f4')
    directions = [Vector((np.sin(angle), np.cos(angle), 0)) for angle in angles]
    reach = .150
    for row, height in enumerate(heights):
        origin = Vector((0, CENTER_Y, height))
        for column, direction in enumerate(directions):
            hit, _, _, distance = tree.ray_cast(origin + direction * reach, -direction, reach)
            if hit is not None:
                radii[row, column] = reach - distance
    assert radii.max() < reach and radii.max() > .085
    return heights, angles, radii


def interpolate_skin(heights, angles, atlas, z, phi):
    wrapped = (phi + np.pi) % (2 * np.pi) - np.pi
    u = (wrapped - angles[0]) * (len(angles) - 1) / (angles[-1] - angles[0])
    v = np.clip((z - heights[0]) * (len(heights) - 1) / (heights[-1] - heights[0]), 0, len(heights) - 1)
    ui = np.minimum(u.astype('i4'), len(angles) - 2)
    vi = np.minimum(v.astype('i4'), len(heights) - 2)
    u -= ui
    v -= vi
    lower = atlas[vi, ui] * (1 - u) + atlas[vi, ui + 1] * u
    upper = atlas[vi + 1, ui] * (1 - u) + atlas[vi + 1, ui + 1] * u
    return lower * (1 - v) + upper * v


def shaped_radius(z, radii):
    """Cubic interpolation with continuous tangent across the authored heights."""
    slopes = np.gradient(radii, LEVELS)
    index = np.clip(np.searchsorted(LEVELS, z) - 1, 0, len(LEVELS) - 2)
    width = LEVELS[index + 1] - LEVELS[index]
    t = np.clip((z - LEVELS[index]) / width, 0, 1)
    t2, t3 = t * t, t * t * t
    return ((2 * t3 - 3 * t2 + 1) * radii[index] + (t3 - 2 * t2 + t) * width * slopes[index]
            + (-2 * t3 + 3 * t2) * radii[index + 1] + (t3 - t2) * width * slopes[index + 1])


def construct(roots, curve_ids, layout, atlas):
    """Each follicle follows one lock through exterior angular coordinates."""
    stations = np.asarray(layout, dtype='f8')
    phi_root = np.arctan2(roots[:, 0], roots[:, 1] - CENTER_Y).astype('f8')
    part = .009 + .004 * smooth((roots[:, 1] + .095) / .055)
    front = abs(phi_root) > 2.48
    phi_root -= (front & (phi_root > 0) & (roots[:, 0] < part)) * (2 * np.pi)
    phi_root += (front & (phi_root < 0) & (roots[:, 0] >= part)) * (2 * np.pi)
    height = roots[:, 2].astype('f8')
    layer = smooth((height - 1.446) / .114)
    extent = abs(phi_root)
    target = np.sign(phi_root) * np.where(extent > 1.70, 1.70 + .28 * (extent - 1.70), extent)
    # Different elevations feed staggered neighbouring locks. The rear has one continuous chart.
    offset = .14 * (layer - .5)
    centers = np.radians(stations[:, 0])
    owner = abs(target[:, None] - (centers[None] + offset[:, None])).argmin(axis=1).astype('i4')
    center = centers[owner] + offset
    lane = target - center
    crest = np.exp(-(lane / .14) ** 2)
    noise = ((curve_ids.astype('u8') * np.uint64(2654435761)) & np.uint64(0xFFFFFFFF)).astype('f8') / 4294967296.0
    selected = stations[owner]
    finish = selected[:, 4] + .024 * (1 - layer) + .016 * np.sin(7 * lane + .25) + .012 * (noise - .5)
    finish = np.minimum(finish, height - .058)
    phase = np.linspace(0, 1, POINTS)[None]
    positions = np.empty((len(roots), POINTS, 3), dtype='f4')
    for start in range(0, len(roots), 1024):
        rows = slice(start, start + 1024)
        drop = (height[rows] - finish[rows])[:, None] * (phase - .075 * np.sin(np.pi * phase))
        z = height[rows, None] - drop
        peel = smooth(drop / (.035 + .018 * layer[rows, None]))
        fall = smooth((1.513 - z) / .147)
        middle_turn = np.radians(selected[rows, 1, None]) * np.sin(np.pi * fall)
        tip_turn = np.radians(selected[rows, 2, None]) * fall
        angle = phi_root[rows, None] + peel * (target[rows, None] - phi_root[rows, None])
        angle += (middle_turn + tip_turn) * peel
        angle -= .10 * lane[rows, None] * np.sin(np.pi * fall) * peel
        skin = interpolate_skin(*atlas, z, angle)
        side_mix = np.sin(angle) ** 2
        silhouette = shaped_radius(z, RADII_REAR) * (1 - side_mix) + shaped_radius(z, RADII_SIDE) * side_mix
        loft = smooth((1.529 - z) / .050)
        relief = selected[rows, 3, None] * crest[rows, None]
        wave = .45 + .55 * np.sin(2 * np.pi * fall + owner[rows, None] * .63)
        silhouette += (relief * wave + .011 * (layer[rows, None] - .62)) * smooth(drop / .035)
        crown = skin + .003 + .006 * layer[rows, None]
        radius = crown + (silhouette - crown) * loft
        radius = np.maximum(radius, skin + .0018)
        root_radius = np.hypot(roots[rows, 0], roots[rows, 1] - CENTER_Y).astype('f8')
        radius += (root_radius - radius[:, 0])[:, None] * (1 - smooth(drop / .017))
        positions[rows] = np.stack((radius * np.sin(angle), CENTER_Y + radius * np.cos(angle), z), axis=2)
    positions[:, 0] = roots
    return positions, owner


def set_integer_attribute(data, name, values):
    attribute = data.attributes.get(name) or data.attributes.new(name, 'INT', 'CURVE')
    attribute.data.foreach_set('value', np.asarray(values, dtype='i4'))


def create_lock_guides(name, positions, lock_ids, curve_ids):
    """Save two representative native curves per lock as visual authoring guides."""
    representatives = []
    for lock in np.unique(lock_ids):
        members = np.flatnonzero(lock_ids == lock)
        ranked = members[np.argsort(positions[members, 0, 2], kind='stable')]
        ranks = (np.array([.30, .72]) * (len(ranked) - 1)).astype('i4')
        representatives.extend(ranked[ranks].tolist())
    indices = np.asarray(representatives, dtype='i4')
    data = bpy.data.hair_curves.new(name)
    data.add_curves([POINTS] * len(indices))
    data.position_data.foreach_set('vector', positions[indices].ravel())
    radius = data.attributes.get('radius') or data.attributes.new('radius', 'FLOAT', 'POINT')
    radius.data.foreach_set('value', np.full(len(indices) * POINTS, .00020, dtype='f4'))
    set_integer_attribute(data, 'AEVRYND_LOCK_ID', lock_ids[indices])
    set_integer_attribute(data, 'AEVRYND_SOURCE_CURVE_ID', curve_ids[indices])
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    return obj, indices


def main():
    previous = read_json(PARENT / 'continuation.json')
    assert not DEST.exists() and digest(SOURCE) == previous['source']['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE), load_ui=False, use_scripts=False)
    control = bpy.data.objects[CONTROL]
    skin = bpy.data.objects[BODY]
    assert control.matrix_world == Matrix.Identity(4) and skin.matrix_world == Matrix.Identity(4)
    roots = read_positions(control)[:, 0].copy()
    curve_ids = get_curve_ids(control)
    atlas = measure_skin(skin_tree(skin))
    atlas_path = ROOT / 'neutral-skin-ray-atlas.npz'
    np.savez_compressed(atlas_path, heights=atlas[0], angles=atlas[1], radius=atlas[2])
    variants = {}
    scene = bpy.context.scene
    for label, layout in LAYOUTS.items():
        positions, owners = construct(roots, curve_ids, layout, atlas)
        assert np.array_equal(positions[:, 0], roots) and np.isfinite(positions).all()
        obj = control.copy()
        obj.data = control.data.copy()
        obj.name = f'R488 complete hair | {label}'
        obj.data.name = f'R488 section-shaped strands | {label}'
        scene.collection.objects.link(obj)
        set_positions(obj, positions)
        stale = obj.data.attributes.get('AEVRYND_PRIMARY_GUIDE')
        if stale:
            obj.data.attributes.remove(stale)
        set_integer_attribute(obj.data, 'AEVRYND_LOCK_ID', owners)
        obj['Aevrynd_Lock_Stations'] = json.dumps(layout)
        guides, indices = create_lock_guides(f'R488 lock representatives | {label}', positions, owners, curve_ids)
        guides.data.materials.append(control.data.materials[0])
        variants[label] = dict(object=obj.name, guideObject=guides.name, positionHash=geometry_hash(positions),
            ownershipHash=sha256(owners.tobytes()).hexdigest(), guides=len(indices),
            guideSourceIDs=curve_ids[indices].tolist(), strandCounts=np.bincount(owners, minlength=len(layout)).tolist(),
            tipHeightMetres=np.quantile(positions[:, -1, 2], [0, .25, .5, .75, 1]).tolist())
    active = bpy.data.objects[variants['layers']['object']]
    for obj in scene.objects:
        if obj.type == 'CURVES':
            obj.hide_render = obj != active
            obj.hide_set(obj != active)
    bpy.ops.object.select_all(action='DESELECT')
    active.select_set(True)
    bpy.context.view_layer.objects.active = active
    text = bpy.data.texts.new('Aevrynd_R488_Lock_Stations')
    text.write('Two unaccepted study layouts. Each render strand keeps its original root, radius and binding. '
               'Aevrynd_Lock_Stations stores each layout. The native lock representative objects visualize '
               'the construction. Regeneration uses the external Blender Python script and skin atlas.\n')
    shot = read_json(ROOT.parent / 'r0470-independent-posterior-locks/shot-A-face.json')['shot']
    scene.camera.matrix_world = Matrix(shot['camera'])
    scene.camera.data.type = shot['cameraType']
    scene.camera.data.lens = shot['lens']
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 4
    bpy.ops.wm.save_as_mainfile(filepath=str(DEST), compress=True, copy=True)
    receipt = dict(source=dict(path=str(DEST), sha256=digest(DEST), bytes=DEST.stat().st_size),
        parent=previous['source'], controlObject=control.name, variants=variants, curveCount=len(roots),
        pointsPerCurve=POINTS, rootHash=geometry_hash(roots), chartOriginYMetres=CENTER_Y,
        atlas=dict(path=str(atlas_path), sha256=digest(atlas_path), shape=list(atlas[2].shape)),
        defaultVisible='layers', layoutFields=['angle_deg', 'middle_turn_deg', 'tip_turn_deg', 'crest_m', 'tip_height_m'])
    (ROOT / 'construction-receipt.json').write_bytes(json.dumps(receipt, indent=2).encode('utf-8'))
    print('R488_SOURCE', receipt['source'], flush=True)


if __name__ == '__main__':
    main()
