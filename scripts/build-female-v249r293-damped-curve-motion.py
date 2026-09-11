import json
import math
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-curve-clearance-r292.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-damped-curve-motion-r293.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-damped-curve-motion-r293.build-report.json"
AUDIT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-damped-curve-motion-r293.audit.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r293-damped-curve-motion"
BODY = "AevryndFemaleBody_CC0_R249"
LAYERS = (
    ("AevryndFemalePrimaryClumps_R264", 1.00),
    ("AevryndFemaleSecondaryFill_R264", 0.86),
    ("AevryndFemaleFlyaways_R264", 1.28),
)
POINTS = 24
FRAMES = (1, 33, 61)


def math_node(nodes, operation, label=None):
    node = nodes.new("ShaderNodeMath")
    node.operation = operation
    if label:
        node.label = label
    return node


def build_motion_group(name, scale):
    group = bpy.data.node_groups.new(name, "GeometryNodeTree")
    group.interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    group.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    nodes = group.nodes
    links = group.links
    group_input = nodes.new("NodeGroupInput")
    group_output = nodes.new("NodeGroupOutput")
    set_position = nodes.new("GeometryNodeSetPosition")
    scene_time = nodes.new("GeometryNodeInputSceneTime")
    spline_parameter = nodes.new("GeometryNodeSplineParameter")

    frame_minus_one = math_node(nodes, "SUBTRACT", "animation starts at rest")
    frame_minus_one.inputs[1].default_value = 1.0
    normalized_time = math_node(nodes, "DIVIDE")
    normalized_time.inputs[1].default_value = 60.0
    envelope_phase = math_node(nodes, "MULTIPLY")
    envelope_phase.inputs[1].default_value = math.pi
    envelope_sine = math_node(nodes, "SINE")
    envelope_squared = math_node(nodes, "MULTIPLY", "zero at frames 1 and 61")

    oscillation_phase = math_node(nodes, "MULTIPLY")
    oscillation_phase.inputs[1].default_value = 0.205
    oscillation_x = math_node(nodes, "SINE")
    phase_y = math_node(nodes, "ADD")
    phase_y.inputs[1].default_value = 1.35
    oscillation_y = math_node(nodes, "SINE")

    factor_squared = math_node(nodes, "MULTIPLY", "root pinned; tip receives full motion")
    common_weight = math_node(nodes, "MULTIPLY")
    x_osc_weight = math_node(nodes, "MULTIPLY")
    y_osc_weight = math_node(nodes, "MULTIPLY")
    x_amplitude = math_node(nodes, "MULTIPLY")
    x_amplitude.inputs[1].default_value = 0.0052 * scale
    y_amplitude = math_node(nodes, "MULTIPLY")
    y_amplitude.inputs[1].default_value = 0.0026 * scale
    combine = nodes.new("ShaderNodeCombineXYZ")

    links.new(group_input.outputs["Geometry"], set_position.inputs["Geometry"])
    links.new(set_position.outputs["Geometry"], group_output.inputs["Geometry"])
    links.new(scene_time.outputs["Frame"], frame_minus_one.inputs[0])
    links.new(frame_minus_one.outputs[0], normalized_time.inputs[0])
    links.new(normalized_time.outputs[0], envelope_phase.inputs[0])
    links.new(envelope_phase.outputs[0], envelope_sine.inputs[0])
    links.new(envelope_sine.outputs[0], envelope_squared.inputs[0])
    links.new(envelope_sine.outputs[0], envelope_squared.inputs[1])
    links.new(frame_minus_one.outputs[0], oscillation_phase.inputs[0])
    links.new(oscillation_phase.outputs[0], oscillation_x.inputs[0])
    links.new(oscillation_phase.outputs[0], phase_y.inputs[0])
    links.new(phase_y.outputs[0], oscillation_y.inputs[0])
    links.new(spline_parameter.outputs["Factor"], factor_squared.inputs[0])
    links.new(spline_parameter.outputs["Factor"], factor_squared.inputs[1])
    links.new(envelope_squared.outputs[0], common_weight.inputs[0])
    links.new(factor_squared.outputs[0], common_weight.inputs[1])
    links.new(oscillation_x.outputs[0], x_osc_weight.inputs[0])
    links.new(common_weight.outputs[0], x_osc_weight.inputs[1])
    links.new(oscillation_y.outputs[0], y_osc_weight.inputs[0])
    links.new(common_weight.outputs[0], y_osc_weight.inputs[1])
    links.new(x_osc_weight.outputs[0], x_amplitude.inputs[0])
    links.new(y_osc_weight.outputs[0], y_amplitude.inputs[0])
    links.new(x_amplitude.outputs[0], combine.inputs["X"])
    links.new(y_amplitude.outputs[0], combine.inputs["Y"])
    links.new(combine.outputs["Vector"], set_position.inputs["Offset"])
    group["aevrynd_model"] = "damped spring response proxy"
    group["aevrynd_root_constraint"] = "spline_factor_squared"
    group["aevrynd_rest_frames"] = "1|61"
    group["aevrynd_peak_window"] = "around frame 33"
    return group


def body_tree(body):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, faces, all_triangles=False)


