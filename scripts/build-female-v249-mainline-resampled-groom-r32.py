import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-face-r31.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-groom-r32.blend"
OUT = ROOT.parent / "Temp/female-realism/v249-mainline-groom-r32"
OUT.mkdir(parents=True, exist_ok=True)
BODY = "AevryndFemaleBodyBaseV118"
OLD_HAIR = ("AevryndFemaleGuideBob_v249r25", "AevryndFemaleNapeFiberFill_v249r17")
GUIDES = 320
FOLLOWERS = 28
POINTS = 24
ROOT_CLEARANCE = 0.0014


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def smooth(value):
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def fract(value):
    return value - math.floor(value)


def rnd(index, salt):
    return fract(math.sin(index * 12.9898 + salt * 78.233) * 43758.5453)


def radical_inverse(index, base):
    value = 0.0
    factor = 1.0 / base
    while index:
        value += (index % base) * factor
        index //= base
        factor /= base
    return value


def cubic(p0, p1, p2, p3, t):
    u = 1.0 - t
    return p0 * u**3 + p1 * 3.0 * u * u * t + p2 * 3.0 * u * t * t + p3 * t**3


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
body = bpy.data.objects[BODY]
depsgraph = bpy.context.evaluated_depsgraph_get()
evaluated = body.evaluated_get(depsgraph)
mesh = evaluated.to_mesh()
vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
faces = [tuple(poly.vertices) for poly in mesh.polygons]
tree = BVHTree.FromPolygons(vertices, faces, all_triangles=False)

for name in OLD_HAIR:
    obj = bpy.data.objects.get(name)
    if obj:
        obj.hide_render = True
        obj.hide_viewport = True


def scalp_half_width(y):
    yn = clamp((y + 0.112) / 0.218)
    profile = math.sin(math.pi * (0.10 + 0.82 * yn))
    return 0.050 + 0.048 * max(0.0, profile)


def part_x(y):
    return -0.026 + 0.011 * smooth((y + 0.105) / 0.205)


def scalp_point(x, y, lift=ROOT_CLEARANCE):
    cast = tree.ray_cast(Vector((x, y, 1.86)), Vector((0.0, 0.0, -1.0)), 0.38)
    if cast[0] is None:
        return None
    return cast[0] + cast[1].normalized() * lift


golden = 0.6180339887498949
guide_roots = []
candidate = 0
while len(guide_roots) < GUIDES and candidate < 20000:
    sample_index = candidate + 1
    y = -0.112 + 0.216 * radical_inverse(sample_index, 2)
    width = scalp_half_width(y)
    x = (-0.96 + 1.92 * radical_inverse(sample_index, 3)) * width
    seam = part_x(y)
    side = -1.0 if x < seam else 1.0
    part_gap = 0.00125 + 0.00045 * smooth((y + 0.04) / 0.12)
    if abs(x - seam) < part_gap:
        x = seam + side * part_gap
    root = scalp_point(x, y)
    candidate += 1
    if root is None:
        continue
    # Match the existing v249 hairline height while retaining temple recession.
    if y < -0.088:
        minimum_z = 1.646 + 0.20 * abs(x)
        if root.z < minimum_z:
            continue
    if all((root - existing).length > 0.0042 for existing in guide_roots):
        guide_roots.append(root)

if len(guide_roots) != GUIDES:
    raise RuntimeError(f"Only sampled {len(guide_roots)} of {GUIDES} roots")

