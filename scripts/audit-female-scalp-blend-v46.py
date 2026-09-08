import hashlib
import json
import math
import struct
import sys
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


candidate_path = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
baseline_path = candidate_path.parent / "aevrynd-female-authoring-v45.blend"


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
unexpected = [name for name, value in baseline.items() if name != "HairUndercutScalp" and candidate.get(name) != value]
if unexpected:
    failures.append("unexpected geometry: " + ",".join(unexpected))
undercut = bpy.data.objects["HairUndercutScalp"]
if len(undercut.data.vertices) != 2688 or len(undercut.data.polygons) != 2565:
    failures.append("undercut topology invalid")
if int(undercut.get("aevrynd_projection_misses", -1)) != 0:
    failures.append("projection misses")
if sum(modifier.type == "ARMATURE" for modifier in undercut.modifiers) != 1:
    failures.append("armature modifier invalid")
if any(not vertex.groups for vertex in undercut.data.vertices):
    failures.append("unweighted undercut vertices")
density = undercut.data.color_attributes.get("AevryndUndercutDensity")
if not density or density.domain != "POINT":
    failures.append("density attribute missing")
alpha = [entry.color_srgb[3] for entry in density.data] if density else []
if not alpha or min(alpha) > 0.001 or not 0.44 <= max(alpha) <= 0.47:
    failures.append("alpha range invalid")
if sum(value < 0.05 for value in alpha) < 500:
    failures.append("edge fade is too narrow")


def tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    result = BVHTree.FromPolygons(points, faces, all_triangles=False)
    evaluated.to_mesh_clear()
    return result


hair_names = [obj.name for obj in bpy.data.objects if obj.type == "MESH" and obj.name.startswith("Hair") and obj.name != "HairUndercutScalp"]
frames = {}
scene = bpy.context.scene
for frame in (1, 20):
    scene.frame_set(frame)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    subject = tree(undercut, depsgraph)
    values = {"body": len(subject.overlap(tree(bpy.data.objects["AevryndFemaleBodyBase"], depsgraph)))}
    for name in hair_names:
        values[name] = len(subject.overlap(tree(bpy.data.objects[name], depsgraph)))
    frames[str(frame)] = values
    for name, count in values.items():
        if count:
            failures.append(f"frame {frame} {name} {count}")
nonfinite = sum(not all(math.isfinite(value) for value in vertex.co) for vertex in undercut.data.vertices)
if nonfinite:
    failures.append(f"nonfinite {nonfinite}")
report = {"unchanged_baseline_meshes": sum(candidate.get(name) == value for name, value in baseline.items() if name != "HairUndercutScalp"), "vertices": len(undercut.data.vertices), "faces": len(undercut.data.polygons), "alpha_range": [min(alpha), max(alpha)], "alpha_below_0_05": sum(value < 0.05 for value in alpha), "frames": frames, "nonfinite": nonfinite}
print("AEVRYND_SCALP_BLEND_V46_AUDIT=" + json.dumps(report))
if failures:
    raise SystemExit("; ".join(failures))
