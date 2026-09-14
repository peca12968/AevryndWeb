import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-natural-lower-lashes-r498.blend"
OUTPUT = ASSETS / "aevrynd-female-authoring-v249-mainline-sorted-tear-film-r499.blend"
REPORT = ASSETS / "female-v249-mainline-sorted-tear-film-r499.build-report.json"
REVIEW_DIR = ASSETS / "reviews" / "v249r499-sorted-tear-film"


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
bpy.context.preferences.filepaths.save_version = 0
scene = bpy.context.scene
material = bpy.data.materials["Aevrynd_TearMeniscus_Clear_R109"]
before = material.surface_render_method
material.surface_render_method = "BLENDED"
material["aevrynd_revision"] = "v249r499-sorted-tear-film"
material["aevrynd_change"] = "surface render method only; physical socket values retained"
for side in ("L", "R"):
    bpy.data.objects[f"Eye_{side}_TearMeniscus"]["aevrynd_tear_film_revision"] = "v249r499-sorted"
scene["aevrynd_mainline_revision"] = "v249r499-sorted-tear-film"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "SORTED_TEAR_FILM_VISUAL_CANDIDATE_COLLISION_AUDIT_REQUIRED"
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
    (1, "02-tear-oblique-f01", (0.18, -0.34, 1.608), (0.033, -0.113, 1.606), 125, (1200, 900)),
    (1, "03-three-quarter-f01", (0.45, -0.66, 1.60), (0.0, -0.005, 1.56), 84, (1000, 1000)),
    (20, "04-eye-close-f20", (0.0, -0.49, 1.615), (0.0, -0.13, 1.610), 105, (1200, 700)),
):
    render(scene, camera, *values)
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
shader = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "selectedVariant": "b-sorted-same",
    "surfaceRenderMethodBefore": before,
    "surfaceRenderMethodAfter": material.surface_render_method,
    "retainedSockets": {
        "baseColor": list(shader.inputs["Base Color"].default_value),
        "roughness": float(shader.inputs["Roughness"].default_value),
        "specularIorLevel": float(shader.inputs["Specular IOR Level"].default_value),
        "transmissionWeight": float(shader.inputs["Transmission Weight"].default_value),
        "alpha": float(shader.inputs["Alpha"].default_value),
        "coatWeight": float(shader.inputs["Coat Weight"].default_value),
        "coatRoughness": float(shader.inputs["Coat Roughness"].default_value),
    },
    "geometryChangedFromR498": False,
    "materialNodeCountChange": 0,
    "reviewDirectory": str(REVIEW_DIR),
    "ownedAssetOnly": True,
    "status": "FORMAL_GATES_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R499_SORTED_TEAR=" + json.dumps(report, sort_keys=True))
