import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-nasal-midface-planes-r473.blend"
REPORT = ASSETS / "female-v249-mainline-r474.vermilion-plane-sweep.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r474-vermilion-plane-sweep"
BODY = "AevryndFemaleBodyBaseV118"
TARGET_COLOR = (0.39, 0.115, 0.095, 1.0)
COLOR_MIX = 0.16


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def smoothstep(value):
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def gaussian(value, center, sigma):
    return math.exp(-0.5 * ((value - center) / sigma) ** 2)


def lip_bounds(point):
    ax = abs(point.x)
    corner = smoothstep((ax - 0.026) / 0.016)
    cupid = gaussian(ax, 0.0112, 0.0050)
    notch = gaussian(ax, 0.0, 0.0045)
    slit = 1.52955
    top = (1.5369 + 0.00135 * cupid - 0.00062 * notch) * (1.0 - corner) + 1.5300 * corner
    bottom = 1.5202 * (1.0 - corner) + 1.5284 * corner
    return slit, top, bottom, corner, cupid, notch


def vermilion_mask(point):
    ax = abs(point.x)
    if ax >= 0.045 or point.y > -0.108 or not (1.518 < point.z < 1.540):
        return 0.0
    slit, top, bottom, corner, _cupid, _notch = lip_bounds(point)
    width = 1.0 - smoothstep((ax - 0.031) / 0.014)
    front = 1.0 - smoothstep((point.y + 0.126) / 0.018)
    upper = smoothstep((point.z - (slit - 0.0004)) / 0.0011) * (1.0 - smoothstep((point.z - (top - 0.0011)) / 0.0015))
    lower = smoothstep((point.z - (bottom - 0.0008)) / 0.0015) * (1.0 - smoothstep((point.z - (slit - 0.0010)) / 0.0012))
    return clamp(max(upper, lower) * width * front * (1.0 - 0.18 * corner))


def geometry_delta(point):
    ax = abs(point.x)
    if ax >= 0.047 or point.y > -0.108 or not (1.5265 < point.z < 1.541):
        return Vector()
    slit, top, _bottom, corner, cupid, notch = lip_bounds(point)
    width = 1.0 - smoothstep((ax - 0.030) / 0.017)
    front = 1.0 - smoothstep((point.y + 0.126) / 0.018)
    if width <= 0.0 or front <= 0.0:
        return Vector()

    # Form a shallow vermilion plane and a readable border rather than a
    # single outward ridge.  The top groove turns inward while the center of
    # the upper lip moves outward by less than one millimetre.
    height = max(0.001, top - slit)
    t = clamp((point.z - slit) / height)
    plane = math.sin(math.pi * t) if slit <= point.z <= top else 0.0
    top_groove = gaussian(point.z, top, 0.00105)
    slit_roll = gaussian(point.z, slit + 0.0007, 0.00110)
    gate = width * front * (1.0 - 0.35 * corner)
    outward = -0.00072 * plane * gate - 0.00018 * slit_roll * gate
    inward_border = 0.00034 * top_groove * gate
    peak_lift = 0.00030 * cupid * plane * gate
    center_notch = -0.00017 * notch * top_groove * gate
    corner_tension = -0.00010 * corner * gaussian(point.z, slit, 0.0018) * width * front
    side = -1.0 if point.x < 0.0 else 1.0
    return Vector((-side * corner_tension, outward + inward_border, peak_lift + center_notch))


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, camera, label, location, target, lens, size):
    scene.frame_set(1)
    bpy.context.view_layer.update()
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.filepath = str(RENDER_DIR / f"{label}.png")
    bpy.ops.render.render(write_still=True)


def build_variant(strength, label):
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    bpy.context.view_layer.update()
    body = bpy.data.objects[BODY]
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    world_points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    evaluated.to_mesh_clear()
    inverse3 = body.matrix_world.inverted().to_3x3()
    deltas = {i: geometry_delta(point) for i, point in enumerate(world_points)}
    deltas = {i: delta for i, delta in deltas.items() if delta.length > 0.000001}
    keys = list(body.data.shape_keys.key_blocks)
    for key in keys:
        for index, delta in deltas.items():
            key.data[index].co += inverse3 @ (delta * strength)
    body.data.update()

    material_name = body.active_material.name
    tinted = 0
    max_mask = 0.0
    if strength > 0.0:
        attr_name = f"AevryndVermilionPlaneR474_{label}"
        old = body.data.color_attributes.get(attr_name)
        if old:
            body.data.color_attributes.remove(old)
        attr = body.data.color_attributes.new(name=attr_name, type="FLOAT_COLOR", domain="POINT")
        for index, point in enumerate(world_points):
            mask = vermilion_mask(point) * COLOR_MIX
            attr.data[index].color = (mask, mask, mask, 1.0)
            if mask > 0.001:
                tinted += 1
                max_mask = max(max_mask, mask)
        material = body.active_material.copy()
        material.name = f"Aevrynd_Skin_VermilionPlane_R474_{label}"
        body.data.materials.clear()
        body.data.materials.append(material)
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        shader = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
        base = shader.inputs["Base Color"]
        source_socket = base.links[0].from_socket
        for link in list(base.links):
            links.remove(link)
        color = nodes.new("ShaderNodeVertexColor")
        color.name = "Aevrynd Vermilion Plane Mask R474"
        color.layer_name = attr_name
        mix = nodes.new("ShaderNodeMixRGB")
        mix.name = "Aevrynd Vermilion Plane Color R474"
        mix.blend_type = "MIX"
        mix.inputs[2].default_value = TARGET_COLOR
        links.new(color.outputs["Color"], mix.inputs[0])
        links.new(source_socket, mix.inputs[1])
        links.new(mix.outputs["Color"], base)
        material_name = material.name

    scene.render.engine = "BLENDER_EEVEE"
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0.0
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
    scene.camera = camera
    views = (
        ("face-front", (0.0, -0.56, 1.585), (0.0, -0.060, 1.585), 108, (1100, 1100)),
        ("mouth-close", (0.0, -0.405, 1.528), (0.0, -0.115, 1.528), 135, (1400, 800)),
        ("mouth-oblique", (0.235, -0.405, 1.53), (0.0, -0.112, 1.528), 135, (1400, 800)),
        ("three-quarter", (0.40, -0.57, 1.58), (0.0, -0.030, 1.56), 92, (1000, 1000)),
    )
    for view_name, location, target, lens, size in views:
        render(scene, camera, f"{label}-{view_name}", location, target, lens, size)
    return {
        "strength": strength,
        "verticesMoved": len(deltas) if strength else 0,
        "maximumNominalDeltaMm": max((delta.length for delta in deltas.values()), default=0.0) * strength * 1000.0,
        "shapeKeysMovedTogether": [key.name for key in keys],
        "verticesTinted": tinted,
        "maximumColorMix": max_mask,
        "material": material_name,
    }


RENDER_DIR.mkdir(parents=True, exist_ok=True)
report = {
    "source": str(SOURCE),
    "method": "shallow upper-vermilion plane, inward top-border groove, cupid peaks, center notch, commissure tension and low-amplitude continuous-body tint",
    "targetColorLinear": TARGET_COLOR,
    "variants": {},
    "renderDirectory": str(RENDER_DIR),
    "status": "STRICT_VISUAL_SELECTION_REQUIRED",
}
for label, strength in (("a-control", 0.0), ("b-subtle-070", 0.70), ("c-balanced-100", 1.0), ("d-defined-130", 1.30)):
    report["variants"][label] = build_variant(strength, label)
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R474_VERMILION_SWEEP=" + json.dumps(report, sort_keys=True))
