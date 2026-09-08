import json
import math
import sys

import bpy


def input_path():
    if "--" not in sys.argv:
        raise SystemExit("usage: blender --background --python audit-female-identity-v18.py -- model.blend")
    values = sys.argv[sys.argv.index("--") + 1:]
    if len(values) != 1:
        raise SystemExit("expected one Blender file")
    return values[0]


bpy.ops.wm.open_mainfile(filepath=input_path())
scene = bpy.context.scene
body = bpy.data.objects["AevryndFemaleBodyBase"]
modifier = body.modifiers.get("Aevrynd Face Planar Smoothing")
group = body.vertex_groups.get("AevryndFacePlanarSmooth")
failures = []
if body.get("aevrynd_face_revision") != 18:
    failures.append("face revision is not 18")
changed = int(body.get("aevrynd_identity_vertices", 0))
maximum_delta = float(body.get("aevrynd_identity_max_delta_m", 0.0))
if changed < 1500:
    failures.append(f"too few identity vertices changed: {changed}")
if not 0.0006 <= maximum_delta <= 0.0010:
    failures.append(f"identity maximum delta outside guarded range: {maximum_delta}")
if not modifier or modifier.type != "LAPLACIANSMOOTH":
    failures.append("face planar smoothing modifier is missing")
if not group:
    failures.append("face smoothing vertex group is missing")

weighted = 0
maximum_weight = 0.0
if group:
    for vertex in body.data.vertices:
        try:
            weight = group.weight(vertex.index)
        except RuntimeError:
            continue
        weighted += 1
        maximum_weight = max(maximum_weight, weight)
    if weighted < 900:
        failures.append(f"too few smoothing vertices: {weighted}")
if modifier:
    armature_index = next(index for index, item in enumerate(body.modifiers) if item.type == "ARMATURE")
    smoothing_index = list(body.modifiers).index(modifier)
    if smoothing_index >= armature_index:
        failures.append("face smoothing must run before the armature")
    if modifier.iterations != 2 or not modifier.use_volume_preserve:
        failures.append("face smoothing settings regressed")

frame_report = {}
for frame in (1, 20):
    scene.frame_set(frame)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    positions = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    non_finite = sum(1 for point in positions if not all(math.isfinite(value) for value in point))
    frame_report[str(frame)] = {"vertices": len(positions), "non_finite_positions": non_finite}
    if non_finite:
        failures.append(f"frame {frame} has non-finite body positions")
    evaluated.to_mesh_clear()

report = {
    "changed_vertices": changed,
    "maximum_identity_delta_m": maximum_delta,
    "smoothing_vertices": weighted,
    "maximum_smoothing_weight": maximum_weight,
    "modifier_iterations": modifier.iterations if modifier else None,
    "volume_preserve": modifier.use_volume_preserve if modifier else None,
    "frames": frame_report,
}
print("AEVRYND_IDENTITY_V18_AUDIT=" + json.dumps(report))
if failures:
    raise SystemExit("; ".join(failures))
