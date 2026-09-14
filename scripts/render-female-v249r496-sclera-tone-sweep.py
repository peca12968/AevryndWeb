import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-integrated-caruncle-r495.blend"
REPORT = ASSETS / "female-v249-mainline-sclera-tone-r496.study.json"
RENDER_DIR = ASSETS / "reviews/v249r496-sclera-tone-sweep"
TEXTURES = ASSETS / "textures"
VARIANTS = (
    ("a-current-v61", TEXTURES / "aevrynd-sclera-basecolor-v61.png"),
    ("b-soft-warm", TEXTURES / "aevrynd-sclera-basecolor-v496-b-soft-warm.png"),
    ("c-natural-warm", TEXTURES / "aevrynd-sclera-basecolor-v496-c-natural-warm.png"),
    ("d-muted-warm", TEXTURES / "aevrynd-sclera-basecolor-v496-d-muted-warm.png"),
)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, camera, name, location, target, lens, size):
    scene.frame_set(1)
    bpy.context.view_layer.update()
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
material = bpy.data.materials["Aevrynd_Eye_Sclera"]
texture = material.node_tree.nodes["Aevrynd Sclera BaseColor"]
scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
scene.render.image_settings.file_format = "PNG"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
metrics = {}
for label, path in VARIANTS:
    image = bpy.data.images.load(str(path), check_existing=False)
    image.colorspace_settings.name = "sRGB"
    texture.image = image
    render(scene, camera, label + "-eye-close", (0.0, -0.49, 1.615), (0.0, -0.13, 1.610), 105, (1200, 700))
    render(scene, camera, label + "-three-quarter", (0.45, -0.66, 1.60), (0.0, -0.005, 1.56), 84, (1000, 1000))
    pixels = image.pixels[:]
    count = len(pixels) // 4
    means = [sum(pixels[channel::4]) / count for channel in range(3)]
    metrics[label] = {"path": str(path), "size": list(image.size), "meanLinearRgb": means}

report = {
    "source": str(SOURCE),
    "method": "Aevrynd-owned baked sclera base-color sweep; preserve v61 vessels while lowering encoded mean value and adding restrained warm edge falloff",
    "variants": metrics,
    "renderDirectory": str(RENDER_DIR),
    "status": "VISUAL_REVIEW_REQUIRED",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R496_SCLERA_TONE=" + json.dumps(report, sort_keys=True))
