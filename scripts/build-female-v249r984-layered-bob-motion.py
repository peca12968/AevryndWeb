"""Add root-pinned, outward-biased secondary motion to the r981 groom."""

import json
import math
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-coherent-clump-waves-r981.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-layered-bob-motion-r984.blend"
REPORT = ASSETS / "female-v249-mainline-cc0-layered-bob-motion-r984.build-report.json"
AUDIT = ASSETS / "female-v249-mainline-cc0-layered-bob-motion-r984.motion-collision-audit.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r984-layered-bob-motion"
BODY = "AevryndFemaleCC0Baseline_v259"
HAIR = "AevryndFemaleCoherentClumpGroom_R981"
SCALP = "AevryndFemaleTargetScalp_R976"
FRAMES = (1, 16, 31, 46, 61)


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def smoothstep(value):
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def math_node(nodes, operation, label=None):
    node = nodes.new("ShaderNodeMath")
    node.operation = operation
    if label:
        node.label = label
    return node


def build_motion_group():
    group = bpy.data.node_groups.new("AevryndLayeredBobMotion_R984", "GeometryNodeTree")
    group.interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    group.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    nodes = group.nodes
    links = group.links
    group_input = nodes.new("NodeGroupInput")
    group_output = nodes.new("NodeGroupOutput")
    set_position = nodes.new("GeometryNodeSetPosition")
    scene_time = nodes.new("GeometryNodeInputSceneTime")
    spline_parameter = nodes.new("GeometryNodeSplineParameter")
    position = nodes.new("GeometryNodeInputPosition")
    separate = nodes.new("ShaderNodeSeparateXYZ")

    frame_minus_one = math_node(nodes, "SUBTRACT", "rest at frame 1")
    frame_minus_one.inputs[1].default_value = 1.0
    normalized = math_node(nodes, "DIVIDE")
    normalized.inputs[1].default_value = 60.0
    envelope_phase = math_node(nodes, "MULTIPLY")
    envelope_phase.inputs[1].default_value = math.pi
    envelope_sine = math_node(nodes, "SINE")
    envelope = math_node(nodes, "MULTIPLY", "rest again at frame 61")

    factor_squared = math_node(nodes, "MULTIPLY", "root pinned")
    weight = math_node(nodes, "MULTIPLY")
    oscillation_phase = math_node(nodes, "MULTIPLY")
    oscillation_phase.inputs[1].default_value = 0.19
    oscillation_x = math_node(nodes, "SINE")
    phase_y = math_node(nodes, "ADD")
    phase_y.inputs[1].default_value = 1.20
    oscillation_y = math_node(nodes, "SINE")
    weighted_x = math_node(nodes, "MULTIPLY")
    weighted_y = math_node(nodes, "MULTIPLY")
    x_amount = math_node(nodes, "MULTIPLY")
    x_amount.inputs[1].default_value = 0.0025
    y_amount = math_node(nodes, "MULTIPLY")
    y_amount.inputs[1].default_value = 0.0012
    oscillation_vector = nodes.new("ShaderNodeCombineXYZ")

    shifted_y = math_node(nodes, "ADD")
    shifted_y.inputs[1].default_value = 0.058
    radial_xy = nodes.new("ShaderNodeCombineXYZ")
    radial_normalize = nodes.new("ShaderNodeVectorMath")
    radial_normalize.operation = "NORMALIZE"
    outward_amount = math_node(nodes, "MULTIPLY")
    outward_amount.inputs[1].default_value = 0.0040
    outward_scale = nodes.new("ShaderNodeVectorMath")
    outward_scale.operation = "SCALE"
    combined = nodes.new("ShaderNodeVectorMath")
    combined.operation = "ADD"

    links.new(group_input.outputs["Geometry"], set_position.inputs["Geometry"])
    links.new(set_position.outputs["Geometry"], group_output.inputs["Geometry"])
    links.new(scene_time.outputs["Frame"], frame_minus_one.inputs[0])
    links.new(frame_minus_one.outputs[0], normalized.inputs[0])
    links.new(normalized.outputs[0], envelope_phase.inputs[0])
    links.new(envelope_phase.outputs[0], envelope_sine.inputs[0])
    links.new(envelope_sine.outputs[0], envelope.inputs[0])
    links.new(envelope_sine.outputs[0], envelope.inputs[1])
    links.new(spline_parameter.outputs["Factor"], factor_squared.inputs[0])
    links.new(spline_parameter.outputs["Factor"], factor_squared.inputs[1])
    links.new(factor_squared.outputs[0], weight.inputs[0])
    links.new(envelope.outputs[0], weight.inputs[1])
    links.new(frame_minus_one.outputs[0], oscillation_phase.inputs[0])
    links.new(oscillation_phase.outputs[0], oscillation_x.inputs[0])
    links.new(oscillation_phase.outputs[0], phase_y.inputs[0])
    links.new(phase_y.outputs[0], oscillation_y.inputs[0])
    links.new(oscillation_x.outputs[0], weighted_x.inputs[0])
    links.new(weight.outputs[0], weighted_x.inputs[1])
    links.new(oscillation_y.outputs[0], weighted_y.inputs[0])
    links.new(weight.outputs[0], weighted_y.inputs[1])
    links.new(weighted_x.outputs[0], x_amount.inputs[0])
    links.new(weighted_y.outputs[0], y_amount.inputs[0])
    links.new(x_amount.outputs[0], oscillation_vector.inputs["X"])
    links.new(y_amount.outputs[0], oscillation_vector.inputs["Y"])
    links.new(position.outputs["Position"], separate.inputs["Vector"])
    links.new(separate.outputs["X"], radial_xy.inputs["X"])
    links.new(separate.outputs["Y"], shifted_y.inputs[0])
    links.new(shifted_y.outputs[0], radial_xy.inputs["Y"])
    links.new(radial_xy.outputs["Vector"], radial_normalize.inputs[0])
    links.new(weight.outputs[0], outward_amount.inputs[0])
    links.new(radial_normalize.outputs["Vector"], outward_scale.inputs[0])
    links.new(outward_amount.outputs[0], outward_scale.inputs[3])
    links.new(oscillation_vector.outputs["Vector"], combined.inputs[0])
    links.new(outward_scale.outputs["Vector"], combined.inputs[1])
    links.new(combined.outputs["Vector"], set_position.inputs["Offset"])
    group["aevrynd_model"] = "root-pinned damped sway proxy with outward collision bias"
    group["aevrynd_rest_frames"] = "1|61"
    group["aevrynd_peak_frame"] = 31
    return group


