import json
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-recessed-natural-eyes-r301.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r315-collision-safe-optical-scale-sweep"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-collision-safe-optical-scale-r315.study.json"
BODY = "AevryndFemaleBody_CC0_R249"
VARIANTS = (("a-current", 1.0), ("b-0p74", 0.74), ("c-0p76", 0.76), ("d-0p78", 0.78), ("e-0p82", 0.82), ("f-0p86", 0.86))


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def tree(obj, depsgraph):
    return BVHTree.FromObject(obj, depsgraph)


def scale_object_xz(obj, factor):
    points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    cx = sum(point.x for point in points) / len(points)
    cz = sum(point.z for point in points) / len(points)
    inverse = obj.matrix_world.inverted()
    for vertex, world in zip(obj.data.vertices, points):
        world.x = cx + (world.x - cx) * factor
        world.z = cz + (world.z - cz) * factor
        vertex.co = inverse @ world
    obj.data.update()


def audit(scene):
    scene.frame_set(1)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    body_tree = tree(bpy.data.objects[BODY], depsgraph)
    rows, total = {}, 0
    for side in ("L", "R"):
        parts = {}
        for part in ("Sclera_R249", "Cornea_R252", "Limbal_R253", "Iris_R253", "Pupil_R253"):
            count = len(body_tree.overlap(tree(bpy.data.objects[f"AevryndEye_{side}_{part}"], depsgraph)))
            parts[part] = count
            total += count
        rows[side] = parts
    return rows, total


OUT.mkdir(parents=True, exist_ok=True)
metrics = {}
for name, factor in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.frame_set(1)
    bpy.context.view_layer.update()
    if factor != 1.0:
        for side in ("L", "R"):
            for part in ("Cornea_R252", "Limbal_R253", "Iris_R253", "Pupil_R253"):
                obj = bpy.data.objects[f"AevryndEye_{side}_{part}"]
                obj.data = obj.data.copy()
                scale_object_xz(obj, factor)
    overlaps, total = audit(scene)
    camera = bpy.data.objects["Aevrynd R249 Review Camera"]
    for suffix, location in (("front", (0.0, -0.68, 1.605)), ("three-quarter", (0.45, -0.62, 1.62)), ("profile", (0.67, -0.36, 1.61))):
        camera.location = location
        camera.data.lens = 92
        look_at(camera, (0.0, -0.02, 1.605))
        scene.render.resolution_x = scene.render.resolution_y = 1000
        scene.render.filepath = str(OUT / f"{name}-{suffix}.png")
        bpy.ops.render.render(write_still=True)
    metrics[name] = {"scaleXZ": factor, "overlaps": overlaps, "bodyEyeTriangleOverlaps": total}

report = {"source": str(SOURCE), "renderDirectory": str(OUT), "variants": metrics, "method": "concentric XZ scaling while preserving material depth order", "status": "STRICT_VISUAL_AND_COLLISION_SELECTION_REQUIRED"}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R315_OPTICAL_SCALE_SWEEP=" + json.dumps({name: {"scaleXZ": row["scaleXZ"], "bodyEyeTriangleOverlaps": row["bodyEyeTriangleOverlaps"]} for name, row in metrics.items()}, sort_keys=True))
