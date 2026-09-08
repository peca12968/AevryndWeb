import hashlib
import json
import math
import struct
import sys
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


candidate_path = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
baseline_path = candidate_path.parent / "aevrynd-female-authoring-v44.blend"
changed = {"HairClumpsLarge", "HairClumpsMediumCards"}


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


baseline = snapshot(baseline_path)
candidate = snapshot(candidate_path)
failures = []
if set(candidate) != set(baseline):
    failures.append("mesh set changed")
unexpected = [name for name, value in baseline.items() if name not in changed and candidate.get(name) != value]
if unexpected:
    failures.append("unexpected geometry: " + ",".join(unexpected))


def tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    result = BVHTree.FromPolygons(points, faces, all_triangles=False)
    evaluated.to_mesh_clear()
    return result


scene = bpy.context.scene
frames = {}
for frame in (1, 20):
    scene.frame_set(frame)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    body = tree(bpy.data.objects["AevryndFemaleBodyBase"], depsgraph)
    scalp = tree(bpy.data.objects["HairScalp"], depsgraph)
    large = tree(bpy.data.objects["HairClumpsLarge"], depsgraph)
    medium = tree(bpy.data.objects["HairClumpsMediumCards"], depsgraph)
    values = {"large_body": len(large.overlap(body)), "medium_body": len(medium.overlap(body)), "large_scalp": len(large.overlap(scalp)), "medium_scalp": len(medium.overlap(scalp)), "large_medium": len(large.overlap(medium))}
    frames[str(frame)] = values
    for name, count in values.items():
        if count:
            failures.append(f"frame {frame} {name} {count}")

objects = {name: bpy.data.objects[name] for name in changed}
geometry = {
    name: {
        "components": int(obj.get("aevrynd_card_component_count", 0)),
        "shell_clearance_m": float(obj.get("aevrynd_card_shell_clearance_m", 0.0)),
        "width_min": float(obj.get("aevrynd_card_width_factor_min", 0.0)),
        "width_max": float(obj.get("aevrynd_card_width_factor_max", 0.0)),
    }
    for name, obj in objects.items()
}
if geometry["HairClumpsLarge"]["components"] != 133 or geometry["HairClumpsMediumCards"]["components"] != 161:
    failures.append("component counts invalid")
if geometry["HairClumpsLarge"]["shell_clearance_m"] < 0.001 or geometry["HairClumpsMediumCards"]["shell_clearance_m"] < 0.0025:
    failures.append("shell clearance invalid")
nonfinite = sum(not all(math.isfinite(value) for value in vertex.co) for obj in bpy.data.objects if obj.type == "MESH" for vertex in obj.data.vertices)
if nonfinite:
    failures.append(f"nonfinite {nonfinite}")
report = {"unchanged_baseline_meshes": sum(candidate.get(name) == value for name, value in baseline.items() if name not in changed), "geometry": geometry, "frames": frames, "nonfinite": nonfinite}
print("AEVRYND_CROWN_CARDS_V45_AUDIT=" + json.dumps(report))
if failures:
    raise SystemExit("; ".join(failures))
