"""Reduce exposed family-0 root diameter without changing groom topology or motion."""
from pathlib import Path
import json

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-rear-contour-r1123-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-frontal-root-diameter-r1126-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1126-frontal-root-diameter-sweep.study.json"
OUT = ROOT.parent / "Temp" / "female-realism" / "v249r1126-frontal-root-diameter-sweep"
BODY = "AevryndFemaleCC0PalpebralClosure_R1097"
HAIR = "AevryndFemaleGradedHairlineGroom_R1081"
SCALP = "AevryndFemaleTargetScalp_R976"
FAMILY = "aevrynd_family_r1087"
FRAMES = (1, 20, 33, 61)
# label, root cap in metres, normalized blend length
VARIANTS = (("a-natural", 0.000070, 0.22), ("b-balanced", 0.000055, 0.30), ("c-fine", 0.000040, 0.38))
SELECTED = "b-balanced"


def smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def body_tree(body, depsgraph):
    evaluated = body.evaluated_get(depsgraph); mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ v.co for v in mesh.vertices]
    faces = [tuple(p.vertices) for p in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, faces, all_triangles=False)
    evaluated.to_mesh_clear(); return tree


def tune_roots(hair, root_cap, blend_length):
    data = hair.data; family = data.attributes[FAMILY]; radius = data.attributes["radius"]
    edited_curves = 0; edited_points = 0; before = []; after = []
    for ci, curve in enumerate(data.curves):
        root = hair.matrix_world @ data.points[curve.first_point_index].position
        if family.data[ci].value != 0 or root.y >= -0.075 or root.z <= 1.50:
            continue
        edited_curves += 1
        for local in range(curve.points_length):
            t = local / max(1, curve.points_length - 1)
            if t >= blend_length:
                break
            index = curve.first_point_index + local
            old = radius.data[index].value
            blend = smoothstep(t / blend_length)
            cap = root_cap + (old - root_cap) * blend
            new = min(old, cap)
            before.append(old); after.append(new)
            if new < old - 1e-10:
                radius.data[index].value = new; edited_points += 1
    return {"editedCurves": edited_curves, "editedPoints": edited_points,
            "rootCapM": root_cap, "blendLengthNormalized": blend_length,
            "meanRadiusBeforeM": sum(before) / len(before), "meanRadiusAfterM": sum(after) / len(after),
            "minimumRadiusAfterM": min(after), "maximumRadiusAfterM": max(after)}


def collision_audit(scene, hair, body):
    result = {}
    for frame in FRAMES:
        scene.frame_set(frame); depsgraph = bpy.context.evaluated_depsgraph_get(); depsgraph.update()
        tree = body_tree(body, depsgraph); evaluated = hair.evaluated_get(depsgraph); signed = []
        for point in evaluated.data.points:
            world = evaluated.matrix_world @ point.position; hit = tree.find_nearest(world)
            if hit and hit[1] is not None: signed.append((world - hit[0]).dot(hit[1].normalized()))
        result[str(frame)] = {"pointsTested": len(signed), "minimumSignedClearanceM": min(signed),
                              "penetratingPoints": sum(v < -0.00005 for v in signed),
                              "belowOneMmPoints": sum(v < 0.001 for v in signed)}
    scene.frame_set(1); return result


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, label, view, frame=1):
    scene.frame_set(frame); camera = scene.camera
    views = {"front": ((0.0, -1.05, 1.43), (0.0, 0.0, 1.40), 72, (1000, 1000)),
             "oblique": ((0.44, -0.92, 1.46), (0.0, -0.01, 1.40), 72, (1000, 1000)),
             "hairline": ((0.0, -0.53, 1.59), (0.0, -0.02, 1.55), 115, (1200, 850)),
             "right-temple": ((0.25, -0.72, 1.46), (0.025, -0.01, 1.42), 88, (1000, 1000))}
    camera.location, target, camera.data.lens, size = views[view]; look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size; scene.render.resolution_percentage = 100
    path = OUT / f"{label}-{view}-f{frame:02d}.png"; scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True); return str(path)


OUT.mkdir(parents=True, exist_ok=True)
variants = []
for label, root_cap, blend_length in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene; body = bpy.data.objects[BODY]; hair = bpy.data.objects[HAIR]; scalp = bpy.data.objects[SCALP]
    hair.hide_render = hair.hide_viewport = scalp.hide_render = scalp.hide_viewport = False
    edit = tune_roots(hair, root_cap, blend_length); collision = collision_audit(scene, hair, body)
    passed = all(a["penetratingPoints"] == 0 for a in collision.values())
    renders = [render(scene, label, view, 1) for view in ("front", "oblique", "hairline", "right-temple")]
    renders.append(render(scene, label, "front", 33))
    variants.append({"label": label, "edit": edit, "collisionAudit": collision,
                     "technicalStatus": "TECHNICAL_PASS" if passed else "TECHNICAL_FAIL", "renders": renders})
    if label == SELECTED and passed:
        hair["aevrynd_revision"] = "v249r1126-frontal-root-diameter"
        hair["aevrynd_root_method"] = "front family-0 physical diameter cap with smooth recovery"
        scene["aevrynd_release_state"] = "VISUAL_REVIEW_PENDING"; scene["aevrynd_website_promotion"] = "forbidden"
        scene.frame_set(1); bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

selected = next((v for v in variants if v["label"] == SELECTED and v["technicalStatus"] == "TECHNICAL_PASS"), None)
report = {"revision": "v249r1126-frontal-root-diameter-sweep", "source": str(SOURCE),
          "output": str(OUTPUT) if selected else None,
          "method": "cap only the visible frontal family-0 root diameter and blend smoothly back to the authored shaft width without changing topology or motion",
          "variants": variants, "selectedVariant": SELECTED if selected else None, "websitePromotionApproved": False,
          "candidateStatus": "VISUAL_REVIEW_PENDING" if selected else "TECHNICAL_FAIL_DIAGNOSTIC_ONLY"}
REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print("AEVRYND_R1126=" + json.dumps({"variants": [{"label": v["label"], "editedCurves": v["edit"]["editedCurves"],
      "editedPoints": v["edit"]["editedPoints"], "meanAfterUm": v["edit"]["meanRadiusAfterM"] * 1e6,
      "penetrating": {f: a["penetratingPoints"] for f, a in v["collisionAudit"].items()}, "status": v["technicalStatus"]}
      for v in variants]}, sort_keys=True))
