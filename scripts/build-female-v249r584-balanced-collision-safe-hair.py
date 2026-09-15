import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-multiframe-envelope-tangent-cards-r582-study.blend"
OUTPUT = ASSETS / "aevrynd-female-authoring-v249-mainline-balanced-collision-safe-hair-r584.blend"
REPORT = ASSETS / "female-v249-mainline-balanced-collision-safe-hair-r584.build.json"
RENAMES = {
    "AevryndFemaleOwnedScalpGuideGroom_R582_Coverage": "AevryndFemaleOwnedScalpGuideGroom_R584_Coverage",
    "AevryndFemaleTangentOuterHairCards_R582": "AevryndFemaleTangentOuterHairCards_R584",
}


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
for old, new in RENAMES.items():
    obj = bpy.data.objects[old]
    obj.name = new
    obj.data.name = obj.data.name.replace("R582", "R584")
    obj["aevrynd_revision"] = "v249r584"

coverage = bpy.data.objects["AevryndFemaleOwnedScalpGuideGroom_R584_Coverage"]
coverage_material = coverage.data.materials[0]
coverage_material.name = "Aevrynd_OwnedScalpGuideHair_R584"
hair_node = next(node for node in coverage_material.node_tree.nodes if node.type == "BSDF_HAIR_PRINCIPLED")
hair_node.parametrization = "COLOR"
hair_node.inputs["Color"].default_value = (0.0385, 0.0132, 0.0055, 1.0)
coverage_material["aevrynd_revision"] = "v249r584"

cards = bpy.data.objects["AevryndFemaleTangentOuterHairCards_R584"]
card_material = cards.data.materials[0]
card_material.name = "Aevrynd_TangentOuterHairCards_R584"
card_material["aevrynd_revision"] = "v249r584"

scene = bpy.context.scene
scene["aevrynd_revision"] = "v249r584"
scene["aevrynd_status"] = "OFFLINE_TECHNICAL_CANDIDATE_PENDING_FINAL_GATES"
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "coverageLinearRGBA": [0.0385, 0.0132, 0.0055, 1.0],
    "coverageCurves": len(coverage.data.curves),
    "coveragePoints": len(coverage.data.points),
    "outerCards": cards.get("aevrynd_card_count"),
    "outerVertices": len(cards.data.vertices),
    "outerPolygons": len(cards.data.polygons),
    "ownership": "Aevrynd procedural geometry and atlas; no external runtime dependency",
    "status": "BUILT_PENDING_COLLISION_AND_11SHOT",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R584_BUILD=" + json.dumps(report, sort_keys=True))
