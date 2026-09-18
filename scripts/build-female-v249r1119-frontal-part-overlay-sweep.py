"""Add short scalp-projected fibers to narrow the exposed frontal centre part."""
from pathlib import Path
import json
import math
import random

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-groom-cleanup-r1118-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-frontal-part-overlay-r1119-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1119-frontal-part-overlay-sweep.study.json"
OUT = ROOT.parent / "Temp" / "female-realism" / "v249r1119-frontal-part-overlay-sweep"
BODY = "AevryndFemaleCC0PalpebralClosure_R1097"
HAIR = "AevryndFemaleGradedHairlineGroom_R1081"
SCALP = "AevryndFemaleTargetScalp_R976"
PATCH = "Aevrynd_ContinuousUpperLip_R1105"
CLEARANCE = 0.0010
FRAMES = (1, 20, 33, 61)
# label, rows, children per side per row, outer width range
VARIANTS = (
    ("a-light", 4, 8, (0.052, 0.072)),
    ("b-balanced", 6, 10, (0.058, 0.082)),
    ("c-dense", 8, 12, (0.064, 0.092)),
)
SELECTED = "b-balanced"


def smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


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


def build_overlay_strands(scalp_tree, rows, children, outer_range):
    strands = []
    for row in range(rows):
        root_y = -0.118 + row * 0.0065
        for side in (-1.0, 1.0):
            for child in range(children):
                rng = random.Random(1119000 + row * 1000 + int((side + 1.0) * 500) + child)
                root_x = side * rng.uniform(0.0012, 0.0042)
                root_y_jitter = root_y + rng.uniform(-0.0018, 0.0018)
                outer_x = side * rng.uniform(*outer_range)
                outer_y = root_y_jitter + rng.uniform(0.004, 0.016)
                strand = []
                valid = True
                for point_index in range(16):
                    t = point_index / 15.0
                    eased = smoothstep(t)
                    probe = Vector((
                        root_x + (outer_x - root_x) * eased,
                        root_y_jitter + (outer_y - root_y_jitter) * eased + math.sin(math.pi * t) * rng.uniform(-0.0007, 0.0007),
                        1.585,
                    ))
                    hit = scalp_tree.find_nearest(probe, 0.14)
                    if hit is None or hit[1] is None:
                        valid = False
                        break
                    strand.append(hit[0] + hit[1].normalized() * CLEARANCE)
                if valid:
                    strands.append(strand)
    return strands


def append_strands(hair, strands):
    old_curves = len(hair.data.curves)
    old_points = len(hair.data.points)
    hair.data.add_curves([len(strand) for strand in strands])
    inverse = hair.matrix_world.inverted()
    radius = hair.data.attributes.get("radius") or hair.data.attributes.new("radius", "FLOAT", "POINT")
    family = hair.data.attributes.get("aevrynd_family_r1087") or hair.data.attributes.new("aevrynd_family_r1087", "INT", "CURVE")
    motion = hair.data.attributes.get("aevrynd_motion_vector_r1083")
    phase = hair.data.attributes.get("aevrynd_motion_phase_r1083")
    for offset, strand in enumerate(strands):
        curve_index = old_curves + offset
        curve = hair.data.curves[curve_index]
        family.data[curve_index].value = 5
        for local, world in enumerate(strand):
            index = curve.first_point_index + local
            t = local / max(1, len(strand) - 1)
            hair.data.points[index].position = inverse @ world
            radius.data[index].value = 0.000052 * (1.0 - smoothstep((t - 0.42) / 0.58)) + 0.000004
            if motion:
                motion.data[index].vector = (0.0, 0.0, 0.0)
            if phase:
                phase.data[index].value = 0.0
    return {
        "oldCurves": old_curves,
        "oldPoints": old_points,
        "addedCurves": len(strands),
        "newPointStart": old_points,
        "totalCurves": len(hair.data.curves),
        "totalPoints": len(hair.data.points),
    }


