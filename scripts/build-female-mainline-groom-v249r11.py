import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-r9.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-r11.blend"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249-mainline-hair-r11"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
HAIR = "AevryndFemaleGuideBob_v249r9"
SOLIDS = (
    "AevryndFemaleBodyBaseV118",
    "Clothing_Bandeau_v160",
    "Clothing_BandeauBinding_v162",
    "Clothing_BodyFitShorts_v135",
)
TARGET_CLEARANCE = 0.00065
NEAR_LIMIT = 0.025


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def surface_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    polygons = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, polygons, all_triangles=False)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
hair = bpy.data.objects[HAIR]
data = hair.data
projection_counts = {}

for iteration in range(10):
    for frame in (1, 20):
        scene.frame_set(frame)
        depsgraph = bpy.context.evaluated_depsgraph_get()
        trees = {name: surface_tree(bpy.data.objects[name], depsgraph) for name in SOLIDS}
        world = hair.matrix_world.copy()
        inverse = world.inverted()
        for solid_name, tree in trees.items():
            moved = 0
            maximum_move = 0.0
            for point in data.points:
                world_point = world @ point.position
                nearest = tree.find_nearest(world_point, NEAR_LIMIT)
                if nearest is None or nearest[1] is None or nearest[3] > NEAR_LIMIT:
                    continue
                location, normal = nearest[0], nearest[1].normalized()
                signed = (world_point - location).dot(normal)
                if signed < TARGET_CLEARANCE:
                    corrected = location + normal * TARGET_CLEARANCE
                    maximum_move = max(maximum_move, (corrected - world_point).length)
                    point.position = inverse @ corrected
                    moved += 1
            projection_counts[f"iteration_{iteration + 1}_frame_{frame}_{solid_name}"] = {
                "moved": moved,
                "maximum_move_m": maximum_move,
            }
            data.update_tag()

hair["aevrynd_candidate"] = "v249-mainline-hair-r11"
hair["aevrynd_collision_solution"] = "alternating body and garment surface constraints at frames 1 and 20"
scene["aevrynd_hair_candidate"] = "v249-mainline-hair-r11"
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
print("AEVRYND_V249_MAINLINE_HAIR_R11=" + json.dumps({
    "output": str(OUTPUT),
    "target_clearance_m": TARGET_CLEARANCE,
    "near_limit_m": NEAR_LIMIT,
    "projection_counts": projection_counts,
}, sort_keys=True))
