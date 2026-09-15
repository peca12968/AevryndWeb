import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-balanced-collision-safe-hair-r584.blend"
OUT = ASSETS / "reviews/v249r586-outer-card-opacity-sweep"
REPORT = ASSETS / "female-v249-mainline-outer-card-opacity-r586.study.json"
CARDS = "AevryndFemaleTangentOuterHairCards_R584"
VARIANTS = (
    ("a-r584-current", 1.00),
    ("b-alpha-1p50", 1.50),
    ("c-alpha-2p00", 2.00),
    ("d-alpha-2p50", 2.50),
    ("e-alpha-3p00", 3.00),
)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, camera, label, location, target, lens):
    scene.frame_set(1)
    bpy.context.view_layer.update()
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x = scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(OUT / f"{label}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
scene.view_settings.gamma = 1.0
scene.render.image_settings.file_format = "PNG"
OUT.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
material = bpy.data.objects[CARDS].data.materials[0]
nodes = material.node_tree.nodes
links = material.node_tree.links
shader = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
texture = next(node for node in nodes if node.type == "TEX_IMAGE")
for link in list(shader.inputs["Alpha"].links):
    links.remove(link)
multiply = nodes.get("Aevrynd R586 Outer Alpha") or nodes.new("ShaderNodeMath")
multiply.name = "Aevrynd R586 Outer Alpha"
multiply.operation = "MULTIPLY"
multiply.use_clamp = True
links.new(texture.outputs["Alpha"], multiply.inputs[0])
links.new(multiply.outputs[0], shader.inputs["Alpha"])

variant_report = {}
for label, factor in VARIANTS:
    multiply.inputs[1].default_value = factor
    for view, location, target, lens in (
        ("front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
        ("three-quarter", (0.45, -0.66, 1.60), (0.0, -0.005, 1.56), 84),
        ("profile", (0.72, -0.03, 1.61), (0.0, 0.0, 1.58), 88),
        ("top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
        ("back", (0.0, 0.72, 1.60), (0.0, 0.025, 1.58), 88),
    ):
        render(scene, camera, f"{label}-{view}", location, target, lens)
    variant_report[label] = {"alphaMultiplier": factor}

report = {
    "source": str(SOURCE),
    "method": "hold r584 geometry, direct warm coverage, root fade, lights and collision envelope fixed; multiply only the owned outer-card atlas alpha and clamp to one",
    "variants": variant_report,
    "geometryInvariant": "material-only; r584 collision geometry unchanged",
    "status": "VISUAL_SWEEP_PENDING_REVIEW",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R586_OUTER_CARD_OPACITY=" + json.dumps(report, sort_keys=True))
