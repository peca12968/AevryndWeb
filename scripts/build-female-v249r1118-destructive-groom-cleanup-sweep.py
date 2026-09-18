"""Actually remove camera-visible face crossings and trim curve topology."""
from pathlib import Path
import json
import math

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-integrated-upper-lip-r1110-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-groom-cleanup-r1118-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1118-destructive-groom-cleanup-sweep.study.json"
OUT = ROOT.parent / "Temp" / "female-realism" / "v249r1118-destructive-groom-cleanup-sweep"
BODY = "AevryndFemaleCC0PalpebralClosure_R1097"
HAIR = "AevryndFemaleGradedHairlineGroom_R1081"
SCALP = "AevryndFemaleTargetScalp_R976"
PATCH = "Aevrynd_ContinuousUpperLip_R1105"
FRAMES = (1, 20, 33, 61)
# label, facial clear-zone width scale, minimum visible points, minimum retained point fraction
VARIANTS = (
    ("a-conservative", 0.65, 5, 0.90),
    ("b-balanced", 0.80, 4, 0.82),
    ("c-open-face", 1.00, 3, 0.74),
)
SELECTED = "a-conservative"


def smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def evaluated_points(scene, hair):
    scene.frame_set(1)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    evaluated = hair.evaluated_get(depsgraph)
    return evaluated, [evaluated.matrix_world @ point.position for point in evaluated.data.points]


def refine_geometry(scene, hair, body, width_scale, minimum_hits, minimum_fraction):
    evaluated, world_points = evaluated_points(scene, hair)
    if len(evaluated.data.curves) != len(hair.data.curves) or len(world_points) != len(hair.data.points):
        raise RuntimeError("The motion modifier changed curve topology")
    hidden = []
    before_curves = len(hair.data.curves)
    before_points = len(hair.data.points)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    tree = body_tree(body, depsgraph)
    camera = Vector((0.0, -1.05, 1.43))
    for curve_index, curve in enumerate(hair.data.curves):
        crossing = 0
        for local in range(curve.points_length):
            point = world_points[curve.first_point_index + local]
            if not 1.29 < point.z < 1.535:
                continue
            ray = point - camera
            distance = ray.length
            hit, normal, _polygon, hit_distance = tree.ray_cast(camera, ray.normalized(), distance + 0.30)
            if hit is None or hit_distance is None or hit_distance <= distance + 0.0005 or normal.y >= -0.25:
                continue
            width = (0.074 if hit.z < 1.38 else 0.092) * width_scale
            if abs(hit.x) < width:
                crossing += 1
        if crossing >= minimum_hits:
            hidden.append(curve_index)
    sizes = []
    for curve_index, curve in enumerate(hair.data.curves):
        random_value = math.sin(curve_index * 12.9898 + 78.233) * 43758.5453
        random_value -= math.floor(random_value)
        fraction = minimum_fraction + (1.0 - minimum_fraction) * random_value
        sizes.append(max(8, min(curve.points_length, round(curve.points_length * fraction))))
    hair.data.resize_curves(sizes=sizes)
    hair.data.remove_curves(indices=hidden)
    return {
        "removedFaceCrossingCurves": len(hidden),
        "removedCurveSample": hidden[:30],
        "beforeCurves": before_curves,
        "afterCurves": len(hair.data.curves),
        "beforePoints": before_points,
        "afterPoints": len(hair.data.points),
        "rayCamera": list(camera),
        "faceZoneWidthScale": width_scale,
        "minimumVisiblePointsPerCurve": minimum_hits,
        "faceZone": {"lowerFaceHalfWidthM": 0.074 * width_scale, "upperFaceHalfWidthM": 0.092 * width_scale, "zRangeM": [1.29, 1.535]},
        "minimumRetainedPointFraction": minimum_fraction,
        "minimumCurvePoints": min(curve.points_length for curve in hair.data.curves),
        "maximumCurvePoints": max(curve.points_length for curve in hair.data.curves),
    }


def body_tree(body, depsgraph):
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, faces, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


