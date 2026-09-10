import json
import math
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v248.blend"
CANDIDATE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249.blend"
BODY = "AevryndFemaleBodyBaseV118"
LAYERS = [
    *[f"Eye_{side}_{part}" for side in ("L", "R") for part in (
        "Sclera", "Cornea", "Iris", "TearMeniscus", "Caruncle",
        "UpperLashes", "LowerLashes", "UpperFold",
    )],
    "Lip_Upper", "Lip_Lower", "Mouth_WetLine", "Mouth_OralCavity",
    "Mouth_UpperTeeth", "Mouth_Tongue",
    "HairScalp", "HairCoverageTiles_v246", "HairSilhouetteCards_v246",
    "HairDetailFibers_v246", "HairCrownCoverage_v212",
    "HairlineNaturalCards_v214",
    "Clothing_Bandeau_v160", "Clothing_BandeauBinding_v162",
    "Clothing_BodyFitShorts_v135",
]


def evaluated_geometry(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return points, faces


def tree(obj, depsgraph):
    points, faces = evaluated_geometry(obj, depsgraph)
    return BVHTree.FromPolygons(points, faces, all_triangles=False)


def regional_self_intersections(obj, depsgraph):
    points, faces = evaluated_geometry(obj, depsgraph)
    bvh = BVHTree.FromPolygons(points, faces, all_triangles=False)
    pairs = set()
    vertex_sets = [set(face) for face in faces]
    centers = [sum((points[i] for i in face), points[face[0]] * 0.0) / len(face) for face in faces]
    for first, second in bvh.overlap(bvh):
        if first == second:
            continue
        pair = tuple(sorted((first, second)))
        if pair in pairs or vertex_sets[first] & vertex_sets[second]:
            continue
        a, b = centers[first], centers[second]
        if not any(abs(p.x) < 0.120 and p.y < 0.045 and 1.400 < p.z < 1.625 for p in (a, b)):
            continue
        pairs.add(pair)
    return len(pairs)


def snapshot(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    scene = bpy.context.scene
    report = {}
    for frame in (1, 20):
        scene.frame_set(frame)
        depsgraph = bpy.context.evaluated_depsgraph_get()
        body = bpy.data.objects[BODY]
        body_tree = tree(body, depsgraph)
        values = {}
        for name in LAYERS:
            values[name] = len(body_tree.overlap(tree(bpy.data.objects[name], depsgraph)))
        values["body_face_self_intersections"] = regional_self_intersections(body, depsgraph)
        report[str(frame)] = values
    return report


baseline = snapshot(BASELINE)
candidate = snapshot(CANDIDATE)
regressions = []
for frame, values in candidate.items():
    for name, count in values.items():
        previous = baseline[frame][name]
        if count > previous:
            regressions.append({
                "frame": frame, "layer": name,
                "baseline": previous, "candidate": count,
            })

bpy.ops.wm.open_mainfile(filepath=str(CANDIDATE))
body = bpy.data.objects[BODY]
nonfinite = sum(
    not all(math.isfinite(value) for value in vertex.co)
    for vertex in body.data.vertices
)
if bpy.context.scene.get("aevrynd_face_revision") != 249:
    regressions.append({"contract": "scene face revision mismatch"})
if not (1.8 <= float(body.get("aevrynd_philtrum_max_delta_mm", 0.0)) <= 2.2):
    regressions.append({"contract": "philtrum displacement out of range"})
if nonfinite:
    regressions.append({"contract": f"nonfinite vertices {nonfinite}"})

report = {
    "status": "PASS" if not regressions else "FAIL",
    "baseline": baseline,
    "candidate": candidate,
    "nonfinite": nonfinite,
    "regressions": regressions,
}
(ROOT / "assets-source/aevrynd-character/female-authoring-v249.face-collision-audit.json").write_text(
    json.dumps(report, indent=2), encoding="utf-8"
)
print("AEVRYND_V249_FACE_COLLISION_AUDIT=" + json.dumps(report, sort_keys=True))
if regressions:
    raise SystemExit(2)

