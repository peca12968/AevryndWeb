import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-canthus-fitted-wedge-r345.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-recessed-orbital-folds-r413.build-report.json"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-recessed-orbital-folds-r413.blend"
AUDIT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-recessed-orbital-folds-r413.collision-audit.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r413-recessed-orbital-folds"
BODY = "AevryndFemaleBody_CC0_R249"
EYES = {"L": (0.034528, 1.607765, 1.0), "R": (-0.034443, 1.607765, -1.0)}
OLD_HALF = 0.01025
UPPER_APERTURE = 0.0022
LOWER_APERTURE = 0.0041
NEW_HALF = 0.0098
LAYER_RECESS = 0.0010
ORBITAL_STRENGTH = 1.10


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def smoothstep(value):
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def gaussian(value, sigma):
    return math.exp(-((value / sigma) ** 2))


def edge(lateral, half):
    return math.sqrt(max(0.0, 1.0 - min(1.0, (lateral / half) ** 2)))


def margin_z(cz, lateral, half, upper):
    aperture = UPPER_APERTURE if upper else -LOWER_APERTURE
    return cz + aperture * edge(lateral, half)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def world_bvh(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, faces, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


def make_body(source, name):
    obj = bpy.data.objects.new(name, source.data.copy())
    bpy.context.scene.collection.objects.link(obj)
    obj.matrix_world = source.matrix_world.copy()
    return obj


def sculpt_outer_canthus(body, new_half):
    inverse = body.matrix_world.inverted()
    moved = {"L": 0, "R": 0}
    maximum = 0.0
    for vertex in body.data.vertices:
        world = body.matrix_world @ vertex.co
        if not (-0.122 <= world.y <= -0.112):
            continue
        side = "L" if world.x >= 0.0 else "R"
        cx, cz, sign = EYES[side]
        dx = world.x - cx
        lateral = sign * dx
        if lateral <= 0.0015 or lateral >= 0.0134 or abs(world.z - cz) > 0.0115:
            continue
        upper = world.z >= cz
        old_z = margin_z(cz, lateral, OLD_HALF, upper)
        margin_weight = gaussian(world.z - old_z, 0.0032)
        lateral_weight = smoothstep((lateral - 0.0015) / 0.0065)
        outer_fade = 1.0 - smoothstep((lateral - 0.0117) / 0.0017)
        weight = margin_weight * lateral_weight * outer_fade
        if weight < 0.002:
            continue
        target_lateral = lateral * new_half / OLD_HALF
        target_z = margin_z(cz, target_lateral, new_half, upper)
        before = world.copy()
        world.x += sign * (target_lateral - lateral) * weight
        world.z += (target_z - old_z) * weight
        vertex.co = inverse @ world
        moved[side] += 1
        maximum = max(maximum, (world - before).length)
    body.data.update()
    return {"movedVertices": moved, "maximumDisplacementM": maximum}


def sculpt_orbital_folds(body, strength):
    inverse = body.matrix_world.inverted()
    moved = {"L": 0, "R": 0}
    maximum = 0.0
    components = {"upperRoll": 0.0, "upperCrease": 0.0, "lowerRoll": 0.0, "tearTrough": 0.0}
    for vertex in body.data.vertices:
        world = body.matrix_world @ vertex.co
        if not (-0.122 <= world.y <= -0.112):
            continue
        side = "L" if world.x >= 0.0 else "R"
        cx, cz, sign = EYES[side]
        dx = world.x - cx
        u = dx / OLD_HALF
        if abs(u) > 1.34 or abs(world.z - cz) > 0.014:
            continue
        ellipse = edge(abs(dx), OLD_HALF)
        lateral_fade = smoothstep((1.30 - abs(u)) / 0.24)
        upper_margin = cz + UPPER_APERTURE * ellipse
        lower_margin = cz - LOWER_APERTURE * ellipse
        upper_roll = -0.00058 * gaussian(world.z - (upper_margin + 0.00115), 0.00145)
        upper_crease = 0.00048 * gaussian(world.z - (upper_margin + 0.00415), 0.00105)
        lower_roll = -0.00046 * gaussian(world.z - (lower_margin - 0.00115), 0.00155)
        lateral_u = sign * dx / OLD_HALF
        trough_z = lower_margin - 0.0034 - 0.0010 * clamp((lateral_u + 0.65) / 0.95)
        tear_trough = 0.00036 * gaussian(world.z - trough_z, 0.00135) * gaussian(lateral_u + 0.24, 0.62)
        side_strength = strength * (1.0 if side == "L" else 0.94)
        values = {
            "upperRoll": upper_roll * lateral_fade * side_strength,
            "upperCrease": upper_crease * lateral_fade * side_strength,
            "lowerRoll": lower_roll * lateral_fade * side_strength,
            "tearTrough": tear_trough * lateral_fade * side_strength,
        }
        delta_y = sum(values.values())
        if abs(delta_y) < 1e-7:
            continue
        before = world.copy()
        world.y += delta_y
        vertex.co = inverse @ world
        moved[side] += 1
        maximum = max(maximum, (world - before).length)
        for name, value in values.items():
            components[name] = max(components[name], abs(value))
    body.data.update()
    return {"movedVertices": moved, "maximumDisplacementM": maximum, "maximumComponentM": components}


def attached_names():
    return [
        name
        for side in EYES
        for name in (
            f"AevryndEye_{side}_Sclera_R249",
            f"AevryndEye_{side}_Caruncle_R258",
            f"AevryndEye_{side}_UpperLidMargin_R258",
            f"AevryndEye_{side}_LowerLidMargin_R258",
            f"AevryndEye_{side}_TearMeniscus_R258",
            f"AevryndFemaleUpperLashes_{side}_R256",
            f"AevryndFemaleLowerLashes_{side}_R256",
        )
    ]


def curve_point_snapshot(obj):
    return [point.co.copy() for spline in obj.data.splines for point in spline.points]


def restore_and_fit_layers(new_half, recess, matrices, curves):
    moved_points = 0
    for name in attached_names():
        obj = bpy.data.objects[name]
        obj.matrix_world = matrices[name].copy()
        obj.matrix_world.translation.y += recess
        if obj.type != "CURVE":
            continue
        original = curves[name]
        point_index = 0
        side = "L" if "_L_" in name else "R"
        cx, cz, sign = EYES[side]
        upper = "Upper" in name
        if "Lower" in name or "Meniscus" in name:
            upper = False
        for spline in obj.data.splines:
            for point in spline.points:
                point.co = original[point_index].copy()
                dx = point.co.x - cx
                lateral = sign * dx
                if lateral > 0.0015:
                    blend = smoothstep((lateral - 0.0015) / 0.0065)
                    target_lateral = lateral * (1.0 - blend + blend * new_half / OLD_HALF)
                    point.co.x = cx + sign * target_lateral
                    point.co.z += (margin_z(cz, target_lateral, new_half, upper) - margin_z(cz, lateral, OLD_HALF, upper)) * blend
                    moved_points += 1
                point_index += 1
    return moved_points


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
body = bpy.data.objects[BODY]
body.data = body.data.copy()
names = attached_names()
matrices = {name: bpy.data.objects[name].matrix_world.copy() for name in names}
curves = {}
for name in names:
    obj = bpy.data.objects[name]
    if obj.type == "CURVE":
        obj.data = obj.data.copy()
        curves[name] = curve_point_snapshot(obj)

outer_edit = sculpt_outer_canthus(body, NEW_HALF)
orbital_edit = sculpt_orbital_folds(body, ORBITAL_STRENGTH)
moved_points = restore_and_fit_layers(NEW_HALF, LAYER_RECESS, matrices, curves)
body["aevrynd_revision"] = "v249r413-recessed-orbital-folds"
body["aevrynd_outer_canthus_half_width_m"] = NEW_HALF
body["aevrynd_eye_layer_recess_m"] = LAYER_RECESS
body["aevrynd_orbital_fold_strength"] = ORBITAL_STRENGTH

collision = {"frames": {}, "violations": []}
for frame in (1, 20):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    body_tree = world_bvh(body, depsgraph)
    collision["frames"][str(frame)] = {}
    for side in EYES:
        sclera = bpy.data.objects[f"AevryndEye_{side}_Sclera_R249"]
        caruncle = bpy.data.objects[f"AevryndEye_{side}_Caruncle_R258"]
        eye_tree = world_bvh(sclera, depsgraph)
        caruncle_tree = world_bvh(caruncle, depsgraph)
        counts = {
            "bodyVsIntegratedEye": len(body_tree.overlap(eye_tree)),
            "bodyVsCaruncle": len(body_tree.overlap(caruncle_tree)),
            "integratedEyeVsCaruncle": len(eye_tree.overlap(caruncle_tree)),
        }
        collision["frames"][str(frame)][side] = counts
        for pair, count in counts.items():
            if count:
                collision["violations"].append({"frame": frame, "side": side, "pair": pair, "triangleOverlaps": count})
collision["status"] = "PASS" if not collision["violations"] else "FAIL"
AUDIT.write_text(json.dumps(collision, indent=2), encoding="utf-8")

scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.view_settings.exposure = 0.0
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
views = (
    (1, "front-f01", (0.0, -0.90, 1.59), (0.0, 0.0, 1.56), 82),
    (20, "front-f20", (0.0, -0.90, 1.59), (0.0, 0.0, 1.56), 82),
    (1, "face-close-f01", (0.0, -0.68, 1.605), (0.0, -0.035, 1.606), 92),
    (1, "eyes-close-f01", (0.0, -0.46, 1.615), (0.0, -0.035, 1.610), 105),
    (1, "three-quarter-f01", (0.45, -0.62, 1.62), (0.0, -0.02, 1.605), 90),
    (1, "left-f01", (-0.72, -0.55, 1.59), (0.0, 0.0, 1.56), 82),
    (1, "right-f01", (0.72, -0.55, 1.59), (0.0, 0.0, 1.56), 82),
    (1, "back-f01", (0.0, 0.90, 1.59), (0.0, 0.0, 1.56), 82),
)
for frame, view_name, location, target, lens in views:
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x = scene.render.resolution_y = 1000
    scene.render.filepath = str(RENDER_DIR / f"{view_name}.png")
    bpy.ops.render.render(write_still=True)

scene.frame_set(1)
scene["aevrynd_mainline_revision"] = "v249r413-recessed-orbital-folds"
scene["aevrynd_release_state"] = "TECHNICAL_PASS_VISUAL_REVIEW_PENDING" if collision["status"] == "PASS" else "COLLISION_FAIL"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "renderDirectory": str(RENDER_DIR),
    "outerHalfWidthM": NEW_HALF,
    "nominalFullWidthM": NEW_HALF * 2.0,
    "eyeLayerRecessM": LAYER_RECESS,
    "orbitalFoldStrength": ORBITAL_STRENGTH,
    "outerCanthusEdit": outer_edit,
    "orbitalFoldEdit": orbital_edit,
    "movedAttachedCurvePoints": moved_points,
    "collisionAudit": str(AUDIT),
    "collisionStatus": collision["status"],
    "ownedAssetOnly": True,
    "status": "TECHNICAL_PASS_VISUAL_REVIEW_PENDING" if collision["status"] == "PASS" else "COLLISION_FAIL",
    "websitePromotionApproved": False,
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R413_RECESSED_ORBITAL_FOLDS=" + json.dumps(report, sort_keys=True))
if collision["status"] != "PASS":
    raise SystemExit(2)
