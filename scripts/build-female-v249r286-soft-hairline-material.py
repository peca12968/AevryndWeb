import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hairline-transition-cards-r285.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-soft-hairline-material-r286.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-soft-hairline-material-r286.build-report.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r286-soft-hairline-material"
HAIRLINE = "AevryndFemaleHairlineTransitionCards_R285"
MATERIAL = "Aevrynd_RuntimeHairCards_Alpha_R272"


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, frame, name, location):
    scene = bpy.context.scene
    scene.frame_set(frame)
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    camera.location = location
    camera.data.lens = 82
    look_at(camera, (0.0, 0.0, 1.56))
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
hairline = bpy.data.objects[HAIRLINE]
previous = [material.name for material in hairline.data.materials]
hairline.data.materials.clear()
hairline.data.materials.append(bpy.data.materials[MATERIAL])
hairline["aevrynd_revision"] = "v249r286"
hairline["aevrynd_material_role"] = "soft low-opacity hairline transition"
scene["aevrynd_mainline_revision"] = "v249r286-soft-hairline-material"
scene["aevrynd_release_state"] = "SOFT_HAIRLINE_VISUAL_REVIEW_PENDING"
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 800
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
for frame, name, location in (
    (1, "front-f01", (0.0, -0.90, 1.59)), (33, "front-f33", (0.0, -0.90, 1.59)),
    (1, "left-f01", (-0.72, -0.55, 1.59)), (1, "right-f01", (0.72, -0.55, 1.59)),
    (1, "back-f01", (0.0, 0.90, 1.59)), (33, "back-f33", (0.0, 0.90, 1.59)),
):
    render(camera, frame, name, location)
scene.frame_set(1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE), "output": str(OUTPUT), "hairlineObject": HAIRLINE,
    "previousMaterials": previous, "material": MATERIAL,
    "geometryChanged": False, "bindingChanged": False, "collisionContractChanged": False,
    "ownedAssetOnly": True, "renderDirectory": str(RENDER_DIR), "status": "VISUAL_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R286_SOFT_HAIRLINE_MATERIAL=" + json.dumps(report, sort_keys=True))
