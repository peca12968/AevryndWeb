import json
import math
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-recessed-natural-eyes-r301.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r313-native-socket-clearance-sweep"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-native-socket-clearance-r313.study.json"
BODY = "AevryndFemaleBody_CC0_R249"
EYES = {"L": (0.034528, 1.607765), "R": (-0.034443, 1.607765)}
VARIANTS = (("a-current", 0.0), ("b-0p5mm", 0.0005), ("c-0p9mm", 0.0009), ("d-1p3mm", 0.0013))


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def tree_for(obj, depsgraph=None):
    if depsgraph is not None:
        return BVHTree.FromObject(obj, depsgraph)
    vertices = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    polygons = [tuple(polygon.vertices) for polygon in obj.data.polygons]
    return BVHTree.FromPolygons(vertices, polygons, all_triangles=False)


def sculpt(body, forward):
    changed = {}
    for side, (cx, cz) in EYES.items():
        cornea = bpy.data.objects[f"AevryndEye_{side}_Cornea_R252"]
        cornea_tree = tree_for(cornea)
        count = 0
        max_weight = 0.0
        for vertex in body.data.vertices:
            world = body.matrix_world @ vertex.co
            u = (world.x - cx) / 0.0130
            v = (world.z - cz) / 0.0100
            if u * u + v * v >= 1.35 or world.y > -0.120:
                continue
            hit = cornea_tree.find_nearest(world)
            if hit[0] is None or hit[3] > 0.0042:
                continue
            radial = max(0.0, 1.0 - (u * u + v * v) / 1.35)
            proximity = max(0.0, 1.0 - hit[3] / 0.0042)
            weight = radial * proximity
            if weight <= 0.015:
                continue
            world.y -= forward * weight
            edge = math.sqrt(max(0.0, 1.0 - min(1.0, u * u)))
            if world.z > cz:
                world.z -= 0.00155 * (forward / 0.0013 if forward else 0.0) * weight * edge
            else:
                world.z += 0.00035 * (forward / 0.0013 if forward else 0.0) * weight * edge
            vertex.co = body.matrix_world.inverted() @ world
            count += 1
            max_weight = max(max_weight, weight)
        changed[side] = {"vertices": count, "maximumWeight": max_weight}
    body.data.update()
    return changed


def audit(scene, body):
    scene.frame_set(1)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    body_tree = tree_for(body, depsgraph)
    rows = {}
    for side in EYES:
        parts = {}
        for part in ("Sclera_R249", "Cornea_R252", "Limbal_R253", "Iris_R253", "Pupil_R253"):
            parts[part] = len(body_tree.overlap(tree_for(bpy.data.objects[f"AevryndEye_{side}_{part}"], depsgraph)))
        rows[side] = parts
    return rows, sum(value for side in rows.values() for value in side.values())


OUT.mkdir(parents=True, exist_ok=True)
metrics = {}
for name, forward in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.frame_set(1)
    bpy.context.view_layer.update()
    body = bpy.data.objects[BODY]
    body.data = body.data.copy()
    changed = sculpt(body, forward) if forward else {side: {"vertices": 0, "maximumWeight": 0.0} for side in EYES}
    overlaps, total = audit(scene, body)
    camera = bpy.data.objects["Aevrynd R249 Review Camera"]
    for suffix, location in (("front", (0.0, -0.68, 1.605)), ("three-quarter", (0.45, -0.62, 1.62)), ("profile", (0.67, -0.36, 1.61))):
        camera.location = location
        camera.data.lens = 92
        look_at(camera, (0.0, -0.02, 1.605))
        scene.render.resolution_x = scene.render.resolution_y = 1000
        scene.render.filepath = str(OUT / f"{name}-{suffix}.png")
        bpy.ops.render.render(write_still=True)
    metrics[name] = {"forwardM": forward, "changed": changed, "overlaps": overlaps, "totalTriangleOverlaps": total}

report = {"source": str(SOURCE), "renderDirectory": str(OUT), "variants": metrics, "status": "STRICT_VISUAL_AND_COLLISION_SELECTION_REQUIRED"}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R313_NATIVE_SOCKET_SWEEP=" + json.dumps({name: {"forwardM": row["forwardM"], "totalTriangleOverlaps": row["totalTriangleOverlaps"]} for name, row in metrics.items()}, sort_keys=True))
