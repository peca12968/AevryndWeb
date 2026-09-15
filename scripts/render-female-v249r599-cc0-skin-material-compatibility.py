import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-eye-composite-v260.blend"
MATERIAL_SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-lower-face-clearance-r569.blend"
MATERIAL_NAME = "Aevrynd_Skin_Breakup_R510_lighter-neutral"
BODY = "AevryndFemaleCC0Baseline_v259"
OUT = ASSETS / "reviews/v249r599-cc0-skin-material-compatibility"
REPORT = ASSETS / "female-v249-mainline-cc0-skin-material-r599.study.json"


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, camera, label, location, target):
    camera.location = location
    camera.data.lens = 105
    look_at(camera, target)
    scene.render.filepath = str(OUT / f"{label}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
scene.view_settings.gamma = 1.0
scene.render.image_settings.file_format = "PNG"
scene.render.resolution_x = scene.render.resolution_y = 1200
scene.render.resolution_percentage = 100
OUT.mkdir(parents=True, exist_ok=True)
body = bpy.data.objects[BODY]
camera = bpy.data.objects["Aevrynd Baseline Camera"]
scene.camera = camera

baseline_material = body.data.materials[0]
for view, location, target in (
    ("front", (0.0, -1.22, 1.55), (0.0, -0.01, 1.55)),
    ("three-quarter", (0.74, -1.0, 1.56), (0.0, 0.0, 1.55)),
):
    render(scene, camera, f"a-baseline-{view}", location, target)

with bpy.data.libraries.load(str(MATERIAL_SOURCE), link=False) as (data_from, data_to):
    data_to.materials = [MATERIAL_NAME]
transferred = data_to.materials[0]
body.data.materials[0] = transferred
for view, location, target in (
    ("front", (0.0, -1.22, 1.55), (0.0, -0.01, 1.55)),
    ("three-quarter", (0.74, -1.0, 1.56), (0.0, 0.0, 1.55)),
):
    render(scene, camera, f"b-r510-transfer-{view}", location, target)

report = {
    "source": str(SOURCE),
    "materialSource": str(MATERIAL_SOURCE),
    "material": MATERIAL_NAME,
    "bodyUvLayers": [layer.name for layer in body.data.uv_layers],
    "materialExpectedUvLayers": ["UVMap", "AevryndAtlasUV", "AevryndLipDetailUV"],
    "missingUvLayers": [name for name in ("AevryndAtlasUV", "AevryndLipDetailUV") if body.data.uv_layers.get(name) is None],
    "geometryChanged": False,
    "lightingChanged": False,
    "status": "VISUAL_COMPATIBILITY_PENDING_REVIEW",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R599_CC0_SKIN_MATERIAL=" + json.dumps(report, sort_keys=True))
