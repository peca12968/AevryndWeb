import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-integrated-eye-shader-r328.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-dense-lower-eyelid-r332.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r332-dense-lower-eyelid-sweep"
BODY = "AevryndFemaleBody_CC0_R249"
EYES = {"L": (0.034528, 1.607765), "R": (-0.034443, 1.607765)}
SOURCE_APERTURE = 0.00448
VARIANTS = (("a-4p1mm", 0.0041), ("b-3p8mm", 0.0038), ("c-3p5mm", 0.0035))


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def lower_height(side, x, aperture):
    cx, cz = EYES[side]
    u = max(-1.0, min(1.0, (x - cx) / 0.01025))
    edge = math.sqrt(max(0.0, 1.0 - u * u))
    return cz - aperture * edge


def world_bvh(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, faces, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


def make_body_variant(source, name):
    mesh = source.data.copy()
    mesh.name = name + "Geometry"
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.matrix_world = source.matrix_world.copy()
    for material in source.data.materials:
        if material and material.name not in [item.name for item in mesh.materials]:
            mesh.materials.append(material)
    return obj


def sculpt_lower_lids(body, aperture, sclera_trees):
    inverse = body.matrix_world.inverted()
    moved = {"L": 0, "R": 0}
    maximum = 0.0
    for vertex in body.data.vertices:
        world = body.matrix_world @ vertex.co
        side = "L" if world.x >= 0 else "R"
        cx, cz = EYES[side]
        u = (world.x - cx) / 0.01025
        if abs(u) >= 1.02:
            continue
        edge = math.sqrt(max(0.0, 1.0 - min(1.0, u * u)))
        target = lower_height(side, world.x, aperture)
        if world.z >= target or world.z <= cz - 0.012:
            continue
        hit = sclera_trees[side].find_nearest(world, 0.010)
        if hit is None or hit[0] is None or hit[3] is None or hit[3] > 0.0045:
            continue
        distance = hit[3]
        proximity = max(0.0, min(1.0, (0.0045 - distance) / 0.0040))
        vertical = max(0.0, min(1.0, (world.z - (cz - 0.0105)) / 0.009))
        weight = (proximity ** 1.45) * (vertical ** 0.85) * (edge ** 0.5)
        if weight < 0.025:
            continue
        before = world.copy()
        world.z += (target - world.z) * weight
        vertex.co = inverse @ world
        moved[side] += 1
        maximum = max(maximum, (world - before).length)
    body.data.update()
    return {"movedVertices": moved, "maximumDisplacementM": maximum}


def set_attached_curves(aperture, originals):
    for name, points in originals.items():
        obj = bpy.data.objects[name]
        side = "L" if "_L_" in name else "R"
        index = 0
        for spline in obj.data.splines:
            for point in spline.points:
                point.co = points[index].copy()
                point.co.z += lower_height(side, point.co.x, aperture) - lower_height(side, point.co.x, SOURCE_APERTURE)
                index += 1


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
depsgraph = bpy.context.evaluated_depsgraph_get()
source_body = bpy.data.objects[BODY]
sclera_trees = {side: world_bvh(bpy.data.objects[f"AevryndEye_{side}_Sclera_R249"], depsgraph) for side in EYES}
source_body.hide_render = True
curve_names = [
    name for side in EYES for name in (
        f"AevryndEye_{side}_LowerLidMargin_R258",
        f"AevryndEye_{side}_TearMeniscus_R258",
        f"AevryndFemaleLowerLashes_{side}_R256",
    )
]
originals = {}
for name in curve_names:
    obj = bpy.data.objects[name]
    obj.data = obj.data.copy()
    originals[name] = [point.co.copy() for spline in obj.data.splines for point in spline.points]

scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
views = (
    ("face", (0.0, -0.68, 1.605), (0.0, -0.035, 1.606), 92),
    ("eyes", (0.0, -0.46, 1.615), (0.0, -0.035, 1.610), 105),
    ("three-quarter", (0.45, -0.62, 1.62), (0.0, -0.02, 1.605), 90),
)
metrics = {}
previous = None
for label, aperture in VARIANTS:
    if previous:
        bpy.data.objects.remove(previous, do_unlink=True)
    body = make_body_variant(source_body, f"AevryndFemaleBodyLowerLid_{label}")
    edit = sculpt_lower_lids(body, aperture, sclera_trees)
    set_attached_curves(aperture, originals)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    body_tree = world_bvh(body, depsgraph)
    overlaps = {side: len(body_tree.overlap(world_bvh(bpy.data.objects[f"AevryndEye_{side}_Sclera_R249"], depsgraph))) for side in EYES}
    metrics[label] = {"lowerApertureM": aperture, **edit, "bodyScleraTriangleOverlaps": overlaps}
    for view_name, location, target, lens in views:
        camera.location = location
        camera.data.lens = lens
        look_at(camera, target)
        scene.render.resolution_x = scene.render.resolution_y = 1000
        scene.render.filepath = str(RENDER_DIR / f"{label}-{view_name}.png")
        bpy.ops.render.render(write_still=True)
    previous = body

report = {
    "source": str(SOURCE), "renderDirectory": str(RENDER_DIR), "variants": metrics,
    "method": "Raise the lower eyelid on the continuous 169,362-vertex body with sclera-proximity falloff and move lower lid-margin, tear-film and lash curves by the same aperture delta.",
    "status": "VISUAL_AND_COLLISION_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R332_DENSE_LOWER_EYELID_SWEEP=" + json.dumps(report, sort_keys=True))
