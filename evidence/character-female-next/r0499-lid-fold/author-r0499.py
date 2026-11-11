"""Author closure-driven corrections for the measured temporal eyelid fold."""
from heapq import heappop, heappush
from pathlib import Path
from runpy import run_path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

ROOT = Path(__file__).resolve().parent
PARENT = ROOT.parent / 'r0498-orbit-cheek'
SOURCE = PARENT / 'female-next-r0498-orbit-cheek-UNACCEPTED.blend'
DEST = ROOT / 'female-next-r0499-lid-fold-UNACCEPTED.blend'
previous = run_path(str(PARENT / 'preview-r0498.py'))
author = previous['author']
read_json, write_json, digest, array_hash = (author[key] for key in ('read_json', 'write_json', 'digest', 'array_hash'))
KEY_NAMES = {'relaxed': 'R499 A | Upper lid curvature', 'profile': 'R499 B | Upper lid depth profile'}
CONTROL = 'R499_Lid_Fold_Layout'
MODES = ('control', *KEY_NAMES)
PHASES = (0., .5, .82, 1.)


def driver(key, gaze, mode):
    expression = 'min(1,max(0,(blink-.54)/.46))'
    settings = key.driver_add('value').driver
    for name, prop in (('mode', CONTROL), ('blink', author['BLINK'])):
        variable = settings.variables.new()
        variable.name = name
        variable.type = 'SINGLE_PROP'
        variable.targets[0].id = gaze
        variable.targets[0].data_path = f'["{prop}"]'
    settings.expression = f'(mode=={MODES.index(mode)})*{expression}**2*(3-2*{expression})'


def activate(scene, gaze, mode, phase, frame=1):
    gaze[CONTROL] = MODES.index(mode)
    gaze[author['BLINK']] = phase
    gaze.update_tag()
    scene.frame_set(int(frame), subframe=frame-int(frame))
    bpy.context.view_layer.update()


def triangle_data(mesh):
    mesh.calc_loop_triangles()
    tri = np.empty((len(mesh.loop_triangles), 3), dtype='i4')
    materials = np.empty(len(tri), dtype='i4')
    mesh.loop_triangles.foreach_get('vertices', tri.ravel())
    mesh.loop_triangles.foreach_get('material_index', materials)
    return tri, materials


def domain(body, gaze, scene, scalp, hair, wet, lashes, probe):
    author['blink'](scene, gaze, 1.)
    closed = author['evaluated'](body)
    basis = author['xyz'](body.data.shape_keys.reference_key.data)
    tri, materials = triangle_data(body.data)
    skin_slots = [index for index, mat in enumerate(body.data.materials) if mat and 'skin' in mat.name.lower()]
    eligible = np.zeros(len(closed), dtype=bool)
    eligible[tri[np.isin(materials, skin_slots)]] = True
    eligible[tri[~np.isin(materials, skin_slots)]] = False
    x, y, z = closed.T
    eligible &= (abs(x) >= .025) & (abs(x) <= .060) & (y <= -.092) & (z >= 1.455) & (z <= 1.481)

    lash_vertices = np.unique(np.concatenate([author['prior']['read_attribute'](lashes.data, f'R455 Skin Vertex {i}')
                                              for i in range(3)]))
    assert lash_vertices.min() >= 0 and lash_vertices.max() < len(closed)
    scalp_tri, _ = triangle_data(scalp.data)
    bind = author['prior']['read_attribute'](hair.data, 'AFN409_SKIN_TRIANGLE_ID')
    scalp_vertices = np.unique(scalp_tri[bind])
    cheek = np.any(author['xyz'](body.data.shape_keys.key_blocks[previous['KEY_NAMES']['orbital']].data) != basis, axis=1)
    guard = cheek.copy()
    guard[lash_vertices] = True
    guard[scalp_vertices] = True
    wet_coordinates = author['evaluated'](wet)
    wet_tree = KDTree(len(wet_coordinates))
    for index, value in enumerate(wet_coordinates):
        wet_tree.insert(value, index)
    wet_tree.balance()
    possible = np.flatnonzero(eligible)
    wet_gap = np.array([wet_tree.find(closed[index])[2] for index in possible])
    guard[possible[wet_gap < .00072]] = True
    eligible[guard] = False

    edges = np.empty((len(body.data.edges), 2), dtype='i4')
    body.data.edges.foreach_get('vertices', edges.ravel())
    active_edges = edges[eligible[edges].any(1)]
    graph = [[] for _ in closed]
    for a, b in active_edges:
        length = max(.000045, float(np.linalg.norm(closed[a] - closed[b])))
        graph[a].append((b, length))
        graph[b].append((a, length))
    sample = [row for row in probe['rays']['1.0'] if row['pixel'][0] in (196,204,212,428,436,444)
              and row['pixel'][1] in (337,342,347)]
    seeds = np.unique([index for row in sample for index in row['vertices'] if eligible[index]])
    assert len(seeds) >= 8
    distance = np.full(len(closed), np.inf)
    frontier = []
    for index in seeds:
        distance[index] = 0.
        heappush(frontier, (0., index))
    while frontier:
        cost, a = heappop(frontier)
        if cost != distance[a]:
            continue
        for b, step in graph[a]:
            route = cost + step
            if eligible[b] and route < min(.010, distance[b]):
                distance[b] = route
                heappush(frontier, (route, b))
    selected = np.flatnonzero(distance < .010)
    guard_tree = KDTree(len(lash_vertices))
    for index in lash_vertices:
        guard_tree.insert(closed[index], int(index))
    guard_tree.balance()
    lash_distance = np.array([guard_tree.find(closed[index])[2] for index in selected])
    weights = np.zeros(len(closed), dtype='f8')
    weights[selected] = author['smooth'](1 - distance[selected] / .010) * author['smooth']((lash_distance - .00025) / .0014)
    assert np.count_nonzero(weights) >= 60
    return basis, closed, tri, graph, weights, seeds, guard, lash_vertices


