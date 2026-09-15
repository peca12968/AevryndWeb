import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-eye-composite-v260.blend"
OUT = ASSETS / "reviews/v249r600-cc0-owned-skin-sweep"
REPORT = ASSETS / "female-v249-mainline-cc0-owned-skin-r600.study.json"
BODY = "AevryndFemaleCC0Baseline_v259"
VARIANTS = (
    ("a-v260-flat-control", None),
    ("b-neutral-owned-skin", ((0.180, 0.060, 0.040, 1.0), (0.245, 0.100, 0.065, 1.0), (0.250, 0.050, 0.045, 1.0))),
    ("c-balanced-owned-skin", ((0.195, 0.067, 0.045, 1.0), (0.270, 0.110, 0.072, 1.0), (0.270, 0.055, 0.048, 1.0))),
    ("d-warm-owned-skin", ((0.210, 0.073, 0.048, 1.0), (0.290, 0.120, 0.078, 1.0), (0.285, 0.060, 0.052, 1.0))),
)
VIEWS = (
    ("front", (0.0, -1.22, 1.55), (0.0, -0.01, 1.55)),
    ("three-quarter", (0.74, -1.0, 1.56), (0.0, 0.0, 1.55)),
    ("profile", (1.22, 0.0, 1.55), (0.0, 0.0, 1.55)),
)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def owned_skin(label, dark, light, lip):
    material = bpy.data.materials.new(f"Aevrynd_CC0_OwnedSkin_R600_{label}")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    shader.inputs["Roughness"].default_value = 0.50
    shader.inputs["Subsurface Weight"].default_value = 0.045
    shader.inputs["Subsurface Scale"].default_value = 0.0045
    shader.inputs["Specular IOR Level"].default_value = 0.20
    shader.inputs["Coat Weight"].default_value = 0.006
    coords = nodes.new("ShaderNodeTexCoord")
    tone = nodes.new("ShaderNodeTexNoise")
    tone.noise_dimensions = "3D"
    tone.inputs["Scale"].default_value = 34.0
    tone.inputs["Detail"].default_value = 2.4
    tone.inputs["Roughness"].default_value = 0.56
    tone.inputs["Distortion"].default_value = 0.06
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.20
    ramp.color_ramp.elements[0].color = dark
    ramp.color_ramp.elements[1].position = 0.80
    ramp.color_ramp.elements[1].color = light
    lips = nodes.new("ShaderNodeAttribute")
    lips.attribute_name = "lips"
    lip_mix = nodes.new("ShaderNodeMixRGB")
    lip_mix.blend_type = "MIX"
    lip_mix.inputs[2].default_value = lip
    pore = nodes.new("ShaderNodeTexNoise")
    pore.noise_dimensions = "3D"
    pore.inputs["Scale"].default_value = 720.0
    pore.inputs["Detail"].default_value = 2.0
    pore.inputs["Roughness"].default_value = 0.62
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.045
    bump.inputs["Distance"].default_value = 0.00007
    links.new(coords.outputs["Object"], tone.inputs["Vector"])
    links.new(tone.outputs["Factor"], ramp.inputs["Factor"])
    links.new(ramp.outputs["Color"], lip_mix.inputs[1])
    links.new(lips.outputs["Fac"], lip_mix.inputs[0])
    links.new(lip_mix.outputs["Color"], shader.inputs["Base Color"])
    links.new(coords.outputs["Object"], pore.inputs["Vector"])
    links.new(pore.outputs["Factor"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return material


report = {"source": str(SOURCE), "method": "Aevrynd-owned object-space tone and pore fields plus the MPFB CC0 lips vertex group; no topology-specific UV dependency", "variants": {}}
OUT.mkdir(parents=True, exist_ok=True)
for label, colors in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0
    scene.render.image_settings.file_format = "PNG"
    scene.render.resolution_x = scene.render.resolution_y = 1100
    scene.render.resolution_percentage = 100
    body = bpy.data.objects[BODY]
    if colors is not None:
        body.data.materials[0] = owned_skin(label, *colors)
    camera = bpy.data.objects["Aevrynd Baseline Camera"]
    scene.camera = camera
    for view, location, target in VIEWS:
        camera.location = location
        camera.data.lens = 105
        look_at(camera, target)
        scene.render.filepath = str(OUT / f"{label}-{view}.png")
        bpy.ops.render.render(write_still=True)
    report["variants"][label] = {
        "colorsLinearRGBA": None if colors is None else [list(color) for color in colors],
        "roughness": None if colors is None else 0.50,
        "subsurfaceWeight": None if colors is None else 0.045,
        "poreScale": None if colors is None else 720.0,
        "poreStrength": None if colors is None else 0.045,
        "usesUv": False if colors is not None else None,
        "usesOwnedOrCC0DataOnly": True,
    }
report["status"] = "VISUAL_SWEEP_PENDING_REVIEW"
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R600_CC0_OWNED_SKIN=" + json.dumps(report, sort_keys=True))
