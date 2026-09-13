import json
import math
from collections import defaultdict
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-tail-collision-envelope-r452-study.blend"
OUTPUT = ASSETS / "aevrynd-female-authoring-v249-mainline-macro-clump-hierarchy-r453-study.blend"
REPORT = ASSETS / "female-v249-mainline-macro-clump-hierarchy-r453.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r453-macro-clump-hierarchy"
BODY = "AevryndFemaleBodyBaseV118"
RIG = "AevryndFemaleRig"
LAYERS = (
    "AevryndFemaleFrontSurfaceFlow_R383",
    "AevryndFemaleCrownSurfaceFlow_R383",
    "AevryndFemaleRearSurfaceFlow_R383",
)
FRAMES = (1, 20, 33, 61)
POINTS_PER_CURVE = 24
SECTORS = 18
HEIGHT_BANDS = 3
PENETRATION_LIMIT = -0.0005
TARGET_CLEARANCE = 0.002


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def deterministic_unit(value):
    return 0.5 + 0.5 * math.sin(value * 91.731 + 17.173)


def assign_macro_clumps(obj):
    points = obj.data.points
    curve_count = len(points) // POINTS_PER_CURVE
    roots = [points[curve * POINTS_PER_CURVE].position.copy() for curve in range(curve_count)]
    z_min = min(root.z for root in roots)
    z_max = max(root.z for root in roots)
    groups = defaultdict(list)
    curve_clumps = []
    for curve, root in enumerate(roots):
        angle = math.atan2(root.y + 0.04, root.x)
        sector = int(((angle + math.pi) / (2.0 * math.pi)) * SECTORS) % SECTORS
        height_t = (root.z - z_min) / max(1e-8, z_max - z_min)
        height_band = min(HEIGHT_BANDS - 1, int(height_t * HEIGHT_BANDS))
        clump = height_band * SECTORS + sector
        groups[clump].append(curve)
        curve_clumps.append(clump)

    centroids = {}
    for clump, curves in groups.items():
        centroids[clump] = []
        for segment in range(POINTS_PER_CURVE):
            total = Vector((0.0, 0.0, 0.0))
            for curve in curves:
                total += points[curve * POINTS_PER_CURVE + segment].position
            centroids[clump].append(total / len(curves))

    radius = obj.data.attributes["radius"].data
    maximum_displacement = 0.0
    maximum_tip_lift = 0.0
    for curve, clump in enumerate(curve_clumps):
        group_center = centroids[clump]
        phase = clump * 1.913 + len(groups[clump]) * 0.071
        root = roots[curve]
        angle = math.atan2(root.y + 0.04, root.x)
        tangent = Vector((-math.sin(angle), math.cos(angle), 0.0))
        wave_amplitude = 0.0005 + 0.0013 * deterministic_unit(phase)
        clump_lift = 0.003 + 0.012 * deterministic_unit(phase + 4.71)
        strand_lift = 0.002 * deterministic_unit(curve * 0.371 + clump)
        tip_lift = clump_lift + strand_lift
        maximum_tip_lift = max(maximum_tip_lift, tip_lift)
        radius_scale = 0.92 + 0.28 * deterministic_unit(phase + 8.13)
        base = curve * POINTS_PER_CURVE
        for segment in range(POINTS_PER_CURVE):
            index = base + segment
            t = segment / (POINTS_PER_CURVE - 1)
            root_lock = smoothstep((segment - 3) / 20.0)
            delta = group_center[segment] - points[index].position
            displacement = Vector((delta.x * 0.065, delta.y * 0.065, delta.z * 0.018)) * root_lock
            displacement += tangent * (wave_amplitude * math.sin(math.pi * t) * root_lock)
            if segment >= 17:
                displacement.z += tip_lift * smoothstep((segment - 17) / 6.0)
            points[index].position += displacement
            maximum_displacement = max(maximum_displacement, displacement.length)
            radius[index].value *= radius_scale

    attribute = obj.data.attributes.get("aevrynd_macro_clump")
    if attribute is None:
        attribute = obj.data.attributes.new("aevrynd_macro_clump", "INT", "CURVE")
    for index, clump in enumerate(curve_clumps):
        attribute.data[index].value = clump
    obj.data.update_tag()
    obj["aevrynd_macro_clump_count"] = len(groups)
    obj["aevrynd_revision"] = "v249r453"
    return {
        "curves": curve_count,
        "macroClumps": len(groups),
        "maximumInitialDisplacementM": maximum_displacement,
        "maximumTipLiftM": maximum_tip_lift,
    }


