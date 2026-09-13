import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-tail-collision-envelope-r452-study.blend"
OUTPUT = ASSETS / "aevrynd-female-authoring-v249-mainline-authored-primary-locks-r454-study.blend"
REPORT = ASSETS / "female-v249-mainline-authored-primary-locks-r454.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r454-authored-primary-locks"
BODY = "AevryndFemaleBodyBaseV118"
RIG = "AevryndFemaleRig"
BASE_LAYERS = {
    "front": "AevryndFemaleFrontSurfaceFlow_R383",
    "crown": "AevryndFemaleCrownSurfaceFlow_R383",
    "rear": "AevryndFemaleRearSurfaceFlow_R383",
}
FRAMES = (1, 20, 33, 61)
POINTS = 24
FOLLOWERS = 13
PENETRATION_LIMIT = -0.0005
TARGET_CLEARANCE = 0.002


def smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def unit(seed):
    return 0.5 + 0.5 * math.sin(seed * 78.233 + 19.191)


def nearest_unique_curves(obj, targets):
    roots = [obj.data.points[index].position.copy() for index in range(0, len(obj.data.points), POINTS)]
    selected = []
    used = set()
    for target_x, target_y in targets:
        candidates = sorted(
            ((root.x - target_x) ** 2 + 1.6 * (root.y - target_y) ** 2, index)
            for index, root in enumerate(roots) if index not in used
        )
        index = candidates[0][1]
        used.add(index)
        selected.append(index)
    return selected


def authored_targets(region):
    if region == "front":
        return [(side * x, y) for side in (-1, 1) for y, x in ((-0.102, 0.018), (-0.082, 0.030), (-0.060, 0.045), (-0.040, 0.060))]
    if region == "crown":
        return [(side * x, y) for side in (-1, 1) for y in (-0.030, -0.010, 0.010) for x in (0.018, 0.047)]
    return [(x, y) for y in (0.016, 0.042, 0.068) for x in (-0.058, -0.022, 0.022, 0.058)]


def build_lock_strands(source_obj, region):
    selected = nearest_unique_curves(source_obj, authored_targets(region))
    strands = []
    guide_records = []
    for family, curve_index in enumerate(selected):
        base_index = curve_index * POINTS
        guide = [source_obj.data.points[base_index + segment].position.copy() for segment in range(POINTS)]
        root = guide[0]
        radial = Vector((root.x, root.y + 0.04, 0.0))
        if radial.length < 1e-6:
            radial = Vector((1.0, 0.0, 0.0))
        radial.normalize()
        tangent = Vector((-radial.y, radial.x, 0.0)).normalized()
        lift_axis = radial.cross(tangent).normalized()
        direction_sign = -1.0 if unit(family + len(region)) < 0.5 else 1.0
        macro_amplitude = 0.0018 + 0.0024 * unit(family + 3.7)
        tip_lift = 0.001 + 0.010 * unit(family + 8.1)
        for segment, point in enumerate(guide):
            t = segment / (POINTS - 1)
            flow = smoothstep((segment - 2) / 21.0)
            point += tangent * (direction_sign * macro_amplitude * math.sin(math.pi * t) * flow)
            if segment >= 18:
                point.z += tip_lift * smoothstep((segment - 18) / 5.0)
        for follower in range(FOLLOWERS):
            angle = math.tau * follower / FOLLOWERS + unit(family * 31 + follower) * 0.24
            radius = 0.00035 + 0.00155 * math.sqrt(unit(family * 47 + follower + 0.3))
            offset = tangent * (math.cos(angle) * radius) + lift_axis * (math.sin(angle) * radius * 0.55)
            strand = []
            phase = math.tau * unit(family * 59 + follower + 1.9)
            for segment, base in enumerate(guide):
                t = segment / (POINTS - 1)
                spread = 0.12 + 0.88 * smoothstep(t)
                fine = tangent * (0.00028 * math.sin(phase + t * math.tau * 0.85) * smoothstep(t))
                strand.append(base + offset * spread + radial * (0.00025 * spread) + fine)
            strands.append(strand)
        guide_records.append({
            "family": family,
            "sourceCurve": curve_index,
            "root": list(root),
            "followers": FOLLOWERS,
            "macroAmplitudeM": macro_amplitude,
            "tipLiftM": tip_lift,
        })
    return strands, guide_records


