import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-tail-collision-envelope-r452-study.blend"
OUTPUT = ASSETS / "aevrynd-female-authoring-v249-mainline-guide-child-groom-r457-study.blend"
REPORT = ASSETS / "female-v249-mainline-guide-child-groom-r457.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r457-guide-child-groom"
BODY = "AevryndFemaleBodyBaseV118"
RIG = "AevryndFemaleRig"
SOURCE_LAYERS = {
    "front": "AevryndFemaleFrontSurfaceFlow_R383",
    "crown": "AevryndFemaleCrownSurfaceFlow_R383",
    "rear": "AevryndFemaleRearSurfaceFlow_R383",
}
GUIDE_COUNTS = {"front": 56, "crown": 48, "rear": 56}
CHILDREN = 48
POINTS = 24
FRAMES = (1, 20, 33, 61)
PENETRATION_LIMIT = -0.0005
TARGET_CLEARANCE = 0.002


def smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def unit(seed):
    return 0.5 + 0.5 * math.sin(seed * 83.731 + 11.917)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def seed_targets(region):
    if region == "front":
        return [(side * x, y) for side in (-1, 1) for y, x in ((-0.104, 0.014), (-0.086, 0.026), (-0.066, 0.040), (-0.046, 0.056), (-0.030, 0.070))]
    if region == "crown":
        return [(side * x, y) for side in (-1, 1) for y in (-0.034, -0.016, 0.002, 0.018) for x in (0.014, 0.038, 0.064)]
    return [(x, y) for y in (0.010, 0.030, 0.052, 0.074) for x in (-0.066, -0.036, -0.010, 0.010, 0.036, 0.066)]


def root_distance(a, b):
    return (a.x - b.x) ** 2 + 1.45 * (a.y - b.y) ** 2 + 0.30 * (a.z - b.z) ** 2


