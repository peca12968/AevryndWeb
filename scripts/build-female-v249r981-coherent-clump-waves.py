"""Create coherent clump waves inside r978 without adding or moving roots."""

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
OUTPUT = ASSETS / "aevrynd-female-cc0-coherent-clump-waves-r981.blend"
REPORT = ASSETS / "female-v249-mainline-cc0-coherent-clump-waves-r981.build-report.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r981-coherent-clump-waves"
BODY = "AevryndFemaleCC0Baseline_v259"
HAIR = "AevryndFemaleMacroLockGroom_R978"
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


def coherent_clump(hair):
    if len(hair.data.curves) % FOLLOWERS_PER_GUIDE:
        raise RuntimeError("Unexpected r978 guide grouping")
    guide_count = len(hair.data.curves) // FOLLOWERS_PER_GUIDE
    matrix = hair.matrix_world
    inverse = matrix.inverted()
    radius = hair.data.attributes.get("radius")
    changed = 0
    maximum_wave = 0.0
    for guide_index in range(guide_count):
        guide_curve = hair.data.curves[guide_index * FOLLOWERS_PER_GUIDE]
        guide_points = [
            matrix @ hair.data.points[guide_curve.first_point_index + local].position
            for local in range(guide_curve.points_length)
        ]
        root = guide_points[0]
        side = -1.0 if root.x < 0.0 else 1.0
        rng = random.Random(981000 + guide_index)
        family = int((math.atan2(root.x, root.y + 0.058) + math.pi) / (2.0 * math.pi) * 18.0) % 18
        family_rng = random.Random(98100 + family)
        phase = family_rng.uniform(-0.65, 0.65)
        amplitude = family_rng.uniform(0.010, 0.023)
        clump_strength = family_rng.uniform(0.20, 0.34)
        for follower in range(FOLLOWERS_PER_GUIDE):
            curve = hair.data.curves[guide_index * FOLLOWERS_PER_GUIDE + follower]
            follower_bias = (follower - 6.5) / 6.5
            for local in range(curve.points_length):
                index = curve.first_point_index + local
                t = local / max(1, curve.points_length - 1)
                point = matrix @ hair.data.points[index].position
                root_pin = smoothstep((t - 0.18) / 0.82)
                mid_clump = math.sin(math.pi * t) ** 1.35
                point = point.lerp(guide_points[local], clump_strength * mid_clump)
                wave = (math.sin(phase + t * math.pi * 1.55) - math.sin(phase)) * root_pin
                depth = (math.cos(phase + t * math.pi * 1.25) - math.cos(phase)) * root_pin
                delta = Vector((side * amplitude * wave, amplitude * 0.42 * depth, 0.0))
                # A small follower fan preserves fiber separation inside each lock.
                delta.x += side * follower_bias * 0.0022 * root_pin
                delta.y += follower_bias * 0.0010 * root_pin
                point += delta
                maximum_wave = max(maximum_wave, delta.length)
                hair.data.points[index].position = inverse @ point
                if radius:
                    base = radius.data[index].value
                    radius.data[index].value = base * (1.30 if follower == 0 else 0.88)
                changed += 1
    return guide_count, changed, maximum_wave


def repair_collision(hair, tree):
    matrix = hair.matrix_world
    inverse = matrix.inverted()
    corrected = 0
    maximum = 0.0
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
guide_count, changed_points, maximum_wave = coherent_clump(hair)
collision_corrected, maximum_collision = repair_collision(hair, evaluated_tree(bpy.data.objects[BODY]))
hair.name = "AevryndFemaleCoherentClumpGroom_R981"
hair["aevrynd_revision"] = "v249r981"
hair["aevrynd_layer"] = "hair.guide_follow.coherent_macro_clumps"
hair["aevrynd_collision_clearance_m"] = CLEARANCE_M
scene["aevrynd_mainline_revision"] = "v249r981-coherent-clump-waves"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "STATIC_COHERENT_CLUMP_VISUAL_AND_COLLISION_AUDIT_REQUIRED"
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
    "changedPointCount": changed_points,
    "maximumAddedWaveM": maximum_wave,
    "collisionCorrectedOperations": collision_corrected,
    "maximumCollisionCorrectionM": maximum_collision,
    "clearanceM": CLEARANCE_M,
    "rootsMovedByDesign": False,
    "secondaryMotion": False,
    "websitePromotionApproved": False,
    "status": "STRICT_VISUAL_AND_COLLISION_REVIEW_REQUIRED",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_R981_COHERENT_CLUMP_WAVES=" + json.dumps(report, sort_keys=True))
