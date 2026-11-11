"""Author guide paths on the original skin and inspect them before interpolation."""
from pathlib import Path
from hashlib import file_digest
import json

import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parent
PARENT = ROOT.parent / 'r0486-primary-guide-foundation'
SOURCE = PARENT / 'female-next-r0486-primary-guides-UNACCEPTED.blend'
MODES = ('drape', 'sweep')
CONTROL_NAME = 'R486 complete hair | primary guide foundation'


def sha(path):
    with path.open('rb') as stream:
        return file_digest(stream, 'sha256').hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def smooth(value):
    unit = np.clip(value, 0.0, 1.0)
    return unit * unit * (3.0 - 2.0 * unit)


def normalized(vector):
    return vector / max(float(np.linalg.norm(vector)), 1e-10)


def sample_guides(roots, members, count):
    group = roots[members]
    closest = np.full(len(group), np.inf)
    selected = [int(np.argmin(np.linalg.norm(group - group.mean(axis=0), axis=1)))]
    for _ in range(count - 1):
        closest = np.minimum(closest, np.sum((group - group[selected[-1]]) ** 2, axis=1))
        selected.append(int(closest.argmax()))
    return members[selected]


def walk_scalp(root, tree, mode):
    """Follow the actual scalp while directing crown roots toward the fall."""
    points = [root.copy()]
    position = root.copy()
    part = .008 + .003 * np.clip((root[1] + .10) / .070, 0, 1)
    lateral = -1 if root[0] < part else 1
    for step in range(1, 100):
        hit, normal, _, _ = tree.find_nearest(Vector(position))
        skin = np.array(hit)
        normal = np.array(normal)
        if skin[2] <= 1.504 or (skin[1] >= .040 and normal[2] < .30):
            break
        front = float(1.0 - smooth((skin[1] + .033) / .050))
        ear_side = float(smooth((abs(skin[0]) - .040) / .030))
        # The part ends at the crown. Posterior flow is continuous in x.
        cross_head = lateral * .54 * front + .09 * np.tanh(skin[0] / .045) * (1 - front)
        back_sweep = .62 + (.65 if mode == 'sweep' else .10) * ear_side * front
        force = np.array([cross_head, back_sweep, -.85])
        tangent = normalized(force - normal * np.dot(force, normal))
        if np.linalg.norm(tangent) < .8:
            break
        hit, normal, _, _ = tree.find_nearest(Vector(skin + tangent * .0014))
        lift = .005 + .004 * front * (1 - ear_side)
        position = np.array(hit) + np.array(normal) * lift * float(smooth(step / 7))
        points.append(position.copy())
    return np.asarray(points)


def build_guide(root, tree, ear, mode):
    scalp = walk_scalp(root, tree, mode)
    start = scalp[-1]
    side = -1 if root[0] < 0 else 1
    side_flow = float(smooth((abs(start[0]) - .033) / .046))
    front_flow = float(1 - smooth((start[1] - .006) / .049))
    ear_flow = side_flow * front_flow
    azimuth = np.arctan2(start[0], start[1] + .038)
    phase = np.linspace(0, 1, 144)

    # The outer layers end lower. Section lengths vary continuously around the head.
    crown = float(smooth((root[2] - 1.455) / .114))
    end_height = 1.389 - .048 * crown + .009 * np.sin(3 * azimuth + .35)
    end_height += .010 * np.cos(6 * azimuth - .50) * side_flow
    end_height = min(end_height, start[2] - .064)
    z = start[2] + (end_height - start[2]) * phase
    release = smooth(phase / .25)

    # The posterior has one shared fall, with a gentle lateral sweep.
    bend = np.sin(1.65 * np.pi * phase) * smooth(phase / .20)
    x = start[0] * (1.0 - .09 * release)
    x += .006 * np.sin(3 * azimuth + .45) * bend
    x += .005 * (1 - side_flow) * release
    rear = float(smooth((start[1] + .008) / .053))
    y = start[1] + (.017 + .007 * crown) * rear * release
    y += .007 * np.cos(4 * azimuth - .35) * bend

    # Author the side route around the measured pinna, with a smooth return below it.
    # Route width and fore-aft offset vary continuously among the temple guides.
    enter = smooth((ear['top'] + .035 - z) / .033) * release
    leave = smooth((z - (ear['bottom'] - .062)) / .059)
    clearance = float(ear['outer'] + .011) + .006 * crown
    target_x = side * (clearance + .006 * np.sin(azimuth * 4 + .2))
    if mode == 'sweep':
        # Move to the rear of the pinna and then let the fall follow the neck.
        behind = smooth((ear['top'] + .026 - z) / .060) * release
        target_y = ear['back'] + .018 + .020 * smooth((start[1] + .045) / .065)
        y += (target_y - y) * ear_flow * behind
        ear_hold = leave * (1 - .44 * behind)
    else:
        y += (.014 + .010 * side_flow) * ear_flow * release
        ear_hold = leave
    weight = ear_flow * enter * ear_hold
    x += (target_x - x) * weight

    free = np.column_stack((x, y, z))
    # Join with the scalp exit tangent over the first few centimetres.
    if len(scalp) > 4:
        tangent = normalized(scalp[-1] - scalp[-4])
        if tangent[2] < -.22:
            distance = np.clip((start[2] - z) / -tangent[2], 0, .019)
            along = start + tangent * distance[:, None]
            free += (along - free) * (1 - smooth((start[2] - z) / .024))[:, None]
    path = np.concatenate((scalp, free[1:]))
    arc = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))]
    targets = np.linspace(0, arc[-1], 80)
    guide = np.column_stack([np.interp(targets, arc, path[:, axis]) for axis in range(3)])
    guide[0] = root
    return guide.astype('f4')


