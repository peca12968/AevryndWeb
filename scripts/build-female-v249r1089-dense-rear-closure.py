"""Close the visible posterior center seam in the r1087 authored groom."""
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
SOURCE = ASSETS / "aevrynd-female-cc0-groom-coverage-r1087-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-dense-rear-closure-r1089-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1089-dense-rear-closure.build-report.json"
RENDER_REPORT = ASSETS / "female-v249-mainline-r1089-dense-rear-closure.render.json"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "v249r1089-dense-rear-closure"
BODY = "AevryndFemaleCC0BalancedEyeOptics_R1080"
HAIR = "AevryndFemaleGradedHairlineGroom_R1081"
SCALP = "AevryndFemaleTargetScalp_R976"
CLEARANCE = 0.0010
FRAMES = (1, 20, 21, 33, 61)


def smoothstep(value: float) -> float:
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


def central_rear_strands(scalp_tree):
    """Create a narrow overlapping curtain whose tips remain near the rear midline."""
    strands = []
    roots = []
    rows = (0.004, 0.012, 0.020, 0.028, 0.036)
    for row_index, y in enumerate(rows):
        half_width = 0.052 - row_index * 0.0035
        for column in range(13):
            x = -half_width + 2.0 * half_width * column / 12.0
            hit = scalp_tree.find_nearest(Vector((x, y, 1.535)), 0.080)
            if hit is None or hit[1] is None:
                continue
            surface, normal = hit[0], hit[1].normalized()
            if normal.y < -0.45:
                continue
            root_index = len(roots)
            roots.append(surface.copy())
            tangent = Vector((1.0, 0.0, -normal.x / max(0.25, normal.z))).normalized()
            bitangent = normal.cross(tangent).normalized()
            for child in range(20):
                rng = random.Random(1088000 + root_index * 19 + child)
                root_probe = surface + tangent * rng.uniform(-0.0025, 0.0025) + bitangent * rng.uniform(-0.0018, 0.0018)
                root_hit = scalp_tree.find_nearest(root_probe, 0.012)
                root = surface if root_hit is None else root_hit[0]
                root_normal = normal if root_hit is None or root_hit[1] is None else root_hit[1].normalized()
                root = root + root_normal * CLEARANCE
                release = root + Vector((rng.uniform(-0.002, 0.002), rng.uniform(0.013, 0.021), -rng.uniform(0.016, 0.028)))
                end = Vector((
                    root.x * rng.uniform(0.45, 0.82) + rng.uniform(-0.018, 0.018),
                    rng.uniform(0.060, 0.090),
                    rng.uniform(1.225, 1.355),
                ))
                p1 = release + Vector((rng.uniform(-0.004, 0.004), rng.uniform(0.012, 0.022), -rng.uniform(0.014, 0.026)))
                p2 = Vector((end.x + rng.uniform(-0.006, 0.006), end.y + rng.uniform(-0.002, 0.010), rng.uniform(1.37, 1.46)))
                points = []
                for point_index in range(20):
                    if point_index < 6:
                        u = point_index / 5.0
                        probe = root.lerp(release, u)
                        surface_hit = scalp_tree.find_nearest(probe, 0.025)
                        point = probe if surface_hit is None or surface_hit[1] is None else surface_hit[0] + surface_hit[1].normalized() * CLEARANCE
                    else:
                        u = (point_index - 5) / 14.0
                        point = cubic(release, p1, p2, end, u)
                        point.x += rng.uniform(-0.0022, 0.0022) * math.sin(math.pi * u)
                        point.y += math.sin(rng.uniform(0.0, math.tau) + u * math.pi) * 0.0012 * math.sin(math.pi * u)
                    points.append(point)
                strands.append(points)
    return strands, roots


def append_strands(hair, strands):
    old_curves = len(hair.data.curves)
    old_points = len(hair.data.points)
    hair.data.add_curves([len(strand) for strand in strands])
    inverse = hair.matrix_world.inverted()
    radius = hair.data.attributes.get("radius") or hair.data.attributes.new("radius", "FLOAT", "POINT")
    family = hair.data.attributes.get("aevrynd_family_r1087") or hair.data.attributes.new("aevrynd_family_r1087", "INT", "CURVE")
    for offset, strand in enumerate(strands):
        curve = hair.data.curves[old_curves + offset]
        family.data[old_curves + offset].value = 3
        for local, world in enumerate(strand):
            index = curve.first_point_index + local
            hair.data.points[index].position = inverse @ world
            t = local / max(1, len(strand) - 1)
            radius.data[index].value = 0.000060 * (1.0 - 0.74 * smoothstep((t - 0.45) / 0.55))
    return {"oldCurves": old_curves, "oldPoints": old_points, "newPointStart": old_points,
            "centralRearCurves": len(strands), "totalCurves": len(hair.data.curves), "totalPoints": len(hair.data.points)}


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
        family_sign = 1.0 if math.sin(curve_index * 0.61803398875) >= 0.0 else -1.0
        direction = (radial * 0.91 + tangent * (0.09 * family_sign)).normalized()
        curve_phase = (math.sin(curve_index * 12.9898 + 78.233) * 0.5 + 0.5) * 1.35 - 0.675
        variation = 0.72 + 0.28 * (math.sin(curve_index * 7.13 + 1.7) * 0.5 + 0.5)
        for local in range(curve.points_length):
            t = local / max(1, curve.points_length - 1)
            index = curve.first_point_index + local
            vector.data[index].vector = direction * (maximum_amplitude * variation * t**2.15)
            phase.data[index].value = curve_phase


