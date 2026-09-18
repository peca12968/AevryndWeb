"""Clear the face curtain and vary clump tips by editing only strand radius."""
from pathlib import Path
import json
import math

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-integrated-upper-lip-r1110-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-face-clear-hair-r1115-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1115-face-clear-hair-tip-sweep.study.json"
OUT = ROOT.parent / "Temp" / "female-realism" / "v249r1115-face-clear-hair-tip-sweep"
BODY = "AevryndFemaleCC0PalpebralClosure_R1097"
HAIR = "AevryndFemaleGradedHairlineGroom_R1081"
SCALP = "AevryndFemaleTargetScalp_R976"
PATCH = "Aevrynd_ContinuousUpperLip_R1105"
FRAMES = (1, 20, 33, 61)
# label, central x limit, forward y limit, taper start min/max, crown radius multiplier
VARIANTS = (
    ("a-conservative", 0.090, -0.135, 0.82, 0.96, 1.15),
    ("b-balanced", 0.105, -0.130, 0.72, 0.94, 1.35),
    ("c-open-face", 0.120, -0.125, 0.62, 0.92, 1.60),
)
SELECTED = None


def smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def evaluated_points(scene, hair):
    scene.frame_set(1)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    evaluated = hair.evaluated_get(depsgraph)
    return evaluated, [evaluated.matrix_world @ point.position for point in evaluated.data.points]


def refine_radius(scene, hair, x_limit, y_limit, taper_min, taper_max, crown_multiplier):
    radius = hair.data.attributes.get("radius")
    if radius is None:
        raise RuntimeError("Hair radius attribute is missing")
    family = hair.data.attributes.get("aevrynd_family_r1087")
    evaluated, world_points = evaluated_points(scene, hair)
    if len(evaluated.data.curves) != len(hair.data.curves) or len(world_points) != len(hair.data.points):
        raise RuntimeError("The motion modifier changed curve topology")
    hidden = []
    tapered = 0
    crown_curves = 0
    radius_before = [item.value for item in radius.data]
    for curve_index, curve in enumerate(hair.data.curves):
        crossing = 0
        for local in range(curve.points_length):
            point = world_points[curve.first_point_index + local]
            if abs(point.x) < x_limit and point.y < y_limit and 1.26 < point.z < 1.56:
                crossing += 1
        if crossing >= 2:
            hidden.append(curve_index)
            for local in range(curve.points_length):
                radius.data[curve.first_point_index + local].value = 0.0
            continue
        family_value = family.data[curve_index].value if family else 0
        is_crown = family_value == 4
        if is_crown:
            crown_curves += 1
        random_value = math.sin(curve_index * 12.9898 + 78.233) * 43758.5453
        random_value -= math.floor(random_value)
        taper_start = taper_min + (taper_max - taper_min) * random_value
        for local in range(curve.points_length):
            index = curve.first_point_index + local
            t = local / max(1, curve.points_length - 1)
            taper = 1.0 if t <= taper_start else 1.0 - smoothstep((t - taper_start) / max(1e-8, 1.0 - taper_start))
            multiplier = crown_multiplier if is_crown and t < 0.65 else 1.0
            radius.data[index].value = radius_before[index] * taper * multiplier
            if taper < 0.999:
                tapered += 1
    visible_points = sum(item.value > 1e-8 for item in radius.data)
    return {
        "hiddenFaceCrossingCurves": len(hidden),
        "hiddenCurveSample": hidden[:30],
        "taperedPoints": tapered,
        "visiblePointsAfter": visible_points,
        "crownFamilyCurves": crown_curves,
        "crownRadiusMultiplier": crown_multiplier,
        "faceZone": {"absoluteXLessThanM": x_limit, "yLessThanM": y_limit, "zRangeM": [1.26, 1.56]},
        "tipTaperStartRange": [taper_min, taper_max],
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
for label, x_limit, y_limit, taper_min, taper_max, crown_multiplier in VARIANTS:
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
    edit = refine_radius(scene, hair, x_limit, y_limit, taper_min, taper_max, crown_multiplier)
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
        hair["aevrynd_revision"] = "v249r1115-face-clear-hair-tip"
        hair["aevrynd_face_clearance_method"] = "radius mask; no point displacement"
        hair["aevrynd_tip_method"] = "deterministic per-curve taper"
        scene["aevrynd_release_state"] = "VISUAL_REVIEW_PENDING"
        scene["aevrynd_website_promotion"] = "forbidden"
        scene.frame_set(1)
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))


selected_item = next((item for item in variants if item["label"] == SELECTED and item["technicalStatus"] == "TECHNICAL_PASS"), None)
report = {
    "revision": "v249r1115-face-clear-hair-tip-sweep",
    "source": str(SOURCE),
    "output": str(OUTPUT) if selected_item else None,
    "method": "hide only curves that cross a measured face projection zone, taper every remaining curve at a deterministic clump-specific length, and thicken the existing crown-overlay family without moving any control point",
    "variants": variants,
    "selectedVariant": SELECTED if selected_item else None,
    "websitePromotionApproved": False,
    "candidateStatus": "VISUAL_REVIEW_PENDING" if selected_item else "TECHNICAL_FAIL_DIAGNOSTIC_ONLY",
}
REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print("AEVRYND_R1115_HAIR=" + json.dumps({
    "variants": [{
        "label": item["label"],
        "hidden": item["edit"]["hiddenFaceCrossingCurves"],
        "visiblePoints": item["edit"]["visiblePointsAfter"],
        "penetrating": {frame: value["penetratingPoints"] for frame, value in item["collisionAudit"].items()},
        "minimumMm": {frame: value["minimumSignedClearanceM"] * 1000.0 for frame, value in item["collisionAudit"].items()},
        "status": item["technicalStatus"],
    } for item in variants]
}, sort_keys=True))
