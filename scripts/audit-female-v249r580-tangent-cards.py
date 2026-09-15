import json
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-balanced-tangent-cards-r580-study.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-balanced-tangent-cards-r580.collision-audit.json"
BODY = "AevryndFemaleBodyBaseV118"
SOLIDS = (
    BODY,
    "Clothing_Bandeau_v160",
    "Clothing_BandeauBinding_v162",
    "Clothing_BodyFitShorts_v135",
)
NEAR = {BODY: 0.025, SOLIDS[1]: 0.010, SOLIDS[2]: 0.010, SOLIDS[3]: 0.010}
LAYERS = (
    "AevryndFemaleOwnedScalpGuideGroom_R580_Coverage",
    "AevryndFemaleTangentOuterHairCards_R580",
)
FRAMES = (1, 20, 33, 61)
PENETRATION_LIMIT = -0.0005


def surface_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    result = BVHTree.FromPolygons(vertices, faces, all_triangles=False)
    evaluated.to_mesh_clear()
    return result


def evaluated_points(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    if evaluated.type == "CURVES":
        return [evaluated.matrix_world @ point.position for point in evaluated.data.points]
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    evaluated.to_mesh_clear()
    return points


bpy.ops.wm.open_mainfile(filepath=str(MODEL))
scene = bpy.context.scene
failures = []
collision = {}
for frame in FRAMES:
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    trees = {name: surface_tree(bpy.data.objects[name], depsgraph) for name in SOLIDS}
    collision[str(frame)] = {}
    for layer_name in LAYERS:
        points = evaluated_points(bpy.data.objects[layer_name], depsgraph)
        collision[str(frame)][layer_name] = {}
        for solid_name, tree in trees.items():
            signed = []
            for point in points:
                hit = tree.find_nearest(point, NEAR[solid_name])
                if hit is not None and hit[1] is not None:
                    signed.append((point - hit[0]).dot(hit[1].normalized()))
            penetrating = sum(value < PENETRATION_LIMIT for value in signed)
            entry = {
                "pointCount": len(points),
                "nearSamples": len(signed),
                "minimumSignedM": min(signed) if signed else None,
                "penetratingPoints": penetrating,
            }
            collision[str(frame)][layer_name][solid_name] = entry
            if penetrating:
                failures.append({
                    "frame": frame,
                    "layer": layer_name,
                    "solid": solid_name,
                    "penetratingPoints": penetrating,
                    "minimumSignedM": entry["minimumSignedM"],
                })

report = {
    "model": str(MODEL),
    "frames": list(FRAMES),
    "layers": list(LAYERS),
    "solids": list(SOLIDS),
    "penetrationLimitM": PENETRATION_LIMIT,
    "collision": collision,
    "failures": failures,
    "status": "PASS" if not failures else "FAIL",
    "motionStatus": "RIGID_HEAD_BOUND_STUDY_ONLY; secondary hair motion not implemented or claimed",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R580_COLLISION=" + json.dumps({"status": report["status"], "failures": failures}, sort_keys=True))
if failures:
    raise SystemExit(2)
