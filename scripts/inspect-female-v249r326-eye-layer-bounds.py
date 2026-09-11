import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-collision-safe-optical-stack-r318.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-eye-layer-bounds-r326.study.json"

bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
rows = {}
for side in ("L", "R"):
    rows[side] = {}
    for part in ("Sclera_R249", "Cornea_R252", "Limbal_R253", "Iris_R253", "Pupil_R253"):
        obj = bpy.data.objects[f"AevryndEye_{side}_{part}"]
        points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
        rows[side][part] = {
            "vertices": len(points),
            "bounds": {axis: [min(point[index] for point in points), max(point[index] for point in points)] for index, axis in enumerate("xyz")},
            "center": [sum(point[index] for point in points) / len(points) for index in range(3)],
        }
report = {"source": str(SOURCE), "layers": rows, "status": "PASS"}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R326_EYE_LAYER_BOUNDS=" + json.dumps(report, sort_keys=True))
