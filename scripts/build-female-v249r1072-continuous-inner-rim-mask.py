"""Blend a continuous ray-localized inner-rim response inside the owned skin shader."""
import json
import hashlib
import struct
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-exact-edge-support-r1068-study.blend"
INSPECTION = ASSETS / "female-v249-mainline-r1070-visible-support-faces.inspect.json"
OUTPUT = ASSETS / "aevrynd-female-cc0-continuous-inner-rim-r1072-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1072-continuous-inner-rim-mask.study.json"
OUT = ROOT.parent / "Temp/female-realism/v249r1072-continuous-inner-rim"
BODY = "AevryndFemaleCC0ExactEdgeSupport_R1068"
OPEN_KEY = "Aevrynd_MouthOpenTest_R1030"
SMILE_KEY = "Aevrynd_SmileTest_R1030"
ATTRIBUTE = "aevrynd_inner_rim_r1072"
VARIANTS = (
    ("a-control", 0.0, 0.0),
    ("b-narrow-1.0mm", 1.0, 0.70),
    ("c-medium-2.0mm", 2.0, 0.78),
    ("d-wide-3.0mm", 3.0, 0.86),
    ("e-balanced-1.35mm", 1.35, 0.55),
    ("f-soft-1.60mm", 1.60, 0.52),
    ("g-soft-1.80mm", 1.80, 0.48),
)
SELECTED = "e-balanced-1.35mm"


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def hide_hair(scene):
    for obj in scene.objects:
        name = obj.name.lower()
        if obj.type == "CURVES" or any(token in name for token in ("groom", "scalp", "haircard", "hairfiber")):
            if not any(token in name for token in ("brow", "lash")):
                obj.hide_render = True


def active_coordinates(body):
    blocks = body.data.shape_keys.key_blocks
    coords = [item.co.copy() for item in blocks[0].data]
    for block in blocks[1:]:
        if block.name in (OPEN_KEY, SMILE_KEY) or block.mute or abs(block.value) < 1e-8:
            continue
        for index, item in enumerate(block.data):
            coords[index] += block.value * (item.co - block.relative_key.data[index].co)
    return coords


def geometry_digest(body):
    digest = hashlib.sha256()
    blocks = body.data.shape_keys.key_blocks
    for block in blocks:
        digest.update(block.name.encode("utf-8"))
        for item in block.data:
            digest.update(struct.pack("<3f", item.co.x, item.co.y, item.co.z))
    return digest.hexdigest()


def weight_digest(body):
    digest = hashlib.sha256()
    for vertex in body.data.vertices:
        for group in sorted(vertex.groups, key=lambda item: item.group):
            digest.update(struct.pack("<If", group.group, group.weight))
    return digest.hexdigest()


def point_segment_distance(point, start, end):
    delta = end - start
    if delta.length_squared < 1e-16:
        return (point - start).length
    factor = max(0.0, min(1.0, (point - start).dot(delta) / delta.length_squared))
    return (point - (start + factor * delta)).length


def write_mask(body, line, radius_mm, strength):
    radius = radius_mm / 1000.0
    attribute = body.data.attributes.get(ATTRIBUTE) or body.data.attributes.new(ATTRIBUTE, "FLOAT", "POINT")
    coords = active_coordinates(body)
    values = []
    distances = []
    for local in coords:
        world = body.matrix_world @ local
        if radius <= 0.0 or world.y > -0.105 or abs(world.x) > 0.038 or not (1.378 < world.z < 1.394):
            distance, value = 1.0, 0.0
        else:
            distance = min(point_segment_distance(world, line[index], line[index + 1]) for index in range(len(line) - 1))
            linear = max(0.0, 1.0 - distance / radius)
            value = strength * linear * linear * (3.0 - 2.0 * linear)
        attribute.data[len(values)].value = value
        values.append(value)
        distances.append(distance)
    positive = [value for value in values if value > 1e-6]
    return {
        "radiusMm": radius_mm,
        "strength": strength,
        "positiveVertices": len(positive),
        "aboveHalfVertices": sum(value >= 0.5 for value in values),
        "maximumWeight": max(values),
        "minimumVertexDistanceMm": min(distances) * 1000.0,
    }


