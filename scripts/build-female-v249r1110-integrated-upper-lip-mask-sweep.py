"""Render the owned upper lip on the continuous body mesh instead of a floating geometry layer."""
from pathlib import Path
import json

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-lip-surface-balance-r1106-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-integrated-upper-lip-r1110-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1110-integrated-upper-lip-mask-sweep.study.json"
OUT = ROOT.parent / "Temp" / "female-realism" / "v249r1110-integrated-upper-lip-mask-sweep"
BODY = "AevryndFemaleCC0PalpebralClosure_R1097"
DONOR = "AevryndFemaleCC0Baseline_v259"
PATCH = "Aevrynd_ContinuousUpperLip_R1105"
OPEN_KEY = "Aevrynd_MouthOpenTest_R1030"
SMILE_KEY = "Aevrynd_SmileTest_R1030"
MASK = "aevrynd_upper_lip_tint_r1110"
FRAMES = (1, 20, 33, 61)
VARIANTS = (("a-subtle", 0.55), ("b-balanced", 0.75), ("c-rich", 0.95))
SELECTED = "b-balanced"


def active_coordinates(obj):
    blocks = obj.data.shape_keys.key_blocks
    points = [item.co.copy() for item in blocks[0].data]
    for block in blocks[1:]:
        if block.mute or abs(block.value) < 1e-8:
            continue
        for index, item in enumerate(block.data):
            points[index] += block.value * (item.co - block.relative_key.data[index].co)
    return points


def group_weights(obj, name):
    group = obj.vertex_groups[name]
    result = {}
    for vertex in obj.data.vertices:
        for assignment in vertex.groups:
            if assignment.group == group.index:
                result[vertex.index] = assignment.weight
                break
    return result


def donor_upper_lip(donor):
    weights = group_weights(donor, "lips")
    points = active_coordinates(donor)
    faces = []
    for polygon in donor.data.polygons:
        if not all(weights.get(index, 0.0) >= 0.60 for index in polygon.vertices):
            continue
        centre = sum((points[index] for index in polygon.vertices), Vector()) / len(polygon.vertices)
        if centre.z >= 1.3885 and centre.y <= -0.1300:
            faces.append(tuple(polygon.vertices))
    indices = sorted({index for face in faces for index in face})
    return indices, faces, weights, points


def add_integrated_mask(body, donor):
    donor_indices, donor_faces, donor_weights, donor_points = donor_upper_lip(donor)
    body_points = active_coordinates(body)
    tree = KDTree(len(body_points))
    for index, point in enumerate(body_points):
        tree.insert(point, index)
    tree.balance()
    mapping = {}
    distances = []
    for donor_index in donor_indices:
        _point, body_index, distance = tree.find(donor_points[donor_index])
        if body_index in mapping.values():
            raise RuntimeError("Upper-lip mapping is not one-to-one")
        mapping[donor_index] = body_index
        distances.append(distance)
    if max(distances) > 0.0006:
        raise RuntimeError(f"Upper-lip mapping exceeds 0.6 mm: {max(distances) * 1000.0:.4f} mm")
    if MASK in body.data.attributes:
        body.data.attributes.remove(body.data.attributes[MASK])
    attribute = body.data.attributes.new(MASK, "FLOAT", "POINT")
    values = []
    for donor_index, body_index in mapping.items():
        # Retain a small edge response while letting the original lips group
        # soften the vermilion boundary under subdivision.
        value = max(0.35, min(1.0, (donor_weights[donor_index] - 0.45) / 0.55))
        attribute.data[body_index].value = value
        values.append(value)
    body_faces = {frozenset(polygon.vertices) for polygon in body.data.polygons}
    mapped_faces = [tuple(mapping[index] for index in face) for face in donor_faces]
    return {
        "attribute": MASK,
        "vertices": len(mapping),
        "uniqueBodyVertices": len(set(mapping.values())),
        "donorFaces": len(donor_faces),
        "matchingBodyFaces": sum(frozenset(face) in body_faces for face in mapped_faces),
        "maximumDistanceMm": max(distances) * 1000.0,
        "meanDistanceMm": sum(distances) / len(distances) * 1000.0,
        "minimumMask": min(values),
        "maximumMask": max(values),
    }


def insert_upper_lip_shader(body, strength_value):
    source = body.material_slots[0].material
    material = source.copy()
    material.name = f"Aevrynd_CC0_ContinuousLip_R1110_{int(strength_value * 100):02d}"
    body.data.materials[0] = material
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = next(node for node in nodes if node.bl_idname == "ShaderNodeBsdfPrincipled")
    base = shader.inputs["Base Color"]
    previous = base.links[0].from_socket if base.links else None
    for link in list(base.links):
        links.remove(link)
    attribute = nodes.new("ShaderNodeAttribute")
    attribute.name = "Aevrynd Integrated Upper Lip Mask R1110"
    attribute.attribute_name = MASK
    strength = nodes.new("ShaderNodeMath")
    strength.name = "Aevrynd Integrated Upper Lip Strength R1110"
    strength.operation = "MULTIPLY"
    strength.inputs[1].default_value = strength_value
    mix = nodes.new("ShaderNodeMixRGB")
    mix.name = "Aevrynd Integrated Upper Lip Vermilion R1110"
    mix.blend_type = "MIX"
    mix.inputs[2].default_value = (0.115, 0.018, 0.016, 1.0)
    links.new(attribute.outputs["Fac"], strength.inputs[0])
    links.new(strength.outputs[0], mix.inputs[0])
    if previous:
        links.new(previous, mix.inputs[1])
    else:
        mix.inputs[1].default_value = base.default_value
    links.new(mix.outputs[0], base)
    return {"material": material.name, "strength": strength_value, "targetLinearRgba": [0.115, 0.018, 0.016, 1.0]}


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


