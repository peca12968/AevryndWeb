import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-satin-hair-r192.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r196-lip-microrelief-sweep"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-lip-microrelief-r196.sweep-report.json"
VARIANTS = (
    {"name": "a-control", "control": True},
    {"name": "b-subtle", "strength": 0.075, "distanceMm": 0.11},
    {"name": "c-balanced", "strength": 0.13, "distanceMm": 0.16},
    {"name": "d-strong", "strength": 0.21, "distanceMm": 0.23},
)
MATERIALS = ("Aevrynd_LipVermilion_v50", "Aevrynd_LipInner_v50")


def add_microrelief(source, variant):
    material = source.copy()
    material.name = source.name + "_R196_" + variant["name"]
    tree = material.node_tree
    shader = next(node for node in tree.nodes if node.bl_idname == "ShaderNodeBsdfPrincipled")
    texcoord = tree.nodes.new("ShaderNodeTexCoord")
    texcoord.name = "Aevrynd Lip Coordinates r196"
    mapping = tree.nodes.new("ShaderNodeMapping")
    mapping.name = "Aevrynd Lip Vertical Scale r196"
    mapping.inputs["Scale"].default_value = (1.0, 0.16, 0.32)
    wave = tree.nodes.new("ShaderNodeTexWave")
    wave.name = "Aevrynd Lip Primary Furrows r196"
    wave.wave_type = "BANDS"
    wave.bands_direction = "X"
    wave.inputs["Scale"].default_value = 18.0
    wave.inputs["Distortion"].default_value = 6.0
    wave.inputs["Detail"].default_value = 5.0
    wave.inputs["Detail Scale"].default_value = 1.7
    noise = tree.nodes.new("ShaderNodeTexNoise")
    noise.name = "Aevrynd Lip Irregularity r196"
    noise.noise_dimensions = "3D"
    noise.inputs["Scale"].default_value = 32.0
    noise.inputs["Detail"].default_value = 3.5
    noise.inputs["Roughness"].default_value = 0.62
    mix = tree.nodes.new("ShaderNodeMixRGB")
    mix.name = "Aevrynd Lip Furrow Breakup r196"
    mix.blend_type = "MULTIPLY"
    mix.inputs[0].default_value = 0.38
    bump = tree.nodes.new("ShaderNodeBump")
    bump.name = "Aevrynd Lip Microrelief r196"
    bump.inputs["Strength"].default_value = variant["strength"]
    bump.inputs["Distance"].default_value = variant["distanceMm"] / 1000.0
    tree.links.new(texcoord.outputs["Generated"], mapping.inputs["Vector"])
    tree.links.new(mapping.outputs["Vector"], wave.inputs["Vector"])
    tree.links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
    tree.links.new(wave.outputs["Color"], mix.inputs[1])
    tree.links.new(noise.outputs["Fac"], mix.inputs[2])
    tree.links.new(mix.outputs["Color"], bump.inputs["Height"])
    tree.links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    shader.inputs["Roughness"].default_value = 0.56 if "Vermilion" in source.name else 0.48
    material["aevrynd_revision"] = "v249r196"
    material["aevrynd_layer"] = "face.lip.microrelief"
    return material


def apply_variant(variant):
    if variant.get("control"):
        return
    replacements = {name: add_microrelief(bpy.data.materials[name], variant) for name in MATERIALS}
    for object_name in ("Lip_Upper", "Lip_Lower"):
        obj = bpy.data.objects[object_name]
        for index, slot in enumerate(obj.data.materials):
            if slot.name in replacements:
                obj.data.materials[index] = replacements[slot.name]


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, filename, location, target, lens, size):
    scene = bpy.context.scene
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.filepath = str(OUT / filename)
    bpy.ops.render.render(write_still=True)


OUT.mkdir(parents=True, exist_ok=True)
report = {"source": str(SOURCE), "geometryChanged": False, "runtimeDependency": "none", "variants": []}
for variant in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    apply_variant(variant)
    camera = bpy.data.objects["Aevrynd Review Camera"]
    views = (
        ("01-mouth-front", (0.0, -0.42, 1.535), (0.0, -0.090, 1.535), 145, (1400, 900)),
        ("02-face-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88, (1000, 1000)),
        ("03-face-three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88, (1000, 1000)),
        ("04-mouth-profile", (0.48, -0.035, 1.535), (0.0, -0.055, 1.535), 122, (1100, 900)),
    )
    for view_name, location, target, lens, size in views:
        render(camera, f"{variant['name']}-{view_name}.png", location, target, lens, size)
    report["variants"].append(variant)

REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R196_LIP_MICRORELIEF=" + json.dumps(report, sort_keys=True))
