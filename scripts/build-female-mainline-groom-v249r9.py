import json
import math
from pathlib import Path

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-r7.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-r9.blend"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249-mainline-hair-r9"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
BODY = "AevryndFemaleBodyBaseV118"
RIG = "AevryndFemaleRig"
OLD_HAIR = "AevryndFemaleGuideBob_v378"
NEW_HAIR = "AevryndFemaleGuideBob_v249r9"
POINTS = 20
FOLLOW = 25
CLEARANCE = 0.0020


def clamp(value, lo=0.0, hi=1.0):
    return max(lo, min(hi, value))


def smooth(value):
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def fract(value):
    return value - math.floor(value)


def rand(index, salt=0.0):
    return fract(math.sin(index * 12.9898 + salt * 78.233) * 43758.5453)


def part_x(y):
    return -0.032 + 0.027 * smooth((y + 0.105) / 0.170)


def bezier(p0, p1, p2, p3, t):
    u = 1.0 - t
    return p0 * u ** 3 + p1 * 3.0 * u * u * t + p2 * 3.0 * u * t * t + p3 * t ** 3


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def evaluated_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    polygons = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, polygons, all_triangles=False)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
body = bpy.data.objects[BODY]
rig = bpy.data.objects[RIG]
old_hair = bpy.data.objects[OLD_HAIR]
old_hair.hide_render = True
old_hair.hide_viewport = True
old_hair["aevrynd_mainline_hair_collision"] = False

depsgraph = bpy.context.evaluated_depsgraph_get()
body_bvh = evaluated_tree(body, depsgraph)
center = Vector((0.0, -0.012, 1.635))
radius_x, radius_y, radius_z = 0.083, 0.108, 0.096
guides = []
guide_meta = []
guide_index = 0

for row in range(23):
    y = -0.110 + row * (0.188 / 22.0)
    y_norm = (y - center.y) / radius_y
    half_x = radius_x * math.sqrt(max(0.05, 1.0 - y_norm * y_norm))
    base_columns = max(12, round(30 * half_x / radius_x))
    posterior = y > 0.014
    columns = base_columns + (1 if posterior and base_columns % 2 == 0 else 0)
    for column in range(columns):
        if posterior:
            u = column / max(1, columns - 1)
        else:
            u = (column + 0.5 + (0.35 if row % 2 else 0.0)) / columns
        x = -half_x + 2.0 * half_x * u
        seam = part_x(y)
        if not posterior and abs(x - seam) < 0.0008:
            continue
        x_norm = x / radius_x
        z = center.z + radius_z * math.sqrt(max(0.0, 1.0 - x_norm * x_norm - y_norm * y_norm))
        nearest = body_bvh.find_nearest(Vector((x, y, z)), 0.050)
        if nearest is None or nearest[1] is None or nearest[1].z < -0.05:
            continue
        location, normal = nearest[0], nearest[1].normalized()
        root = location + normal * CLEARANCE
        if abs(x - seam) < 0.0015:
            side = -1.0 if (row + column) % 2 == 0 else 1.0
        else:
            side = -1.0 if x < seam else 1.0
        front = clamp((-y - 0.015) / 0.095)
        back = clamp((y - 0.005) / 0.080)
        crown = clamp((z - 1.670) / 0.070)
        length = 0.220 + 0.055 * crown + 0.028 * back + 0.040 * (rand(guide_index, 1.0) - 0.5)
        end_z = root.z - length
        outward = 0.045 + 0.045 * crown + 0.035 * front
        rear_centering = smooth((back - 0.18) / 0.82)
        outward *= 1.0 - 0.78 * rear_centering
        end_x = root.x * (1.0 - 0.30 * rear_centering) + side * outward
        end_x = clamp(end_x, -0.145, 0.145)
        end_y = root.y + 0.030 * back - 0.012 * front
        p0 = root
        p1 = root + normal * (0.006 + 0.004 * crown) + Vector((
            side * (0.018 + 0.012 * front) * (1.0 - 0.60 * rear_centering),
            0.010 * rear_centering - 0.003 * front,
            0.004,
        ))
        p2 = Vector((end_x - side * 0.008 * (1.0 - rear_centering), end_y, end_z + 0.075))
        p3 = Vector((end_x, end_y, end_z))
        phase = rand(guide_index, 2.0) * math.tau
        wave_amp = 0.006 + 0.012 * rand(guide_index, 3.0)
        guide = []
        for point_index in range(POINTS):
            t = point_index / (POINTS - 1)
            point = bezier(p0, p1, p2, p3, t)
            wave_weight = smooth((t - 0.22) / 0.78)
            wave = math.sin(phase + t * math.tau * (0.75 + rand(guide_index, 4.0)))
            point.x += side * wave_amp * wave * wave_weight
            point.y += wave_amp * 0.55 * math.cos(phase + t * math.tau) * wave_weight
            if front > 0.25:
                avoid = front * smooth((t - 0.10) / 0.42)
                safe_x = side * (0.078 + 0.035 * smooth(t))
                point.x = min(point.x, point.x * (1.0 - avoid) + safe_x * avoid) if side < 0.0 else max(point.x, point.x * (1.0 - avoid) + safe_x * avoid)
            guide.append(point)
        guides.append(guide)
        guide_meta.append((root, normal, side, guide_index))
        guide_index += 1

