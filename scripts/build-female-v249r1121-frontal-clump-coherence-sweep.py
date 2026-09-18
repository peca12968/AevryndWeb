"""Group chaotic frontal family-0 strands into ten coherent flow clumps."""
from pathlib import Path
import json
import math

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-right-temple-cleanup-r1120-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-frontal-clumps-r1121-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1121-frontal-clump-coherence-sweep.study.json"
OUT = ROOT.parent / "Temp" / "female-realism" / "v249r1121-frontal-clump-coherence-sweep"
BODY = "AevryndFemaleCC0PalpebralClosure_R1097"
HAIR = "AevryndFemaleGradedHairlineGroom_R1081"
SCALP = "AevryndFemaleTargetScalp_R976"
FAMILY = "aevrynd_family_r1087"
FRAMES = (1, 20, 33, 61)
CLEARANCE = 0.001
VARIANTS = (("a-soft", 0.35), ("b-balanced", 0.60), ("c-strong", 0.82))
SELECTED = "b-balanced"


def evaluated_tree(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, faces, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


def sample_polyline(points, t):
    scaled = t * (len(points) - 1)
    low = min(len(points) - 1, int(math.floor(scaled)))
    high = min(len(points) - 1, low + 1)
    f = scaled - low
    return points[low].lerp(points[high], f)


def smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def group_frontal_curves(hair):
    data = hair.data
    family = data.attributes[FAMILY]
    records = []
    for ci, curve in enumerate(data.curves):
        root = hair.matrix_world @ data.points[curve.first_point_index].position
        if family.data[ci].value != 0 or root.y >= -0.075 or root.z <= 1.50:
            continue
        pts = [hair.matrix_world @ data.points[curve.first_point_index + i].position for i in range(curve.points_length)]
        side = -1 if root.x < 0 else 1
        normalized = min(0.999999, abs(root.x) / 0.067)
        band = min(4, int(normalized * 5.0))
        records.append({"curve": ci, "points": pts, "root": pts[0], "end": pts[-1], "group": (side, band)})
    return records


def reshape(hair, strength):
    records = group_frontal_curves(hair)
    groups = {}
    for record in records:
        groups.setdefault(record["group"], []).append(record)
    centers = {}
    samples = 32
    for key, group in groups.items():
        centers[key] = [sum((sample_polyline(r["points"], i / (samples - 1)) for r in group), Vector()) / len(group) for i in range(samples)]
    inverse = hair.matrix_world.inverted()
    edited_points = []
    displacement = []
    for record in records:
        center = centers[record["group"]]
        center_root, center_end = center[0], center[-1]
        curve = hair.data.curves[record["curve"]]
        for local in range(1, curve.points_length - 1):
            index = curve.first_point_index + local
            t = local / (curve.points_length - 1)
            original = hair.matrix_world @ hair.data.points[index].position
            mean = sample_polyline(center, t)
            root_offset = (record["root"] - center_root) * ((1.0 - t) ** 1.7)
            end_offset = (record["end"] - center_end) * (t ** 1.7)
            target = mean + root_offset + end_offset
            weight = strength * smoothstep(t / 0.20) * smoothstep((1.0 - t) / 0.18)
            changed = original.lerp(target, weight)
            hair.data.points[index].position = inverse @ changed
            edited_points.append(index)
            displacement.append((changed - original).length)
    return {
        "editedCurves": len(records),
        "editedPoints": len(edited_points),
        "groupSizes": {f"{side}:{band}": len(group) for (side, band), group in sorted(groups.items())},
        "meanDisplacementM": sum(displacement) / len(displacement),
        "maximumDisplacementM": max(displacement),
    }, sorted(set(edited_points))


def repair_points(scene, hair, body, point_indices):
    inverse = hair.matrix_world.inverted()
    corrected = 0
    maximum = 0.0
    for _pass in range(5):
        pass_count = 0
        for frame in FRAMES:
            scene.frame_set(frame)
            depsgraph = bpy.context.evaluated_depsgraph_get()
            depsgraph.update()
            tree = evaluated_tree(body)
            evaluated = hair.evaluated_get(depsgraph)
            for index in point_indices:
                world = evaluated.matrix_world @ evaluated.data.points[index].position
                hit = tree.find_nearest(world)
                if not hit or hit[1] is None:
                    continue
                normal = hit[1].normalized()
                signed = (world - hit[0]).dot(normal)
                if signed < CLEARANCE:
                    delta = normal * (CLEARANCE - signed + 0.00005)
                    base = hair.matrix_world @ hair.data.points[index].position
                    hair.data.points[index].position = inverse @ (base + delta)
                    corrected += 1
                    pass_count += 1
                    maximum = max(maximum, delta.length)
        if not pass_count:
            break
    scene.frame_set(1)
    return {"correctedOperations": corrected, "maximumCorrectionM": maximum}


def collision_audit(scene, hair, body):
    result = {}
    for frame in FRAMES:
        scene.frame_set(frame)
        depsgraph = bpy.context.evaluated_depsgraph_get()
        depsgraph.update()
        tree = evaluated_tree(body)
        evaluated = hair.evaluated_get(depsgraph)
        signed = []
        for point in evaluated.data.points:
            world = evaluated.matrix_world @ point.position
            hit = tree.find_nearest(world)
            if hit and hit[1] is not None:
                signed.append((world - hit[0]).dot(hit[1].normalized()))
        result[str(frame)] = {
            "pointsTested": len(signed),
            "minimumSignedClearanceM": min(signed),
            "penetratingPoints": sum(v < -0.00005 for v in signed),
            "belowOneMmPoints": sum(v < CLEARANCE for v in signed),
        }
    scene.frame_set(1)
    return result


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, label, view, frame=1):
    scene.frame_set(frame)
    camera = scene.camera
    views = {
        "front": ((0.0, -1.05, 1.43), (0.0, 0.0, 1.40), 72, (1000, 1000)),
        "oblique": ((0.44, -0.92, 1.46), (0.0, -0.01, 1.40), 72, (1000, 1000)),
        "hairline": ((0.0, -0.53, 1.59), (0.0, -0.02, 1.55), 115, (1200, 850)),
        "top": ((0.0, -0.28, 1.88), (0.0, 0.0, 1.55), 105, (1200, 850)),
    }
    camera.location, target, camera.data.lens, size = views[view]
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    path = OUT / f"{label}-{view}-f{frame:02d}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return str(path)


