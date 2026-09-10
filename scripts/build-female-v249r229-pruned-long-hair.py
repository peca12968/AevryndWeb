import json
import math
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-converged-upper-lid-r210.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-pruned-long-hair-r229.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-pruned-long-hair-r229.build-report.json"
MAIN = "AevryndFemaleCC0LongHairStudyMain_v249r85"
FLYAWAY = "AevryndFemaleCC0LongHairStudyFlyaway_v249r85"
KEEP_FRACTION = 0.55
RADIUS_SCALE = 1.22


def stable_fraction(index, root):
    value = math.sin(index * 12.9898 + root.x * 78.233 + root.y * 37.719 + root.z * 19.913) * 43758.5453
    return value - math.floor(value)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
bpy.context.scene.frame_set(1)
main = bpy.data.objects[MAIN]
data = main.data
before_curves = len(data.curves)
before_points = len(data.points)
source_index = data.attributes.get("aevrynd_source_curve_index")
if source_index:
    data.attributes.remove(source_index)
source_index = data.attributes.new(name="aevrynd_source_curve_index", type="INT", domain="CURVE")
source_index_name = source_index.name
for curve in data.curves:
    source_index.data[curve.index].value = curve.index
remove = []
for curve in data.curves:
    root = data.points[curve.first_point_index].position
    if stable_fraction(curve.index, root) > KEEP_FRACTION:
        remove.append(curve.index)
data.remove_curves(indices=remove)
source_index = data.attributes[source_index_name]
radius = data.attributes["radius"]
for item in radius.data:
    item.value *= RADIUS_SCALE
bpy.data.objects[FLYAWAY].hide_render = True
main["aevrynd_revision"] = "v249r229-pruned-long-hair"
main["aevrynd_parent_revision"] = "v249r210"
main["aevrynd_source_curve_index_attribute"] = source_index_name
main["aevrynd_keep_fraction"] = KEEP_FRACTION
main["aevrynd_radius_scale"] = RADIUS_SCALE
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "curvesBefore": before_curves,
    "pointsBefore": before_points,
    "curvesRemoved": len(remove),
    "curvesAfter": len(data.curves),
    "pointsAfter": len(data.points),
    "actualKeepFraction": len(data.curves) / before_curves,
    "radiusScale": RADIUS_SCALE,
    "sourceIndexAttribute": source_index_name,
    "sourceIndexMinimum": min(item.value for item in source_index.data),
    "sourceIndexMaximum": max(item.value for item in source_index.data),
    "flyawayRenderVisible": not bpy.data.objects[FLYAWAY].hide_render,
    "status": "COLLISION_AND_DYNAMIC_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R229_PRUNED_LONG_HAIR=" + json.dumps(report, sort_keys=True))
