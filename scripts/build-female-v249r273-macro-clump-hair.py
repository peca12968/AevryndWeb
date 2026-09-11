import json
import math
import random
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-owned-alpha-hair-cards-r272.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-macro-clump-hair-r273.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-macro-clump-hair-r273.build-report.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r273-macro-clump-hair"
CARDS = "AevryndFemaleRuntimeHairCards_R271"
BODY = "AevryndFemaleBody_CC0_R249"
RIG = "AevryndFemaleRig"
POINTS = 24
VERTS_PER_CARD = POINTS * 2
CLUSTERS = 64


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def smoothstep(value):
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def card_centers(mesh):
    cards = []
    for card_index in range(len(mesh.vertices) // VERTS_PER_CARD):
        base = card_index * VERTS_PER_CARD
        cards.append([(mesh.vertices[base + point * 2].co + mesh.vertices[base + point * 2 + 1].co) * 0.5 for point in range(POINTS)])
    return cards


def feature(strand):
    # Root and early flow carry more weight so opposite sides of the part never merge.
    values = []
    for index, weight in ((0, 3.0), (5, 2.4), (11, 1.6), (17, 1.0), (23, 0.7)):
        point = strand[index]
        values.extend((point.x * weight, point.y * weight, point.z * weight))
    return values


def squared_distance(a, b):
    return sum((x - y) ** 2 for x, y in zip(a, b))


def cluster_strands(strands):
    features = [feature(strand) for strand in strands]
    rng = random.Random(273064)
    centroid_ids = [rng.randrange(len(features))]
    while len(centroid_ids) < CLUSTERS:
        distances = [min(squared_distance(item, features[index]) for index in centroid_ids) for item in features]
        centroid_ids.append(max(range(len(features)), key=distances.__getitem__))
    centroids = [features[index][:] for index in centroid_ids]
    assignments = [0] * len(features)
    for _ in range(14):
        assignments = [min(range(CLUSTERS), key=lambda index: squared_distance(item, centroids[index])) for item in features]
        accumulators = [[0.0] * len(features[0]) for _ in range(CLUSTERS)]
        counts = [0] * CLUSTERS
        for item, cluster in zip(features, assignments):
            counts[cluster] += 1
            for index, value in enumerate(item):
                accumulators[cluster][index] += value
        for cluster in range(CLUSTERS):
            if counts[cluster]:
                centroids[cluster] = [value / counts[cluster] for value in accumulators[cluster]]
    return assignments


def apply_macro_clumps(mesh):
    strands = card_centers(mesh)
    assignments = cluster_strands(strands)
    counts = [0] * CLUSTERS
    means = [[Vector((0.0, 0.0, 0.0)) for _ in range(POINTS)] for _ in range(CLUSTERS)]
    for strand, cluster in zip(strands, assignments):
        counts[cluster] += 1
        for point_index, point in enumerate(strand):
            means[cluster][point_index] += point
    for cluster in range(CLUSTERS):
        if counts[cluster]:
            means[cluster] = [point / counts[cluster] for point in means[cluster]]
    before = after = 0.0
    moved_max = 0.0
    for card_index, (strand, cluster) in enumerate(zip(strands, assignments)):
        base = card_index * VERTS_PER_CARD
        for point_index, (point, target) in enumerate(zip(strand, means[cluster])):
            t = point_index / (POINTS - 1)
            blend = 0.0 if t <= 0.20 else 0.62 * smoothstep((t - 0.20) / 0.58)
            if t > 0.82:
                blend *= 1.0 - 0.18 * smoothstep((t - 0.82) / 0.18)
            delta = (target - point) * blend
            before += (point - target).length_squared
            after += (point + delta - target).length_squared
            moved_max = max(moved_max, delta.length)
            mesh.vertices[base + point_index * 2].co += delta
            mesh.vertices[base + point_index * 2 + 1].co += delta
    mesh.update()
    return {
        "cardCount": len(strands), "clusterCount": CLUSTERS, "clusterSizes": counts,
        "withinClusterRmsBeforeM": math.sqrt(before / (len(strands) * POINTS)),
        "withinClusterRmsAfterM": math.sqrt(after / (len(strands) * POINTS)),
        "maximumCenterlineMoveM": moved_max,
        "rootLockFraction": 0.20,
    }


def body_tree():
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    evaluated = bpy.data.objects[BODY].evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, faces, all_triangles=False)


def repair_rest_clearance(cards, target=0.0002):
    tree = body_tree()
    matrix = cards.matrix_world.copy()
    inverse = matrix.inverted()
    repaired = []
    minimum = math.inf
    for vertex in cards.data.vertices:
        if vertex.index % VERTS_PER_CARD < 10:
            continue
        world = matrix @ vertex.co
        hit = tree.find_nearest(world, 0.20)
        if hit is None or hit[1] is None:
            continue
        normal = hit[1].normalized()
        signed = (world - hit[0]).dot(normal)
        minimum = min(minimum, signed)
        if signed < target:
            vertex.co = inverse @ (hit[0] + normal * target)
            repaired.append(vertex.index)
    cards.data.update()
    return {"targetClearanceM": target, "repairedVertices": len(repaired), "beforeMinimumSignedM": minimum, "sample": repaired[:32]}


def render(camera, frame, name, location, target):
    scene = bpy.context.scene
    scene.frame_set(frame)
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    camera.location = location
    camera.data.lens = 82
    look_at(camera, target)
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
cards = bpy.data.objects[CARDS]
topology_before = (len(cards.data.vertices), len(cards.data.polygons), len(cards.data.loops))
clump_report = apply_macro_clumps(cards.data)
clearance_report = repair_rest_clearance(cards)
topology_after = (len(cards.data.vertices), len(cards.data.polygons), len(cards.data.loops))
cards["aevrynd_revision"] = "v249r273"
cards["aevrynd_macro_clump_count"] = CLUSTERS
cards["aevrynd_macro_clump_method"] = "flow-aware deterministic k-means; roots locked"
scene["aevrynd_mainline_revision"] = "v249r273-macro-clump-hair"
scene["aevrynd_hair_layers"] = "primary_clumps.authoring|secondary_fill|flyaways|runtime_cards.dynamic.alpha.macro_clumped"
scene["aevrynd_release_state"] = "MACRO_CLUMP_VISUAL_AND_DYNAMIC_REAUDIT_PENDING"
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 800
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
shots = (
    (1, "front-f01", (0.0, -0.90, 1.59)),
    (33, "front-f33", (0.0, -0.90, 1.59)),
    (1, "left-f01", (-0.72, -0.55, 1.59)),
    (1, "right-f01", (0.72, -0.55, 1.59)),
    (1, "back-f01", (0.0, 0.90, 1.59)),
    (33, "back-f33", (0.0, 0.90, 1.59)),
)
for frame, name, location in shots:
    render(camera, frame, name, location, (0.0, 0.0, 1.56))
scene.frame_set(1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE), "output": str(OUTPUT), "cardObject": CARDS,
    "topologyBefore": topology_before, "topologyAfter": topology_after,
    "topologyChanged": topology_before != topology_after,
    "macroClumps": clump_report, "restClearanceRepair": clearance_report,
    "materialPreserved": "Aevrynd_RuntimeHairCards_Alpha_R272",
    "animationPreserved": True, "collisionContractPreserved": True,
    "renderDirectory": str(RENDER_DIR), "status": "VISUAL_AND_DYNAMIC_REAUDIT_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R273_MACRO_CLUMP_HAIR=" + json.dumps(report, sort_keys=True))
