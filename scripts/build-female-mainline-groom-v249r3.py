import json
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-r2.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-r3.blend"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249-mainline-hair-r3"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
HAIR = "AevryndFemaleGuideBob_v378"
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
hair = bpy.data.objects[HAIR]
data = hair.data

# End the visible part at the crown.  Roots stay fixed; central rear locks cross
# the seam immediately after the root and overlap in alternating directions.
adjusted = 0
maximum_shift = 0.0
for curve in data.curves:
    root = curve.points[0].position.copy()
    if root.y <= 0.004 or abs(root.x) >= 0.060:
        continue
    side = -1.0 if root.x < 0.0 else 1.0
    center = smooth((0.060 - abs(root.x)) / 0.060)
    rear = smooth((root.y - 0.004) / 0.060)
    for point_index, point in enumerate(curve.points):
        t = point_index / max(1, curve.points_length - 1)
        rise = smooth((t - 0.015) / 0.22)
        fade = 1.0 - smooth((t - 0.52) / 0.25)
        shift = -side * (0.006 + 0.009 * rear) * center * rise * fade
        point.position.x += shift
        maximum_shift = max(maximum_shift, abs(shift))
    adjusted += 1
data.update_tag()

projection_counts = {}
for iteration in range(6):
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

hair["aevrynd_candidate"] = "v249-mainline-hair-r3"
hair["aevrynd_crown_part_termination"] = "root-locked alternating rear overlap"
scene["aevrynd_hair_candidate"] = "v249-mainline-hair-r3"
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
print("AEVRYND_V249_MAINLINE_HAIR_R3=" + json.dumps({
    "output": str(OUTPUT),
    "adjusted_curves": adjusted,
    "maximum_shift_m": maximum_shift,
    "projection_counts": projection_counts,
}, sort_keys=True))
