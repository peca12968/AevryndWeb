"""Break r977's uniform curtain into coherent regional macro-lock families."""

import json
import math
import random
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-hair-collision-repair-r977.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-macro-lock-hierarchy-r978.blend"
REPORT = ASSETS / "female-v249-mainline-cc0-macro-lock-hierarchy-r978.build-report.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r978-macro-lock-hierarchy"
BODY = "AevryndFemaleCC0Baseline_v259"
HAIR = "AevryndFemaleTargetGuideGroom_R977"
FOLLOWERS_PER_GUIDE = 14
CLEARANCE_M = 0.0016


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def smoothstep(value):
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def evaluated_tree(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    polygons = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, polygons, all_triangles=False)


def required_delta(tree, point):
    hit = tree.find_nearest(point)
    if hit is None or hit[1] is None:
        return Vector()
    nearest, normal, _face, _distance = hit
    normal = normal.normalized()
    signed = (point - nearest).dot(normal)
    return normal * (CLEARANCE_M - signed) if signed < CLEARANCE_M else Vector()


def part_x(y):
    return -0.012 + 0.010 * smoothstep((y + 0.105) / 0.165)


def family_for(root):
    angle = math.atan2(root.x, root.y + 0.058)
    sector = int(((angle + math.pi) / (2.0 * math.pi)) * 12.0) % 12
    height = 1 if root.z > 1.595 else 0
    return sector + height * 12


def region_for(root):
    front = root.y < -0.095
    temple = front and abs(root.x) > 0.045
    near_part = front and abs(root.x - part_x(root.y)) < 0.038
    if near_part:
        return "front_frame"
    if temple:
        return "temple_tuck"
    if root.y > 0.005:
        return "rear"
    if abs(root.x) > 0.055:
        return "side"
    return "crown"


def apply_macro_hierarchy(hair):
    curve_count = len(hair.data.curves)
    if curve_count % FOLLOWERS_PER_GUIDE:
        raise RuntimeError("Unexpected r977 curve grouping")
    guide_count = curve_count // FOLLOWERS_PER_GUIDE
    matrix = hair.matrix_world
    inverse = matrix.inverted()
    changed_points = 0
    regions = {}
    families = set()
    for guide_index in range(guide_count):
        first_curve = hair.data.curves[guide_index * FOLLOWERS_PER_GUIDE]
        root = matrix @ hair.data.points[first_curve.first_point_index].position
        region = region_for(root)
        regions[region] = regions.get(region, 0) + 1
        family = family_for(root)
        families.add(family)
        rng = random.Random(978000 + family * 101 + guide_index)
        side = -1.0 if root.x < part_x(root.y) else 1.0
        phase = random.Random(97800 + family).uniform(-0.75, 0.75)
        family_amp = random.Random(97810 + family).uniform(0.007, 0.016)
        trim_tiers = (-0.024, -0.008, 0.010, 0.030, 0.050)
        trim = trim_tiers[(family * 3 + guide_index * 2) % len(trim_tiers)] + rng.uniform(-0.006, 0.006)
        if region == "front_frame":
            trim += 0.025
            family_amp *= 1.15
        elif region == "temple_tuck":
            trim += 0.018
        elif region == "rear":
            trim -= 0.008
        for follower in range(FOLLOWERS_PER_GUIDE):
            curve = hair.data.curves[guide_index * FOLLOWERS_PER_GUIDE + follower]
            follower_phase = phase + (follower - 6.5) * 0.018
            follower_trim = trim + (follower % 4 - 1.5) * 0.0035
            for local_index in range(curve.points_length):
                index = curve.first_point_index + local_index
                t = local_index / max(1, curve.points_length - 1)
                point = matrix @ hair.data.points[index].position
                motion = smoothstep((t - 0.20) / 0.80)
                coherent = math.sin(follower_phase + t * math.pi * 1.35) - math.sin(follower_phase)
                depth = math.cos(follower_phase + t * math.pi * 1.10) - math.cos(follower_phase)
                point.x += side * family_amp * coherent * motion
                point.y += family_amp * 0.52 * depth * motion
                point.z += follower_trim * smoothstep((t - 0.48) / 0.52)
                if region == "temple_tuck":
                    point.x -= side * 0.014 * smoothstep((t - 0.28) / 0.62)
                    point.y += 0.030 * smoothstep((t - 0.24) / 0.70)
                elif region == "front_frame":
                    point.x += side * 0.010 * smoothstep((t - 0.34) / 0.58)
                    point.y -= 0.007 * smoothstep((t - 0.45) / 0.50)
                # Narrow only the first quarter of near-part roots.  The later
                # points retain separation so the style does not become a tube.
                gap = point.x - part_x(point.y)
                if abs(gap) < 0.026:
                    point.x -= math.copysign(min(0.0042, abs(gap) * 0.22), gap) * (1.0 - smoothstep(t / 0.26))
                hair.data.points[index].position = inverse @ point
                changed_points += 1
    return guide_count, len(families), regions, changed_points


def repair_collision(hair, tree):
    matrix = hair.matrix_world
    inverse = matrix.inverted()
    corrected = 0
    maximum = 0.0
    # Two passes are used because shoulder projection can change the nearest
    # surface for adjacent points on a long strand.
    for _pass in range(2):
        for point in hair.data.points:
            world = matrix @ point.position
            delta = required_delta(tree, world)
            if delta.length > 0.0:
                point.position = inverse @ (world + delta)
                corrected += 1
                maximum = max(maximum, delta.length)
    return corrected, maximum


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
hair = bpy.data.objects[HAIR]
guide_count, family_count, regions, changed_points = apply_macro_hierarchy(hair)
collision_corrected, maximum_collision_correction = repair_collision(hair, evaluated_tree(bpy.data.objects[BODY]))
hair.name = "AevryndFemaleMacroLockGroom_R978"
hair["aevrynd_revision"] = "v249r978"
hair["aevrynd_layer"] = "hair.guide_follow.macro_lock_hierarchy"
hair["aevrynd_macro_family_count"] = family_count
hair["aevrynd_collision_clearance_m"] = CLEARANCE_M
scene["aevrynd_mainline_revision"] = "v249r978-macro-lock-hierarchy"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "STATIC_MACRO_LOCK_VISUAL_AND_COLLISION_AUDIT_REQUIRED"
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
    "hair": hair.name,
    "guideCount": guide_count,
    "followersPerGuide": FOLLOWERS_PER_GUIDE,
    "macroFamilyCount": family_count,
    "guideRegions": regions,
    "changedPointCount": changed_points,
    "collisionCorrectedOperations": collision_corrected,
    "maximumCollisionCorrectionM": maximum_collision_correction,
    "clearanceM": CLEARANCE_M,
    "secondaryMotion": False,
    "websitePromotionApproved": False,
    "status": "STRICT_VISUAL_AND_COLLISION_REVIEW_REQUIRED",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_R978_MACRO_LOCK_HIERARCHY=" + json.dumps(report, sort_keys=True))