def body_tree(body, depsgraph):
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, faces, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


def evaluated_world_points(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    return [evaluated.matrix_world @ point.position for point in evaluated.data.points]


def collision_envelope_pass(scene, body, rig, objects):
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
            for index, point in enumerate(evaluated_world_points(obj, depsgraph)):
                hit = tree.find_nearest(point, 0.025)
                if hit is None or hit[1] is None:
                    continue
                signed = (point - hit[0]).dot(hit[1].normalized())
                if signed >= PENETRATION_LIMIT:
                    continue
                penetrating += 1
                curve = index // POINTS_PER_CURVE
                affected.add(curve)
                minimum = signed if minimum is None else min(minimum, signed)
                head_delta = world_to_head @ (hit[1].normalized() * (TARGET_CLEARANCE - signed))
                previous = corrections[obj.name].get(curve)
                if previous is None or signed < previous[0]:
                    corrections[obj.name][curve] = (signed, head_delta)
            frame_stats[str(frame)][obj.name] = {
                "penetratingPoints": penetrating,
                "affectedCurves": len(affected),
                "minimumSignedM": minimum,
            }
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
            base = curve * POINTS_PER_CURVE
            for segment in range(8, POINTS_PER_CURVE):
                weight = smoothstep((segment - 7) / 16.0)
                obj.data.points[base + segment].position += local_delta * weight
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
body = bpy.data.objects[BODY]
rig = bpy.data.objects[RIG]
objects = [bpy.data.objects[name] for name in LAYERS]
clump_stats = {obj.name: assign_macro_clumps(obj) for obj in objects}

material = bpy.data.materials.get("Aevrynd_SemanticGuideHair_R383")
material_stats = {}
if material and material.use_nodes:
    hair = next((node for node in material.node_tree.nodes if node.bl_idname == "ShaderNodeBsdfHairPrincipled"), None)
    if hair:
        for name, value in (("Melanin", 0.64), ("Melanin Redness", 0.52), ("Roughness", 0.34), ("Random Color", 0.20)):
            if hair.inputs.get(name):
                hair.inputs[name].default_value = value
                material_stats[name] = value

collision_passes = []
for pass_index in range(1, 5):
    before, applied, affected = collision_envelope_pass(scene, body, rig, objects)
    collision_passes.append({"pass": pass_index, "before": before, "affectedCurves": affected, "applied": applied})
    if not affected:
        break

scene.frame_set(1)
scene["aevrynd_mainline_revision"] = "v249r453-macro-clump-hierarchy-study"
scene["aevrynd_release_state"] = "R453_COLLISION_REVALIDATION_AND_VISUAL_REVIEW_REQUIRED"
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
    "macroClumpSectors": SECTORS,
    "macroClumpHeightBands": HEIGHT_BANDS,
    "clumpStats": clump_stats,
    "hairMaterial": material_stats,
    "collisionEnvelopePasses": collision_passes,
    "method": "Group neighboring roots into spatial macro clumps, apply low-amplitude coherent flow, vary clump width and stagger tips by clump, then preserve roots while rebuilding the four-frame body collision envelope.",
    "ownedAssetOnly": True,
    "websitePromotionApproved": False,
    "status": "COLLISION_REVALIDATION_AND_VISUAL_REVIEW_REQUIRED",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R453_MACRO_CLUMP_HIERARCHY=" + json.dumps(report, sort_keys=True))
