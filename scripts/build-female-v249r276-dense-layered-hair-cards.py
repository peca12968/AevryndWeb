import json
import math
import random
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-owned-alpha-hair-cards-r272.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-dense-layered-hair-cards-r276.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-dense-layered-hair-cards-r276.build-report.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r276-dense-layered-hair-cards"
SOURCE_CARDS = "AevryndFemaleRuntimeHairCards_R271"
CARDS = "AevryndFemaleRuntimeHairCards_R276"
BODY = "AevryndFemaleBody_CC0_R249"
RIG = "AevryndFemaleRig"
POINTS = 24
SOURCE_STRIDE = POINTS * 2
CARD_COUNT = 384
CHAINS = {
    "hair_dyn.L.front": (-0.082, -0.030),
    "hair_dyn.R.front": (0.082, -0.030),
    "hair_dyn.L.back": (-0.065, 0.060),
    "hair_dyn.C.back": (0.000, 0.078),
    "hair_dyn.R.back": (0.065, 0.060),
}


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def smoothstep(value):
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def source_strands(mesh):
    result = []
    for card_index in range(len(mesh.vertices) // SOURCE_STRIDE):
        base = card_index * SOURCE_STRIDE
        result.append([(mesh.vertices[base + point * 2].co + mesh.vertices[base + point * 2 + 1].co) * 0.5 for point in range(POINTS)])
    return result


def feature(strand):
    values = []
    for index, weight in ((0, 4.0), (4, 3.0), (9, 2.0), (15, 1.2), (23, 0.7)):
        point = strand[index]
        values.extend((point.x * weight, point.y * weight, point.z * weight))
    return values


def distance_squared(a, b):
    return sum((x - y) ** 2 for x, y in zip(a, b))


def kmeans(strands):
    features = [feature(strand) for strand in strands]
    rng = random.Random(276384)
    ids = [rng.randrange(len(features))]
    minimum_distances = [distance_squared(item, features[ids[0]]) for item in features]
    while len(ids) < CARD_COUNT:
        next_id = max(range(len(features)), key=minimum_distances.__getitem__)
        ids.append(next_id)
        for index, item in enumerate(features):
            minimum_distances[index] = min(minimum_distances[index], distance_squared(item, features[next_id]))
    centroids = [features[index][:] for index in ids]
    assignments = [0] * len(features)
    for _ in range(10):
        assignments = [min(range(CARD_COUNT), key=lambda index: distance_squared(item, centroids[index])) for item in features]
        accumulators = [[0.0] * len(features[0]) for _ in range(CARD_COUNT)]
        counts = [0] * CARD_COUNT
        for item, cluster in zip(features, assignments):
            counts[cluster] += 1
            for index, value in enumerate(item):
                accumulators[cluster][index] += value
        for cluster in range(CARD_COUNT):
            if counts[cluster]:
                centroids[cluster] = [value / counts[cluster] for value in accumulators[cluster]]
    return assignments


def nearest_chain(point):
    choices = []
    for name, (x, y) in CHAINS.items():
        penalty = 0.018 if ((".front" in name and point.y > 0.020) or (".back" in name and point.y < 0.000)) else 0.0
        choices.append(((point.x - x) ** 2 + (point.y - y) ** 2 + penalty, name))
    return min(choices)[1]


def level_weights(t):
    raw = [max(0.0, 1.0 - abs(t - center) / 0.40) for center in (0.25, 0.58, 0.90)]
    total = sum(raw) or 1.0
    return [value / total for value in raw]


def make_dense_alpha_material():
    material = bpy.data.materials["Aevrynd_RuntimeHairCards_Alpha_R272"].copy()
    material.name = "Aevrynd_RuntimeHairCards_DenseAlpha_R276"
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
    texture = next(node for node in nodes if node.type == "TEX_IMAGE")
    for link in list(links):
        if link.to_node == shader and link.to_socket == shader.inputs["Alpha"]:
            links.remove(link)
    opacity = nodes.new("ShaderNodeMath")
    opacity.operation = "MULTIPLY"
    opacity.use_clamp = True
    opacity.inputs[1].default_value = 2.45
    opacity.label = "Inner coverage opacity 2.45x"
    links.new(texture.outputs["Alpha"], opacity.inputs[0])
    links.new(opacity.outputs[0], shader.inputs["Alpha"])
    material["aevrynd_layer"] = "material.hair.runtime_cards.dense_alpha"
    material["aevrynd_revision"] = "v249r276"
    material["aevrynd_alpha_gain"] = 2.45
    return material


def build_wide_cards(source, rig):
    strands = source_strands(source.data)
    assignments = kmeans(strands)
    members = [[] for _ in range(CARD_COUNT)]
    for strand, cluster in zip(strands, assignments):
        members[cluster].append(strand)
    paths = []
    for group in members:
        paths.append([sum((strand[index] for strand in group), Vector()) / len(group) for index in range(POINTS)])
    vertices, faces, weights = [], [], []
    rng = random.Random(276077)
    widths = []
    for card_index, (path, group) in enumerate(zip(paths, members)):
        chain = nearest_chain(path[0])
        fullness = clamp((len(group) - 1) / 7.0)
        base_width = 0.0028 + 0.0014 * fullness + rng.uniform(-0.00025, 0.00025)
        widths.append(base_width)
        for point_index, point in enumerate(path):
            before = path[max(0, point_index - 1)]
            after = path[min(POINTS - 1, point_index + 1)]
            direction = (after - before).normalized()
            radial = Vector((point.x, point.y + 0.010, 0.0))
            if radial.length < 1e-5:
                radial = Vector((1.0, 0.0, 0.0))
            radial.normalize()
            side = direction.cross(radial)
            if side.length < 1e-5:
                side = direction.cross(Vector((0.0, 1.0, 0.0)))
            side.normalize()
            t = point_index / (POINTS - 1)
            root_taper = 0.72 + 0.28 * smoothstep(t / 0.13)
            tip_taper = 1.0 - 0.82 * smoothstep((t - 0.70) / 0.30)
            width = base_width * root_taper * tip_taper
            # A shallow alternating lift breaks a single cylindrical shell while
            # keeping roots and collision-sensitive lower sections stable.
            lift = radial * (0.0015 * (0.35 + 0.65 * (card_index % 3) / 2.0) * math.sin(math.pi * t) ** 2)
            center = point + lift
            vertices.extend((center - side * width, center + side * width))
            dynamic = smoothstep((t - 0.08) / 0.64)
            weights.extend(((chain, t, dynamic), (chain, t, dynamic)))
        base = card_index * SOURCE_STRIDE
        for point_index in range(POINTS - 1):
            a = base + point_index * 2
            faces.append((a, a + 1, a + 3, a + 2))
    mesh = bpy.data.meshes.new("AevryndFemaleRuntimeHairCardsTopology_R276")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(bpy.data.materials["Aevrynd_RuntimeHairCards_DenseAlpha_R276"])
    uv = mesh.uv_layers.new(name="AevryndRuntimeHairCardUV")
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            local = mesh.loops[loop_index].vertex_index % SOURCE_STRIDE
            uv.data[loop_index].uv = (float(local % 2), (local // 2) / (POINTS - 1))
    uv.active_render = True
    obj = bpy.data.objects.new(CARDS, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = rig
    obj.matrix_parent_inverse = rig.matrix_world.inverted()
    head = obj.vertex_groups.new(name="head")
    for chain in CHAINS:
        for segment in range(3):
            obj.vertex_groups.new(name=f"{chain}.{segment + 1:02d}")
    chain_counts = {name: 0 for name in CHAINS}
    for vertex_index, (chain, t, dynamic) in enumerate(weights):
        head.add([vertex_index], 1.0 - dynamic, "REPLACE")
        for segment, weight in enumerate(level_weights(t)):
            obj.vertex_groups[f"{chain}.{segment + 1:02d}"].add([vertex_index], dynamic * weight, "REPLACE")
        chain_counts[chain] += 1
    modifier = obj.modifiers.new("Aevrynd Hair Secondary Motion", "ARMATURE")
    modifier.object = rig
    obj["aevrynd_layer"] = "hair.runtime_cards.dynamic.alpha.wide_clumps"
    obj["aevrynd_revision"] = "v249r276"
    obj["aevrynd_source_card_count"] = len(strands)
    obj["aevrynd_card_count"] = CARD_COUNT
    return obj, members, widths, chain_counts


def body_tree():
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    evaluated = bpy.data.objects[BODY].evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(points, faces, all_triangles=False)


def repair_clearance(cards, target=0.0002):
    tree = body_tree()
    matrix, inverse = cards.matrix_world.copy(), cards.matrix_world.inverted()
    repaired, minimum = [], math.inf
    for vertex in cards.data.vertices:
        if vertex.index % SOURCE_STRIDE < 6:
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
    return {"targetM": target, "beforeMinimumSignedM": minimum, "repairedVertices": len(repaired), "sample": repaired[:32]}


def render(camera, frame, name, location):
    scene = bpy.context.scene
    scene.frame_set(frame)
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    camera.location = location
    camera.data.lens = 82
    look_at(camera, (0.0, 0.0, 1.56))
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
make_dense_alpha_material()
source = bpy.data.objects[SOURCE_CARDS]
source.hide_render = True
source.hide_viewport = True
secondary = bpy.data.objects["AevryndFemaleSecondaryFill_R264"]
secondary.hide_render = True
secondary.hide_viewport = True
cards, members, widths, chain_counts = build_wide_cards(source, bpy.data.objects[RIG])
clearance = repair_clearance(cards)
scene["aevrynd_mainline_revision"] = "v249r276-dense-layered-hair-cards"
scene["aevrynd_hair_layers"] = "authoring.primary|authoring.secondary_fill|authoring.flyaways|runtime.wide_alpha_cards.dynamic"
scene["aevrynd_release_state"] = "DENSE_LAYERED_CARD_VISUAL_AND_DYNAMIC_REAUDIT_PENDING"
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 800
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
for frame, name, location in (
    (1, "front-f01", (0.0, -0.90, 1.59)), (33, "front-f33", (0.0, -0.90, 1.59)),
    (1, "left-f01", (-0.72, -0.55, 1.59)), (1, "right-f01", (0.72, -0.55, 1.59)),
    (1, "back-f01", (0.0, 0.90, 1.59)), (33, "back-f33", (0.0, 0.90, 1.59)),
):
    render(camera, frame, name, location)
scene.frame_set(1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE), "output": str(OUTPUT), "cardObject": CARDS,
    "sourceCards": len(source_strands(source.data)), "runtimeCards": CARD_COUNT,
    "vertices": len(cards.data.vertices), "faces": len(cards.data.polygons), "uvLoops": len(cards.data.loops),
    "clusterSizes": [len(group) for group in members], "halfWidthRangeM": [min(widths), max(widths)],
    "chainVertexCounts": chain_counts, "restClearanceRepair": clearance,
    "material": "Aevrynd_RuntimeHairCards_DenseAlpha_R276", "alphaGain": 2.45,
    "hiddenAuthoringSecondaryFillPoints": 242112, "ownedAssetOnly": True,
    "renderDirectory": str(RENDER_DIR), "status": "VISUAL_AND_DYNAMIC_REAUDIT_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R276_DENSE_LAYERED_HAIR_CARDS=" + json.dumps(report, sort_keys=True))

