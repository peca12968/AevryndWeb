import json
import os
import statistics
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
MODEL = Path(os.environ.get(
    "AEVRYND_HAIR_RADIUS_MODEL",
    ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-face-r38.blend",
))
NAMES = ("AevryndFemaleGuideBob_v249r25", "AevryndFemaleNapeFiberFill_v249r17")

bpy.ops.wm.open_mainfile(filepath=str(MODEL))
report = {"model": str(MODEL), "objects": {}}
for name in NAMES:
    obj = bpy.data.objects[name]
    values = sorted(item.value for item in obj.data.attributes["radius"].data)
    report["objects"][name] = {
        "curve_count": len(obj.data.curves),
        "point_count": len(obj.data.points),
        "radius_m": {
            "min": values[0],
            "p10": values[len(values) // 10],
            "median": values[len(values) // 2],
            "p90": values[len(values) * 9 // 10],
            "max": values[-1],
            "mean": statistics.fmean(values),
        },
    }
print("AEVRYND_HAIR_RADIUS=" + json.dumps(report, sort_keys=True))
