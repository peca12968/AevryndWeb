import json
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-aligned-continuous-guide-groom-r451-study.blend"
OUTPUT = ASSETS / "aevrynd-female-authoring-v249-mainline-tail-collision-envelope-r452-study.blend"
REPORT = ASSETS / "female-v249-mainline-tail-collision-envelope-r452.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r452-tail-collision-envelope"
BODY = "AevryndFemaleBodyBaseV118"
RIG = "AevryndFemaleRig"
LAYERS = (
    "AevryndFemaleFrontSurfaceFlow_R383",
    "AevryndFemaleCrownSurfaceFlow_R383",
    "AevryndFemaleRearSurfaceFlow_R383",
    "AevryndFemaleHairlineTransition_R383",
)
FRAMES = (1, 20, 33, 61)
POINTS_PER_CURVE = 24
PENETRATION_LIMIT = -0.0005
TARGET_CLEARANCE = 0.002
RAMP_START = 8
MAX_PASSES = 4


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def body_tree(body, depsgraph):
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, faces, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


def evaluated_world_points(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    return [evaluated.matrix_world @ point.position for point in evaluated.data.points]


def find_curve_corrections(scene, body, rig, objects):
    corrections = {obj.name: {} for obj in objects}
    frame_stats = {}
    for frame in FRAMES:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        tree = body_tree(body, depsgraph)
        head_world = rig.matrix_world @ rig.pose.bones["head"].matrix
        world_to_head = head_world.inverted().to_3x3()
        frame_stats[str(frame)] = {}
        for obj in objects:
            penetrating = 0
            affected = set()
            minimum = None
            for index, point in enumerate(evaluated_world_points(obj, depsgraph)):
                hit = tree.find_nearest(point, 0.025)
                if hit is None or hit[1] is None:
                    continue
                signed = (point - hit[0]).dot(hit[1].normalized())
                if signed >= PENETRATION_LIMIT:
                    continue
                penetrating += 1
                curve = index // POINTS_PER_CURVE
                affected.add(curve)
                minimum = signed if minimum is None else min(minimum, signed)
                world_delta = hit[1].normalized() * (TARGET_CLEARANCE - signed)
                head_delta = world_to_head @ world_delta
                previous = corrections[obj.name].get(curve)
                if previous is None or signed < previous[0]:
                    corrections[obj.name][curve] = (signed, head_delta)
            frame_stats[str(frame)][obj.name] = {
                "penetratingPoints": penetrating,
                "affectedCurves": len(affected),
                "minimumSignedM": minimum,
            }
    return corrections, frame_stats


def apply_corrections(scene, rig, objects, corrections):
    scene.frame_set(1)
    bpy.context.view_layer.update()
    head_world = rig.matrix_world @ rig.pose.bones["head"].matrix
    applied = {}
    for obj in objects:
        world_to_local = obj.matrix_world.inverted().to_3x3()
        head_to_world = head_world.to_3x3()
        maximum = 0.0
        for curve, (_signed, head_delta) in corrections[obj.name].items():
            local_delta = world_to_local @ (head_to_world @ head_delta)
            maximum = max(maximum, local_delta.length)
            base = curve * POINTS_PER_CURVE
            for segment in range(RAMP_START, POINTS_PER_CURVE):
                t = (segment - RAMP_START + 1) / (POINTS_PER_CURVE - RAMP_START)
                weight = t * t * (3.0 - 2.0 * t)
                obj.data.points[base + segment].position += local_delta * weight
        obj.data.update_tag()
        applied[obj.name] = {
            "correctedCurves": len(corrections[obj.name]),
            "maximumTailDisplacementM": maximum,
        }
    bpy.context.view_layer.update()
    return applied


def render(scene, camera, frame, label, location, target, lens):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(RENDER_DIR / f"{label}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
body = bpy.data.objects[BODY]
rig = bpy.data.objects[RIG]
objects = [bpy.data.objects[name] for name in LAYERS]
passes = []
for pass_index in range(1, MAX_PASSES + 1):
    corrections, before = find_curve_corrections(scene, body, rig, objects)
    affected_total = sum(len(values) for values in corrections.values())
    if not affected_total:
        passes.append({"pass": pass_index, "before": before, "affectedCurves": 0, "applied": {}})
        break
    applied = apply_corrections(scene, rig, objects, corrections)
    passes.append({"pass": pass_index, "before": before, "affectedCurves": affected_total, "applied": applied})

scene.frame_set(1)
scene["aevrynd_mainline_revision"] = "v249r452-tail-collision-envelope-study"
scene["aevrynd_release_state"] = "R452_COLLISION_REVALIDATION_AND_VISUAL_REVIEW_REQUIRED"
for obj in objects:
    obj["aevrynd_revision"] = "v249r452"
    obj["aevrynd_tail_collision_envelope"] = True
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
for frame, label, location, target, lens in (
    (1, "01-front-f01", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
    (1, "02-hairline-f01", (0.0, -0.57, 1.76), (0.0, -0.02, 1.64), 92),
    (1, "03-top-f01", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
    (1, "04-three-quarter-f01", (0.45, -0.66, 1.60), (0.0, -0.005, 1.56), 84),
    (1, "05-back-f01", (0.0, 0.90, 1.59), (0.0, 0.0, 1.56), 82),
    (33, "06-front-f33", (0.0, -0.76, 1.58), (0.0, -0.015, 1.56), 84),
    (33, "07-back-f33", (0.0, 0.90, 1.59), (0.0, 0.0, 1.56), 82),
):
    render(scene, camera, frame, label, location, target, lens)
scene.frame_set(1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "renderDirectory": str(RENDER_DIR),
    "frames": list(FRAMES),
    "pointsPerCurve": POINTS_PER_CURVE,
    "penetrationLimitM": PENETRATION_LIMIT,
    "targetClearanceM": TARGET_CLEARANCE,
    "tailRampStartPoint": RAMP_START,
    "passes": passes,
    "method": "For each affected 24-point guide, preserve points 0-7 and smoothly displace points 8-23 using the deepest cross-frame body-surface correction expressed in head-local space.",
    "ownedAssetOnly": True,
    "websitePromotionApproved": False,
    "status": "COLLISION_REVALIDATION_AND_VISUAL_REVIEW_REQUIRED",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R452_TAIL_COLLISION_ENVELOPE=" + json.dumps(report, sort_keys=True))
