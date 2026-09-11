import json
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-recessed-natural-eyes-r301.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r314-conformal-eye-stack-sweep"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-conformal-eye-stack-r314.study.json"
BODY = "AevryndFemaleBody_CC0_R249"
VARIANTS = (("a-current", None), ("b-cornea-0p78", 0.78), ("c-cornea-0p86", 0.86), ("d-cornea-0p94", 0.94))


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def tree_for(obj, depsgraph=None):
    if depsgraph is not None:
        return BVHTree.FromObject(obj, depsgraph)
    vertices = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    polygons = [tuple(polygon.vertices) for polygon in obj.data.polygons]
    return BVHTree.FromPolygons(vertices, polygons, all_triangles=False)


def center_xz(obj):
    points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    return (sum(point.x for point in points) / len(points), sum(point.z for point in points) / len(points))


def conform_to_sclera(obj, sclera_tree, offset):
    inverse = obj.matrix_world.inverted()
    changed = 0
    for vertex in obj.data.vertices:
        world = obj.matrix_world @ vertex.co
        origin = Vector((world.x, -0.20, world.z))
        hit, _normal, _face, _distance = sclera_tree.ray_cast(origin, Vector((0.0, 1.0, 0.0)), 0.20)
        if hit is None:
            continue
        world.y = hit.y - offset
        vertex.co = inverse @ world
        changed += 1
    obj.data.update()
    return changed


def modify_stack(scale):
    metrics = {}
    for side in ("L", "R"):
        sclera = bpy.data.objects[f"AevryndEye_{side}_Sclera_R249"]
        sclera_tree = tree_for(sclera)
        conformed = {}
        for part, offset in (("Limbal_R253", 0.000055), ("Iris_R253", 0.000070), ("Pupil_R253", 0.000085)):
            obj = bpy.data.objects[f"AevryndEye_{side}_{part}"]
            obj.data = obj.data.copy()
            conformed[part] = conform_to_sclera(obj, sclera_tree, offset)
        cornea = bpy.data.objects[f"AevryndEye_{side}_Cornea_R252"]
        cornea.data = cornea.data.copy()
        cx, cz = center_xz(cornea)
        inverse = cornea.matrix_world.inverted()
        for vertex in cornea.data.vertices:
            world = cornea.matrix_world @ vertex.co
            world.x = cx + (world.x - cx) * scale
            world.z = cz + (world.z - cz) * scale
            vertex.co = inverse @ world
        cornea.data.update()
        metrics[side] = {"conformedVertices": conformed, "corneaScaleXZ": scale}
    return metrics


def audit(scene):
    scene.frame_set(1)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    body_tree = tree_for(bpy.data.objects[BODY], depsgraph)
    rows = {}
    total = 0
    for side in ("L", "R"):
        parts = {}
        for part in ("Sclera_R249", "Cornea_R252", "Limbal_R253", "Iris_R253", "Pupil_R253"):
            obj = bpy.data.objects[f"AevryndEye_{side}_{part}"]
            count = len(body_tree.overlap(tree_for(obj, depsgraph)))
            parts[part] = count
            total += count
        parts["CorneaVsIris"] = len(tree_for(bpy.data.objects[f"AevryndEye_{side}_Cornea_R252"], depsgraph).overlap(tree_for(bpy.data.objects[f"AevryndEye_{side}_Iris_R253"], depsgraph)))
        rows[side] = parts
    return rows, total


OUT.mkdir(parents=True, exist_ok=True)
metrics = {}
for name, scale in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.frame_set(1)
    bpy.context.view_layer.update()
    stack = modify_stack(scale) if scale is not None else {}
    overlaps, total = audit(scene)
    camera = bpy.data.objects["Aevrynd R249 Review Camera"]
    for suffix, location in (("front", (0.0, -0.68, 1.605)), ("three-quarter", (0.45, -0.62, 1.62)), ("profile", (0.67, -0.36, 1.61))):
        camera.location = location
        camera.data.lens = 92
        look_at(camera, (0.0, -0.02, 1.605))
        scene.render.resolution_x = scene.render.resolution_y = 1000
        scene.render.filepath = str(OUT / f"{name}-{suffix}.png")
        bpy.ops.render.render(write_still=True)
    metrics[name] = {"corneaScaleXZ": scale, "stack": stack, "overlaps": overlaps, "bodyEyeTriangleOverlaps": total}

report = {"source": str(SOURCE), "renderDirectory": str(OUT), "variants": metrics, "method": "sclera-conformal limbal iris pupil with scaled cornea cap", "status": "STRICT_VISUAL_AND_COLLISION_SELECTION_REQUIRED"}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R314_CONFORMAL_EYE_SWEEP=" + json.dumps({name: {"corneaScaleXZ": row["corneaScaleXZ"], "bodyEyeTriangleOverlaps": row["bodyEyeTriangleOverlaps"], "corneaVsIris": [row["overlaps"][side]["CorneaVsIris"] for side in ("L", "R")]} for name, row in metrics.items()}, sort_keys=True))
