import json
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-satin-hair-r192.blend"
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-mouth-placement-r198.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r199-mouth-clearance-sweep"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-mouth-clearance-r199.sweep-report.json"
BODY = "AevryndFemaleBodyBaseV118"
LAYERS = ("Lip_Upper", "Mouth_WetLine")
VARIANTS = (("a-control", 0.0), ("b-015mm", 0.00015), ("c-030mm", 0.00030), ("d-050mm", 0.00050), ("e-080mm", 0.00080))


def geometry(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return points, faces


def tree(obj, depsgraph):
    points, faces = geometry(obj, depsgraph)
    return BVHTree.FromPolygons(points, faces, all_triangles=False)


def overlaps(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    scene = bpy.context.scene
    result = {}
    for frame in (1, 20):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        body_tree = tree(bpy.data.objects[BODY], depsgraph)
        result[str(frame)] = {name: len(body_tree.overlap(tree(bpy.data.objects[name], depsgraph))) for name in LAYERS}
    return result


def offset_layer(obj, offset):
    obj.data = obj.data.copy()
    inverse = obj.matrix_world.inverted()
    for vertex in obj.data.vertices:
        world = obj.matrix_world @ vertex.co
        world.y -= offset
        vertex.co = inverse @ world
    obj.data.update()


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, filename):
    scene = bpy.context.scene
    scene.frame_set(1)
    camera.location = (0.0, -0.47, 1.525)
    camera.data.lens = 122
    look_at(camera, (0.0, -0.075, 1.520))
    scene.render.resolution_x, scene.render.resolution_y = (1200, 900)
    scene.render.filepath = str(OUT / filename)
    bpy.ops.render.render(write_still=True)


OUT.mkdir(parents=True, exist_ok=True)
baseline = overlaps(BASELINE)
report = {"baseline": str(BASELINE), "source": str(SOURCE), "baselineOverlaps": baseline, "variants": {}}
for label, offset in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    for name in LAYERS:
        offset_layer(bpy.data.objects[name], offset)
    values = {}
    for frame in (1, 20):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        body_tree = tree(bpy.data.objects[BODY], depsgraph)
        values[str(frame)] = {name: len(body_tree.overlap(tree(bpy.data.objects[name], depsgraph))) for name in LAYERS}
    values["passesBaseline"] = all(values[frame][name] <= baseline[frame][name] for frame in ("1", "20") for name in LAYERS)
    values["offsetMm"] = offset * 1000.0
    report["variants"][label] = values
    render(bpy.data.objects["Aevrynd Review Camera"], f"{label}-mouth-front.png")

REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R199_MOUTH_CLEARANCE=" + json.dumps(report, sort_keys=True))
