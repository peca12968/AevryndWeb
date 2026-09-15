"""Cover the r1035 topology proof with a smooth owned deformable lip annulus."""

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-contiguous-mouth-aperture-r1035-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-continuous-lip-patch-r1036-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1036-continuous-lip-patch-sweep.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r1036-continuous-lip-patch-sweep"
BODY = "AevryndFemaleCC0Baseline_v259"
RIG = "AevryndFemaleRig"
PATCH = "Aevrynd_ContinuousLipPatch_R1036"
OPEN_KEY = "Aevrynd_MouthOpenTest_R1030"
SMILE_KEY = "Aevrynd_SmileTest_R1030"
ORAL_LAYERS = (
    "Aevrynd_OralBackWall_R1035", "Aevrynd_UpperGum_R1035", "Aevrynd_LowerGum_R1035",
    "Aevrynd_UpperTeeth_R1035", "Aevrynd_LowerTeeth_R1035", "Aevrynd_Tongue_R1035",
)
VARIANTS = (
    ("a-closed-soft", 0.0009, 0.00045, 0.00035),
    ("b-natural-slit", 0.00135, 0.00070, 0.00055),
    ("c-relaxed-open", 0.00180, 0.00100, 0.00080),
)
SELECTED = "b-natural-slit"
SEGMENTS = 64
CENTER_Z = 1.3890


def material(name, color, roughness, subsurface):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = next(node for node in mat.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    if "Subsurface Weight" in bsdf.inputs:
        bsdf.inputs["Subsurface Weight"].default_value = subsurface
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = 0.08
    mat["aevrynd_owned_procedural"] = True
    mat["aevrynd_layer_revision"] = "v249r1036"
    return mat


def evaluated_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    mesh.calc_loop_triangles()
    triangles = [tuple(triangle.vertices) for triangle in mesh.loop_triangles]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, triangles, all_triangles=True), triangles


def front_surface_y(tree, x, z):
    hit = tree.ray_cast(Vector((x, -0.300, z)), Vector((0.0, 1.0, 0.0)), 0.5)
    return hit[0].y if hit[0] is not None else -0.134


def profile_z(theta, ring, upper_gap, lower_gap):
    sine = math.sin(theta)
    x = math.cos(theta)
    upper = sine >= 0.0
    arc = abs(sine)
    if ring == 0:
        amplitude = 0.0105 if upper else 0.0100
    elif ring == 1:
        amplitude = 0.0062 if upper else 0.0057
    else:
        amplitude = upper_gap if upper else lower_gap
    z = CENTER_Z + (amplitude * arc if upper else -amplitude * arc)
    if upper:
        world_x = 0.038 * x
        cupid = math.exp(-0.5 * ((abs(world_x) - 0.0105) / 0.0040) ** 2)
        notch = math.exp(-0.5 * (world_x / 0.0036) ** 2)
        influence = (1.0, 0.72, 0.42)[ring]
        z += influence * (0.0010 * cupid - 0.00050 * notch)
    return z


