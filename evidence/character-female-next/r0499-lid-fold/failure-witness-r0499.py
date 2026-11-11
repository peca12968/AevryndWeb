"""Locate the new polygon overlaps and capture the failing held pose."""
from pathlib import Path
from runpy import run_path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parent
stage = run_path(str(ROOT / 'author-r0499.py'))
contact = run_path(str(ROOT / 'contact-r0499.py'))
author, previous = stage['author'], stage['previous']
read_json, write_json, digest = (stage[key] for key in ('read_json', 'write_json', 'digest'))


def main():
    proof = read_json(ROOT / 'construction-receipt.json')
    audit = read_json(ROOT / 'facial-contact.json')
    source = Path(proof['source']['path'])
    assert digest(source) == proof['source']['sha256'] and audit['source'] == proof['source']
    bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False, use_scripts=False)
    scene = bpy.context.scene
    body, gaze = (bpy.data.objects[proof[name]] for name in ('body', 'gaze'))
    recorded = {}
    for state, modes in audit['states'].items():
        frame, phase = map(float, state.split(':'))
        for label, row in modes.items():
            pairs = row.get('newSkinSelfPairs', [])
            if not pairs:
                continue
            stage['activate'](scene, gaze, label, phase, frame)
            coords, _, _ = contact['mesh_data'](body)
            mesh = body.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
            def polygon(index):
                poly = mesh.polygons[index]
                vertices = list(poly.vertices)
                return dict(id=index, vertices=vertices, centroidMetres=coords[vertices].mean(0).tolist(),
                            material=mesh.materials[poly.material_index].name)
            locations = [dict(polygons=[polygon(first), polygon(second)]) for first, second in pairs]
            all_centres = np.array([p['centroidMetres'] for pair in locations for p in pair['polygons']])
            recorded[f'{state}:{label}'] = dict(newPairs=len(locations), centroidBoundsMetres=[all_centres.min(0).tolist(),
                all_centres.max(0).tolist()], witnesses=locations)

    stage['activate'](scene, gaze, 'control', 1., 1.)
    previous['view_setup'](scene, 'portrait-front', 0.)
    camera = scene.camera.matrix_world.copy()
    rig = bpy.data.objects['AFN69_BODY_CONTROLS']
    head0 = (rig.matrix_world @ rig.pose.bones['Head'].matrix).copy()
    config = read_json(ROOT.parent / 'r0477-hair-shader-isolation/material-probe.json')['view']
    scene.view_settings.view_transform = config['transform']
    scene.view_settings.look = config['look']
    scene.view_settings.exposure = config['exposure']
    scene.render.use_persistent_data = False
    for key, value in config['cycles'].items():
        setattr(scene.cycles, key, value)
    render = scene.render
    render.resolution_x = render.resolution_y = 960
    render.use_border = render.use_crop_to_border = True
    render.border_min_x, render.border_max_x = .235, .765
    render.border_min_y, render.border_max_y = .345, .565
    captures = {}
    for label in stage['MODES']:
        stage['activate'](scene, gaze, label, 1., 37.)
        head = rig.matrix_world @ rig.pose.bones['Head'].matrix
        scene.camera.matrix_world = head @ head0.inverted() @ camera
        path = ROOT / f'{label}-frame37-closed.png'
        assert not path.exists()
        render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        captures[label] = dict(path=str(path), sha256=digest(path), frame=37, blink=1.,
            camera=[list(row) for row in scene.camera.matrix_world], exposure=scene.view_settings.exposure)
        print('R499_FAILURE_WITNESS', label, flush=True)
    assert digest(source) == proof['source']['sha256']
    write_json(ROOT / 'failure-witness.json', dict(source=proof['source'], polygonCentroids=recorded, captures=captures))


if __name__ == '__main__':
    main()
