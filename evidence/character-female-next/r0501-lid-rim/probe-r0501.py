"""Extract the live eyelid rim anchors and classify finite lash/skin contact."""
from pathlib import Path
from runpy import run_path

import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
PARENT = ROOT.parent / 'r0500-multi-pose-lid'
setup = run_path(str(PARENT / 'contact-r0500.py'))
stage = setup['stage']
read_json, write_json, digest = (setup[k] for k in ('read_json', 'write_json', 'digest'))
mesh_data, tree = (setup[k] for k in ('mesh_data', 'tree'))
POSES = ((1., 0.), (1., .75), (1., .875), (1., 1.), (36.75, 1.), (37., .875), (37., 1.))


def anchors():
    lower = ROOT.parent / 'r0456-lower-margin-clearance'
    receipt = read_json(lower / 'trim-plan.json')['nearRimLashes']['asset']
    data = lower / receipt['file']
    assert digest(data) == receipt['sha256']
    with np.load(data, allow_pickle=False) as bank:
        return {name: bank[name] for name in ('tri', 'bary', 'row', 'side', 'segment', 'siteID', 'owner', 'faces')}


def rim_sites(coords, binding):
    return np.sum(coords[binding['tri']] * binding['bary'][..., None], axis=1)


def contact(skin, lash, binding, orbital_triangles):
    sv, sf, sp = skin
    lv, lf, lp = lash
    assert np.array_equal(lf, binding['faces'])
    support = tree(sv, sf[orbital_triangles])
    raw = tree(lv, lf).overlap(support)
    witnesses = []
    for l, s in raw:
        j = int(orbital_triangles[s])
        fibre = int(binding['owner'][l])
        point = lv[lf[l]].mean(0)
        near, normal, _, dist = support.find_nearest(Vector(point))
        witnesses.append(dict(site=int(binding['siteID'][fibre]), fibre=fibre,
            row=int(binding['row'][fibre]), side=int(binding['side'][fibre]),
            segment=int(binding['segment'][l]), lashTriangle=l, skinTriangle=j, skinPolygon=int(sp[j]),
            skinVertices=sf[j].tolist(), pointMetres=point.tolist(),
            centroidSignedNearestMetres=float(dist if (Vector(point)-near).dot(normal) >= 0 else -dist)))
    return sorted(witnesses, key=lambda row: (row['segment'], row['fibre'], row['skinTriangle'], row['lashTriangle']))


def main():
    proof = read_json(PARENT / 'construction-receipt.json')
    source = Path(proof['source']['path'])
    assert digest(source) == proof['source']['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False, use_scripts=False)
    scene = bpy.context.scene
    skin, gaze = (bpy.data.objects[proof[name]] for name in ('body','gaze'))
    lash = bpy.data.objects['R461 A | Shaft relief']
    ocular = [bpy.data.objects[n] for n in stage['previous']['LAYERS'][:2]]
    binding = anchors()
    report = dict(source=proof['source'], lash=lash.name, modifiers=[dict(name=m.name,type=m.type) for m in lash.modifiers], poses={})
    arrays = dict(binding)
    for index, (frame, phase) in enumerate(POSES):
        stage['activate'](scene, gaze, 'separated', phase, frame)
        v, f, ids = mesh_data(skin)
        roots = rim_sites(v, binding)
        eye_centres = np.array([v0.mean(0) for v0, _, _ in (mesh_data(obj) for obj in ocular)])
        # Both eyeballs are in each ocular mesh; the four separate lash rows bound the orbital region.
        flags = np.zeros(len(v), dtype=bool)
        for side in np.unique(binding['side']):
            row = roots[binding['side'] == side]
            low = row.min(0) - np.array((.0075,.008,.009))
            high = row.max(0) + np.array((.0075,.012,.012))
            flags |= np.all((v>=low)&(v<=high), axis=1)
        orbit = np.flatnonzero(flags[f].any(1))
        lv, lf, lp = mesh_data(lash)
        rows = contact((v,f,ids),(lv,lf,lp),binding,orbit)
        geom = [dict(side=int(side), row=int(row), count=len(r), rootBoundsMetres=[r.min(0).tolist(),r.max(0).tolist()])
                for side in np.unique(binding['side']) for row in np.unique(binding['row'])
                if len(r := roots[(binding['side']==side)&(binding['row']==row)])]
        report['poses'][f'{frame:g}:{phase:g}'] = dict(anchors=geom, rootPairs=sum(w['segment']==0 for w in rows),
            shaftPairs=sum(w['segment']>0 for w in rows), witnesses=rows, orbitTriangles=len(orbit),
            lashRootMaxMetres=float(np.linalg.norm(lv.reshape(-1,68,3)[:,66]-roots,axis=1).max()))
        for key, data in dict(roots=roots, orbit=orbit, skin=v, lash=lv, world=np.asarray(skin.matrix_world), eyeCentres=eye_centres).items():
            arrays[f'{index}/{key}'] = data.astype('i4' if key=='orbit' else 'f4')
        if index==0:
            arrays['skinFaces'], arrays['skinPolygons'] = f, ids
        arrays[f'{index}/skinFaces'] = f
        arrays[f'{index}/skinPolygons'] = ids
        print('R501_PROBE', frame, phase, report['poses'][f'{frame:g}:{phase:g}']['rootPairs'],
              report['poses'][f'{frame:g}:{phase:g}']['shaftPairs'], flush=True)
    write_json(ROOT / 'rim-witness.json', report)
    np.savez_compressed(ROOT / 'rim-witness.npz', **arrays)


if __name__ == '__main__':
    main()