def repair_new_points(scene, hair, body, start):
    corrected = 0
    maximum = 0.0
    for _pass in range(4):
        pass_count = 0
        for frame in FRAMES:
            scene.frame_set(frame)
            depsgraph = bpy.context.evaluated_depsgraph_get()
            depsgraph.update()
            tree = evaluated_tree(body)
            evaluated = hair.evaluated_get(depsgraph)
            inverse = hair.matrix_world.inverted()
            for index in range(start, len(hair.data.points)):
                world = evaluated.matrix_world @ evaluated.data.points[index].position
                hit = tree.find_nearest(world)
                if hit is None or hit[1] is None:
                    continue
                normal = hit[1].normalized()
                signed = (world - hit[0]).dot(normal)
                if signed < CLEARANCE:
                    delta = normal * (CLEARANCE - signed + 0.00005)
                    base_world = hair.matrix_world @ hair.data.points[index].position
                    hair.data.points[index].position = inverse @ (base_world + delta)
                    corrected += 1
                    pass_count += 1
                    maximum = max(maximum, delta.length)
        if pass_count == 0:
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
            "penetratingPoints": sum(value < -0.00005 for value in signed),
            "belowOneMmPoints": sum(value < CLEARANCE for value in signed),
        }
    scene.frame_set(1)
    return result


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, label, view, frame=1):
    scene.frame_set(frame)
    camera = scene.camera
    if view == "front":
        camera.location, target, lens, size = (0.0, -1.05, 1.43), (0.0, 0.0, 1.40), 72, (1000, 1000)
    elif view == "oblique":
        camera.location, target, lens, size = (0.44, -0.92, 1.46), (0.0, -0.01, 1.40), 72, (1000, 1000)
    elif view == "profile":
        camera.location, target, lens, size = (0.92, -0.18, 1.45), (0.0, -0.01, 1.40), 72, (1000, 1000)
    elif view == "hairline":
        camera.location, target, lens, size = (0.0, -0.53, 1.59), (0.0, -0.02, 1.55), 115, (1200, 850)
    else:
        camera.location, target, lens, size = (0.0, -0.28, 1.88), (0.0, 0.0, 1.55), 105, (1200, 850)
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    path = OUT / f"{label}-{view}-f{frame:02d}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return str(path)


OUT.mkdir(parents=True, exist_ok=True)
variants = []
for label, rows, children, outer_range in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    body = bpy.data.objects[BODY]
    hair = bpy.data.objects[HAIR]
    scalp = bpy.data.objects[SCALP]
    hair.hide_render = hair.hide_viewport = False
    scalp.hide_render = scalp.hide_viewport = False
    patch = bpy.data.objects.get(PATCH)
    if patch:
        patch.hide_render = patch.hide_viewport = True
    strands = build_overlay_strands(evaluated_tree(scalp), rows, children, outer_range)
    append = append_strands(hair, strands)
    repair = repair_new_points(scene, hair, body, append["newPointStart"])
    collision = collision_audit(scene, hair, body)
    technical_pass = all(item["penetratingPoints"] == 0 for item in collision.values())
    renders = [render(scene, label, view) for view in ("front", "oblique", "profile", "hairline", "top")]
    renders.append(render(scene, label, "front", 33))
    variants.append({
        "label": label,
        "rows": rows,
        "childrenPerSidePerRow": children,
        "outerRangeM": list(outer_range),
        "append": append,
        "collisionRepair": repair,
        "collisionAudit": collision,
        "technicalStatus": "TECHNICAL_PASS" if technical_pass else "TECHNICAL_FAIL",
        "renders": renders,
    })
    if label == SELECTED and technical_pass:
        hair["aevrynd_revision"] = "v249r1119-frontal-part-overlay"
        hair["aevrynd_frontal_part_family"] = 5
        scene["aevrynd_release_state"] = "VISUAL_REVIEW_PENDING"
        scene["aevrynd_website_promotion"] = "forbidden"
        scene.frame_set(1)
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))


selected_item = next((item for item in variants if item["label"] == SELECTED and item["technicalStatus"] == "TECHNICAL_PASS"), None)
report = {
    "revision": "v249r1119-frontal-part-overlay-sweep",
    "source": str(SOURCE),
    "output": str(OUTPUT) if selected_item else None,
    "method": "append short tapered family-5 fibers projected along the existing owned scalp from near-centre frontal roots toward the side flow, then repair the new point envelope across four motion frames",
    "variants": variants,
    "selectedVariant": SELECTED if selected_item else None,
    "websitePromotionApproved": False,
    "candidateStatus": "VISUAL_REVIEW_PENDING" if selected_item else "TECHNICAL_FAIL_DIAGNOSTIC_ONLY",
}
REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print("AEVRYND_R1119_PART_OVERLAY=" + json.dumps({
    "variants": [{
        "label": item["label"],
        "added": item["append"]["addedCurves"],
        "points": item["append"]["totalPoints"],
        "repair": item["collisionRepair"],
        "penetrating": {frame: value["penetratingPoints"] for frame, value in item["collisionAudit"].items()},
        "minimumMm": {frame: value["minimumSignedClearanceM"] * 1000.0 for frame, value in item["collisionAudit"].items()},
        "status": item["technicalStatus"],
    } for item in variants]
}, sort_keys=True))