def select_guides(obj, region, count):
    paths = [
        [obj.data.points[curve * POINTS + segment].position.copy() for segment in range(POINTS)]
        for curve in range(len(obj.data.points) // POINTS)
    ]
    roots = [path[0] for path in paths]
    selected = []
    selected_set = set()
    for x, y in seed_targets(region):
        index = min(
            (item for item in range(len(roots)) if item not in selected_set),
            key=lambda item: (roots[item].x - x) ** 2 + 1.45 * (roots[item].y - y) ** 2,
        )
        selected.append(index)
        selected_set.add(index)
        if len(selected) == count:
            break
    while len(selected) < count:
        index = max(
            (item for item in range(len(roots)) if item not in selected_set),
            key=lambda item: min(root_distance(roots[item], roots[chosen]) for chosen in selected),
        )
        selected.append(index)
        selected_set.add(index)
    return [(index, paths[index]) for index in selected]


def make_family(region, selections):
    guides = []
    children = []
    records = []
    for family, (source_index, source_path) in enumerate(selections):
        guide = [point.copy() for point in source_path]
        root = guide[0]
        root_tangent = (guide[2] - guide[0]).normalized()
        outward = Vector((root.x, root.y + 0.012, root.z - 1.62))
        if outward.length < 1e-6:
            outward = Vector((0.0, -1.0, 0.0))
        outward.normalize()
        side = root_tangent.cross(outward)
        if side.length < 1e-6:
            side = Vector((1.0, 0.0, 0.0))
        side.normalize()
        family_sway = (unit(family + len(region) * 3.1) - 0.5) * 0.005
        family_tip = (unit(family + len(region) * 7.3) - 0.5) * 0.012
        for segment, point in enumerate(guide):
            t = segment / (POINTS - 1)
            flow = smoothstep((segment - 2) / 21.0)
            point += side * (family_sway * math.sin(math.pi * t) * flow)
            if segment >= 18:
                point.z += family_tip * smoothstep((segment - 18) / 5.0)
        guides.append(guide)
        clump_radius = 0.0022 + 0.0026 * unit(family + 15.7)
        for child in range(CHILDREN):
            angle = math.tau * ((child + 0.35 * unit(family * 71 + child)) / CHILDREN)
            radial = clump_radius * math.sqrt((child + 0.5) / CHILDREN)
            cross_offset = side * (math.cos(angle) * radial)
            depth_offset = outward * (0.00030 + max(0.0, math.sin(angle)) * radial * 0.34)
            vertical_offset = Vector((0.0, 0.0, math.sin(angle) * radial * 0.24))
            child_tip = (unit(family * 97 + child + 2.1) - 0.5) * 0.0045
            phase = math.tau * unit(family * 131 + child + 5.9)
            strand = []
            for segment, base in enumerate(guide):
                t = segment / (POINTS - 1)
                profile = 0.42 + 0.72 * math.sin(math.pi * t) ** 1.25 - 0.14 * t
                root_lock = 0.35 + 0.65 * smoothstep(t / 0.20)
                fine = side * (0.00024 * math.sin(phase + t * math.tau * 0.92) * smoothstep(t))
                point = base + (cross_offset + vertical_offset) * profile * root_lock + depth_offset * (0.65 + 0.35 * smoothstep(t)) + fine
                if segment >= 18:
                    point.z += child_tip * smoothstep((segment - 18) / 5.0)
                strand.append(point)
            children.append(strand)
        records.append({
            "family": family,
            "sourceCurve": source_index,
            "root": list(root),
            "children": CHILDREN,
            "clumpRadiusM": clump_radius,
            "familySwayM": family_sway,
            "familyTipOffsetM": family_tip,
        })
    return guides, children, records


def create_curves(name, strands, layer, material, motion_group, root_radius):
    data = bpy.data.hair_curves.new(f"{name}Data")
    data.add_curves([POINTS] * len(strands))
    data.points.foreach_set("position", [value for strand in strands for point in strand for value in point])
    radius = data.attributes.new("radius", "FLOAT", "POINT")
    values = []
    for strand_index, _strand in enumerate(strands):
        strand_scale = 0.88 + 0.24 * unit(strand_index + len(strands) * 0.01)
        for segment in range(POINTS):
            t = segment / (POINTS - 1)
            values.append(root_radius * strand_scale * (1.0 - 0.82 * smoothstep((t - 0.56) / 0.44)))
    radius.data.foreach_set("value", values)
    data.materials.append(material)
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    source = bpy.data.objects[SOURCE_LAYERS["front"]]
    obj.parent = bpy.data.objects[RIG]
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = source.matrix_world.copy()
    modifier = obj.modifiers.new("Aevrynd Guide Child Secondary Motion R457", "NODES")
    modifier.node_group = motion_group
    obj["aevrynd_layer"] = layer
    obj["aevrynd_revision"] = "v249r457"
    obj["aevrynd_curve_count"] = len(strands)
    obj["aevrynd_root_locked"] = True
    obj["aevrynd_collision_audit"] = True
    obj["aevrynd_collision_clearance_m"] = TARGET_CLEARANCE
    return obj


def surface_tree(body, depsgraph):
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
        tree = surface_tree(body, depsgraph)
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
                curve = index // POINTS
                penetrating += 1
                affected.add(curve)
                minimum = signed if minimum is None else min(minimum, signed)
                delta = world_to_head @ (hit[1].normalized() * (TARGET_CLEARANCE - signed))
                previous = corrections[obj.name].get(curve)
                if previous is None or signed < previous[0]:
                    corrections[obj.name][curve] = (signed, delta)
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
            for segment in range(5, POINTS):
                obj.data.points[base + segment].position += local_delta * smoothstep((segment - 4) / 19.0)
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
source_objects = {region: bpy.data.objects[name] for region, name in SOURCE_LAYERS.items()}
motion_group = source_objects["front"].modifiers[0].node_group
for obj in source_objects.values():
    obj.hide_render = True
    obj.hide_viewport = True

source_material = bpy.data.materials["Aevrynd_SemanticGuideHair_R383"]
guide_material = source_material.copy()
guide_material.name = "Aevrynd_GuideHair_R457"
child_material = source_material.copy()
child_material.name = "Aevrynd_ChildHair_R457"
for material, melanin, roughness, random_color in (
    (guide_material, 0.63, 0.34, 0.10),
    (child_material, 0.66, 0.37, 0.22),
):
    if material.use_nodes:
        hair = next((node for node in material.node_tree.nodes if node.bl_idname == "ShaderNodeBsdfHairPrincipled"), None)
        if hair:
            for name, value in (("Melanin", melanin), ("Melanin Redness", 0.52), ("Roughness", roughness), ("Random Color", random_color)):
                if hair.inputs.get(name):
                    hair.inputs[name].default_value = value
    material["aevrynd_ownership"] = "procedurally generated in-project"
    material["aevrynd_revision"] = "v249r457"

objects = []
family_records = {}
for region, source_obj in source_objects.items():
    selections = select_guides(source_obj, region, GUIDE_COUNTS[region])
    guides, children, records = make_family(region, selections)
    objects.append(create_curves(
        f"AevryndFemaleGuides_{region.title()}_R457", guides,
        f"hair.guides.{region}.dynamic", guide_material, motion_group, 0.000032,
    ))
    objects.append(create_curves(
        f"AevryndFemaleChildren_{region.title()}_R457", children,
        f"hair.children.{region}.dynamic", child_material, motion_group, 0.0000145,
    ))
    family_records[region] = records

collision_passes = []
for pass_index in range(1, 6):
    before, applied, affected = collision_pass(scene, body, rig, objects)
    collision_passes.append({"pass": pass_index, "before": before, "affectedCurves": affected, "applied": applied})
    if not affected:
        break

scene.frame_set(1)
scene["aevrynd_mainline_revision"] = "v249r457-guide-child-groom-study"
scene["aevrynd_release_state"] = "R457_COLLISION_REVALIDATION_AND_VISUAL_REVIEW_REQUIRED"
scene["aevrynd_hair_layers"] = "|".join(obj.get("aevrynd_layer") for obj in objects)
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
    "guideCounts": GUIDE_COUNTS,
    "childrenPerGuide": CHILDREN,
    "curveCounts": {obj.name: len(obj.data.curves) for obj in objects},
    "totalVisibleDynamicCurves": sum(len(obj.data.curves) for obj in objects),
    "familyRecords": family_records,
    "retainedFoundationLayers": ["hair.hairline_microclumps.head_bound", "hair.scalp_density_foundation.head_bound"],
    "hiddenDenseCurtainLayers": list(SOURCE_LAYERS.values()),
    "collisionEnvelopePasses": collision_passes,
    "method": "Select 160 spatially distributed collision-safe guides, preserve each guide as an explicit layer, generate 48 tapered children per guide with a shared clump profile, and hide the three dense continuous curtain layers.",
    "ownedAssetOnly": True,
    "websitePromotionApproved": False,
    "status": "COLLISION_REVALIDATION_AND_VISUAL_REVIEW_REQUIRED",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R457_GUIDE_CHILD_GROOM=" + json.dumps(report, sort_keys=True))
