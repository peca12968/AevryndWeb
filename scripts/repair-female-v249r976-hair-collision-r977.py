"""Repair r976 hair/body penetrations with smoothed per-curve displacements."""

import json
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-target-scalp-guide-groom-r976.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-hair-collision-repair-r977.blend"
REPORT = ASSETS / "female-v249-mainline-cc0-hair-collision-repair-r977.build-report.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r977-hair-collision-repair"
BODY = "AevryndFemaleCC0Baseline_v259"
HAIR = "AevryndFemaleTargetGuideGroom_R976"
CLEARANCE_M = 0.0016


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def evaluated_tree(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(points, faces, all_triangles=False)


def required_delta(tree, point):
    hit = tree.find_nearest(point)
    if hit is None or hit[1] is None:
        return Vector()
    nearest, normal, _face, _distance = hit
    normal = normal.normalized()
    signed = (point - nearest).dot(normal)
    return normal * (CLEARANCE_M - signed) if signed < CLEARANCE_M else Vector()


def smooth_curve_deltas(hair, deltas, passes=3):
    result = [delta.copy() for delta in deltas]
    for _pass in range(passes):
        source = [delta.copy() for delta in result]
        for curve in hair.data.curves:
            first = curve.first_point_index
            last = first + curve.points_length - 1
            for index in range(first + 1, last):
                result[index] = source[index - 1] * 0.22 + source[index] * 0.56 + source[index + 1] * 0.22
    return result


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
hair = bpy.data.objects[HAIR]
inverse = hair.matrix_world.inverted()
world_points = [hair.matrix_world @ point.position for point in hair.data.points]
raw = [required_delta(tree, point) for point in world_points]
smoothed = smooth_curve_deltas(hair, raw)
initial_corrected = sum(delta.length > 0.0 for delta in raw)
max_initial = max((delta.length for delta in raw), default=0.0)
for index, delta in enumerate(smoothed):
    hair.data.points[index].position = inverse @ (world_points[index] + delta)

# The smoothing step keeps curves continuous but can leave a small residual.
# Final projection is the hard no-penetration gate and is intentionally exact.
bpy.context.view_layer.update()
final_corrected = 0
max_final = 0.0
for index, point in enumerate(hair.data.points):
    world = hair.matrix_world @ point.position
    delta = required_delta(tree, world)
    if delta.length > 0.0:
        point.position = inverse @ (world + delta)
        final_corrected += 1
        max_final = max(max_final, delta.length)

hair.name = "AevryndFemaleTargetGuideGroom_R977"
hair["aevrynd_revision"] = "v249r977"
hair["aevrynd_collision_clearance_m"] = CLEARANCE_M
hair["aevrynd_collision_repair"] = "three-pass per-curve displacement smoothing plus exact final projection"
scene["aevrynd_mainline_revision"] = "v249r977-hair-collision-repair"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "STATIC_HAIR_COLLISION_AUDIT_PENDING"
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
):
    render(scene, camera, *args)

report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "hair": hair.name,
    "pointCount": len(hair.data.points),
    "clearanceM": CLEARANCE_M,
    "initialCorrectedPointCount": initial_corrected,
    "maximumInitialCorrectionM": max_initial,
    "finalResidualCorrectedPointCount": final_corrected,
    "maximumFinalCorrectionM": max_final,
    "websitePromotionApproved": False,
    "status": "STRICT_VISUAL_AND_COLLISION_REVIEW_REQUIRED",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_R977_HAIR_COLLISION_REPAIR=" + json.dumps(report, sort_keys=True))
