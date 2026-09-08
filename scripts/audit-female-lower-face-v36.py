import json
import math
import sys

import bpy


def inputs():
    values = sys.argv[sys.argv.index("--") + 1:]
    if len(values) != 2:
        raise SystemExit("expected baseline.blend candidate.blend")
    return values


def snapshot(path):
    bpy.ops.wm.open_mainfile(filepath=path)
    objects = {}
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        objects[obj.name] = {
            "vertices": len(obj.data.vertices),
            "faces": len(obj.data.polygons),
            "positions": [tuple(obj.matrix_world @ vertex.co) for vertex in obj.data.vertices],
        }
    rig = bpy.data.objects["AevryndFemaleRig"]
    body = bpy.data.objects["AevryndFemaleBodyBase"]
    return {
        "objects": objects,
        "bones": [bone.name for bone in rig.data.bones],
        "actions": sorted(action.name for action in bpy.data.actions),
        "face_revision": body.get("aevrynd_face_revision"),
        "scene_revision": bpy.context.scene.get("aevrynd_face_revision"),
        "reported_changed": body.get("aevrynd_lower_face_vertices"),
        "reported_maximum": body.get("aevrynd_lower_face_max_delta_m"),
    }


baseline_path, candidate_path = inputs()
baseline = snapshot(baseline_path)
candidate = snapshot(candidate_path)
failures = []
if set(baseline["objects"]) != set(candidate["objects"]):
    failures.append("mesh object set changed")
if baseline["bones"] != candidate["bones"] or len(candidate["bones"]) != 21:
    failures.append("rig bone set changed")
if baseline["actions"] != candidate["actions"]:
    failures.append("action set changed")
if candidate["face_revision"] != 36 or candidate["scene_revision"] != 36:
    failures.append("face revision is not 36")

changed_objects = []
body_changed = 0
body_outside = 0
body_maximum = 0.0
for name, before in baseline["objects"].items():
    after = candidate["objects"][name]
    if before["vertices"] != after["vertices"] or before["faces"] != after["faces"]:
        failures.append(f"{name} topology changed")
    maximum = 0.0
    for source, target in zip(before["positions"], after["positions"]):
        delta = math.dist(source, target)
        maximum = max(maximum, delta)
        if name == "AevryndFemaleBodyBase" and delta > 1e-7:
            body_changed += 1
            body_maximum = max(body_maximum, delta)
            x, y, z = source
            if y > 0.015 or abs(x) > 0.105 or not (1.425 <= z <= 1.590):
                body_outside += 1
    if maximum > 1e-7:
        changed_objects.append(name)
if changed_objects != ["AevryndFemaleBodyBase"]:
    failures.append(f"unexpected changed mesh objects: {changed_objects}")
if not 1800 <= body_changed <= 1950:
    failures.append(f"unexpected changed body vertex count: {body_changed}")
if body_outside:
    failures.append(f"{body_outside} vertices changed outside guarded lower-face region")
if not 0.0029 <= body_maximum <= 0.0031:
    failures.append(f"maximum body delta is outside 3 mm guard: {body_maximum}")
if candidate["reported_changed"] != body_changed:
    failures.append("reported changed-vertex count does not match geometry")
if abs(candidate["reported_maximum"] - body_maximum) > 1e-7:
    failures.append("reported maximum delta does not match geometry")

non_finite = sum(
    not all(math.isfinite(value) for value in position)
    for obj in candidate["objects"].values() for position in obj["positions"]
)
if non_finite:
    failures.append(f"candidate contains {non_finite} non-finite vertices")

report = {
    "body_changed_vertices": body_changed,
    "body_maximum_delta_m": body_maximum,
    "body_changes_outside_guarded_region": body_outside,
    "changed_mesh_objects": changed_objects,
    "unchanged_mesh_objects": len(candidate["objects"]) - len(changed_objects),
    "mesh_objects": len(candidate["objects"]),
    "bones": len(candidate["bones"]),
    "actions": len(candidate["actions"]),
    "non_finite_vertices": non_finite,
}
print("AEVRYND_LOWER_FACE_V36_AUDIT=" + json.dumps(report))
if failures:
    raise SystemExit("; ".join(failures))
