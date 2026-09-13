import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-layered-optical-stack-r420.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-external-lid-smoothing-r425.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r425-external-lid-smoothing-sweep"
BODY = "AevryndFemaleBody_CC0_R249"
EYE_LAYERS = ("ScleraOpen", "LimbalAnnulus", "IrisConcave", "PupilRecessed", "CorneaConvex")


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def gaussian(value, center, spread):
    return math.exp(-0.5 * ((value - center) / spread) ** 2)


def smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def curve_samples(name):
    obj = bpy.data.objects[name]
    return sorted((obj.matrix_world @ point.co.xyz for spline in obj.data.splines for point in spline.points), key=lambda point: point.x)


def interpolate(samples, x):
    if x <= samples[0].x:
        return samples[0]
    if x >= samples[-1].x:
        return samples[-1]
    low, high = 0, len(samples) - 1
    while high - low > 1:
        mid = (low + high) // 2
        if samples[mid].x <= x:
            low = mid
        else:
            high = mid
    a, b = samples[low], samples[high]
    t = (x - a.x) / max(1e-9, b.x - a.x)
    return a.lerp(b, t)


def copy_body(source, name):
    obj = source.copy()
    obj.data = source.data.copy()
    obj.name = name
    obj.data.name = name + "Geometry"
    bpy.context.scene.collection.objects.link(obj)
    return obj


