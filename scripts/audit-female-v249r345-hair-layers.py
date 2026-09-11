import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-canthus-fitted-wedge-r345.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-canthus-fitted-wedge-r345.hair-layer-audit.json"
EXPECTED = {
    "AevryndFemaleScalpUnderlayer_R280": ("MESH", "hair.scalp_underlayer.head_bound", True),
    "AevryndFemalePrimaryClumps_R264": ("CURVES", "hair.primary_clumps", True),
    "AevryndFemaleSecondaryFill_R264": ("CURVES", "hair.secondary_fill", True),
    "AevryndFemaleFlyaways_R264": ("CURVES", "hair.flyaways", True),
    "AevryndFemaleHairlineTransitionCards_R285": ("MESH", "hair.hairline_transition.head_bound", True),
    "AevryndFemaleRuntimeHairCards_R276": ("MESH", "hair.runtime_cards.dynamic.alpha.wide_clumps", False),
}


bpy.ops.wm.open_mainfile(filepath=str(MODEL))
failures = []
layers = {}
for name, (expected_type, expected_layer, render_visible) in EXPECTED.items():
    obj = bpy.data.objects.get(name)
    if obj is None:
        failures.append({"missing": name})
        continue
    actual_layer = str(obj.get("aevrynd_layer", ""))
    visible = not obj.hide_render
    modifiers = [{"name": modifier.name, "type": modifier.type} for modifier in obj.modifiers]
    entry = {
        "type": obj.type, "layer": actual_layer, "renderVisible": visible,
        "viewportVisible": not obj.hide_viewport, "modifiers": modifiers,
        "materials": [slot.material.name if slot.material else None for slot in obj.material_slots],
    }
    if obj.type == "CURVES":
        entry.update({"curves": len(obj.data.curves), "points": len(obj.data.points)})
        if visible and not any(modifier.type == "NODES" and "Motion" in modifier.name for modifier in obj.modifiers):
            failures.append({"missingMotionModifier": name})
    elif obj.type == "MESH":
        entry.update({"vertices": len(obj.data.vertices), "polygons": len(obj.data.polygons)})
    layers[name] = entry
    if obj.type != expected_type:
        failures.append({"object": name, "type": obj.type, "expected": expected_type})
    if actual_layer != expected_layer:
        failures.append({"object": name, "layer": actual_layer, "expected": expected_layer})
    if visible != render_visible:
        failures.append({"object": name, "renderVisible": visible, "expected": render_visible})

material = bpy.data.materials.get("Aevrynd_PrincipledHair_CC0_R264")
hair_node = next((node for node in material.node_tree.nodes if node.type == "BSDF_HAIR_PRINCIPLED"), None) if material and material.use_nodes else None
material_info = {
    "name": material.name if material else None,
    "owned": bool(material and material.get("aevrynd_ownership") == "procedural in-project"),
    "principledHair": hair_node is not None,
    "revision": str(material.get("aevrynd_revision", "")) if material else None,
}
if not material_info["owned"] or not material_info["principledHair"]:
    failures.append({"material": material_info})

report = {
    "model": str(MODEL), "layers": layers, "material": material_info,
    "visibleAuthoredPointCount": sum(value.get("points", 0) for key, value in layers.items() if value["renderVisible"]),
    "runtimeProxySeparate": bool(layers.get("AevryndFemaleRuntimeHairCards_R276", {}).get("renderVisible") is False),
    "failures": failures, "status": "PASS" if not failures else "FAIL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R345_HAIR_LAYER_AUDIT=" + json.dumps(report, sort_keys=True))
if failures:
    raise SystemExit(2)
