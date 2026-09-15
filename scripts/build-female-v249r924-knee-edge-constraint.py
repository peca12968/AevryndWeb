import json
import math
import os
from pathlib import Path

import bpy
from mathutils import Matrix, Quaternion, Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = Path(os.environ.get(
    "AEVRYND_KNEE_EDGE_SOURCE",
    ASSETS / "aevrynd-female-cc0-knee-support-bones-r849.blend",
))
REVISION = os.environ.get("AEVRYND_KNEE_EDGE_REVISION", "r924")
ITERATIONS = int(os.environ.get("AEVRYND_KNEE_EDGE_ITERATIONS", "60"))
STIFFNESS = float(os.environ.get("AEVRYND_KNEE_EDGE_STIFFNESS", "0.35"))
SIGMA = float(os.environ.get("AEVRYND_KNEE_EDGE_SIGMA", "0.070"))
TARGET_DEGREES = float(os.environ.get("AEVRYND_KNEE_EDGE_TARGET_DEGREES", "75.0"))
ONSET_DEGREES = float(os.environ.get("AEVRYND_KNEE_EDGE_ONSET_DEGREES", "45.0"))
EPSILON = 0.001
ONSET_Q = math.sin(math.radians(ONSET_DEGREES / 2.0))
FULL_Q = math.sin(math.radians(TARGET_DEGREES / 2.0))
OUTPUT = ASSETS / f"aevrynd-female-cc0-knee-edge-constraint-{REVISION}.blend"
REPORT = ASSETS / f"female-v249-mainline-cc0-knee-edge-constraint-{REVISION}.build.json"
BODY = "AevryndFemaleCC0Baseline_v259"
RIG = "AevryndFemaleRig"
DEFORM_BONES = (
    "pelvis", "spine_01", "spine_02", "chest", "neck", "head",
    "clavicle.L", "upper_arm.L", "forearm.L", "hand.L",
    "clavicle.R", "upper_arm.R", "forearm.R", "hand.R",
    "thigh.L", "shin.L", "foot.L", "thigh.R", "shin.R", "foot.R",
)


def reset_pose(rig):
    for name in DEFORM_BONES:
        bone = rig.pose.bones[name]
        bone.rotation_mode = "QUATERNION"
        bone.location = (0.0, 0.0, 0.0)
        bone.rotation_quaternion = Quaternion()
        bone.scale = (1.0, 1.0, 1.0)


def evaluated_cage(body):
    bpy.context.view_layer.update()
    evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    edges = [tuple(edge.vertices) for edge in mesh.edges]
    evaluated.to_mesh_clear()
    if len(points) != len(body.data.vertices):
        raise RuntimeError(f"cage topology mismatch: {len(points)} != {len(body.data.vertices)}")
    return points, edges


def probe_axis(body, basis, axis):
    key = body.shape_key_add(name="AevryndTemporaryKneeEdgeProbe", from_mix=False)
    key.relative_key = basis
    offset = Vector(axis) * EPSILON
    for index, item in enumerate(key.data):
        item.co = basis.data[index].co + offset
    key.value = 1.0
    points, _edges = evaluated_cage(body)
    key.value = 0.0
    body.shape_key_remove(key)
    return points


def add_driver(key, side):
    curve = key.driver_add("value")
    driver = curve.driver
    driver.type = "SCRIPTED"
    variable = driver.variables.new()
    variable.name = "q"
    variable.type = "SINGLE_PROP"
    variable.targets[0].id_type = "OBJECT"
    variable.targets[0].id = bpy.data.objects[RIG]
    variable.targets[0].data_path = f'pose.bones["shin.{side}"].rotation_quaternion[1]'
    driver.expression = f"max(0,min(1,(q-{ONSET_Q:.9f})/{FULL_Q - ONSET_Q:.9f}))"
    return driver.expression


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
body = bpy.data.objects[BODY]
rig = bpy.data.objects[RIG]
basis = body.data.shape_keys.key_blocks["Basis"]
visible_group = body.vertex_groups["body"]
visible = set()
for vertex in body.data.vertices:
    try:
        if visible_group.weight(vertex.index) > 0.0:
            visible.add(vertex.index)
    except RuntimeError:
        pass
