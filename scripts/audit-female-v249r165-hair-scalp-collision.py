import json
import math
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-scalp-clump-coverage-r165.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-scalp-clump-coverage-r165.collision-audit.json"
CURVES = (
    "AevryndFemaleOwnedCurlyHairMain_v249r162",
    "AevryndFemaleOwnedCurlyScalpClumps_v249r165",
)
MESHES = ("AevryndFemaleDeformMatchedScalp_v249r163",)
SOLIDS = (
    "AevryndFemaleBodyBaseV118",
    "Clothing_Bandeau_v160",
    "Clothing_BandeauBinding_v162",
    "Clothing_BodyFitShorts_v135",
)
NEAR = {SOLIDS[0]: 0.025, SOLIDS[1]: 0.010, SOLIDS[2]: 0.010, SOLIDS[3]: 0.010}
LIMIT = -0.0005


def evaluated_mesh(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return vertices, faces


def tree(obj, depsgraph):
    vertices, faces = evaluated_mesh(obj, depsgraph)
    return BVHTree.FromPolygons(vertices, faces, all_triangles=False)


def sample(points, target, near):
    count = 0
    minimum = math.inf
    examples = []
    for index, point in enumerate(points):
        hit = target.find_nearest(point)
        if hit is None or hit[1] is None or hit[3] > near:
            continue
        signed = (point - hit[0]).dot(hit[1].normalized())
        minimum = min(minimum, signed)
        if signed < LIMIT:
            count += 1
            if len(examples) < 20:
                examples.append(index)
    return {
        "sampleCount": len(points),
        "minimumSignedM": minimum if math.isfinite(minimum) else None,
        "penetratingCount": count,
        "penetratingIndicesSample": examples,
    }


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
frames = {}
violations = []
for frame in (1, 20):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    trees = {solid: tree(bpy.data.objects[solid], depsgraph) for solid in SOLIDS}
    layers = {}
    for name in CURVES:
        evaluated = bpy.data.objects[name].evaluated_get(depsgraph)
        layers[name] = [evaluated.matrix_world @ point.position for point in evaluated.data.points]
    for name in MESHES:
        layers[name] = evaluated_mesh(bpy.data.objects[name], depsgraph)[0]
    layer_results = {}
    for layer, points in layers.items():
        results = {}
        for solid in SOLIDS:
            result = sample(points, trees[solid], NEAR[solid])
            results[solid] = result
            if result["penetratingCount"]:
                violations.append({"frame": frame, "layer": layer, "solid": solid, "count": result["penetratingCount"]})
        layer_results[layer] = results
    frames[str(frame)] = layer_results

report = {
    "source": str(SOURCE), "curveLayers": list(CURVES), "meshLayers": list(MESHES),
    "frames": frames, "penetrationLimitM": LIMIT,
    "violations": violations, "status": "PASS" if not violations else "FAIL",
}
OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R165_COLLISION=" + json.dumps({
    "output": str(OUTPUT), "violations": violations, "status": report["status"]
}, sort_keys=True))
if violations:
    raise SystemExit(2)
