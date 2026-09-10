import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cc0-long-hair-multiframe-r89.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cc0-root-density-r90.blend"
OUT = ROOT.parent / "Temp/female-realism/v249-mainline-cc0-root-density-r90"
MAIN = "AevryndFemaleCC0LongHairFitMain_v249r86"
ROOT_LAYER = "AevryndFemaleCC0LongHairRootDensity_v249r90"
BODY = "AevryndFemaleBodyBaseV118"
TARGET = 0.0014


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def evaluated_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, faces, all_triangles=False)


def project_clear(tree, point):
    hit = tree.find_nearest(point)
    if hit is None or hit[1] is None or hit[3] > 0.030:
        return point
    normal = hit[1].normalized()
    signed = (point - hit[0]).dot(normal)
    return point if signed >= TARGET else hit[0] + normal * TARGET


def render(camera, name, location, target, lens):
    scene = bpy.context.scene
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
OUT.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
scene.frame_set(1)
tree = evaluated_tree(bpy.data.objects[BODY], bpy.context.evaluated_depsgraph_get())
main = bpy.data.objects[MAIN]
records = []
for curve_index, curve in enumerate(main.data.curves):
    if curve_index % 2:
        continue
    count = min(7, curve.points_length)
    source = [main.matrix_world @ main.data.points[curve.first_point_index + i].position for i in range(count)]
    if len(source) < 3:
        continue
    for side_sign in (-1.0, 1.0):
        strand = []
        for index, point in enumerate(source):
            before = source[max(0, index - 1)]
            after = source[min(len(source) - 1, index + 1)]
            tangent = (after - before).normalized() if (after - before).length_squared else Vector((0.0, 0.0, -1.0))
            hit = tree.find_nearest(point)
            normal = hit[1].normalized() if hit and hit[1] else Vector((0.0, -1.0, 0.0))
            side = normal.cross(tangent)
            if side.length_squared < 1.0e-10:
                side = Vector((1.0, 0.0, 0.0))
            side.normalize()
            phase = math.sin(curve_index * 1.618 + index * 0.71)
            offset = side * side_sign * (0.00038 + 0.00012 * phase)
            strand.append(project_clear(tree, point + offset))
        records.append(strand)

data = bpy.data.hair_curves.new(ROOT_LAYER + "Data")
data.add_curves([len(strand) for strand in records])
radius = data.attributes.get("radius") or data.attributes.new("radius", "FLOAT", "POINT")
flat = 0
for strand in records:
    for point_index, point in enumerate(strand):
        data.points[flat].position = point
        t = point_index / max(1, len(strand) - 1)
        radius.data[flat].value = 0.000026 * (1.0 - t) + 0.000004 * t
        flat += 1
if main.data.materials:
    data.materials.append(main.data.materials[0])
root = bpy.data.objects.new(ROOT_LAYER, data)
scene.collection.objects.link(root)
root["aevrynd_layer"] = "hair.root_density.short-fibers"
root["aevrynd_revision"] = "v249-mainline-cc0-root-density-r90"
root["aevrynd_runtime_dependency"] = "none"
rig = bpy.data.objects["AevryndFemaleRig"]
world = root.matrix_world.copy()
root.parent = rig
root.parent_type = "BONE"
root.parent_bone = "head"
root.matrix_world = world

scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_mainline_revision"] = "cc0-root-density-r90"
scene["aevrynd_release_state"] = "R90_VISUAL_AND_MULTIFRAME_COLLISION_REVIEW_REQUIRED"
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
camera = bpy.data.objects["Aevrynd Review Camera"]
for args in (
    ("01-front", (0.0, -2.15, 1.55), (0.0, 0.0, 1.55), 82),
    ("02-three-quarter", (1.28, -1.72, 1.57), (0.0, 0.0, 1.55), 82),
    ("03-back", (0.0, 2.10, 1.56), (0.0, 0.02, 1.54), 82),
    ("04-top", (0.0, -0.30, 2.35), (0.0, 0.0, 1.66), 78),
    ("05-face-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
):
    render(camera, *args)

report = {
    "source": str(SOURCE), "output": str(OUTPUT), "layer": "hair.root_density.short-fibers",
    "curves": len(data.curves), "points": len(data.points), "source_stride": 2,
    "offset_m": [0.00026, 0.00050], "target_clearance_m": TARGET,
    "status": "VISUAL_AND_COLLISION_REVIEW_REQUIRED",
}
(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249_CC0_ROOT_DENSITY_R90=" + json.dumps(report, sort_keys=True))
