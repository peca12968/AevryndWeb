import json
import math
from pathlib import Path

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-r12.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-r14.blend"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249-mainline-hair-r14"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
BODY = "AevryndFemaleBodyBaseV118"
RIG = "AevryndFemaleRig"
MAIN_HAIR = "AevryndFemaleGuideBob_v249r12"
FILL_HAIR = "AevryndFemaleNapeFiberFill_v249r14"
POINTS = 20
GUIDES = 44
FOLLOW = 14


def fract(value):
    return value - math.floor(value)


def rand(index, salt=0.0):
    return fract(math.sin(index * 12.9898 + salt * 78.233) * 43758.5453)


def smooth(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
body = bpy.data.objects[BODY]
rig = bpy.data.objects[RIG]
main_hair = bpy.data.objects[MAIN_HAIR]

depsgraph = bpy.context.evaluated_depsgraph_get()
evaluated = body.evaluated_get(depsgraph)
mesh = evaluated.to_mesh()
body_tree = BVHTree.FromPolygons(
    [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices],
    [tuple(poly.vertices) for poly in mesh.polygons],
    all_triangles=False,
)
evaluated.to_mesh_clear()


def posterior_surface(x, z, offset):
    hit = body_tree.ray_cast(Vector((x, 0.34, z)), Vector((0.0, -1.0, 0.0)), 0.55)
    if hit[0] is None or hit[1] is None:
        raise RuntimeError(f"No posterior body hit at x={x:.5f}, z={z:.5f}")
    normal = hit[1].normalized()
    return hit[0] + normal * offset


guide_curves = []
for guide_index in range(GUIDES):
    lane = guide_index / (GUIDES - 1)
    root_x = -0.026 + 0.052 * lane
    phase = rand(guide_index, 1.0) * math.tau
    root_z = 1.682 + 0.018 * rand(guide_index, 2.0)
    end_z = 1.407 + 0.047 * rand(guide_index, 3.0)
    curve = []
    for point_index in range(POINTS):
        t = point_index / (POINTS - 1)
        z = root_z * (1.0 - t) + end_z * t
        spread = 0.003 + 0.011 * smooth(t)
        x = root_x + math.sin(phase + t * math.pi * (0.85 + 0.25 * rand(guide_index, 4.0))) * spread
        x += (lane - 0.5) * 0.008 * smooth(t)
        surface_offset = 0.0058 + 0.0072 * smooth(t)
        point = posterior_surface(x, z, surface_offset)
        point.y += math.cos(phase + t * math.tau * 0.72) * 0.0018 * smooth(t)
        curve.append(point)
    guide_curves.append(curve)

strands = []
for guide_index, guide in enumerate(guide_curves):
    for follow_index in range(FOLLOW):
        angle = math.tau * rand(guide_index * 29 + follow_index, 5.0)
        radius = 0.00045 + 0.0022 * math.sqrt(rand(guide_index * 29 + follow_index, 6.0))
        length_jitter = (rand(guide_index * 29 + follow_index, 7.0) - 0.5) * 0.026
        strand = []
        for point_index, base in enumerate(guide):
            t = point_index / (POINTS - 1)
            point = base.copy()
            point.x += math.cos(angle) * radius * (0.65 + 0.35 * smooth(t))
            point.y += math.sin(angle) * radius * (0.65 + 0.35 * smooth(t))
            point.z += length_jitter * smooth(t)
            strand.append(point)
        strands.append(strand)

data = bpy.data.hair_curves.new("AevryndFemaleNapeFiberFillData_v249r14")
data.add_curves([POINTS] * len(strands))
data.points.foreach_set("position", [axis for strand in strands for point in strand for axis in point])
radius_attribute = data.attributes.new("radius", "FLOAT", "POINT")
radii = []
for _strand in strands:
    for point_index in range(POINTS):
        t = point_index / (POINTS - 1)
        radii.append(0.000062 * (1.0 - 0.58 * smooth(t)))
radius_attribute.data.foreach_set("value", radii)

fill = bpy.data.objects.new(FILL_HAIR, data)
scene.collection.objects.link(fill)
if main_hair.data.materials:
    data.materials.append(main_hair.data.materials[0])
fill.parent = rig
fill.parent_type = "BONE"
fill.parent_bone = "head"
fill.matrix_world = Matrix.Identity(4)
fill["aevrynd_layer"] = "hair.nape.fiber-underlayer"
fill["aevrynd_mainline_base"] = "v249"
fill["aevrynd_candidate"] = "v249-mainline-hair-r14"
fill["aevrynd_mainline_hair_collision"] = True
fill["aevrynd_guide_count"] = GUIDES
fill["aevrynd_follow_per_guide"] = FOLLOW

scene["aevrynd_hair_candidate"] = "v249-mainline-hair-r14"
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
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)

bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249_MAINLINE_HAIR_R14=" + json.dumps({
    "output": str(OUTPUT),
    "guides": GUIDES,
    "strands": len(strands),
    "points": len(strands) * POINTS,
}, sort_keys=True))
