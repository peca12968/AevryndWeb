import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-layered-rear-locks-r506.blend"
OUTPUT = ASSETS / "aevrynd-female-authoring-v249-mainline-lighter-neutral-skin-r510.blend"
REPORT = ASSETS / "female-v249-mainline-lighter-neutral-skin-r510.build-report.json"
COLORS = ((0.145, 0.050, 0.032, 1.0), (0.188, 0.070, 0.042, 1.0))

bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
body = bpy.data.objects["AevryndFemaleBodyBaseV118"]
material = body.data.materials[0]
ramp = material.node_tree.nodes["Aevrynd restrained melanin range"].color_ramp
before = [list(element.color) for element in ramp.elements]
for element, color in zip(ramp.elements, COLORS):
    element.color = color
material.name = "Aevrynd_Skin_Breakup_R510_lighter-neutral"
material["aevrynd_revision"] = "v249r510-lighter-neutral-skin"
material["aevrynd_change_scope"] = "melanin ramp endpoints only"
material["aevrynd_reference_study"] = "r509 b-lighter-neutral"
scene["aevrynd_mainline_revision"] = "v249r510-lighter-neutral-skin"
scene["aevrynd_release_state"] = "OFFLINE_TECHNICAL_CANDIDATE_REQUIRES_FORMAL_GATES"
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
REPORT.write_text(json.dumps({
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "selectedStudy": "r509 b-lighter-neutral",
    "material": material.name,
    "rampBeforeLinearRGBA": before,
    "rampAfterLinearRGBA": [list(color) for color in COLORS],
    "geometryChanged": False,
    "rigChanged": False,
    "lightingChanged": False,
    "exposureChanged": False,
    "websitePromotionApproved": False,
    "status": "BUILD_COMPLETE_FORMAL_GATES_REQUIRED",
}, indent=2), encoding="utf-8")
print("AEVRYND_R510_LIGHTER_NEUTRAL_SKIN=" + str(OUTPUT))
