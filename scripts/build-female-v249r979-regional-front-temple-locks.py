"""Add explicit front, temple-tuck and part-root macro locks to r978."""

import json
import math
import random
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-macro-lock-hierarchy-r978.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-regional-front-temple-locks-r979.blend"
REPORT = ASSETS / "female-v249-mainline-cc0-regional-front-temple-locks-r979.build-report.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r979-regional-front-temple-locks"
BODY = "AevryndFemaleCC0Baseline_v259"
BASE_HAIR = "AevryndFemaleMacroLockGroom_R978"
LOCKS = "AevryndFemaleFrontTempleMacroLocks_R979"
POINTS_PER_STRAND = 20
FOLLOWERS_PER_GUIDE = 8
CLEARANCE_M = 0.0018


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def smoothstep(value):
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def hairline_z(x):
    side = clamp(abs(x) / 0.095)
    return 1.545 + 0.012 * smoothstep((side - 0.28) / 0.45) - 0.009 * smoothstep((side - 0.80) / 0.20)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def evaluated_tree(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    polygons = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, polygons, all_triangles=False)


def surface_point(tree, seed, clearance=CLEARANCE_M):
    hit = tree.find_nearest(seed)
    if hit is None or hit[1] is None:
        raise RuntimeError("Unable to locate body surface for regional hair root")
    return hit[0] + hit[1].normalized() * clearance, hit[1].normalized()


def keep_clear(tree, point):
    hit = tree.find_nearest(point)
    if hit is None or hit[1] is None:
        return point
    nearest, normal, _face, _distance = hit
    normal = normal.normalized()
    signed = (point - nearest).dot(normal)
    return nearest + normal * CLEARANCE_M if signed < CLEARANCE_M else point


def bezier(p0, p1, p2, p3, t):
    u = 1.0 - t
    return p0 * u ** 3 + p1 * 3.0 * u * u * t + p2 * 3.0 * u * t * t + p3 * t ** 3


def explicit_roots(tree):
    roots = []
    # Full frontal boundary, deliberately denser than the topology-derived set.
    for index in range(24):
        x = -0.092 + index * (0.184 / 23.0)
        root, normal = surface_point(tree, Vector((x, -0.175, hairline_z(x) + 0.004)))
        roots.append((root, normal, "front"))
    # Temple rows provide the ear-tuck structure missing from r978.
    for side in (-1.0, 1.0):
        for index in range(12):
            y = -0.102 + index * (0.115 / 11.0)
            z = 1.548 + 0.064 * smoothstep((y + 0.102) / 0.115)
            root, normal = surface_point(tree, Vector((side * 0.110, y, z)))
            roots.append((root, normal, "temple"))
    # Paired roots along the part narrow the exposed scalp without closing it.
    for side in (-1.0, 1.0):
        for index in range(9):
            y = -0.086 + index * (0.105 / 8.0)
            z = 1.586 + 0.070 * smoothstep((y + 0.086) / 0.105)
            root, normal = surface_point(tree, Vector((side * 0.007, y, z)))
            roots.append((root, normal, "part"))
    return roots


def guide_for(root, normal, region, index):
    rng = random.Random(979000 + index)
    side = -1.0 if root.x < 0.0 else 1.0
    if region == "front":
        central = 1.0 - clamp(abs(root.x) / 0.092)
        end = Vector((side * (0.105 + 0.025 * central), -0.120 + rng.uniform(-0.008, 0.008), 1.315 + 0.060 * (1.0 - central) + rng.uniform(-0.018, 0.018)))
        p1 = root + normal * 0.010 + Vector((side * (0.016 + 0.012 * central), -0.002, 0.004))
    elif region == "temple":
        end = Vector((side * (0.103 + rng.uniform(-0.008, 0.008)), -0.005 + rng.uniform(-0.010, 0.014), 1.330 + rng.uniform(-0.025, 0.025)))
        p1 = root + normal * 0.008 + Vector((-side * 0.010, 0.020, 0.002))
    else:
        end = Vector((side * (0.118 + rng.uniform(-0.010, 0.010)), -0.080 + rng.uniform(-0.008, 0.012), 1.292 + rng.uniform(-0.025, 0.025)))
        p1 = root + normal * 0.012 + Vector((side * 0.020, -0.002, 0.006))
    p2 = Vector((end.x - side * 0.018, end.y, end.z + 0.105))
    phase = rng.uniform(-0.7, 0.7)
    amplitude = rng.uniform(0.005, 0.012)
    points = []
    for point_index in range(POINTS_PER_STRAND):
        t = point_index / (POINTS_PER_STRAND - 1)
        point = bezier(root, p1, p2, end, t)
        weight = smoothstep((t - 0.22) / 0.78)
        point.x += side * amplitude * (math.sin(phase + t * math.pi * 1.25) - math.sin(phase)) * weight
        point.y += amplitude * 0.4 * (math.cos(phase + t * math.pi) - math.cos(phase)) * weight
        points.append(point)
    return points, side, rng