def self_collision(obj):
    tree, triangles = world_tree(obj)
    pairs = [(a, b) for a, b in tree.overlap(tree) if a < b and set(triangles[a]).isdisjoint(triangles[b])]
    return {"nonAdjacentPairs": len(pairs), "samplePairs": [list(pair) for pair in pairs[:20]]}


def set_pose(body, pose):
    keys = body.data.shape_keys.key_blocks
    keys[OPEN_KEY].value = 1.0 if pose == "open" else 0.0
    keys[SMILE_KEY].value = 1.0 if pose == "smile" else 0.0


def audit(scene, body):
    poses = {}
    scene.frame_set(1)
    for pose in ("neutral", "open", "smile"):
        set_pose(body, pose)
        bpy.context.view_layer.update()
        poses[pose] = self_collision(body)
    set_pose(body, "neutral")
    frames = {}
    for frame in FRAMES:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        frames[str(frame)] = self_collision(body)
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
for label, strength in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    body = bpy.data.objects[BODY]
    donor = bpy.data.objects[DONOR]
    patch = bpy.data.objects[PATCH]
    hide_hair(scene)
    patch.hide_render = True
    patch.hide_viewport = True
    patch["aevrynd_release_excluded"] = True
    patch["aevrynd_replaced_by"] = "continuous body material mask r1110"
    source_poses, source_frames = audit(scene, body)
    mask = add_integrated_mask(body, donor)
    shader = insert_upper_lip_shader(body, strength)
    poses, frames = audit(scene, body)
    technical_pass = all(poses[key]["nonAdjacentPairs"] <= source_poses[key]["nonAdjacentPairs"] for key in poses) and all(
        frames[key]["nonAdjacentPairs"] <= source_frames[key]["nonAdjacentPairs"] for key in frames
    )
    scene.frame_set(1)
    set_pose(body, "neutral")
    renders = [
        render(scene, f"{label}-neutral-mouth-front", (0.0, -0.43, 1.391), (0.0, -0.115, 1.386), 135, (1100, 720)),
        render(scene, f"{label}-neutral-face-front", (0.0, -0.72, 1.445), (0.0, -0.025, 1.445), 88, (1000, 1000)),
    ]
    set_pose(body, "open")
    renders.append(render(scene, f"{label}-open-mouth-front", (0.0, -0.43, 1.391), (0.0, -0.115, 1.386), 135, (1100, 720)))
    set_pose(body, "smile")
    renders.append(render(scene, f"{label}-smile-mouth-front", (0.0, -0.43, 1.391), (0.0, -0.115, 1.386), 135, (1100, 720)))
    set_pose(body, "neutral")
    variants.append({
        "label": label,
        "mask": mask,
        "shader": shader,
        "sourcePoseSelfCollision": source_poses,
        "sourceFrameSelfCollision": source_frames,
        "poseSelfCollision": poses,
        "frameSelfCollision": frames,
        "excludedGeometryLayer": PATCH,
        "technicalStatus": "TECHNICAL_PASS" if technical_pass else "TECHNICAL_FAIL",
        "renders": renders,
    })
    if label == SELECTED and technical_pass:
        body["aevrynd_revision"] = "v249r1110-integrated-upper-lip"
        body["aevrynd_upper_lip_layer"] = "point-domain material mask on continuous body topology"
        scene["aevrynd_release_state"] = "VISUAL_REVIEW_PENDING"
        scene["aevrynd_website_promotion"] = "forbidden"
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))


selected_item = next((item for item in variants if item["label"] == SELECTED and item["technicalStatus"] == "TECHNICAL_PASS"), None)
report = {
    "revision": "v249r1110-integrated-upper-lip-mask-sweep",
    "source": str(SOURCE),
    "output": str(OUTPUT) if selected_item else None,
    "method": "map the owned donor upper-lip region one-to-one onto the active body's continuous topology, shade it through a point-domain mask, and exclude the former floating geometry patch",
    "variants": variants,
    "selectedVariant": SELECTED if selected_item else None,
    "websitePromotionApproved": False,
    "candidateStatus": "VISUAL_REVIEW_PENDING" if selected_item else "TECHNICAL_FAIL_DIAGNOSTIC_ONLY",
}
REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print("AEVRYND_R1110_INTEGRATED_LIP=" + json.dumps({
    "variants": [{
        "label": item["label"],
        "mask": item["mask"],
        "poses": {key: value["nonAdjacentPairs"] for key, value in item["poseSelfCollision"].items()},
        "frames": {key: value["nonAdjacentPairs"] for key, value in item["frameSelfCollision"].items()},
        "status": item["technicalStatus"],
    } for item in variants]
}, sort_keys=True))
