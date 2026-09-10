import json
import math
import random
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-owned-hair-material-r129.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r129-family-root-lift-r141-sweep"
MAIN = "AevryndFemaleCC0LongHairStudyMain_v249r85"
BODY = "AevryndFemaleBodyBaseV118"
VARIANTS = (
    ("a-baseline", 0.0),
    ("b-root-lift-2mm", 0.002),
    ("c-root-lift-4mm", 0.004),
    ("d-root-lift-6mm", 0.006),
)
EARLY_FRACTION = 0.35
NEAR_HEAD_M = 0.030
FAMILY_CELL_M = 0.014


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, location, target, lens):
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    bpy.context.scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


def body_tree(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, faces, all_triangles=False)


def family_factor(root):
    family_x = round(root.x / FAMILY_CELL_M)
    family_y = round(root.y / FAMILY_CELL_M)
    rng = random.Random(249141000 + family_x * 1009 + family_y * 9176)
    return rng.uniform(0.78, 1.22)


def restore(obj, original):
    for index, position in enumerate(original):
        obj.data.points[index].position = position


def apply_root_lift(obj, tree, maximum_lift):
    world_matrix = obj.matrix_world
    inverse = world_matrix.inverted()
    modified = 0
    maximum = 0.0
    families = set()
    for curve in obj.data.curves:
        root_world = world_matrix @ obj.data.points[curve.first_point_index].position
        family = (round(root_world.x / FAMILY_CELL_M), round(root_world.y / FAMILY_CELL_M))
        families.add(family)
        amplitude = maximum_lift * family_factor(root_world)
        for local_index in range(1, curve.points_length):
            t = local_index / max(1, curve.points_length - 1)
            if t >= EARLY_FRACTION:
                break
            point_index = curve.first_point_index + local_index
            world = world_matrix @ obj.data.points[point_index].position
            nearest = tree.find_nearest(world)
            if nearest is None or nearest[1] is None or nearest[3] > NEAR_HEAD_M:
                continue
            phase = t / EARLY_FRACTION
            weight = math.sin(math.pi * phase) ** 1.35
            delta = nearest[1].normalized() * amplitude * weight
            obj.data.points[point_index].position = inverse @ (world + delta)
            modified += 1
            maximum = max(maximum, delta.length)
    return modified, maximum, len(families)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
OUT.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
main = bpy.data.objects[MAIN]
original = [point.position.copy() for point in main.data.points]
tree = body_tree(bpy.data.objects[BODY])
camera = bpy.data.objects["Aevrynd Review Camera"]
views = (
    ("front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
    ("three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88),
    ("top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
    ("back", (0.0, 2.10, 1.56), (0.0, 0.02, 1.54), 82),
)
report = {"source": str(SOURCE), "earlyFraction": EARLY_FRACTION, "variants": []}

for name, lift in VARIANTS:
    restore(main, original)
    modified, maximum, family_count = apply_root_lift(main, tree, lift)
    bpy.context.view_layer.update()
    for suffix, location, target, lens in views:
        render(camera, f"{name}-{suffix}", location, target, lens)
    report["variants"].append({
        "name": name,
        "nominalLiftM": lift,
        "maximumDisplacementM": maximum,
        "modifiedControlPoints": modified,
        "familyCount": family_count,
    })

(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R141_FAMILY_ROOT_LIFT=" + json.dumps(report, sort_keys=True))
