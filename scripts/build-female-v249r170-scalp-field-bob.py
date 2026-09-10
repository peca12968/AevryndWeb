import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-deform-matched-scalp-r163.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-scalp-field-bob-r170.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-scalp-field-bob-r170.build-report.json"
SCALP = "AevryndFemaleDeformMatchedScalp_v249r163"
OLD_HAIR = "AevryndFemaleOwnedCurlyHairMain_v249r162"
RIG = "AevryndFemaleRig"
GUIDES = "AevryndFemaleScalpFieldGuides_v249r170"
FOLLOWERS = "AevryndFemaleScalpFieldFollowers_v249r170"
POINTS = 24
FOLLOWERS_PER_ROOT = 2
GUIDE_COUNT = 260


def clamp(value, low, high):
    return max(low, min(high, value))


def smoothstep(value):
    value = clamp(value, 0.0, 1.0)
    return value * value * (3.0 - 2.0 * value)


def fract(value):
    return value - math.floor(value)


def rnd(index, salt):
    return fract(math.sin(index * 12.9898 + salt * 78.233) * 43758.5453)


def bezier(p0, p1, p2, p3, t):
    u = 1.0 - t
    return p0 * (u ** 3) + p1 * (3.0 * u * u * t) + p2 * (3.0 * u * t * t) + p3 * (t ** 3)


