import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cc0-normalized-rig-r251.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-cc0-normalized-rig-r251.eye-foundation-audit.json"


def bounds_world(obj):
    points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    return {
        "minimum": [min(point[i] for point in points) for i in range(3)],
        "maximum": [max(point[i] for point in points) for i in range(3)],
        "center": [sum(point[i] for point in points) / len(points) for i in range(3)],
        "vertices": len(points),
        "polygons": len(obj.data.polygons),
    }


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
bpy.context.scene.frame_set(1)
bpy.context.view_layer.update()

objects = {}
for obj in bpy.context.scene.objects:
    if obj.type != "MESH":
        continue
    layer = obj.get("aevrynd_layer", "")
    if layer.startswith("eye.") or "Eye" in obj.name:
        objects[obj.name] = {
            "layer": layer,
            "parent": obj.parent.name if obj.parent else None,
            "parentType": obj.parent_type,
            "parentBone": obj.parent_bone,
            "bounds": bounds_world(obj),
        }

body = bpy.data.objects["AevryndFemaleBody_CC0_R249"]
depsgraph = bpy.context.evaluated_depsgraph_get()
evaluated = body.evaluated_get(depsgraph)
mesh = evaluated.to_mesh()
world_points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
samples = {}
for side, center_x in (("L", 0.03446), ("R", -0.03440)):
    for label, x_offset, z in (
        ("brow_inner", -0.006 if side == "L" else 0.006, 1.632),
        ("brow_mid", 0.0, 1.635),
        ("brow_outer", 0.008 if side == "L" else -0.008, 1.631),
        ("lower_lid_inner", -0.005 if side == "L" else 0.005, 1.604),
        ("lower_lid_mid", 0.0, 1.6025),
        ("lower_lid_outer", 0.006 if side == "L" else -0.006, 1.604),
    ):
        target_x = center_x + x_offset
        nearest = min(world_points, key=lambda point: (point.x - target_x) ** 2 + (point.z - z) ** 2)
        samples[f"{side}.{label}"] = {
            "targetXZ": [target_x, z],
            "surface": list(nearest),
            "xzError": ((nearest.x - target_x) ** 2 + (nearest.z - z) ** 2) ** 0.5,
        }
evaluated.to_mesh_clear()

report = {"source": str(SOURCE), "frame": 1, "objects": objects, "faceSurfaceSamples": samples}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R251_EYE_FOUNDATION=" + json.dumps(report, sort_keys=True))