def build_strands(roots, tree):
    strands = []
    region_counts = {}
    for index, (root, normal, region) in enumerate(roots):
        region_counts[region] = region_counts.get(region, 0) + 1
        guide, side, rng = guide_for(root, normal, region, index)
        tangent = Vector((normal.z, 0.0, -normal.x)).normalized()
        bitangent = normal.cross(tangent).normalized()
        for follower in range(FOLLOWERS_PER_GUIDE):
            angle = math.tau * ((follower * 0.61803398875 + rng.random() * 0.06) % 1.0)
            radius = 0.0004 if follower == 0 else 0.0012 + 0.0032 * math.sqrt(rng.random())
            offset = tangent * (math.cos(angle) * radius) + bitangent * (math.sin(angle) * radius)
            follower_root, _normal = surface_point(tree, root + offset)
            root_delta = follower_root - root
            strand = []
            length_jitter = rng.uniform(-0.012, 0.012)
            for point_index, base in enumerate(guide):
                t = point_index / (POINTS_PER_STRAND - 1)
                point = base + root_delta * (1.0 - 0.45 * smoothstep(t))
                point += offset * (0.18 + 0.82 * smoothstep(t))
                point.z += length_jitter * smoothstep(t)
                strand.append(keep_clear(tree, point))
            strands.append(strand)
    return strands, region_counts


def make_locks(strands, material):
    data = bpy.data.hair_curves.new(LOCKS + "Data")
    data.add_curves([POINTS_PER_STRAND] * len(strands))
    data.points.foreach_set("position", [coordinate for strand in strands for point in strand for coordinate in point])
    radius = data.attributes.new("radius", "FLOAT", "POINT")
    values = []
    for _strand in strands:
        for point_index in range(POINTS_PER_STRAND):
            t = point_index / (POINTS_PER_STRAND - 1)
            values.append(0.000105 * (1.0 - 0.74 * smoothstep(t)))
    radius.data.foreach_set("value", values)
    data.materials.append(material)
    obj = bpy.data.objects.new(LOCKS, data)
    bpy.context.scene.collection.objects.link(obj)
    obj["aevrynd_layer"] = "hair.macro_locks.front_temple_part"
    obj["aevrynd_revision"] = "v249r979"
    obj["aevrynd_runtime_dependency"] = "none"
    return obj


def render(scene, camera, name, location, target, lens):
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
tree = evaluated_tree(bpy.data.objects[BODY])
base = bpy.data.objects[BASE_HAIR]
radius = base.data.attributes.get("radius")
if radius:
    for item in radius.data:
        item.value *= 0.76
roots = explicit_roots(tree)
strands, region_counts = build_strands(roots, tree)
locks = make_locks(strands, base.data.materials[0])
for obj in (locks,):
    world = obj.matrix_world.copy()
    obj.parent = bpy.data.objects["AevryndFemaleRig"]
    obj.parent_type = "OBJECT"
    obj.matrix_parent_inverse = obj.parent.matrix_world.inverted()
    obj.matrix_world = world
scene["aevrynd_mainline_revision"] = "v249r979-regional-front-temple-locks"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "STATIC_REGIONAL_LOCKS_VISUAL_AND_COLLISION_AUDIT_REQUIRED"
scene["aevrynd_hair_layers"] = "hair.scalp.target_native|hair.guide_follow.macro_lock_hierarchy|hair.macro_locks.front_temple_part"
scene["aevrynd_website_promotion"] = "forbidden pending strict gates and user approval"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
scene.render.resolution_x = scene.render.resolution_y = 900
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects.get("Aevrynd Review Camera") or scene.camera
scene.camera = camera
for args in (
    ("01-face-front", (0.0, -0.68, 1.49), (0.0, -0.055, 1.48), 88),
    ("02-face-three-quarter", (0.42, -0.58, 1.51), (0.0, -0.045, 1.48), 88),
    ("03-face-profile", (0.68, -0.02, 1.50), (0.0, -0.035, 1.48), 90),
    ("04-hair-back", (0.0, 0.76, 1.50), (0.0, -0.01, 1.48), 86),
    ("05-hair-top", (0.0, -0.18, 2.05), (0.0, -0.02, 1.57), 82),
    ("06-full-three-quarter", (1.10, -1.62, 1.22), (0.0, -0.01, 0.92), 58),
):
    render(scene, camera, *args)

report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "baseHair": BASE_HAIR,
    "regionalLocks": locks.name,
    "baseRadiusMultiplier": 0.76,
    "guideCount": len(roots),
    "followersPerGuide": FOLLOWERS_PER_GUIDE,
    "strandCount": len(strands),
    "pointCount": len(strands) * POINTS_PER_STRAND,
    "guideRegions": region_counts,
    "clearanceM": CLEARANCE_M,
    "secondaryMotion": False,
    "websitePromotionApproved": False,
    "status": "STRICT_VISUAL_AND_COLLISION_REVIEW_REQUIRED",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_R979_REGIONAL_LOCKS=" + json.dumps(report, sort_keys=True))
