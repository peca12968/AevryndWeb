import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-r2.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-r4.blend"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249-mainline-hair-r4"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
MAIN = "AevryndFemaleGuideBob_v378"
OVERLAY = "AevryndFemaleBackSeamLocks_v249r4"
BODY = "AevryndFemaleBodyBaseV118"
POINTS = 20
FOLLOW = 11
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

# Follow 0 of each 25-strand group is the authored guide.  Choose rear guides
# nearest the part, then build a separate crossover layer from them.
guide_curves = [curve for curve in main.data.curves if curve.index % 25 == 0]
anchors = []
for side in (-1.0, 1.0):
    candidates = [
        curve for curve in guide_curves
        if (curve.points[0].position.x < 0.0) == (side < 0.0)
        and curve.points[0].position.y > 0.010
        and abs(curve.points[0].position.x) < 0.050
    ]
    for target_y in (0.014, 0.023, 0.032, 0.041, 0.050, 0.059, 0.066):
        remaining = [curve for curve in candidates if curve not in anchors]
        if not remaining:
            break
        anchors.append(min(
            remaining,
            key=lambda curve: abs(curve.points[0].position.y - target_y)
            + 0.35 * abs(abs(curve.points[0].position.x) - 0.020),
        ))

strands = []
for anchor_index, curve in enumerate(anchors):
    base = [point.position.copy() for point in curve.points]
    root = base[0]
    side = -1.0 if root.x < 0.0 else 1.0
    rear = smooth((root.y - 0.010) / 0.058)
    for follow in range(FOLLOW):
        phase = anchor_index * 1.61803398875 + follow * 0.73
        lateral = (follow - (FOLLOW - 1) * 0.5) * 0.00075
        strand = []
        for point_index, source_point in enumerate(base):
            t = point_index / (POINTS - 1)
            root_lock = smooth(t / 0.18)
            center_target = side * (0.010 + 0.022 * t)
            center_blend = (0.62 + 0.18 * rear) * smooth((t - 0.04) / 0.42)
            point = source_point.copy()
            point.x += (center_target - point.x) * center_blend
            point.x += lateral * root_lock
            point.x += side * math.sin(phase + t * math.pi * 1.25) * 0.0025 * smooth(t)
            point.y += math.cos(phase + t * math.pi) * 0.0014 * smooth(t)
            point.z += (follow % 4 - 1.5) * 0.0018 * smooth((t - 0.45) / 0.55)
            strand.append(point)
        strands.append(strand)

data = bpy.data.hair_curves.new("AevryndFemaleBackSeamLocksData_v249r4")
data.add_curves([POINTS] * len(strands))
data.points.foreach_set("position", [axis for strand in strands for point in strand for axis in point])
radius = data.attributes.new("radius", "FLOAT", "POINT")
radii = []
for _strand in strands:
    for point_index in range(POINTS):
        t = point_index / (POINTS - 1)
        radii.append(0.000052 * (1.0 - 0.64 * smooth(t)))
radius.data.foreach_set("value", radii)

overlay = bpy.data.objects.new(OVERLAY, data)
scene.collection.objects.link(overlay)
if main.data.materials:
    data.materials.append(main.data.materials[0])
overlay.parent = main.parent
overlay.parent_type = main.parent_type
overlay.parent_bone = main.parent_bone
overlay.matrix_world = main.matrix_world.copy()
overlay["aevrynd_layer"] = "hair.overlay.back_seam"
overlay["aevrynd_mainline_base"] = "v249"
overlay["aevrynd_candidate"] = "v249-mainline-hair-r4"
overlay["aevrynd_guide_count"] = len(anchors)
overlay["aevrynd_follow_per_guide"] = FOLLOW
overlay["aevrynd_mainline_hair_collision"] = True

projection_counts = {}
for iteration in range(6):
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
scene["aevrynd_hair_candidate"] = "v249-mainline-hair-r4"
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
print("AEVRYND_V249_MAINLINE_HAIR_R4=" + json.dumps({
    "output": str(OUTPUT),
    "overlay_guides": len(anchors),
    "overlay_strands": len(strands),
    "overlay_points": len(strands) * POINTS,
    "projection_counts": projection_counts,
}, sort_keys=True))
