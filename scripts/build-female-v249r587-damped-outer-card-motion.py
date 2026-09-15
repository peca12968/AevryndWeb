import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-balanced-collision-safe-hair-r584.blend"
OUTPUT = ASSETS / "aevrynd-female-authoring-v249-mainline-damped-outer-card-motion-r587.blend"
REPORT = ASSETS / "female-v249-mainline-damped-outer-card-motion-r587.build.json"
COVERAGE_OLD = "AevryndFemaleOwnedScalpGuideGroom_R584_Coverage"
CARDS_OLD = "AevryndFemaleTangentOuterHairCards_R584"
POINTS_PER_CARD = 24
VERTICES_PER_CARD = POINTS_PER_CARD * 2
BODY = "AevryndFemaleBodyBaseV118"
COLLISION_MARGIN_M = 0.0002


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def smoothstep(value):
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def rand(index, salt=0.0):
    return (math.sin(index * 12.9898 + salt * 78.233) * 43758.5453) % 1.0


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
coverage = bpy.data.objects[COVERAGE_OLD]
cards = bpy.data.objects[CARDS_OLD]
coverage.name = "AevryndFemaleOwnedScalpGuideGroom_R587_Coverage"
coverage.data.name = coverage.data.name.replace("R584", "R587")
coverage["aevrynd_revision"] = "v249r587"
cards.name = "AevryndFemaleTangentOuterHairCards_R587"
cards.data.name = cards.data.name.replace("R584", "R587")
cards["aevrynd_revision"] = "v249r587"

material = cards.data.materials[0]
material.name = "Aevrynd_DampedOuterHairCards_R587"
material["aevrynd_revision"] = "v249r587"
nodes = material.node_tree.nodes
links = material.node_tree.links
shader = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
texture = next(node for node in nodes if node.type == "TEX_IMAGE")
for link in list(shader.inputs["Alpha"].links):
    links.remove(link)
alpha = nodes.new("ShaderNodeMath")
alpha.name = "Aevrynd R587 Outer Alpha"
alpha.operation = "MULTIPLY"
alpha.use_clamp = True
alpha.inputs[1].default_value = 1.5
links.new(texture.outputs["Alpha"], alpha.inputs[0])
links.new(alpha.outputs[0], shader.inputs["Alpha"])

basis = cards.shape_key_add(name="Basis")
positive = cards.shape_key_add(name="HairSwayPositive")
negative = cards.shape_key_add(name="HairSwayNegative")
maximum_positive = 0.0
maximum_negative = 0.0
for vertex_index, vertex in enumerate(cards.data.vertices):
    card_index = vertex_index // VERTICES_PER_CARD
    guide_index = card_index // 2
    point_index = (vertex_index % VERTICES_PER_CARD) // 2
    t = point_index / (POINTS_PER_CARD - 1)
    envelope = smoothstep((t - 0.20) / 0.80) ** 1.35
    amplitude = 0.78 + 0.36 * rand(guide_index, 201.0)
    phase_bias = rand(guide_index, 202.0) - 0.5
    pos_delta = Vector((
        (0.0044 + 0.0012 * phase_bias) * amplitude,
        (0.0048 + 0.0010 * rand(guide_index, 203.0)) * amplitude,
        -0.0018 * amplitude,
    )) * envelope
    neg_delta = Vector((
        (-0.0030 + 0.0008 * phase_bias) * amplitude,
        (-0.0022 - 0.0007 * rand(guide_index, 204.0)) * amplitude,
        -0.0009 * amplitude,
    )) * envelope
    positive.data[vertex_index].co = basis.data[vertex_index].co + pos_delta
    negative.data[vertex_index].co = basis.data[vertex_index].co + neg_delta
    maximum_positive = max(maximum_positive, pos_delta.length)
    maximum_negative = max(maximum_negative, neg_delta.length)

