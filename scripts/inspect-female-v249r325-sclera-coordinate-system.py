import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-collision-safe-optical-stack-r318.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-sclera-coordinate-system-r325.study.json"

bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
rows = {}
for side in ("L", "R"):
    obj = bpy.data.objects[f"AevryndEye_{side}_Sclera_R249"]
    local = [vertex.co for vertex in obj.data.vertices]
    world = [obj.matrix_world @ value for value in local]
    rows[side] = {
        "object": obj.name,
        "vertices": len(local),
        "polygons": len(obj.data.polygons),
        "matrixWorld": [list(row) for row in obj.matrix_world],
        "localBounds": {axis: [min(value[index] for value in local), max(value[index] for value in local)] for index, axis in enumerate("xyz")},
        "worldBounds": {axis: [min(value[index] for value in world), max(value[index] for value in world)] for index, axis in enumerate("xyz")},
        "uvLayers": [{"name": layer.name, "active": layer.active, "render": layer.active_render} for layer in obj.data.uv_layers],
        "materials": [slot.material.name if slot.material else None for slot in obj.material_slots],
    }
report = {"source": str(SOURCE), "eyes": rows, "status": "PASS"}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R325_SCLERA_COORDINATES=" + json.dumps(report, sort_keys=True))
