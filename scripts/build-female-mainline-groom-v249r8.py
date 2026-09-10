import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-r7.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-r8.blend"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249-mainline-hair-r8"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
HAIR = "AevryndFemaleGuideBob_v378"
BODY = "AevryndFemaleBodyBaseV118"
CLEARANCE = 0.0004


def clamp(value, lo=0.0, hi=1.0):
    return max(lo, min(hi, value))


def smooth(value):
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def fract(value):
    return value - math.floor(value)


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
hair = bpy.data.objects[HAIR]
data = hair.data

maximum_shift = 0.0
for curve in data.curves:
    root = curve.points[0].position.copy()
    guide_id = curve.index // 25
    family_layer = fract(guide_id * 0.61803398875)
    # One length is shared by all 25 followers of a guide; small follower-only
    # variation prevents a stamped edge without destroying the clump shape.
    clump_length = (family_layer - 0.5) * 0.020
    follower = curve.index % 25
    follower_length = ((follower % 5) - 2) * 0.0011
    for point_index, point in enumerate(curve.points):
        t = point_index / max(1, curve.points_length - 1)
        tip = smooth((t - 0.62) / 0.38)
        old = point.position.copy()
        point.position.z += (clump_length + follower_length) * tip
        # A restrained bevel turns the terminal fibers toward the neck instead
        # of leaving a vertical cut plane.  It is strongest at the sides and
        # weaker at the face-framing front locks.
        front = smooth((-root.y - 0.020) / 0.090)
        inward = (1.0 - 0.55 * front) * tip
        point.position.x += -point.position.x * 0.040 * inward
        point.position.y += (0.018 - point.position.y) * 0.045 * inward
        maximum_shift = max(maximum_shift, (point.position - old).length)
data.update_tag()

projection_counts = {}
for iteration in range(8):
    for frame in (1, 20):
        scene.frame_set(frame)
        depsgraph = bpy.context.evaluated_depsgraph_get()
        tree = body_tree(bpy.data.objects[BODY], depsgraph)
        world = hair.matrix_world.copy()
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

hair["aevrynd_candidate"] = "v249-mainline-hair-r8"
hair["aevrynd_tip_design"] = "guide-family layered length with restrained inward bevel"
scene["aevrynd_hair_candidate"] = "v249-mainline-hair-r8"
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
print("AEVRYND_V249_MAINLINE_HAIR_R8=" + json.dumps({
    "output": str(OUTPUT),
    "maximum_shift_m": maximum_shift,
    "projection_counts": projection_counts,
}, sort_keys=True))
