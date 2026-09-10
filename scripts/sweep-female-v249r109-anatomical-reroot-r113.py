import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-tear-meniscus-r109.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r109-anatomical-reroot-r113-sweep"
MAIN = "AevryndFemaleCC0LongHairStudyMain_v249r85"
BODY = "AevryndFemaleBodyBaseV118"
ROOT_COUNT = 72
CLEARANCE = 0.0015
VARIANTS = (
    ("a-control", 0.0),
    ("b-subtle-0p45", 0.45),
    ("c-balanced-0p70", 0.70),
    ("d-full-1p00", 1.00),
)


def smooth(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def evaluated_tree(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, faces, all_triangles=False)


def root_world(obj, curve):
    return obj.matrix_world @ obj.data.points[curve.first_point_index].position


def hairline_height(x):
    side = min(1.0, abs(x) / 0.090)
    # A shallow M contour: a lower centre point and gradual temporal recession.
    return 1.663 + 0.026 * side ** 1.55


def choose_front_curves(obj):
    candidates = []
    for index, curve in enumerate(obj.data.curves):
        root = root_world(obj, curve)
        if root.y <= -0.050 and abs(root.x) <= 0.098 and root.z >= 1.655:
            candidates.append((index, root))
    selected = []
    used = set()
    for bin_index in range(ROOT_COUNT):
        x = -0.092 + 0.184 * (bin_index + 0.5) / ROOT_COUNT
        z = hairline_height(x)
        seed = Vector((x, -0.135, z))
        ranked = sorted(
            candidates,
            key=lambda item: (item[1] - seed).length_squared + 1.7 * (item[1].x - x) ** 2,
        )
        match = next((item for item in ranked if item[0] not in used), None)
        if match is None:
            break
        used.add(match[0])
        selected.append(match)
    return selected, len(candidates)


def target_root(tree, root, order):
    jitter = (((order * 37) % 11) / 10.0 - 0.5) * 0.0040
    seed = Vector((root.x, -0.150, hairline_height(root.x) + jitter))
    hit = tree.find_nearest(seed, 0.065)
    if hit is None or hit[1] is None:
        raise RuntimeError(f"could not project anatomical root at {tuple(seed)}")
    return hit[0] + hit[1].normalized() * CLEARANCE


def project_clear(tree, point):
    hit = tree.find_nearest(point, 0.040)
    if hit is None or hit[1] is None:
        return point, False
    normal = hit[1].normalized()
    signed = (point - hit[0]).dot(normal)
    if signed >= CLEARANCE:
        return point, False
    return hit[0] + normal * CLEARANCE, True


def apply_reroot(obj, tree, strength):
    obj.data = obj.data.copy()
    inverse = obj.matrix_world.inverted()
    selected, eligible = choose_front_curves(obj)
    moved_points = projected_points = 0
    maximum = 0.0
    root_shifts = []
    for order, (curve_index, original_root) in enumerate(selected):
        curve = obj.data.curves[curve_index]
        target = target_root(tree, original_root, order)
        delta = (target - original_root) * strength
        root_shifts.append(delta.length * 1000.0)
        for local_index in range(curve.points_length):
            unit = local_index / max(1, curve.points_length - 1)
            envelope = 1.0 - smooth(unit / 0.42)
            if envelope <= 0.0:
                continue
            point = obj.data.points[curve.first_point_index + local_index]
            world = obj.matrix_world @ point.position
            candidate = world + delta * envelope
            candidate, projected = project_clear(tree, candidate)
            displacement = (candidate - world).length
            if displacement > 1.0e-9:
                point.position = inverse @ candidate
                moved_points += 1
                maximum = max(maximum, displacement)
            projected_points += int(projected)
    return {
        "eligibleCurves": eligible,
        "selectedCurves": len(selected),
        "movedPoints": moved_points,
        "collisionProjectedPoints": projected_points,
        "maximumDisplacementMm": maximum * 1000.0,
        "rootShiftMm": {
            "minimum": min(root_shifts) if root_shifts else 0.0,
            "average": sum(root_shifts) / len(root_shifts) if root_shifts else 0.0,
            "maximum": max(root_shifts) if root_shifts else 0.0,
        },
    }


def render(camera, name, location, target, lens):
    scene = bpy.context.scene
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


OUT.mkdir(parents=True, exist_ok=True)
report = {"source": str(SOURCE), "rootCount": ROOT_COUNT, "variants": []}
for name, strength in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    main = bpy.data.objects[MAIN]
    metrics = apply_reroot(main, evaluated_tree(bpy.data.objects[BODY]), strength) if strength else {
        "eligibleCurves": None, "selectedCurves": 0, "movedPoints": 0,
        "collisionProjectedPoints": 0, "maximumDisplacementMm": 0.0,
        "rootShiftMm": {"minimum": 0.0, "average": 0.0, "maximum": 0.0},
    }
    camera = bpy.data.objects["Aevrynd Review Camera"]
    for suffix, location, target, lens in (
        ("01-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
        ("02-three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88),
        ("03-top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
    ):
        render(camera, f"{name}-{suffix}", location, target, lens)
    metrics.update({"name": name, "strength": strength})
    report["variants"].append(metrics)

(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_ANATOMICAL_REROOT_R113=" + json.dumps(report, sort_keys=True))
