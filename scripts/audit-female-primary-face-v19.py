import json
import math
import sys

import bpy


def input_path():
    if "--" not in sys.argv:
        raise SystemExit("usage: blender --background --python audit-female-primary-face-v19.py -- model.blend")
    values = sys.argv[sys.argv.index("--") + 1:]
    if len(values) != 1:
        raise SystemExit("expected one Blender file")
    return values[0]


bpy.ops.wm.open_mainfile(filepath=input_path())
scene = bpy.context.scene
body = bpy.data.objects["AevryndFemaleBodyBase"]
modifier = body.modifiers.get("Aevrynd Face Primary Smoothing")
group = body.vertex_groups.get("AevryndFacePrimarySmooth")
failures = []
if bpy.data.objects.get("HairFoundationV19"):
    failures.append("rejected hair-foundation experiment leaked into v19")
if body.get("aevrynd_face_revision") != 19 or scene.get("aevrynd_face_revision") != 19:
    failures.append("face revision is not 19")
changed = int(body.get("aevrynd_primary_face_vertices", 0))
maximum_delta = float(body.get("aevrynd_primary_face_max_delta_m", 0.0))
if changed < 2800:
    failures.append(f"too few primary-form vertices changed: {changed}")
if not 0.0035 <= maximum_delta <= 0.0050:
    failures.append(f"maximum primary-form delta outside guarded range: {maximum_delta}")
if body.modifiers.get("Aevrynd Face Planar Smoothing"):
    failures.append("v18 smoothing modifier was not replaced")
if not modifier or modifier.type != "LAPLACIANSMOOTH":
    failures.append("primary face smoothing modifier is missing")
if not group:
    failures.append("primary face smoothing group is missing")

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
    if weighted < 1000:
        failures.append(f"too few primary smoothing vertices: {weighted}")
if modifier:
    armature_index = next(index for index, item in enumerate(body.modifiers) if item.type == "ARMATURE")
    if list(body.modifiers).index(modifier) >= armature_index:
        failures.append("primary smoothing must run before armature deformation")
    if modifier.iterations != 4 or not modifier.use_volume_preserve:
        failures.append("primary smoothing settings regressed")

frames = {}
for frame in (1, 20):
    scene.frame_set(frame)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    non_finite = 0
    for vertex in mesh.vertices:
        point = evaluated.matrix_world @ vertex.co
        if not all(math.isfinite(value) for value in point):
            non_finite += 1
    frames[str(frame)] = {"vertices": len(mesh.vertices), "non_finite_positions": non_finite}
    evaluated.to_mesh_clear()
    if non_finite:
        failures.append(f"frame {frame} has non-finite body positions")

report = {
    "changed_vertices": changed,
    "maximum_primary_delta_m": maximum_delta,
    "smoothing_vertices": weighted,
    "maximum_smoothing_weight": maximum_weight,
    "modifier_iterations": modifier.iterations if modifier else None,
    "volume_preserve": modifier.use_volume_preserve if modifier else None,
    "frames": frames,
}
print("AEVRYND_PRIMARY_FACE_V19_AUDIT=" + json.dumps(report))
if failures:
    raise SystemExit("; ".join(failures))
