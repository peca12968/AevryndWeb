"""Build owned, explicit oral cavity, gum, tooth and tongue layers behind r1033."""

import json
import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-lower-lip-rim-turn-r1033-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-owned-oral-layers-r1034-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1034-owned-oral-layers-sweep.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r1034-owned-oral-layers-sweep"
BODY = "AevryndFemaleCC0Baseline_v259"
RIG = "AevryndFemaleRig"
OPEN_KEY = "Aevrynd_MouthOpenTest_R1030"
LAYERS = (
    "Aevrynd_OralCavity_R1034",
    "Aevrynd_UpperGum_R1034",
    "Aevrynd_LowerGum_R1034",
    "Aevrynd_UpperTeeth_R1034",
    "Aevrynd_LowerTeeth_R1034",
    "Aevrynd_Tongue_R1034",
)
VARIANTS = (("a-forward", 0.000), ("b-safe-depth", 0.003), ("c-deep", 0.006))
SELECTED = "b-safe-depth"


def material(name, color, roughness, subsurface=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.diffuse_color = (*color, 1.0)
    bsdf = next(node for node in mat.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    if "Subsurface Weight" in bsdf.inputs:
        bsdf.inputs["Subsurface Weight"].default_value = subsurface
    mat["aevrynd_owned_procedural"] = True
    mat["aevrynd_layer_revision"] = "v249r1034"
    return mat


def object_from_bmesh(name, bm, mat):
    mesh = bpy.data.meshes.new(name + "_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(mat)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return obj


def add_ellipsoid(bm, center, radii, segments=16, rings=8):
    transform = Matrix.Translation(Vector(center)) @ Matrix.Diagonal((*radii, 1.0))
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, radius=1.0, matrix=transform)


def make_ellipsoid_layer(name, entries, mat):
    bm = bmesh.new()
    for center, radii in entries:
        add_ellipsoid(bm, center, radii)
    return object_from_bmesh(name, bm, mat)


def make_cavity(name, depth, mat):
    center_z = 1.387
    rings = (
        (-0.068 + depth, 0.031, 0.013),
        (-0.043 + depth, 0.038, 0.024),
        (-0.018 + depth, 0.033, 0.020),
    )
    segments = 40
    vertices = []
    faces = []
    for y, radius_x, radius_z in rings:
        for index in range(segments):
            angle = 2.0 * math.pi * index / segments
            vertices.append((radius_x * math.sin(angle), y, center_z + radius_z * math.cos(angle)))
    for ring in range(len(rings) - 1):
        start = ring * segments
        following = (ring + 1) * segments
        for index in range(segments):
            nxt = (index + 1) % segments
            faces.append((start + index, start + nxt, following + nxt, following + index))
    back = len(vertices)
    vertices.append((0.0, 0.000 + depth, center_z))
    start = (len(rings) - 1) * segments
    for index in range(segments):
        nxt = (index + 1) % segments
        faces.append((start + index, start + nxt, back))
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(mat)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    for poly in mesh.polygons:
        poly.use_smooth = True
    return obj


def make_gum(name, upper, depth, mat):
    vertices = []
    faces = []
    path_segments = 25
    ring_segments = 8
    base_z = 1.3995 if upper else 1.3750
    sign = 1.0 if upper else -1.0
    for path_index in range(path_segments):
        t = path_index / (path_segments - 1) * 2.0 - 1.0
        x = 0.028 * t
        y = -0.050 + depth + 0.006 * t * t
        z = base_z + sign * 0.0025 * t * t
        for ring_index in range(ring_segments):
            angle = 2.0 * math.pi * ring_index / ring_segments
            vertices.append((x, y + 0.0018 * math.sin(angle), z + 0.0018 * math.cos(angle)))
    for path_index in range(path_segments - 1):
        first = path_index * ring_segments
        second = (path_index + 1) * ring_segments
        for ring_index in range(ring_segments):
            nxt = (ring_index + 1) % ring_segments
            faces.append((first + ring_index, first + nxt, second + nxt, second + ring_index))
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(mat)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    for poly in mesh.polygons:
        poly.use_smooth = True
    return obj


def bind_to_head(obj):
    rig = bpy.data.objects[RIG]
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = world
    obj["aevrynd_layer_owner"] = "Aevrynd"
    obj["aevrynd_layer_revision"] = "v249r1034"
    obj["aevrynd_collision_role"] = "internal oral layer"


def build_layers(depth):
    cavity_mat = material("Aevrynd_OralCavityMat_R1034", (0.075, 0.012, 0.016), 0.72, 0.05)
    gum_mat = material("Aevrynd_GumMat_R1034", (0.32, 0.075, 0.085), 0.58, 0.12)
    tooth_mat = material("Aevrynd_ToothMat_R1034", (0.72, 0.66, 0.55), 0.34, 0.0)
    tongue_mat = material("Aevrynd_TongueMat_R1034", (0.30, 0.055, 0.065), 0.62, 0.16)
    created = [make_cavity(LAYERS[0], depth, cavity_mat)]
    created.append(make_gum(LAYERS[1], True, depth, gum_mat))
    created.append(make_gum(LAYERS[2], False, depth, gum_mat))

    upper_entries = []
    upper_x = (-0.0265, -0.0210, -0.0152, -0.0092, -0.0031, 0.0031, 0.0092, 0.0152, 0.0210, 0.0265)
    for index, x in enumerate(upper_x):
        lateral = abs(x) / 0.0265
        width = 0.00325 if 3 <= index <= 6 else 0.00285
        center = (x, -0.0735 + depth + 0.0040 * lateral * lateral, 1.3930 + 0.0015 * lateral)
        upper_entries.append((center, (width, 0.0032, 0.0050 - 0.0007 * lateral)))
    created.append(make_ellipsoid_layer(LAYERS[3], upper_entries, tooth_mat))

    lower_entries = []
    lower_x = (-0.0215, -0.0155, -0.0094, -0.0031, 0.0031, 0.0094, 0.0155, 0.0215)
    for index, x in enumerate(lower_x):
        lateral = abs(x) / 0.0215
        width = 0.0031 if 2 <= index <= 5 else 0.00275
        center = (x, -0.0695 + depth + 0.0035 * lateral * lateral, 1.3810 - 0.0010 * lateral)
        lower_entries.append((center, (width, 0.0030, 0.0040 - 0.0004 * lateral)))
    created.append(make_ellipsoid_layer(LAYERS[4], lower_entries, tooth_mat))
    created.append(make_ellipsoid_layer(LAYERS[5], [((0.0, -0.037 + depth, 1.3760), (0.0255, 0.0170, 0.0055))], tongue_mat))
    for obj in created:
        bind_to_head(obj)
    return created


def world_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    mesh.calc_loop_triangles()
    polygons = [tuple(triangle.vertices) for triangle in mesh.loop_triangles]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, polygons, all_triangles=True), len(vertices), len(polygons)


def overlap_counts(body, layers):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    body_tree, _, _ = world_tree(body, depsgraph)
    trees = {}
    body_counts = {}
    topology = {}
    for obj in layers:
        tree, vertices, triangles = world_tree(obj, depsgraph)
        trees[obj.name] = tree
        body_counts[obj.name] = len(body_tree.overlap(tree))
        topology[obj.name] = {"vertices": vertices, "triangles": triangles}
    pair_counts = {}
    for first_index, first in enumerate(layers):
        for second in layers[first_index + 1:]:
            pair_counts[first.name + "::" + second.name] = len(trees[first.name].overlap(trees[second.name]))
    return body_counts, pair_counts, topology


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def hide_hair(scene):
    hidden = []
    for obj in scene.objects:
        is_hair = obj.name.startswith(("Groom_", "AevryndFemaleTargetScalp")) or obj.type == "CURVES"
        is_face_fibre = "Brow" in obj.name or obj.name.endswith(("UpperLashes", "LowerLashes"))
        if is_hair and not is_face_fibre and not obj.hide_render:
            obj.hide_render = True
            hidden.append(obj.name)
    return hidden


def render(scene, label, location, target, lens, size):
    camera = scene.camera
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    path = RENDER_DIR / (label + ".png")
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return str(path)


RENDER_DIR.mkdir(parents=True, exist_ok=True)
variants = []
for label, depth in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    bpy.context.view_layer.update()
    body = bpy.data.objects[BODY]
    layers = build_layers(depth)
    bpy.context.view_layer.update()
    body_counts, pair_counts, topology = overlap_counts(body, layers)
    hidden = hide_hair(scene)
    rendered = [
        render(scene, label + "-face-front", (0.0, -0.72, 1.430), (0.0, -0.060, 1.420), 88, (1000, 1000)),
        render(scene, label + "-mouth-front", (0.0, -0.43, 1.388), (0.0, -0.105, 1.386), 135, (1200, 700)),
        render(scene, label + "-mouth-oblique", (0.21, -0.39, 1.392), (0.0, -0.100, 1.386), 128, (1200, 700)),
    ]
    open_key = body.data.shape_keys.key_blocks.get(OPEN_KEY)
    if open_key:
        open_key.value = 1.5
        bpy.context.view_layer.update()
        rendered.append(render(scene, label + "-mouth-open", (0.0, -0.43, 1.388), (0.0, -0.100, 1.386), 135, (1200, 700)))
        open_key.value = 0.0
    for name in hidden:
        bpy.data.objects[name].hide_render = False
    failures = {name: count for name, count in body_counts.items() if count}
    pair_failures = {name: count for name, count in pair_counts.items() if count}
    status = "TECHNICAL_PASS" if not failures and not pair_failures else "TECHNICAL_FAIL"
    variants.append({"label": label, "depthOffsetM": depth, "bodyLayerTriangleOverlap": body_counts, "interLayerTriangleOverlap": pair_counts, "topology": topology, "rendered": rendered, "status": status})
    if label == SELECTED and status == "TECHNICAL_PASS":
        scene["aevrynd_mainline_revision"] = "v249r1034-owned-oral-layers"
        scene["aevrynd_mainline_parent"] = SOURCE.name
        scene["aevrynd_release_state"] = "TECHNICAL_PASS_VISUAL_REVIEW_REQUIRED"
        scene["aevrynd_website_promotion"] = "forbidden"
        scene["aevrynd_oral_layer_names"] = json.dumps(list(LAYERS))
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "method": "procedurally owned head-bound oral cavity, gum, tooth and tongue mesh layers behind the existing paired mouth boundaries",
    "layerOwnership": {name: "Aevrynd procedural asset" for name in LAYERS},
    "variants": variants,
    "provisionalSelection": None,
    "selectedVariant": None,
    "topologyDiscovery": {
        "mainFaceStillCoversMouth": True,
        "mainVisibleFaceComponentVertices": 13583,
        "detachedLipShells": 2,
        "verticesPerLipShell": 68,
        "boundaryEdgesPerLipShell": 38,
        "hiddenInternalMouthComponentVertices": 226,
        "existingNamedOralObjects": 0,
        "requiredNextStep": "cut one contiguous mouth aperture, remove the hidden broken source components, then attach a weighted inner rim before rebuilding oral layers",
    },
    "websitePromotionApproved": False,
    "status": "REJECTED_ALL_VARIANTS_COLLISION_AND_OCCLUSION",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1034_ORAL_LAYERS=" + json.dumps({"output": str(OUTPUT), "variants": [{"label": item["label"], "bodyFailures": sum(1 for count in item["bodyLayerTriangleOverlap"].values() if count), "pairFailures": sum(1 for count in item["interLayerTriangleOverlap"].values() if count), "status": item["status"]} for item in variants]}, sort_keys=True))
