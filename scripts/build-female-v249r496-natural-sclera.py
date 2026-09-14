import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-integrated-caruncle-r495.blend"
OUTPUT = ASSETS / "aevrynd-female-authoring-v249-mainline-natural-sclera-r496.blend"
TEXTURE_PATH = ASSETS / "textures/aevrynd-sclera-basecolor-v496-c-natural-warm.png"
REPORT = ASSETS / "female-v249-mainline-natural-sclera-r496.build-report.json"
REVIEW_DIR = ASSETS / "reviews/v249r496-natural-sclera"


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, camera, frame, name, location, target, lens, size):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(REVIEW_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
material = bpy.data.materials["Aevrynd_Eye_Sclera"]
node = material.node_tree.nodes["Aevrynd Sclera BaseColor"]
image = bpy.data.images.load(str(TEXTURE_PATH), check_existing=False)
image.name = "aevrynd-sclera-basecolor-v496-natural-warm"
image.filepath = "//textures/aevrynd-sclera-basecolor-v496-c-natural-warm.png"
image.colorspace_settings.name = "sRGB"
image.pack()
node.image = image
material["aevrynd_revision"] = "v249r496-natural-warm-sclera"
material["aevrynd_ownership"] = "Aevrynd deterministic baked texture"
for side in ("L", "R"):
    obj = bpy.data.objects[f"Eye_{side}_Sclera"]
    obj["aevrynd_sclera_texture_revision"] = "v496-natural-warm"

scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
scene.render.image_settings.file_format = "PNG"
REVIEW_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
for values in (
    (1, "01-eye-close-f01", (0.0, -0.49, 1.615), (0.0, -0.13, 1.610), 105, (1200, 700)),
    (1, "02-face-front-f01", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88, (1000, 1000)),
    (1, "03-three-quarter-f01", (0.45, -0.66, 1.60), (0.0, -0.005, 1.56), 84, (1000, 1000)),
    (20, "04-eye-close-f20", (0.0, -0.49, 1.615), (0.0, -0.13, 1.610), 105, (1200, 700)),
):
    render(scene, camera, *values)

scene.frame_set(1)
scene["aevrynd_mainline_revision"] = "v249r496-natural-sclera"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "NATURAL_SCLERA_VISUAL_CANDIDATE_COLLISION_AUDIT_REQUIRED"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "selectedTexture": str(TEXTURE_PATH),
    "textureSize": list(image.size),
    "selectionReason": "Natural-warm preserves readable sclera/iris separation without the luminous white of v61 or the gray-fatigued appearance of the muted bound",
    "runtimeMaterialNodeCountChange": 0,
    "geometryChangedFromR495": False,
    "reviewDirectory": str(REVIEW_DIR),
    "ownedAssetOnly": True,
    "status": "FORMAL_GATES_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R496_NATURAL_SCLERA=" + json.dumps(report, sort_keys=True))