hidden_modifiers = [m for m in body.modifiers if m.type in {"MASK", "SUBSURF"} and m.show_viewport]
for modifier in hidden_modifiers:
    modifier.show_viewport = False

reset_pose(rig)
scene.frame_set(1)
rest, edges = evaluated_cage(body)
rest_lengths = [(rest[b] - rest[a]).length for a, b in edges]
created = {}
for side, sign in (("L", 1.0), ("R", -1.0)):
    reset_pose(rig)
    rig.pose.bones[f"shin.{side}"].rotation_quaternion = Quaternion((1.0, 0.0, 0.0), math.radians(TARGET_DEGREES))
    posed, posed_edges = evaluated_cage(body)
    if posed_edges != edges:
        raise RuntimeError("evaluated cage edges changed with pose")
    probes = [probe_axis(body, basis, axis) for axis in ((1, 0, 0), (0, 1, 0), (0, 0, 1))]
    joint = rig.matrix_world @ rig.data.bones[f"shin.{side}"].head_local
    weights = []
    for index, point in enumerate(rest):
        if index not in visible or sign * point.x < 0.04:
            weights.append(0.0)
            continue
        distance = (point - joint).length
        value = math.exp(-(distance * distance) / (2.0 * SIGMA * SIGMA))
        weights.append(value if value >= 0.002 else 0.0)
    target = [point.copy() for point in posed]
    for _iteration in range(ITERATIONS):
        displacements = [Vector() for _point in target]
        counts = [0.0] * len(target)
        for edge_index, (a, b) in enumerate(edges):
            wa, wb = weights[a], weights[b]
            if wa <= 0.0 and wb <= 0.0:
                continue
            vector = target[b] - target[a]
            length = vector.length
            if length <= 1e-9:
                continue
            error = length - rest_lengths[edge_index]
            correction = vector * (STIFFNESS * error / length)
            total = wa + wb
            if wa > 0.0:
                displacements[a] += correction * (wa / total)
                counts[a] += 1.0
            if wb > 0.0:
                displacements[b] -= correction * (wb / total)
                counts[b] += 1.0
        for index, count in enumerate(counts):
            if count > 0.0:
                target[index] += displacements[index] / count

    key = body.shape_key_add(name=f"KneeEdgeConstraint{TARGET_DEGREES:g}.{side}", from_mix=False)
    key.relative_key = basis
    changed = 0
    maximum_pose = maximum_basis = 0.0
    for index, weight in enumerate(weights):
        if weight <= 0.0:
            continue
        correction = target[index] - posed[index]
        if correction.length < 1e-8:
            continue
        columns = [(probes[axis][index] - posed[index]) / EPSILON for axis in range(3)]
        transform = Matrix((columns[0], columns[1], columns[2])).transposed()
        if abs(transform.determinant()) < 1e-8:
            continue
        basis_delta = transform.inverted() @ correction
        key.data[index].co = basis.data[index].co + basis_delta
        changed += 1
        maximum_pose = max(maximum_pose, correction.length)
        maximum_basis = max(maximum_basis, basis_delta.length)
    created[key.name] = {
        "vertices": changed, "maximumPoseCorrectionM": maximum_pose,
        "maximumBasisDeltaM": maximum_basis, "driver": add_driver(key, side),
    }

reset_pose(rig)
for modifier in hidden_modifiers:
    modifier.show_viewport = True
bpy.context.view_layer.update()
body["aevrynd_revision"] = f"v249{REVISION}"
body["aevrynd_knee_edge_constraint"] = "inverse-skinned localized rest-edge constraint target"
scene["aevrynd_mainline_revision"] = f"v249{REVISION}-cc0-knee-edge-constraint"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "FULL_JOINT_DEFORMATION_COLLISION_VISUAL_AUDIT_PENDING"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
report = {
    "source": str(SOURCE), "output": str(OUTPUT), "revision": REVISION,
    "iterations": ITERATIONS, "stiffness": STIFFNESS, "sigmaM": SIGMA,
    "targetDegrees": TARGET_DEGREES, "onsetDegrees": ONSET_DEGREES,
    "created": created,
    "status": "FULL_JOINT_DEFORMATION_COLLISION_VISUAL_AUDIT_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_KNEE_EDGE_CONSTRAINT=" + json.dumps(report, sort_keys=True))