def world_bvh(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, faces, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


def sculpt_lids(body, iterations, samples):
    inverse = body.matrix_world.inverted()
    normal_matrix = body.matrix_world.to_3x3()
    points = [body.matrix_world @ vertex.co for vertex in body.data.vertices]
    normals = [(normal_matrix @ vertex.normal).normalized() for vertex in body.data.vertices]
    external = [normal.y < -0.35 and point.y < -0.125 for point, normal in zip(points, normals)]
    weights = [0.0] * len(points)
    sides = [None] * len(points)
    for index, point in enumerate(points):
        if not external[index]:
            continue
        side = "L" if point.x >= 0.0 else "R"
        upper = samples[side]["upper"]
        lower = samples[side]["lower"]
        x_min, x_max = upper[0].x, upper[-1].x
        if point.x < x_min - 0.002 or point.x > x_max + 0.002:
            continue
        upper_point = interpolate(upper, point.x)
        lower_point = interpolate(lower, point.x)
        center_x = 0.5 * (x_min + x_max)
        half_width = 0.5 * (x_max - x_min)
        u = (point.x - center_x) / max(half_width, 1e-8)
        edge = smoothstep((1.13 - abs(u)) / 0.20)
        above = point.z - upper_point.z
        below = lower_point.z - point.z
        upper_band = smoothstep((above - 0.00035) / 0.0010) * smoothstep((0.0072 - above) / 0.0012)
        lower_band = smoothstep((below - 0.00035) / 0.0010) * smoothstep((0.0065 - below) / 0.0013)
        weights[index] = edge * max(upper_band, lower_band)
        if weights[index] > 0.0:
            sides[index] = side

    neighbors = [[] for _ in points]
    for edge in body.data.edges:
        a, b = edge.vertices
        neighbors[a].append(b)
        neighbors[b].append(a)
    original_y = [point.y for point in points]
    values = original_y[:]
    for _ in range(iterations):
        updated = values[:]
        for index, weight in enumerate(weights):
            if weight <= 0.0:
                continue
            candidates = [neighbor for neighbor in neighbors[index] if external[neighbor]]
            if not candidates:
                continue
            average = sum(values[neighbor] for neighbor in candidates) / len(candidates)
            updated[index] = values[index] + 0.42 * weight * (average - values[index])
        values = updated

    moved = {"L": 0, "R": 0}
    maximum = 0.0
    for index, weight in enumerate(weights):
        delta = values[index] - original_y[index]
        if weight <= 0.0 or abs(delta) < 1e-8:
            continue
        point = points[index].copy()
        point.y = values[index]
        body.data.vertices[index].co = inverse @ point
        moved[sides[index]] += 1
        maximum = max(maximum, abs(delta))
    body.data.update()
    return {"movedVertices": moved, "maximumDisplacementM": maximum, "iterations": iterations}


def neutral_lights(scene):
    for obj in list(bpy.data.objects):
        if obj.type == "LIGHT":
            bpy.data.objects.remove(obj, do_unlink=True)
    target = (0.0, -0.025, 1.60)
    for name, location, energy, size in (
        ("Aevrynd Neutral Key R425", (-0.42, -0.82, 1.82), 39.0, 0.56),
        ("Aevrynd Neutral Fill R425", (0.48, -0.62, 1.70), 24.0, 0.68),
        ("Aevrynd Neutral Top R425", (0.00, -0.08, 2.28), 22.0, 0.52),
    ):
        data = bpy.data.lights.new(name, "AREA")
        data.energy, data.color, data.shape, data.size = energy, (1.0, 1.0, 1.0), "DISK", size
        obj = bpy.data.objects.new(name, data)
        bpy.context.scene.collection.objects.link(obj)
        obj.location = location
        look_at(obj, target)
    scene.world.use_nodes = True
    background = next((node for node in scene.world.node_tree.nodes if node.type == "BACKGROUND"), None)
    background.inputs["Color"].default_value = (0.018, 0.018, 0.018, 1.0)
    background.inputs["Strength"].default_value = 0.35


def hide_large_hair():
    for obj in bpy.data.objects:
        name = obj.name.lower()
        preserve = ("brow", "lash", "lid", "tear", "caruncle", "eye")
        if any(token in name for token in preserve):
            continue
        materials = getattr(obj.data, "materials", ()) if hasattr(obj, "data") else ()
        material_names = " ".join(material.name.lower() for material in materials if material)
        if obj.type in {"MESH", "CURVES", "CURVE"} and any(token in name or token in material_names for token in ("hair", "scalp", "groom", "flyaway", "root", "lock", "fiber")):
            obj.hide_render = True


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Base Contrast"
scene.view_settings.exposure = 0.0
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
scene.camera = camera
hide_large_hair()
neutral_lights(scene)

samples = {
    side: {
        "upper": curve_samples(f"AevryndEye_{side}_UpperLidMargin_R258"),
        "lower": curve_samples(f"AevryndEye_{side}_LowerLidMargin_R258"),
    }
    for side in ("L", "R")
}
source_body = bpy.data.objects[BODY]
source_body.hide_render = True
views = (
    ("face", (0.0, -0.68, 1.605), (0.0, -0.035, 1.606), 92, (1000, 1000)),
    ("eyes", (0.0, -0.46, 1.615), (0.0, -0.035, 1.610), 105, (1200, 760)),
    ("three-quarter", (0.44, -0.63, 1.62), (0.0, -0.02, 1.595), 88, (1000, 1000)),
)
variants = (("a-four", 4), ("b-eight", 8), ("c-fourteen", 14))
metrics = {}
previous = None
for label, strength in variants:
    if previous:
        bpy.data.objects.remove(previous, do_unlink=True)
    body = copy_body(source_body, f"AevryndFemaleBody_LidSmooth_{label}_R425")
    body.hide_render = False
    edit = sculpt_lids(body, strength, samples)
    scene.frame_set(1)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    body_tree = world_bvh(body, depsgraph)
    overlaps = {}
    for side in ("L", "R"):
        overlaps[side] = {
            kind: len(body_tree.overlap(world_bvh(bpy.data.objects[f"AevryndEye_{side}_{kind}_R420"], depsgraph)))
            for kind in EYE_LAYERS
        }
    metrics[label] = {"strength": strength, **edit, "frame1BodyOpticalTriangleOverlaps": overlaps}
    for view_name, location, target, lens, size in views:
        camera.location = location
        camera.data.lens = lens
        look_at(camera, target)
        scene.render.resolution_x, scene.render.resolution_y = size
        scene.render.filepath = str(RENDER_DIR / f"{label}-{view_name}.png")
        bpy.ops.render.render(write_still=True)
    previous = body

report = {
    "source": str(SOURCE), "renderDirectory": str(RENDER_DIR), "variants": metrics,
    "method": "Normal-gated Laplacian smoothing of only the external upper/lower eyelid relief, preserving aperture edges, inner eyelid surfaces and the optical stack.",
    "fixedConditions": {"neutralWhiteLights": True, "AgX": "Base Contrast", "exposureEV": 0.0, "largeHairHidden": True},
    "status": "VISUAL_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R425_EXTERNAL_LID_SMOOTHING_SWEEP=" + json.dumps(report, sort_keys=True))
