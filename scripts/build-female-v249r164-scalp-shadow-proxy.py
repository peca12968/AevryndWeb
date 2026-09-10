import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-deform-matched-scalp-r163.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-scalp-shadow-proxy-r164.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-scalp-shadow-proxy-r164.build-report.json"
HAIR = "AevryndFemaleOwnedCurlyHairMain_v249r162"
SCALP = "AevryndFemaleDeformMatchedScalp_v249r163"


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
hair = bpy.data.objects[HAIR]
scalp = bpy.data.objects[SCALP]
hair.visible_shadow = False
hair["aevrynd_shadow_mode"] = "scalp proxy; strand shadow disabled to prevent opaque accumulation"
hair["aevrynd_revision"] = "v249r164"

density = scalp.data.attributes["aevrynd_root_density"]
boosted = 0
for vertex in scalp.data.vertices:
    original = density.data[vertex.index].value
    if vertex.co.y > 0.0:
        rear = min(1.0, max(0.0, (vertex.co.y + 0.005) / 0.075))
        target = 0.35 + 0.55 * rear
        if target > original:
            density.data[vertex.index].value = target
            boosted += 1

material = scalp.data.materials[0]
material.name = "AevryndDeformMatchedScalpShadowProxyMaterial_v249r164"
for node in material.node_tree.nodes:
    if node.bl_idname == "ShaderNodeBsdfPrincipled":
        node.inputs["Base Color"].default_value = (0.013, 0.0035, 0.0018, 1.0)
        node.inputs["Roughness"].default_value = 0.90
        node.inputs["Specular IOR Level"].default_value = 0.08
material["aevrynd_revision"] = "v249r164"
material["aevrynd_role"] = "scalp color and broad contact-shadow proxy"
scalp.visible_shadow = True
scalp["aevrynd_layer"] = "hair.scalp.shadow-proxy"
scalp["aevrynd_revision"] = "v249r164"
scalp["aevrynd_collision_status"] = "INHERITS_R163_PASS_REAUDIT_REQUIRED"
scene["aevrynd_revision"] = "v249r164"
scene["aevrynd_candidate_status"] = "COLLISION_REAUDIT_AND_VISUAL_REVIEW_PENDING"
scene["aevrynd_hair_layers"] = ["hair.scalp.shadow-proxy", "hair.follow.curly.main"]
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "source": str(SOURCE), "output": str(OUTPUT),
    "hair": HAIR, "hairVisibleShadow": hair.visible_shadow,
    "shadowProxy": SCALP, "shadowProxyVisibleShadow": scalp.visible_shadow,
    "rearDensityVerticesBoosted": boosted,
    "geometryChanged": False, "runtimeDependency": "none",
    "status": "COLLISION_REAUDIT_AND_VISUAL_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R164_BUILD=" + json.dumps(report, sort_keys=True))
