"""Localize the non-even root probes in the neutral straight-span check."""
from collections import Counter
from pathlib import Path
import runpy

import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
author = runpy.run_path(str(ROOT / 'author-r0490.py'))
probe = runpy.run_path(str(ROOT.parent / 'r0489-crown-attachment-flow/preview-r0489.py'))


def winding(triangles, point):
    a, b, c = (triangles - point).transpose(1, 0, 2)
    length_a, length_b, length_c = (np.linalg.norm(v, axis=1) for v in (a, b, c))
    numerator = (a * np.cross(b, c)).sum(axis=1)
    denominator = (length_a*length_b*length_c + (a*b).sum(axis=1)*length_c
                   + (b*c).sum(axis=1)*length_a + (c*a).sum(axis=1)*length_b)
    return float(np.arctan2(numerator, denominator).sum() / (2*np.pi))


def main():
    proof = author['read_json'](ROOT / 'construction-receipt.json')
    proxy = author['read_json'](ROOT / 'straight-contact.json')
    source = Path(proof['source']['path'])
    assert author['digest'](source) == proof['source']['sha256'] == proxy['source']['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False, use_scripts=False)
    obj = bpy.data.objects[proof['variants']['swept']['object']]
    skin = bpy.data.objects[author['BODY']]
    roots = author['positions'](obj)[:, 0]
    assert author['array_hash'](roots) == proof['rootHash']
    _, tree, _ = author['foundation']['binding_frame'](obj, skin, roots)
    ids = author['read_attribute'](obj.data, 'AFN409_CURVE_ID')
    offsets = author['read_attribute'](obj.data, 'AEVRYND_ROOT_NORMAL_OFFSET')
    mesh = skin.data
    coordinates = np.empty((len(mesh.vertices), 3), dtype='f4')
    faces = np.empty((len(mesh.loop_triangles), 3), dtype='i4')
    mesh.vertices.foreach_get('co', coordinates.ravel())
    mesh.loop_triangles.foreach_get('vertices', faces.ravel())
    directed = np.concatenate((faces[:, [0,1]], faces[:, [1,2]], faces[:, [2,0]]))
    edge_key = np.sort(directed, axis=1)
    edges, inverse, counts = np.unique(edge_key, axis=0, return_inverse=True, return_counts=True)
    orientation = np.bincount(inverse, weights=np.where(directed[:,0] < directed[:,1], 1, -1), minlength=len(edges))
    mesh_scope = dict(boundaryEdges=int((counts == 1).sum()), otherNonTwoFaceEdges=int((counts > 2).sum()),
                      twoFaceEdgesWithSameDirection=int(((counts == 2) & (orientation != 0)).sum()))
    triangles = coordinates[faces].astype('f8')
    issues = []
    for index, root in enumerate(roots):
        center = Vector(root)
        rays = probe['ray_counts'](center, tree)
        if not any(count % 2 for count in rays):
            continue
        issues.append(dict(curveID=int(ids[index]), positionMetres=root.tolist(), rayCrossings=rays,
            nearestSignedCenterDistanceMetres=probe['signed_gap'](center, tree),
            rootNormalOffsetMetres=float(offsets[index]), winding=winding(triangles, root.astype('f8'))))
    assert len(issues) == proxy['rootCenters'] - proxy['rootCentersWithAllEvenParity']
    result = dict(source=proof['source'], variant='swept', pose=proxy['pose'], disputedRoots=len(issues),
        fixtureTopology=mesh_scope, rayPatterns=dict(Counter(str(row['rayCrossings']) for row in issues)),
        minimumWinding=min(row['winding'] for row in issues), maximumWinding=max(row['winding'] for row in issues),
        method='Exact bound root positions and three rays, plus the full neutral fixture triangle solid-angle sum at each disputed root.',
        roots=issues)
    author['write_json'](ROOT / 'root-parity.json', result)
    print('R490_ROOT_RECHECK', {key: value for key, value in result.items() if key != 'roots'}, flush=True)


if __name__ == '__main__':
    main()
