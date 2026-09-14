import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-natural-lower-lashes-r498.blend"
REPORT = ASSETS / "female-v249-mainline-tear-film-r499.study.json"
RENDER_DIR = ASSETS / "reviews" / "v249r499-tear-film-sweep"
VARIANTS = (
    ("a-current-dither", {"method": "DITHERED", "base": (0.82, 0.91, 0.95, 1.0), "rough": 0.055, "spec": 0.42, "transmission": 0.28, "alpha": 0.24, "coat": 0.55, "coatRough": 0.035}),
    ("b-sorted-same", {"method": "BLENDED", "base": (0.82, 0.91, 0.95, 1.0), "rough": 0.055, "spec": 0.42, "transmission": 0.28, "alpha": 0.24, "coat": 0.55, "coatRough": 0.035}),
    ("c-thin-clear", {"method": "BLENDED", "base": (0.72, 0.82, 0.86, 1.0), "rough": 0.065, "spec": 0.35, "transmission": 0.35, "alpha": 0.14, "coat": 0.35, "coatRough": 0.045}),
    ("d-restrained-water", {"method": "BLENDED", "base": (0.58, 0.68, 0.72, 1.0), "rough": 0.075, "spec": 0.32, "transmission": 0.22, "alpha": 0.10, "coat": 0.28, "coatRough": 0.055}),
)


def apply(shader, material, values):
    material.surface_render_method = values["method"]
    shader.inputs["Base Color"].default_value = values["base"]
    shader.inputs["Roughness"].default_value = values["rough"]
    shader.inputs["Specular IOR Level"].default_value = values["spec"]
    shader.inputs["Transmission Weight"].default_value = values["transmission"]
    shader.inputs["Alpha"].default_value = values["alpha"]
    shader.inputs["Coat Weight"].default_value = values["coat"]
    shader.inputs["Coat Roughness"].default_value = values["coatRough"]


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
scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
scene.render.image_settings.file_format = "PNG"
material = bpy.data.materials["Aevrynd_TearMeniscus_Clear_R109"]
shader = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
RENDER_DIR.mkdir(parents=True, exist_ok=True)
for label, values in VARIANTS:
    apply(shader, material, values)
    render(scene, camera, label + "-eye-close", (0.0, -0.49, 1.615), (0.0, -0.13, 1.610), 105, (1200, 700))
    render(scene, camera, label + "-tear-oblique", (0.18, -0.34, 1.608), (0.033, -0.113, 1.606), 125, (1200, 900))
REPORT.write_text(json.dumps({
    "source": str(SOURCE),
    "variants": {label: values for label, values in VARIANTS},
    "geometryChanged": False,
    "renderDirectory": str(RENDER_DIR),
    "status": "VISUAL_REVIEW_REQUIRED",
}, indent=2), encoding="utf-8")
print("AEVRYND_R499_TEAR_SWEEP=complete")
