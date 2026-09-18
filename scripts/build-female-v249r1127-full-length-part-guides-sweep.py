"""Add complete centre-part-to-bob strands that join the side mass instead of ending on the scalp."""
from pathlib import Path
import json
import math
import random

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-rear-contour-r1123-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-full-length-part-guides-r1127-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1127-full-length-part-guides-sweep.study.json"
OUT = ROOT.parent / "Temp" / "female-realism" / "v249r1127-full-length-part-guides-sweep"
BODY = "AevryndFemaleCC0PalpebralClosure_R1097"
HAIR = "AevryndFemaleGradedHairlineGroom_R1081"
SCALP = "AevryndFemaleTargetScalp_R976"
FRAMES = (1, 20, 33, 61)
CLEARANCE = 0.001
# label, rows, left children, screen-right children
VARIANTS = (("a-light", 5, 3, 7), ("b-balanced", 7, 4, 9), ("c-dense", 9, 5, 11))
SELECTED = "b-balanced"


def smoothstep(t):
    t = max(0.0, min(1.0, t)); return t * t * (3.0 - 2.0 * t)


def cubic(a, b, c, d, t):
    s = 1.0 - t
    return a * (s ** 3) + b * (3.0 * s * s * t) + c * (3.0 * s * t * t) + d * (t ** 3)


def evaluated_tree(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get(); depsgraph.update(); evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh(); vertices = [evaluated.matrix_world @ v.co for v in mesh.vertices]
    faces = [tuple(p.vertices) for p in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, faces, all_triangles=False); evaluated.to_mesh_clear(); return tree


def build_strands(scalp_tree, rows, left_children, right_children):
    strands = []
    for row in range(rows):
        row_t = row / max(1, rows - 1)
        root_y_base = -0.108 + 0.078 * row_t
        for side, children in ((-1.0, left_children), (1.0, right_children)):
            for child in range(children):
                rng = random.Random(1127000 + row * 1000 + int((side + 1) * 500) + child)
                root_x = side * rng.uniform(0.0020, 0.0055)
                root_y = root_y_base + rng.uniform(-0.0022, 0.0022)
                outer_x = side * rng.uniform(0.068, 0.082)
                outer_y = root_y + rng.uniform(0.006, 0.014)
                scalp_points = []
                valid = True
                for i in range(12):
                    u = i / 11.0
                    eased = smoothstep(u)
                    probe = Vector((root_x + (outer_x - root_x) * eased,
                                    root_y + (outer_y - root_y) * eased,
                                    1.61))
                    hit = scalp_tree.find_nearest(probe, 0.20)
                    if hit is None or hit[1] is None:
                        valid = False; break
                    scalp_points.append(hit[0] + hit[1].normalized() * CLEARANCE)
                if not valid:
                    continue
                start = scalp_points[-1]
                endpoint = Vector((side * rng.uniform(0.092, 0.116),
                                   outer_y + rng.uniform(-0.006, 0.012),
                                   rng.uniform(1.315, 1.335)))
                control1 = start + Vector((side * rng.uniform(0.018, 0.030), rng.uniform(0.000, 0.008), -0.045))
                control2 = endpoint + Vector((-side * rng.uniform(0.006, 0.016), rng.uniform(-0.004, 0.004), 0.085))
                tail = [cubic(start, control1, control2, endpoint, i / 12.0) for i in range(1, 13)]
                strands.append(scalp_points + tail)
    return strands


def append_strands(hair, strands):
    data = hair.data; old_curves = len(data.curves); old_points = len(data.points)
    # Capture original attributes before extension for nearest-neighbour motion inheritance.
    old_world = [hair.matrix_world @ p.position for p in data.points]
    motion = data.attributes.get("aevrynd_motion_vector_r1083")
    phase = data.attributes.get("aevrynd_motion_phase_r1083")
    old_motion = [Vector(x.vector) for x in motion.data[:old_points]] if motion else None
    old_phase = [x.value for x in phase.data[:old_points]] if phase else None
    kd = KDTree(old_points)
    for i, point in enumerate(old_world): kd.insert(point, i)
    kd.balance()
    data.add_curves([len(s) for s in strands])
    radius = data.attributes.get("radius") or data.attributes.new("radius", "FLOAT", "POINT")
    family = data.attributes.get("aevrynd_family_r1087") or data.attributes.new("aevrynd_family_r1087", "INT", "CURVE")
    inverse = hair.matrix_world.inverted()
    for offset, strand in enumerate(strands):
        ci = old_curves + offset; curve = data.curves[ci]; family.data[ci].value = 5
        for local, world in enumerate(strand):
            index = curve.first_point_index + local; t = local / max(1, len(strand) - 1)
            data.points[index].position = inverse @ world
            radius.data[index].value = 0.000058 * (1.0 - smoothstep((t - 0.68) / 0.32)) + 0.000008
            _co, nearest, _distance = kd.find(world)
            if motion and old_motion: motion.data[index].vector = old_motion[nearest]
            if phase and old_phase: phase.data[index].value = old_phase[nearest]
    return {"oldCurves": old_curves, "oldPoints": old_points, "addedCurves": len(strands),
            "newPointStart": old_points, "totalCurves": len(data.curves), "totalPoints": len(data.points)}


def repair_new_points(scene, hair, body, start):
    inverse = hair.matrix_world.inverted(); corrected = 0; maximum = 0.0
    for _pass in range(6):
        pass_count = 0
        for frame in FRAMES:
            scene.frame_set(frame); depsgraph = bpy.context.evaluated_depsgraph_get(); depsgraph.update()
            tree = evaluated_tree(body); evaluated = hair.evaluated_get(depsgraph)
            for index in range(start, len(hair.data.points)):
                world = evaluated.matrix_world @ evaluated.data.points[index].position; hit = tree.find_nearest(world)
                if not hit or hit[1] is None: continue
                normal = hit[1].normalized(); signed = (world - hit[0]).dot(normal)
                if signed < CLEARANCE:
                    delta = normal * (CLEARANCE - signed + 0.00005)
                    base = hair.matrix_world @ hair.data.points[index].position
                    hair.data.points[index].position = inverse @ (base + delta)
                    corrected += 1; pass_count += 1; maximum = max(maximum, delta.length)
        if not pass_count: break
    scene.frame_set(1); return {"correctedOperations": corrected, "maximumCorrectionM": maximum}


def collision_audit(scene, hair, body):
    result = {}
    for frame in FRAMES:
        scene.frame_set(frame); depsgraph = bpy.context.evaluated_depsgraph_get(); depsgraph.update()
        tree = evaluated_tree(body); evaluated = hair.evaluated_get(depsgraph); signed = []
        for point in evaluated.data.points:
            world = evaluated.matrix_world @ point.position; hit = tree.find_nearest(world)
            if hit and hit[1] is not None: signed.append((world - hit[0]).dot(hit[1].normalized()))
        result[str(frame)] = {"pointsTested": len(signed), "minimumSignedClearanceM": min(signed),
                              "penetratingPoints": sum(v < -0.00005 for v in signed),
                              "belowOneMmPoints": sum(v < CLEARANCE for v in signed)}
    scene.frame_set(1); return result


def look_at(camera, target): camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, label, view, frame=1):
    scene.frame_set(frame); camera = scene.camera
    views = {"front": ((0.0, -1.05, 1.43), (0.0, 0.0, 1.40), 72, (1000, 1000)),
             "oblique": ((0.44, -0.92, 1.46), (0.0, -0.01, 1.40), 72, (1000, 1000)),
             "hairline": ((0.0, -0.53, 1.59), (0.0, -0.02, 1.55), 115, (1200, 850)),
             "top": ((0.0, -0.28, 1.88), (0.0, 0.0, 1.55), 105, (1200, 850))}
    camera.location, target, camera.data.lens, size = views[view]; look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size; scene.render.resolution_percentage = 100
    path = OUT / f"{label}-{view}-f{frame:02d}.png"; scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True); return str(path)


