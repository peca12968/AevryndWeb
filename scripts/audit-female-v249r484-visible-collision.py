import json
import math
import os
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
BASELINE = Path(os.environ.get("AEVRYND_FACE_COLLISION_BASELINE", ASSETS / "aevrynd-female-authoring-v249-mainline-runtime-brows-r480.blend"))
CANDIDATE = Path(os.environ.get("AEVRYND_FACE_COLLISION_CANDIDATE", ASSETS / "aevrynd-female-authoring-v249-mainline-continuous-upper-lip-r484.blend"))
REPORT = Path(os.environ.get("AEVRYND_FACE_COLLISION_OUTPUT", ASSETS / "female-v249-mainline-continuous-upper-lip-r484.collision-audit.json"))
BODY = "AevryndFemaleBodyBaseV118"
EYES = tuple(
    f"Eye_{side}_{part}"
    for side in ("L", "R")
    for part in ("Caruncle", "Cornea", "Iris", "Pupil", "Sclera", "TearMeniscus", "UpperLashes")
)
MOUTH = ("Mouth_OralCavity", "Mouth_Tongue", "Mouth_UpperTeeth")
RETIRED_LAYERS = ("Lip_Lower", "Lip_Upper", "Mouth_WetLine")
HAIR = tuple(f"AevryndFemaleRuntimeCards_{region}_R467" for region in ("front", "crown", "rear", "hairline")) + (
    "AevryndFemaleRuntimeScalpCap_R467",
    "AevryndFemaleRuntimeHairlineDensity_R467",
    "AevryndFemaleRuntimePartRootDensity_R467",
)
FACE_FRAMES = (1, 20)
HAIR_FRAMES = (1, 20, 33, 61)
PENETRATION_LIMIT = -0.0005


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
    return sum(
        1 for first, second in surface.overlap(surface)
        if first < second and not sets[first].intersection(sets[second])
    )


def face_snapshot(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    scene = bpy.context.scene
    result = {}
    for frame in FACE_FRAMES:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        body_tree = tree(bpy.data.objects[BODY], depsgraph)
        result[str(frame)] = {
            "bodyLayerOverlaps": {
                name: len(body_tree.overlap(tree(bpy.data.objects[name], depsgraph)))
                for name in EYES + MOUTH
            },
            "bodySelfIntersections": self_intersections(bpy.data.objects[BODY], depsgraph),
        }
    return result


baseline = face_snapshot(BASELINE)
candidate = face_snapshot(CANDIDATE)
regressions = []
for frame in map(str, FACE_FRAMES):
    for layer, count in candidate[frame]["bodyLayerOverlaps"].items():
        previous = baseline[frame]["bodyLayerOverlaps"][layer]
        if count > previous:
            regressions.append({"frame": int(frame), "category": "bodyLayerOverlap", "layer": layer, "baseline": previous, "candidate": count})
    current_self = candidate[frame]["bodySelfIntersections"]
    previous_self = baseline[frame]["bodySelfIntersections"]
    if current_self > previous_self:
        regressions.append({"frame": int(frame), "category": "bodySelfIntersection", "baseline": previous_self, "candidate": current_self})

# Reload the candidate and explicitly verify the active runtime hair against the
# changed body across the complete four-frame motion envelope.
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
        obj = bpy.data.objects[name]
        evaluated = obj.evaluated_get(depsgraph)
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

retired_state = {name: {"hideRender": bpy.data.objects[name].hide_render, "hideViewport": bpy.data.objects[name].hide_viewport, "export": bpy.data.objects[name].get("aevrynd_export")} for name in RETIRED_LAYERS}
for name, state in retired_state.items():
    if not state["hideRender"] or state["export"] is not False:
        regressions.append({"category": "retiredLayerStillExportable", "layer": name, "state": state})
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
    "faceFrames": list(FACE_FRAMES),
    "hairFrames": list(HAIR_FRAMES),
    "baselineFace": baseline,
    "candidateFace": candidate,
    "runtimeHairBodyCollision": hair_collision,
    "nonfiniteShapeKeyPoints": nonfinite,
    "regressions": regressions,
    "status": "PASS" if not regressions else "FAIL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R484_VISIBLE_COLLISION=" + json.dumps({"status": report["status"], "regressions": regressions}, sort_keys=True))
if regressions:
    raise SystemExit(2)
