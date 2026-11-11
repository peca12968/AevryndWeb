"""Independently reopen the r501 asset, operate its skin, and render matched views."""
from pathlib import Path
from runpy import run_path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parent
study = run_path(str(ROOT/'author-r0501.py'))
probe, author, stage = (study[key] for key in ('probe','author','stage'))
read_json, write_json, digest, array_hash = (study[key] for key in ('read_json','write_json','digest','array_hash'))
activate, MODES = (study[key] for key in ('activate','MODES'))
parent_preview = run_path(str(probe['PARENT']/'preview-r0500.py'))


def evaluated_hash(obj):
    return array_hash(author['evaluated'](obj))


def main():
    proof = read_json(ROOT/'construction-receipt.json')
    parent = read_json(probe['PARENT']/'reopen-verification.json')
    original_renders = read_json(probe['PARENT']/'preview-receipt.json')['renders']
    assert proof['parent'] == parent['source']
    source = Path(proof['source']['path'])
    assert digest(source) == proof['source']['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False, use_scripts=False)
    scene = bpy.context.scene
    body, gaze = (bpy.data.objects[proof[k]] for k in ('body','gaze'))
    hair = bpy.data.objects[proof['hair']['object']]
    assert gaze[proof['layoutProperty']] == 1 and gaze[proof['blinkProperty']] == 0.
    keys = body.data.shape_keys.key_blocks
    basis = author['xyz'](body.data.shape_keys.reference_key.data)
    assert array_hash(basis) == proof['basisHash']
    assert array_hash(author['mesh_winding'](body)) == proof['topologyHash']
    assert array_hash(author['prior']['positions'](hair)) == proof['hair']['positionHash']
    assert array_hash(author['xyz'](keys[stage['previous']['KEY_NAMES']['orbital']].data)) == proof['cheekCoordinateHash']
    attachment = probe['anchors']()
    anchors = np.unique(attachment['tri'])
    masks = {}
    for mode, members in proof['variants'].items():
        active = np.zeros(len(basis),dtype=bool)
        for spec in members:
            positions = author['xyz'](keys[spec['name']].data)
            assert array_hash(positions) == spec['hash']
            mask = np.any(positions!=basis,axis=1)
            assert not mask[anchors].any()
            active |= mask
        masks[mode] = active
    lash = bpy.data.objects['R461 A | Shaft relief']
    layers = {name: bpy.data.objects[name] for name in stage['previous']['LAYERS']}
    positions = {}
    switch = {}
    tests = [(1.,p) for p in (0.,.5,.75,.82,.875,1.)]+[(37.,p) for p in (.92,1.)]
    for frame, phase in tests:
        key = f'{frame:g}:{phase:g}'
        activate(scene,gaze,'control',phase,frame)
        baseline = author['evaluated'](body)
        layer_coords = {name:author['evaluated'](layer) for name,layer in layers.items()}
        control = array_hash(baseline)
        if key in parent['evaluated']:
            assert control == parent['evaluated'][key]['separated']['skinHash']
        positions[key] = {'control': dict(skinHash=control)}
        for mode, mask in masks.items():
            activate(scene,gaze,mode,phase,frame)
            current = author['evaluated'](body)
            assert np.isfinite(current).all() and np.array_equal(baseline[~mask], current[~mask])
            delta = np.linalg.norm(current-baseline,axis=1)
            current_hash = array_hash(current)
            assert (current_hash == control) == (phase<=.5)
            layer_delta = {name:float(np.linalg.norm(author['evaluated'](layer)-layer_coords[name],axis=1).max())
                           for name,layer in layers.items()}
            assert not any(layer_delta.values()), layer_delta
            positions[key][mode] = dict(skinHash=current_hash, vertices=int(np.count_nonzero(delta)),
                maxLocalMetres=float(delta.max()), layerDeltaMetres=layer_delta)
            if phase == 1. and frame == 37.:
                activate(scene,gaze,'control',phase,frame)
                assert evaluated_hash(body) == control
                activate(scene,gaze,mode,phase,frame)
                assert evaluated_hash(body) == current_hash
                switch[mode] = dict(control=control, restored=current_hash, changedVertices=int(np.count_nonzero(delta)))
    assert all(driver.is_valid for driver in body.data.shape_keys.animation_data.drivers
               if 'R501' in driver.data_path)
    rig = next(obj for obj in scene.objects if obj.type=='ARMATURE' and 'Head' in obj.pose.bones
               and any(mod.type=='ARMATURE' and mod.object==obj for mod in body.modifiers))
    activate(scene,gaze,'control',0.,1.)
    head0 = rig.matrix_world @ rig.pose.bones['Head'].matrix
    stats = dict(parent['stats'])
    stats['morphs'] += sum(len(members) for members in proof['variants'].values())
    write_json(ROOT/'reopen-verification.json',dict(source=proof['source'], evaluates=positions,
        lash=lash.name, lashRimAnchors=len(anchors), operation=switch, stats=stats))
    capture = parent_preview['capture']
    capture.__globals__.update(ROOT=ROOT, MODES=MODES[1:], activate=activate)
    renders, recovered = capture(scene, body, gaze, proof['source'], positions, head0, rig)
    baseline_renders = {}
    for view, _, _, _, _ in parent_preview['VIEWS']:
        control = original_renders[f'separated:{view}']
        baseline_renders[view] = control
        assert digest(Path(control['path'])) == control['sha256']
        for mode in MODES[1:]:
            candidate = renders[f'{mode}:{view}']
            for setting in ('phase','frame','camera','lens','exposure','crop'):
                assert candidate[setting]==control[setting], (view,mode,setting)
    activate(scene,gaze,'hermite',0.,1.)
    assert digest(source) == proof['source']['sha256']
    write_json(ROOT/'preview-receipt.json',dict(source=proof['source'], parent=proof['parent'],
        renders=renders, baseline=baseline_renders, recovered=recovered, restored='hermite:1:0'))


if __name__=='__main__':
    main()

