"""Trim only rear-rooted long strands to remove the sparse centre tail."""
from pathlib import Path
import json
import math

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-long-bob-contour-r1122-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-rear-contour-r1123-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1123-rear-contour-sweep.study.json"
OUT = ROOT.parent / "Temp" / "female-realism" / "v249r1123-rear-contour-sweep"
BODY = "AevryndFemaleCC0PalpebralClosure_R1097"
HAIR = "AevryndFemaleGradedHairlineGroom_R1081"
SCALP = "AevryndFemaleTargetScalp_R976"
FAMILY = "aevrynd_family_r1087"
FRAMES = (1, 20, 33, 61)
VARIANTS = (("a-low", 1.300), ("b-balanced", 1.315), ("c-high", 1.330))
SELECTED = "c-high"


def body_tree(body, depsgraph):
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, faces, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


def variation(index):
    value = math.sin(index * 17.117 + 13.91) * 43758.5453
    return (value - math.floor(value)) * 2.0 - 1.0


def trim_rear(hair, base_height):
    data = hair.data
    family = data.attributes[FAMILY]
    sizes = [curve.points_length for curve in data.curves]
    before = len(data.points)
    trimmed = []
    for ci, curve in enumerate(data.curves):
        if family.data[ci].value not in (0, 1, 3) or curve.points_length < 9:
            continue
        points = [hair.matrix_world @ data.points[curve.first_point_index + i].position for i in range(curve.points_length)]
        root, end = points[0], points[-1]
        if root.y <= 0.0 or end.z >= base_height + 0.012:
            continue
        target = base_height + 0.006 * min(1.0, abs(end.x) / 0.12) + 0.004 * variation(ci // 9)
        if end.z >= target:
            continue
        start = max(6, int(curve.points_length * 0.45))
        cut = next((i for i in range(start, curve.points_length) if points[i].z <= target), None)
        if cut is None or cut + 1 >= curve.points_length:
            continue
        sizes[ci] = max(8, cut + 1)
        trimmed.append(ci)
    data.resize_curves(sizes=sizes)
    radius = data.attributes.get("radius")
    if radius:
        profile = (0.000055, 0.000040, 0.000025, 0.000009)
        for ci in trimmed:
            curve = data.curves[ci]
            for offset, desired in enumerate(profile[-min(4, curve.points_length):]):
                index = curve.first_point_index + curve.points_length - min(4, curve.points_length) + offset
                radius.data[index].value = min(radius.data[index].value, desired)
    return {"trimmedRearCurves": len(trimmed), "trimmedSample": trimmed[:30], "beforePoints": before,
            "afterPoints": len(data.points), "removedPoints": before - len(data.points),
            "baseContourHeightM": base_height, "rootYGateM": 0.0}


def collision_audit(scene, hair, body):
    result = {}
    for frame in FRAMES:
        scene.frame_set(frame)
        depsgraph = bpy.context.evaluated_depsgraph_get(); depsgraph.update()
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
    views = {"front": ((0.0, -1.05, 1.43), (0.0, 0.0, 1.40), 72),
             "oblique": ((0.44, -0.92, 1.46), (0.0, -0.01, 1.40), 72),
             "profile": ((0.92, -0.18, 1.45), (0.0, -0.01, 1.40), 72),
             "back": ((0.0, 1.02, 1.43), (0.0, 0.0, 1.40), 72)}
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
    scene = bpy.context.scene; body = bpy.data.objects[BODY]; hair = bpy.data.objects[HAIR]; scalp = bpy.data.objects[SCALP]
    hair.hide_render = hair.hide_viewport = scalp.hide_render = scalp.hide_viewport = False
    edit = trim_rear(hair, base_height)
    collision = collision_audit(scene, hair, body)
    passed = all(a["penetratingPoints"] == 0 for a in collision.values())
    renders = [render(scene, label, view, 1) for view in ("front", "oblique", "profile", "back")]
    renders.append(render(scene, label, "back", 33))
    variants.append({"label": label, "edit": edit, "collisionAudit": collision,
                     "technicalStatus": "TECHNICAL_PASS" if passed else "TECHNICAL_FAIL", "renders": renders})
    if label == SELECTED and passed:
        hair["aevrynd_revision"] = "v249r1123-rear-contour"
        hair["aevrynd_rear_tip_method"] = "rear-root gated contour topology trim"
        scene["aevrynd_release_state"] = "VISUAL_REVIEW_PENDING"; scene["aevrynd_website_promotion"] = "forbidden"
        scene.frame_set(1); bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

selected = next((v for v in variants if v["label"] == SELECTED and v["technicalStatus"] == "TECHNICAL_PASS"), None)
report = {"revision": "v249r1123-rear-contour-sweep", "source": str(SOURCE),
          "output": str(OUTPUT) if selected else None,
          "method": "trim only curves rooted on the rear scalp to remove the sparse centre tail while preserving the accepted front contour",
          "variants": variants, "selectedVariant": SELECTED if selected else None,
          "websitePromotionApproved": False,
          "candidateStatus": "VISUAL_REVIEW_PENDING" if selected else "TECHNICAL_FAIL_DIAGNOSTIC_ONLY"}
REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print("AEVRYND_R1123=" + json.dumps({"variants": [{"label": v["label"], "trimmed": v["edit"]["trimmedRearCurves"],
      "removedPoints": v["edit"]["removedPoints"], "remainingPoints": v["edit"]["afterPoints"],
      "penetrating": {f: a["penetratingPoints"] for f, a in v["collisionAudit"].items()},
      "status": v["technicalStatus"]} for v in variants]}, sort_keys=True))
