"""Build the complete child grooms from the inspected primary paths."""
from pathlib import Path
from hashlib import sha256
import json
import sys

import bpy
import numpy as np
from mathutils import Matrix

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from plan_r0487_import import load_plan

plan = load_plan()
DEST = ROOT / 'female-next-r0487-posterior-and-ear-routes-UNACCEPTED.blend'


def read_positions(obj):
    positions = np.empty((len(obj.data.curves), 80, 3), dtype='f4')
    obj.data.position_data.foreach_get('vector', positions.ravel())
    return positions


def positions_hash(positions):
    return sha256(positions.tobytes()).hexdigest()


def blend_roots(roots, guides, owners, weights):
    """Retain follicle position, while carrying distinct free paths into the fall."""
    result = np.empty((len(roots), guides.shape[1], 3), dtype='f4')
    hold = (1 - .36 * plan.smooth(np.linspace(0, 1, guides.shape[1]) / .60)).astype('f4')
    for start in range(0, len(roots), 2048):
        rows = slice(start, start + 2048)
        selected = guides[owners[rows]]
        mixed = np.sum(selected * weights[rows, :, None, None], axis=1)
        offset = roots[rows] - mixed[:, 0]
        result[rows] = mixed + offset[:, None] * hold[None, :, None]
    result[:, 0] = roots
    return result


def assign_owners(roots, guide_roots):
    owners = np.empty((len(roots), 8), dtype='i4')
    weights = np.empty_like(owners, dtype='f4')
    front = 1 - plan.smooth((roots[:, 1] + .041) / .041)
    guide_front = 1 - plan.smooth((guide_roots[:, 1] + .041) / .041)
    part = .008 + .003 * np.clip((roots[:, 1] + .10) / .070, 0, 1)
    guide_part = .008 + .003 * np.clip((guide_roots[:, 1] + .10) / .070, 0, 1)
    for start in range(0, len(roots), 2048):
        rows = slice(start, start + 2048)
        displacement = roots[rows, None] - guide_roots[None]
        distance = np.sum(displacement ** 2, axis=2)
        side_difference = ((roots[rows, 0] < part[rows])[:, None] !=
                           (guide_roots[:, 0] < guide_part)[None])
        # A frontal part is useful, while posterior ownership must overlap.
        distance += .008 * front[rows, None] * guide_front[None] * side_difference
        order = np.argsort(distance, axis=1, kind='stable')[:, :8]
        distance = np.take_along_axis(distance, order, axis=1)
        unnormalized = 1 / (distance + .000021) ** 2
        owners[rows] = order
        weights[rows] = unnormalized / unnormalized.sum(axis=1, keepdims=True)
    return owners, weights


def curve_ids(obj):
    ids = np.empty(len(obj.data.curves), dtype='i4')
    obj.data.attributes['AFN409_CURVE_ID'].data.foreach_get('value', ids)
    return ids


def store_int(data, name, values):
    attribute = data.attributes.get(name) or data.attributes.new(name, 'INT', 'CURVE')
    attribute.data.foreach_set('value', np.asarray(values, dtype='i4'))


def set_positions(obj, positions):
    obj.data.position_data.foreach_set('vector', positions.ravel())
    obj.data.update_tag()
    obj.update_tag()


