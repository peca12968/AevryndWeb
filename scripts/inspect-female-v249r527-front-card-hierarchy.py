import json
import math
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-orbital-brow-refit-r526.blend"
REPORT = ASSETS / "female-v249-mainline-front-card-hierarchy-r527.inspection.json"
OBJECT = "AevryndFemaleRuntimeLayeredLocks_front_R517"
POINTS = 24
STRIDE = POINTS * 2


def center(mesh, card, row):
    base = card * STRIDE + row * 2
    return (mesh.vertices[base].co + mesh.vertices[base + 1].co) * 0.5


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
obj = bpy.data.objects[OBJECT]
cards = int(obj.get("aevrynd_card_count", len(obj.data.vertices) // STRIDE))
items = []
for card in range(cards):
    centers = [center(obj.data, card, row) for row in range(POINTS)]
    root, middle, tail = centers[0], centers[POINTS // 2], centers[-1]
    length = sum((centers[index + 1] - centers[index]).length for index in range(POINTS - 1))
    azimuth = math.degrees(math.atan2(root.x, -(root.y + 0.012)))
    width = (obj.data.vertices[card * STRIDE + 1].co - obj.data.vertices[card * STRIDE].co).length
    items.append(
        {
            "card": card,
            "root": list(root),
            "middle": list(middle),
            "tail": list(tail),
            "rootAzimuthDegrees": azimuth,
            "lengthMm": length * 1000.0,
            "rootWidthMm": width * 1000.0,
        }
    )

lengths = [item["lengthMm"] for item in items]
widths = [item["rootWidthMm"] for item in items]
bins = {}
for start in range(-100, 100, 10):
    selected = [item for item in items if start <= item["rootAzimuthDegrees"] < start + 10]
    if selected:
        bins[f"{start}:{start + 10}"] = {
            "cards": len(selected),
            "meanLengthMm": sum(item["lengthMm"] for item in selected) / len(selected),
            "minimumRootZ": min(item["root"][2] for item in selected),
            "maximumRootZ": max(item["root"][2] for item in selected),
        }
report = {
    "source": str(SOURCE),
    "object": OBJECT,
    "cards": cards,
    "pointsPerCard": POINTS,
    "lengthMm": {"minimum": min(lengths), "median": sorted(lengths)[len(lengths) // 2], "maximum": max(lengths)},
    "rootWidthMm": {"minimum": min(widths), "median": sorted(widths)[len(widths) // 2], "maximum": max(widths)},
    "azimuthBins": bins,
    "cardData": items,
    "status": "MEASURED",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R527_FRONT_CARD_INSPECTION=" + json.dumps({key: value for key, value in report.items() if key != "cardData"}, sort_keys=True))
