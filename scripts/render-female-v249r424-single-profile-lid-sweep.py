import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-layered-optical-stack-r420.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-single-profile-lid-r424.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r424-single-profile-lid-sweep"
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


def sculpt_lids(body, strength, samples):
    inverse = body.matrix_world.inverted()
    moved = {"L": 0, "R": 0}
    maximum = 0.0
    clamped = 0
    for vertex in body.data.vertices:
        point = body.matrix_world @ vertex.co
        normal = (body.matrix_world.to_3x3() @ vertex.normal).normalized()
        if normal.y > -0.35 or point.y > -0.125:
            continue
        side = "L" if point.x >= 0.0 else "R"
        upper = samples[side]["upper"]
        lower = samples[side]["lower"]
        x_min, x_max = upper[0].x, upper[-1].x
        if point.x < x_min - 0.0030 or point.x > x_max + 0.0030 or point.y > -0.105:
            continue
        upper_point = interpolate(upper, point.x)
        lower_point = interpolate(lower, point.x)
        center_x = 0.5 * (x_min + x_max)
        half_width = 0.5 * (x_max - x_min)
        u = (point.x - center_x) / max(half_width, 1e-8)
        edge = smoothstep((1.18 - abs(u)) / 0.28)
        front = smoothstep((-point.y - 0.105) / 0.027)
        if edge <= 0.0 or front <= 0.0:
            continue

        above = point.z - upper_point.z
        below = lower_point.z - point.z
        temporal = smoothstep((u + 0.15) / 0.95) if side == "L" else smoothstep((-u + 0.15) / 0.95)
        medial = 1.0 - temporal
        asymmetry = 0.94 if side == "L" else 1.0
        target = None
        region = None
        if -0.00035 <= above <= 0.0085:
            offset = (
                -0.00052 * gaussian(above, 0.00105, 0.00076)
                + 0.00062 * gaussian(above, 0.00355, 0.00062) * (0.82 + 0.24 * temporal)
                - 0.00006 * gaussian(above, 0.0062, 0.0012)
            )
            target = upper_point.y + offset
            region = "upper"
        elif -0.00035 <= below <= 0.0080:
            offset = (
                -0.00030 * gaussian(below, 0.00080, 0.00072)
                + 0.00036 * gaussian(below, 0.00385, 0.00115) * (0.84 + 0.26 * medial)
            )
            target = lower_point.y + offset
            region = "lower"
        if target is None:
            continue
        delta_y = (target - point.y) * strength * asymmetry * edge * front
        if delta_y > 0.0020:
            delta_y = 0.0020
            clamped += 1
        elif delta_y < -0.0020:
            delta_y = -0.0020
            clamped += 1
        if abs(delta_y) < 1e-7:
            continue
        before = point.copy()
        point.y += delta_y
        vertex.co = inverse @ point
        moved[side] += 1
        maximum = max(maximum, abs(delta_y))
    body.data.update()
    return {"movedVertices": moved, "maximumDisplacementM": maximum, "clampedVertices": clamped}


def neutral_lights(scene):
    for obj in list(bpy.data.objects):
        if obj.type == "LIGHT":
            bpy.data.objects.remove(obj, do_unlink=True)
    target = (0.0, -0.025, 1.60)
    for name, location, energy, size in (
        ("Aevrynd Neutral Key R424", (-0.42, -0.82, 1.82), 39.0, 0.56),
        ("Aevrynd Neutral Fill R424", (0.48, -0.62, 1.70), 24.0, 0.68),
        ("Aevrynd Neutral Top R424", (0.00, -0.08, 2.28), 22.0, 0.52),
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
variants = (("a-quarter", 0.25), ("b-half", 0.50), ("c-three-quarter", 0.75))
metrics = {}
previous = None
for label, strength in variants:
    if previous:
        bpy.data.objects.remove(previous, do_unlink=True)
    body = copy_body(source_body, f"AevryndFemaleBody_SingleLidProfile_{label}_R424")
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
    "method": "Replace the overlapping inherited external-lid relief with one target front-depth profile anchored to the authored upper and lower lid margins; inner eyelid surfaces are excluded by normal and depth.",
    "fixedConditions": {"neutralWhiteLights": True, "AgX": "Base Contrast", "exposureEV": 0.0, "largeHairHidden": True},
    "status": "VISUAL_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R424_SINGLE_PROFILE_LID_SWEEP=" + json.dumps(report, sort_keys=True))
