import json
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-orbital-brow-refit-r526.blend"
OUT = ASSETS / "reviews/v249r564-complete-eye-layer-isolation"
REPORT = ASSETS / "female-v249-mainline-complete-eye-layer-isolation-r564.study.json"
VARIANTS = (
    ("a-all-eye-layers", ()),
    ("b-no-upper-or-lower-lashes", ("UpperLashes", "LowerLashes")),
    ("c-no-lashes-tear-caruncle", ("UpperLashes", "LowerLashes", "TearMeniscus", "Caruncle")),
    ("d-body-and-optics-only", ("UpperLashes", "LowerLashes", "TearMeniscus", "Caruncle", "Catchlight")),
)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
scene.view_settings.gamma = 1.0
scene.render.image_settings.file_format = "PNG"
scene.render.resolution_x = 1300
scene.render.resolution_y = 700
scene.render.resolution_percentage = 100
OUT.mkdir(parents=True, exist_ok=True)
for obj in bpy.data.objects:
    name = obj.name.lower()
    layer = str(obj.get("aevrynd_layer", "")).lower()
    if "hair" in name or layer.startswith("hair"):
        obj.hide_render = True
        obj.hide_viewport = True

eye_objects = sorted(obj.name for obj in bpy.data.objects if obj.name.startswith("Eye_"))
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
camera.location = (0.0, -0.48, 1.608)
camera.data.lens = 120
look_at(camera, (0.0, -0.055, 1.608))
visibility = {}
for label, hidden_suffixes in VARIANTS:
    hidden = []
    for name in eye_objects:
        obj = bpy.data.objects[name]
        hide = any(name.endswith(suffix) for suffix in hidden_suffixes)
        obj.hide_render = hide
        obj.hide_viewport = hide
        if hide:
            hidden.append(name)
    scene.render.filepath = str(OUT / f"{label}.png")
    bpy.ops.render.render(write_still=True)
    visibility[label] = hidden

report = {
    "source": str(SOURCE),
    "eyeObjects": eye_objects,
    "variantsHidden": visibility,
    "method": "fixed-camera layer isolation to identify the source of the triangular outer-canthus artifact",
    "status": "DIAGNOSTIC_ONLY",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R564_COMPLETE_EYE_LAYER_ISOLATION=" + json.dumps(report, sort_keys=True))
