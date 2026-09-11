import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-matte-root-underlayer-r287.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-r287-card-layout.json"
CARDS = "AevryndFemaleRuntimeHairCards_R276"
POINTS = 24
STRIDE = POINTS * 2


bpy.ops.wm.open_mainfile(filepath=str(MODEL))
obj = bpy.data.objects[CARDS]
items = []
for card_index in range(len(obj.data.vertices) // STRIDE):
    centers = []
    widths = []
    for point_index in range(POINTS):
        left = obj.data.vertices[card_index * STRIDE + point_index * 2].co
        right = obj.data.vertices[card_index * STRIDE + point_index * 2 + 1].co
        centers.append((left + right) * 0.5)
        widths.append((right - left).length * 0.5)
    root = centers[0]
    middle = centers[12]
    tip = centers[-1]
    items.append({
        "card": card_index,
        "root": list(root), "middle": list(middle), "tip": list(tip),
        "rootAzimuthDeg": math.degrees(math.atan2(root.x, -(root.y + 0.01))),
        "rootRadius": math.hypot(root.x, root.y + 0.01),
        "meanHalfWidth": sum(widths) / len(widths),
        "middleRadius": math.hypot(middle.x, middle.y + 0.01),
        "length": sum((centers[index] - centers[index - 1]).length for index in range(1, POINTS)),
    })


def extent(key, axis):
    values = [item[key][axis] for item in items]
    return [min(values), max(values)]


summary = {
    "model": str(MODEL), "cardObject": CARDS, "cardCount": len(items),
    "rootExtents": {"x": extent("root", 0), "y": extent("root", 1), "z": extent("root", 2)},
    "middleExtents": {"x": extent("middle", 0), "y": extent("middle", 1), "z": extent("middle", 2)},
    "tipExtents": {"x": extent("tip", 0), "y": extent("tip", 1), "z": extent("tip", 2)},
    "meanHalfWidthRange": [min(item["meanHalfWidth"] for item in items), max(item["meanHalfWidth"] for item in items)],
    "lengthRange": [min(item["length"] for item in items), max(item["length"] for item in items)],
    "backCentralCards": [item["card"] for item in items if item["root"][1] > 0.025 and abs(item["root"][0]) < 0.065],
    "leftOuterCards": [item["card"] for item in items if item["middle"][0] < -0.105],
    "rightOuterCards": [item["card"] for item in items if item["middle"][0] > 0.105],
    "cards": items,
}
REPORT.write_text(json.dumps(summary, indent=2), encoding="utf-8")
print("AEVRYND_V249R287_CARD_LAYOUT=" + json.dumps({key: value for key, value in summary.items() if key != "cards"}, sort_keys=True))
