import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-r2.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-r5.blend"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249-mainline-hair-r5"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
MAIN = "AevryndFemaleGuideBob_v378"
OVERLAY = "AevryndFemaleBackDensityOverlap_v249r5"
BODY = "AevryndFemaleBodyBaseV118"
CLEARANCE = 0.0004


def clamp(value, lo=0.0, hi=1.0):
    return max(lo, min(hi, value))


def smooth(value):
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def body_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    polygons = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, polygons, all_triangles=False)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
main = bpy.data.objects[MAIN]
main["aevrynd_mainline_hair_collision"] = True
bpy.data.objects["AevryndFemaleScalpCoverage_v378"]["aevrynd_mainline_hair_collision"] = True

# Reuse every second authored rear fiber near the part.  This preserves the
# existing guide/follow variation while adding enough density to read at game
# distance.  Roots remain unchanged and the crossover begins after attachment.
source_curves = [
    curve for curve in main.data.curves
    if curve.index % 2 == 0
    and curve.points[0].position.y > 0.006
    and abs(curve.points[0].position.x) < 0.058
]
strands = []
for curve in source_curves:
    root = curve.points[0].position.copy()
    side = -1.0 if root.x < 0.0 else 1.0
    rear = smooth((root.y - 0.006) / 0.060)
    phase = (curve.index // 25) * 2.399963229728653
    strand = []
    for point_index, source_point in enumerate(curve.points):
        t = point_index / max(1, curve.points_length - 1)
        attach = smooth((t - 0.02) / 0.32)
        center_target = side * (0.006 + 0.020 * t)
        blend = (0.58 + 0.16 * rear) * attach
        point = source_point.position.copy()
        point.x += (center_target - point.x) * blend
        point.x += side * math.sin(phase + t * math.pi * 1.15) * 0.0028 * smooth(t)
        point.y += (0.0025 + 0.0035 * rear) * math.sin(math.pi * t)
        strand.append(point)
    strands.append(strand)

point_counts = [len(strand) for strand in strands]
data = bpy.data.hair_curves.new("AevryndFemaleBackDensityOverlapData_v249r5")
data.add_curves(point_counts)
data.points.foreach_set("position", [axis for strand in strands for point in strand for axis in point])
radius = data.attributes.new("radius", "FLOAT", "POINT")
radii = []
for strand in strands:
    for point_index in range(len(strand)):
        t = point_index / max(1, len(strand) - 1)
        radii.append(0.000054 * (1.0 - 0.62 * smooth(t)))
radius.data.foreach_set("value", radii)

overlay = bpy.data.objects.new(OVERLAY, data)
scene.collection.objects.link(overlay)
if main.data.materials:
    data.materials.append(main.data.materials[0])
overlay.parent = main.parent
overlay.parent_type = main.parent_type
overlay.parent_bone = main.parent_bone
overlay.matrix_world = main.matrix_world.copy()
overlay["aevrynd_layer"] = "hair.overlay.back_density"
overlay["aevrynd_mainline_base"] = "v249"
overlay["aevrynd_candidate"] = "v249-mainline-hair-r5"
overlay["aevrynd_source_curve_count"] = len(source_curves)
overlay["aevrynd_mainline_hair_collision"] = True

projection_counts = {}
for iteration in range(8):
    for frame in (1, 20):
        scene.frame_set(frame)
        depsgraph = bpy.context.evaluated_depsgraph_get()
        tree = body_tree(bpy.data.objects[BODY], depsgraph)
        world = overlay.matrix_world.copy()
        inverse = world.inverted()
        moved = 0
        for point in data.points:
            world_point = world @ point.position
            nearest = tree.find_nearest(world_point, 0.16)
            if nearest is None or nearest[1] is None:
                continue
            location, normal = nearest[0], nearest[1].normalized()
            signed = (world_point - location).dot(normal)
            if signed < CLEARANCE:
                point.position = inverse @ (location + normal * CLEARANCE)
                moved += 1
        projection_counts[f"iteration_{iteration + 1}_frame_{frame}"] = moved
        data.update_tag()

scene["aevrynd_mainline_base"] = "v249"
scene["aevrynd_hair_candidate"] = "v249-mainline-hair-r5"
scene["aevrynd_release_state"] = "MAINLINE_GROOM_VISUAL_AND_COLLISION_AUDIT_REQUIRED"

camera = bpy.data.objects.get("Camera") or next(obj for obj in bpy.data.objects if obj.type == "CAMERA")
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
views = (
    ("01-front", (0.0, -2.15, 1.55), (0.0, 0.0, 1.55), 82),
    ("02-three-quarter", (1.28, -1.72, 1.57), (0.0, 0.0, 1.55), 82),
    ("03-profile", (2.15, 0.0, 1.57), (0.0, 0.0, 1.55), 86),
    ("04-back", (0.0, 2.10, 1.56), (0.0, 0.02, 1.54), 82),
    ("05-top", (0.0, -0.30, 2.35), (0.0, 0.0, 1.66), 78),
)
for name, location, target, lens in views:
    scene.frame_set(1)
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)

bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249_MAINLINE_HAIR_R5=" + json.dumps({
    "output": str(OUTPUT),
    "overlay_strands": len(strands),
    "overlay_points": sum(point_counts),
    "projection_counts": projection_counts,
}, sort_keys=True))