strands = []
layers = []
for guide, guide_root in enumerate(guide_roots):
    seam = part_x(guide_root.y)
    side = -1.0 if guide_root.x < seam else 1.0
    front = clamp((-guide_root.y - 0.015) / 0.095)
    back = clamp((guide_root.y - 0.005) / 0.095)
    lateral = clamp(abs(guide_root.x - seam) / 0.090)
    cluster_phase = rnd(guide, 2.0) * math.tau
    exit_y = guide_root.y + 0.018 + 0.014 * front - 0.005 * back
    exit_x = side * scalp_half_width(exit_y) * (0.91 + 0.045 * rnd(guide, 3.0))
    endpoint_x = side * (0.125 + 0.016 * back + 0.010 * rnd(guide, 4.0))
    endpoint_y = -0.012 + 0.090 * back + 0.016 * (rnd(guide, 5.0) - 0.5)
    endpoint_z = 1.382 + 0.072 * rnd(guide, 6.0) + 0.015 * lateral
    flyaway_guide = guide % 23 == 0
    if flyaway_guide:
        endpoint_z += 0.025 + 0.030 * rnd(guide, 7.0)
        endpoint_x += side * 0.010

    for follower in range(FOLLOWERS):
        strand_index = guide * FOLLOWERS + follower
        angle = math.tau * fract(follower * golden + rnd(guide, 8.0))
        radius = 0.00025 if follower == 0 else 0.0030 * math.sqrt((follower + 0.4) / FOLLOWERS)
        root_y = clamp(guide_root.y + math.sin(angle) * radius, -0.113, 0.105)
        width = scalp_half_width(root_y)
        root_x = clamp(guide_root.x + math.cos(angle) * radius, -width * 0.985, width * 0.985)
        local_seam = part_x(root_y)
        local_side = -1.0 if root_x < local_seam else 1.0
        if local_side != side:
            root_x = local_seam + side * 0.0012
        root = scalp_point(root_x, root_y, ROOT_CLEARANCE + 0.00025 * rnd(strand_index, 9.0))
        if root is None:
            continue

        surface = []
        for sample in range(10):
            q = sample / 9.0
            s = smooth(q)
            sx = root_x + (exit_x - root_x) * s
            sy = root_y + (exit_y - root_y) * s
            lift = ROOT_CLEARANCE + 0.0018 * math.sin(math.pi * q) ** 2
            point = scalp_point(sx, sy, lift)
            if point is None:
                break
            surface.append(point)
        if len(surface) != 10:
            continue

        p0 = surface[-1]
        tangent = (surface[-1] - surface[-2]).normalized()
        end_variation = (rnd(strand_index, 10.0) - 0.5)
        p3 = Vector((
            endpoint_x + side * 0.0045 * end_variation,
            endpoint_y + 0.008 * (rnd(strand_index, 11.0) - 0.5),
            endpoint_z + 0.018 * end_variation,
        ))
        p1 = p0 + tangent * 0.046 + Vector((side * 0.010, 0.004 * front, -0.012))
        p2 = p3 + Vector((-side * 0.008, -0.004 * front, 0.090 + 0.015 * rnd(guide, 12.0)))
        strand = []
        for point_index in range(POINTS):
            t = point_index / (POINTS - 1)
            if t <= 0.38:
                f = (t / 0.38) * 9.0
                a = min(8, int(f))
                point = surface[a].lerp(surface[a + 1], f - a)
            else:
                q = (t - 0.38) / 0.62
                point = cubic(p0, p1, p2, p3, q)
            free = smooth((t - 0.32) / 0.68)
            shared = math.sin(cluster_phase + t * math.tau * 0.68) * 0.0023
            fine = math.sin(rnd(strand_index, 13.0) * math.tau + t * math.tau * 1.4) * 0.00045
            point.x += side * (shared + fine) * free
            point.y += (shared * 0.24 + fine * 0.35) * free
            strand.append(point)
        strands.append(strand)
        layers.append(2 if flyaway_guide and follower < 5 else (1 if lateral > 0.72 else 0))

if not strands:
    raise RuntimeError("No strands survived scalp surface projection")
hair_data = bpy.data.hair_curves.new("AevryndFemaleResampledGroomData_v249r32")
hair_data.add_curves([POINTS] * len(strands))
hair_data.points.foreach_set("position", [axis for strand in strands for point in strand for axis in point])
radius_attribute = hair_data.attributes.new("radius", "FLOAT", "POINT")
radii = []
for layer in layers:
    scale = 0.72 if layer == 2 else (0.92 if layer == 1 else 1.0)
    for point_index in range(POINTS):
        t = point_index / (POINTS - 1)
        radii.append(scale * 0.000042 * (1.0 - 0.72 * smooth(t)))
radius_attribute.data.foreach_set("value", radii)
layer_attribute = hair_data.attributes.new("aevrynd_layer_id", "INT", "CURVE")
layer_attribute.data.foreach_set("value", layers)
material = bpy.data.materials["AevryndFemaleHairMaterial_v249r27"]
hair_data.materials.append(material)
hair = bpy.data.objects.new("AevryndFemaleResampledGroom_v249r32", hair_data)
scene.collection.objects.link(hair)
hair["aevrynd_mainline_baseline"] = "v249"
hair["aevrynd_parent"] = SOURCE.name
hair["aevrynd_layer"] = "hair.guide_follow.resampled"
hair["aevrynd_guide_count"] = len(guide_roots)
hair["aevrynd_followers_per_guide"] = FOLLOWERS
hair["aevrynd_points_per_curve"] = POINTS
hair["aevrynd_root_clearance_m"] = ROOT_CLEARANCE
hair["aevrynd_runtime_status"] = "static visual candidate; dynamic mapping pending visual pass"

evaluated.to_mesh_clear()
scene["aevrynd_mainline_baseline"] = "v249"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_hair_candidate"] = "v249-mainline-groom-r32"
scene["aevrynd_release_state"] = "RESAMPLED_GROOM_PENDING_STRICT_VISUAL_REVIEW"
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
camera = bpy.data.objects["Aevrynd Review Camera"]
views = (
    ("01-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
    ("02-three-quarter", (0.45, -0.66, 1.60), (0.0, -0.005, 1.56), 84),
    ("03-profile", (0.70, -0.02, 1.60), (0.0, 0.0, 1.56), 88),
    ("04-back", (0.0, 0.74, 1.58), (0.0, 0.02, 1.56), 88),
    ("05-top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
)
for name, location, target, lens in views:
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)

report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "guide_count": len(guide_roots),
    "followers_per_guide": FOLLOWERS,
    "curve_count": len(strands),
    "point_count": len(strands) * POINTS,
    "layers": {
        "coverage": sum(layer == 0 for layer in layers),
        "silhouette": sum(layer == 1 for layer in layers),
        "flyaway": sum(layer == 2 for layer in layers),
    },
    "root_clearance_m": ROOT_CLEARANCE,
    "status": "STRICT_VISUAL_REVIEW_REQUIRED",
}
(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249_MAINLINE_GROOM_R32=" + json.dumps(report, sort_keys=True))
