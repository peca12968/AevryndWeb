import json
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-recessed-natural-eyes-r301.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r316-separated-optical-stack-sweep"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-separated-optical-stack-r316.study.json"
BODY = "AevryndFemaleBody_CC0_R249"
CORNEA_SCALE = 0.76
VARIANTS = (("a-iris-0p66", 0.66), ("b-iris-0p70", 0.70), ("c-iris-0p74", 0.74))


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


def tree(obj, depsgraph):
    return BVHTree.FromObject(obj, depsgraph)


def audit(scene):
    scene.frame_set(1)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    body_tree = tree(bpy.data.objects[BODY], depsgraph)
    rows, body_total, internal_total = {}, 0, 0
    for side in ("L", "R"):
        objects = {part: bpy.data.objects[f"AevryndEye_{side}_{part}"] for part in ("Sclera_R249", "Cornea_R252", "Limbal_R253", "Iris_R253", "Pupil_R253")}
        body_rows = {part: len(body_tree.overlap(tree(obj, depsgraph))) for part, obj in objects.items()}
        internal = {
            "corneaVsLimbal": len(tree(objects["Cornea_R252"], depsgraph).overlap(tree(objects["Limbal_R253"], depsgraph))),
            "corneaVsIris": len(tree(objects["Cornea_R252"], depsgraph).overlap(tree(objects["Iris_R253"], depsgraph))),
            "irisVsPupil": len(tree(objects["Iris_R253"], depsgraph).overlap(tree(objects["Pupil_R253"], depsgraph))),
        }
        body_total += sum(body_rows.values())
        internal_total += sum(internal.values())
        rows[side] = {"body": body_rows, "internal": internal}
    return rows, body_total, internal_total


OUT.mkdir(parents=True, exist_ok=True)
metrics = {}
for name, iris_scale in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    for side in ("L", "R"):
        cornea = bpy.data.objects[f"AevryndEye_{side}_Cornea_R252"]
        cornea.data = cornea.data.copy()
        scale_xz(cornea, CORNEA_SCALE)
        for part in ("Limbal_R253", "Iris_R253", "Pupil_R253"):
            obj = bpy.data.objects[f"AevryndEye_{side}_{part}"]
            obj.data = obj.data.copy()
            scale_xz(obj, iris_scale)
    overlaps, body_total, internal_total = audit(scene)
    camera = bpy.data.objects["Aevrynd R249 Review Camera"]
    for suffix, location in (("front", (0.0, -0.68, 1.605)), ("three-quarter", (0.45, -0.62, 1.62)), ("profile", (0.67, -0.36, 1.61))):
        camera.location = location
        camera.data.lens = 92
        look_at(camera, (0.0, -0.02, 1.605))
        scene.render.resolution_x = scene.render.resolution_y = 1000
        scene.render.filepath = str(OUT / f"{name}-{suffix}.png")
        bpy.ops.render.render(write_still=True)
    metrics[name] = {"corneaScaleXZ": CORNEA_SCALE, "irisStackScaleXZ": iris_scale, "overlaps": overlaps, "bodyEyeTriangleOverlaps": body_total, "internalTriangleOverlaps": internal_total}

report = {"source": str(SOURCE), "renderDirectory": str(OUT), "variants": metrics, "status": "STRICT_VISUAL_AND_COLLISION_SELECTION_REQUIRED"}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R316_SEPARATED_OPTICAL_SWEEP=" + json.dumps({name: {"irisScale": row["irisStackScaleXZ"], "body": row["bodyEyeTriangleOverlaps"], "internal": row["internalTriangleOverlaps"]} for name, row in metrics.items()}, sort_keys=True))