def tune_shader(body):
    source = body.data.materials[0]
    material = source.copy()
    material.name = "Aevrynd_CC0_OwnedSkin_R1072_ContinuousInnerRim"
    body.data.materials[0] = material
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = next(node for node in nodes if node.bl_idname == "ShaderNodeBsdfPrincipled")
    attribute = nodes.new("ShaderNodeAttribute")
    attribute.name = "Aevrynd Continuous Inner Rim Attribute R1072"
    attribute.attribute_name = ATTRIBUTE

    base_input = shader.inputs["Base Color"]
    old_base = base_input.links[0] if base_input.links else None
    colour_mix = nodes.new("ShaderNodeMixRGB")
    colour_mix.name = "Aevrynd Continuous Inner Rim Colour R1072"
    colour_mix.blend_type = "MIX"
    colour_mix.inputs[2].default_value = (0.12, 0.018, 0.024, 1.0)
    if old_base:
        source_socket = old_base.from_socket
        links.remove(old_base)
        links.new(source_socket, colour_mix.inputs[1])
    else:
        colour_mix.inputs[1].default_value = base_input.default_value
    links.new(attribute.outputs[2], colour_mix.inputs[0])
    links.new(colour_mix.outputs[0], base_input)

    rough_input = shader.inputs["Roughness"]
    old_rough = rough_input.links[0] if rough_input.links else None
    rough_delta = nodes.new("ShaderNodeMath")
    rough_delta.name = "Aevrynd Continuous Inner Rim Roughness Delta R1072"
    rough_delta.operation = "MULTIPLY"
    rough_delta.inputs[1].default_value = 0.18
    rough_add = nodes.new("ShaderNodeMath")
    rough_add.name = "Aevrynd Continuous Inner Rim Roughness Add R1072"
    rough_add.operation = "ADD"
    rough_add.use_clamp = True
    if old_rough:
        source_socket = old_rough.from_socket
        links.remove(old_rough)
        links.new(source_socket, rough_add.inputs[0])
    else:
        rough_add.inputs[0].default_value = rough_input.default_value
    links.new(attribute.outputs[2], rough_delta.inputs[0])
    links.new(rough_delta.outputs[0], rough_add.inputs[1])
    links.new(rough_add.outputs[0], rough_input)

    specular_input = shader.inputs.get("Specular IOR Level")
    if specular_input:
        base_specular = specular_input.default_value
        specular_delta = nodes.new("ShaderNodeMath")
        specular_delta.name = "Aevrynd Continuous Inner Rim Specular Delta R1072"
        specular_delta.operation = "MULTIPLY"
        specular_delta.inputs[1].default_value = -max(0.0, base_specular - 0.08)
        specular_add = nodes.new("ShaderNodeMath")
        specular_add.name = "Aevrynd Continuous Inner Rim Specular Add R1072"
        specular_add.operation = "ADD"
        specular_add.inputs[0].default_value = base_specular
        specular_add.use_clamp = True
        links.new(attribute.outputs[2], specular_delta.inputs[0])
        links.new(specular_delta.outputs[0], specular_add.inputs[1])
        links.new(specular_add.outputs[0], specular_input)
    return material.name


def render(scene, label, oblique=False, opened=False):
    body = bpy.data.objects[BODY]
    keys = body.data.shape_keys.key_blocks
    keys[OPEN_KEY].value = 1.0 if opened else 0.0
    keys[SMILE_KEY].value = 0.0
    camera = scene.camera
    camera.data.lens = 135
    camera.location = ((-0.105 if oblique else 0.0), -0.43, 1.391)
    look_at(camera, (0.0, -0.115, 1.386))
    scene.render.resolution_x, scene.render.resolution_y = 1100, 720
    scene.render.resolution_percentage = 100
    path = OUT / f"{label}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return str(path)


inspection = json.loads(INSPECTION.read_text(encoding="utf-8"))
points = []
seen = set()
for item in inspection["whiteLinePixelRays"]:
    if item.get("sampleKind") != "brightLine" or item.get("object") != BODY or item.get("location", [0.0, 0.0])[1] >= -0.1:
        continue
    point = Vector(item["location"])
    key = tuple(round(value, 6) for value in point)
    if key not in seen:
        points.append(point)
        seen.add(key)
line = sorted(points, key=lambda point: point.x)
OUT.mkdir(parents=True, exist_ok=True)
results = []
for label, radius_mm, strength in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    body = bpy.data.objects[BODY]
    hide_hair(scene)
    geometry_before = geometry_digest(body)
    weights_before = weight_digest(body)
    metrics = write_mask(body, line, radius_mm, strength)
    if radius_mm > 0.0:
        metrics["material"] = tune_shader(body)
    else:
        metrics["material"] = body.data.materials[0].name
    metrics.update({
        "shapeKeys": len(body.data.shape_keys.key_blocks),
        "vertices": len(body.data.vertices),
        "faces": len(body.data.polygons),
        "materialSlots": len(body.data.materials),
        "geometryDigestBefore": geometry_before,
        "geometryDigestAfter": geometry_digest(body),
        "weightDigestBefore": weights_before,
        "weightDigestAfter": weight_digest(body),
    })
    renders = [render(scene, f"{label}-neutral-front"), render(scene, f"{label}-neutral-oblique", oblique=True), render(scene, f"{label}-open", opened=True)]
    results.append({"label": label, "metrics": metrics, "renders": renders})
    if label == SELECTED:
        body.name = "AevryndFemaleCC0ContinuousInnerRim_R1072"
        body["aevrynd_revision"] = "v249r1072-continuous-inner-rim"
        body["aevrynd_source"] = SOURCE.name
        body["aevrynd_inner_rim_attribute"] = ATTRIBUTE
        scene["aevrynd_release_state"] = "VISUAL_AND_TONE_REVIEW_PENDING"
        scene["aevrynd_website_promotion"] = "forbidden"
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "revision": "v249r1072-continuous-inner-rim-mask",
    "source": str(SOURCE),
    "inspection": str(INSPECTION),
    "output": str(OUTPUT),
    "method": "smooth point-domain distance mask from measured bright-line rays, blended inside the existing owned skin shader for colour, roughness and specular response without another material slot",
    "rayPolylinePoints": [list(point) for point in line],
    "variants": results,
    "selectedVariant": SELECTED,
    "topologyChanged": False,
    "materialSlotDelta": 0,
    "websitePromotionApproved": False,
    "candidateStatus": "VISUAL_AND_TONE_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1072_CONTINUOUS_RIM=" + json.dumps({"rayPoints": len(line), "variants": {item["label"]: item["metrics"] for item in results}}, sort_keys=True))
