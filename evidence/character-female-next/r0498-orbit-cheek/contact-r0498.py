"""Compare the actual moved facial patch against evaluated surfaces at three blink positions."""
from pathlib import Path
from runpy import run_path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parent
preview = run_path(str(ROOT / 'preview-r0498.py'))
author = preview['author']
read_json, write_json, digest = (author[key] for key in ('read_json', 'write_json', 'digest'))


def mesh_data(obj):
    current = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = current.data
    local = author['xyz'](mesh.vertices)
    transform = np.array(current.matrix_world, dtype='f8')
    vertices = local.astype('f8') @ transform[:3, :3].T + transform[:3, 3]
    mesh.calc_loop_triangles()
    triangles = np.empty((len(mesh.loop_triangles), 3), dtype='i4')
    polygons = np.empty(len(mesh.loop_triangles), dtype='i4')
    mesh.loop_triangles.foreach_get('vertices', triangles.ravel())
    mesh.loop_triangles.foreach_get('polygon_index', polygons)
    return vertices, triangles, polygons


def tree(vertices, triangles):
    return BVHTree.FromPolygons(vertices.tolist(), triangles.tolist(), all_triangles=True)


def snapshot(body_mesh, mask, layers):
    coords, triangles, polygons = body_mesh
    subset = np.flatnonzero(mask[triangles].any(1))
    patch = tree(coords, triangles[subset])
    whole = tree(coords, triangles)
    self_pairs = set()
    for a, b in patch.overlap(whole):
        a = subset[a]
        if polygons[a] == polygons[b] or (triangles[a, :, None] == triangles[b, None, :]).any():
            continue
        self_pairs.add(tuple(sorted((int(polygons[a]), int(polygons[b])))))
    layer_results = {}
    for name, (other, layer_polygons) in layers.items():
        contacts = {(int(polygons[subset[a]]), int(layer_polygons[b])) for a, b in patch.overlap(other)}
        distances = [(other.find_nearest(Vector(coords[index]))[3], int(index)) for index in np.flatnonzero(mask)]
        distance, index = min((row for row in distances if row[0] is not None), key=lambda row: row[0])
        layer_results[name] = dict(pairs=contacts, closestMovedVertex=dict(vertexID=index, unsignedMetres=float(distance),
                                                                          positionMetres=coords[index].tolist()))
    return self_pairs, layer_results


def main():
    proof = read_json(ROOT / 'construction-receipt.json')
    source = Path(proof['source']['path'])
    assert digest(source) == proof['source']['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False, use_scripts=False)
    scene = bpy.context.scene
    body, gaze = (bpy.data.objects[proof[name]] for name in ('body', 'gaze'))
    layers = {name: bpy.data.objects[name] for name in preview['LAYERS']}
    basis = author['xyz'](body.data.shape_keys.reference_key.data)
    masks = {label: np.any(author['xyz'](body.data.shape_keys.key_blocks[name].data) != basis, axis=1)
             for label, name in preview['KEY_NAMES'].items()}
    results = {}
    for phase in author['PHASES']:
        preview['activate'](scene, body, gaze, 'control', phase)
        reference = mesh_data(body)
        fixtures = {}
        for name, layer in layers.items():
            coords, triangles, polygons = mesh_data(layer)
            fixtures[name] = tree(coords, triangles), polygons
        phase_results = {}
        for label, mask in masks.items():
            old_self, old = snapshot(reference, mask, fixtures)
            preview['activate'](scene, body, gaze, label, phase)
            candidate = mesh_data(body)
            new_self, new = snapshot(candidate, mask, fixtures)
            winding = author['triangle_metrics'](reference[0], candidate[0], reference[1])
            layers_report = {}
            for name in layers:
                start, finish = old[name]['pairs'], new[name]['pairs']
                layers_report[name] = dict(baselinePairs=len(start), candidatePairs=len(finish),
                    newPairs=sorted(finish - start), closestMovedVertex=new[name]['closestMovedVertex'],
                    baselineClosestMovedVertex=old[name]['closestMovedVertex'])
            phase_results[label] = dict(editedVertices=int(mask.sum()), baselineSkinSelfPairs=len(old_self),
                candidateSkinSelfPairs=len(new_self), newSkinSelfPairs=sorted(new_self - old_self), layers=layers_report,
                evaluatedPatchWinding=winding)
        results[str(phase)] = phase_results
        print('R498_FACIAL_CONTACT', phase, {label: (len(row['newSkinSelfPairs']),
            sum(len(layer['newPairs']) for layer in row['layers'].values())) for label, row in phase_results.items()}, flush=True)
    assert digest(source) == proof['source']['sha256']
    write_json(ROOT / 'facial-contact.json', dict(source=proof['source'], poseFrame=1,
        scope='Evaluated moved skin patch at three discrete blink settings. BVH triangle overlaps compared at source polygon IDs. Shared-vertex self pairs excluded. Closest moved vertices give unsigned samples.',
        states=results))


if __name__ == '__main__':
    main()