def build_patch(body, upper_gap, lower_gap, forward):
    scene = bpy.context.scene
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    body_tree, _ = evaluated_tree(body, depsgraph)
    radii = (0.0380, 0.0335, 0.0290)
    ring_forward = (0.00020, 0.0018 + forward * 0.30, 0.0035 + forward)
    vertices = []
    metadata = []
    outer_y = []
    for index in range(SEGMENTS):
        theta = 2.0 * math.pi * index / SEGMENTS
        x = radii[0] * math.cos(theta)
        z = profile_z(theta, 0, upper_gap, lower_gap)
        outer_y.append(front_surface_y(body_tree, x, z) - ring_forward[0])
    for ring in range(3):
        for index in range(SEGMENTS):
            theta = 2.0 * math.pi * index / SEGMENTS
            x = radii[ring] * math.cos(theta)
            z = profile_z(theta, ring, upper_gap, lower_gap)
            y_reference = outer_y[index]
            y = y_reference - ring_forward[ring]
            vertices.append((x, y, z))
            metadata.append((ring, theta))
    faces = []
    for ring in range(2):
        first = ring * SEGMENTS
        second = (ring + 1) * SEGMENTS
        for index in range(SEGMENTS):
            nxt = (index + 1) % SEGMENTS
            faces.append((first + index, first + nxt, second + nxt, second + index))
    mesh = bpy.data.meshes.new(PATCH + "_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(material("Aevrynd_LipVermilionMat_R1036", (0.185, 0.040, 0.038), 0.59, 0.14))
    mesh.update()
    patch = bpy.data.objects.new(PATCH, mesh)
    scene.collection.objects.link(patch)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    world = patch.matrix_world.copy()
    patch.parent = bpy.data.objects[RIG]
    patch.parent_type = "BONE"
    patch.parent_bone = "head"
    patch.matrix_world = world
    patch["aevrynd_layer_owner"] = "Aevrynd"
    patch["aevrynd_layer_revision"] = "v249r1036"
    patch["aevrynd_layer_role"] = "continuous outer vermilion to inner mouth margin"

    patch.shape_key_add(name="Basis", from_mix=False)
    open_key = patch.shape_key_add(name=OPEN_KEY, from_mix=False)
    smile_key = patch.shape_key_add(name=SMILE_KEY, from_mix=False)
    for vertex_index, (ring, theta) in enumerate(metadata):
        sine = math.sin(theta)
        cosine = math.cos(theta)
        inner = (0.22, 0.62, 1.0)[ring]
        if sine >= 0.0:
            open_key.data[vertex_index].co.z += 0.00075 * inner * abs(sine)
        else:
            open_key.data[vertex_index].co.z -= 0.00310 * inner * abs(sine)
            open_key.data[vertex_index].co.y += 0.00030 * inner * abs(sine)
        corner = abs(cosine) ** 5
        smile_key.data[vertex_index].co.x += math.copysign(0.0022 * corner, cosine)
        smile_key.data[vertex_index].co.z += 0.00165 * corner
        smile_key.data[vertex_index].co.y += 0.00018 * corner
    open_key.value = 0.0
    smile_key.value = 0.0
    return patch, {"vertices": len(vertices), "polygons": len(faces), "segments": SEGMENTS, "rings": 3, "shapeKeys": [block.name for block in patch.data.shape_keys.key_blocks]}


def body_self_collision(body):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    tree, triangles = evaluated_tree(body, depsgraph)
    pairs = [(first, second) for first, second in tree.overlap(tree) if first < second and set(triangles[first]).isdisjoint(triangles[second])]
    return {"nonAdjacentPairs": len(pairs), "samplePairs": [list(pair) for pair in pairs[:24]], "status": "PASS" if not pairs else "FAIL"}


def collision(body, patch, oral_layers):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    body_tree, _ = evaluated_tree(body, depsgraph)
    patch_tree, _ = evaluated_tree(patch, depsgraph)
    body_patch = len(body_tree.overlap(patch_tree))
    patch_oral = {}
    for obj in oral_layers:
        tree, _ = evaluated_tree(obj, depsgraph)
        patch_oral[obj.name] = len(patch_tree.overlap(tree))
    return {"bodyPatchTriangleOverlap": body_patch, "patchOralLayerTriangleOverlap": patch_oral, "status": "PASS" if body_patch == 0 and not any(patch_oral.values()) else "FAIL"}


def expression_audit(body, patch, oral_layers, expression):
    body_key = body.data.shape_keys.key_blocks.get(expression)
    patch_key = patch.data.shape_keys.key_blocks.get(expression)
    body_old = float(body_key.value) if body_key else 0.0
    patch_old = float(patch_key.value) if patch_key else 0.0
    if body_key:
        body_key.value = 1.0
    if patch_key:
        patch_key.value = 1.0
    bpy.context.view_layer.update()
    result = {"bodySelfCollision": body_self_collision(body), "patchCollision": collision(body, patch, oral_layers)}
    if body_key:
        body_key.value = body_old
    if patch_key:
        patch_key.value = patch_old
    bpy.context.view_layer.update()
    result["status"] = "PASS" if result["bodySelfCollision"]["status"] == "PASS" and result["patchCollision"]["status"] == "PASS" else "FAIL"
    return result


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
for label, upper_gap, lower_gap, forward in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    bpy.context.view_layer.update()
    body = bpy.data.objects[BODY]
    oral_layers = [bpy.data.objects[name] for name in ORAL_LAYERS]
    patch, topology = build_patch(body, upper_gap, lower_gap, forward)
    bpy.context.view_layer.update()
    neutral_self = body_self_collision(body)
    neutral_collision = collision(body, patch, oral_layers)
    expressions = {expression: expression_audit(body, patch, oral_layers, expression) for expression in (OPEN_KEY, SMILE_KEY)}
    hidden = hide_hair(scene)
    rendered = [
        render(scene, label + "-face-front", (0.0, -0.72, 1.430), (0.0, -0.060, 1.420), 88, (1000, 1000)),
        render(scene, label + "-mouth-front", (0.0, -0.43, 1.388), (0.0, -0.105, 1.386), 135, (1200, 700)),
        render(scene, label + "-mouth-oblique", (0.21, -0.39, 1.392), (0.0, -0.100, 1.386), 128, (1200, 700)),
    ]
    for expression in (OPEN_KEY, SMILE_KEY):
        body.data.shape_keys.key_blocks[expression].value = 1.0
        patch.data.shape_keys.key_blocks[expression].value = 1.0
        bpy.context.view_layer.update()
        rendered.append(render(scene, label + "-" + ("open" if expression == OPEN_KEY else "smile"), (0.0, -0.43, 1.388), (0.0, -0.100, 1.386), 135, (1200, 700)))
        body.data.shape_keys.key_blocks[expression].value = 0.0
        patch.data.shape_keys.key_blocks[expression].value = 0.0
    for name in hidden:
        bpy.data.objects[name].hide_render = False
    technical = neutral_self["status"] == "PASS" and neutral_collision["status"] == "PASS" and all(item["status"] == "PASS" for item in expressions.values())
    item = {"label": label, "neutralInnerGapM": {"upper": upper_gap, "lower": lower_gap}, "forwardOffsetM": forward, "topology": topology, "neutralBodySelfCollision": neutral_self, "neutralPatchCollision": neutral_collision, "expressionAudit": expressions, "rendered": rendered, "status": "TECHNICAL_PASS" if technical else "TECHNICAL_FAIL"}
    variants.append(item)
    if label == SELECTED and technical:
        scene["aevrynd_mainline_revision"] = "v249r1036-continuous-lip-patch"
        scene["aevrynd_mainline_parent"] = SOURCE.name
        scene["aevrynd_release_state"] = "TECHNICAL_PASS_VISUAL_REVIEW_REQUIRED"
        scene["aevrynd_website_promotion"] = "forbidden"
        scene["aevrynd_lip_patch"] = PATCH
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {"source": str(SOURCE), "output": str(OUTPUT), "method": "three-ring 64-segment owned lip annulus sampled above the face, with narrow neutral aperture plus matching open and smile shape keys", "variants": variants, "provisionalSelection": SELECTED, "selectedVariant": None, "websitePromotionApproved": False, "status": "VISUAL_REVIEW_REQUIRED"}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1036_LIP_PATCH=" + json.dumps({"output": str(OUTPUT), "variants": [{"label": item["label"], "bodyPatch": item["neutralPatchCollision"]["bodyPatchTriangleOverlap"], "expression": {name: value["status"] for name, value in item["expressionAudit"].items()}, "status": item["status"]} for item in variants]}, sort_keys=True))
