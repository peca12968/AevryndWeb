"""Solve local upper-lid correctives against contact witnesses from two gaze poses."""
from heapq import heappop, heappush
from pathlib import Path
from runpy import run_path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parent
PARENT = ROOT.parent / 'r0498-orbit-cheek'
TRIAL = ROOT.parent / 'r0499-lid-fold'
DEST = ROOT / 'female-next-r0500-multi-pose-lid-UNACCEPTED.blend'
prior = run_path(str(TRIAL / 'author-r0499.py'))
contact = run_path(str(TRIAL / 'contact-r0499.py'))
author, previous = prior['author'], prior['previous']
read_json, write_json, digest, array_hash = (prior[key] for key in ('read_json', 'write_json', 'digest', 'array_hash'))
KEY_NAMES = {'anchored': 'R500 A | Surface anchors', 'separated': 'R500 B | Multi-pose separation'}
MODES = ('control', *KEY_NAMES)
CONTROL = 'R500_Lid_Fold_Layout'


def activate(scene, gaze, mode, phase, frame=1):
    gaze[CONTROL] = MODES.index(mode)
    gaze[author['BLINK']] = phase
    gaze.update_tag()
    scene.frame_set(int(frame), subframe=frame-int(frame))
    bpy.context.view_layer.update()


def install_driver(key, gaze, mode):
    q = 'min(1,max(0,(blink-.54)/.46))'
    settings = key.driver_add('value').driver
    for name, prop in (('mode', CONTROL), ('blink', author['BLINK'])):
        variable = settings.variables.new()
        variable.name = name
        variable.type = 'SINGLE_PROP'
        variable.targets[0].id = gaze
        variable.targets[0].data_path = f'["{prop}"]'
    settings.expression = f'(mode=={MODES.index(mode)})*{q}**2*(3-2*{q})'


def best_axis(a, b):
    e = np.roll(a, -1, axis=0) - a
    f = np.roll(b, -1, axis=0) - b
    n = np.cross(e[0], e[1])
    m = np.cross(f[0], f[1])
    if min(np.linalg.norm(n), np.linalg.norm(m)) < 1e-13:
        return None, 0.
    n /= np.linalg.norm(n)
    m /= np.linalg.norm(m)
    candidates = np.vstack((n, m, np.cross(e[:, None, :], f[None, :, :]).reshape(-1, 3),
                            np.cross(n, e), np.cross(m, f)))
    lengths = np.linalg.norm(candidates, axis=1)
    axes = candidates[lengths > 1e-13] / lengths[lengths > 1e-13, None]
    axes = np.vstack((axes, -axes))
    margins = (b @ axes.T).min(0) - (a @ axes.T).max(0)
    index = int(margins.argmax())
    return axes[index], float(margins[index])


def constrain_pair(coords, delta, first, second, caps):
    axis, margin = best_axis(coords[first], coords[second])
    touched = np.unique(np.r_[first[np.any(delta[first] != 0, axis=1)], second[np.any(delta[second] != 0, axis=1)]])
    if not len(touched):
        return False, margin, False
    if axis is None or margin <= 1e-7:
        caps[touched] = 0.
        return True, margin, True
    a, b = coords[first] @ axis, coords[second] @ axis
    va, vb = delta[first] @ axis, delta[second] @ axis
    close_a, close_b = np.maximum(va, 0), np.maximum(-vb, 0)
    closing = close_a[:, None] + close_b[None, :]
    valid = closing > 1e-10
    if not valid.any():
        return False, margin, False
    buffer = min(.000012, margin * .28)
    safe = float(((b[None, :] - a[:, None] - buffer)[valid] / closing[valid]).min())
    safe = np.clip(safe * .95, 0, 1) if safe < 1 else 1.
    indices = np.r_[first[close_a > 1e-10], second[close_b > 1e-10]]
    caps[indices] = np.minimum(caps[indices], safe)
    return safe < 1, margin, False


