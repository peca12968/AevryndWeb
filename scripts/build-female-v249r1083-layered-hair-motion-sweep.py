"""Add root-pinned, phase-varied outward secondary motion to the r1082 groom."""
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-regional-skin-r1082-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-layered-hair-motion-r1083-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1083-layered-hair-motion-sweep.study.json"
OUT = ROOT.parent / "Temp/female-realism/v249r1083-layered-hair-motion"
HAIR = "AevryndFemaleGradedHairlineGroom_R1081"
VARIANTS = (("a-static-control", 0.0), ("b-subtle-2.8mm", 0.0028), ("c-balanced-4.5mm", 0.0045), ("d-strong-6.5mm", 0.0065))
SELECTED = "c-balanced-4.5mm"


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def math_node(nodes, operation, name):
    node = nodes.new("ShaderNodeMath")
    node.operation = operation
    node.name = name
    return node


def author_motion_attributes(hair, maximum_amplitude):
    vector = hair.data.attributes.get("aevrynd_motion_vector_r1083") or hair.data.attributes.new("aevrynd_motion_vector_r1083", "FLOAT_VECTOR", "POINT")
    phase = hair.data.attributes.get("aevrynd_motion_phase_r1083") or hair.data.attributes.new("aevrynd_motion_phase_r1083", "FLOAT", "POINT")
    amplitudes = []
    for curve_index, curve in enumerate(hair.data.curves):
        root = hair.data.points[curve.first_point_index].position
        radial = Vector((root.x, root.y + 0.010, 0.0))
        if radial.length < 1e-7:
            radial = Vector((1.0 if curve_index % 2 else -1.0, 0.0, 0.0))
        radial.normalize()
        tangent = Vector((-radial.y, radial.x, 0.0))
        family = 1.0 if math.sin(curve_index * 0.61803398875) >= 0.0 else -1.0
        direction = (radial * 0.91 + tangent * (0.09 * family)).normalized()
        curve_phase = (math.sin(curve_index * 12.9898 + 78.233) * 0.5 + 0.5) * 1.35 - 0.675
        amplitude_variation = 0.72 + 0.28 * (math.sin(curve_index * 7.13 + 1.7) * 0.5 + 0.5)
        for local in range(curve.points_length):
            factor = local / max(1, curve.points_length - 1)
            root_pin = factor ** 2.15
            amplitude = maximum_amplitude * amplitude_variation * root_pin
            index = curve.first_point_index + local
            vector.data[index].vector = direction * amplitude
            phase.data[index].value = curve_phase
            amplitudes.append(amplitude)
    return {"maximumAuthoredAmplitudeM": max(amplitudes), "meanAuthoredAmplitudeM": sum(amplitudes) / len(amplitudes), "rootPinned": True, "pointCount": len(amplitudes)}


def build_motion_group(label):
    group = bpy.data.node_groups.new(f"AevryndLayeredHairMotion_R1083_{label}", "GeometryNodeTree")
    group.interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    group.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    nodes = group.nodes
    links = group.links
    group_input = nodes.new("NodeGroupInput")
    group_output = nodes.new("NodeGroupOutput")
    set_position = nodes.new("GeometryNodeSetPosition")
    time = nodes.new("GeometryNodeInputSceneTime")
    motion = nodes.new("GeometryNodeInputNamedAttribute")
    motion.data_type = "FLOAT_VECTOR"
    motion.inputs["Name"].default_value = "aevrynd_motion_vector_r1083"
    phase = nodes.new("GeometryNodeInputNamedAttribute")
    phase.data_type = "FLOAT"
    phase.inputs["Name"].default_value = "aevrynd_motion_phase_r1083"
    frame = math_node(nodes, "SUBTRACT", "Aevrynd Frame From Rest R1083")
    frame.inputs[1].default_value = 1.0
    normalized = math_node(nodes, "DIVIDE", "Aevrynd Normalized Cycle R1083")
    normalized.inputs[1].default_value = 60.0
    envelope_phase = math_node(nodes, "MULTIPLY", "Aevrynd Settle Envelope Phase R1083")
    envelope_phase.inputs[1].default_value = math.pi
    envelope_sine = math_node(nodes, "SINE", "Aevrynd Settle Envelope Sine R1083")
    envelope = math_node(nodes, "MULTIPLY", "Aevrynd Nonnegative Settle Envelope R1083")
    oscillation_phase = math_node(nodes, "MULTIPLY", "Aevrynd Slow Sway Phase R1083")
    oscillation_phase.inputs[1].default_value = math.tau / 48.0
    phase_add = math_node(nodes, "ADD", "Aevrynd Per Clump Phase R1083")
    oscillation = math_node(nodes, "SINE", "Aevrynd Per Clump Sway R1083")
    oscillation_scale = math_node(nodes, "MULTIPLY", "Aevrynd Sway Range R1083")
    oscillation_scale.inputs[1].default_value = 0.45
    positive_bias = math_node(nodes, "ADD", "Aevrynd Outward Collision Bias R1083")
    positive_bias.inputs[1].default_value = 0.55
    temporal = math_node(nodes, "MULTIPLY", "Aevrynd Damped Outward Motion R1083")
    scaled = nodes.new("ShaderNodeVectorMath")
    scaled.operation = "SCALE"
    scaled.name = "Aevrynd Motion Vector Scale R1083"

    links.new(group_input.outputs["Geometry"], set_position.inputs["Geometry"])
    links.new(set_position.outputs["Geometry"], group_output.inputs["Geometry"])
    links.new(time.outputs["Frame"], frame.inputs[0])
    links.new(frame.outputs[0], normalized.inputs[0])
    links.new(normalized.outputs[0], envelope_phase.inputs[0])
    links.new(envelope_phase.outputs[0], envelope_sine.inputs[0])
    links.new(envelope_sine.outputs[0], envelope.inputs[0])
    links.new(envelope_sine.outputs[0], envelope.inputs[1])
    links.new(frame.outputs[0], oscillation_phase.inputs[0])
    links.new(oscillation_phase.outputs[0], phase_add.inputs[0])
    links.new(phase.outputs["Attribute"], phase_add.inputs[1])
    links.new(phase_add.outputs[0], oscillation.inputs[0])
    links.new(oscillation.outputs[0], oscillation_scale.inputs[0])
    links.new(oscillation_scale.outputs[0], positive_bias.inputs[0])
    links.new(positive_bias.outputs[0], temporal.inputs[0])
    links.new(envelope.outputs[0], temporal.inputs[1])
    links.new(motion.outputs["Attribute"], scaled.inputs[0])
    links.new(temporal.outputs[0], scaled.inputs[3])
    links.new(scaled.outputs["Vector"], set_position.inputs["Offset"])
    group["aevrynd_motion_contract"] = "root-pinned point vectors; nonnegative outward bias; rest frames 1 and 61"
    return group


