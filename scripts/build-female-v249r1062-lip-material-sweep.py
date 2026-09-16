"""Tune the existing owned lip mask to reduce the r1061 chalk-white rim."""

import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-structured-lips-r1061-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-balanced-vermilion-r1062-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1062-lip-material.study.json"
OUT = ROOT.parent / "Temp/female-realism/v249r1062-lip-material"
BODY = "AevryndFemaleCC0StructuredLips_R1061"
OPEN_KEY = "Aevrynd_MouthOpenTest_R1030"
SMILE_KEY = "Aevrynd_SmileTest_R1030"
VARIANTS = (
    ("a-r1061-control", 0.78, 0.14, (0.245, 0.075, 0.065, 1.0)),
    ("b-natural", 1.20, 0.38, (0.300, 0.088, 0.072, 1.0)),
    ("c-balanced", 1.55, 0.55, (0.275, 0.074, 0.061, 1.0)),
    ("d-strong", 1.90, 0.70, (0.250, 0.062, 0.052, 1.0)),
    ("e-defined", 3.00, 0.82, (0.300, 0.088, 0.072, 1.0)),
    ("f-full-mask", 4.00, 0.92, (0.315, 0.095, 0.078, 1.0)),
)
SELECTED = "e-defined"


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def hide_hair(scene):
    for obj in scene.objects:
        name = obj.name.lower()
        if obj.type == "CURVES" or any(token in name for token in ("groom", "scalp", "haircard", "hairfiber")):
            if not any(token in name for token in ("brow", "lash")):
                obj.hide_render = True


def render(scene, label):
    camera = scene.camera
    camera.data.lens = 135
    camera.location = (0.0, -0.43, 1.391)
    look_at(camera, (0.0, -0.115, 1.386))
    scene.render.resolution_x = 1100
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    path = OUT / f"{label}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return str(path)


OUT.mkdir(parents=True, exist_ok=True)
results = []
for label, mask_strength, roughness_delta, color in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    body = bpy.data.objects[BODY]
    body.name = "AevryndFemaleCC0BalancedVermilion_R1062"
    hide_hair(scene)
    material = body.material_slots[0].material.copy()
    material.name = f"Aevrynd_CC0_OwnedSkin_R1062_{label}"
    body.data.materials[0] = material
    nodes = material.node_tree.nodes
    nodes["Aevrynd Lip Mask Strength R1031"].inputs[1].default_value = mask_strength
    nodes["Aevrynd Lip Roughness Delta R1031"].inputs[1].default_value = roughness_delta
    nodes["混合 (舊版)"].inputs[2].default_value = color

    keys = body.data.shape_keys.key_blocks
    keys[OPEN_KEY].value = 0.0
    keys[SMILE_KEY].value = 0.0
    rendered = [render(scene, f"{label}-neutral")]
    keys[OPEN_KEY].value = 1.0
    rendered.append(render(scene, f"{label}-open"))
    keys[OPEN_KEY].value = 0.0
    keys[SMILE_KEY].value = 1.0
    rendered.append(render(scene, f"{label}-smile"))
    keys[SMILE_KEY].value = 0.0

    result = {
        "label": label,
        "lipMaskStrength": mask_strength,
        "lipRoughnessDelta": roughness_delta,
        "lipTargetColorLinearRGBA": list(color),
        "renders": rendered,
    }
    results.append(result)
    if label == SELECTED:
        body["aevrynd_revision"] = "v249r1062-balanced-vermilion"
        body["aevrynd_source"] = SOURCE.name
        body["aevrynd_lip_mask_strength"] = mask_strength
        body["aevrynd_lip_roughness_delta"] = roughness_delta
        scene["aevrynd_release_state"] = "VISUAL_AND_COLLISION_REVIEW_PENDING"
        scene["aevrynd_website_promotion"] = "forbidden"
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "revision": "v249r1062-lip-material",
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "method": "reuse the owned lips vertex group through the existing skin shader; sweep mask strength, target vermilion color and lip roughness without new texture or draw call",
    "variants": results,
    "selectedVariant": SELECTED,
    "topologyChanged": False,
    "materialSlotCountChanged": False,
    "websitePromotionApproved": False,
    "candidateStatus": "VISUAL_AND_COLLISION_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1062_LIP_MATERIAL=" + json.dumps({
    "output": str(OUTPUT), "selected": SELECTED,
    "variants": [{"label": item["label"], "mask": item["lipMaskStrength"], "roughness": item["lipRoughnessDelta"]} for item in results],
}, sort_keys=True))
