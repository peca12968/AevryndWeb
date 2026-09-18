"""Narrow the crown part and suppress early-loop defects in the r1089 groom."""
from __future__ import annotations

import json
import math
import random
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-dense-rear-closure-r1089-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-scalp-overlay-r1091-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1091-scalp-overlay.build-report.json"
RENDER_REPORT = ASSETS / "female-v249-mainline-r1091-scalp-overlay.render.json"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "v249r1091-scalp-overlay"
BODY = "AevryndFemaleCC0BalancedEyeOptics_R1080"
HAIR = "AevryndFemaleGradedHairlineGroom_R1081"
SCALP = "AevryndFemaleTargetScalp_R976"
CLEARANCE = 0.0010
FRAMES = (1, 20, 21, 33, 61)


def smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def evaluated_tree(obj):
    deps = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(deps)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, faces, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


def cubic(p0, p1, p2, p3, t):
    u = 1.0 - t
    return p0 * u**3 + p1 * (3.0 * u * u * t) + p2 * (3.0 * u * t * t) + p3 * t**3


def crown_routing_strands(scalp_tree):
    """Lay short tapered fibers across the exposed part; existing long hair supplies the silhouette."""
    strands = []
    roots = []
    for row in range(18):
        y = -0.082 + row * 0.0065
        for side in (-1.0, 1.0):
            guide_index = len(roots)
            for child in range(14):
                rng = random.Random(1091000 + guide_index * 37 + child)
                root_x = side * rng.uniform(0.0030, 0.0090)
                root_y = y + rng.uniform(-0.0020, 0.0020)
                outer_x = side * rng.uniform(0.075, 0.105)
                outer_y = root_y + rng.uniform(0.008, 0.026)
                points = []
                valid = True
                for point_index in range(18):
                    u = point_index / 17.0
                    eased = smoothstep(u)
                    probe = Vector((root_x + (outer_x - root_x) * eased,
                                    root_y + (outer_y - root_y) * eased + math.sin(math.pi * u) * rng.uniform(-0.0010, 0.0010),
                                    1.575))
                    hit = scalp_tree.find_nearest(probe, 0.120)
                    if hit is None or hit[1] is None:
                        valid = False
                        break
                    points.append(hit[0] + hit[1].normalized() * CLEARANCE)
                if valid:
                    strands.append(points)
            roots.append((side, y))
    return strands, roots

def suppress_early_reversals(hair):
    family = hair.data.attributes.get("aevrynd_family_r1087")
    radius = hair.data.attributes.get("radius")
    suppressed = []
    if family is None or radius is None:
        return suppressed
    for curve_index, curve in enumerate(hair.data.curves):
        if family.data[curve_index].value != 3 or curve.points_length < 3:
            continue
        points = [hair.data.points[curve.first_point_index + i].position for i in range(min(curve.points_length, 8))]
        tangents = []
        for index in range(1, len(points)):
            delta = points[index] - points[index - 1]
            if delta.length > 1e-8:
                tangents.append(delta.normalized())
        minimum_dot = min((tangents[i].dot(tangents[i - 1]) for i in range(1, len(tangents))), default=1.0)
        if minimum_dot < 0.0:
            for local in range(curve.points_length):
                radius.data[curve.first_point_index + local].value = 0.0
            suppressed.append(curve_index)
    return suppressed


def append_strands(hair, strands):
    old_curves = len(hair.data.curves)
    old_points = len(hair.data.points)
    hair.data.add_curves([len(strand) for strand in strands])
    inverse = hair.matrix_world.inverted()
    radius = hair.data.attributes.get("radius") or hair.data.attributes.new("radius", "FLOAT", "POINT")
    family = hair.data.attributes.get("aevrynd_family_r1087") or hair.data.attributes.new("aevrynd_family_r1087", "INT", "CURVE")
    for offset, strand in enumerate(strands):
        curve = hair.data.curves[old_curves + offset]
        family.data[old_curves + offset].value = 4
        for local, world in enumerate(strand):
            index = curve.first_point_index + local
            hair.data.points[index].position = inverse @ world
            t = local / max(1, len(strand) - 1)
            radius.data[index].value = 0.000050 * (1.0 - smoothstep((t - 0.35) / 0.65))
    return {"oldCurves": old_curves, "oldPoints": old_points, "newPointStart": old_points,
            "crownCurves": len(strands), "totalCurves": len(hair.data.curves), "totalPoints": len(hair.data.points)}


def author_motion(hair, maximum_amplitude=0.0045):
    vector = hair.data.attributes.get("aevrynd_motion_vector_r1083")
    phase = hair.data.attributes.get("aevrynd_motion_phase_r1083")
    for curve_index, curve in enumerate(hair.data.curves):
        root = hair.data.points[curve.first_point_index].position
        radial = Vector((root.x, root.y + 0.010, 0.0))
        if radial.length < 1e-7:
            radial = Vector((1.0 if curve_index % 2 else -1.0, 0.0, 0.0))
        radial.normalize()
        tangent = Vector((-radial.y, radial.x, 0.0))
        sign = 1.0 if math.sin(curve_index * 0.61803398875) >= 0.0 else -1.0
        direction = (radial * 0.91 + tangent * (0.09 * sign)).normalized()
        curve_phase = (math.sin(curve_index * 12.9898 + 78.233) * 0.5 + 0.5) * 1.35 - 0.675
        variation = 0.72 + 0.28 * (math.sin(curve_index * 7.13 + 1.7) * 0.5 + 0.5)
        for local in range(curve.points_length):
            t = local / max(1, curve.points_length - 1)
            index = curve.first_point_index + local
            vector.data[index].vector = direction * (maximum_amplitude * variation * t**2.15)
            phase.data[index].value = curve_phase


