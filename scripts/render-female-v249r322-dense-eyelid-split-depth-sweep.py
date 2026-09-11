import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-collision-safe-optical-stack-r318.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-dense-eyelid-split-depth-r322.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r322-dense-eyelid-split-depth-sweep"
BODY = "AevryndFemaleBody_CC0_R249"
EYES = {"L": (0.034528, 1.607765, 1.0), "R": (-0.034443, 1.607765, -1.0)}
SOURCE_APERTURE = 0.0027
CLEARANCE = 0.00012
APERTURE = 0.0022
SCLERA_RECESS = 0.0003
VARIANTS = (("a-optical-forward-0p3mm", 0.0003), ("b-optical-forward-0p6mm", 0.0006), ("c-optical-forward-0p9mm", 0.0009))


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def lid_height(side, x, aperture):
    cx, cz, anatomical_sign = EYES[side]
    u = max(-1.0, min(1.0, (x - cx) / 0.01035))
    edge = math.sqrt(max(0.0, 1.0 - u * u))
    return cz + aperture * edge - 0.00032 * anatomical_sign * u * edge


def bvh(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, faces, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


def make_dense_body(source, depsgraph, name):
    evaluated = source.evaluated_get(depsgraph)
    mesh = bpy.data.meshes.new_from_object(evaluated, depsgraph=depsgraph)
    mesh.name = name + "Geometry"
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.matrix_world = source.matrix_world.copy()
    for slot in source.material_slots:
        if slot.material and slot.material.name not in [m.name for m in mesh.materials]:
            mesh.materials.append(slot.material)
    return obj


def sculpt_upper_lids(body, aperture, eye_trees):
    inverse = body.matrix_world.inverted()
    moved = {"L": 0, "R": 0}
    maximum_delta = 0.0
    diagnostic = {"sideWindow": 0, "verticalWindow": 0, "nearestHit": 0, "within6mm": 0}
    for vertex in body.data.vertices:
        world = body.matrix_world @ vertex.co
        side = "L" if world.x >= 0 else "R"
        cx, cz, _ = EYES[side]
        u = (world.x - cx) / 0.01035
        if abs(u) >= 1.04:
            continue
        diagnostic["sideWindow"] += 1
        edge = math.sqrt(max(0.0, 1.0 - min(1.0, u * u)))
        target = lid_height(side, world.x, aperture)
        if world.z <= target or world.z >= cz + 0.0125:
            continue
        diagnostic["verticalWindow"] += 1
        nearest = eye_trees[side]["Sclera_R249"].find_nearest(world, 0.012)
        if nearest is None or nearest[0] is None or nearest[3] is None:
            continue
        diagnostic["nearestHit"] += 1
        location, normal, _index, distance = nearest
        if distance > 0.006:
            continue
        diagnostic["within6mm"] += 1
        proximity = max(0.0, min(1.0, (0.006 - distance) / 0.0055))
        vertical = max(0.0, min(1.0, (cz + 0.0105 - world.z) / 0.009))
        weight = (proximity ** 1.35) * (vertical ** 0.8) * (edge ** 0.45)
        if weight < 0.02:
            continue
        before = world.copy()
        world.z += (target - world.z) * weight
        # Keep the continuous skin shell outside the spherical sclera while it wraps down.
        hit = eye_trees[side]["Sclera_R249"].find_nearest(world, 0.003)
        if hit is not None and hit[0] is not None and hit[1] is not None:
            location, normal, _index, distance = hit
            normal = normal.normalized()
            signed = (world - location).dot(normal)
            if signed < CLEARANCE:
                world = location + normal * CLEARANCE
        vertex.co = inverse @ world
        moved[side] += 1
        maximum_delta = max(maximum_delta, (world - before).length)
    body.data.update()
    return {"movedVertices": moved, "maximumDisplacementM": maximum_delta, "diagnostic": diagnostic}


def set_attached_curves(aperture, originals):
    for name, points in originals.items():
        obj = bpy.data.objects[name]
        side = "L" if "_L_" in name else "R"
        index = 0
        for spline in obj.data.splines:
            for point in spline.points:
                base = points[index]
                point.co = base.copy()
                point.co.z += lid_height(side, point.co.x, aperture) - lid_height(side, point.co.x, SOURCE_APERTURE)
                index += 1


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
depsgraph = bpy.context.evaluated_depsgraph_get()
source_body = bpy.data.objects[BODY]
eye_trees = {
    side: {
        part: bvh(bpy.data.objects[f"AevryndEye_{side}_{part}"], depsgraph)
        for part in ("Sclera_R249", "Cornea_R252", "Limbal_R253", "Iris_R253", "Pupil_R253")
    }
    for side in EYES
}
for side in EYES:
    overlay = bpy.data.objects.get(f"AevryndEye_{side}_UpperLidSurface_R308")
    if overlay:
        overlay.hide_render = True
source_body.hide_render = True

curve_names = [name for side in EYES for name in (f"AevryndEye_{side}_UpperLidMargin_R258", f"AevryndFemaleUpperLashes_{side}_R256")]
original_curves = {}
for name in curve_names:
    obj = bpy.data.objects[name]
    obj.data = obj.data.copy()
    original_curves[name] = [point.co.copy() for spline in obj.data.splines for point in spline.points]

scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
views = (
    ("front", (0.0, -0.68, 1.605), (0.0, -0.035, 1.606), 92),
    ("three-quarter", (0.45, -0.62, 1.62), (0.0, -0.02, 1.605), 90),
)
metrics = {}
previous = None
eye_objects = [bpy.data.objects[f"AevryndEye_{side}_{part}"] for side in EYES for part in ("Sclera_R249", "Cornea_R252", "Limbal_R253", "Iris_R253", "Pupil_R253")]
eye_matrices = {obj.name: obj.matrix_world.copy() for obj in eye_objects}
for label, advance in VARIANTS:
    if previous:
        bpy.data.objects.remove(previous, do_unlink=True)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    body = make_dense_body(source_body, depsgraph, f"AevryndFemaleBodyDenseLids_{label}")
    edit = sculpt_upper_lids(body, APERTURE, eye_trees)
    set_attached_curves(APERTURE, original_curves)
    for obj in eye_objects:
        matrix = eye_matrices[obj.name].copy()
        matrix.translation.y += SCLERA_RECESS if "Sclera" in obj.name else -advance
        obj.matrix_world = matrix
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    overlaps = {}
    body_tree = bvh(body, depsgraph)
    for side in EYES:
        overlaps[side] = {}
        for part in ("Sclera_R249", "Cornea_R252", "Limbal_R253", "Iris_R253", "Pupil_R253"):
            eye = bpy.data.objects[f"AevryndEye_{side}_{part}"]
            overlaps[side][part] = len(body_tree.overlap(bvh(eye, depsgraph)))
    metrics[label] = {"apertureM": APERTURE, "scleraRecessM": SCLERA_RECESS, "frontOpticalAdvanceM": advance, **edit, "bodyEyeTriangleOverlaps": overlaps}
    for view_name, location, target, lens in views:
        camera.location = location
        camera.data.lens = lens
        look_at(camera, target)
        scene.render.resolution_x = scene.render.resolution_y = 1000
        scene.render.filepath = str(RENDER_DIR / f"{label}-{view_name}.png")
        bpy.ops.render.render(write_still=True)
    previous = body

report = {
    "source": str(SOURCE),
    "method": "Use the selected 2.2mm dense native upper lid from r320, recess the sclera by 0.3mm, and test small anterior offsets for the already intersection-free front optical stack.",
    "renderDirectory": str(RENDER_DIR),
    "variants": metrics,
    "status": "VISUAL_AND_COLLISION_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R322_DENSE_EYELID_SPLIT_DEPTH_SWEEP=" + json.dumps(report, sort_keys=True))
