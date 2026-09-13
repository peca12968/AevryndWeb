import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-recessed-orbital-folds-r413.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-natural-iris-r414.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r414-natural-iris-sweep"


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def math_node(nodes, operation, value=None, name=None):
    node = nodes.new("ShaderNodeMath")
    node.operation = operation
    if value is not None:
        node.inputs[1].default_value = value
    if name:
        node.name = name
    return node


def radial_ramp(nodes, links, radius, name, stops):
    node = nodes.new("ShaderNodeValToRGB")
    node.name = name
    ramp = node.color_ramp
    ramp.interpolation = "EASE"
    while len(ramp.elements) > 2:
        ramp.elements.remove(ramp.elements[-1])
    for index, (position, value) in enumerate(stops):
        element = ramp.elements[index] if index < 2 else ramp.elements.new(position)
        element.position = position
        element.color = (value, value, value, 1.0)
    links.new(radius.outputs[0], node.inputs["Fac"])
    return node


def build_material(side, label, vascular, coat_weight, coat_roughness, iris_high):
    material = bpy.data.materials.new(f"Aevrynd_LayeredEye_{side}_{label}_R414")
    material.use_nodes = True
    material["aevrynd_ownership"] = "procedural in-project"
    material["aevrynd_revision"] = "v249r414"
    material["aevrynd_eye_layers"] = "sclera,veins,limbal,iris-fibers,collarette,pupil,corneal-coat"
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    shader.name = "Aevrynd Integrated Eye Surface"
    shader.inputs["Roughness"].default_value = 0.27
    if "IOR" in shader.inputs:
        shader.inputs["IOR"].default_value = 1.376
    if "Coat Weight" in shader.inputs:
        shader.inputs["Coat Weight"].default_value = coat_weight
        shader.inputs["Coat Roughness"].default_value = coat_roughness
    if "Subsurface Weight" in shader.inputs:
        shader.inputs["Subsurface Weight"].default_value = 0.012
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])

    texcoord = nodes.new("ShaderNodeTexCoord")
    separate = nodes.new("ShaderNodeSeparateXYZ")
    links.new(texcoord.outputs["Generated"], separate.inputs["Vector"])
    x = math_node(nodes, "SUBTRACT", 0.5)
    z = math_node(nodes, "SUBTRACT", 0.5)
    links.new(separate.outputs["X"], x.inputs[0]); links.new(separate.outputs["Z"], z.inputs[0])
    x2 = math_node(nodes, "MULTIPLY"); z2 = math_node(nodes, "MULTIPLY")
    links.new(x.outputs[0], x2.inputs[0]); links.new(x.outputs[0], x2.inputs[1])
    links.new(z.outputs[0], z2.inputs[0]); links.new(z.outputs[0], z2.inputs[1])
    radius2 = math_node(nodes, "ADD"); radius = math_node(nodes, "SQRT", name="Aevrynd Iris Radius")
    links.new(x2.outputs[0], radius2.inputs[0]); links.new(z2.outputs[0], radius2.inputs[1]); links.new(radius2.outputs[0], radius.inputs[0])
    front = math_node(nodes, "LESS_THAN", 0.24, "Aevrynd Front Hemisphere")
    links.new(separate.outputs["Y"], front.inputs[0])

    iris_radial = radial_ramp(nodes, links, radius, "Aevrynd Soft Iris Mask", ((0.185, 1.0), (0.202, 0.0)))
    pupil_radial = radial_ramp(nodes, links, radius, "Aevrynd Soft Pupil Mask", ((0.056, 1.0), (0.071, 0.0)))
    limbal_radial = radial_ramp(nodes, links, radius, "Aevrynd Limbal Band", ((0.160, 0.0), (0.174, 1.0), (0.197, 1.0), (0.208, 0.0)))
    collarette_radial = radial_ramp(nodes, links, radius, "Aevrynd Collarette Band", ((0.088, 0.0), (0.108, 1.0), (0.132, 1.0), (0.151, 0.0)))
    masks = {}
    for name, source in (("iris", iris_radial), ("pupil", pupil_radial), ("limbal", limbal_radial), ("collarette", collarette_radial)):
        mask = math_node(nodes, "MULTIPLY", name=f"Aevrynd {name.title()} Front Mask")
        links.new(source.outputs["Color"], mask.inputs[0]); links.new(front.outputs[0], mask.inputs[1])
        masks[name] = mask

    sclera_noise = nodes.new("ShaderNodeTexNoise")
    sclera_noise.name = "Aevrynd Sclera Mottle"
    sclera_noise.inputs["Scale"].default_value = 8.0
    sclera_noise.inputs["Detail"].default_value = 4.0
    sclera_noise.inputs["Roughness"].default_value = 0.68
    links.new(texcoord.outputs["Generated"], sclera_noise.inputs["Vector"])
    sclera_ramp = nodes.new("ShaderNodeValToRGB")
    sclera_ramp.color_ramp.elements[0].color = (0.18, 0.14, 0.13, 1.0)
    sclera_ramp.color_ramp.elements[1].color = (0.42, 0.36, 0.32, 1.0)
    links.new(sclera_noise.outputs["Fac"], sclera_ramp.inputs["Fac"])
    base_color = sclera_ramp.outputs["Color"]

    if vascular:
        voronoi = nodes.new("ShaderNodeTexVoronoi")
        voronoi.name = "Aevrynd Sclera Capillaries"
        voronoi.feature = "DISTANCE_TO_EDGE"
        voronoi.distance = "EUCLIDEAN"
        voronoi.inputs["Scale"].default_value = 24.0
        links.new(texcoord.outputs["Generated"], voronoi.inputs["Vector"])
        vein_ramp = nodes.new("ShaderNodeValToRGB")
        vein_ramp.color_ramp.elements[0].position = 0.012
        vein_ramp.color_ramp.elements[0].color = (1.0, 1.0, 1.0, 1.0)
        vein_ramp.color_ramp.elements[1].position = 0.042
        vein_ramp.color_ramp.elements[1].color = (0.0, 0.0, 0.0, 1.0)
        links.new(voronoi.outputs["Distance"], vein_ramp.inputs["Fac"])
        inverse_iris = math_node(nodes, "SUBTRACT")
        inverse_iris.inputs[0].default_value = 1.0
        links.new(masks["iris"].outputs[0], inverse_iris.inputs[1])
        vein_mask = math_node(nodes, "MULTIPLY")
        links.new(vein_ramp.outputs["Color"], vein_mask.inputs[0]); links.new(inverse_iris.outputs[0], vein_mask.inputs[1])
        vein_strength = math_node(nodes, "MULTIPLY", 0.055)
        links.new(vein_mask.outputs[0], vein_strength.inputs[0])
        vein_mix = nodes.new("ShaderNodeMixRGB")
        vein_mix.inputs[2].default_value = (0.36, 0.055, 0.045, 1.0)
        links.new(vein_strength.outputs[0], vein_mix.inputs[0]); links.new(base_color, vein_mix.inputs[1])
        base_color = vein_mix.outputs[0]

    angle = math_node(nodes, "ARCTAN2")
    links.new(z.outputs[0], angle.inputs[0]); links.new(x.outputs[0], angle.inputs[1])
    spoke_a = math_node(nodes, "MULTIPLY", 53.0); spoke_b = math_node(nodes, "MULTIPLY", 23.0)
    links.new(angle.outputs[0], spoke_a.inputs[0]); links.new(angle.outputs[0], spoke_b.inputs[0])
    sine_a = math_node(nodes, "SINE"); sine_b = math_node(nodes, "SINE")
    abs_a = math_node(nodes, "ABSOLUTE"); abs_b = math_node(nodes, "ABSOLUTE")
    links.new(spoke_a.outputs[0], sine_a.inputs[0]); links.new(spoke_b.outputs[0], sine_b.inputs[0])
    links.new(sine_a.outputs[0], abs_a.inputs[0]); links.new(sine_b.outputs[0], abs_b.inputs[0])
    spoke_mix = math_node(nodes, "MULTIPLY")
    links.new(abs_a.outputs[0], spoke_mix.inputs[0]); links.new(abs_b.outputs[0], spoke_mix.inputs[1])
    iris_noise = nodes.new("ShaderNodeTexNoise")
    iris_noise.inputs["Scale"].default_value = 42.0
    iris_noise.inputs["Detail"].default_value = 6.0
    iris_noise.inputs["Roughness"].default_value = 0.76
    links.new(texcoord.outputs["Generated"], iris_noise.inputs["Vector"])
    fibers = nodes.new("ShaderNodeMixRGB")
    fibers.blend_type = "MULTIPLY"
    fibers.inputs[0].default_value = 0.68
    links.new(iris_noise.outputs["Fac"], fibers.inputs[1]); links.new(spoke_mix.outputs[0], fibers.inputs[2])
    iris_ramp = nodes.new("ShaderNodeValToRGB")
    iris_ramp.name = "Aevrynd Iris Fiber Color"
    iris_ramp.color_ramp.elements[0].position = 0.12
    iris_ramp.color_ramp.elements[0].color = (0.002, 0.010, 0.005, 1.0)
    iris_ramp.color_ramp.elements[1].position = 0.76
    iris_ramp.color_ramp.elements[1].color = iris_high
    links.new(fibers.outputs[0], iris_ramp.inputs["Fac"])

    iris_mix = nodes.new("ShaderNodeMixRGB")
    links.new(masks["iris"].outputs[0], iris_mix.inputs[0]); links.new(base_color, iris_mix.inputs[1]); links.new(iris_ramp.outputs["Color"], iris_mix.inputs[2])
    collarette_mix = nodes.new("ShaderNodeMixRGB")
    collarette_mix.inputs[2].default_value = (0.10, 0.075, 0.018, 1.0)
    links.new(masks["collarette"].outputs[0], collarette_mix.inputs[0]); links.new(iris_mix.outputs[0], collarette_mix.inputs[1])
    limbal_mix = nodes.new("ShaderNodeMixRGB")
    limbal_mix.inputs[2].default_value = (0.002, 0.010, 0.006, 1.0)
    links.new(masks["limbal"].outputs[0], limbal_mix.inputs[0]); links.new(iris_mix.outputs[0], limbal_mix.inputs[1])
    pupil_mix = nodes.new("ShaderNodeMixRGB")
    pupil_mix.inputs[2].default_value = (0.0004, 0.0004, 0.0004, 1.0)
    links.new(masks["pupil"].outputs[0], pupil_mix.inputs[0]); links.new(limbal_mix.outputs[0], pupil_mix.inputs[1])
    links.new(pupil_mix.outputs[0], shader.inputs["Base Color"])
    return material


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
views = (
    ("face", (0.0, -0.68, 1.605), (0.0, -0.035, 1.606), 92),
    ("eyes", (0.0, -0.46, 1.615), (0.0, -0.035, 1.610), 105),
)
variants = (
    ("a-r413", None),
    ("b-natural-soft", (0.08, 0.22, (0.030, 0.135, 0.065, 1.0))),
    ("c-natural-muted", (0.045, 0.30, (0.020, 0.095, 0.050, 1.0))),
)
metrics = {}
for label, settings in variants:
    if settings is not None:
        coat_weight, coat_roughness, iris_high = settings
        for side in ("L", "R"):
            eye = bpy.data.objects[f"AevryndEye_{side}_Sclera_R249"]
            material = build_material(side, label, False, coat_weight, coat_roughness, iris_high)
            eye.data = eye.data.copy()
            eye.data.materials.clear()
            eye.data.materials.append(material)
    for view_name, location, target, lens in views:
        camera.location = location
        camera.data.lens = lens
        look_at(camera, target)
        scene.render.resolution_x = scene.render.resolution_y = 1000
        scene.render.filepath = str(RENDER_DIR / f"{label}-{view_name}.png")
        bpy.ops.render.render(write_still=True)
    metrics[label] = {"settings": settings, "geometryChanged": False, "skinLightingExposureChanged": False}

report = {
    "source": str(SOURCE), "renderDirectory": str(RENDER_DIR), "variants": metrics,
    "fixedConditions": {"skinMaterial": "unchanged", "lighting": "unchanged", "exposureEV": 0.0, "eyeGeometry": "unchanged"},
    "status": "VISUAL_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R414_LAYERED_IRIS_SWEEP=" + json.dumps(report, sort_keys=True))
