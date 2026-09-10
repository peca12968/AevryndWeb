import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-owned-hair-material-r129.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r129-root-darkening-r140-sweep"
MATERIAL = "AevryndOwnedLayeredHairMaterial_v249r129"
VARIANTS = (
    ("a-official-baseline", 0.6313559413, 0.3220338821),
    ("b-balanced-short-root", 0.35, 0.16),
    ("c-subtle-short-root", 0.18, 0.08),
    ("d-no-root-darkening", 0.0, 0.0),
)


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, location, target, lens):
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    bpy.context.scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
OUT.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
material = bpy.data.materials[MATERIAL]
group = next(node for node in material.node_tree.nodes if node.bl_idname == "ShaderNodeGroup")
camera = bpy.data.objects["Aevrynd Review Camera"]
views = (
    ("front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
    ("three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88),
    ("top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
    ("back", (0.0, 2.10, 1.56), (0.0, 0.02, 1.54), 82),
)
report = {"source": str(SOURCE), "geometryChanged": False, "variants": []}

for name, darken, length in VARIANTS:
    group.inputs["Darken root"].default_value = darken
    group.inputs["Root color length"].default_value = length
    for suffix, location, target, lens in views:
        render(camera, f"{name}-{suffix}", location, target, lens)
    report["variants"].append({
        "name": name,
        "darkenRoot": darken,
        "rootColorLength": length,
    })

(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R140_ROOT_DARKENING=" + json.dumps(report, sort_keys=True))