def bind_to_head(obj, rig):
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = world
    obj["aevrynd_head_binding"] = True


def shape_layered_bob(hair):
    if len(hair.data.curves) % 14:
        raise RuntimeError("Unexpected r981 guide grouping")
    matrix = hair.matrix_world
    inverse = matrix.inverted()
    changed = 0
    maximum_raise = 0.0
    guide_count = len(hair.data.curves) // 14
    for guide_index in range(guide_count):
        guide_curve = hair.data.curves[guide_index * 14]
        root = matrix @ hair.data.points[guide_curve.first_point_index].position
        side = -1.0 if root.x < 0.0 else 1.0
        tier = (guide_index * 7 + int(abs(root.x) * 1000)) % 5
        if root.y < -0.090:
            target_tip_z = 1.315 + tier * 0.011
        elif root.y > 0.005:
            target_tip_z = 1.345 + tier * 0.010
        else:
            target_tip_z = 1.330 + tier * 0.010
        for follower in range(14):
            curve = hair.data.curves[guide_index * 14 + follower]
            tip_index = curve.first_point_index + curve.points_length - 1
            tip = matrix @ hair.data.points[tip_index].position
            follower_target = target_tip_z + (follower % 4 - 1.5) * 0.003
            raise_amount = max(0.0, follower_target - tip.z)
            maximum_raise = max(maximum_raise, raise_amount)
            for local in range(curve.points_length):
                index = curve.first_point_index + local
                t = local / max(1, curve.points_length - 1)
                point = matrix @ hair.data.points[index].position
                tip_weight = smoothstep((t - 0.44) / 0.56)
                point.z += raise_amount * tip_weight
                point.x += side * (0.004 + 0.010 * smoothstep((t - 0.58) / 0.42)) * tip_weight
                if root.y > 0.005:
                    point.y += 0.016 * tip_weight
                elif root.y < -0.090:
                    point.y -= 0.006 * tip_weight
                hair.data.points[index].position = inverse @ point
                changed += 1
    return changed, maximum_raise


def body_tree(body):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    polygons = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, polygons, all_triangles=False)


def repair_static_clearance(hair, tree, clearance=0.0016):
    matrix = hair.matrix_world
    inverse = matrix.inverted()
    corrected = 0
    maximum = 0.0
    for _pass in range(2):
        for point in hair.data.points:
            world = matrix @ point.position
            hit = tree.find_nearest(world)
            if hit is None or hit[1] is None:
                continue
            nearest, normal, _face, _distance = hit
            normal = normal.normalized()
            signed = (world - nearest).dot(normal)
            if signed >= clearance:
                continue
            delta = normal * (clearance - signed)
            point.position = inverse @ (world + delta)
            corrected += 1
            maximum = max(maximum, delta.length)
    return corrected, maximum


def evaluated_points(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    evaluated = obj.evaluated_get(depsgraph)
    local = [point.position.copy() for point in evaluated.data.points]
    return local, [evaluated.matrix_world @ point for point in local]


def percentile(values, fraction):
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int((len(ordered) - 1) * fraction))]


