import json
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-recessed-natural-eyes-r301.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r317-cornea-clearance-sweep"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-cornea-clearance-r317.study.json"
BODY = "AevryndFemaleBody_CC0_R249"
SCALE = 0.76
VARIANTS = (("a-0p04mm", 0.00004), ("b-0p08mm", 0.00008), ("c-0p12mm", 0.00012))


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


def clamp_cornea(cornea, iris, clearance):
    iris_y = sum((iris.matrix_world @ vertex.co).y for vertex in iris.data.vertices) / len(iris.data.vertices)
    inverse = cornea.matrix_world.inverted()
    changed = 0
    for vertex in cornea.data.vertices:
        world = cornea.matrix_world @ vertex.co
        maximum_y = iris_y - clearance
        if world.y > maximum_y:
            world.y = maximum_y
            vertex.co = inverse @ world
            changed += 1
    cornea.data.update()
    return {"irisPlaneY": iris_y, "maximumCorneaY": iris_y - clearance, "clampedVertices": changed}


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
            "corneaVsPupil": len(tree(objects["Cornea_R252"], depsgraph).overlap(tree(objects["Pupil_R253"], depsgraph))),
            "irisVsPupil": len(tree(objects["Iris_R253"], depsgraph).overlap(tree(objects["Pupil_R253"], depsgraph))),
        }
        body_total += sum(body_rows.values())
        internal_total += sum(internal.values())
        rows[side] = {"body": body_rows, "internal": internal}
    return rows, body_total, internal_total


OUT.mkdir(parents=True, exist_ok=True)
metrics = {}
for name, clearance in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    clamped = {}
    for side in ("L", "R"):
        for part in ("Cornea_R252", "Limbal_R253", "Iris_R253", "Pupil_R253"):
            obj = bpy.data.objects[f"AevryndEye_{side}_{part}"]
            obj.data = obj.data.copy()
            scale_xz(obj, SCALE)
        cornea = bpy.data.objects[f"AevryndEye_{side}_Cornea_R252"]
        iris = bpy.data.objects[f"AevryndEye_{side}_Iris_R253"]
        clamped[side] = clamp_cornea(cornea, iris, clearance)
    overlaps, body_total, internal_total = audit(scene)
    camera = bpy.data.objects["Aevrynd R249 Review Camera"]
    for suffix, location in (("front", (0.0, -0.68, 1.605)), ("three-quarter", (0.45, -0.62, 1.62)), ("profile", (0.67, -0.36, 1.61))):
        camera.location = location
        camera.data.lens = 92
        look_at(camera, (0.0, -0.02, 1.605))
        scene.render.resolution_x = scene.render.resolution_y = 1000
        scene.render.filepath = str(OUT / f"{name}-{suffix}.png")
        bpy.ops.render.render(write_still=True)
    metrics[name] = {"scaleXZ": SCALE, "clearanceM": clearance, "clamped": clamped, "overlaps": overlaps, "bodyEyeTriangleOverlaps": body_total, "internalTriangleOverlaps": internal_total}

report = {"source": str(SOURCE), "renderDirectory": str(OUT), "variants": metrics, "status": "STRICT_VISUAL_AND_COLLISION_SELECTION_REQUIRED"}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R317_CORNEA_CLEARANCE_SWEEP=" + json.dumps({name: {"clearanceM": row["clearanceM"], "body": row["bodyEyeTriangleOverlaps"], "internal": row["internalTriangleOverlaps"]} for name, row in metrics.items()}, sort_keys=True))