def evaluated_points(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    evaluated = obj.evaluated_get(depsgraph)
    return [evaluated.matrix_world @ point.position for point in evaluated.data.points]


def percentile(values, fraction):
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int((len(ordered) - 1) * fraction))]


def run_audit(scene, body, objects):
    snapshots = {}
    collision = {}
    failures = []
    for frame in FRAMES:
        scene.frame_set(frame)
        tree = body_tree(body)
        snapshots[frame] = {}
        collision[str(frame)] = {}
        for obj in objects:
            points = evaluated_points(obj)
            snapshots[frame][obj.name] = points
            values = []
            for world in points:
                hit = tree.find_nearest(world, 0.20)
                if hit is not None and hit[1] is not None:
                    values.append((world - hit[0]).dot(hit[1].normalized()))
            penetrating = sum(value < -1e-7 for value in values)
            collision[str(frame)][obj.name] = {
                "samples": len(values), "minimumSignedM": min(values), "penetratingVertices": penetrating,
            }
            if penetrating:
                failures.append({"frame": frame, "object": obj.name, "penetratingVertices": penetrating})
    motion = {}
    all_peak = []
    all_settle = []
    all_roots = []
    for obj in objects:
        rest = snapshots[1][obj.name]
        peak = snapshots[33][obj.name]
        settled = snapshots[61][obj.name]
        peak_delta = [(b - a).length for a, b in zip(rest, peak)]
        settle_delta = [(b - a).length for a, b in zip(rest, settled)]
        root_delta = [peak_delta[index] for index in range(0, len(peak_delta), POINTS)]
        all_peak.extend(peak_delta)
        all_settle.extend(settle_delta)
        all_roots.extend(root_delta)
        motion[obj.name] = {
            "peakMeanM": sum(peak_delta) / len(peak_delta), "peakP95M": percentile(peak_delta, 0.95),
            "peakMaximumM": max(peak_delta), "rootMaximumM": max(root_delta),
            "settleMaximumM": max(settle_delta),
        }
    summary = {
        "peakMeanM": sum(all_peak) / len(all_peak), "peakP95M": percentile(all_peak, 0.95),
        "peakMaximumM": max(all_peak), "rootMaximumM": max(all_roots),
        "settleMaximumM": max(all_settle),
    }
    if summary["peakP95M"] < 0.0020:
        failures.append({"motion": "peak P95 below 2mm", "valueM": summary["peakP95M"]})
    if summary["rootMaximumM"] > 0.00002:
        failures.append({"motion": "root drift above 0.02mm", "valueM": summary["rootMaximumM"]})
    if summary["settleMaximumM"] > 0.00005:
        failures.append({"motion": "frame 61 not settled", "valueM": summary["settleMaximumM"]})
    return collision, motion, summary, failures


def look_at(obj, target):
    from mathutils import Vector
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, frame, name, location):
    scene = bpy.context.scene
    scene.frame_set(frame)
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    camera.location = location
    camera.data.lens = 82
    look_at(camera, (0.0, 0.0, 1.56))
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
objects = []
groups = []
for object_name, scale in LAYERS:
    obj = bpy.data.objects[object_name]
    group = build_motion_group(f"AevryndDampedCurveMotion_{object_name}_R293", scale)
    modifier = obj.modifiers.new("Aevrynd Damped Secondary Motion R293", "NODES")
    modifier.node_group = group
    obj["aevrynd_revision"] = "v249r293"
    obj["aevrynd_motion"] = "root-pinned damped spring response; authored preview"
    objects.append(obj)
    groups.append(group.name)
scene["aevrynd_mainline_revision"] = "v249r293-damped-curve-motion"
scene["aevrynd_release_state"] = "CURVE_MOTION_AUDIT_PENDING"
collision, motion, motion_summary, failures = run_audit(scene, bpy.data.objects[BODY], objects)
AUDIT.write_text(json.dumps({
    "model": str(OUTPUT), "frames": list(FRAMES), "collision": collision,
    "motion": motion, "motionSummary": motion_summary, "failures": failures,
    "status": "PASS" if not failures else "FAIL",
}, indent=2), encoding="utf-8")
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
for frame, name, location in (
    (1, "front-f01", (0.0, -0.90, 1.59)), (33, "front-f33", (0.0, -0.90, 1.59)),
    (1, "left-f01", (-0.72, -0.55, 1.59)), (1, "right-f01", (0.72, -0.55, 1.59)),
    (1, "back-f01", (0.0, 0.90, 1.59)), (33, "back-f33", (0.0, 0.90, 1.59)),
):
    render(camera, frame, name, location)
scene.frame_set(1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE), "output": str(OUTPUT), "layers": [name for name, _ in LAYERS],
    "nodeGroups": groups, "audit": str(AUDIT), "auditStatus": "PASS" if not failures else "FAIL",
    "motionSummary": motion_summary, "failures": failures,
    "runtimeCardProxyPreserved": "AevryndFemaleRuntimeHairCards_R276",
    "ownedAssetOnly": True, "renderDirectory": str(RENDER_DIR),
    "status": "VISUAL_REVIEW_PENDING" if not failures else "FAIL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R293_DAMPED_CURVE_MOTION=" + json.dumps(report, sort_keys=True))
if failures:
    raise SystemExit(2)