def repair_new_points(scene, hair, body, new_point_start):
    corrected = 0
    maximum = 0.0
    frame_minimum = {}
    for _pass in range(4):
        pass_corrections = 0
        for frame in FRAMES:
            scene.frame_set(frame)
            deps = bpy.context.evaluated_depsgraph_get(); deps.update()
            tree = evaluated_tree(body)
            evaluated = hair.evaluated_get(deps)
            inverse = hair.matrix_world.inverted()
            minimum = math.inf
            for index in range(new_point_start, len(hair.data.points)):
                world = evaluated.matrix_world @ evaluated.data.points[index].position
                hit = tree.find_nearest(world)
                if hit is None or hit[1] is None:
                    continue
                normal = hit[1].normalized(); signed = (world - hit[0]).dot(normal)
                minimum = min(minimum, signed)
                if signed < CLEARANCE:
                    delta = normal * (CLEARANCE - signed + 0.00005)
                    hair.data.points[index].position = inverse @ ((hair.matrix_world @ hair.data.points[index].position) + delta)
                    corrected += 1; pass_corrections += 1; maximum = max(maximum, delta.length)
            frame_minimum[str(frame)] = minimum
        if pass_corrections == 0:
            break
    scene.frame_set(1)
    return {"correctedOperations": corrected, "maximumCorrectionM": maximum, "minimumBeforeRepairByFrame": frame_minimum}


def audit_new_points(scene, hair, body, new_point_start):
    results = {}
    for frame in FRAMES:
        scene.frame_set(frame)
        deps = bpy.context.evaluated_depsgraph_get(); deps.update()
        tree = evaluated_tree(body); evaluated = hair.evaluated_get(deps); signed = []
        for index in range(new_point_start, len(hair.data.points)):
            world = evaluated.matrix_world @ evaluated.data.points[index].position
            hit = tree.find_nearest(world)
            if hit and hit[1] is not None:
                signed.append((world - hit[0]).dot(hit[1].normalized()))
        results[str(frame)] = {"pointsTested": len(signed), "minimumSignedClearanceM": min(signed),
                               "penetratingPoints": sum(value < -0.00005 for value in signed),
                               "belowClearancePoints": sum(value < CLEARANCE for value in signed)}
    scene.frame_set(1)
    return results


def render(scene, frame, view):
    scene.frame_set(frame); camera = scene.camera
    settings = {"front": ((0.0, -0.72, 1.445), (0.0, -0.025, 1.445)),
                "three-quarter": ((0.45, -0.62, 1.46), (0.0, -0.015, 1.445)),
                "back": ((0.0, 0.72, 1.445), (0.0, 0.025, 1.445)),
                "top": ((0.0, -0.25, 2.0), (0.0, 0.015, 1.51))}
    camera.location, target = settings[view]; camera.data.lens = 88 if view != "top" else 78; look_at(camera, target)
    scene.render.resolution_x = scene.render.resolution_y = 900; scene.render.resolution_percentage = 100
    path = RENDER_DIR / f"r1089-f{frame:02d}-{view}.png"; scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return str(path)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene; scene.frame_set(1)
scene.view_settings.view_transform = "Standard"; scene.view_settings.look = "None"; scene.view_settings.exposure = 0.0; scene.view_settings.gamma = 1.0
hair = bpy.data.objects[HAIR]; body = bpy.data.objects[BODY]; scalp_tree = evaluated_tree(bpy.data.objects[SCALP])
central, roots = central_rear_strands(scalp_tree)
append_report = append_strands(hair, central)
author_motion(hair)
repair_report = repair_new_points(scene, hair, body, append_report["newPointStart"])
audit = audit_new_points(scene, hair, body, append_report["newPointStart"])
hair["aevrynd_revision"] = "v249r1089-dense-rear-closure"; hair["aevrynd_added_central_rear_curves"] = len(central); hair["aevrynd_clearance_m"] = CLEARANCE
scene["aevrynd_release_state"] = "VISUAL_REVIEW_PENDING"; scene["aevrynd_website_promotion"] = "forbidden"
bpy.context.preferences.filepaths.save_version = 0; bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
RENDER_DIR.mkdir(parents=True, exist_ok=True)
renders = [render(scene, 1, view) for view in ("front", "three-quarter", "back", "top")]
renders += [render(scene, 21, view) for view in ("front", "back")]
report = {"revision": "v249r1089-dense-rear-closure", "source": str(SOURCE), "output": str(OUTPUT),
          "method": "append a dense 1,300-curve overlapping, inward-falling center-back family to close the posterior split while retaining r1087 outer coverage and root-pinned motion",
          "append": append_report, "posteriorGuideRoots": len(roots), "collisionRepair": repair_report, "collisionAudit": audit,
          "ownership": "Aevrynd-authored procedural curves on Aevrynd-owned/CC0-traceable body and scalp", "externalDependencies": [],
          "status": "PASS" if all(item["penetratingPoints"] == 0 for item in audit.values()) else "FAIL", "websitePromotionApproved": False}
REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
RENDER_REPORT.write_text(json.dumps({"revision": report["revision"], "source": str(OUTPUT), "renders": renders}, indent=2) + "\n", encoding="utf-8")
print("AEVRYND_R1089_GROOM=" + json.dumps({"append": append_report, "guideRoots": len(roots), "collision": audit, "renders": len(renders), "status": report["status"]}, sort_keys=True))
if report["status"] != "PASS":
    raise SystemExit(2)