def create_curve_object(name, strands, layer, material, motion_group):
    data = bpy.data.hair_curves.new(f"{name}Data")
    data.add_curves([POINTS] * len(strands))
    data.points.foreach_set("position", [value for strand in strands for point in strand for value in point])
    radius = data.attributes.new("radius", "FLOAT", "POINT")
    radii = []
    for strand_index, _strand in enumerate(strands):
        family_scale = 0.86 + 0.28 * unit(strand_index // FOLLOWERS + 12.7)
        for segment in range(POINTS):
            t = segment / (POINTS - 1)
            taper = 1.0 - 0.84 * smoothstep((t - 0.52) / 0.48)
            radii.append(0.000030 * family_scale * taper)
    radius.data.foreach_set("value", radii)
    data.materials.append(material)
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = bpy.data.objects[RIG]
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = source_world = bpy.data.objects[BASE_LAYERS["front"]].matrix_world.copy()
    modifier = obj.modifiers.new("Aevrynd Authored Primary Lock Motion R454", "NODES")
    modifier.node_group = motion_group
    obj["aevrynd_layer"] = layer
    obj["aevrynd_revision"] = "v249r454"
    obj["aevrynd_curve_count"] = len(strands)
    obj["aevrynd_root_locked"] = True
    obj["aevrynd_collision_audit"] = True
    obj["aevrynd_collision_clearance_m"] = TARGET_CLEARANCE
    return obj


def body_tree(body, depsgraph):
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, faces, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


def evaluated_points(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    return [evaluated.matrix_world @ point.position for point in evaluated.data.points]


def collision_pass(scene, body, rig, objects):
    corrections = {obj.name: {} for obj in objects}
    frame_stats = {}
    for frame in FRAMES:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        tree = body_tree(body, depsgraph)
        head_world = rig.matrix_world @ rig.pose.bones["head"].matrix
        world_to_head = head_world.inverted().to_3x3()
        frame_stats[str(frame)] = {}
        for obj in objects:
            penetrating = 0
            affected = set()
            minimum = None
            for index, point in enumerate(evaluated_points(obj, depsgraph)):
                hit = tree.find_nearest(point, 0.025)
                if hit is None or hit[1] is None:
                    continue
                signed = (point - hit[0]).dot(hit[1].normalized())
                if signed >= PENETRATION_LIMIT:
                    continue
                penetrating += 1
                curve = index // POINTS
                affected.add(curve)
                minimum = signed if minimum is None else min(minimum, signed)
                head_delta = world_to_head @ (hit[1].normalized() * (TARGET_CLEARANCE - signed))
                previous = corrections[obj.name].get(curve)
                if previous is None or signed < previous[0]:
                    corrections[obj.name][curve] = (signed, head_delta)
            frame_stats[str(frame)][obj.name] = {"penetratingPoints": penetrating, "affectedCurves": len(affected), "minimumSignedM": minimum}
    scene.frame_set(1)
    bpy.context.view_layer.update()
    head_world = rig.matrix_world @ rig.pose.bones["head"].matrix
    applied = {}
    for obj in objects:
        world_to_local = obj.matrix_world.inverted().to_3x3()
        maximum = 0.0
        for curve, (_signed, head_delta) in corrections[obj.name].items():
            local_delta = world_to_local @ (head_world.to_3x3() @ head_delta)
            maximum = max(maximum, local_delta.length)
            base = curve * POINTS
            for segment in range(6, POINTS):
                obj.data.points[base + segment].position += local_delta * smoothstep((segment - 5) / 18.0)
        obj.data.update_tag()
        applied[obj.name] = {"correctedCurves": len(corrections[obj.name]), "maximumDisplacementM": maximum}
    bpy.context.view_layer.update()
    return frame_stats, applied, sum(len(values) for values in corrections.values())


def render(scene, camera, frame, label, location, target, lens):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(RENDER_DIR / f"{label}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
body = bpy.data.objects[BODY]
rig = bpy.data.objects[RIG]
base_objects = {region: bpy.data.objects[name] for region, name in BASE_LAYERS.items()}
motion_group = base_objects["front"].modifiers[0].node_group

# Thin the continuous field so the authored primary layer controls grouping and highlights.
base_radius_scale = 0.78
for obj in base_objects.values():
    radius = obj.data.attributes["radius"].data
    for item in radius:
        item.value *= base_radius_scale

source_material = bpy.data.materials["Aevrynd_SemanticGuideHair_R383"]
primary_material = source_material.copy()
primary_material.name = "Aevrynd_AuthoredPrimaryHair_R454"
if primary_material.use_nodes:
    hair = next((node for node in primary_material.node_tree.nodes if node.bl_idname == "ShaderNodeBsdfHairPrincipled"), None)
    if hair:
        for name, value in (("Melanin", 0.61), ("Melanin Redness", 0.50), ("Roughness", 0.32), ("Random Color", 0.16)):
            if hair.inputs.get(name):
                hair.inputs[name].default_value = value

primary_objects = []
guide_records = {}
for region, source_obj in base_objects.items():
    strands, records = build_lock_strands(source_obj, region)
    obj = create_curve_object(
        f"AevryndFemaleAuthoredPrimaryLocks_{region.title()}_R454",
        strands,
        f"hair.authored_primary_locks.{region}.dynamic",
        primary_material,
        motion_group,
    )
    primary_objects.append(obj)
    guide_records[region] = records

collision_objects = list(base_objects.values()) + primary_objects
collision_passes = []
for pass_index in range(1, 5):
    before, applied, affected = collision_pass(scene, body, rig, collision_objects)
    collision_passes.append({"pass": pass_index, "before": before, "affectedCurves": affected, "applied": applied})
    if not affected:
        break

scene.frame_set(1)
scene["aevrynd_mainline_revision"] = "v249r454-authored-primary-locks-study"
scene["aevrynd_release_state"] = "R454_COLLISION_REVALIDATION_AND_VISUAL_REVIEW_REQUIRED"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
for frame, label, location, target, lens in (
    (1, "01-front-f01", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
    (1, "02-hairline-f01", (0.0, -0.57, 1.76), (0.0, -0.02, 1.64), 92),
    (1, "03-top-f01", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
    (1, "04-three-quarter-f01", (0.45, -0.66, 1.60), (0.0, -0.005, 1.56), 84),
    (1, "05-back-f01", (0.0, 0.90, 1.59), (0.0, 0.0, 1.56), 82),
    (33, "06-front-f33", (0.0, -0.76, 1.58), (0.0, -0.015, 1.56), 84),
    (33, "07-back-f33", (0.0, 0.90, 1.59), (0.0, 0.0, 1.56), 82),
):
    render(scene, camera, frame, label, location, target, lens)
scene.frame_set(1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "renderDirectory": str(RENDER_DIR),
    "baseRadiusScale": base_radius_scale,
    "primaryLayers": [obj.get("aevrynd_layer") for obj in primary_objects],
    "primaryCurveCounts": {obj.name: len(obj.data.curves) for obj in primary_objects},
    "guideFamilies": guide_records,
    "collisionEnvelopePasses": collision_passes,
    "method": "Choose explicit anatomical front-frame, crown and rear source guides; author coherent guide arcs and tip lengths; generate compact follower bundles as separate dynamic primary-lock layers over a thinner continuous field.",
    "ownedAssetOnly": True,
    "websitePromotionApproved": False,
    "status": "COLLISION_REVALIDATION_AND_VISUAL_REVIEW_REQUIRED",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R454_AUTHORED_PRIMARY_LOCKS=" + json.dumps(report, sort_keys=True))
