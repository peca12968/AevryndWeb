"""Identify the real displayed skin and available facial controls in the r497 source."""
from pathlib import Path
from runpy import run_path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parent
PARENT = ROOT.parent / 'r0497-feathered-rear-locks'
author = run_path(str(PARENT / 'author-r0497.py'))


def main():
    proof = author['read_json'](PARENT / 'construction-receipt.json')
    source = Path(proof['source']['path'])
    assert author['digest'](source) == proof['source']['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False, use_scripts=False)
    scene = bpy.context.scene
    objects = []
    for obj in scene.objects:
        if obj.type not in ('ARMATURE', 'MESH', 'CURVES', 'EMPTY'):
            continue
        keys = getattr(obj.data, 'shape_keys', None)
        row = dict(name=obj.name, kind=obj.type, visible=not obj.hide_render, parent=obj.parent.name if obj.parent else None,
                   transform=[list(value) for value in obj.matrix_world], modifiers=[(mod.name, mod.type) for mod in obj.modifiers],
                   keys=[(key.name, float(key.value)) for key in keys.key_blocks] if keys else [],
                   drivers=[driver.data_path for driver in keys.animation_data.drivers] if keys and keys.animation_data else [],
                   properties=[key for key in obj.keys() if 'blink' in key.lower() or 'gaze' in key.lower()])
        if obj.type == 'MESH':
            row['vertices'] = len(obj.data.vertices)
            row['materials'] = [mat.name if mat else None for mat in obj.data.materials]
        objects.append(row)
    skin = bpy.data.objects[author['BODY']]
    coords = np.empty((len(skin.data.vertices), 3), dtype='f4')
    skin.data.vertices.foreach_get('co', coords.ravel())
    bounds = []
    for x0, x1 in ((.012, .025), (.025, .042), (.042, .059), (.059, .072)):
        for z0, z1 in ((1.446, 1.466), (1.466, 1.486), (1.486, 1.506), (1.506, 1.526)):
            selected = coords[(coords[:, 0] >= x0) & (coords[:, 0] < x1) & (coords[:, 2] >= z0)
                              & (coords[:, 2] < z1) & (coords[:, 1] < -.046)]
            if len(selected):
                bounds.append(dict(x=[x0, x1], z=[z0, z1], count=len(selected),
                                   y=np.quantile(selected[:, 1], [.05, .25, .5, .75, .95]).tolist()))
    author['write_json'](ROOT / 'face-inspection.json', dict(source=proof['source'], objects=objects, skin=skin.name,
        frontSkinWindows=bounds, frame=scene.frame_current, camera=scene.camera.name))
    print('R498_FACE_INSPECTION', len(objects), skin.name, flush=True)


if __name__ == '__main__':
    main()
