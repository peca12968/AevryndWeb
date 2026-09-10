import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-converged-upper-lid-r210.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r222-integrated-lip-color-sweep"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-integrated-lip-color-r222.sweep-report.json"
BODY = "AevryndFemaleBodyBaseV118"
VARIANTS = (
    ("a-control", None),
    ("b-natural", (1.025, 0.88, 0.86, 0.90)),
    ("c-balanced", (1.040, 0.80, 0.77, 0.82)),
    ("d-strong", (1.055, 0.70, 0.67, 0.74)),
)


def gaussian(value, center, sigma):
    return math.exp(-0.5 * ((value - center) / sigma) ** 2)


def build_field(body, target):
    name = "AevryndIntegratedLipColorR222"
    old = body.data.color_attributes.get(name)
    if old:
        body.data.color_attributes.remove(old)
    field = body.data.color_attributes.new(name=name, type="FLOAT_COLOR", domain="POINT")
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    changed = 0
    maximum = 0.0
    for index, vertex in enumerate(mesh.vertices):
        p = evaluated.matrix_world @ vertex.co
        ax = abs(p.x)
        front = gaussian(p.y, -0.130, 0.019)
        width = gaussian(ax, 0.0, 0.037)
        upper = gaussian(p.z, 1.5330, 0.0058)
        lower = gaussian(p.z, 1.5240, 0.0065)
        mask = min(1.0, width * front * max(upper, lower))
        # Preserve a soft skin transition at the vermilion border.
        mask = max(0.0, min(1.0, (mask - 0.08) / 0.72))
        color = tuple(1.0 + (target[channel] - 1.0) * mask for channel in range(3)) + (1.0,)
        field.data[index].color = color
        if mask > 0.01:
            changed += 1
            maximum = max(maximum, mask)
    evaluated.to_mesh_clear()
    return field, {"verticesTinted": changed, "maximumMask": maximum}


def tune_material(body, target, label):
    material = body.active_material.copy()
    material.name = f"Aevrynd_Skin_IntegratedLip_R222_{label}"
    body.data.materials.clear()
    body.data.materials.append(material)
    field, metrics = build_field(body, target)
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
    base = shader.inputs["Base Color"]
    source = base.links[0].from_socket
    for link in list(base.links):
        links.remove(link)
    color = nodes.new("ShaderNodeVertexColor")
    color.name = "Aevrynd Integrated Lip Color Field R222"
    color.layer_name = field.name
    multiply = nodes.new("ShaderNodeMixRGB")
    multiply.name = "Aevrynd Integrated Lip Color Multiply R222"
    multiply.blend_type = "MULTIPLY"
    multiply.inputs[0].default_value = 1.0
    links.new(source, multiply.inputs[1])
    links.new(color.outputs["Color"], multiply.inputs[2])
    links.new(multiply.outputs["Color"], base)
    material["aevrynd_skin_revision"] = "v249r222-sweep"
    material["aevrynd_lip_color_variant"] = label
    return material.name, metrics


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
report = {"source": str(SOURCE), "variants": {}, "status": "VISUAL_SELECTION_PENDING"}
for label, target in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    body = bpy.data.objects[BODY]
    metrics = {"targetMultiplier": target or "r210-control", "material": body.active_material.name}
    if target:
        metrics["material"], field_metrics = tune_material(body, target, label)
        metrics.update(field_metrics)
    camera = bpy.data.objects["Aevrynd Review Camera"]
    views = (
        ("01-face-front", (0.0, -0.56, 1.585), (0.0, -0.060, 1.585), 108, (1100, 1100)),
        ("02-mouth-close", (0.0, -0.43, 1.525), (0.0, -0.105, 1.525), 120, (1100, 760)),
        ("03-three-quarter", (0.45, -0.62, 1.58), (0.0, -0.015, 1.565), 92, (1000, 1000)),
        ("04-profile", (0.70, -0.03, 1.57), (0.0, -0.010, 1.555), 96, (1000, 1000)),
    )
    for view_name, location, aim, lens, size in views:
        render(camera, f"{label}-{view_name}.png", location, aim, lens, size)
    report["variants"][label] = metrics
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R222_INTEGRATED_LIP_COLOR=" + json.dumps(report, sort_keys=True))
