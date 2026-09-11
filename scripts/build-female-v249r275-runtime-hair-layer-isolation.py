import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-layered-wide-hair-cards-r274.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-runtime-hair-layer-isolation-r275.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-runtime-hair-layer-isolation-r275.build-report.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r275-runtime-hair-layer-isolation"


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
visibility = {}
for name, visible in {
    "AevryndFemalePrimaryClumps_R264": False,
    "AevryndFemaleSecondaryFill_R264": False,
    "AevryndFemaleFlyaways_R264": True,
    "AevryndFemaleRuntimeHairCards_R271": False,
    "AevryndFemaleRuntimeHairCards_R274": True,
}.items():
    obj = bpy.data.objects[name]
    obj.hide_render = not visible
    obj.hide_viewport = not visible
    visibility[name] = visible
scene["aevrynd_mainline_revision"] = "v249r275-runtime-hair-layer-isolation"
scene["aevrynd_hair_layers"] = "runtime.wide_alpha_cards.dynamic|flyaways; authoring layers hidden"
scene["aevrynd_release_state"] = "RUNTIME_LAYER_ISOLATION_VISUAL_AND_DYNAMIC_REAUDIT_PENDING"
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
    "source": str(SOURCE), "output": str(OUTPUT), "layerVisibility": visibility,
    "runtimeCardObject": "AevryndFemaleRuntimeHairCards_R274",
    "runtimeCards": 192, "vertices": 9216, "faces": 4416,
    "authoringSecondaryFillPointsHidden": 242112, "flyawayPointsVisible": 1704,
    "renderDirectory": str(RENDER_DIR), "status": "VISUAL_AND_DYNAMIC_REAUDIT_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R275_RUNTIME_HAIR_LAYER_ISOLATION=" + json.dumps(report, sort_keys=True))