def audit(scene, body, hair):
    snapshots = {}
    collisions = {}
    failures = []
    for frame in FRAMES:
        scene.frame_set(frame)
        local, world = evaluated_points(hair)
        snapshots[frame] = local
        tree = body_tree(body)
        signed = []
        for point in world:
            hit = tree.find_nearest(point, 0.12)
            if hit is not None and hit[1] is not None:
                signed.append((point - hit[0]).dot(hit[1].normalized()))
        penetrating = sum(value < -1e-7 for value in signed)
        collisions[str(frame)] = {
            "sampleCount": len(signed),
            "minimumSignedM": min(signed),
            "penetratingPointCount": penetrating,
        }
        if penetrating:
            failures.append({"frame": frame, "penetratingPointCount": penetrating})
    rest = snapshots[1]
    peak = snapshots[31]
    settled = snapshots[61]
    peak_delta = [(b - a).length for a, b in zip(rest, peak)]
    settle_delta = [(b - a).length for a, b in zip(rest, settled)]
    root_indices = [curve.first_point_index for curve in hair.data.curves]
    roots = [peak_delta[index] for index in root_indices]
    motion = {
        "peakMeanM": sum(peak_delta) / len(peak_delta),
        "peakP95M": percentile(peak_delta, 0.95),
        "peakMaximumM": max(peak_delta),
        "rootMaximumM": max(roots),
        "settleMaximumM": max(settle_delta),
    }
    if motion["peakP95M"] < 0.002:
        failures.append({"motion": "peak P95 below 2mm", "valueM": motion["peakP95M"]})
    if motion["peakMaximumM"] > 0.020:
        failures.append({"motion": "peak maximum above 20mm", "valueM": motion["peakMaximumM"]})
    if motion["rootMaximumM"] > 0.00002:
        failures.append({"motion": "root drift above 0.02mm", "valueM": motion["rootMaximumM"]})
    if motion["settleMaximumM"] > 0.00005:
        failures.append({"motion": "frame 61 not settled", "valueM": motion["settleMaximumM"]})
    return collisions, motion, failures


def look_at(camera, target):
    from mathutils import Vector
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, camera, frame, name, location, target, lens):
    scene.frame_set(frame)
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
hair = bpy.data.objects[HAIR]
rig = bpy.data.objects["AevryndFemaleRig"]
shaped_points, maximum_bob_raise = shape_layered_bob(hair)
static_corrected, maximum_static_correction = repair_static_clearance(hair, body_tree(bpy.data.objects[BODY]))
bind_to_head(hair, rig)
bind_to_head(bpy.data.objects[SCALP], rig)
group = build_motion_group()
modifier = hair.modifiers.new("Aevrynd Layered Bob Motion R984", "NODES")
modifier.node_group = group
hair["aevrynd_revision"] = "v249r984"
hair["aevrynd_secondary_motion"] = True
hair["aevrynd_root_constraint"] = "spline factor squared"
hair["aevrynd_motion_rest_frames"] = "1|61"
scene["aevrynd_mainline_revision"] = "v249r984-layered-bob-motion"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "DYNAMIC_HAIR_AUDIT_PENDING"
collisions, motion, failures = audit(scene, bpy.data.objects[BODY], hair)
AUDIT.write_text(json.dumps({
    "source": str(SOURCE),
    "model": str(OUTPUT),
    "frames": list(FRAMES),
    "collision": collisions,
    "motion": motion,
    "failures": failures,
    "status": "PASS" if not failures else "FAIL",
}, indent=2), encoding="utf-8")
scene["aevrynd_release_state"] = "DYNAMIC_HAIR_TECHNICAL_PASS" if not failures else "DYNAMIC_HAIR_REJECTED"
scene["aevrynd_website_promotion"] = "forbidden pending visual and runtime gates"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
scene.render.resolution_x = scene.render.resolution_y = 900
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects.get("Aevrynd Review Camera") or scene.camera
scene.camera = camera
for args in (
    (1, "01-rest-front", (0.0, -0.68, 1.49), (0.0, -0.055, 1.48), 88),
    (31, "02-peak-front", (0.0, -0.68, 1.49), (0.0, -0.055, 1.48), 88),
    (1, "03-rest-three-quarter", (0.42, -0.58, 1.51), (0.0, -0.045, 1.48), 88),
    (31, "04-peak-three-quarter", (0.42, -0.58, 1.51), (0.0, -0.045, 1.48), 88),
    (1, "05-rest-back", (0.0, 0.76, 1.50), (0.0, -0.01, 1.48), 86),
    (31, "06-peak-back", (0.0, 0.76, 1.50), (0.0, -0.01, 1.48), 86),
):
    render(scene, camera, *args)
scene.frame_set(1)
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "audit": str(AUDIT),
    "frames": list(FRAMES),
    "nodeGroup": group.name,
    "shapedPointCount": shaped_points,
    "maximumBobTipRaiseM": maximum_bob_raise,
    "staticCollisionCorrectedOperations": static_corrected,
    "maximumStaticCollisionCorrectionM": maximum_static_correction,
    "motion": motion,
    "failures": failures,
    "auditStatus": "PASS" if not failures else "FAIL",
    "ownedAssetOnly": True,
    "runtimeDependency": "none; native Blender Geometry Nodes authored in project",
    "websitePromotionApproved": False,
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_R984_LAYERED_BOB_MOTION=" + json.dumps(report, sort_keys=True))
if failures:
    raise SystemExit(2)
