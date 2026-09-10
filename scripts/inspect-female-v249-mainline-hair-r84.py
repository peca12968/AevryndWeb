import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-eye-aperture-r83.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-hair-r84.json"


def bounds(points):
    if not points:
        return None
    return {
        "min": [min(point[axis] for point in points) for axis in range(3)],
        "max": [max(point[axis] for point in points) for axis in range(3)],
    }


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
objects = []
for obj in bpy.data.objects:
    layer = str(obj.get("aevrynd_layer", ""))
    lower = obj.name.lower()
    if not (layer.startswith("hair.") or any(token in lower for token in ("hair", "groom", "scalp"))):
        continue
    entry = {
        "name": obj.name,
        "type": obj.type,
        "layer": layer,
        "hide_render": obj.hide_render,
        "parent": obj.parent.name if obj.parent else None,
    }
    if obj.type == "CURVES":
        points = [point.position for point in obj.data.points]
        offsets = [value.value for value in obj.data.curve_offset_data]
        roots = [points[offset] for offset in offsets[:-1]]
        tips = [points[offsets[index + 1] - 1] for index, offset in enumerate(offsets[:-1])]
        entry.update({
            "curves": len(obj.data.curves),
            "points": len(points),
            "points_per_curve_min": min(offsets[index + 1] - offset for index, offset in enumerate(offsets[:-1])),
            "points_per_curve_max": max(offsets[index + 1] - offset for index, offset in enumerate(offsets[:-1])),
            "root_bounds": bounds(roots),
            "tip_bounds": bounds(tips),
            "attributes": sorted(attribute.name for attribute in obj.data.attributes),
        })
    elif obj.type == "MESH":
        entry.update({"vertices": len(obj.data.vertices), "polygons": len(obj.data.polygons)})
    objects.append(entry)
report = {"source": str(SOURCE), "objects": objects}
OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249_HAIR_R84=" + json.dumps({
    "objects": len(objects),
    "visible": [entry["name"] for entry in objects if not entry["hide_render"]],
    "curves": {entry["name"]: entry.get("curves") for entry in objects if entry["type"] == "CURVES"},
}, sort_keys=True))