def evaluated_roots(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    normal_matrix = evaluated.matrix_world.to_3x3().inverted().transposed()
    roots = []
    for vertex in mesh.vertices:
        position = evaluated.matrix_world @ vertex.co
        normal = (normal_matrix @ vertex.normal).normalized()
        roots.append((position, normal))
    evaluated.to_mesh_clear()
    return roots


def choose_guides(roots, count):
    # Deterministic farthest-point coverage across the actual deform-matched scalp.
    first = min(range(len(roots)), key=lambda index: (roots[index][0].y, abs(roots[index][0].x)))
    chosen = [first]
    nearest = [(root[0] - roots[first][0]).length_squared for root in roots]
    while len(chosen) < min(count, len(roots)):
        candidate = max(range(len(roots)), key=lambda index: nearest[index])
        chosen.append(candidate)
        point = roots[candidate][0]
        for index, root in enumerate(roots):
            distance = (root[0] - point).length_squared
            if distance < nearest[index]:
                nearest[index] = distance
    return chosen


def strand(root, normal, index, variant, is_guide=False):
    # Hair leaves the scalp along the surface normal, then follows a coherent
    # middle-part field toward the side/back before gravity forms the bob.
    side = -1.0 if root.x < 0.0 else 1.0
    if abs(root.x) < 0.002:
        side = -1.0 if rnd(index, 9.0 + variant) < 0.5 else 1.0
    side_axis = Vector((side, 0.0, 0.0))
    tangent = side_axis - normal * side_axis.dot(normal)
    if tangent.length < 1e-6:
        tangent = Vector((side, 0.15, 0.0))
    tangent.normalize()
    back = Vector((0.0, 1.0, 0.0))
    back -= normal * back.dot(normal)
    if back.length > 1e-6:
        back.normalize()
    front_weight = smoothstep((-root.y + 0.005) / 0.115)
    flow = (tangent * (1.0 + 0.45 * front_weight) + back * (0.20 + 0.35 * front_weight)).normalized()

    family = int(index * 0.61803398875) % 97
    phase = rnd(family, 1.0) * math.tau
    length_jitter = (rnd(index * 3 + variant, 2.0) - 0.5) * 0.045
    lateral_jitter = (rnd(index * 5 + variant, 3.0) - 0.5) * 0.016
    p0 = root + normal * 0.0022
    p1 = p0 + normal * 0.018 + flow * 0.030
    end_x = side * (0.142 + 0.018 * rnd(index, 4.0)) + lateral_jitter
    end_y = clamp(root.y + 0.030 + 0.012 * rnd(index, 5.0), -0.005, 0.105)
    end_z = 1.425 + length_jitter + 0.020 * smoothstep((root.y + 0.12) / 0.20)
    p3 = Vector((end_x, end_y, end_z))
    p2 = Vector((side * (0.112 + 0.018 * rnd(index, 6.0)), end_y, max(1.545, root.z - 0.055)))

    result = []
    for point_index in range(POINTS):
        t = point_index / (POINTS - 1)
        point = bezier(p0, p1, p2, p3, t)
        lock_weight = smoothstep((t - 0.25) / 0.75)
        shared_wave = math.sin(phase + t * math.tau * 0.72) * 0.0060 * lock_weight
        fine_wave = math.sin(phase * 1.7 + t * math.tau * 1.35) * 0.0012 * lock_weight
        point.x += side * (shared_wave + fine_wave * (variant - 0.5))
        point.y += shared_wave * 0.24
        if not is_guide:
            # Followers separate only after they have safely left the scalp.
            separation = smoothstep(t / 0.32)
            point.x += side * (variant - 0.5) * 0.0018 * separation
            point.y += (variant - 0.5) * 0.0010 * separation
        result.append(point)
    return result


def create_curves(name, curves, material, root_radius, tip_radius, layer):
    data = bpy.data.hair_curves.new(name + "Data")
    data.add_curves([len(curve) for curve in curves])
    radius = data.attributes.new("radius", "FLOAT", "POINT")
    flat = 0
    for curve in curves:
        for point_index, point in enumerate(curve):
            t = point_index / (len(curve) - 1)
            data.points[flat].position = point
            radius.data[flat].value = root_radius * (1.0 - t) + tip_radius * t
            flat += 1
    data.materials.append(material)
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.visible_shadow = False
    obj["aevrynd_layer"] = layer
    obj["aevrynd_revision"] = "v249r170"
    obj["aevrynd_runtime_dependency"] = "none"
    obj["aevrynd_collision_status"] = "PENDING_STRICT_AUDIT"
    return obj


def bone_parent(obj, rig):
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = world


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
scalp = bpy.data.objects[SCALP]
roots = evaluated_roots(scalp)
guide_indices = choose_guides(roots, GUIDE_COUNT)
guide_curves = [strand(roots[index][0], roots[index][1], index, 0.5, True) for index in guide_indices]
follower_curves = []
family_ids = []
for index, (root, normal) in enumerate(roots):
    for variant in range(FOLLOWERS_PER_ROOT):
        follower_curves.append(strand(root, normal, index, variant, False))
        family_ids.append(index)

hair_mat = bpy.data.materials.get("AevryndPrincipledHair_v249r170") or bpy.data.materials.new("AevryndPrincipledHair_v249r170")
hair_mat.use_nodes = True
nodes = hair_mat.node_tree.nodes
nodes.clear()
output = nodes.new("ShaderNodeOutputMaterial")
fiber = nodes.new("ShaderNodeBsdfHairPrincipled")
fiber.parametrization = "COLOR"
fiber.inputs["Color"].default_value = (0.020, 0.0060, 0.0027, 1.0)
fiber.inputs["Roughness"].default_value = 0.48
fiber.inputs["Radial Roughness"].default_value = 0.62
fiber.inputs["Coat"].default_value = 0.020
fiber.inputs["IOR"].default_value = 1.52
hair_mat.node_tree.links.new(fiber.outputs["BSDF"], output.inputs["Surface"])

guide_obj = create_curves(GUIDES, guide_curves, hair_mat, 0.000060, 0.000012, "hair.guides.primary")
follow_obj = create_curves(FOLLOWERS, follower_curves, hair_mat, 0.000044, 0.000007, "hair.followers.render")
family = follow_obj.data.attributes.new("aevrynd_clump_family", "INT", "CURVE")
for index, family_id in enumerate(family_ids):
    family.data[index].value = family_id
rig = bpy.data.objects[RIG]
bone_parent(guide_obj, rig)
bone_parent(follow_obj, rig)

old_hair = bpy.data.objects[OLD_HAIR]
old_hair.hide_render = True
old_hair.hide_viewport = True
old_hair["aevrynd_replaced_by"] = f"{GUIDES},{FOLLOWERS}"

scalp_mat = bpy.data.materials.get("AevryndScalpShadow_v249r170") or bpy.data.materials.new("AevryndScalpShadow_v249r170")
scalp_mat.use_nodes = True
scalp_bsdf = next(node for node in scalp_mat.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
scalp_bsdf.inputs["Base Color"].default_value = (0.010, 0.0030, 0.0014, 1.0)
scalp_bsdf.inputs["Roughness"].default_value = 0.86
scalp_bsdf.inputs["Specular IOR Level"].default_value = 0.16
scalp.data.materials.clear()
scalp.data.materials.append(scalp_mat)
scalp["aevrynd_layer"] = "hair.scalp.foundation"

scene["aevrynd_revision"] = "v249r170"
scene["aevrynd_candidate_status"] = "COLLISION_AND_VISUAL_REVIEW_PENDING"
scene["aevrynd_hair_layers"] = ["hair.scalp.foundation", "hair.guides.primary", "hair.followers.render"]
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "source": str(SOURCE), "output": str(OUTPUT),
    "scalpRootCount": len(roots), "primaryGuides": len(guide_curves),
    "followersPerRoot": FOLLOWERS_PER_ROOT, "followCurves": len(follower_curves),
    "guidePoints": len(guide_obj.data.points), "followPoints": len(follow_obj.data.points),
    "combinedHairPoints": len(guide_obj.data.points) + len(follow_obj.data.points),
    "layers": ["hair.scalp.foundation", "hair.guides.primary", "hair.followers.render"],
    "shader": "Principled Hair BSDF", "runtimeDependency": "none",
    "status": "COLLISION_AND_VISUAL_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R170_BUILD=" + json.dumps(report, sort_keys=True))
