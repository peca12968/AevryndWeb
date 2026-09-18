"""Smooth the upper-lip layer and restore a lower-lip-only vermilion response."""
from pathlib import Path
import json
import math

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-continuous-upper-lip-r1105-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-lip-surface-balance-r1106-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1106-lip-surface-balance.study.json"
OUT = ROOT.parent / "Temp" / "female-realism" / "v249r1106-lip-surface-balance"
BODY = "AevryndFemaleCC0PalpebralClosure_R1097"
PATCH = "Aevrynd_ContinuousUpperLip_R1105"
OPEN_KEY = "Aevrynd_MouthOpenTest_R1030"
SMILE_KEY = "Aevrynd_SmileTest_R1030"
FRAMES = (1, 20, 33, 61)
MASK = "aevrynd_lower_lip_tint_r1106"


def gaussian(value, centre, width):
    return math.exp(-0.5 * ((value - centre) / width) ** 2)


def smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def active_coordinates(body):
    blocks = body.data.shape_keys.key_blocks
    points = [item.co.copy() for item in blocks[0].data]
    for block in blocks[1:]:
        if block.mute or abs(block.value) < 1e-8:
            continue
        for index, item in enumerate(block.data):
            points[index] += block.value * (item.co - block.relative_key.data[index].co)
    return [body.matrix_world @ point for point in points]


def add_lower_lip_mask(body):
    if MASK in body.data.attributes:
        body.data.attributes.remove(body.data.attributes[MASK])
    attribute = body.data.attributes.new(MASK, "FLOAT", "POINT")
    points = active_coordinates(body)
    group = body.vertex_groups["lips"]
    count = 0
    maximum = 0.0
    for vertex in body.data.vertices:
        if not any(item.group == group.index for item in vertex.groups):
            continue
        point = points[vertex.index]
        if abs(point.x) > 0.031 or not 1.3715 < point.z < 1.3888 or point.y > -0.1315:
            continue
        horizontal = 1.0 - smoothstep((abs(point.x) - 0.020) / 0.011)
        depth = smoothstep((-point.y - 0.1315) / 0.0065)
        value = gaussian(point.z, 1.3818, 0.0072) * horizontal * depth
        if value <= 0.01:
            continue
        attribute.data[vertex.index].value = value
        count += 1
        maximum = max(maximum, value)
    return {"attribute": MASK, "vertices": count, "maximum": maximum}


def insert_lower_lip_shader(body):
    source = body.material_slots[0].material
    material = source.copy()
    material.name = "Aevrynd_CC0_RegionalSkin_R1106_LipBalance"
    body.data.materials[0] = material
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = next(node for node in nodes if node.bl_idname == "ShaderNodeBsdfPrincipled")
    base = shader.inputs["Base Color"]
    previous = base.links[0].from_socket if base.links else None
    for link in list(base.links):
        links.remove(link)
    attribute = nodes.new("ShaderNodeAttribute")
    attribute.name = "Aevrynd Lower Lip Mask R1106"
    attribute.attribute_name = MASK
    strength = nodes.new("ShaderNodeMath")
    strength.name = "Aevrynd Lower Lip Strength R1106"
    strength.operation = "MULTIPLY"
    strength.inputs[1].default_value = 1.0
    mix = nodes.new("ShaderNodeMixRGB")
    mix.name = "Aevrynd Lower Lip Vermilion R1106"
    mix.blend_type = "MIX"
    mix.inputs[2].default_value = (0.120, 0.015, 0.012, 1.0)
    links.new(attribute.outputs["Fac"], strength.inputs[0])
    links.new(strength.outputs[0], mix.inputs[0])
    if previous:
        links.new(previous, mix.inputs[1])
    else:
        mix.inputs[1].default_value = base.default_value
    links.new(mix.outputs[0], base)
    return {"material": material.name, "strength": 1.0, "targetLinearRgba": [0.120, 0.015, 0.012, 1.0]}


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