def main():
    assert not DEST.exists()
    landmarks = plan.read_json(ROOT / 'guide-landmarks.json')
    source = plan.SOURCE
    assert plan.sha(source) == landmarks['source']['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False, use_scripts=False)
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    control = bpy.data.objects[plan.CONTROL_NAME]
    roots = read_positions(control)[:, 0].copy()
    follicle_ids = curve_ids(control)
    guide_path = ROOT / 'guide-paths.npz'
    paths = np.load(guide_path, allow_pickle=False)
    selected = paths['selected']
    domains = paths['domains']
    assert len(np.unique(selected)) == len(selected)
    owners, weights = assign_owners(roots, roots[selected])
    rear_midline = (roots[:, 1] >= .004) & (abs(roots[:, 0]) < .012)
    owner_x = roots[selected[owners], 0]
    cross_midline = (owner_x < 0).any(axis=1) & (owner_x > 0).any(axis=1)
    np.savez_compressed(ROOT / 'guide-ownership.npz', owners=owners, weights=weights,
                        curveIDs=follicle_ids, guideSourceIDs=follicle_ids[selected])
    variants = {}
    for mode in plan.MODES:
        guides = paths[mode]
        assert np.array_equal(guides[:, 0], roots[selected])
        bank = blend_roots(roots, guides, owners, weights)
        assert np.isfinite(bank).all() and np.array_equal(bank[:, 0], roots)
        obj = control.copy()
        obj.data = control.data.copy()
        obj.name = f'R487 complete hair | {mode}'
        obj.data.name = f'R487 reconstructed child strands | {mode}'
        bpy.context.scene.collection.objects.link(obj)
        set_positions(obj, bank)
        store_int(obj.data, 'AEVRYND_SCALP_REGION', domains)
        store_int(obj.data, 'AEVRYND_PRIMARY_GUIDE', owners[:, 0])
        guide = plan.create_guide_object(f'R487 editable primary paths | {mode}', guides, .00015)
        guide.data.materials.append(control.data.materials[0])
        store_int(guide.data, 'AEVRYND_PRIMARY_GUIDE_ID', np.arange(len(selected)))
        store_int(guide.data, 'AEVRYND_SOURCE_CURVE_ID', follicle_ids[selected])
        store_int(guide.data, 'AEVRYND_SCALP_REGION', domains[selected])
        variants[mode] = dict(object=obj.name, guideObject=guide.name, positionHash=positions_hash(bank),
                              guideHash=positions_hash(guides))
    visible = bpy.data.objects[variants['sweep']['object']]
    for obj in bpy.data.objects:
        if obj.type == 'CURVES':
            obj.hide_render = obj != visible
            obj.hide_set(obj != visible)
    bpy.ops.object.select_all(action='DESELECT')
    visible.select_set(True)
    bpy.context.view_layer.objects.active = visible
    note = bpy.data.texts.new('Aevrynd_R487_Posterior_And_Ear_Routes')
    note.write('Unaccepted study. Two complete ear routes share a continuous posterior scalp region. '
               'The editable primary paths and 24,831 original follicle IDs are retained. '
               'The accompanying NPZ files hold the reproducible owner map. '
               'Use the inherited source credits and licenses.\n')
    shot = plan.read_json(ROOT.parent / 'r0470-independent-posterior-locks/shot-A-face.json')['shot']
    scene = bpy.context.scene
    scene.camera.matrix_world = Matrix(shot['camera'])
    scene.camera.data.type = shot['cameraType']
    scene.camera.data.lens = shot['lens']
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 4
    bpy.ops.wm.save_as_mainfile(filepath=str(DEST), compress=True, copy=True)
    proof = dict(source=dict(path=str(DEST), sha256=plan.sha(DEST), bytes=DEST.stat().st_size),
                 parent=landmarks['source'], variants=variants, controlObject=control.name,
                 rootsBitIdentical=True, rootHash=positions_hash(roots), guideCount=len(selected),
                 childCount=len(roots), ownerCount=owners.shape[1], rearMidlineRoots=int(rear_midline.sum()),
                 rearMidlineRootsWithTwoSidedOwners=int((rear_midline & cross_midline).sum()),
                 guidePathSHA256=plan.sha(guide_path), ownerSHA256=plan.sha(ROOT / 'guide-ownership.npz'))
    (ROOT / 'construction-receipt.json').write_text(json.dumps(proof, indent=2), encoding='utf-8')
    print('R487_SOURCE', proof['source'], flush=True)


if __name__ == '__main__':
    main()
