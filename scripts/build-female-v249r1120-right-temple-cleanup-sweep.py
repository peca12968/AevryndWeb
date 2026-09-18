"""Remove the remaining screen-right temple curtain from the accepted r1118 groom."""
from pathlib import Path
import json

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-groom-cleanup-r1118-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-right-temple-cleanup-r1120-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1120-right-temple-cleanup-sweep.study.json"
OUT = ROOT.parent / "Temp" / "female-realism" / "v249r1120-right-temple-cleanup-sweep"
BODY = "AevryndFemaleCC0PalpebralClosure_R1097"
HAIR = "AevryndFemaleGradedHairlineGroom_R1081"
SCALP = "AevryndFemaleTargetScalp_R976"
FRAMES = (1, 20, 33, 61)
# label, inner x, outer x, minimum camera-visible hits
VARIANTS = (
    ("a-narrow", 0.028, 0.070, 5),
    ("b-balanced", 0.018, 0.082, 4),
    ("c-open", 0.010, 0.092, 3),
)
SELECTED = "b-balanced"


def body_tree(body, depsgraph):
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, faces, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


def evaluated_points(scene, hair):
    scene.frame_set(1)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    evaluated = hair.evaluated_get(depsgraph)
    return evaluated, [evaluated.matrix_world @ point.position for point in evaluated.data.points]


def remove_right_temple(scene, hair, body, inner_x, outer_x, minimum_hits):
    evaluated, points = evaluated_points(scene, hair)
    if len(evaluated.data.curves) != len(hair.data.curves) or len(points) != len(hair.data.points):
        raise RuntimeError("The motion modifier changed curve topology")
    tree = body_tree(body, bpy.context.evaluated_depsgraph_get())
    camera = Vector((0.0, -1.05, 1.43))
    remove = []
    samples = []
    for curve_index, curve in enumerate(hair.data.curves):
        hits = 0
        for local in range(curve.points_length):
            point = points[curve.first_point_index + local]
            if not 1.295 < point.z < 1.525:
                continue
            ray = point - camera
            distance = ray.length
            hit, normal, _polygon, hit_distance = tree.ray_cast(camera, ray.normalized(), distance + 0.30)
            if hit is None or hit_distance is None or hit_distance <= distance + 0.0005 or normal.y >= -0.25:
                continue
            if inner_x < hit.x < outer_x:
                hits += 1
        if hits >= minimum_hits:
            remove.append(curve_index)
            if len(samples) < 30:
                samples.append({"curve": curve_index, "hits": hits})
    before_curves = len(hair.data.curves)
    before_points = len(hair.data.points)
    hair.data.remove_curves(indices=remove)
    return {
        "removedCurves": len(remove),
        "removedSample": samples,
        "beforeCurves": before_curves,
        "afterCurves": len(hair.data.curves),
        "beforePoints": before_points,
        "afterPoints": len(hair.data.points),
        "bodyHitXRangeM": [inner_x, outer_x],
        "bodyHitZRangeM": [1.295, 1.525],
        "minimumVisibleHits": minimum_hits,
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
        result[str(frame)] = {
            "pointsTested": len(signed),
            "minimumSignedClearanceM": min(signed),
            "penetratingPoints": sum(value < -0.00005 for value in signed),
            "belowOneMmPoints": sum(value < 0.001 for value in signed),
        }
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
        "right-temple": ((0.25, -0.72, 1.46), (0.025, -0.01, 1.42), 88),
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
for label, inner_x, outer_x, minimum_hits in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    body = bpy.data.objects[BODY]
    hair = bpy.data.objects[HAIR]
    scalp = bpy.data.objects[SCALP]
    hair.hide_render = hair.hide_viewport = False
    scalp.hide_render = scalp.hide_viewport = False
    edit = remove_right_temple(scene, hair, body, inner_x, outer_x, minimum_hits)
    collision = collision_audit(scene, hair, body)
    passed = all(item["penetratingPoints"] == 0 for item in collision.values())
    renders = [render(scene, label, view, 1) for view in ("front", "oblique", "right-temple")]
    renders.append(render(scene, label, "front", 33))
    variants.append({
        "label": label,
        "edit": edit,
        "collisionAudit": collision,
        "technicalStatus": "TECHNICAL_PASS" if passed else "TECHNICAL_FAIL",
        "renders": renders,
    })
    if label == SELECTED and passed:
        hair["aevrynd_revision"] = "v249r1120-right-temple-cleanup"
        hair["aevrynd_cleanup_method"] = "one-sided front-camera body-ray curve deletion"
        scene["aevrynd_release_state"] = "VISUAL_REVIEW_PENDING"
        scene["aevrynd_website_promotion"] = "forbidden"
        scene.frame_set(1)
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

selected = next((item for item in variants if item["label"] == SELECTED and item["technicalStatus"] == "TECHNICAL_PASS"), None)
report = {
    "revision": "v249r1120-right-temple-cleanup-sweep",
    "source": str(SOURCE),
    "output": str(OUTPUT) if selected else None,
    "method": "physically delete only curves occluding the screen-right temple and cheek, based on body-ray hit coordinates",
    "variants": variants,
    "selectedVariant": SELECTED if selected else None,
    "websitePromotionApproved": False,
    "candidateStatus": "VISUAL_REVIEW_PENDING" if selected else "TECHNICAL_FAIL_DIAGNOSTIC_ONLY",
}
REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print("AEVRYND_R1120=" + json.dumps({
    "variants": [{
        "label": item["label"],
        "removed": item["edit"]["removedCurves"],
        "curves": item["edit"]["afterCurves"],
        "points": item["edit"]["afterPoints"],
        "penetrating": {frame: value["penetratingPoints"] for frame, value in item["collisionAudit"].items()},
        "status": item["technicalStatus"],
    } for item in variants]
}, sort_keys=True))
