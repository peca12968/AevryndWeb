import json
from pathlib import Path

import bpy
from mathutils import Matrix, Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-natural-sclera-r337.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-caruncle-tissue-r339.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r339-caruncle-tissue-sweep"
VARIANTS = (
    ("a-r337-red", (0.16, 0.029, 0.021, 1.0), 0.34, 0.0),
    ("b-muted-tissue", (0.18, 0.070, 0.055, 1.0), 0.42, 0.025),
    ("c-soft-tissue", (0.13, 0.055, 0.045, 1.0), 0.46, 0.035),
    ("d-pale-tissue", (0.25, 0.100, 0.080, 1.0), 0.44, 0.030),
)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
for side in ("L", "R"):
    obj = bpy.data.objects[f"AevryndEye_{side}_Caruncle_R258"]
    matrix = obj.matrix_world.copy()
    obj.matrix_world = matrix @ Matrix.Diagonal((1.6, 1.15, 1.20, 1.0))
    obj.matrix_world.translation.x += -0.00035 if side == "L" else 0.00035
    obj["aevrynd_r339_shape"] = "medial-small-1p86mm"

material = bpy.data.materials["Aevrynd_Caruncle_R258"]
shader = next(node for node in material.node_tree.nodes if node.bl_idname == "ShaderNodeBsdfPrincipled")
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.view_settings.exposure = 0.0
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
views = (
    ("eyes", (0.0, -0.46, 1.615), (0.0, -0.035, 1.610), 105),
    ("face", (0.0, -0.68, 1.605), (0.0, -0.035, 1.606), 92),
    ("three-quarter", (0.45, -0.62, 1.62), (0.0, -0.02, 1.605), 90),
)
metrics = {}
for label, color, roughness, subsurface in VARIANTS:
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Subsurface Weight"].default_value = subsurface
    material["aevrynd_r339_variant"] = label
    for view_name, location, target, lens in views:
        camera.location = location
        camera.data.lens = lens
        look_at(camera, target)
        scene.render.resolution_x = scene.render.resolution_y = 1000
        scene.render.filepath = str(RENDER_DIR / f"{label}-{view_name}.png")
        bpy.ops.render.render(write_still=True)
    metrics[label] = {"baseColor": list(color), "roughness": roughness, "subsurfaceWeight": subsurface}

report = {
    "source": str(SOURCE), "renderDirectory": str(RENDER_DIR), "variants": metrics,
    "fixedGeometry": {"scaleXYZ": [1.6, 1.15, 1.2], "medialShiftM": 0.00035, "worldWidthM": 0.001855999},
    "method": "Hold the collision-safe r338 small medial caruncle shape and sweep tissue saturation, roughness and low subsurface response at fixed 0 EV.",
    "status": "VISUAL_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R339_CARUNCLE_TISSUE=" + json.dumps(report, sort_keys=True))
