from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249.blend"
OUT = ROOT.parent / "Temp/female-realism/hair-ablation-v249"
LAYERS = {
    "coverage": "HairCoverageTiles_v246",
    "silhouette": "HairSilhouetteCards_v246",
    "fibers": "HairDetailFibers_v246",
    "scalp": "HairScalp",
    "hairline": "HairlineNaturalCards_v214",
}


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, location, target, lens, resolution=900):
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(OUT / f"{name}.png")
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
OUT.mkdir(parents=True, exist_ok=True)
objects = {key: bpy.data.objects[name] for key, name in LAYERS.items()}
camera = bpy.data.objects["Aevrynd Review Camera"]
states = {"all": None, **{f"no-{key}": key for key in objects}}
for label, hidden in states.items():
    for key, obj in objects.items():
        obj.hide_render = key == hidden
    render(camera, f"{label}-top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78)
    render(camera, f"{label}-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88)
    render(camera, f"{label}-three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88)
print("AEVRYND_HAIR_ABLATION_V249=", OUT)
