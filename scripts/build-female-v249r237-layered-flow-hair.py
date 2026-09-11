import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-converged-upper-lid-r210.blend"
HAIR_SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-anisotropic-hair-v360.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-layered-flow-hair-r237.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-layered-flow-hair-r237.build-report.json"
HAIR_OBJECTS = (
    "AevryndFemaleHair_ShapedOverlay_v319_R",
    "AevryndFemaleHair_ShapedOverlay_v319_L",
    "AevryndFemaleHair_CrownRootVeil_v338_R",
    "AevryndFemaleHair_CrownRootVeil_v338_L",
    "AevryndFemaleHair_ContinuousFlow_v317_R",
    "AevryndFemaleHair_ContinuousFlow_v317_L",
)


def is_old_hair(obj):
    layer = str(obj.get("aevrynd_layer", "")).lower()
    name = obj.name.lower()
    return layer.startswith("hair.") or "longhairstudy" in name or "scalp" in name


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
removed = []
for obj in list(bpy.context.scene.objects):
    if is_old_hair(obj):
        removed.append(obj.name)
        bpy.data.objects.remove(obj, do_unlink=True)

with bpy.data.libraries.load(str(HAIR_SOURCE), link=False) as (source, target):
    missing = [name for name in HAIR_OBJECTS if name not in source.objects]
    if missing:
        raise RuntimeError(f"Missing layered hair objects: {missing}")
    target.objects = list(HAIR_OBJECTS)

collection = bpy.data.collections.new("AevryndFemaleHair_v249r237")
bpy.context.scene.collection.children.link(collection)
linked = []
for obj in target.objects:
    if obj is None:
        continue
    collection.objects.link(obj)
    obj.hide_render = False
    obj.hide_viewport = False
    obj["aevrynd_revision"] = "v249r237-layered-flow-hair"
    obj["aevrynd_mainline_hair_collision"] = True
    obj["aevrynd_source_asset"] = "Aevrynd-owned procedural layered flow hair v360"
    linked.append({
        "name": obj.name,
        "layer": obj.get("aevrynd_layer"),
        "curves": len(obj.data.curves),
        "points": len(obj.data.points),
        "modifiers": [modifier.name for modifier in obj.modifiers],
    })

scene = bpy.context.scene
scene["aevrynd_mainline_revision"] = "v249r237-layered-flow-hair"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_hair_source"] = HAIR_SOURCE.name
scene["aevrynd_asset_ownership"] = "Aevrynd-owned procedural geometry and materials"
scene["aevrynd_release_state"] = "STATIC_COLLISION_AND_DYNAMIC_BINDING_PENDING"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "source": str(SOURCE),
    "hairSource": str(HAIR_SOURCE),
    "output": str(OUTPUT),
    "ownership": "Aevrynd-owned procedural geometry and materials; no runtime third-party dependency",
    "removedLegacyObjects": sorted(removed),
    "layers": linked,
    "totals": {
        "objects": len(linked),
        "curves": sum(item["curves"] for item in linked),
        "points": sum(item["points"] for item in linked),
    },
    "status": "STATIC_COLLISION_AND_DYNAMIC_BINDING_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R237_LAYERED_FLOW_HAIR=" + json.dumps(report, sort_keys=True))
