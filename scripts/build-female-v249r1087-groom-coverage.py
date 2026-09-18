"""Add explicit frontal and posterior coverage families to the r1083 mainline groom."""
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
SOURCE = ASSETS / "aevrynd-female-cc0-layered-hair-motion-r1083-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-groom-coverage-r1087-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1087-groom-coverage.build-report.json"
RENDER_REPORT = ASSETS / "female-v249-mainline-r1087-groom-coverage.render.json"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "v249r1087-groom-coverage"
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


def rear_coverage_strands(scalp_tree):
    strands = []
    roots = []
    rows = (0.004, 0.012, 0.020, 0.028, 0.034)
    for row_index, y in enumerate(rows):
        half_width = 0.061 - row_index * 0.0045
        columns = 19 - row_index * 2
        for column in range(columns):
            unit = column / max(1, columns - 1)
            x = -half_width + 2.0 * half_width * unit
            query = Vector((x, y, 1.535))
            hit = scalp_tree.find_nearest(query, 0.080)
            if hit is None or hit[1] is None:
                continue
            surface, normal = hit[0], hit[1].normalized()
            if normal.y < -0.45:
                continue
            guide_index = len(roots)
            roots.append(surface.copy())
            tangent = Vector((1.0, 0.0, -normal.x / max(0.25, normal.z)))
            tangent.normalize()
            bitangent = normal.cross(tangent).normalized()
            for child in range(5):
                rng = random.Random(1087000 + guide_index * 17 + child)
                root_query = surface + tangent * rng.uniform(-0.0026, 0.0026) + bitangent * rng.uniform(-0.0018, 0.0018)
                root_hit = scalp_tree.find_nearest(root_query, 0.012)
                root = surface if root_hit is None else root_hit[0]
                root_normal = normal if root_hit is None or root_hit[1] is None else root_hit[1].normalized()
                root = root + root_normal * CLEARANCE
                side = -1.0 if root.x < 0 else 1.0
                release = root + Vector((side * rng.uniform(0.002, 0.006), rng.uniform(0.012, 0.022), -rng.uniform(0.015, 0.028)))
                end = Vector((
                    root.x * rng.uniform(1.18, 1.48) + side * rng.uniform(0.008, 0.026),
                    rng.uniform(0.052, 0.086),
                    rng.uniform(1.225, 1.355),
                ))
                p1 = release + Vector((side * rng.uniform(0.003, 0.012), rng.uniform(0.010, 0.020), -rng.uniform(0.012, 0.025)))
                p2 = Vector((end.x * rng.uniform(0.90, 1.02), end.y + rng.uniform(-0.004, 0.012), rng.uniform(1.38, 1.47)))
                points = []
                for point_index in range(20):
                    t = point_index / 19.0
                    if point_index < 5:
                        u = point_index / 4.0
                        probe = root.lerp(release, u)
                        surface_hit = scalp_tree.find_nearest(probe, 0.025)
                        point = probe if surface_hit is None or surface_hit[1] is None else surface_hit[0] + surface_hit[1].normalized() * CLEARANCE
                    else:
                        u = (point_index - 4) / 15.0
                        point = cubic(release, p1, p2, end, u)
                        point.x += side * math.sin(math.pi * u) * rng.uniform(0.001, 0.004)
                        point.y += math.sin(rng.uniform(0, math.tau) + u * math.pi) * 0.0015 * math.sin(math.pi * u)
                    points.append(point)
                strands.append(points)
    return strands, roots


def densified_hairline_strands(hair):
    matrix = hair.matrix_world
    short_curves = [curve for curve in hair.data.curves if curve.points_length < 20]
    strands = []
    for template_index, curve in enumerate(short_curves):
        base = [matrix @ hair.data.points[curve.first_point_index + local].position for local in range(curve.points_length)]
        root = base[0]
        for copy_index in range(2):
            rng = random.Random(1087100 + template_index * 11 + copy_index)
            side = -1.0 if copy_index == 0 else 1.0
            lateral = Vector((side * rng.uniform(0.00035, 0.00095), rng.uniform(-0.0004, 0.0002), 0.0))
            extension = rng.uniform(0.0025, 0.0065) if root.y < -0.055 else rng.uniform(0.001, 0.003)
            strand = []
            for local, source in enumerate(base):
                t = local / max(1, len(base) - 1)
                point = source + lateral * (1.0 - 0.35 * smoothstep(t))
                point.z -= extension * smoothstep(t)
                point.x += side * 0.0008 * math.sin(math.pi * t)
                strand.append(point)
            strands.append(strand)
    return strands


