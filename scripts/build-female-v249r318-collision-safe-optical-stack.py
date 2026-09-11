import json
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-curved-projected-upper-eyelids-r308.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-collision-safe-optical-stack-r318.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-collision-safe-optical-stack-r318.build-report.json"
AUDIT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-collision-safe-optical-stack-r318.collision-audit.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r318-collision-safe-optical-stack"
BODY = "AevryndFemaleBody_CC0_R249"
SCALE = 0.76
CORNEA_IRIS_CLEARANCE = 0.00008
FRAMES = (1, 20)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def scale_xz(obj, factor):
    points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    cx = sum(point.x for point in points) / len(points)
    cz = sum(point.z for point in points) / len(points)
    inverse = obj.matrix_world.inverted()
    for vertex, world in zip(obj.data.vertices, points):
        world.x = cx + (world.x - cx) * factor
        world.z = cz + (world.z - cz) * factor
        vertex.co = inverse @ world
    obj.data.update()


def clamp_cornea(cornea, iris):
    iris_y = sum((iris.matrix_world @ vertex.co).y for vertex in iris.data.vertices) / len(iris.data.vertices)
    maximum_y = iris_y - CORNEA_IRIS_CLEARANCE
    inverse = cornea.matrix_world.inverted()
    changed = 0
    for vertex in cornea.data.vertices:
        world = cornea.matrix_world @ vertex.co
        if world.y > maximum_y:
            world.y = maximum_y
            vertex.co = inverse @ world
            changed += 1
    cornea.data.update()
    return {"irisPlaneY": iris_y, "maximumCorneaY": maximum_y, "clampedVertices": changed}


def tree(obj, depsgraph):
    return BVHTree.FromObject(obj, depsgraph)


def overlaps(a, b, depsgraph):
    return len(tree(a, depsgraph).overlap(tree(b, depsgraph)))


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
modified = {}
for side in ("L", "R"):
    for part in ("Cornea_R252", "Limbal_R253", "Iris_R253", "Pupil_R253"):
        obj = bpy.data.objects[f"AevryndEye_{side}_{part}"]
        obj.data = obj.data.copy()
        scale_xz(obj, SCALE)
        obj["aevrynd_revision"] = "v249r318"
        obj["aevrynd_optical_scale_xz"] = SCALE
    cornea = bpy.data.objects[f"AevryndEye_{side}_Cornea_R252"]
    iris = bpy.data.objects[f"AevryndEye_{side}_Iris_R253"]
    modified[side] = clamp_cornea(cornea, iris)
    cornea["aevrynd_cornea_iris_clearance_m"] = CORNEA_IRIS_CLEARANCE

audit = {"frames": {}, "violations": []}
for frame in FRAMES:
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    body = bpy.data.objects[BODY]
    frame_rows = {}
    for side in ("L", "R"):
        objects = {part: bpy.data.objects[f"AevryndEye_{side}_{part}"] for part in ("Sclera_R249", "Cornea_R252", "Limbal_R253", "Iris_R253", "Pupil_R253")}
        lid = bpy.data.objects[f"AevryndEye_{side}_UpperLidSurface_R308"]
        body_rows = {part: overlaps(body, obj, depsgraph) for part, obj in objects.items()}
        lid_rows = {part: overlaps(lid, obj, depsgraph) for part, obj in objects.items()}
        lid_rows["Body"] = overlaps(lid, body, depsgraph)
        internal = {
            "corneaVsLimbal": overlaps(objects["Cornea_R252"], objects["Limbal_R253"], depsgraph),
            "corneaVsIris": overlaps(objects["Cornea_R252"], objects["Iris_R253"], depsgraph),
            "corneaVsPupil": overlaps(objects["Cornea_R252"], objects["Pupil_R253"], depsgraph),
            "irisVsPupil": overlaps(objects["Iris_R253"], objects["Pupil_R253"], depsgraph),
        }
        frame_rows[side] = {"body": body_rows, "upperLid": lid_rows, "internal": internal}
        for group, rows in frame_rows[side].items():
            for pair, count in rows.items():
                if count:
                    audit["violations"].append({"frame": frame, "side": side, "group": group, "pair": pair, "triangleOverlaps": count})
    audit["frames"][str(frame)] = frame_rows
audit["status"] = "PASS" if not audit["violations"] else "FAIL"
AUDIT.write_text(json.dumps(audit, indent=2), encoding="utf-8")

scene["aevrynd_mainline_revision"] = "v249r318-collision-safe-optical-stack"
scene["aevrynd_release_state"] = "TECHNICAL_PASS_VISUAL_REVIEW_PENDING" if audit["status"] == "PASS" else "COLLISION_FAIL"
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
views = (
    (1, "front-f01", (0.0, -0.90, 1.59), (0.0, 0.0, 1.56), 82),
    (20, "front-f20", (0.0, -0.90, 1.59), (0.0, 0.0, 1.56), 82),
    (1, "face-close-f01", (0.0, -0.68, 1.605), (0.0, -0.035, 1.606), 92),
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
    scene.render.resolution_x = scene.render.resolution_y = 1000
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)

scene.frame_set(1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE), "output": str(OUTPUT), "opticalScaleXZ": SCALE,
    "corneaIrisClearanceM": CORNEA_IRIS_CLEARANCE, "modified": modified,
    "collisionAudit": str(AUDIT), "collisionStatus": audit["status"],
    "renderDirectory": str(RENDER_DIR), "ownedAssetOnly": True,
    "status": "TECHNICAL_PASS_VISUAL_REVIEW_PENDING" if audit["status"] == "PASS" else "FAIL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R318_COLLISION_SAFE_OPTICAL_STACK=" + json.dumps(report, sort_keys=True))
if audit["status"] != "PASS":
    raise SystemExit(2)
