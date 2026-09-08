import hashlib
import json
import math
import struct
import sys
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


candidate_path = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
baseline_path = candidate_path.parent / "aevrynd-female-authoring-v57.blend"
allowed_geometry = {
    "AevryndFemaleBodyBase",
    "Eye_L_Cornea", "Eye_R_Cornea",
    "Eye_L_Catchlight", "Eye_R_Catchlight",
    "Eye_L_Caruncle", "Eye_R_Caruncle",
    "Eye_L_TearMeniscus", "Eye_R_TearMeniscus",
    "Eye_L_UpperLashes", "Eye_R_UpperLashes",
    "Eye_L_LowerLashes", "Eye_R_LowerLashes",
}
retired = {
    "Eye_L_IrisFibers", "Eye_R_IrisFibers",
    "Eye_L_LimbalRing", "Eye_R_LimbalRing",
    "Eye_L_UpperFold", "Eye_R_UpperFold",
}


def signature(obj):
    digest = hashlib.sha256()
    digest.update(struct.pack("<II", len(obj.data.vertices), len(obj.data.polygons)))
    for vertex in obj.data.vertices:
        digest.update(struct.pack("<fff", *vertex.co))
    for polygon in obj.data.polygons:
        digest.update(struct.pack("<I", len(polygon.vertices)))
        for index in polygon.vertices:
            digest.update(struct.pack("<I", index))
    return digest.hexdigest()


def snapshot(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    return {obj.name: signature(obj) for obj in bpy.data.objects if obj.type == "MESH"}


def positions(path, names):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    return {
        name: [bpy.data.objects[name].matrix_world @ vertex.co for vertex in bpy.data.objects[name].data.vertices]
        for name in names
    }


def tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    result = BVHTree.FromPolygons(points, faces, all_triangles=False)
    evaluated.to_mesh_clear()
    return result


def collision_snapshot(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    scene = bpy.context.scene
    report = {}
    for frame in (1, 20):
        scene.frame_set(frame)
        depsgraph = bpy.context.evaluated_depsgraph_get()
        trees = {}

        def get(name):
            if name not in trees:
                trees[name] = tree(bpy.data.objects[name], depsgraph)
            return trees[name]

        values = {}
        for side in ("L", "R"):
            names = {
                "body": "AevryndFemaleBodyBase",
                "cornea": f"Eye_{side}_Cornea",
                "sclera": f"Eye_{side}_Sclera",
                "iris": f"Eye_{side}_Iris",
                "pupil": f"Eye_{side}_Pupil",
                "limbal": f"Eye_{side}_LimbalRing",
                "tear": f"Eye_{side}_TearMeniscus",
                "caruncle": f"Eye_{side}_Caruncle",
                "upper_lashes": f"Eye_{side}_UpperLashes",
                "lower_lashes": f"Eye_{side}_LowerLashes",
            }
            for left, right in (
                ("body", "tear"), ("body", "caruncle"),
                ("body", "upper_lashes"), ("body", "lower_lashes"),
                ("body", "cornea"), ("cornea", "sclera"),
                ("cornea", "iris"), ("cornea", "pupil"),
                ("cornea", "tear"), ("cornea", "caruncle"),
                ("cornea", "upper_lashes"), ("cornea", "lower_lashes"),
            ):
                key = f"{side}:{left}__{right}"
                values[key] = len(get(names[left]).overlap(get(names[right])))
        report[str(frame)] = values
    return report


baseline_signature = snapshot(baseline_path)
candidate_signature = snapshot(candidate_path)
failures = []
if set(candidate_signature) != set(baseline_signature):
    failures.append("mesh set mismatch")
unexpected = [
    name for name, value in baseline_signature.items()
    if name not in allowed_geometry and candidate_signature.get(name) != value
]
if unexpected:
    failures.append("unexpected geometry: " + ",".join(unexpected))

tracked_positions = {"AevryndFemaleBodyBase", "Eye_L_Cornea", "Eye_R_Cornea"}
baseline_positions = positions(baseline_path, tracked_positions)
candidate_positions = positions(candidate_path, tracked_positions)
deltas = {}
for name in tracked_positions:
    if len(baseline_positions[name]) != len(candidate_positions[name]):
        failures.append(name + " vertex count changed")
        continue
    values = [(after - before).length for before, after in zip(baseline_positions[name], candidate_positions[name])]
    deltas[name] = {"changed": sum(value > 1e-8 for value in values), "maximum_m": max(values, default=0.0)}

body_delta = deltas.get("AevryndFemaleBodyBase", {}).get("maximum_m", 0.0)
if not (0.00045 <= body_delta <= 0.0007001):
    failures.append(f"body palpebral displacement outside contract: {body_delta}")
for name in ("Eye_L_Cornea", "Eye_R_Cornea"):
    value = deltas.get(name, {}).get("maximum_m", 0.0)
    if not (0.00150 <= value <= 0.00156):
        failures.append(f"{name} apex displacement outside contract: {value}")

baseline_collisions = collision_snapshot(baseline_path)
candidate_collisions = collision_snapshot(candidate_path)
for frame, values in candidate_collisions.items():
    for pair, count in values.items():
        baseline_count = baseline_collisions[frame][pair]
        contact = pair.split(":", 1)[1]
        if contact in {"body__tear", "body__caruncle", "body__upper_lashes", "body__lower_lashes"} and count:
            failures.append(f"frame {frame} new body collision {pair}={count}")
        elif contact == "body__cornea":
            if count > baseline_count + 12:
                failures.append(f"frame {frame} body/cornea contact regression {pair}={count}>{baseline_count}+12")
        elif count > baseline_count:
            failures.append(f"frame {frame} collision regression {pair}={count}>{baseline_count}")

bpy.ops.wm.open_mainfile(filepath=str(candidate_path))
scene = bpy.context.scene
if scene.get("aevrynd_eye_revision") != 61 or scene.get("aevrynd_eye_method") != "body_integrated_lids_pbr_layered_eye":
    failures.append("scene eye contract mismatch")
for name in retired:
    obj = bpy.data.objects[name]
    if not obj.hide_render or not obj.get("aevrynd_runtime_exclude"):
        failures.append(name + " retirement contract mismatch")

texture_report = {}
for name, expected_size in (("aevrynd-iris-hazel-v61", (512, 512)), ("aevrynd-sclera-basecolor-v61", (512, 256))):
    image = bpy.data.images.get(name)
    texture_report[name] = tuple(image.size) if image else None
    if image is None or tuple(image.size) != expected_size or not Path(bpy.path.abspath(image.filepath)).exists():
        failures.append(name + " texture contract mismatch")

nonfinite = sum(
    not all(math.isfinite(value) for value in vertex.co)
    for obj in bpy.data.objects if obj.type == "MESH"
    for vertex in obj.data.vertices
)
if nonfinite:
    failures.append(f"nonfinite {nonfinite}")

report = {
    "status": "PASS" if not failures else "FAIL",
    "unchanged_baseline_meshes": sum(candidate_signature.get(name) == value for name, value in baseline_signature.items()),
    "allowed_geometry": sorted(allowed_geometry),
    "retired_overlays": sorted(retired),
    "deltas": deltas,
    "textures": texture_report,
    "baseline_collisions": baseline_collisions,
    "candidate_collisions": candidate_collisions,
    "nonfinite": nonfinite,
    "failures": failures,
}
print("AEVRYND_EYE_ANATOMY_V61_AUDIT=" + json.dumps(report))
if failures:
    raise SystemExit(1)
