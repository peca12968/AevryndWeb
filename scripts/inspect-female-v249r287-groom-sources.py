import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-matte-root-underlayer-r287.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-r287-groom-sources.json"


bpy.ops.wm.open_mainfile(filepath=str(MODEL))
items = []
for obj in bpy.data.objects:
    name_lower = obj.name.lower()
    layer = str(obj.get("aevrynd_layer", ""))
    if any(token in name_lower or token in layer.lower() for token in ("hair", "groom", "clump", "flyaway", "scalp")):
        entry = {
            "name": obj.name, "type": obj.type, "layer": layer,
            "revision": str(obj.get("aevrynd_revision", "")),
            "hideRender": obj.hide_render, "hideViewport": obj.hide_viewport,
            "parent": obj.parent.name if obj.parent else None,
            "modifiers": [{"name": modifier.name, "type": modifier.type} for modifier in obj.modifiers],
            "materials": [slot.material.name if slot.material else None for slot in obj.material_slots],
        }
        if obj.type == "MESH":
            entry.update({"vertices": len(obj.data.vertices), "edges": len(obj.data.edges), "polygons": len(obj.data.polygons)})
        elif obj.type == "CURVE":
            entry.update({"splines": len(obj.data.splines), "bevelDepth": obj.data.bevel_depth, "bevelResolution": obj.data.bevel_resolution,
                          "points": sum(len(spline.points) + len(spline.bezier_points) for spline in obj.data.splines)})
        elif obj.type == "CURVES":
            entry.update({"curves": len(obj.data.curves), "points": len(obj.data.points)})
        items.append(entry)
REPORT.write_text(json.dumps({"model": str(MODEL), "objects": items}, indent=2), encoding="utf-8")
print("AEVRYND_V249R287_GROOM_SOURCES=" + json.dumps({"count": len(items), "objects": items}, sort_keys=True))
