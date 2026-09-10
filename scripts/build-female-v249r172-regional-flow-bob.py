import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-deform-matched-scalp-r163.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-regional-flow-bob-r172.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-regional-flow-bob-r172.build-report.json"
SCALP = "AevryndFemaleDeformMatchedScalp_v249r163"
OLD_HAIR = "AevryndFemaleOwnedCurlyHairMain_v249r162"
RIG = "AevryndFemaleRig"
GUIDES = "AevryndFemaleScalpFieldGuides_v249r172"
FOLLOWERS = "AevryndFemaleScalpFieldFollowers_v249r172"
POINTS = 24
SAMPLES_PER_FACE = 3
GUIDE_COUNT = 320


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
    for polygon_index, polygon in enumerate(mesh.polygons):
        indices = list(polygon.vertices)
        for sample_index in range(SAMPLES_PER_FACE):
            # Sample a deterministic triangle fan. sqrt(u) gives uniform area
            # density inside each triangle and removes visible topology rows.
            triangle = 1 + ((polygon_index + sample_index) % max(1, len(indices) - 2))
            a = mesh.vertices[indices[0]]
            b = mesh.vertices[indices[triangle]]
            c = mesh.vertices[indices[triangle + 1]]
            u = math.sqrt(max(1e-6, rnd(polygon_index * 7 + sample_index, 11.0)))
            v = rnd(polygon_index * 11 + sample_index, 12.0)
            wa, wb, wc = 1.0 - u, u * (1.0 - v), u * v
            local_position = a.co * wa + b.co * wb + c.co * wc
            local_normal = (a.normal * wa + b.normal * wb + c.normal * wc).normalized()
            position = evaluated.matrix_world @ local_position
            normal = (normal_matrix @ local_normal).normalized()
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
    # Four regional fields keep the front frame, crown, temples and rear mass
    # from collapsing into one symmetric helmet-shaped cubic field.
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
    if root.y < -0.073:
        region = 0  # front frame: leave the forehead toward the temple
        flow = (tangent * 1.45 + back * 0.55).normalized()
        p2 = Vector((side * 0.142, -0.002, max(1.565, root.z - 0.030)))
        p3 = Vector((side * 0.160, 0.012, 1.445))
    elif abs(root.x) > 0.058 and root.y < 0.030:
        region = 1  # temple: sweep behind the ear before dropping
        flow = (tangent * 1.10 + back * 0.48).normalized()
        p2 = Vector((side * 0.148, 0.040, max(1.555, root.z - 0.040)))
        p3 = Vector((side * 0.158, 0.060, 1.425))
    elif root.y > 0.025:
        region = 3  # rear: travel backward instead of crossing to the sides
        flow = (back * 1.25 + tangent * 0.22).normalized()
        rear_x = clamp(root.x * 1.35, -0.125, 0.125)
        p2 = Vector((rear_x, 0.132, max(1.560, root.z - 0.035)))
        p3 = Vector((clamp(root.x * 1.55, -0.145, 0.145), 0.170, 1.415))
    else:
        region = 2  # crown: broad lateral arc with a slower gravity handoff
        flow = (tangent * 1.05 + back * 0.25).normalized()
        p2 = Vector((side * 0.140, 0.045, max(1.580, root.z - 0.020)))
        p3 = Vector((side * 0.162, 0.062, 1.435))

    family = region * 100 + int((root.y + 0.125) / 0.026) * 10 + int((abs(root.x) + 0.004) / 0.022)
    phase = rnd(family, 1.0) * math.tau
    length_jitter = (rnd(index * 3 + variant, 2.0) - 0.5) * 0.050
    lateral_jitter = (rnd(index * 5 + variant, 3.0) - 0.5) * 0.013
    p0 = root + normal * 0.0050
    p1 = p0 + normal * 0.024 + flow * 0.020
    p2.x += lateral_jitter * 0.45
    p2.y += (rnd(index, 5.0) - 0.5) * 0.010
    p3.x += lateral_jitter
    p3.y += (rnd(index, 6.0) - 0.5) * 0.016
    p3.z += length_jitter

    result = []
    for point_index in range(POINTS):
        t = point_index / (POINTS - 1)
        point = bezier(p0, p1, p2, p3, t)
        lock_weight = smoothstep((t - 0.25) / 0.75)
        shared_wave = math.sin(phase + t * math.tau * 0.62) * 0.0052 * lock_weight
        fine_wave = math.sin(phase * 1.7 + t * math.tau * 1.25) * 0.0010 * lock_weight
        point.x += side * (shared_wave + fine_wave * (variant - 0.5))
        point.y += shared_wave * 0.24
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
    obj["aevrynd_revision"] = "v249r172"
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
follower_curves = [strand(root, normal, index, rnd(index, 13.0), False) for index, (root, normal) in enumerate(roots)]
family_ids = []
for root, _normal in roots:
    family_ids.append(min(range(len(guide_indices)), key=lambda guide: (roots[guide_indices[guide]][0] - root).length_squared))

hair_mat = bpy.data.materials.get("AevryndPrincipledHair_v249r172") or bpy.data.materials.new("AevryndPrincipledHair_v249r172")
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

# Keep r163's density/noise-driven dithered alpha. r170/r171 accidentally
# replaced it with an opaque scalp material, which created the gray cap.
scalp_mat = bpy.data.materials["AevryndDeformMatchedScalpMaterial_v249r163"].copy()
scalp_mat.name = "AevryndDensityScalp_v249r172"
scalp_bsdf = next(node for node in scalp_mat.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
scalp_bsdf.inputs["Base Color"].default_value = (0.012, 0.0036, 0.0018, 1.0)
scalp_bsdf.inputs["Roughness"].default_value = 0.88
scalp_bsdf.inputs["Specular IOR Level"].default_value = 0.12
scalp.data.materials.clear()
scalp.data.materials.append(scalp_mat)
scalp["aevrynd_layer"] = "hair.scalp.foundation"

scene["aevrynd_revision"] = "v249r172"
scene["aevrynd_candidate_status"] = "COLLISION_AND_VISUAL_REVIEW_PENDING"
scene["aevrynd_hair_layers"] = ["hair.scalp.foundation", "hair.guides.primary", "hair.followers.render"]
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "source": str(SOURCE), "output": str(OUTPUT),
    "scalpRootCount": len(roots), "primaryGuides": len(guide_curves),
    "sampling": "three deterministic area samples per scalp face", "followCurves": len(follower_curves),
    "guidePoints": len(guide_obj.data.points), "followPoints": len(follow_obj.data.points),
    "combinedHairPoints": len(guide_obj.data.points) + len(follow_obj.data.points),
    "layers": ["hair.scalp.foundation", "hair.guides.primary", "hair.followers.render"],
    "shader": "Principled Hair BSDF", "runtimeDependency": "none",
    "status": "COLLISION_AND_VISUAL_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R172_BUILD=" + json.dumps(report, sort_keys=True))