def train(rejected, failure):
    file = Path(rejected['source']['path'])
    assert digest(file) == rejected['source']['sha256'] == failure['source']['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(file), load_ui=False, use_scripts=False)
    scene = bpy.context.scene
    body, gaze = (bpy.data.objects[rejected[key]] for key in ('body', 'gaze'))
    basis = author['xyz'](body.data.shape_keys.reference_key.data)
    key = body.data.shape_keys.key_blocks[prior['KEY_NAMES']['profile']]
    target = author['xyz'](key.data)
    assert array_hash(target) == rejected['variants']['profile']['coordinateHash']
    raw = target - basis
    active = np.any(raw != 0, axis=1)
    fixed = np.ones(len(basis), dtype='f8')
    separated = fixed.copy()
    reports = {}
    for state, info in failure['polygonCentroids'].items():
        frame, phase, _ = state.split(':')
        frame, phase = float(frame), float(phase)
        if frame == 1.:
            phase = round(phase * 24) / 24
        prior['activate'](scene, gaze, 'control', phase, frame)
        baseline = contact['mesh_data'](body)
        prior['activate'](scene, gaze, 'profile', phase, frame)
        corrected = contact['mesh_data'](body)
        delta = corrected[0] - baseline[0]
        assert not np.any(delta[~active])
        ids = {poly['id'] for item in info['witnesses'] for poly in item['polygons']}
        faces = {index: baseline[1][baseline[2] == index] for index in ids}
        counts = dict(witnessPolygonPairs=len(info['witnesses']), trianglePairs=0, cappedPairs=0, degenerateFallbackPairs=0)
        smallest = None
        for item in info['witnesses']:
            a, b = [poly['id'] for poly in item['polygons']]
            for first in faces[a]:
                for second in faces[b]:
                    touched = np.unique(np.r_[first[active[first]], second[active[second]]])
                    fixed[touched] = 0.
                    changed, margin, fallback = constrain_pair(baseline[0], delta, first, second, separated)
                    counts['trianglePairs'] += 1
                    counts['cappedPairs'] += int(changed)
                    counts['degenerateFallbackPairs'] += int(fallback)
                    if margin > 0 and (smallest is None or margin < smallest):
                        smallest = margin
        counts['minimumPositiveBaselineAxisMetres'] = smallest
        if state == '37:1:profile':
            base_pairs, _ = contact['snapshot'](baseline, active, {})
            raw_pairs, _ = contact['snapshot'](corrected, active, {})
            expected = {tuple(poly['id'] for poly in item['polygons']) for item in info['witnesses']}
            assert raw_pairs-base_pairs == expected and len(expected) == 33
            counts['exactlyReproducedNewPolygonPairs'] = len(expected)
        reports[state] = counts
    assert digest(file) == rejected['source']['sha256']
    return raw, fixed, separated, reports


def propagate(basis, mesh, active, caps, radius):
    edges = np.empty((len(mesh.edges), 2), dtype='i4')
    mesh.edges.foreach_get('vertices', edges.ravel())
    active_edges = edges[active[edges].all(1)]
    graph = {int(index): [] for index in np.flatnonzero(active)}
    for a, b in active_edges:
        length = max(.000045, float(np.linalg.norm(basis[a]-basis[b])))
        graph[a].append((b, length))
        graph[b].append((a, length))
    result = caps.copy()
    for seed in np.flatnonzero((caps < 1) & active):
        best = {seed: 0.}
        queue = [(0., seed)]
        while queue:
            distance, index = heappop(queue)
            if best[index] != distance:
                continue
            t = distance / radius
            result[index] = min(result[index], caps[seed] + (1 - caps[seed]) * (t*t*(3-2*t)))
            for adjacent, step in graph[index]:
                arrival = distance + step
                if arrival < min(radius, best.get(adjacent, radius)):
                    best[adjacent] = arrival
                    heappush(queue, (arrival, adjacent))
    return result


def main():
    parent = read_json(PARENT / 'construction-receipt.json')
    rejected = read_json(TRIAL / 'construction-receipt.json')
    failure = read_json(TRIAL / 'failure-witness.json')
    source = Path(parent['source']['path'])
    assert not DEST.exists() and digest(source) == parent['source']['sha256']
    raw, anchors, axes, training = train(rejected, failure)
    bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False, use_scripts=False)
    scene = bpy.context.scene
    body, gaze = (bpy.data.objects[parent[key]] for key in ('body', 'gaze'))
    basis = author['xyz'](body.data.shape_keys.reference_key.data)
    assert array_hash(basis) == rejected['basisHash'] == parent['basisHash']
    assert array_hash(author['mesh_winding'](body)) == rejected['topologyHash']
    hair = bpy.data.objects[parent['hair']['object']]
    assert array_hash(author['prior']['positions'](hair)) == parent['hair']['positionHash']
    active = np.any(raw != 0, axis=1)
    variants = {}
    gaze[CONTROL] = 0
    gaze.id_properties_ui(CONTROL).update(min=0, max=2, description='0 r498, 1 local surface anchors, 2 multi-pose separation')
    for label, caps, radius in (('anchored', anchors, .0030), ('separated', axes, .0020)):
        mask = propagate(basis, body.data, active, caps, radius)
        assert np.all((mask >= 0) & (mask <= caps))
        candidate = basis + (raw * mask[:, None]).astype('f4')
        changed = np.linalg.norm(candidate-basis, axis=1)
        assert int(np.count_nonzero(changed)) >= 150 and changed.max() > .00035
        key = body.shape_key_add(name=KEY_NAMES[label], from_mix=False)
        key.relative_key = body.data.shape_keys.reference_key
        key.data.foreach_set('co', candidate.ravel())
        install_driver(key, gaze, label)
        variants[label] = dict(key=key.name, coordinateHash=array_hash(candidate), changedVertices=int(np.count_nonzero(changed)),
            untouchedTargetVertices=int((active & (mask == 1)).sum()), locallyConstrainedVertices=int((active & (mask < 1)).sum()),
            pinnedVertices=int((active & (mask == 0)).sum()), maximumLocalDisplacementMetres=float(changed.max()),
            geodesicFalloffMetres=radius)
    activate(scene, gaze, 'separated', 0.)
    bpy.ops.object.select_all(action='DESELECT')
    body.select_set(True)
    bpy.context.view_layer.objects.active = body
    body.active_shape_key_index = body.data.shape_keys.key_blocks.find(KEY_NAMES['separated'])
    bpy.ops.wm.save_as_mainfile(filepath=str(DEST), compress=True, copy=True)
    assert digest(source) == parent['source']['sha256']
    write_json(ROOT / 'construction-receipt.json', dict(source=dict(path=str(DEST), sha256=digest(DEST), bytes=DEST.stat().st_size),
        parent=parent['source'], rejectedDesign=rejected['source'], training=training, body=body.name, gaze=gaze.name,
        blinkProperty=author['BLINK'], layoutProperty=CONTROL, defaultVisible='separated', variants=variants,
        basisHash=array_hash(basis), topologyHash=rejected['topologyHash'], hair=parent['hair'],
        cheekCoordinateHash=parent['variants']['orbital']['coordinateHash']))
    print('R500_SOURCE', str(DEST), flush=True)


if __name__ == '__main__':
    main()