strands = []
for guide, (root, normal, side, index) in zip(guides, guide_meta):
    tangent = Vector((normal.z, 0.0, -normal.x)).normalized()
    bitangent = normal.cross(tangent).normalized()
    for follow in range(FOLLOW):
        if follow == 0:
            strands.append([point.copy() for point in guide])
            continue
        angle = math.tau * rand(index * 31 + follow, 5.0)
        radius = 0.0010 + 0.0042 * math.sqrt(rand(index * 31 + follow, 6.0))
        offset = tangent * (math.cos(angle) * radius) + bitangent * (math.sin(angle) * radius)
        length_jitter = (rand(index * 31 + follow, 7.0) - 0.5) * 0.032
        follow_phase = rand(index * 31 + follow, 8.0) * math.tau
        strand = []
        for point_index, base in enumerate(guide):
            t = point_index / (POINTS - 1)
            point = base + offset * (0.82 + 0.18 * smooth(t))
            point.z += length_jitter * smooth(t)
            fine = math.sin(follow_phase + t * math.tau * 1.35) * 0.0012 * smooth(t)
            point.x += side * fine
            point.y += fine * 0.45
            strand.append(point)
        strands.append(strand)

data = bpy.data.hair_curves.new("AevryndFemaleGuideBobData_v249r9")
data.add_curves([POINTS] * len(strands))
data.points.foreach_set("position", [axis for strand in strands for point in strand for axis in point])
radius_attribute = data.attributes.new("radius", "FLOAT", "POINT")
radii = []
for _strand in strands:
    for point_index in range(POINTS):
        t = point_index / (POINTS - 1)
        radii.append(0.000055 * (1.0 - 0.62 * smooth(t)))
radius_attribute.data.foreach_set("value", radii)

hair = bpy.data.objects.new(NEW_HAIR, data)
scene.collection.objects.link(hair)
if old_hair.data.materials:
    data.materials.append(old_hair.data.materials[0])
hair.parent = rig
hair.parent_type = "BONE"
hair.parent_bone = "head"
hair.matrix_world = Matrix.Identity(4)
hair["aevrynd_layer"] = "hair.guide_follow.main"
hair["aevrynd_mainline_base"] = "v249"
hair["aevrynd_candidate"] = "v249-mainline-hair-r9"
hair["aevrynd_guide_count"] = len(guides)
hair["aevrynd_follow_per_guide"] = FOLLOW
hair["aevrynd_mainline_hair_collision"] = True

projection_counts = {}
for iteration in range(6):
    for frame in (1, 20):
        scene.frame_set(frame)
        depsgraph = bpy.context.evaluated_depsgraph_get()
        tree = evaluated_tree(body, depsgraph)
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

scene["aevrynd_mainline_base"] = "v249"
scene["aevrynd_hair_candidate"] = "v249-mainline-hair-r9"
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
print("AEVRYND_V249_MAINLINE_HAIR_R9=" + json.dumps({
    "output": str(OUTPUT),
    "guides": len(guides),
    "strands": len(strands),
    "points": len(strands) * POINTS,
    "projection_counts": projection_counts,
}, sort_keys=True))
