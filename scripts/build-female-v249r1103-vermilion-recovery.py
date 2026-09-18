"""Recover readable upper and lower vermilion lost during later skin-material revisions."""
from pathlib import Path
import json

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-lower-wetline-r1102-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-vermilion-recovery-r1103-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1103-vermilion-recovery.study.json"
OUT = ROOT.parent / "Temp" / "female-realism" / "v249r1103-vermilion-recovery"
BODY = "AevryndFemaleCC0PalpebralClosure_R1097"
OPEN_KEY = "Aevrynd_MouthOpenTest_R1030"
SMILE_KEY = "Aevrynd_SmileTest_R1030"
MASK_STRENGTH = 4.0
ROUGHNESS_DELTA = 0.35
TARGET = (0.450, 0.150, 0.120, 1.0)


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def hide_hair(scene):
    for obj in scene.objects:
        name = obj.name.lower()
        if obj.type == "CURVES" or any(token in name for token in ("groom", "scalp", "haircard", "hairfiber")):
            if not any(token in name for token in ("brow", "lash")):
                obj.hide_render = True


def render(scene, label, location, target, lens, size):
    camera = scene.camera
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    path = OUT / f"{label}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return str(path)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
body = bpy.data.objects[BODY]
hide_hair(scene)

source_material = body.material_slots[0].material
material = source_material.copy()
material.name = "Aevrynd_CC0_RegionalSkin_R1103_VermilionRecovery"
body.data.materials[0] = material
nodes = material.node_tree.nodes
before = {
    "material": source_material.name,
    "maskStrength": nodes["Aevrynd Lip Mask Strength R1031"].inputs[1].default_value,
    "targetLinearRgba": list(nodes["混合 (舊版)"].inputs[2].default_value),
    "roughnessDelta": nodes["Aevrynd Lip Roughness Delta R1031"].inputs[1].default_value,
}
nodes["Aevrynd Lip Mask Strength R1031"].inputs[1].default_value = MASK_STRENGTH
nodes["混合 (舊版)"].inputs[2].default_value = TARGET
nodes["Aevrynd Lip Roughness Delta R1031"].inputs[1].default_value = ROUGHNESS_DELTA

OUT.mkdir(parents=True, exist_ok=True)
keys = body.data.shape_keys.key_blocks
keys[OPEN_KEY].value = 0.0
keys[SMILE_KEY].value = 0.0
renders = [
    render(scene, "neutral-mouth-front", (0.0, -0.43, 1.391), (0.0, -0.115, 1.386), 135, (1100, 720)),
    render(scene, "neutral-face-front", (0.0, -0.72, 1.445), (0.0, -0.025, 1.445), 88, (1000, 1000)),
]
keys[OPEN_KEY].value = 1.0
renders.append(render(scene, "open-mouth-front", (0.0, -0.43, 1.391), (0.0, -0.115, 1.386), 135, (1100, 720)))
keys[OPEN_KEY].value = 0.0
keys[SMILE_KEY].value = 1.0
renders.append(render(scene, "smile-mouth-front", (0.0, -0.43, 1.391), (0.0, -0.115, 1.386), 135, (1100, 720)))
keys[SMILE_KEY].value = 0.0

body["aevrynd_revision"] = "v249r1103-vermilion-recovery"
body["aevrynd_source"] = SOURCE.name
scene["aevrynd_release_state"] = "VISUAL_REVIEW_PENDING"
scene["aevrynd_website_promotion"] = "forbidden"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "revision": "v249r1103-vermilion-recovery",
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "method": "restore the inherited lips vertex-group response in the current regional skin shader without changing geometry, topology, rigging, or object layers",
    "before": before,
    "after": {"material": material.name, "maskStrength": MASK_STRENGTH, "targetLinearRgba": list(TARGET), "roughnessDelta": ROUGHNESS_DELTA},
    "geometryChanged": False,
    "topologyChanged": False,
    "collisionStateChanged": False,
    "materialSlotCountChanged": False,
    "renders": renders,
    "websitePromotionApproved": False,
    "candidateStatus": "VISUAL_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print("AEVRYND_R1103_VERMILION=" + json.dumps(report, sort_keys=True))

