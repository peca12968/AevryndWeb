import json
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-clipped-optical-fronts-r493.blend"
REPORT = ASSETS / "female-v249-mainline-caruncle-wedge-r494.study.json"
RENDER_DIR = ASSETS / "reviews/v249r494-caruncle-wedge-sweep"
BODY = "AevryndFemaleBodyBaseV118"
VARIANTS = (
    ("a-baseline", 1.00, 1.00, 1.00),
    ("b-readable-wedge", 2.50, 0.70, 0.75),
    ("c-anatomical-wedge", 3.50, 0.65, 0.72),
    ("d-maximum-wedge", 4.50, 0.60, 0.70),
)


def tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(points, faces, all_triangles=False)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, camera, name, location, target, lens, size):
    scene.frame_set(1)
    bpy.context.view_layer.update()
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
caruncles = {side: bpy.data.objects[f"Eye_{side}_Caruncle"] for side in ("L", "R")}
original = {
    side: [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    for side, obj in caruncles.items()
}
centers = {side: sum(points, Vector()) / len(points) for side, points in original.items()}


def apply_shape(toward_eye, medial, vertical):
    for side, obj in caruncles.items():
        inverse = obj.matrix_world.inverted()
        center = centers[side]
        eye_sign = 1.0 if side == "L" else -1.0
        for index, source in enumerate(original[side]):
            point = source.copy()
            anatomical = (point.x - center.x) * eye_sign
            point.x = center.x + (point.x - center.x) * (toward_eye if anatomical >= 0.0 else medial)
            point.z = center.z + (point.z - center.z) * vertical
            obj.data.vertices[index].co = inverse @ point
        obj.data.update()


scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
scene.render.image_settings.file_format = "PNG"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
metrics = {}
for label, toward_eye, medial, vertical in VARIANTS:
    apply_shape(toward_eye, medial, vertical)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    body_tree = tree(bpy.data.objects[BODY], depsgraph)
    collisions = {}
    dimensions = {}
    for side, obj in caruncles.items():
        caruncle_tree = tree(obj, depsgraph)
        collisions[side] = {
            "body": len(body_tree.overlap(caruncle_tree)),
            "sclera": len(tree(bpy.data.objects[f"Eye_{side}_Sclera"], depsgraph).overlap(caruncle_tree)),
            "cornea": len(tree(bpy.data.objects[f"Eye_{side}_Cornea"], depsgraph).overlap(caruncle_tree)),
            "tearMeniscus": len(tree(bpy.data.objects[f"Eye_{side}_TearMeniscus"], depsgraph).overlap(caruncle_tree)),
        }
        dimensions[side] = [float(value) for value in obj.dimensions]
    render(scene, camera, label + "-eye-close", (0.0, -0.49, 1.615), (0.0, -0.13, 1.610), 105, (1200, 700))
    render(scene, camera, label + "-three-quarter", (0.45, -0.66, 1.60), (0.0, -0.005, 1.56), 84, (1000, 1000))
    metrics[label] = {
        "towardEyeScale": toward_eye,
        "medialScale": medial,
        "verticalScale": vertical,
        "dimensionsM": dimensions,
        "triangleOverlaps": collisions,
        "collisionPass": all(value == 0 for side in collisions.values() for value in side.values()),
    }

report = {
    "source": str(SOURCE),
    "method": "asymmetric reshape of the existing owned 15-vertex caruncle: extend only toward the eye, taper toward the nose and flatten vertically",
    "variants": metrics,
    "renderDirectory": str(RENDER_DIR),
    "status": "VISUAL_REVIEW_REQUIRED",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R494_CARUNCLE_WEDGE=" + json.dumps(report, sort_keys=True))
