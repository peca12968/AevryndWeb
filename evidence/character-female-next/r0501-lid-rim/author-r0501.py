"""Reconstruct the closing canthus envelope over the live rim and its return wall."""
from pathlib import Path
from runpy import run_path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parent
probe = run_path(str(ROOT / 'probe-r0501.py'))
stage = probe['stage']
read_json, write_json, digest = (probe[k] for k in ('read_json', 'write_json', 'digest'))
author = stage['author']
array_hash = stage['array_hash']
front_depth = run_path(str(ROOT / 'inspect-rim-r0501.py'))['front_depth']
DEST = ROOT / 'female-next-r0501-lid-rim-UNACCEPTED.blend'
CONTROL = 'R501_Lid_Rim'
MODES = ('control', 'hermite', 'membrane')
PHASES = np.array([.5, .75, .875, 1.])
PROFILE_SAMPLES = 25
WIDTH = 7.4


def smooth(t):
    q = np.clip(t, 0., 1.)
    return q*q*(3.-2.*q)


def activate(scene, gaze, mode, phase, frame=1.):
    gaze[CONTROL] = MODES.index(mode)
    stage['activate'](scene, gaze, 'separated', phase, frame)


def extended_rim(path, x):
    # Fit the actual upper attachment line and extend only its measured outer tangent.
    sorted_path = path[np.argsort(abs(path[:, 0]))]
    xs, z = abs(sorted_path[:,0]), sorted_path[:,2]
    slope = np.clip(np.polyfit(xs[-9:], z[-9:], 1)[0], .06, .54)
    return np.interp(x, xs, z) + np.maximum(0., x-xs[-1])*slope


def hermite_profile(raw, dt):
    t = np.linspace(0., 1., len(raw))
    start, end = raw[[0,-1]]
    slope = (end-start)/WIDTH
    bounds = sorted((0., 2.5*slope))
    a = np.clip(np.mean(np.diff(raw[:4]))/dt, *bounds) * WIDTH
    b = np.clip(np.mean(np.diff(raw[-4:]))/dt, *bounds) * WIDTH
    return ((2*t**3-3*t**2+1)*start + (t**3-2*t*t+t)*a
            + (-2*t**3+3*t*t)*end + (t**3-t*t)*b)


def membrane_profile(raw):
    # Keep both end points while minimizing second differences with a soft data term.
    n = len(raw)
    difference = np.diff(np.eye(n), n=2, axis=0)
    system = np.eye(n) + 18. * difference.T @ difference
    interior = slice(1, -1)
    result = raw.copy()
    result[interior] = np.linalg.solve(system[interior, interior], raw[interior] -
        system[interior][:, [0,-1]] @ raw[[0,-1]])
    return result


def tracks(coords, faces, roots, binding, side):
    candidates = roots[(binding['side']==side)&(binding['row']==0)]
    xs = np.arange(34., 49.0001, .5)
    relative = np.linspace(0., WIDTH, PROFILE_SAMPLES)
    rim = extended_rim(candidates, xs)
    floor = rim + 1.45
    raw = np.empty((len(xs), len(relative)))
    for i, (x, z0) in enumerate(zip(xs, floor)):
        # Limit each slab to actual triangles that can intersect its fixed x section.
        points = coords[faces, 0]
        selected = (points.min(1) <= side*x) & (points.max(1) >= side*x)
        slab = faces[selected]
        raw[i] = [front_depth(coords, slab, side*x, z) for z in z0+relative]
    valid = np.isfinite(raw).all(1)
    assert valid.sum() >= 24, (side, xs[~valid].tolist())
    raw = raw[valid]
    xs, floor = xs[valid], floor[valid]
    return xs, floor, relative, raw


def profile_delta(xs, floor, depth, raw, coords, variant):
    # Interpolate the entire depth field between measured ribs. Both skin sheets
    # sample the same field, preserving their separation along the local depth axis.
    t = depth / WIDTH
    edge = smooth(t/.18) * smooth((1.-t)/.18)
    if variant == 'hermite':
        fit = np.array([hermite_profile(row, depth[1]) for row in raw])
    else:
        fit = np.array([membrane_profile(row) for row in raw])
    changes = (fit-raw)*edge
    # Filter small x sampling discontinuities while retaining the 3D canthus shape.
    changes[1:-1] = .2*changes[:-2] + .6*changes[1:-1] + .2*changes[2:]
    x = abs(coords[:,0])
    f = np.interp(x, xs, floor)
    v = coords[:,2] - f
    x0 = np.clip(np.searchsorted(xs, x)-1, 0, len(xs)-2)
    z0 = np.clip(np.searchsorted(depth, v)-1, 0, len(depth)-2)
    a = np.clip((x-xs[x0])/(xs[x0+1]-xs[x0]), 0, 1)
    b = np.clip((v-depth[z0])/(depth[z0+1]-depth[z0]), 0, 1)
    delta = ((1-a)*(1-b)*changes[x0,z0] + a*(1-b)*changes[x0+1,z0] +
             (1-a)*b*changes[x0,z0+1] + a*b*changes[x0+1,z0+1])
    front = ((1-a)*(1-b)*raw[x0,z0] + a*(1-b)*raw[x0+1,z0] +
             (1-a)*b*raw[x0,z0+1] + a*b*raw[x0+1,z0+1])
    fade = smooth((x-xs[0])/4.) * smooth((xs[-1]-x)/3.5)
    # Full transport at the external sheet and first 2.3 mm of tissue; taper
    # gradually to zero behind the return wall. No globe or lash vertex is edited.
    wall = smooth((6.2-(coords[:,1]-front))/3.9)
    return np.clip(delta, -1.25, 1.25)*fade*wall, changes


