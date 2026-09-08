import json
import math
import sys

import bpy


def inputs():
    if "--" not in sys.argv:
        raise SystemExit("usage: blender --background --python audit-female-facial-proportions-v30.py -- baseline.blend candidate.blend")
    values = sys.argv[sys.argv.index("--") + 1:]
    if len(values) != 2:
        raise SystemExit("expected baseline and candidate Blender files")
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
    body = bpy.data.objects["AevryndFemaleBodyBase"]
    rig = bpy.data.objects["AevryndFemaleRig"]
    return {
        "objects": objects,
        "bones": [bone.name for bone in rig.data.bones],
        "actions": sorted(action.name for action in bpy.data.actions),
        "face_revision": body.get("aevrynd_face_revision"),
        "scene_revision": bpy.context.scene.get("aevrynd_face_revision"),
        "changed_vertices": body.get("aevrynd_facial_transition_vertices"),
        "maximum_delta": body.get("aevrynd_facial_transition_max_delta_m"),
    }


baseline_path, candidate_path = inputs()
baseline = snapshot(baseline_path)
candidate = snapshot(candidate_path)
failures = []
allowed = {
    "AevryndFemaleBodyBase", "Eye_L_UpperFold", "Eye_R_UpperFold",
    "Eye_L_UpperLashes", "Eye_R_UpperLashes",
    "Eye_L_LowerLashes", "Eye_R_LowerLashes",
    "Eye_L_TearMeniscus", "Eye_R_TearMeniscus",
    "Eye_L_IrisFibers", "Eye_R_IrisFibers",
    "Lip_Upper", "Lip_Lower", "Mouth_WetLine",
}

if set(baseline["objects"]) != set(candidate["objects"]):
    failures.append("mesh object set changed")
if baseline["bones"] != candidate["bones"] or len(candidate["bones"]) != 21:
    failures.append("rig bone set changed")
if baseline["actions"] != candidate["actions"]:
    failures.append("action set changed")
if candidate["face_revision"] != 30 or candidate["scene_revision"] != 30:
    failures.append("face revision is not 30")

changed_objects = []
unchanged_objects = []
body_changed = 0
body_outside_region = 0
body_maximum = 0.0
for name, before in baseline["objects"].items():
    after = candidate["objects"][name]
    if name not in {"Eye_L_UpperFold", "Eye_R_UpperFold"}:
        if before["vertices"] != after["vertices"] or before["faces"] != after["faces"]:
            failures.append(f"{name} topology changed")
    if name in {"Eye_L_UpperFold", "Eye_R_UpperFold"}:
        if after["vertices"] != 74 or after["faces"] != 36:
            failures.append(f"{name} rebuilt topology is invalid")
        changed_objects.append(name)
        continue
    deltas = []
    for source, target in zip(before["positions"], after["positions"]):
        delta = math.dist(source, target)
        deltas.append(delta)
        if name == "AevryndFemaleBodyBase" and delta > 1e-7:
            body_changed += 1
            body_maximum = max(body_maximum, delta)
            x, y, z = source
            if y > -0.064 or not (1.468 <= z <= 1.646) or abs(x) > 0.096:
                body_outside_region += 1
    if max(deltas, default=0.0) > 1e-7:
        changed_objects.append(name)
    else:
        unchanged_objects.append(name)
    if name not in allowed and max(deltas, default=0.0) > 1e-7:
        failures.append(f"unintended geometry change in {name}")

if not 2000 <= body_changed <= 2300:
    failures.append(f"unexpected body vertex change count: {body_changed}")
if body_outside_region:
    failures.append(f"{body_outside_region} body vertices changed outside guarded face region")
if not 0.0014 <= body_maximum <= 0.0017:
    failures.append(f"body maximum delta outside guarded range: {body_maximum}")

for name in ("Lip_Upper", "Lip_Lower", "Mouth_WetLine"):
    obj = bpy.data.objects[name]
    maximum_influences = max((len(vertex.groups) for vertex in obj.data.vertices), default=0)
    if maximum_influences > 4 or any(not vertex.groups for vertex in obj.data.vertices):
        failures.append(f"{name} skin weights are invalid")

for name in ("Eye_L_IrisFibers", "Eye_R_IrisFibers", "Lip_Upper", "Mouth_WetLine"):
    if float(bpy.data.objects[name].get("aevrynd_safety_offset_m", 0.0)) <= 0.0:
        failures.append(f"{name} safety offset is missing")

non_finite = 0
for obj in bpy.data.objects:
    if obj.type == "MESH":
        non_finite += sum(
            not all(math.isfinite(value) for value in vertex.co)
            for vertex in obj.data.vertices
        )
if non_finite:
    failures.append(f"candidate contains {non_finite} non-finite vertices")

report = {
    "body_changed_vertices": body_changed,
    "body_maximum_delta_m": body_maximum,
    "body_changes_outside_guarded_region": body_outside_region,
    "changed_mesh_objects": sorted(changed_objects),
    "unchanged_mesh_objects": len(unchanged_objects),
    "mesh_objects": len(candidate["objects"]),
    "bones": len(candidate["bones"]),
    "actions": len(candidate["actions"]),
    "non_finite_vertices": non_finite,
}
print("AEVRYND_FACIAL_PROPORTIONS_V30_AUDIT=" + json.dumps(report))
if failures:
    raise SystemExit("; ".join(failures))