def render(scene, label, frame, view):
    scene.frame_set(frame)
    camera = scene.camera
    if view == "front":
        camera.location, target, camera.data.lens = (0.0, -0.72, 1.445), (0.0, -0.025, 1.445), 88
    elif view == "three-quarter":
        camera.location, target, camera.data.lens = (0.45, -0.62, 1.46), (0.0, -0.015, 1.445), 88
    else:
        camera.location, target, camera.data.lens = (0.0, 0.72, 1.445), (0.0, 0.025, 1.445), 88
    look_at(camera, target)
    scene.render.resolution_x = scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    path = OUT / f"{label}-f{frame:02d}-{view}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return str(path)


OUT.mkdir(parents=True, exist_ok=True)
variants = []
for label, amplitude in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0
    hair = bpy.data.objects[HAIR]
    before = {"objects": len(bpy.data.objects), "curves": len(hair.data.curves), "points": len(hair.data.points), "modifiers": len(hair.modifiers), "materialSlots": len(hair.data.materials)}
    if amplitude > 0.0:
        attributes = author_motion_attributes(hair, amplitude)
        group = build_motion_group(label)
        modifier = hair.modifiers.new("Aevrynd Layered Hair Motion R1083", "NODES")
        modifier.node_group = group
    else:
        attributes = {"maximumAuthoredAmplitudeM": 0.0, "meanAuthoredAmplitudeM": 0.0, "rootPinned": True, "pointCount": len(hair.data.points)}
        group = None
    renders = [render(scene, label, frame, view) for frame in (1, 31, 61) for view in ("front", "three-quarter", "back")]
    after = {"objects": len(bpy.data.objects), "curves": len(hair.data.curves), "points": len(hair.data.points), "modifiers": len(hair.modifiers), "materialSlots": len(hair.data.materials)}
    variants.append({"label": label, "maximumAmplitudeM": amplitude, "attributes": attributes, "nodeGroup": group.name if group else None, "before": before, "after": after, "renders": renders, "status": "MOTION_COLLISION_REVIEW_REQUIRED"})
    if label == SELECTED:
        hair["aevrynd_motion_revision"] = "v249r1083-layered-hair-motion"
        hair["aevrynd_motion_rest_frames"] = "1|61"
        hair["aevrynd_root_constraint"] = "authored point-vector t^2.15 falloff"
        scene["aevrynd_release_state"] = "MOTION_COLLISION_REVIEW_PENDING"
        scene["aevrynd_website_promotion"] = "forbidden"
        scene.frame_set(1)
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "revision": "v249r1083-layered-hair-motion-sweep",
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "method": "author point-domain root-pinned motion vectors with per-clump phase and evaluate them through a nonnegative outward-biased damped 60-frame Geometry Nodes cycle",
    "variants": variants,
    "selectedVariant": SELECTED,
    "newObjects": 0,
    "materialSlotDelta": 0,
    "websitePromotionApproved": False,
    "candidateStatus": "MOTION_COLLISION_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1083_HAIR_MOTION=" + json.dumps({"selected": SELECTED, "variants": [{"label": item["label"], "attributes": item["attributes"], "after": item["after"]} for item in variants]}, sort_keys=True))
