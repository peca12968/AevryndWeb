import hashlib
import json
import math
import struct
import sys

import bpy
from mathutils.bvhtree import BVHTree


values = sys.argv[sys.argv.index("--") + 1:]
if len(values) != 2:
    raise SystemExit("expected baseline.blend candidate.blend")
baseline_path, candidate_path = values
BODY = "AevryndFemaleBodyBase"
ALLOWED_ATTACHMENTS = {
    "Brow_L_Density", "Brow_R_Density",
    "Eye_L_UpperFold", "Eye_R_UpperFold",
    "Eye_L_TearMeniscus", "Eye_R_TearMeniscus",
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
    bpy.ops.wm.open_mainfile(filepath=path)
    body = bpy.data.objects[BODY]
    positions = [vertex.co.copy() for vertex in body.data.vertices]
    meshes = {obj.name: signature(obj) for obj in bpy.data.objects if obj.type == "MESH"}
    return meshes, positions


def world_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    result = BVHTree.FromPolygons(points, faces, all_triangles=False)
    evaluated.to_mesh_clear()
    return result


baseline, baseline_positions = snapshot(baseline_path)
candidate, candidate_positions = snapshot(candidate_path)
failures = []
if set(baseline) != set(candidate):
    failures.append("mesh object set changed")
unexpected = [
    name for name, value in baseline.items()
    if name != BODY and name not in ALLOWED_ATTACHMENTS and candidate.get(name) != value
]
if unexpected:
    failures.append(f"unexpected geometry changes: {unexpected}")
if len(baseline_positions) != len(candidate_positions):
    failures.append("body vertex count changed")
displacements = [
    (candidate_positions[index] - baseline_positions[index]).length
    for index in range(min(len(baseline_positions), len(candidate_positions)))
]
changed = sum(delta > 1e-7 for delta in displacements)
maximum = max(displacements, default=0.0)

bpy.ops.wm.open_mainfile(filepath=candidate_path)
scene = bpy.context.scene
body = bpy.data.objects[BODY]
if scene.get("aevrynd_face_revision") != 52 or body.get("aevrynd_face_revision") != 52:
    failures.append("face revision metadata invalid")
if changed != int(body.get("aevrynd_facial_plane_vertices", -1)):
    failures.append("changed vertex metadata invalid")
if not (8000 <= changed <= 10000):
    failures.append(f"unexpected changed vertex count {changed}")
if not (0.0009 <= maximum <= 0.0012):
    failures.append(f"unexpected maximum displacement {maximum}")
if abs(maximum - float(body.get("aevrynd_facial_plane_max_delta_m", 0.0))) > 0.00006:
    failures.append("maximum displacement metadata invalid")

attachments = [
    "Brow_L", "Brow_R", "Brow_L_Density", "Brow_R_Density",
    "Eye_L_UpperFold", "Eye_R_UpperFold",
    "Eye_L_UpperLashes", "Eye_R_UpperLashes",
    "Eye_L_LowerLashes", "Eye_R_LowerLashes",
    "Eye_L_TearMeniscus", "Eye_R_TearMeniscus",
    "Eye_L_Caruncle", "Eye_R_Caruncle",
    "Lip_Upper", "Lip_Lower", "Mouth_WetLine", "Mouth_OralCavity",
]
frames = {}
for frame in (1, 20):
    scene.frame_set(frame)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    body_bvh = world_tree(body, depsgraph)
    frame_report = {}
    for name in attachments:
        count = len(body_bvh.overlap(world_tree(bpy.data.objects[name], depsgraph)))
        frame_report["body__" + name] = count
        if count:
            failures.append(f"frame {frame} body/{name} has {count} overlaps")
    for side in ("L", "R"):
        cornea = world_tree(bpy.data.objects[f"Eye_{side}_Cornea"], depsgraph)
        sclera = world_tree(bpy.data.objects[f"Eye_{side}_Sclera"], depsgraph)
        for kind in ("Upper", "Lower"):
            lash = world_tree(bpy.data.objects[f"Eye_{side}_{kind}Lashes"], depsgraph)
            for label, target in (("cornea", cornea), ("sclera", sclera)):
                count = len(lash.overlap(target))
                key = f"{side}_{kind.lower()}_{label}"
                frame_report[key] = count
                if count:
                    failures.append(f"frame {frame} {key} has {count} overlaps")
    frames[str(frame)] = frame_report

nonfinite = sum(
    not all(math.isfinite(value) for value in vertex.co)
    for obj in bpy.data.objects if obj.type == "MESH" for vertex in obj.data.vertices
)
if nonfinite:
    failures.append(f"candidate contains {nonfinite} non-finite vertices")

report = {
    "status": "PASS" if not failures else "FAIL",
    "unchanged_non_body_meshes": sum(
        candidate.get(name) == value
        for name, value in baseline.items()
        if name != BODY and name not in ALLOWED_ATTACHMENTS
    ),
    "body": {
        "vertices": len(body.data.vertices),
        "faces": len(body.data.polygons),
        "changed_vertices": changed,
        "maximum_delta_m": maximum,
    },
    "frames": frames,
    "nonfinite_vertices": nonfinite,
    "failures": failures,
}
print("AEVRYND_FACIAL_PLANES_V52_AUDIT=" + json.dumps(report))
if failures:
    raise SystemExit(1)
