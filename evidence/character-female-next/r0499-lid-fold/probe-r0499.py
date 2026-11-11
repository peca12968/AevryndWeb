"""Attribute the closed-eye crease on the actual r498 displayed rig."""
from pathlib import Path
from runpy import run_path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parent
PARENT = ROOT.parent / 'r0498-orbit-cheek'
prior = run_path(str(PARENT / 'preview-r0498.py'))
author = prior['author']
read_json, write_json, digest = (author[key] for key in ('read_json', 'write_json', 'digest'))


def pixels(scene, mesh):
    coords = author['xyz'](mesh.vertices)
    mesh.calc_loop_triangles()
    triangles = np.empty((len(mesh.loop_triangles), 3), dtype='i4')
    mesh.loop_triangles.foreach_get('vertices', triangles.ravel())
    surface = BVHTree.FromPolygons(coords.tolist(), triangles.tolist(), all_triangles=True)
    camera = scene.camera
    corners = np.asarray(camera.data.view_frame(scene=scene))
    lo, hi = corners.min(0), corners.max(0)
    output = []
    for x in (196, 204, 212, 220, 420, 428, 436, 444):
        for y in (332, 337, 342, 347, 352, 357, 362, 367):
            position = Vector((lo[0] + (hi[0] - lo[0]) * (x + .5) / 640,
                               hi[1] - (hi[1] - lo[1]) * (y + .5) / 640, lo[2]))
            direction = camera.matrix_world.to_3x3() @ position.normalized()
            hit, normal, face, _ = surface.ray_cast(camera.matrix_world.translation, direction, 2.)
            if hit is not None:
                output.append(dict(pixel=[x,y], world=list(hit), normal=list(normal), vertices=triangles[face].tolist()))
    return output


def main():
    proof = read_json(PARENT / 'construction-receipt.json')
    source = Path(proof['source']['path'])
    assert digest(source) == proof['source']['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False, use_scripts=False)
    scene = bpy.context.scene
    body, gaze = (bpy.data.objects[proof[name]] for name in ('body', 'gaze'))
    hair = bpy.data.objects[proof['hair']['object']]
    layers = [bpy.data.objects[name] for name in prior['LAYERS']]
    records = {}
    prior['view_setup'](scene, 'portrait-front', 0.)
    for phase in (0., .5, .82, 1.):
        author['blink'](scene, gaze, phase)
        current = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
        records[str(phase)] = pixels(scene, current.data)
    author['blink'](scene, gaze, 1.)
    for obj in list(scene.objects):
        if obj.type == 'CURVES' and obj != hair and obj.hide_render:
            data = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if not data.users:
                bpy.data.hair_curves.remove(data)
    config = read_json(ROOT.parent / 'r0477-hair-shader-isolation/material-probe.json')['view']
    scene.view_settings.view_transform = config['transform']
    scene.view_settings.look = config['look']
    scene.view_settings.exposure = config['exposure']
    for key, value in config['cycles'].items():
        setattr(scene.cycles, key, value)
    scene.render.use_persistent_data = False
    render = scene.render
    render.resolution_x = render.resolution_y = 960
    render.use_border = render.use_crop_to_border = True
    render.border_min_x, render.border_max_x = .235, .765
    render.border_min_y, render.border_max_y = .365, .565
    scene.cycles.samples = 16
    captures = {}
    for label in ('complete', 'without-lash-and-tear', 'clay'):
        if label == 'without-lash-and-tear':
            for obj in layers[2:]:
                obj.hide_render = True
        if label == 'clay':
            material = bpy.data.materials.new('R499 transient clay inspection')
            material.use_nodes = True
            node = material.node_tree.nodes.get('Principled BSDF')
            node.inputs['Base Color'].default_value = (.37, .32, .29, 1.)
            node.inputs['Roughness'].default_value = .82
            for index, mat in enumerate(body.data.materials):
                if mat and 'skin' in mat.name.lower():
                    body.data.materials[index] = material
        file = ROOT / f'probe-{label}.png'
        assert not file.exists()
        render.filepath = str(file)
        bpy.ops.render.render(write_still=True)
        captures[label] = dict(path=str(file), sha256=digest(file), hiddenLayers=[obj.name for obj in layers if obj.hide_render])
        print('R499_PROBE', label, flush=True)
    assert digest(source) == proof['source']['sha256']
    write_json(ROOT / 'fold-probe.json', dict(source=proof['source'], captures=captures, rays=records,
        blinkLayout=int(gaze['R448_Blink_Layout']), lashAttributes=[attr.name for attr in layers[-1].data.attributes]))


if __name__ == '__main__':
    main()
