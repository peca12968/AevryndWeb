import json
import math
import sys

import bpy


def input_path():
    if "--" not in sys.argv:
        raise SystemExit("usage: blender --background --python audit-female-skin-v17.py -- model.blend")
    values = sys.argv[sys.argv.index("--") + 1:]
    if len(values) != 1:
        raise SystemExit("expected one Blender file")
    return values[0]


def image_report(image):
    values = list(image.pixels)
    channels = [values[index::4] for index in range(4)]
    width, height = image.size

    def pixel(x, y, channel):
        return values[(y * width + x) * 4 + channel]

    horizontal_delta = max(abs(pixel(0, y, c) - pixel(width - 1, y, c)) for y in range(height) for c in range(3))
    vertical_delta = max(abs(pixel(x, 0, c) - pixel(x, height - 1, c)) for x in range(width) for c in range(3))
    return {
        "size": [width, height],
        "minimum": [min(channel) for channel in channels[:3]],
        "maximum": [max(channel) for channel in channels[:3]],
        "mean": [sum(channel) / len(channel) for channel in channels[:3]],
        "horizontal_edge_delta": horizontal_delta,
        "vertical_edge_delta": vertical_delta,
    }


bpy.ops.wm.open_mainfile(filepath=input_path())
body = bpy.data.objects["AevryndFemaleBodyBase"]
material = body.data.materials[0]
nodes = material.node_tree.nodes
shader = nodes["Principled BSDF"]
normal_texture = nodes.get("Aevrynd Runtime Normal")
roughness_texture = nodes.get("Aevrynd Runtime Roughness")
normal_map = nodes.get("Aevrynd Runtime Normal Map")
failures = []
if not normal_texture or not normal_texture.image:
    failures.append("runtime normal texture is disconnected")
if not roughness_texture or not roughness_texture.image:
    failures.append("runtime roughness texture is disconnected")
if not normal_map:
    failures.append("normal map converter is missing")
if not shader.inputs["Normal"].is_linked:
    failures.append("skin shader normal input is not linked")
if not shader.inputs["Roughness"].is_linked:
    failures.append("skin shader roughness input is not linked")

report = {"material": material.name, "uv_layers": [layer.name for layer in body.data.uv_layers]}
for label, node in (("normal", normal_texture), ("roughness", roughness_texture)):
    if not node or not node.image:
        continue
    item = image_report(node.image)
    report[label] = item
    if item["size"] != [256, 256]:
        failures.append(f"{label} texture has unexpected size {item['size']}")
    if max(item["maximum"]) - min(item["minimum"]) < 0.02:
        failures.append(f"{label} texture has no meaningful variation")
    if item["horizontal_edge_delta"] > 1e-5 or item["vertical_edge_delta"] > 1e-5:
        failures.append(f"{label} texture is not tile-edge continuous")

try:
    body.data.calc_tangents(uvmap="UVMap")
    tangent_values = [component for loop in body.data.loops for component in loop.tangent]
    report["tangent_components"] = len(tangent_values)
    report["non_finite_tangent_components"] = sum(1 for value in tangent_values if not math.isfinite(value))
    if report["non_finite_tangent_components"]:
        failures.append("body tangents contain non-finite values")
finally:
    body.data.free_tangents()

print("AEVRYND_SKIN_V17_AUDIT=" + json.dumps(report))
if failures:
    raise SystemExit("; ".join(failures))