def relax(closed, graph, weights):
    raw = closed[:, 1].astype('f8')
    depth = raw.copy()
    active = np.flatnonzero(weights > 0)
    adjacent = [np.array([i for i, _ in graph[index]], dtype='i4') for index in active]
    blend = [1 / np.array([gap for _, gap in graph[index]]) for index in active]
    for _ in range(13):
        average = np.array([np.average(depth[ids], weights=w) for ids, w in zip(adjacent, blend, strict=True)])
        depth[active] += .42 * weights[active] * (average - depth[active])
    return np.clip(depth-raw, -.00125, .00125)


def profile(closed, weights):
    result = np.zeros(len(closed), dtype='f8')
    for sign in (-1, 1):
        rows = np.flatnonzero((weights > 0) & (sign * closed[:, 0] > 0))
        local = closed[rows].astype('f8')
        x = (abs(local[:, 0]) - .044) / .009
        z = (local[:, 2] - 1.466) / .008
        features = np.column_stack((np.ones(len(rows)), x, z, x*x, x*z, z*z))
        border = np.sqrt(np.maximum(.08, 1 - weights[rows]))
        fit, *_ = np.linalg.lstsq(features * border[:, None], local[:, 1] * border, rcond=None)
        result[rows] = np.clip(features @ fit - local[:, 1], -.00135, .00135) * (.83 * weights[rows])
    return result


def main():
    parent = read_json(PARENT / 'construction-receipt.json')
    probe = read_json(ROOT / 'fold-probe.json')
    assert not DEST.exists() and digest(SOURCE) == parent['source']['sha256'] == probe['source']['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE), load_ui=False, use_scripts=False)
    scene = bpy.context.scene
    body, gaze = (bpy.data.objects[parent[name]] for name in ('body', 'gaze'))
    scalp = bpy.data.objects[author['prior']['BODY']]
    hair = bpy.data.objects[parent['hair']['object']]
    wet, lashes = (bpy.data.objects[name] for name in previous['LAYERS'][2:])
    basis, closed, triangles, graph, weights, seeds, guard, lash_vertices = domain(body, gaze, scene, scalp, hair, wet, lashes, probe)
    variants = {}
    gaze[CONTROL] = 0
    gaze.id_properties_ui(CONTROL).update(min=0, max=2, description='0 original, 1 relaxed upper lid, 2 reconstructed depth profile')
    for label, shape in (('relaxed', relax(closed, graph, weights)), ('profile', profile(closed, weights))):
        delta = np.zeros_like(basis)
        delta[:, 1] = shape.astype('f4')
        limited, scale = author['constrain_triangle_orientation'](closed, delta, triangles)
        candidate = basis + (limited - closed)
        assert np.array_equal(candidate[guard], basis[guard]) and np.array_equal(candidate[lash_vertices], basis[lash_vertices])
        edited = np.any(candidate != basis, axis=1)
        magnitude = np.linalg.norm(candidate - basis, axis=1)
        assert int(edited.sum()) >= 50 and magnitude.max() > .00023, (label, int(edited.sum()), float(magnitude.max()), scale)
        key = body.shape_key_add(name=KEY_NAMES[label], from_mix=False)
        key.relative_key = body.data.shape_keys.reference_key
        key.data.foreach_set('co', candidate.ravel())
        driver(key, gaze, label)
        variants[label] = dict(key=key.name, coordinateHash=array_hash(candidate), changedVertices=int(edited.sum()),
            maximumLocalDisplacementMetres=float(magnitude.max()), closedOrientationLimitScale=scale,
            closedPatch=author['triangle_metrics'](closed, limited, triangles))
    activate(scene, gaze, 'profile', 0.)
    bpy.ops.object.select_all(action='DESELECT')
    body.select_set(True)
    bpy.context.view_layer.objects.active = body
    body.active_shape_key_index = body.data.shape_keys.key_blocks.find(KEY_NAMES['profile'])
    bpy.ops.wm.save_as_mainfile(filepath=str(DEST), compress=True, copy=True)
    assert digest(SOURCE) == parent['source']['sha256']
    write_json(ROOT / 'construction-receipt.json', dict(source=dict(path=str(DEST), sha256=digest(DEST), bytes=DEST.stat().st_size),
        parent=parent['source'], body=body.name, gaze=gaze.name, blinkProperty=author['BLINK'], layoutProperty=CONTROL,
        defaultVisible='profile', variants=variants, seedVertices=seeds.tolist(), guardedVertices=int(guard.sum()),
        protectedLashBindingVertices=len(lash_vertices), basisHash=array_hash(basis), topologyHash=array_hash(triangles),
        hair=parent['hair'], cheekCoordinateHash=parent['variants']['orbital']['coordinateHash']))
    print('R499_SOURCE', str(DEST), flush=True)


if __name__ == '__main__':
    main()
