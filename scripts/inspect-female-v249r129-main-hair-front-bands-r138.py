import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-owned-hair-material-r129.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/female-v249r129-main-hair-front-bands-r138.json"
MAIN = "AevryndFemaleCC0LongHairStudyMain_v249r85"


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
obj = bpy.data.objects[MAIN]
matrix = obj.matrix_world
bands = []
for band_index in range(12):
    y_min = -0.160 + band_index * 0.010
    y_max = y_min + 0.010
    curves = set()
    points = []
    for curve_index, curve in enumerate(obj.data.curves):
        for local_index, point_index in enumerate(
            range(curve.first_point_index, curve.first_point_index + curve.points_length)
        ):
            point = matrix @ obj.data.points[point_index].position
            if abs(point.x) <= 0.125 and y_min <= point.y < y_max and 1.625 <= point.z <= 1.735:
                curves.add(curve_index)
                points.append((curve_index, local_index, point_index))
    bands.append({
        "yBandM": [y_min, y_max],
        "curveCount": len(curves),
        "pointCount": len(points),
        "curveIndicesSample": sorted(curves)[:30],
        "pointIndicesSample": [item[2] for item in points[:30]],
    })

report = {
    "source": str(SOURCE),
    "object": MAIN,
    "xAbsLimitM": 0.125,
    "zBandM": [1.625, 1.735],
    "bands": bands,
}
OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R138_MAIN_HAIR_BANDS=" + json.dumps(report, sort_keys=True))
