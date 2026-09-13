import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-explicit-eyelid-loops-r438-study.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-eyelid-surface-r439-study.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-eyelid-surface-r439.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r439-eyelid-surface-review"
BODY = "AevryndFemaleBody_CC0_R249"
PATCHES = {
    "L": "AevryndEye_L_ExplicitLidLoops_R438",
    "R": "AevryndEye_R_ExplicitLidLoops_R438",
}


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
body = bpy.data.objects[BODY]
skin = body.data.materials[0]
patches = {}
for side, name in PATCHES.items():
    patch = bpy.data.objects[name]
    for modifier in list(patch.modifiers):
        patch.modifiers.remove(modifier)
    patch.data.materials.clear()
    patch.data.materials.append(skin)
    for polygon in patch.data.polygons:
        polygon.use_smooth = True
    patch.name = f"AevryndEye_{side}_EyelidSurface_R439"
    patch.data.name = f"AevryndEye_{side}_EyelidSurface_R439Geometry"
    patch["aevrynd_layer"] = f"body.face.eye_{side.lower()}.eyelid_surface.study"
    patch["aevrynd_revision"] = "v249r439-study"
    patches[side] = patch

for obj in bpy.data.objects:
    name = obj.name.lower()
    if obj in patches.values() or obj == body:
        obj.hide_render = False
    elif any(token in name for token in ("eye", "caruncle", "tear", "brow", "lash")):
        obj.hide_render = False
    elif obj.type in {"MESH", "CURVES", "CURVE"}:
        obj.hide_render = True

scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
scene.camera = camera
views = (
    ("front", (0.0, -0.63, 1.607), (0.0, -0.035, 1.607), 105),
    ("three-quarter", (0.31, -0.57, 1.618), (0.0, -0.025, 1.605), 100),
    ("eyes-close", (0.0, -0.44, 1.607), (0.0, -0.045, 1.607), 118),
)
for name, location, target, lens in views:
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x = scene.render.resolution_y = 1200
    scene.render.filepath = str(RENDER_DIR / f"r439-{name}.png")
    bpy.ops.render.render(write_still=True)

scene["aevrynd_eyelid_surface_study"] = "v249r439"
scene["aevrynd_release_state"] = "REJECTED_RECTANGULAR_CANTHUS_AND_OUTER_SEAM"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "renderDirectory": str(RENDER_DIR),
    "method": "Render the r438 four-ring eyelid topology with the inherited physical skin material and no wireframe modifier.",
    "topologyUnchangedFromR438": True,
    "frame1EyeCollisionInheritedFromR438": "PASS_ZERO_SCLERA_AND_CORNEA_TRIANGLE_OVERLAPS",
    "integratedIntoHeadCage": False,
    "rigTransferred": False,
    "websitePromotionApproved": False,
    "colorManagement": {"viewTransform": "Standard", "look": "None", "exposureEV": 0.0},
    "status": "REJECTED_RECTANGULAR_CANTHUS_AND_OUTER_SEAM",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R439_EYELID_SURFACE=" + json.dumps(report, sort_keys=True))