def repair_and_audit(scene, hair, body, start):
    corrected = 0
    maximum = 0.0
    for _pass in range(4):
        pass_count = 0
        for frame in FRAMES:
            scene.frame_set(frame); deps = bpy.context.evaluated_depsgraph_get(); deps.update()
            tree = evaluated_tree(body); evaluated = hair.evaluated_get(deps); inverse = hair.matrix_world.inverted()
            for index in range(start, len(hair.data.points)):
                world = evaluated.matrix_world @ evaluated.data.points[index].position
                hit = tree.find_nearest(world)
                if hit is None or hit[1] is None: continue
                normal = hit[1].normalized(); signed = (world - hit[0]).dot(normal)
                if signed < CLEARANCE:
                    delta = normal * (CLEARANCE - signed + 0.00005)
                    hair.data.points[index].position = inverse @ ((hair.matrix_world @ hair.data.points[index].position) + delta)
                    corrected += 1; pass_count += 1; maximum = max(maximum, delta.length)
        if pass_count == 0: break
    audit = {}
    for frame in FRAMES:
        scene.frame_set(frame); deps = bpy.context.evaluated_depsgraph_get(); deps.update()
        tree = evaluated_tree(body); evaluated = hair.evaluated_get(deps); signed = []
        for index in range(start, len(hair.data.points)):
            world = evaluated.matrix_world @ evaluated.data.points[index].position
            hit = tree.find_nearest(world)
            if hit and hit[1] is not None: signed.append((world - hit[0]).dot(hit[1].normalized()))
        audit[str(frame)] = {"pointsTested": len(signed), "minimumSignedClearanceM": min(signed),
                             "penetratingPoints": sum(v < -0.00005 for v in signed), "belowClearancePoints": sum(v < CLEARANCE for v in signed)}
    scene.frame_set(1)
    return {"correctedOperations": corrected, "maximumCorrectionM": maximum}, audit


def render(scene, frame, view):
    scene.frame_set(frame); camera = scene.camera
    settings = {"front": ((0.0, -0.72, 1.445), (0.0, -0.025, 1.445)),
                "three-quarter": ((0.45, -0.62, 1.46), (0.0, -0.015, 1.445)),
                "back": ((0.0, 0.72, 1.445), (0.0, 0.025, 1.445)),
                "top": ((0.0, -0.25, 2.0), (0.0, 0.015, 1.51))}
    camera.location, target = settings[view]; camera.data.lens = 88 if view != "top" else 78; look_at(camera, target)
    scene.render.resolution_x = scene.render.resolution_y = 900; scene.render.resolution_percentage = 100
    path = RENDER_DIR / f"r1091-f{frame:02d}-{view}.png"; scene.render.filepath = str(path); bpy.ops.render.render(write_still=True)
    return str(path)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene; scene.frame_set(1)
scene.view_settings.view_transform = "Standard"; scene.view_settings.look = "None"; scene.view_settings.exposure = 0.0; scene.view_settings.gamma = 1.0
hair = bpy.data.objects[HAIR]; body = bpy.data.objects[BODY]; scalp_tree = evaluated_tree(bpy.data.objects[SCALP])
suppressed = suppress_early_reversals(hair)
crown, roots = crown_routing_strands(scalp_tree)
append_report = append_strands(hair, crown); author_motion(hair)
repair_report, audit = repair_and_audit(scene, hair, body, append_report["newPointStart"])
hair["aevrynd_revision"] = "v249r1091-scalp-overlay"; hair["aevrynd_added_crown_curves"] = len(crown); hair["aevrynd_suppressed_early_reversals"] = len(suppressed)
scene["aevrynd_release_state"] = "VISUAL_REVIEW_PENDING"; scene["aevrynd_website_promotion"] = "forbidden"
bpy.context.preferences.filepaths.save_version = 0; bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
RENDER_DIR.mkdir(parents=True, exist_ok=True)
renders = [render(scene, 1, view) for view in ("front", "three-quarter", "back", "top")]
renders += [render(scene, 21, view) for view in ("front", "back", "top")]
report = {"revision": "v249r1091-scalp-overlay", "source": str(SOURCE), "output": str(OUTPUT),
          "method": "suppress measured family-3 early reversals and add a fully scalp-projected, end-tapered crown overlay",
          "suppressedEarlyReversalCurves": suppressed, "guideRoots": len(roots), "append": append_report,
          "collisionRepair": repair_report, "collisionAudit": audit,
          "ownership": "Aevrynd-authored procedural curves on Aevrynd-owned/CC0-traceable body and scalp", "externalDependencies": [],
          "status": "PASS" if all(v["penetratingPoints"] == 0 for v in audit.values()) else "FAIL", "websitePromotionApproved": False}
REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
RENDER_REPORT.write_text(json.dumps({"revision": report["revision"], "source": str(OUTPUT), "renders": renders}, indent=2) + "\n", encoding="utf-8")
print("AEVRYND_R1091_CROWN=" + json.dumps({"suppressed": len(suppressed), "append": append_report, "collision": audit, "renders": len(renders), "status": report["status"]}, sort_keys=True))
if report["status"] != "PASS": raise SystemExit(2)

