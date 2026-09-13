import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-canthus-fitted-wedge-r345.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-broad-medial-aperture-r418.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-broad-medial-aperture-r418.build-report.json"
AUDIT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-broad-medial-aperture-r418.collision-audit.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r418-broad-medial-aperture"
BODY = "AevryndFemaleBody_CC0_R249"
EYES = {"L": (0.034528, 1.607765, 1.0), "R": (-0.034443, 1.607765, -1.0)}
OUTER_HALF = 0.01025
SCALE = 1.13
RECESS = 0.0008


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def smoothstep(value):
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def gaussian(value, sigma):
    return math.exp(-0.5 * (value / sigma) ** 2)


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


def mapped_x(x, cx, sign):
    outer = cx + sign * OUTER_HALF
    return outer + (x - outer) * SCALE


def sculpt_body(body):
    body.data = body.data.copy()
    body.data.name = body.data.name + "_BroadMedialAperture_R418"
    inverse = body.matrix_world.inverted()
    moved = {"L": 0, "R": 0}
    maximum = 0.0
    for vertex in body.data.vertices:
        world = body.matrix_world @ vertex.co
        if not (-0.158 <= world.y <= -0.106) or not (1.588 <= world.z <= 1.627):
            continue
        side = min(EYES, key=lambda key: abs(world.x - EYES[key][0]))
        cx, cz, sign = EYES[side]
        u = sign * (world.x - cx)
        if not (-0.032 <= u <= 0.018):
            continue
        inner_fade = smoothstep((u + 0.032) / 0.024)
        outer_fade = 1.0 - smoothstep((u - 0.011) / 0.007)
        weight = gaussian(world.y + 0.132, 0.017) * gaussian(world.z - cz, 0.0105) * inner_fade * outer_fade
        if weight < 0.002:
            continue
        before = world.copy()
        world.x += (mapped_x(world.x, cx, sign) - world.x) * weight
        vertex.co = inverse @ world
        moved[side] += 1
        maximum = max(maximum, (world - before).length)
    body.data.update()
    body["aevrynd_face_revision"] = "v249r418-broad-medial-aperture"
    body["aevrynd_eye_aperture_method"] = "outer-canthus anchored medial extension with broad orbital-wall transition"
    body["aevrynd_eye_center_medial_shift_m"] = OUTER_HALF * (SCALE - 1.0)
    body["aevrynd_eye_layer_recess_m"] = RECESS
    return {"movedVertices": moved, "maximumDisplacementM": maximum}


def layer_names():
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


def fit_layers():
    report = {}
    shift = OUTER_HALF * (SCALE - 1.0)
    for name in layer_names():
        obj = bpy.data.objects[name]
        side = "L" if "_L_" in name or name.endswith("_L_R256") else "R"
        cx, _, sign = EYES[side]
        if "_Sclera_" in name:
            obj.matrix_world.translation.x -= sign * shift
            obj.matrix_world.translation.y += RECESS
            obj["aevrynd_revision"] = "v249r418-broad-medial-aperture"
            report[name] = {"centerShiftM": shift, "recessM": RECESS}
            continue

        obj.data = obj.data.copy()
        inverse = obj.matrix_world.inverted()
        moved = 0
        maximum = 0.0
        elements = obj.data.vertices if obj.type == "MESH" else [point for spline in obj.data.splines for point in spline.points]
        for element in elements:
            world = obj.matrix_world @ element.co
            target = world.copy()
            target.x = mapped_x(world.x, cx, sign)
            target.y += RECESS
            element.co = inverse @ target
            moved += 1
            maximum = max(maximum, (target - world).length)
        if obj.type == "MESH":
            obj.data.update()
        obj["aevrynd_revision"] = "v249r418-broad-medial-aperture"
        report[name] = {"elementsMoved": moved, "maximumDisplacementM": maximum, "recessM": RECESS}
    return report


def collision_audit(scene):
    audit = {"model": str(OUTPUT), "frames": {}, "violations": []}
    for frame in (1, 20):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        body_tree = world_bvh(bpy.data.objects[BODY], depsgraph)
        audit["frames"][str(frame)] = {}
        for side in EYES:
            eye_tree = world_bvh(bpy.data.objects[f"AevryndEye_{side}_Sclera_R249"], depsgraph)
            caruncle_tree = world_bvh(bpy.data.objects[f"AevryndEye_{side}_Caruncle_R258"], depsgraph)
            counts = {
                "bodyVsIntegratedEye": len(body_tree.overlap(eye_tree)),
                "bodyVsCaruncle": len(body_tree.overlap(caruncle_tree)),
                "integratedEyeVsCaruncle": len(eye_tree.overlap(caruncle_tree)),
            }
            audit["frames"][str(frame)][side] = counts
            for pair, count in counts.items():
                if count:
                    audit["violations"].append({"frame": frame, "side": side, "pair": pair, "triangleOverlaps": count})
    audit["status"] = "PASS" if not audit["violations"] else "FAIL"
    AUDIT.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    return audit


def render_views(scene, camera):
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
    for frame, name, location, target, lens in views:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        camera.location = location
        camera.data.lens = lens
        look_at(camera, target)
        scene.render.filepath = str(RENDER_DIR / f"{name}.png")
        bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
body_edit = sculpt_body(bpy.data.objects[BODY])
layer_edit = fit_layers()
collision = collision_audit(scene)

scene.frame_set(1)
scene["aevrynd_mainline_revision"] = "v249r418-broad-medial-aperture"
scene["aevrynd_release_state"] = "TECHNICAL_PASS_VISUAL_REVIEW_PENDING" if collision["status"] == "PASS" else "COLLISION_FAIL"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

RENDER_DIR.mkdir(parents=True, exist_ok=True)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.view_settings.exposure = 0.0
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
render_views(scene, camera)

report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "renderDirectory": str(RENDER_DIR),
    "anchoredOuterScale": SCALE,
    "eyeCenterMedialShiftM": OUTER_HALF * (SCALE - 1.0),
    "nominalInnerCanthusExtensionM": 2.0 * OUTER_HALF * (SCALE - 1.0),
    "eyeLayerRecessM": RECESS,
    "bodyEdit": body_edit,
    "layerEdit": layer_edit,
    "collisionAudit": str(AUDIT),
    "collisionStatus": collision["status"],
    "ownedAssetOnly": True,
    "status": "TECHNICAL_PASS_VISUAL_REVIEW_PENDING" if collision["status"] == "PASS" else "COLLISION_FAIL",
    "websitePromotionApproved": False,
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R418_BROAD_MEDIAL_APERTURE=" + json.dumps(report, sort_keys=True))
if collision["status"] != "PASS":
    raise SystemExit(2)
