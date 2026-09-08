import hashlib
import json
import math
import struct
import sys
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


candidate_path = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
baseline_path = candidate_path.parent / "aevrynd-female-authoring-v43.blend"
changed = {"HairMain", "HairGuides", "HairFlyaways", "HairClumpsLarge", "HairClumpsMediumCards", "HairTempleClumps", "HairNapeClumps", "HairBoundaryClumps"}


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
    trees = {name: tree(bpy.data.objects[name], depsgraph) for name in changed | {"AevryndFemaleBodyBase", "HairScalp"}}
    body = trees["AevryndFemaleBodyBase"]
    scalp = trees["HairScalp"]
    values = {
        "main_body": len(trees["HairMain"].overlap(body)),
        "guides_body": len(trees["HairGuides"].overlap(body)),
        "flyaways_body": len(trees["HairFlyaways"].overlap(body)),
        "large_body": len(trees["HairClumpsLarge"].overlap(body)),
        "medium_body": len(trees["HairClumpsMediumCards"].overlap(body)),
        "large_scalp": len(trees["HairClumpsLarge"].overlap(scalp)),
        "medium_scalp": len(trees["HairClumpsMediumCards"].overlap(scalp)),
        "large_medium": len(trees["HairClumpsLarge"].overlap(trees["HairClumpsMediumCards"])),
        "temple_body": len(trees["HairTempleClumps"].overlap(body)),
        "nape_body": len(trees["HairNapeClumps"].overlap(body)),
        "boundary_body": len(trees["HairBoundaryClumps"].overlap(body)),
        "temple_scalp": len(trees["HairTempleClumps"].overlap(scalp)),
        "nape_scalp": len(trees["HairNapeClumps"].overlap(scalp)),
        "boundary_scalp": len(trees["HairBoundaryClumps"].overlap(scalp)),
        "temple_nape": len(trees["HairTempleClumps"].overlap(trees["HairNapeClumps"])),
        "temple_boundary": len(trees["HairTempleClumps"].overlap(trees["HairBoundaryClumps"])),
        "nape_boundary": len(trees["HairNapeClumps"].overlap(trees["HairBoundaryClumps"])),
    }
    frames[str(frame)] = values
    for name, count in values.items():
        if count:
            failures.append(f"frame {frame} {name} {count}")

expected_fibers = {"HairMain": 141, "HairGuides": 32, "HairFlyaways": 2}
actual_fibers = {name: int(bpy.data.objects[name].get("aevrynd_removed_ear_nape_fibers", -1)) for name in expected_fibers}
if actual_fibers != expected_fibers:
    failures.append("fiber removal counts invalid")
expected_cards = {"HairClumpsLarge": 30, "HairClumpsMediumCards": 39}
actual_cards = {name: int(bpy.data.objects[name].get("aevrynd_removed_ear_nape_cards", -1)) for name in expected_cards}
if actual_cards != expected_cards:
    failures.append("card removal counts invalid")
expected_transitions = {"HairTempleClumps": 46, "HairNapeClumps": 38, "HairBoundaryClumps": 30}
actual_transitions = {name: int(bpy.data.objects[name].get("aevrynd_clump_count", -1)) for name in expected_transitions}
if actual_transitions != expected_transitions:
    failures.append("transition counts invalid")
nonfinite = sum(not all(math.isfinite(value) for value in vertex.co) for obj in bpy.data.objects if obj.type == "MESH" for vertex in obj.data.vertices)
if nonfinite:
    failures.append(f"nonfinite {nonfinite}")
report = {"unchanged_baseline_meshes": sum(candidate.get(name) == value for name, value in baseline.items() if name not in changed), "removed_ear_nape_fibers": actual_fibers, "removed_ear_nape_cards": actual_cards, "transition_clumps": actual_transitions, "frames": frames, "nonfinite": nonfinite}
print("AEVRYND_EAR_NAPE_V44_AUDIT=" + json.dumps(report))
if failures:
    raise SystemExit("; ".join(failures))