def append_strands(hair, rear, hairline):
    old_curves = len(hair.data.curves)
    old_points = len(hair.data.points)
    lengths = [len(strand) for strand in rear] + [len(strand) for strand in hairline]
    hair.data.add_curves(lengths)
    inverse = hair.matrix_world.inverted()
    radius = hair.data.attributes.get("radius") or hair.data.attributes.new("radius", "FLOAT", "POINT")
    family = hair.data.attributes.get("aevrynd_family_r1087") or hair.data.attributes.new("aevrynd_family_r1087", "INT", "CURVE")
    records = [(strand, 1) for strand in rear] + [(strand, 2) for strand in hairline]
    for offset, (strand, family_id) in enumerate(records):
        curve = hair.data.curves[old_curves + offset]
        family.data[old_curves + offset].value = family_id
        for local, world in enumerate(strand):
            index = curve.first_point_index + local
            hair.data.points[index].position = inverse @ world
            t = local / max(1, len(strand) - 1)
            base = 0.000042 if family_id == 1 else 0.000032
            radius.data[index].value = base * (1.0 - 0.74 * smoothstep((t - 0.45) / 0.55))
    return {
        "oldCurves": old_curves,
        "oldPoints": old_points,
        "newPointStart": old_points,
        "rearCurves": len(rear),
        "hairlineCurves": len(hairline),
        "totalCurves": len(hair.data.curves),
        "totalPoints": len(hair.data.points),
    }


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
            deps = bpy.context.evaluated_depsgraph_get()
            deps.update()
            tree = evaluated_tree(body)
            evaluated = hair.evaluated_get(deps)
            inverse = hair.matrix_world.inverted()
            minimum = math.inf
            for index in range(new_point_start, len(hair.data.points)):
                world = evaluated.matrix_world @ evaluated.data.points[index].position
                hit = tree.find_nearest(world)
                if hit is None or hit[1] is None:
                    continue
                normal = hit[1].normalized()
                signed = (world - hit[0]).dot(normal)
                minimum = min(minimum, signed)
                if signed < CLEARANCE:
                    delta = normal * (CLEARANCE - signed + 0.00005)
                    hair.data.points[index].position = inverse @ ((hair.matrix_world @ hair.data.points[index].position) + delta)
                    corrected += 1
                    pass_corrections += 1
                    maximum = max(maximum, delta.length)
            frame_minimum[str(frame)] = minimum
        if pass_corrections == 0:
            break
    scene.frame_set(1)
    return {"correctedOperations": corrected, "maximumCorrectionM": maximum, "minimumBeforeRepairByFrame": frame_minimum}


def audit_new_points(scene, hair, body, new_point_start):
    results = {}
    for frame in FRAMES:
        scene.frame_set(frame)
        deps = bpy.context.evaluated_depsgraph_get()
        deps.update()
        tree = evaluated_tree(body)
        evaluated = hair.evaluated_get(deps)
        signed = []
        for index in range(new_point_start, len(hair.data.points)):
            world = evaluated.matrix_world @ evaluated.data.points[index].position
            hit = tree.find_nearest(world)
            if hit and hit[1] is not None:
                signed.append((world - hit[0]).dot(hit[1].normalized()))
        results[str(frame)] = {
            "pointsTested": len(signed),
            "minimumSignedClearanceM": min(signed),
            "penetratingPoints": sum(value < -0.00005 for value in signed),
            "belowClearancePoints": sum(value < CLEARANCE for value in signed),
        }
    scene.frame_set(1)
    return results


def render(scene, frame, view):
    scene.frame_set(frame)
    camera = scene.camera
    settings = {
        "front": ((0.0, -0.72, 1.445), (0.0, -0.025, 1.445)),
        "three-quarter": ((0.45, -0.62, 1.46), (0.0, -0.015, 1.445)),
        "back": ((0.0, 0.72, 1.445), (0.0, 0.025, 1.445)),
        "top": ((0.0, -0.25, 2.0), (0.0, 0.015, 1.51)),
    }
    camera.location, target = settings[view]
    camera.data.lens = 88 if view != "top" else 78
    look_at(camera, target)
    scene.render.resolution_x = scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    path = RENDER_DIR / f"r1087-f{frame:02d}-{view}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return str(path)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
scene.view_settings.gamma = 1.0
hair = bpy.data.objects[HAIR]
body = bpy.data.objects[BODY]
scalp_tree = evaluated_tree(bpy.data.objects[SCALP])
rear, roots = rear_coverage_strands(scalp_tree)
hairline = densified_hairline_strands(hair)
append_report = append_strands(hair, rear, hairline)
author_motion(hair)
repair_report = repair_new_points(scene, hair, body, append_report["newPointStart"])
audit = audit_new_points(scene, hair, body, append_report["newPointStart"])
hair["aevrynd_revision"] = "v249r1087-groom-coverage"
hair["aevrynd_added_rear_curves"] = len(rear)
hair["aevrynd_added_hairline_curves"] = len(hairline)
hair["aevrynd_clearance_m"] = CLEARANCE
scene["aevrynd_release_state"] = "VISUAL_REVIEW_PENDING"
scene["aevrynd_website_promotion"] = "forbidden"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

RENDER_DIR.mkdir(parents=True, exist_ok=True)
renders = [render(scene, 1, view) for view in ("front", "three-quarter", "back", "top")]
renders += [render(scene, 21, view) for view in ("front", "back")]
report = {
    "revision": "v249r1087-groom-coverage",
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "method": "append explicit posterior guide rows plus two collision-repaired child fibers for every retained r1081 short hairline curve, then reauthor the inherited root-pinned r1083 motion attributes",
    "append": append_report,
    "posteriorGuideRoots": len(roots),
    "collisionRepair": repair_report,
    "collisionAudit": audit,
    "ownership": "Aevrynd-authored procedural curves on Aevrynd-owned/CC0-traceable body and scalp",
    "externalDependencies": [],
    "status": "PASS" if all(item["penetratingPoints"] == 0 for item in audit.values()) else "FAIL",
    "websitePromotionApproved": False,
}
write = lambda path, value: path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
write(REPORT, report)
write(RENDER_REPORT, {"revision": report["revision"], "source": str(OUTPUT), "renders": renders})
print("AEVRYND_R1087_GROOM=" + json.dumps({"append": append_report, "guideRoots": len(roots), "collision": audit, "renders": len(renders), "status": report["status"]}, sort_keys=True))
if report["status"] != "PASS":
    raise SystemExit(2)
