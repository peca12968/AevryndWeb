import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-canthus-fitted-wedge-r345.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-orbital-fold-r410.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r410-orbital-fold-sweep"
BODY = "AevryndFemaleBody_CC0_R249"
EYES = {"L": (0.034528, 1.607765, 1.0), "R": (-0.034443, 1.607765, -1.0)}
HALF_WIDTH = 0.01025
UPPER_APERTURE = 0.0022
LOWER_APERTURE = 0.0041
VARIANTS = (("a-subtle", 0.68), ("b-balanced", 1.00), ("c-strong", 1.32))


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def gaussian(value, sigma):
    return math.exp(-((value / sigma) ** 2))


def aperture_edge(u):
    return math.sqrt(max(0.0, 1.0 - min(1.0, u * u)))


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def world_bvh(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, faces, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


def make_body(source, name):
    obj = bpy.data.objects.new(name, source.data.copy())
    bpy.context.scene.collection.objects.link(obj)
    obj.matrix_world = source.matrix_world.copy()
    return obj


def sculpt(body, strength):
    inverse = body.matrix_world.inverted()
    moved = {"L": 0, "R": 0}
    maxima = {"outwardM": 0.0, "inwardM": 0.0, "totalM": 0.0}
    components = {"upperRoll": 0.0, "upperCrease": 0.0, "lowerRoll": 0.0, "tearTrough": 0.0}
    for vertex in body.data.vertices:
        world = body.matrix_world @ vertex.co
        if not (-0.112 <= world.y <= -0.030):
            continue
        side = "L" if world.x >= 0.0 else "R"
        cx, cz, sign = EYES[side]
        dx = world.x - cx
        u = dx / HALF_WIDTH
        if abs(u) > 1.34 or abs(world.z - cz) > 0.014:
            continue
        edge = aperture_edge(u)
        lateral_fade = clamp((1.30 - abs(u)) / 0.24)
        lateral_fade *= lateral_fade * (3.0 - 2.0 * lateral_fade)
        upper_margin = cz + UPPER_APERTURE * edge
        lower_margin = cz - LOWER_APERTURE * edge
        upper_roll = -0.00058 * gaussian(world.z - (upper_margin + 0.00115), 0.00145)
        upper_crease = 0.00048 * gaussian(world.z - (upper_margin + 0.00415), 0.00105)
        lower_roll = -0.00046 * gaussian(world.z - (lower_margin - 0.00115), 0.00155)
        lateral_u = sign * dx / HALF_WIDTH
        trough_z = lower_margin - 0.0034 - 0.0010 * clamp((lateral_u + 0.65) / 0.95)
        trough_span = gaussian(lateral_u + 0.24, 0.62)
        tear_trough = 0.00036 * gaussian(world.z - trough_z, 0.00135) * trough_span
        side_strength = strength * (1.0 if side == "L" else 0.94)
        values = {
            "upperRoll": upper_roll * lateral_fade * side_strength,
            "upperCrease": upper_crease * lateral_fade * side_strength,
            "lowerRoll": lower_roll * lateral_fade * side_strength,
            "tearTrough": tear_trough * lateral_fade * side_strength,
        }
        delta_y = sum(values.values())
        if abs(delta_y) < 1e-7:
            continue
        before = world.copy()
        world.y += delta_y
        vertex.co = inverse @ world
        moved[side] += 1
        maxima["outwardM"] = max(maxima["outwardM"], max(0.0, -delta_y))
        maxima["inwardM"] = max(maxima["inwardM"], max(0.0, delta_y))
        maxima["totalM"] = max(maxima["totalM"], (world - before).length)
        for name, value in values.items():
            components[name] = max(components[name], abs(value))
    body.data.update()
    return {"movedVertices": moved, "maximumDisplacement": maxima, "maximumComponentM": components}


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
source_body = bpy.data.objects[BODY]
source_body.hide_render = True
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.view_settings.exposure = 0.0
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
views = (
    ("eyes", (0.0, -0.46, 1.615), (0.0, -0.035, 1.610), 105),
    ("face", (0.0, -0.68, 1.605), (0.0, -0.035, 1.606), 92),
    ("three-quarter", (0.45, -0.62, 1.62), (0.0, -0.02, 1.605), 90),
)
metrics = {}
previous = None
for label, strength in VARIANTS:
    if previous is not None:
        bpy.data.objects.remove(previous, do_unlink=True)
    body = make_body(source_body, f"AevryndFemaleOrbitalFold_{label}")
    edit = sculpt(body, strength)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    body_tree = world_bvh(body, depsgraph)
    overlaps = {}
    for side in EYES:
        sclera = bpy.data.objects[f"AevryndEye_{side}_Sclera_R249"]
        caruncle = bpy.data.objects[f"AevryndEye_{side}_Caruncle_R258"]
        overlaps[side] = {
            "bodyVsIntegratedEye": len(body_tree.overlap(world_bvh(sclera, depsgraph))),
            "bodyVsCaruncle": len(body_tree.overlap(world_bvh(caruncle, depsgraph))),
        }
    for view_name, location, target, lens in views:
        camera.location = location
        camera.data.lens = lens
        look_at(camera, target)
        scene.render.resolution_x = scene.render.resolution_y = 1000
        scene.render.filepath = str(RENDER_DIR / f"{label}-{view_name}.png")
        bpy.ops.render.render(write_still=True)
    metrics[label] = {"strength": strength, **edit, "triangleOverlaps": overlaps}
    previous = body

report = {
    "source": str(SOURCE),
    "renderDirectory": str(RENDER_DIR),
    "variants": metrics,
    "method": "Continuous body-surface upper-lid roll, upper crease, lower-lid roll and medial tear-trough displacement fields; no separate eyelid overlay geometry.",
    "status": "VISUAL_AND_COLLISION_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R410_ORBITAL_FOLD_SWEEP=" + json.dumps(report, sort_keys=True))
