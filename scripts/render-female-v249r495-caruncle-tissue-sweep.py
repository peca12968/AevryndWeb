import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-clipped-optical-fronts-r493.blend"
REPORT = ASSETS / "female-v249-mainline-caruncle-tissue-r495.study.json"
RENDER_DIR = ASSETS / "reviews/v249r495-caruncle-tissue-sweep"
SHAPE = {"towardEyeScale": 3.50, "medialScale": 0.65, "verticalScale": 0.72}
VARIANTS = (
    ("a-current-pink", (0.180, 0.040, 0.032, 1.0), 0.48, 0.18, 0.045, 0.05),
    ("b-warm-mucosa", (0.120, 0.034, 0.027, 1.0), 0.56, 0.16, 0.025, 0.02),
    ("c-integrated-mucosa", (0.095, 0.028, 0.024, 1.0), 0.58, 0.15, 0.020, 0.015),
    ("d-skin-relative", (0.130, 0.046, 0.036, 1.0), 0.56, 0.16, 0.022, 0.02),
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
scene.frame_set(1)
for side in ("L", "R"):
    obj = bpy.data.objects[f"Eye_{side}_Caruncle"]
    points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    center = sum(points, Vector()) / len(points)
    inverse = obj.matrix_world.inverted()
    eye_sign = 1.0 if side == "L" else -1.0
    for vertex, source in zip(obj.data.vertices, points):
        point = source.copy()
        anatomical = (point.x - center.x) * eye_sign
        point.x = center.x + (point.x - center.x) * (SHAPE["towardEyeScale"] if anatomical >= 0.0 else SHAPE["medialScale"])
        point.z = center.z + (point.z - center.z) * SHAPE["verticalScale"]
        vertex.co = inverse @ point
    obj.data.update()

material = bpy.data.materials["Aevrynd_Caruncle_v37"]
shader = next(node for node in material.node_tree.nodes if node.bl_idname == "ShaderNodeBsdfPrincipled")
scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
scene.render.image_settings.file_format = "PNG"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
metrics = {}
for label, color, roughness, specular, subsurface, coat in VARIANTS:
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Specular IOR Level"].default_value = specular
    shader.inputs["Subsurface Weight"].default_value = subsurface
    shader.inputs["Coat Weight"].default_value = coat
    render(scene, camera, label + "-eye-close", (0.0, -0.49, 1.615), (0.0, -0.13, 1.610), 105, (1200, 700))
    render(scene, camera, label + "-three-quarter", (0.45, -0.66, 1.60), (0.0, -0.005, 1.56), 84, (1000, 1000))
    metrics[label] = {
        "baseColor": list(color),
        "roughness": roughness,
        "specularIorLevel": specular,
        "subsurfaceWeight": subsurface,
        "coatWeight": coat,
    }

report = {
    "source": str(SOURCE),
    "fixedShape": SHAPE,
    "variants": metrics,
    "renderDirectory": str(RENDER_DIR),
    "status": "VISUAL_REVIEW_REQUIRED",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R495_CARUNCLE_TISSUE=" + json.dumps(report, sort_keys=True))