def create_guide_object(name, bank, radius):
    data = bpy.data.hair_curves.new(name)
    data.add_curves([80] * len(bank))
    data.position_data.foreach_set('vector', bank.ravel())
    width = data.attributes.get('radius') or data.attributes.new('radius', 'FLOAT', 'POINT')
    width.data.foreach_set('value', np.full(bank.shape[:2], radius, dtype='f4').ravel())
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def main():
    receipt = read_json(PARENT / 'construction-receipt.json')
    assert sha(SOURCE) == receipt['source']['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE), load_ui=False, use_scripts=False)
    control = bpy.data.objects[CONTROL_NAME]
    body = bpy.data.objects['R482 archived complete neutral skin']
    vertices = np.empty((len(body.data.vertices), 3), dtype='f4')
    body.data.vertices.foreach_get('co', vertices.ravel())
    polygons = [polygon.vertices[:] for polygon in body.data.polygons]
    tree = BVHTree.FromPolygons(vertices.tolist(), polygons, all_triangles=True)
    positions = np.empty((24831, 80, 3), dtype='f4')
    control.data.position_data.foreach_get('vector', positions.ravel())
    roots = positions[:, 0].copy()
    pinna = vertices[(abs(vertices[:, 0]) > .0752) & (vertices[:, 2] > 1.405) &
                    (vertices[:, 2] < 1.482) & (abs(vertices[:, 1]) < .055)]
    ear = dict(outer=float(abs(pinna[:, 0]).max()), back=float(pinna[:, 1].max()),
               front=float(pinna[:, 1].min()), bottom=float(pinna[:, 2].min()), top=float(pinna[:, 2].max()),
               vertexCount=len(pinna))
    posterior = roots[:, 1] >= .004
    part = .008 + .003 * np.clip((roots[:, 1] + .10) / .070, 0, 1)
    left = roots[:, 0] < part
    domains = np.where(posterior, 2, np.where(left, 0, 1)).astype('i4')
    selected = np.concatenate([sample_guides(roots, np.flatnonzero(domains == region), count)
                               for region, count in enumerate((48, 48, 44))]).astype('i4')
    banks = {mode: np.stack([build_guide(roots[index], tree, ear, mode) for index in selected]) for mode in MODES}
    assert all(np.isfinite(bank).all() and np.array_equal(bank[:, 0], roots[selected]) for bank in banks.values())
    np.savez_compressed(ROOT / 'guide-paths.npz', selected=selected, domains=domains, **banks)
    (ROOT / 'guide-landmarks.json').write_text(json.dumps(dict(source=receipt['source'], ear=ear,
        guidesPerVariant=len(selected), domainCounts=np.bincount(domains).tolist(), posteriorShared=True,
        lateralSamplingRule='neutral skin vertices beyond 75.2 mm in the pinna height window'), indent=2), encoding='utf-8')

    scene = bpy.context.scene
    scene.render.use_persistent_data = False
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 4
    reference = read_json(ROOT.parent / 'r0477-hair-shader-isolation/material-probe.json')['view']
    scene.view_settings.view_transform = reference['transform']
    scene.view_settings.look = reference['look']
    scene.view_settings.exposure = reference['exposure']
    for key, value in reference['cycles'].items():
        setattr(scene.cycles, key, value)
    for obj in bpy.data.objects:
        if obj.type == 'CURVES':
            obj.hide_render = True
    carrier = create_guide_object('R487 guide inspection', banks['drape'], .00039)
    carrier.data.materials.append(control.data.materials[0])
    for view in ('opposite-profile', 'posterior-detail'):
        shot = read_json(ROOT.parent / f'r0470-independent-posterior-locks/shot-A-{view}.json')['shot']
        scene.camera.matrix_world = Matrix(shot['camera'])
        scene.camera.data.type = shot['cameraType']
        scene.camera.data.lens = shot['lens']
        scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = 480, 480, 100
        scene.cycles.samples = min(12, shot['samples'])
        scene.cycles.seed = shot['seed']
        for mode in MODES:
            carrier.data.position_data.foreach_set('vector', banks[mode].ravel())
            carrier.data.update_tag()
            carrier.update_tag()
            scene.render.filepath = str(ROOT / f'guides-{mode}-{view}.png')
            bpy.ops.render.render(write_still=True)
    print('R487_GUIDE_INSPECTION', ear, flush=True)


if __name__ == '__main__':
    main()
