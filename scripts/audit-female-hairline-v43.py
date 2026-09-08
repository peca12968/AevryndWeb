import hashlib
import json
import math
import struct
import sys
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


candidate_path = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
baseline_path = candidate_path.parent / "aevrynd-female-authoring-v42.blend"
changed = {"HairMain", "HairGuides", "HairFlyaways", "HairClumpsLarge", "HairClumpsMediumCards", "HairlineBaby"}


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
    values = {
        "main_body": len(tree(bpy.data.objects["HairMain"], depsgraph).overlap(body)),
        "guides_body": len(tree(bpy.data.objects["HairGuides"], depsgraph).overlap(body)),
        "flyaways_body": len(tree(bpy.data.objects["HairFlyaways"], depsgraph).overlap(body)),
        "baby_body": len(tree(bpy.data.objects["HairlineBaby"], depsgraph).overlap(body)),
        "large_body": len(large.overlap(body)),
        "medium_body": len(medium.overlap(body)),
        "large_scalp": len(large.overlap(scalp)),
        "medium_scalp": len(medium.overlap(scalp)),
        "large_medium": len(large.overlap(medium)),
    }
    frames[str(frame)] = values
    for name, count in values.items():
        if count:
            failures.append(f"frame {frame} {name} {count}")

expected_fibers = {"HairMain": 259, "HairGuides": 31, "HairFlyaways": 8}
actual_fibers = {name: int(bpy.data.objects[name].get("aevrynd_removed_forehead_fibers", -1)) for name in expected_fibers}
if actual_fibers != expected_fibers:
    failures.append("fiber removal counts invalid")
expected_cards = {"HairClumpsLarge": 41, "HairClumpsMediumCards": 38}
actual_cards = {name: int(bpy.data.objects[name].get("aevrynd_removed_forehead_cards", -1)) for name in expected_cards}
if actual_cards != expected_cards:
    failures.append("card removal counts invalid")
if int(bpy.data.objects["HairlineBaby"].get("aevrynd_strand_count", 0)) != 89:
    failures.append("baby hair count invalid")
nonfinite = sum(not all(math.isfinite(value) for value in vertex.co) for obj in bpy.data.objects if obj.type == "MESH" for vertex in obj.data.vertices)
if nonfinite:
    failures.append(f"nonfinite {nonfinite}")
report = {
    "unchanged_baseline_meshes": sum(candidate.get(name) == value for name, value in baseline.items() if name not in changed),
    "removed_forehead_fibers": actual_fibers,
    "removed_forehead_cards": actual_cards,
    "baby_hairs": int(bpy.data.objects["HairlineBaby"]["aevrynd_strand_count"]),
    "frames": frames,
    "nonfinite": nonfinite,
}
print("AEVRYND_HAIRLINE_V43_AUDIT=" + json.dumps(report))
if failures:
    raise SystemExit("; ".join(failures))
