import json
import os
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get(
    "AEVRYND_CHARACTER_SOURCE",
    ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cc0-natural-long-hair-r94.blend",
))
OUTPUT = Path(os.environ.get(
    "AEVRYND_ROOT_COVERAGE_REPORT",
    ROOT.parent / "Temp/female-realism/v249r94-root-coverage.json",
))
HAIR = (
    "AevryndFemaleCC0LongHairStudyMain_v249r85",
    "AevryndFemaleCC0LongHairStudyFlyaway_v249r85",
)


def bin_counts(values, axis, lower, upper, count):
    bins = [0] * count
    for value in values:
        unit = (value[axis] - lower) / (upper - lower)
        if 0.0 <= unit <= 1.0:
            bins[min(count - 1, int(unit * count))] += 1
    return bins


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
report = {"source": str(SOURCE), "objects": {}}
for name in HAIR:
    obj = bpy.data.objects[name]
    roots = []
    for curve in obj.data.curves:
        point = obj.data.points[curve.first_point_index].position
        roots.append(tuple(obj.matrix_world @ point))
    front = [root for root in roots if root[1] <= -0.080]
    low_front = [root for root in front if root[2] <= 1.675]
    report["objects"][name] = {
        "layer": obj.get("aevrynd_layer", ""),
        "curveCount": len(roots),
        "bounds": {
            "x": [min(v[0] for v in roots), max(v[0] for v in roots)],
            "y": [min(v[1] for v in roots), max(v[1] for v in roots)],
            "z": [min(v[2] for v in roots), max(v[2] for v in roots)],
        },
        "frontCount": len(front),
        "lowFrontCount": len(low_front),
        "frontXBins24": bin_counts(front, 0, -0.12, 0.12, 24),
        "frontZBins24": bin_counts(front, 2, 1.54, 1.78, 24),
        "lowFrontXBins24": bin_counts(low_front, 0, -0.12, 0.12, 24),
    }

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R94_ROOT_COVERAGE=" + json.dumps(report, sort_keys=True))
