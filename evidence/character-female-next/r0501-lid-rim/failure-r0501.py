"""Render the exact held pose where both r501 surfaces first overlap."""
from pathlib import Path
from runpy import run_path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
study = run_path(str(ROOT/'author-r0501.py'))
stage = study['stage']
read_json, write_json, digest = (study[key] for key in ('read_json','write_json','digest'))
activate = study['activate']


def main():
    proof = read_json(ROOT/'construction-receipt.json')
    result = read_json(ROOT/'facial-contact.json')
    source = Path(proof['source']['path'])
    assert result['source']==proof['source'] and digest(source)==proof['source']['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False, use_scripts=False)
    scene = bpy.context.scene
    gaze = bpy.data.objects[proof['gaze']]
    config = read_json(ROOT.parent/'r0477-hair-shader-isolation/material-probe.json')['view']
    scene.view_settings.view_transform = config['transform']
    scene.view_settings.look = config['look']
    scene.view_settings.exposure = config['exposure']
    for key, value in config['cycles'].items():
        setattr(scene.cycles,key,value)
    captures = {}
    for mode in study['MODES']:
        activate(scene,gaze,mode,.75,1.)
        stage['previous']['view_setup'](scene,'portrait-front',0.)
        render = scene.render
        render.use_persistent_data = False
        render.resolution_x = render.resolution_y = 960
        render.use_border = render.use_crop_to_border = True
        render.border_min_x, render.border_max_x = .235,.765
        render.border_min_y, render.border_max_y = .365,.565
        output = ROOT/f'{mode}-failure-075.png'
        render.filepath = str(output)
        bpy.ops.render.render(write_still=True)
        points = []
        for row in result['states']['1:0.75'].get(mode,{}).get('skin',{}).get('new',[]):
            x,y,_ = world_to_camera_view(scene,scene.camera,Vector(row['locationMetres']))
            points.append([(x-render.border_min_x)/(render.border_max_x-render.border_min_x),
                           (render.border_max_y-y)/(render.border_max_y-render.border_min_y)])
        captures[mode] = dict(path=str(output),sha256=digest(output),positionsNormalized=points)
    write_json(ROOT/'failure-capture.json',dict(source=proof['source'], pose='1:0.75',captures=captures,
        markers='Midpoints of paired triangle centroids projected to the rendered camera. The marks locate the mesh witness; the actual intersection can be below the visible outer surface.'))


if __name__=='__main__':
    main()

