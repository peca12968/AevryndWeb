import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-damped-outer-card-motion-r587.blend"
OUT = ASSETS / "reviews/v249r590-asymmetric-part-flow-sweep"
REPORT = ASSETS / "female-v249-mainline-asymmetric-part-flow-r590.study.json"
COVERAGE = "AevryndFemaleOwnedScalpGuideGroom_R587_Coverage"
BODY = "AevryndFemaleBodyBaseV118"
POINTS_PER_CURVE = 24
CLEARANCE = 0.002
VARIANTS = (
    ("a-r587-current", 0, 0.0),
    ("b-left-roots-sweep-right-8mm", 1, 0.008),
    ("c-right-roots-sweep-left-8mm", -1, 0.008),
    ("d-right-roots-sweep-left-14mm", -1, 0.014),
)
VIEWS = (
    ("front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
    ("three-quarter", (0.45, -0.66, 1.60), (0.0, -0.005, 1.56), 84),
    ("profile", (0.72, -0.03, 1.61), (0.0, 0.0, 1.58), 88),
    ("back", (0.0, 0.72, 1.60), (0.0, 0.025, 1.58), 88),
    ("top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
)


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def smoothstep(value):
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def part_x(y):
    return -0.021 + 0.017 * smoothstep((y + 0.105) / 0.155)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def evaluated_tree(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, faces, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
scene.view_settings.gamma = 1.0
scene.render.image_settings.file_format = "PNG"
scene.render.resolution_x = 650
scene.render.resolution_y = 650
scene.render.resolution_percentage = 100
OUT.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
coverage = bpy.data.objects[COVERAGE]
tree = evaluated_tree(bpy.data.objects[BODY])
world = coverage.matrix_world.copy()
inverse = world.inverted()
original = [point.position.copy() for point in coverage.data.points]

variant_report = {}
for label, direction, strength in VARIANTS:
    for index, point in enumerate(coverage.data.points):
        point.position = original[index]
    moved_curves = 0
    maximum_displacement = 0.0
    if direction:
        for curve_index in range(len(coverage.data.curves)):
            root = original[curve_index * POINTS_PER_CURVE]
            seam = part_x(root.y)
            side_matches = root.x < seam if direction > 0 else root.x > seam
            if not (-0.108 <= root.y <= 0.052 and abs(root.x - seam) <= 0.018 and side_matches):
                continue
            moved_curves += 1
            for local_index in range(1, 16):
                index = curve_index * POINTS_PER_CURVE + local_index
                t = local_index / 15.0
                bump = math.sin(math.pi * t) ** 1.15
                candidate = original[index] + Vector((direction * strength * bump, 0.0, 0.0))
                candidate_world = world @ candidate
                hit = tree.find_nearest(candidate_world, 0.040)
                if hit is not None and hit[1] is not None:
                    signed = (candidate_world - hit[0]).dot(hit[1].normalized())
                    if signed < CLEARANCE:
                        candidate_world += hit[1].normalized() * (CLEARANCE - signed)
                        candidate = inverse @ candidate_world
                coverage.data.points[index].position = candidate
                maximum_displacement = max(maximum_displacement, (candidate - original[index]).length)
    bpy.context.view_layer.update()
    for view, location, target, lens in VIEWS:
        camera.location = location
        camera.data.lens = lens
        look_at(camera, target)
        scene.render.filepath = str(OUT / f"{label}-{view}.png")
        bpy.ops.render.render(write_still=True)
    variant_report[label] = {
        "direction": direction,
        "strengthM": strength,
        "movedCurves": moved_curves,
        "maximumProjectedDisplacementM": maximum_displacement,
        "rootDriftM": 0.0,
        "affectedControlPoints": "1-15 with a zero-ended sine envelope",
    }

report = {
    "source": str(SOURCE),
    "method": "move only near-part coverage curves from one root side through a projected scalp-following lateral envelope; keep every root and tail endpoint fixed",
    "variants": variant_report,
    "fixed": ["r587 outer cards and motion", "r587 colour", "r586 1.5x outer alpha", "camera", "lights", "Standard/None exposure 0"],
    "status": "VISUAL_SWEEP_PENDING_REVIEW",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R590_ASYMMETRIC_PART_FLOW=" + json.dumps(report, sort_keys=True))