def self_collision(obj):
    tree, triangles = world_tree(obj)
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
        poses[pose] = {"bodyPatch": cross_collision(body, patch), "patchSelf": self_collision(patch)}
    set_pose(body, patch, "neutral")
    frames = {}
    for frame in FRAMES:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        frames[str(frame)] = {"bodyPatch": cross_collision(body, patch), "patchSelf": self_collision(patch)}
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


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
body = bpy.data.objects[BODY]
patch = bpy.data.objects[PATCH]
hide_hair(scene)
subdivision = next(modifier for modifier in patch.modifiers if modifier.type == "SUBSURF")
subdivision.levels = 2
subdivision.render_levels = 3
smooth = patch.modifiers.new("Aevrynd Upper Lip Boundary Smooth R1106", "SMOOTH")
smooth.factor = 0.35
smooth.iterations = 2
patch.modifiers.move(len(patch.modifiers) - 1, 1)
mask = add_lower_lip_mask(body)
material = insert_lower_lip_shader(body)
poses, frames = audit(scene, body, patch)
technical_pass = all(item["bodyPatch"]["trianglePairs"] == 0 and item["patchSelf"]["nonAdjacentPairs"] == 0 for item in list(poses.values()) + list(frames.values()))

OUT.mkdir(parents=True, exist_ok=True)
scene.frame_set(1)
set_pose(body, patch, "neutral")
renders = [
    render(scene, "neutral-mouth-front", (0.0, -0.43, 1.391), (0.0, -0.115, 1.386), 135, (1100, 720)),
    render(scene, "neutral-mouth-oblique", (-0.105, -0.43, 1.391), (0.0, -0.115, 1.386), 135, (1100, 720)),
    render(scene, "neutral-face-front", (0.0, -0.72, 1.445), (0.0, -0.025, 1.445), 88, (1000, 1000)),
]
set_pose(body, patch, "open")
renders.append(render(scene, "open-mouth-front", (0.0, -0.43, 1.391), (0.0, -0.115, 1.386), 135, (1100, 720)))
set_pose(body, patch, "smile")
renders.append(render(scene, "smile-mouth-front", (0.0, -0.43, 1.391), (0.0, -0.115, 1.386), 135, (1100, 720)))
set_pose(body, patch, "neutral")

status = "TECHNICAL_PASS" if technical_pass else "TECHNICAL_FAIL"
if technical_pass:
    patch["aevrynd_revision"] = "v249r1106-lip-surface-balance"
    body["aevrynd_lower_lip_material_revision"] = "v249r1106"
    scene["aevrynd_release_state"] = "VISUAL_REVIEW_PENDING"
    scene["aevrynd_website_promotion"] = "forbidden"
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "revision": "v249r1106-lip-surface-balance",
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "method": "increase the small upper-lip layer to subdivision level three and insert a lower-lip-only chromatic mask after the inherited regional skin color chain",
    "upperLipSubdivision": {"viewport": subdivision.levels, "render": subdivision.render_levels},
    "upperLipBoundarySmooth": {"factor": smooth.factor, "iterations": smooth.iterations, "modifierIndex": 1},
    "lowerLipMask": mask,
    "lowerLipMaterial": material,
    "poseCollision": poses,
    "frameCollision": frames,
    "technicalStatus": status,
    "renders": renders,
    "websitePromotionApproved": False,
    "candidateStatus": "VISUAL_REVIEW_PENDING" if technical_pass else "TECHNICAL_REJECTED",
}
REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print("AEVRYND_R1106_LIP_BALANCE=" + json.dumps({"mask": mask, "material": material, "posePairs": {key: value["bodyPatch"]["trianglePairs"] for key, value in poses.items()}, "framePairs": {key: value["bodyPatch"]["trianglePairs"] for key, value in frames.items()}, "patchSelf": {key: value["patchSelf"]["nonAdjacentPairs"] for key, value in poses.items()}, "status": status}, sort_keys=True))

