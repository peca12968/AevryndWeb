"""Recheck the live transported skin and retained lash attachment in Blender."""
from pathlib import Path
from runpy import run_path

import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
study = run_path(str(ROOT/'author-r0501.py'))
probe, author, stage = (study[k] for k in ('probe','author','stage'))
read_json, write_json, digest = (study[k] for k in ('read_json','write_json','digest'))
mesh_data, tree = (probe[k] for k in ('mesh_data','tree'))
activate, MODES = (study[k] for k in ('activate','MODES'))
fold_witness = probe['setup']['fold_witness']


def signed_vertex_samples(coords, vertex_ids, surface):
    values = []
    for i in vertex_ids:
        point = Vector(coords[i])
        near, normal, _, distance = surface.find_nearest(point)
        if near is not None:
            values.append((float(distance if (point-near).dot(normal)>=0 else -distance), int(i)))
    if not values:
        return None
    distance, index = min(values)
    return dict(signedNearestMetres=distance, vertex=index, positionMetres=coords[index].tolist(),
        negativeBeyond8Microns=sum(value<-8e-6 for value, _ in values), count=len(values))


def take(skin, mask, fixtures, lash_polys, binding):
    v, f, poly = skin
    subset = np.flatnonzero(mask[f].any(1))
    region = tree(v, f[subset])
    whole = tree(v, f)
    pairs = set()
    witnesses = {}
    for a, b in region.overlap(whole):
        s = subset[a]
        if poly[s]==poly[b] or (f[s,:,None]==f[b,None,:]).any():
            continue
        key = tuple(sorted((int(poly[s]),int(poly[b]))))
        pairs.add(key)
        witnesses[key] = ((v[f[s]].mean(0)+v[f[b]].mean(0))/2).tolist()
    ocular = {name:{(int(poly[subset[a]]),int(ids[b])) for a,b in region.overlap(other)}
              for name,(other,ids) in fixtures.items() if name!='lashes'}
    lashes = fixtures['lashes'][0]
    roots, shafts = {}, {}
    for a, b in region.overlap(lashes):
        key = (int(poly[subset[a]]),int(lash_polys[b]))
        group = roots if binding['segment'][b]==0 else shafts
        fibre = int(binding['owner'][b])
        group[key] = dict(site=int(binding['siteID'][fibre]), row=int(binding['row'][fibre]),
            segment=int(binding['segment'][b]),pointMetres=v[f[subset[a]]].mean(0).tolist())
    return pairs, witnesses, ocular, roots, shafts


def main():
    proof = read_json(ROOT/'construction-receipt.json')
    source = Path(proof['source']['path'])
    parent = proof['parent']
    assert digest(source) == proof['source']['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False, use_scripts=False)
    scene = bpy.context.scene
    skin, gaze = (bpy.data.objects[proof[name]] for name in ('body','gaze'))
    names = dict(zip(('eye','cornea','meniscus','lashes'),stage['previous']['LAYERS']))
    layers = {role:bpy.data.objects[name] for role,name in names.items()}
    binding = probe['anchors']()
    basis = author['xyz'](skin.data.shape_keys.reference_key.data)
    keys = skin.data.shape_keys.key_blocks
    previous_mask = np.any(author['xyz'](keys[stage['KEY_NAMES']['separated']].data)!=basis,axis=1)
    masks = {}
    for mode, members in proof['variants'].items():
        fields = [author['xyz'](keys[spec['name']].data) for spec in members]
        masks[mode] = np.any(np.any(np.stack(fields)!=basis,axis=0),axis=1)
    union = masks['hermite']|masks['membrane']
    tests = [(1.,p) for p in (0.,.5,.75,.82,.875,1.)]
    tests += [(36.75,1.),(37.,.875),(37.,.92),(37.,1.)]
    results = {}
    steps = {}
    previous_count = None
    for frame, phase in tests:
        key = f'{frame:g}:{phase:g}'
        activate(scene,gaze,'control',phase,frame)
        control = mesh_data(skin)
        other = {role:mesh_data(obj) for role,obj in layers.items()}
        lv,lf,lp = other['lashes']
        assert np.array_equal(lf,binding['faces'])
        fixtures = {role:(tree(v,f), ids) for role,(v,f,ids) in other.items()}
        if key=='37:1':
            count = take(control, previous_mask, fixtures, lp, binding)
            previous_count = dict(rootPolygonPairs=len(count[3]), shaftPolygonPairs=len(count[4]),
                sites=sorted({row['site'] for row in count[3].values()}))
        before = take(control, union, fixtures, lp, binding)
        rows = {}
        if key=='1:1':
            steps['control'] = fold_witness(scene,skin)
        for mode,mask in masks.items():
            activate(scene,gaze,mode,phase,frame)
            current = mesh_data(skin)
            assert np.array_equal(current[0][~mask], control[0][~mask])
            root = probe['rim_sites'](current[0],binding)
            assert np.array_equal(root,probe['rim_sites'](control[0],binding))
            if key=='1:1':
                steps[mode] = fold_witness(scene,skin)
            if np.array_equal(current[0],control[0]):
                rows[mode] = dict(exactControl=True)
                continue
            assert np.array_equal(mesh_data(layers['lashes'])[0],lv)
            after = take(current, union, fixtures, lp, binding)
            affected = np.flatnonzero(np.any(current[0]!=control[0],axis=1))
            winding = author['triangle_metrics'](control[0], current[0], control[1])
            rows[mode] = dict(
                skin=dict(before=len(before[0]),after=len(after[0]),new=[dict(polygons=p,locationMetres=after[1][p]) for p in sorted(after[0]-before[0])]),
                ocular={role:dict(before=len(prior),after=len(after[2][role]),new=sorted(after[2][role]-prior))
                        for role,prior in before[2].items()},
                planted=dict(before=len(before[3]),after=len(after[3]),newCount=len(after[3].keys()-before[3].keys())),
                exposed=dict(before=len(before[4]),after=len(after[4]),new=[dict(polygons=p,**after[4][p]) for p in sorted(after[4].keys()-before[4].keys())]),
                winding=winding, signedSamples={role:signed_vertex_samples(current[0],affected,t[0])
                    for role,t in fixtures.items() if role!='lashes'},
                attachmentMaxMetres=float(np.linalg.norm(lv.reshape(-1,68,3)[:,66]-root,axis=1).max()))
        results[key] = rows
        print('R501_CONTACT',key,{mode:(len(v['skin']['new']),len(v['exposed']['new'])) if 'skin' in v else 'exact'
                                  for mode,v in rows.items()},flush=True)
    assert digest(source) == proof['source']['sha256']
    write_json(ROOT/'facial-contact.json',dict(source=proof['source'],parent=parent,states=results,
        previousReportedFrame37Pairs=previous_count, fixedFrontalNormalSteps=steps,
        scope=('Evaluated skin and visible lash surface triangles at 10 held settings, including fractional frames. '
               'Self pairs exclude polygons sharing a vertex. Segment zero is the planted base. '
               'Signed nearest point samples use local surface normals and are not whole-volume or swept clearance.')))


if __name__=='__main__':
    main()

