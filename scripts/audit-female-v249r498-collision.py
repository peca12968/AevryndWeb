import hashlib
import json
import math
import os
import struct
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
BASELINE = Path(os.environ.get("AEVRYND_R498_COLLISION_BASELINE", ASSETS / "aevrynd-female-authoring-v249-mainline-natural-sclera-r496.blend"))
CANDIDATE = Path(os.environ.get("AEVRYND_R498_COLLISION_CANDIDATE", ASSETS / "aevrynd-female-authoring-v249-mainline-natural-lower-lashes-r498.blend"))
REPORT = Path(os.environ.get("AEVRYND_R498_COLLISION_REPORT", ASSETS / "female-v249-mainline-natural-lower-lashes-r498.collision-audit.json"))
BODY = "AevryndFemaleBodyBaseV118"
EYE_PARTS = ("Caruncle", "Cornea", "Iris", "Pupil", "Sclera", "TearMeniscus", "UpperLashes", "LowerLashes")
MOUTH = ("Mouth_OralCavity", "Mouth_Tongue", "Mouth_UpperTeeth")
HAIR = tuple(f"AevryndFemaleRuntimeCards_{region}_R467" for region in ("front", "crown", "rear", "hairline")) + (
    "AevryndFemaleRuntimeScalpCap_R467",
    "AevryndFemaleRuntimeHairlineDensity_R467",
    "AevryndFemaleRuntimePartRootDensity_R467",
)
FACE_FRAMES = (1, 20)
HAIR_FRAMES = (1, 20, 33, 61)
PENETRATION_LIMIT = -0.0005


def static_mesh_digest(obj):
    digest = hashlib.sha256()
    digest.update(struct.pack("<II", len(obj.data.vertices), len(obj.data.polygons)))
    for vertex in obj.data.vertices:
        digest.update(struct.pack("<fff", *vertex.co))
    for polygon in obj.data.polygons:
        digest.update(struct.pack("<I", len(polygon.vertices)))
        for index in polygon.vertices:
            digest.update(struct.pack("<I", index))
    return digest.hexdigest()


