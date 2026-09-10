import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-owned-hair-material-r129.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/female-v249r129-forehead-crossing-curves-r133.json"
MAIN = "AevryndFemaleCC0LongHairStudyMain_v249r85"


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
obj = bpy.data.objects[MAIN]
matrix = obj.matrix_world
bands = []
for y_limit in (-0.120, -0.130, -0.140, -0.150, -0.160):
    curve_hits = []
    point_hits = 0
    for curve_index, curve in enumerate(obj.data.curves):
        hit = False
        for point_index in range(curve.first_point_index, curve.first_point_index + curve.points_length):
            point = matrix @ obj.data.points[point_index].position
            if abs(point.x) <= 0.120 and y_limit - 0.020 <= point.y <= y_limit and 1.625 <= point.z <= 1.715:
                point_hits += 1
                hit = True
        if hit:
            curve_hits.append(curve_index)
    bands.append({
        "frontYBandM": [y_limit - 0.020, y_limit],
        "zBandM": [1.625, 1.715],
        "xAbsLimitM": 0.120,
        "curveCount": len(curve_hits),
        "pointCount": point_hits,
        "curveIndicesSample": curve_hits[:40],
    })

report = {
    "source": str(SOURCE),
    "object": MAIN,
    "totalCurves": len(obj.data.curves),
    "totalPoints": len(obj.data.points),
    "bands": bands,
}
OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R133_FOREHEAD_CROSSING=" + json.dumps(report, sort_keys=True))
