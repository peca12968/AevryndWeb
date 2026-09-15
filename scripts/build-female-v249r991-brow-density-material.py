"""Give r990 brows a readable warm-brown density foundation under visible fibres."""

import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-visible-face-features-r990.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-brow-density-material-r991.blend"
REPORT = ASSETS / "female-v249-mainline-cc0-brow-density-material-r991.build-report.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r991-brow-density-material"


def tune_principled(mat, color, alpha, roughness):
    bsdf = next(node for node in mat.node_tree.nodes if node.bl_idname == "ShaderNodeBsdfPrincipled")
    removed = []
    for input_name in ("Base Color", "Alpha"):
        for link in list(bsdf.inputs[input_name].links):
            removed.append(f"{link.from_node.name}.{link.from_socket.name}->{input_name}")
            mat.node_tree.links.remove(link)
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Alpha"].default_value = alpha
    bsdf.inputs["Roughness"].default_value = roughness
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.18
    if hasattr(mat, "surface_render_method"):
        mat.surface_render_method = "DITHERED"
    return removed


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, camera, name, location, target, lens):
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
changes = {
    "Aevrynd_Brow_Density_v39": tune_principled(
        bpy.data.materials["Aevrynd_Brow_Density_v39"], (0.028, 0.0065, 0.0025), 0.42, 0.74),
    "Aevrynd_Brow_Hair_v39_Dark": tune_principled(
        bpy.data.materials["Aevrynd_Brow_Hair_v39_Dark"], (0.010, 0.0018, 0.0007), 1.0, 0.62),
    "Aevrynd_Brow_Hair_v39_Warm": tune_principled(
        bpy.data.materials["Aevrynd_Brow_Hair_v39_Warm"], (0.036, 0.007, 0.002), 1.0, 0.64),
    "Aevrynd_Lash_Hair_v51": tune_principled(
        bpy.data.materials["Aevrynd_Lash_Hair_v51"], (0.003, 0.0005, 0.0002), 1.0, 0.58),
}
scene["aevrynd_mainline_revision"] = "v249r991-brow-density-material"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "STATIC_FACE_FEATURE_PASS_VISUAL_REVIEW_PENDING"
scene["aevrynd_website_promotion"] = "forbidden pending dynamic and runtime gates"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
scene.render.resolution_x = scene.render.resolution_y = 900
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects.get("Aevrynd Review Camera") or scene.camera
scene.camera = camera
for args in (
    ("01-face-front", (0.0, -0.68, 1.49), (0.0, -0.055, 1.48), 88),
    ("02-face-three-quarter", (0.42, -0.58, 1.51), (0.0, -0.045, 1.48), 88),
    ("03-face-profile", (0.68, -0.02, 1.50), (0.0, -0.035, 1.48), 90),
    ("04-eye-front", (0.0, -0.48, 1.485), (0.0, -0.060, 1.485), 105),
    ("05-eye-three-quarter", (0.30, -0.40, 1.49), (0.0, -0.055, 1.485), 105),
    ("06-full-three-quarter", (1.10, -1.62, 1.22), (0.0, -0.01, 0.92), 58),
):
    render(scene, camera, *args)
report = {"source": str(SOURCE), "output": str(OUTPUT), "removedIncomingLinks": changes,
          "geometryChanged": False, "r990StaticClearanceRetained": True,
          "websitePromotionApproved": False, "status": "STRICT_VISUAL_REVIEW_REQUIRED"}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_R991_BROW_DENSITY_MATERIAL=" + json.dumps(report, sort_keys=True))