def mesh_inventory(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    return {obj.name: static_mesh_digest(obj) for obj in bpy.data.objects if obj.type == "MESH"}


def geometry(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    evaluated.to_mesh_clear()
    return points, faces


def tree(obj, depsgraph):
    points, faces = geometry(obj, depsgraph)
    return BVHTree.FromPolygons(points, faces, all_triangles=False)


def self_intersections(obj, depsgraph):
    points, faces = geometry(obj, depsgraph)
    surface = BVHTree.FromPolygons(points, faces, all_triangles=False)
    sets = [set(face) for face in faces]
    return sum(1 for first, second in surface.overlap(surface) if first < second and not sets[first].intersection(sets[second]))


baseline_inventory = mesh_inventory(BASELINE)
candidate_inventory = mesh_inventory(CANDIDATE)
expected_added = {"Eye_L_LowerLashes", "Eye_R_LowerLashes"}
added = set(candidate_inventory) - set(baseline_inventory)
removed = set(baseline_inventory) - set(candidate_inventory)
changed = [name for name, digest in baseline_inventory.items() if candidate_inventory.get(name) != digest]
regressions = []
if added != expected_added:
    regressions.append({"category": "unexpectedAddedMeshes", "expected": sorted(expected_added), "actual": sorted(added)})
if removed:
    regressions.append({"category": "removedMeshes", "meshes": sorted(removed)})
if changed:
    regressions.append({"category": "changedExistingMeshGeometry", "meshes": changed})

bpy.ops.wm.open_mainfile(filepath=str(CANDIDATE))
scene = bpy.context.scene
topology = {}
for side in ("L", "R"):
    name = f"Eye_{side}_LowerLashes"
    obj = bpy.data.objects[name]
    topology[name] = {
        "vertices": len(obj.data.vertices),
        "polygons": len(obj.data.polygons),
        "fibers": int(obj.get("aevrynd_fiber_count", 0)),
        "lengthRangeM": [float(obj.get("aevrynd_length_min_m", 0.0)), float(obj.get("aevrynd_length_max_m", 0.0))],
        "parent": obj.parent.name if obj.parent else None,
        "parentType": obj.parent_type,
        "armatureModifiers": [modifier.object.name for modifier in obj.modifiers if modifier.type == "ARMATURE" and modifier.object],
        "headVertexGroup": obj.vertex_groups.get("head") is not None,
    }
    if topology[name]["fibers"] != 16 or len(obj.data.vertices) != 336 or len(obj.data.polygons) != 320:
        regressions.append({"category": "invalidLowerLashTopology", "layer": name, "state": topology[name]})
    if topology[name]["parent"] != "AevryndFemaleRig" or topology[name]["armatureModifiers"] != ["AevryndFemaleRig"] or not topology[name]["headVertexGroup"]:
        regressions.append({"category": "invalidLowerLashBinding", "layer": name, "state": topology[name]})

face = {}
for frame in FACE_FRAMES:
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    body_tree = tree(bpy.data.objects[BODY], depsgraph)
    values = {"bodySelfIntersections": self_intersections(bpy.data.objects[BODY], depsgraph), "eyes": {}}
    for side in ("L", "R"):
        objects = {part: bpy.data.objects[f"Eye_{side}_{part}"] for part in EYE_PARTS}
        trees = {part: tree(obj, depsgraph) for part, obj in objects.items()}
        values["eyes"][side] = {
            "bodyLayerOverlaps": {part: len(body_tree.overlap(surface)) for part, surface in trees.items()},
            "lowerLayerOverlaps": {
                part: len(trees["LowerLashes"].overlap(trees[part]))
                for part in ("Caruncle", "Cornea", "Iris", "Pupil", "Sclera", "TearMeniscus", "UpperLashes")
            },
        }
        for category in ("bodyLayerOverlaps", "lowerLayerOverlaps"):
            for layer, count in values["eyes"][side][category].items():
                if count:
                    regressions.append({"frame": frame, "category": category, "side": side, "layer": layer, "candidate": count})
    values["mouthBodyOverlaps"] = {name: len(body_tree.overlap(tree(bpy.data.objects[name], depsgraph))) for name in MOUTH}
    for name, count in values["mouthBodyOverlaps"].items():
        if count:
            regressions.append({"frame": frame, "category": "mouthBodyOverlap", "layer": name, "candidate": count})
    face[str(frame)] = values

# Compare the unchanged body self-intersection counts to r496.
bpy.ops.wm.open_mainfile(filepath=str(BASELINE))
baseline_self = {}
for frame in FACE_FRAMES:
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    baseline_self[str(frame)] = self_intersections(bpy.data.objects[BODY], depsgraph)
    if face[str(frame)]["bodySelfIntersections"] != baseline_self[str(frame)]:
        regressions.append({
            "frame": frame,
            "category": "bodySelfIntersectionChanged",
            "baseline": baseline_self[str(frame)],
            "candidate": face[str(frame)]["bodySelfIntersections"],
        })

bpy.ops.wm.open_mainfile(filepath=str(CANDIDATE))
scene = bpy.context.scene
hair_collision = {}
for frame in HAIR_FRAMES:
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    body_tree = tree(bpy.data.objects[BODY], depsgraph)
    hair_collision[str(frame)] = {}
    for name in HAIR:
        evaluated = bpy.data.objects[name].evaluated_get(depsgraph)
        points = [evaluated.matrix_world @ vertex.co for vertex in evaluated.data.vertices]
        signed = []
        for point in points:
            hit = body_tree.find_nearest(point, 0.025)
            if hit is not None and hit[1] is not None:
                signed.append((point - hit[0]).dot(hit[1].normalized()))
        penetrating = sum(value < PENETRATION_LIMIT for value in signed)
        hair_collision[str(frame)][name] = {
            "nearSamples": len(signed),
            "minimumSignedM": min(signed) if signed else None,
            "penetratingVertices": penetrating,
        }
        if penetrating:
            regressions.append({"frame": frame, "category": "runtimeHairBodyPenetration", "layer": name, "candidate": penetrating})

body = bpy.data.objects[BODY]
nonfinite = sum(
    not all(math.isfinite(value) for value in point.co)
    for block in body.data.shape_keys.key_blocks
    for point in block.data
)
if nonfinite:
    regressions.append({"category": "nonfiniteShapeKeyPoints", "candidate": nonfinite})

report = {
    "baseline": str(BASELINE),
    "candidate": str(CANDIDATE),
    "addedMeshes": sorted(added),
    "changedExistingMeshGeometry": changed,
    "topology": topology,
    "faceFrames": list(FACE_FRAMES),
    "faceCollision": face,
    "baselineBodySelfIntersections": baseline_self,
    "hairFrames": list(HAIR_FRAMES),
    "runtimeHairBodyCollision": hair_collision,
    "nonfiniteShapeKeyPoints": nonfinite,
    "addedRuntimeCost": {"vertices": 672, "polygons": 640, "materials": 1},
    "regressions": regressions,
    "status": "PASS" if not regressions else "FAIL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R498_COLLISION=" + json.dumps({"status": report["status"], "regressions": regressions}, sort_keys=True))
if regressions:
    raise SystemExit(2)