OUT.mkdir(parents=True, exist_ok=True)
variants = []
for label, strength in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    body = bpy.data.objects[BODY]
    hair = bpy.data.objects[HAIR]
    scalp = bpy.data.objects[SCALP]
    hair.hide_render = hair.hide_viewport = scalp.hide_render = scalp.hide_viewport = False
    edit, indices = reshape(hair, strength)
    repair = repair_points(scene, hair, body, indices)
    collision = collision_audit(scene, hair, body)
    passed = all(item["penetratingPoints"] == 0 for item in collision.values())
    renders = [render(scene, label, view, 1) for view in ("front", "oblique", "hairline", "top")]
    renders.append(render(scene, label, "front", 33))
    variants.append({"label": label, "strength": strength, "edit": edit, "collisionRepair": repair,
                     "collisionAudit": collision, "technicalStatus": "TECHNICAL_PASS" if passed else "TECHNICAL_FAIL",
                     "renders": renders})
    if label == SELECTED and passed:
        hair["aevrynd_revision"] = "v249r1121-frontal-clump-coherence"
        hair["aevrynd_clump_method"] = "ten root-preserving averaged family-0 flow groups"
        scene["aevrynd_release_state"] = "VISUAL_REVIEW_PENDING"
        scene["aevrynd_website_promotion"] = "forbidden"
        scene.frame_set(1)
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

selected = next((v for v in variants if v["label"] == SELECTED and v["technicalStatus"] == "TECHNICAL_PASS"), None)
report = {"revision": "v249r1121-frontal-clump-coherence-sweep", "source": str(SOURCE),
          "output": str(OUTPUT) if selected else None,
          "method": "cluster frontal family-0 curves into five bands per side and blend their interiors toward a shared mean flow while preserving roots and endpoints",
          "variants": variants, "selectedVariant": SELECTED if selected else None,
          "websitePromotionApproved": False,
          "candidateStatus": "VISUAL_REVIEW_PENDING" if selected else "TECHNICAL_FAIL_DIAGNOSTIC_ONLY"}
REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print("AEVRYND_R1121=" + json.dumps({"variants": [{"label": v["label"], "curves": v["edit"]["editedCurves"],
      "meanMm": v["edit"]["meanDisplacementM"] * 1000, "maxMm": v["edit"]["maximumDisplacementM"] * 1000,
      "repair": v["collisionRepair"], "penetrating": {f: a["penetratingPoints"] for f, a in v["collisionAudit"].items()},
      "status": v["technicalStatus"]} for v in variants]}, sort_keys=True))