OUT.mkdir(parents=True, exist_ok=True); variants = []
for label, rows, left_children, right_children in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene; body = bpy.data.objects[BODY]; hair = bpy.data.objects[HAIR]; scalp = bpy.data.objects[SCALP]
    hair.hide_render = hair.hide_viewport = scalp.hide_render = scalp.hide_viewport = False
    strands = build_strands(evaluated_tree(scalp), rows, left_children, right_children)
    edit = append_strands(hair, strands); repair = repair_new_points(scene, hair, body, edit["newPointStart"])
    collision = collision_audit(scene, hair, body); passed = all(a["penetratingPoints"] == 0 for a in collision.values())
    renders = [render(scene, label, view, 1) for view in ("front", "oblique", "hairline", "top")]
    renders.append(render(scene, label, "front", 33))
    variants.append({"label": label, "edit": edit, "collisionRepair": repair, "collisionAudit": collision,
                     "technicalStatus": "TECHNICAL_PASS" if passed else "TECHNICAL_FAIL", "renders": renders})
    if label == SELECTED and passed:
        hair["aevrynd_revision"] = "v249r1127-full-length-part-guides"
        hair["aevrynd_part_method"] = "asymmetric full-length scalp-tangent guides with inherited motion"
        scene["aevrynd_release_state"] = "VISUAL_REVIEW_PENDING"; scene["aevrynd_website_promotion"] = "forbidden"
        scene.frame_set(1); bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

selected = next((v for v in variants if v["label"] == SELECTED and v["technicalStatus"] == "TECHNICAL_PASS"), None)
report = {"revision": "v249r1127-full-length-part-guides-sweep", "source": str(SOURCE),
          "output": str(OUTPUT) if selected else None,
          "method": "append complete centre-part-to-bob strands that follow the scalp before joining the side mass, with more coverage on the exposed screen-right side and nearest-neighbour inherited motion",
          "variants": variants, "selectedVariant": SELECTED if selected else None, "websitePromotionApproved": False,
          "candidateStatus": "VISUAL_REVIEW_PENDING" if selected else "TECHNICAL_FAIL_DIAGNOSTIC_ONLY"}
REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print("AEVRYND_R1127=" + json.dumps({"variants": [{"label": v["label"], "addedCurves": v["edit"]["addedCurves"],
      "totalPoints": v["edit"]["totalPoints"], "repair": v["collisionRepair"],
      "penetrating": {f: a["penetratingPoints"] for f, a in v["collisionAudit"].items()}, "status": v["technicalStatus"]}
      for v in variants]}, sort_keys=True))
