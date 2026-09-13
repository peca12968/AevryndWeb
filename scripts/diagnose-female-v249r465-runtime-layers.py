from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-runtime-collision-envelope-cards-r465.blend"
OUTPUT = ROOT.parent / "Temp/female-realism/v249r465-runtime-layer-diagnostic"
LAYERS = {
    "front": "AevryndFemaleRuntimeCards_front_R465",
    "crown": "AevryndFemaleRuntimeCards_crown_R465",
    "rear": "AevryndFemaleRuntimeCards_rear_R465",
    "hairline": "AevryndFemaleRuntimeCards_hairline_R465",
    "scalp": "AevryndFemaleRuntimeScalpCap_R465",
    "hairline_density": "AevryndFemaleRuntimeHairlineDensity_R465",
    "part_density": "AevryndFemaleRuntimePartRootDensity_R465",
}


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.wm.open_mainfile(filepath=str(MODEL))
scene = bpy.context.scene
scene.frame_set(1)
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
camera.location = (0.0, 0.90, 1.59)
camera.data.lens = 82
look_at(camera, (0.0, 0.0, 1.56))
OUTPUT.mkdir(parents=True, exist_ok=True)
states = {
    "01-all": set(LAYERS),
    "02-no-rear": set(LAYERS) - {"rear"},
    "03-rear-only": {"rear"},
    "04-no-part-density": set(LAYERS) - {"part_density"},
    "05-front-crown-rear": {"front", "crown", "rear"},
}
for label, visible in states.items():
    for key, name in LAYERS.items():
        bpy.data.objects[name].hide_render = key not in visible
    scene.render.filepath = str(OUTPUT / f"{label}.png")
    bpy.ops.render.render(write_still=True)

camera.location = (0.0, -0.57, 1.76)
camera.data.lens = 92
look_at(camera, (0.0, -0.02, 1.64))
front_states = {
    "11-hairline-all": set(LAYERS),
    "12-hairline-scalp-density": {"scalp", "hairline_density", "part_density"},
    "13-hairline-front-crown": {"front", "crown"},
    "14-hairline-cards-only": {"front", "crown", "rear", "hairline"},
    "15-hairline-no-density-ribbon": set(LAYERS) - {"hairline_density"},
}
for label, visible in front_states.items():
    for key, name in LAYERS.items():
        bpy.data.objects[name].hide_render = key not in visible
    scene.render.filepath = str(OUTPUT / f"{label}.png")
    bpy.ops.render.render(write_still=True)

print(f"AEVRYND_R465_LAYER_DIAGNOSTIC={OUTPUT}")