def install(key, gaze, variant, index):
    lo, middle = PHASES[index-1:index+1]
    left = f'min(1,max(0,(blink-{lo})/{middle-lo}))'
    if index+1 < len(PHASES):
        hi = PHASES[index+1]
        right = f'min(1,max(0,({hi}-blink)/{hi-middle}))'
    else:
        right = '1'
    driver = key.driver_add('value').driver
    for name, prop in (('mode', CONTROL), ('blink', author['BLINK'])):
        variable = driver.variables.new()
        variable.name, variable.type = name, 'SINGLE_PROP'
        variable.targets[0].id = gaze
        variable.targets[0].data_path = f'["{prop}"]'
    driver.expression = f'(mode=={MODES.index(variant)})*{left}*{right}'


def main():
    parent = read_json(probe['PARENT'] / 'construction-receipt.json')
    source = Path(parent['source']['path'])
    assert digest(source) == parent['source']['sha256'] and not DEST.exists()
    witness = read_json(ROOT / 'rim-witness.json')
    assert witness['source'] == parent['source']
    bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False, use_scripts=False)
    scene = bpy.context.scene
    body, gaze = (bpy.data.objects[parent[name]] for name in ('body','gaze'))
    gaze[CONTROL] = 0
    gaze.id_properties_ui(CONTROL).update(min=0, max=2, soft_min=0, soft_max=2,
        description='0 r500 B, 1 rim Hermite interpolation, 2 rim membrane reconstruction')
    basis = author['xyz'](body.data.shape_keys.reference_key.data)
    binding = probe['anchors']()
    layers = {}
    changes = {mode: [] for mode in MODES[1:]}
    rim_vertices = np.unique(binding['tri'])
    exterior_union = np.zeros(len(basis), dtype=bool)
    with np.load(ROOT/'rim-witness.npz', allow_pickle=False) as bank:
        for index in range(1,len(PHASES)):
            phase = PHASES[index]
            activate(scene, gaze, 'control', phase)
            surface, triangles, _ = probe['mesh_data'](body)
            assert np.array_equal(surface.astype('f4'), bank[f'{index}/skin'])
            assert np.array_equal(triangles, bank[f'{index}/skinFaces'])
            roots = probe['rim_sites'](surface, binding)
            orbit = bank[f'{index}/orbit']
            region = np.unique(triangles[orbit])
            local_coords = surface[region]*1000.
            transform = np.asarray(body.matrix_world)[:3,:3]
            variants = {mode: np.zeros((len(region), 3)) for mode in MODES[1:]}
            domains = {}
            for side in (-1,1):
                sign = np.sign(local_coords[:,0]) == side
                coords = local_coords[sign]
                xs, floor, z, raw = tracks(surface*1000., triangles[orbit], roots*1000., binding, side)
                domains[str(side)] = dict(samples=len(xs), depthRibs=PROFILE_SAMPLES,
                    xLimitsMm=[float(xs[0]),float(xs[-1])], rimOffsetMm=1.45)
                for mode, field in variants.items():
                    dy, profile = profile_delta(xs, floor, z, raw, coords, mode)
                    field[sign,1] = dy*.001
                    domains[str(side)][mode] = dict(peakRibDeltaMm=float(np.max(abs(profile))))
                for mode, field in variants.items():
                    selected = region[sign][abs(field[sign,1])>1.e-7]
                    exterior_union[selected] = True
            # The attachment triangles are fixed exactly and a distance ramp
            # blends to the transported return; the live modifier is left active.
            start = surface[rim_vertices]
            near = np.min(np.linalg.norm(surface[region,None]-start[None,:],axis=2),axis=1)
            keep = smooth((near-.00045)/.00125)
            keep[np.isin(region,rim_vertices)] = 0.
            for mode, field in variants.items():
                local = (field*keep[:,None])@np.linalg.inv(transform).T
                proposed = basis.copy()
                proposed[region] += local.astype('f4')
                moved = np.any(proposed!=basis,axis=1)
                assert moved.any() and not moved[rim_vertices].any()
                key = body.shape_key_add(name=f'R501 {mode} | Closure {phase:g}', from_mix=False)
                key.data.foreach_set('co',proposed.ravel())
                install(key,gaze,mode,index)
                changes[mode].append(dict(phase=float(phase), name=key.name, hash=array_hash(proposed),
                    changedVertices=int(moved.sum()), maximumLocalDeltaMetres=float(np.linalg.norm(local,axis=1).max())))
            layers[str(phase)] = domains
            print('R501_REBUILD', phase, {mode: records[-1] for mode,records in changes.items()}, flush=True)
    for name, members in (('R501 | Live lash rim anchors', rim_vertices),
                          ('R501 | Canthus envelope and return', np.flatnonzero(exterior_union))):
        group = body.vertex_groups.new(name=name)
        group.add(members.tolist(),1.,'REPLACE')
    activate(scene,gaze,'hermite',0.)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(DEST),compress=True)
    write_json(ROOT/'construction-receipt.json',dict(source=dict(path=str(DEST),bytes=DEST.stat().st_size,sha256=digest(DEST)),
        parent=parent['source'], body=body.name,gaze=gaze.name,layoutProperty=CONTROL, default='hermite',
        blinkProperty=author['BLINK'], basisHash=parent['basisHash'],topologyHash=parent['topologyHash'],
        hair=parent['hair'],cheekCoordinateHash=parent['cheekCoordinateHash'],
        originalLashRimVertices=len(rim_vertices),canthusTransportVertices=int(exterior_union.sum()),
        profiles=layers, variants=changes, inputWitnessSha256=digest(ROOT/'rim-witness.npz')))


if __name__=='__main__':
    main()

