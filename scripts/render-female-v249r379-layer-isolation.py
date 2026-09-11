from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-grouped-end-silhouette-r379.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r379-layer-isolation"


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
camera.location = (0.0, -0.57, 1.76)
camera.data.lens = 92
look_at(camera, (0.0, -0.02, 1.64))
layers = {
    "primary": bpy.data.objects["AevryndFemaleSemanticPrimary_R379"],
    "fill": bpy.data.objects["AevryndFemaleSemanticFill_R379"],
    "transition": bpy.data.objects["AevryndFemaleHairlineTransition_R379"],
    "front": bpy.data.objects["AevryndFemaleFrontSurfaceFlow_R379"],
}
OUT.mkdir(parents=True, exist_ok=True)
variants = {
    "a-all": set(layers),
    "b-without-transition": {"primary", "fill", "front"},
    "c-front-only": {"front"},
    "d-without-front": {"primary", "fill", "transition"},
}
for label, visible in variants.items():
    for name, obj in layers.items():
        obj.hide_render = name not in visible
    scene.render.filepath = str(OUT / f"{label}.png")
    bpy.ops.render.render(write_still=True)
print(f"AEVRYND_R379_LAYER_ISOLATION={OUT}")