def collision_audit(scene, hair, body):
    result = {}
    for frame in FRAMES:
        scene.frame_set(frame)
        depsgraph = bpy.context.evaluated_depsgraph_get()
        depsgraph.update()
        tree = body_tree(body, depsgraph)
        evaluated = hair.evaluated_get(depsgraph)
        radius = evaluated.data.attributes.get("radius")
        signed = []
        visible = 0
        for index, point in enumerate(evaluated.data.points):
            if radius and radius.data[index].value <= 1e-8:
                continue
            visible += 1
            world = evaluated.matrix_world @ point.position
            hit = tree.find_nearest(world)
            if hit and hit[1] is not None:
                signed.append((world - hit[0]).dot(hit[1].normalized()))
        result[str(frame)] = {
            "visiblePoints": visible,
            "testedPoints": len(signed),
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
    if view == "front":
        camera.location, target, lens = (0.0, -1.05, 1.43), (0.0, 0.0, 1.40), 72
    elif view == "oblique":
        camera.location, target, lens = (0.44, -0.92, 1.46), (0.0, -0.01, 1.40), 72
    elif view == "profile":
        camera.location, target, lens = (0.92, -0.18, 1.45), (0.0, -0.01, 1.40), 72
    else:
        camera.location, target, lens = (0.0, 1.02, 1.43), (0.0, 0.0, 1.40), 72
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x = scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    path = OUT / f"{label}-{view}-f{frame:02d}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return str(path)


OUT.mkdir(parents=True, exist_ok=True)
variants = []
for label, width_scale, minimum_hits, minimum_fraction in VARIANTS:
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
    edit = refine_geometry(scene, hair, body, width_scale, minimum_hits, minimum_fraction)
    collision = collision_audit(scene, hair, body)
    technical_pass = all(item["penetratingPoints"] == 0 for item in collision.values())
    renders = [render(scene, label, view, 1) for view in ("front", "oblique", "profile", "back")]
    renders.append(render(scene, label, "front", 33))
    variants.append({
        "label": label,
        "edit": edit,
        "collisionAudit": collision,
        "technicalStatus": "TECHNICAL_PASS" if technical_pass else "TECHNICAL_FAIL",
        "renders": renders,
    })
    if label == SELECTED and technical_pass:
        hair["aevrynd_revision"] = "v249r1118-destructive-groom-cleanup"
        hair["aevrynd_face_clearance_method"] = "front-camera body-ray curve deletion"
        hair["aevrynd_tip_method"] = "deterministic curve topology trim"
        scene["aevrynd_release_state"] = "VISUAL_REVIEW_PENDING"
        scene["aevrynd_website_promotion"] = "forbidden"
        scene.frame_set(1)
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))


selected_item = next((item for item in variants if item["label"] == SELECTED and item["technicalStatus"] == "TECHNICAL_PASS"), None)
report = {
    "revision": "v249r1118-destructive-groom-cleanup-sweep",
    "source": str(SOURCE),
    "output": str(OUTPUT) if selected_item else None,
    "method": "cast strand points through the front review camera, physically delete curves that sit in front of the facial clear zone, and resize remaining curves to deterministic clump-specific point counts",
    "variants": variants,
    "selectedVariant": SELECTED if selected_item else None,
    "websitePromotionApproved": False,
    "candidateStatus": "VISUAL_REVIEW_PENDING" if selected_item else "TECHNICAL_FAIL_DIAGNOSTIC_ONLY",
}
REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print("AEVRYND_R1118_HAIR=" + json.dumps({
    "variants": [{
        "label": item["label"],
        "removed": item["edit"]["removedFaceCrossingCurves"],
        "curves": item["edit"]["afterCurves"],
        "points": item["edit"]["afterPoints"],
        "penetrating": {frame: value["penetratingPoints"] for frame, value in item["collisionAudit"].items()},
        "minimumMm": {frame: value["minimumSignedClearanceM"] * 1000.0 for frame, value in item["collisionAudit"].items()},
        "status": item["technicalStatus"],
    } for item in variants]
}, sort_keys=True))