for frame, positive_value, negative_value in (
    (1, 0.0, 0.0),
    (20, 0.0, 0.55),
    (33, 1.0, 0.0),
    (45, 0.0, 0.35),
    (61, 0.0, 0.0),
):
    positive.value = positive_value
    negative.value = negative_value
    positive.keyframe_insert(data_path="value", frame=frame)
    negative.keyframe_insert(data_path="value", frame=frame)

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 61
scene.frame_set(33)
bpy.context.view_layer.update()
depsgraph = bpy.context.evaluated_depsgraph_get()
body_evaluated = bpy.data.objects[BODY].evaluated_get(depsgraph)
body_mesh = body_evaluated.to_mesh()
body_vertices = [body_evaluated.matrix_world @ vertex.co for vertex in body_mesh.vertices]
body_faces = [tuple(polygon.vertices) for polygon in body_mesh.polygons]
body_tree = BVHTree.FromPolygons(body_vertices, body_faces, all_triangles=False)
body_evaluated.to_mesh_clear()
cards_world = cards.evaluated_get(depsgraph).matrix_world


def signed_distance(local_point):
    hit = body_tree.find_nearest(cards_world @ local_point, 0.025)
    if hit is None or hit[1] is None:
        return None
    point_world = cards_world @ local_point
    return (point_world - hit[0]).dot(hit[1].normalized())


positive_targets = [item.co.copy() for item in positive.data]
allowed_scales = [1.0] * len(cards.data.vertices)
for vertex_index in range(len(cards.data.vertices)):
    base = basis.data[vertex_index].co.copy()
    target = positive_targets[vertex_index]
    target_signed = signed_distance(target)
    if target_signed is None or target_signed >= COLLISION_MARGIN_M:
        continue
    base_signed = signed_distance(base)
    if base_signed is None or base_signed < COLLISION_MARGIN_M:
        scale = 0.0
    else:
        low = 0.0
        high = 1.0
        for _ in range(18):
            middle = (low + high) * 0.5
            candidate = base.lerp(target, middle)
            value = signed_distance(candidate)
            if value is None or value >= COLLISION_MARGIN_M:
                low = middle
            else:
                high = middle
        scale = low
    allowed_scales[vertex_index] = scale

card_count = len(cards.data.vertices) // VERTICES_PER_CARD
for card_index in range(0, card_count, 2):
    first = card_index * VERTICES_PER_CARD
    second = (card_index + 1) * VERTICES_PER_CARD
    for offset in range(VERTICES_PER_CARD):
        shared_scale = min(allowed_scales[first + offset], allowed_scales[second + offset])
        allowed_scales[first + offset] = shared_scale
        allowed_scales[second + offset] = shared_scale

collision_clamped_vertices = 0
minimum_motion_scale = 1.0
for vertex_index, scale in enumerate(allowed_scales):
    if scale < 0.999999:
        collision_clamped_vertices += 1
        minimum_motion_scale = min(minimum_motion_scale, scale)
    base = basis.data[vertex_index].co
    positive.data[vertex_index].co = base.lerp(positive_targets[vertex_index], scale)

maximum_positive = max(
    (positive.data[index].co - basis.data[index].co).length
    for index in range(len(cards.data.vertices))
)
scene.frame_set(1)
scene["aevrynd_revision"] = "v249r587"
scene["aevrynd_status"] = "DAMPED_OUTER_CARD_MOTION_PENDING_COLLISION"
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "outerAlphaMultiplier": 1.5,
    "shapeKeys": [positive.name, negative.name],
    "keyframes": [1, 20, 33, 45, 61],
    "rootPinnedFraction": 0.20,
    "maximumPositiveDisplacementM": maximum_positive,
    "maximumNegativeDisplacementM": maximum_negative,
    "positiveCollisionMarginM": COLLISION_MARGIN_M,
    "positiveCollisionClampedVertices": collision_clamped_vertices,
    "minimumPositiveMotionScale": minimum_motion_scale,
    "coherence": "two companion cards share one guide-level amplitude and phase bias",
    "runtimeIntent": "engine-drivable morph basis for later Verlet/PBD state; no Blender runtime dependency",
    "status": "BUILT_PENDING_DYNAMIC_COLLISION_AND_MOTION_AUDIT",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R587_DAMPED_OUTER_CARD_MOTION=" + json.dumps(report, sort_keys=True))
