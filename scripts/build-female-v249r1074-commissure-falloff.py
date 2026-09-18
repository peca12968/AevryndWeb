"""Reshape only the measured inner-rim mask endpoints around the commissures."""
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
OUTPUT = ASSETS / "aevrynd-female-cc0-commissure-falloff-r1074-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1074-commissure-falloff.study.json"
OUT = ROOT.parent / "Temp/female-realism/v249r1074-commissure-falloff"
BODY = "AevryndFemaleCC0ExactEdgeSupport_R1068"
OPEN_KEY = "Aevrynd_MouthOpenTest_R1030"
SMILE_KEY = "Aevrynd_SmileTest_R1030"
ATTRIBUTE = "aevrynd_inner_rim_r1074"
# label, endpoint extension (mm), endpoint radius gain (mm)
VARIANTS = (
    ("a-control", 0.0, -1.60),
    ("b-r1073-baseline", 0.0, 0.0),
    ("c-extend-2.50", 2.50, 0.0),
    ("d-extend-2.50-radius-0.20", 2.50, 0.20),
    ("e-extend-2.50-radius-0.40", 2.50, 0.40),
    ("f-extend-2.50-radius-0.60", 2.50, 0.60),
)
SELECTED = "e-extend-2.50-radius-0.40"


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
    for block in body.data.shape_keys.key_blocks:
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


def extended_line(line, extension_mm):
    result = [point.copy() for point in line]
    extension = extension_mm / 1000.0
    if extension <= 0.0:
        return result
    left_direction = (line[0] - line[1]).normalized()
    right_direction = (line[-1] - line[-2]).normalized()
    result.insert(0, line[0] + left_direction * extension)
    result.append(line[-1] + right_direction * extension)
    return result


def write_mask(body, base_line, extension_mm, endpoint_radius_gain_mm):
    radius_mm, strength = 1.60, 0.80
    if endpoint_radius_gain_mm < 0.0:
        radius_mm, strength = 0.0, 0.0
    line = extended_line(base_line, extension_mm)
    attribute = body.data.attributes.get(ATTRIBUTE) or body.data.attributes.new(ATTRIBUTE, "FLOAT", "POINT")
    coords = active_coordinates(body)
    values, distances = [], []
    max_source_x = max(abs(base_line[0].x), abs(base_line[-1].x))
    for local in coords:
        world = body.matrix_world @ local
        endpoint_factor = max(0.0, min(1.0, (abs(world.x) - 0.014) / max(1e-8, max_source_x - 0.014)))
        local_radius = (radius_mm + endpoint_radius_gain_mm * endpoint_factor * endpoint_factor) / 1000.0
        if local_radius <= 0.0 or world.y > -0.105 or abs(world.x) > 0.038 or not (1.378 < world.z < 1.394):
            distance, value = 1.0, 0.0
        else:
            distance = min(point_segment_distance(world, line[index], line[index + 1]) for index in range(len(line) - 1))
            linear = max(0.0, 1.0 - distance / local_radius)
            value = strength * linear * linear * (3.0 - 2.0 * linear)
        attribute.data[len(values)].value = value
        values.append(value)
        distances.append(distance)
    positive = [value for value in values if value > 1e-6]
    return {
        "baseRadiusMm": radius_mm,
        "strength": strength,
        "endpointExtensionMm": extension_mm,
        "endpointRadiusGainMm": endpoint_radius_gain_mm,
        "positiveVertices": len(positive),
        "aboveHalfVertices": sum(value >= 0.5 for value in values),
        "maximumWeight": max(values),
        "minimumVertexDistanceMm": min(distances) * 1000.0,
    }


def tune_shader(body):
    source = body.data.materials[0]
    material = source.copy()
    material.name = "Aevrynd_CC0_OwnedSkin_R1074_CommissureFalloff"
    body.data.materials[0] = material
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = next(node for node in nodes if node.bl_idname == "ShaderNodeBsdfPrincipled")
    attribute = nodes.new("ShaderNodeAttribute")
    attribute.name = "Aevrynd Commissure Falloff Attribute R1074"
    attribute.attribute_name = ATTRIBUTE

    rough_input = shader.inputs["Roughness"]
    old_rough = rough_input.links[0] if rough_input.links else None
    rough_delta = nodes.new("ShaderNodeMath")
    rough_delta.name = "Aevrynd Commissure Roughness Delta R1074"
    rough_delta.operation = "MULTIPLY"
    rough_delta.inputs[1].default_value = 0.36
    rough_add = nodes.new("ShaderNodeMath")
    rough_add.name = "Aevrynd Commissure Roughness Add R1074"
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
    base_specular = specular_input.default_value
    specular_delta = nodes.new("ShaderNodeMath")
    specular_delta.name = "Aevrynd Commissure Specular Delta R1074"
    specular_delta.operation = "MULTIPLY"
    specular_delta.inputs[1].default_value = -base_specular
    specular_add = nodes.new("ShaderNodeMath")
    specular_add.name = "Aevrynd Commissure Specular Add R1074"
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
points, seen = [], set()
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
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
body = bpy.data.objects[BODY]
hide_hair(scene)
shader_nodes_before = len(body.data.materials[0].node_tree.nodes)
geometry_before, weights_before = geometry_digest(body), weight_digest(body)
for variant_index, (label, extension_mm, radius_gain_mm) in enumerate(VARIANTS):
    metrics = write_mask(body, line, extension_mm, radius_gain_mm)
    if variant_index == 1:
        tuned_material = tune_shader(body)
    metrics["material"] = body.data.materials[0].name
    metrics.update({
        "shaderNodesBefore": shader_nodes_before,
        "shaderNodesAfter": len(body.data.materials[0].node_tree.nodes),
        "shapeKeys": len(body.data.shape_keys.key_blocks),
        "vertices": len(body.data.vertices), "faces": len(body.data.polygons),
        "materialSlots": len(body.data.materials),
        "geometryDigestBefore": geometry_before, "geometryDigestAfter": geometry_digest(body),
        "weightDigestBefore": weights_before, "weightDigestAfter": weight_digest(body),
    })
    renders = [render(scene, f"{label}-neutral-front"), render(scene, f"{label}-neutral-oblique", oblique=True), render(scene, f"{label}-open", opened=True)]
    results.append({"label": label, "metrics": metrics, "renders": renders})

selected_parameters = next(item for item in VARIANTS if item[0] == SELECTED)
write_mask(body, line, selected_parameters[1], selected_parameters[2])
body.name = "AevryndFemaleCC0CommissureFalloff_R1074"
body["aevrynd_revision"] = "v249r1074-commissure-falloff"
body["aevrynd_source"] = SOURCE.name
body["aevrynd_inner_rim_attribute"] = ATTRIBUTE
scene["aevrynd_release_state"] = "VISUAL_AND_TONE_REVIEW_PENDING"
scene["aevrynd_website_promotion"] = "forbidden"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "revision": "v249r1074-commissure-falloff", "source": str(SOURCE),
    "inspection": str(INSPECTION), "output": str(OUTPUT),
    "method": "preserve the r1073 colour-free optical response and sweep only polyline endpoint extension plus a small endpoint-local radius gain",
    "rayPolylinePoints": [list(point) for point in line], "variants": results,
    "selectedVariant": SELECTED, "topologyChanged": False, "materialSlotDelta": 0,
    "websitePromotionApproved": False, "candidateStatus": "VISUAL_AND_TONE_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1074_COMMISSURE=" + json.dumps({"rayPoints": len(line), "variants": {item["label"]: item["metrics"] for item in results}}, sort_keys=True))
