"""Extract the intact owned upper-lip surface as a rigged, expression-compatible layer."""
from pathlib import Path
import json

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-lower-wetline-r1102-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-continuous-upper-lip-r1105-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1105-continuous-upper-lip-donor-sweep.study.json"
OUT = ROOT.parent / "Temp" / "female-realism" / "v249r1105-continuous-upper-lip-donor-sweep"
BODY = "AevryndFemaleCC0PalpebralClosure_R1097"
DONOR = "AevryndFemaleCC0Baseline_v259"
PATCH = "Aevrynd_ContinuousUpperLip_R1105"
OPEN_KEY = "Aevrynd_MouthOpenTest_R1030"
SMILE_KEY = "Aevrynd_SmileTest_R1030"
FRAMES = (1, 20, 33, 61)
VARIANTS = (("a-close", 0.0002), ("b-balanced", 0.0004), ("c-clear", 0.0006))
SELECTED = "c-clear"


def active_coordinates(obj):
    blocks = obj.data.shape_keys.key_blocks
    points = [item.co.copy() for item in blocks[0].data]
    for block in blocks[1:]:
        if block.mute or abs(block.value) < 1e-8:
            continue
        for index, item in enumerate(block.data):
            points[index] += block.value * (item.co - block.relative_key.data[index].co)
    return points


def donor_faces(donor):
    group = donor.vertex_groups["lips"]
    weights = {}
    for vertex in donor.data.vertices:
        entries = [item.weight for item in vertex.groups if item.group == group.index]
        if entries:
            weights[vertex.index] = entries[0]
    points = active_coordinates(donor)
    selected = []
    for polygon in donor.data.polygons:
        if not all(weights.get(index, 0.0) >= 0.60 for index in polygon.vertices):
            continue
        centre = sum((points[index] for index in polygon.vertices), Vector()) / len(polygon.vertices)
        if centre.z >= 1.3885 and centre.y <= -0.1300:
            selected.append(tuple(polygon.vertices))
    return selected


def make_material():
    material = bpy.data.materials.new("Aevrynd_UpperLipVermilion_R1105")
    material.use_nodes = True
    shader = next(node for node in material.node_tree.nodes if node.bl_idname == "ShaderNodeBsdfPrincipled")
    shader.inputs["Base Color"].default_value = (0.165, 0.028, 0.024, 1.0)
    shader.inputs["Roughness"].default_value = 0.76
    if "Subsurface Weight" in shader.inputs:
        shader.inputs["Subsurface Weight"].default_value = 0.04
    if "Coat Weight" in shader.inputs:
        shader.inputs["Coat Weight"].default_value = 0.0
    return material


