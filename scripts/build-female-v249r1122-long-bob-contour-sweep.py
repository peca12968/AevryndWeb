"""Trim long groom curves to a controlled long-bob contour and terminal taper."""
from pathlib import Path
import json
import math

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-right-temple-cleanup-r1120-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-long-bob-contour-r1122-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1122-long-bob-contour-sweep.study.json"
OUT = ROOT.parent / "Temp" / "female-realism" / "v249r1122-long-bob-contour-sweep"
BODY = "AevryndFemaleCC0PalpebralClosure_R1097"
HAIR = "AevryndFemaleGradedHairlineGroom_R1081"
SCALP = "AevryndFemaleTargetScalp_R976"
FRAMES = (1, 20, 33, 61)
# label, central minimum end height
VARIANTS = (("a-long", 1.285), ("b-balanced", 1.305), ("c-short", 1.325))
SELECTED = "b-balanced"


def body_tree(body, depsgraph):
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, faces, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


def deterministic_variation(index):
    value = math.sin(index * 12.9898 + 91.771) * 43758.5453
    return (value - math.floor(value)) * 2.0 - 1.0


def trim_contour(hair, base_height):
    data = hair.data
    original_sizes = [curve.points_length for curve in data.curves]
    sizes = list(original_sizes)
    trimmed = []
    before_points = len(data.points)
    for ci, curve in enumerate(data.curves):
        points = [hair.matrix_world @ data.points[curve.first_point_index + i].position for i in range(curve.points_length)]
        length = sum((points[i] - points[i - 1]).length for i in range(1, len(points)))
        if length <= 0.15 or curve.points_length < 9:
            continue
        end = points[-1]
        outer_lift = 0.012 * min(1.0, abs(end.x) / 0.16)
        clump_variation = 0.006 * deterministic_variation(ci // 7)
        target = base_height + outer_lift + clump_variation
        if end.z >= target:
            continue
        start = max(6, int(curve.points_length * 0.42))
        cut = next((local for local in range(start, curve.points_length) if points[local].z <= target), None)
        if cut is None:
            continue
        sizes[ci] = max(8, cut + 1)
        if sizes[ci] < original_sizes[ci]:
            trimmed.append(ci)
    data.resize_curves(sizes=sizes)
    radius = data.attributes.get("radius")
    if radius:
        profile = (0.000060, 0.000045, 0.000028, 0.000010)
        for ci in trimmed:
            curve = data.curves[ci]
            count = min(4, curve.points_length)
            for offset in range(count):
                index = curve.first_point_index + curve.points_length - count + offset
                radius.data[index].value = min(radius.data[index].value, profile[4 - count + offset])
    return {
        "trimmedCurves": len(trimmed),
        "trimmedSample": trimmed[:30],
        "beforePoints": before_points,
        "afterPoints": len(data.points),
        "removedPoints": before_points - len(data.points),
        "minimumPointsPerCurve": min(c.points_length for c in data.curves),
        "maximumPointsPerCurve": max(c.points_length for c in data.curves),
        "baseContourHeightM": base_height,
        "outerLiftM": 0.012,
        "clumpVariationM": 0.006,
    }


def collision_audit(scene, hair, body):
    result = {}
    for frame in FRAMES:
        scene.frame_set(frame)
        depsgraph = bpy.context.evaluated_depsgraph_get()
        depsgraph.update()
        tree = body_tree(body, depsgraph)
        evaluated = hair.evaluated_get(depsgraph)
        signed = []
        for point in evaluated.data.points:
            world = evaluated.matrix_world @ point.position
            hit = tree.find_nearest(world)
            if hit and hit[1] is not None:
                signed.append((world - hit[0]).dot(hit[1].normalized()))
        result[str(frame)] = {"pointsTested": len(signed), "minimumSignedClearanceM": min(signed),
                              "penetratingPoints": sum(v < -0.00005 for v in signed),
                              "belowOneMmPoints": sum(v < 0.001 for v in signed)}
    scene.frame_set(1)
    return result


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, label, view, frame=1):
    scene.frame_set(frame)
    camera = scene.camera
    views = {
        "front": ((0.0, -1.05, 1.43), (0.0, 0.0, 1.40), 72),
        "oblique": ((0.44, -0.92, 1.46), (0.0, -0.01, 1.40), 72),
        "profile": ((0.92, -0.18, 1.45), (0.0, -0.01, 1.40), 72),
        "back": ((0.0, 1.02, 1.43), (0.0, 0.0, 1.40), 72),
    }
    camera.location, target, camera.data.lens = views[view]
    look_at(camera, target)
    scene.render.resolution_x = scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    path = OUT / f"{label}-{view}-f{frame:02d}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return str(path)


OUT.mkdir(parents=True, exist_ok=True)
variants = []
for label, base_height in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    body = bpy.data.objects[BODY]
    hair = bpy.data.objects[HAIR]
    scalp = bpy.data.objects[SCALP]
    hair.hide_render = hair.hide_viewport = scalp.hide_render = scalp.hide_viewport = False
    edit = trim_contour(hair, base_height)
    collision = collision_audit(scene, hair, body)
    passed = all(item["penetratingPoints"] == 0 for item in collision.values())
    renders = [render(scene, label, view, 1) for view in ("front", "oblique", "profile", "back")]
    renders.append(render(scene, label, "front", 33))
    variants.append({"label": label, "edit": edit, "collisionAudit": collision,
                     "technicalStatus": "TECHNICAL_PASS" if passed else "TECHNICAL_FAIL", "renders": renders})
    if label == SELECTED and passed:
        hair["aevrynd_revision"] = "v249r1122-long-bob-contour"
        hair["aevrynd_tip_method"] = "clump-varied contour topology trim with four-point terminal taper"
        scene["aevrynd_release_state"] = "VISUAL_REVIEW_PENDING"
        scene["aevrynd_website_promotion"] = "forbidden"
        scene.frame_set(1)
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

selected = next((v for v in variants if v["label"] == SELECTED and v["technicalStatus"] == "TECHNICAL_PASS"), None)
report = {"revision": "v249r1122-long-bob-contour-sweep", "source": str(SOURCE),
          "output": str(OUTPUT) if selected else None,
          "method": "physically trim long curves at a smooth long-bob contour with deterministic clump variation, then apply a four-point terminal radius taper",
          "variants": variants, "selectedVariant": SELECTED if selected else None,
          "websitePromotionApproved": False,
          "candidateStatus": "VISUAL_REVIEW_PENDING" if selected else "TECHNICAL_FAIL_DIAGNOSTIC_ONLY"}
REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print("AEVRYND_R1122=" + json.dumps({"variants": [{"label": v["label"], "trimmed": v["edit"]["trimmedCurves"],
      "removedPoints": v["edit"]["removedPoints"], "remainingPoints": v["edit"]["afterPoints"],
      "penetrating": {f: a["penetratingPoints"] for f, a in v["collisionAudit"].items()},
      "status": v["technicalStatus"]} for v in variants]}, sort_keys=True))
