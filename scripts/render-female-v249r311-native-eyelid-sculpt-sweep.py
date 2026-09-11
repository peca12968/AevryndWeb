import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-recessed-natural-eyes-r301.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r311-native-eyelid-sculpt-sweep"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-native-eyelid-sculpt-r311.study.json"
BODY = "AevryndFemaleBody_CC0_R249"
EYES = {"L": (0.034528, 1.607765, 1.0), "R": (-0.034443, 1.607765, -1.0)}
VARIANTS = (("a-current", 0.0), ("b-subtle", 0.55), ("c-natural", 0.85), ("d-strong", 1.15))


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def tree_for(obj):
    vertices = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    polygons = [tuple(polygon.vertices) for polygon in obj.data.polygons]
    return BVHTree.FromPolygons(vertices, polygons, all_triangles=False)


def sculpt(body, strength):
    changed = {}
    for side, (cx, cz, anatomical_sign) in EYES.items():
        sclera = bpy.data.objects[f"AevryndEye_{side}_Sclera_R249"]
        tree = tree_for(sclera)
        rows = []
        for vertex in body.data.vertices:
            world = body.matrix_world @ vertex.co
            u = (world.x - cx) / 0.0112
            if abs(u) >= 1.0 or world.z <= cz or world.z >= cz + 0.011 or world.y > -0.122:
                continue
            nearest = tree.find_nearest(world)
            if nearest[0] is None or nearest[3] > 0.0032:
                continue
            edge = math.sqrt(max(0.0, 1.0 - u * u))
            distance_weight = max(0.0, 1.0 - nearest[3] / 0.0032)
            vertical_weight = max(0.0, 1.0 - abs(world.z - (cz + 0.0047 * edge)) / 0.0060)
            weight = distance_weight * vertical_weight * edge
            if weight <= 0.01:
                continue
            delta_z = -0.00235 * strength * weight
            world.z += delta_z
            ray_origin = Vector((world.x, -0.20, world.z))
            hit, _normal, _face, _distance = tree.ray_cast(ray_origin, Vector((0.0, 1.0, 0.0)), 0.20)
            if hit is not None:
                world.y = min(world.y, hit.y - 0.00025)
            vertex.co = body.matrix_world.inverted() @ world
            rows.append({"index": vertex.index, "weight": weight, "deltaZM": delta_z})
        changed[side] = {
            "vertices": len(rows),
            "maximumDeltaZM": min((row["deltaZM"] for row in rows), default=0.0),
            "maximumWeight": max((row["weight"] for row in rows), default=0.0),
        }
    body.data.update()
    return changed


OUT.mkdir(parents=True, exist_ok=True)
metrics = {}
for name, strength in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.frame_set(1)
    bpy.context.view_layer.update()
    body = bpy.data.objects[BODY]
    body.data = body.data.copy()
    changed = sculpt(body, strength) if strength else {side: {"vertices": 0, "maximumDeltaZM": 0.0, "maximumWeight": 0.0} for side in EYES}
    camera = bpy.data.objects["Aevrynd R249 Review Camera"]
    for suffix, location in (("front", (0.0, -0.68, 1.605)), ("three-quarter", (0.45, -0.62, 1.62)), ("profile", (0.67, -0.36, 1.61))):
        camera.location = location
        camera.data.lens = 92
        look_at(camera, (0.0, -0.02, 1.605))
        scene.render.resolution_x = scene.render.resolution_y = 1000
        scene.render.filepath = str(OUT / f"{name}-{suffix}.png")
        bpy.ops.render.render(write_still=True)
    metrics[name] = {"strength": strength, "changed": changed}

report = {"source": str(SOURCE), "renderDirectory": str(OUT), "variants": metrics, "method": "native body vertices with sclera-distance falloff and 0.25mm front clearance", "status": "STRICT_VISUAL_SELECTION_REQUIRED"}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R311_NATIVE_EYELID_SWEEP=" + json.dumps(report, sort_keys=True))
