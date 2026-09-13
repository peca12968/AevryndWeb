import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-canthus-fitted-wedge-r345.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-recessed-canthus-r412.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r412-recessed-canthus-sweep"
BODY = "AevryndFemaleBody_CC0_R249"
EYES = {"L": (0.034528, 1.607765, 1.0), "R": (-0.034443, 1.607765, -1.0)}
OLD_HALF = 0.01025
UPPER_APERTURE = 0.0022
LOWER_APERTURE = 0.0041
VARIANTS = (
    ("a-20p0mm", 0.0100, 0.0008),
    ("b-19p6mm", 0.0098, 0.0010),
    ("c-19p2mm", 0.0096, 0.0012),
)


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def smoothstep(value):
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def gaussian(value, sigma):
    return math.exp(-((value / sigma) ** 2))


def edge(lateral, half):
    return math.sqrt(max(0.0, 1.0 - min(1.0, (lateral / half) ** 2)))


def margin_z(cz, lateral, half, upper):
    aperture = UPPER_APERTURE if upper else -LOWER_APERTURE
    return cz + aperture * edge(lateral, half)


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


def sculpt_outer_canthus(body, new_half):
    inverse = body.matrix_world.inverted()
    moved = {"L": 0, "R": 0}
    maximum = 0.0
    for vertex in body.data.vertices:
        world = body.matrix_world @ vertex.co
        if not (-0.122 <= world.y <= -0.112):
            continue
        side = "L" if world.x >= 0.0 else "R"
        cx, cz, sign = EYES[side]
        dx = world.x - cx
        lateral = sign * dx
        if lateral <= 0.0015 or lateral >= 0.0134 or abs(world.z - cz) > 0.0115:
            continue
        upper = world.z >= cz
        old_z = margin_z(cz, lateral, OLD_HALF, upper)
        margin_weight = gaussian(world.z - old_z, 0.0032)
        lateral_weight = smoothstep((lateral - 0.0015) / 0.0065)
        outer_fade = 1.0 - smoothstep((lateral - 0.0117) / 0.0017)
        weight = margin_weight * lateral_weight * outer_fade
        if weight < 0.002:
            continue
        target_lateral = lateral * new_half / OLD_HALF
        target_z = margin_z(cz, target_lateral, new_half, upper)
        before = world.copy()
        world.x += sign * (target_lateral - lateral) * weight
        world.z += (target_z - old_z) * weight
        vertex.co = inverse @ world
        moved[side] += 1
        maximum = max(maximum, (world - before).length)
    body.data.update()
    return {"movedVertices": moved, "maximumDisplacementM": maximum}


def attached_names():
    return [
        name
        for side in EYES
        for name in (
            f"AevryndEye_{side}_Sclera_R249",
            f"AevryndEye_{side}_Caruncle_R258",
            f"AevryndEye_{side}_UpperLidMargin_R258",
            f"AevryndEye_{side}_LowerLidMargin_R258",
            f"AevryndEye_{side}_TearMeniscus_R258",
            f"AevryndFemaleUpperLashes_{side}_R256",
            f"AevryndFemaleLowerLashes_{side}_R256",
        )
    ]


def curve_point_snapshot(obj):
    return [point.co.copy() for spline in obj.data.splines for point in spline.points]


def restore_and_fit_layers(new_half, recess, matrices, curves):
    moved_points = 0
    for name in attached_names():
        obj = bpy.data.objects[name]
        obj.matrix_world = matrices[name].copy()
        obj.matrix_world.translation.y += recess
        if obj.type != "CURVE":
            continue
        original = curves[name]
        point_index = 0
        side = "L" if "_L_" in name else "R"
        cx, cz, sign = EYES[side]
        upper = "Upper" in name
        if "Lower" in name or "Meniscus" in name:
            upper = False
        for spline in obj.data.splines:
            for point in spline.points:
                point.co = original[point_index].copy()
                dx = point.co.x - cx
                lateral = sign * dx
                if lateral > 0.0015:
                    blend = smoothstep((lateral - 0.0015) / 0.0065)
                    target_lateral = lateral * (1.0 - blend + blend * new_half / OLD_HALF)
                    point.co.x = cx + sign * target_lateral
                    point.co.z += (margin_z(cz, target_lateral, new_half, upper) - margin_z(cz, lateral, OLD_HALF, upper)) * blend
                    moved_points += 1
                point_index += 1
    return moved_points


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
source_body = bpy.data.objects[BODY]
source_body.hide_render = True
names = attached_names()
matrices = {name: bpy.data.objects[name].matrix_world.copy() for name in names}
curves = {}
for name in names:
    obj = bpy.data.objects[name]
    if obj.type == "CURVE":
        obj.data = obj.data.copy()
        curves[name] = curve_point_snapshot(obj)

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
for label, new_half, recess in VARIANTS:
    if previous is not None:
        bpy.data.objects.remove(previous, do_unlink=True)
    body = make_body(source_body, f"AevryndFemaleRecessedCanthus_{label}")
    edit = sculpt_outer_canthus(body, new_half)
    moved_points = restore_and_fit_layers(new_half, recess, matrices, curves)
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
    metrics[label] = {
        "outerHalfWidthM": new_half,
        "nominalFullWidthM": new_half * 2.0,
        "layerRecessM": recess,
        **edit,
        "movedAttachedCurvePoints": moved_points,
        "triangleOverlaps": overlaps,
    }
    previous = body

report = {
    "source": str(SOURCE),
    "renderDirectory": str(RENDER_DIR),
    "variants": metrics,
    "method": "Recess the complete head-bound eye layer stack, then continuously move both X and Z for outer-canthus skin and attached curves toward a narrower lateral ellipse.",
    "status": "VISUAL_AND_COLLISION_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R412_RECESSED_CANTHUS_SWEEP=" + json.dumps(report, sort_keys=True))
