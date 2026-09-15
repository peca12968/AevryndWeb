import json
import os
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = Path(os.environ.get("AEVRYND_CALIBRATED_SOURCE", ASSETS / "aevrynd-female-cc0-retargeted-rig-r603.blend"))
REVISION = os.environ.get("AEVRYND_CALIBRATED_REVISION", "v249r603-retargeted-rig")
OUT = ASSETS / "reviews" / REVISION
REPORT = ASSETS / f"female-{REVISION}.calibrated-review.json"


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def area(name, location, energy, size, color):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    data.color = color
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    look_at(obj, (0.0, 0.0, 0.95))
    return obj


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
for obj in list(bpy.data.objects):
    if obj.type == "LIGHT":
        bpy.data.objects.remove(obj, do_unlink=True)
world = scene.world or bpy.data.worlds.new("Aevrynd Calibrated Review World")
scene.world = world
world.use_nodes = True
background = world.node_tree.nodes.get("Background")
background.inputs["Color"].default_value = (0.025, 0.030, 0.038, 1.0)
background.inputs["Strength"].default_value = 0.28
lights = [
    area("Aevrynd Cal Key", (2.8, -3.8, 4.2), 470.0, 3.4, (1.0, 0.92, 0.84)),
    area("Aevrynd Cal Fill", (-3.0, -2.0, 2.8), 270.0, 3.2, (0.78, 0.88, 1.0)),
    area("Aevrynd Cal Rim", (2.0, 2.8, 3.6), 380.0, 2.6, (0.88, 0.94, 1.0)),
]
scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
scene.view_settings.gamma = 1.0
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False
camera = bpy.data.objects.get("Aevrynd Baseline Camera")
if camera is None:
    data = bpy.data.cameras.new("Aevrynd Calibrated Review Camera")
    camera = bpy.data.objects.new("Aevrynd Calibrated Review Camera", data)
    scene.collection.objects.link(camera)
scene.camera = camera
OUT.mkdir(parents=True, exist_ok=True)
views = (
    (1, "01-neutral-full-front", (0.0, -4.5, 0.82), (0.0, -0.04, 0.82), 76, (800, 1050)),
    (1, "02-neutral-three-quarter", (2.65, -3.55, 0.90), (0.0, -0.02, 0.84), 76, (800, 1050)),
    (1, "03-neutral-face-front", (0.0, -1.18, 1.48), (0.0, -0.035, 1.48), 105, (1000, 1000)),
    (20, "04-pose-full-front", (0.0, -4.5, 0.82), (0.0, -0.04, 0.82), 76, (800, 1050)),
    (20, "05-pose-three-quarter", (2.65, -3.55, 0.90), (0.0, -0.02, 0.84), 76, (800, 1050)),
    (20, "06-pose-face-front", (0.0, -1.18, 1.48), (0.0, -0.035, 1.48), 105, (1000, 1000)),
)
outputs = []
for frame, name, location, target, lens, size in views:
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)
    outputs.append(scene.render.filepath)
report = {
    "source": str(SOURCE),
    "output": str(OUT),
    "colorManagement": {"viewTransform": "Standard", "look": "None", "exposure": 0.0, "gamma": 1.0},
    "world": {"color": [0.025, 0.030, 0.038], "strength": 0.28},
    "lights": [{"name": obj.name, "energy": obj.data.energy, "size": obj.data.size} for obj in lights],
    "images": outputs,
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_CALIBRATED_REVIEW=" + json.dumps(report, sort_keys=True))