def build_patch(donor, body, offset):
    selected_faces = donor_faces(donor)
    used = sorted({index for face in selected_faces for index in face})
    remap = {old: new for new, old in enumerate(used)}
    basis = donor.data.shape_keys.key_blocks[0]
    vertices = []
    for index in used:
        point = basis.data[index].co.copy()
        point.x *= 0.92
        point.z = 1.3885 + (point.z - 1.3885) * 0.68
        vertices.append(point)
    faces = [tuple(remap[index] for index in face) for face in selected_faces]
    mesh = bpy.data.meshes.new(PATCH + "Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    patch = bpy.data.objects.new(PATCH, mesh)
    bpy.context.collection.objects.link(patch)
    for polygon in mesh.polygons:
        polygon.use_smooth = True

    patch.shape_key_add(name="Basis")
    donor_keys = donor.data.shape_keys.key_blocks
    patch_keys = patch.data.shape_keys.key_blocks
    for donor_key in donor_keys[1:]:
        key = patch.shape_key_add(name=donor_key.name)
        key.slider_min = donor_key.slider_min
        key.slider_max = donor_key.slider_max
        key.value = donor_key.value
        for new_index, old_index in enumerate(used):
            point = donor_key.data[old_index].co.copy()
            point.x *= 0.92
            point.z = 1.3885 + (point.z - 1.3885) * 0.68
            key.data[new_index].co = point
    for index, donor_key in enumerate(donor_keys):
        relative_index = list(donor_keys).index(donor_key.relative_key)
        patch_keys[index].relative_key = patch_keys[relative_index]

    for donor_group in donor.vertex_groups:
        values = []
        for new_index, old_index in enumerate(used):
            vertex = donor.data.vertices[old_index]
            entries = [item.weight for item in vertex.groups if item.group == donor_group.index]
            if entries:
                values.append((new_index, entries[0]))
        if not values:
            continue
        group = patch.vertex_groups.new(name=donor_group.name)
        for new_index, weight in values:
            group.add([new_index], weight, "REPLACE")

    subdivision = patch.modifiers.new("Aevrynd Upper Lip Subdivision R1105", "SUBSURF")
    source_subdivision = next(modifier for modifier in donor.modifiers if modifier.type == "SUBSURF")
    subdivision.levels = source_subdivision.levels
    subdivision.render_levels = source_subdivision.render_levels
    armature = patch.modifiers.new("Aevrynd Upper Lip Armature R1105", "ARMATURE")
    armature.object = bpy.data.objects["AevryndFemaleRig"]
    shrinkwrap = patch.modifiers.new("Aevrynd Upper Lip Surface Clearance R1105", "SHRINKWRAP")
    shrinkwrap.target = body
    shrinkwrap.wrap_method = "NEAREST_SURFACEPOINT"
    shrinkwrap.wrap_mode = "OUTSIDE_SURFACE"
    shrinkwrap.offset = offset
    mesh.materials.append(make_material())
    patch["aevrynd_layer"] = "upper_lip_vermilion"
    patch["aevrynd_source_object"] = donor.name
    patch["aevrynd_clearance_mm"] = offset * 1000.0
    return patch, {"faces": len(faces), "vertices": len(vertices), "shapeKeys": len(patch_keys), "vertexGroups": len(patch.vertex_groups)}


def world_tree(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    mesh.calc_loop_triangles()
    triangles = [tuple(item.vertices) for item in mesh.loop_triangles]
    tree = BVHTree.FromPolygons(vertices, triangles, all_triangles=True)
    evaluated.to_mesh_clear()
    return tree, triangles


def cross_collision(a, b):
    tree_a, _ = world_tree(a)
    tree_b, _ = world_tree(b)
    pairs = tree_a.overlap(tree_b)
    return {"trianglePairs": len(pairs), "samplePairs": [list(pair) for pair in pairs[:20]]}


def patch_self_collision(patch):
    tree, triangles = world_tree(patch)
    pairs = [(a, b) for a, b in tree.overlap(tree) if a < b and set(triangles[a]).isdisjoint(triangles[b])]
    return {"nonAdjacentPairs": len(pairs), "samplePairs": [list(pair) for pair in pairs[:20]]}


def set_pose(body, patch, pose):
    for obj in (body, patch):
        keys = obj.data.shape_keys.key_blocks
        keys[OPEN_KEY].value = 1.0 if pose == "open" else 0.0
        keys[SMILE_KEY].value = 1.0 if pose == "smile" else 0.0


def audit(scene, body, patch):
    poses = {}
    scene.frame_set(1)
    for pose in ("neutral", "open", "smile"):
        set_pose(body, patch, pose)
        bpy.context.view_layer.update()
        poses[pose] = {"bodyPatch": cross_collision(body, patch), "patchSelf": patch_self_collision(patch)}
    set_pose(body, patch, "neutral")
    frames = {}
    for frame in FRAMES:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        frames[str(frame)] = {"bodyPatch": cross_collision(body, patch), "patchSelf": patch_self_collision(patch)}
    scene.frame_set(1)
    return poses, frames


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def hide_hair(scene):
    for obj in scene.objects:
        name = obj.name.lower()
        if obj.type == "CURVES" or any(token in name for token in ("groom", "scalp", "haircard", "hairfiber")):
            if not any(token in name for token in ("brow", "lash")):
                obj.hide_render = True


def render(scene, label, location, target, lens, size):
    camera = scene.camera
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    path = OUT / f"{label}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return str(path)


OUT.mkdir(parents=True, exist_ok=True)
variants = []
for label, offset in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    body = bpy.data.objects[BODY]
    donor = bpy.data.objects[DONOR]
    hide_hair(scene)
    patch, inventory = build_patch(donor, body, offset)
    poses, frames = audit(scene, body, patch)
    collision_free = all(item["bodyPatch"]["trianglePairs"] == 0 and item["patchSelf"]["nonAdjacentPairs"] == 0 for item in list(poses.values()) + list(frames.values()))
    technical_status = "TECHNICAL_PASS" if collision_free else "TECHNICAL_FAIL"
    scene.frame_set(1)
    set_pose(body, patch, "neutral")
    renders = [
        render(scene, f"{label}-neutral-mouth-front", (0.0, -0.43, 1.391), (0.0, -0.115, 1.386), 135, (1100, 720)),
        render(scene, f"{label}-neutral-mouth-oblique", (-0.105, -0.43, 1.391), (0.0, -0.115, 1.386), 135, (1100, 720)),
        render(scene, f"{label}-neutral-face-front", (0.0, -0.72, 1.445), (0.0, -0.025, 1.445), 88, (1000, 1000)),
    ]
    if label == SELECTED:
        set_pose(body, patch, "open")
        renders.append(render(scene, f"{label}-open-mouth-front", (0.0, -0.43, 1.391), (0.0, -0.115, 1.386), 135, (1100, 720)))
        set_pose(body, patch, "smile")
        renders.append(render(scene, f"{label}-smile-mouth-front", (0.0, -0.43, 1.391), (0.0, -0.115, 1.386), 135, (1100, 720)))
        set_pose(body, patch, "neutral")
    variants.append({"label": label, "clearanceMm": offset * 1000.0, "inventory": inventory, "poseCollision": poses, "frameCollision": frames, "technicalStatus": technical_status, "renders": renders})
    if label == SELECTED and technical_status == "TECHNICAL_PASS":
        patch["aevrynd_revision"] = "v249r1105-continuous-upper-lip"
        scene["aevrynd_release_state"] = "VISUAL_REVIEW_PENDING"
        scene["aevrynd_website_promotion"] = "forbidden"
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "revision": "v249r1105-continuous-upper-lip-donor-sweep",
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "method": "extract the intact outward upper-lip faces from the retained owned body, copy all expression keys and armature weights, apply an owned vermilion material, and sweep explicit body clearance",
    "variants": variants,
    "selectedVariant": SELECTED,
    "externalDependencies": [],
    "websitePromotionApproved": False,
    "candidateStatus": "VISUAL_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print("AEVRYND_R1105_UPPER_LIP=" + json.dumps({"variants": [{"label": item["label"], "clearanceMm": item["clearanceMm"], "inventory": item["inventory"], "posePairs": {key: value["bodyPatch"]["trianglePairs"] for key, value in item["poseCollision"].items()}, "framePairs": {key: value["bodyPatch"]["trianglePairs"] for key, value in item["frameCollision"].items()}, "selfPairs": {key: value["patchSelf"]["nonAdjacentPairs"] for key, value in item["poseCollision"].items()}, "status": item["technicalStatus"]} for item in variants]}, sort_keys=True))
