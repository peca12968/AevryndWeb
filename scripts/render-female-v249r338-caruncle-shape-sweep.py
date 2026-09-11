import json
from pathlib import Path

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-natural-sclera-r337.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-caruncle-shape-r338.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r338-caruncle-shape-sweep"
BODY = "AevryndFemaleBody_CC0_R249"
VARIANTS = (
    ("a-r337-baseline", 1.0, 1.0, 1.0, 0.0),
    ("b-medial-small", 1.6, 1.15, 1.20, 0.00035),
    ("c-medial-medium", 2.0, 1.20, 1.35, 0.00055),
    ("d-medial-large", 2.4, 1.20, 1.50, 0.00070),
)


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


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
objects = {side: bpy.data.objects[f"AevryndEye_{side}_Caruncle_R258"] for side in ("L", "R")}
originals = {side: (obj.matrix_world.copy(), obj.scale.copy()) for side, obj in objects.items()}
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
for label, sx, sy, sz, medial in VARIANTS:
    for side, obj in objects.items():
        matrix, scale = originals[side]
        obj.matrix_world = matrix @ Matrix.Diagonal((sx, sy, sz, 1.0))
        obj.matrix_world.translation.x += -medial if side == "L" else medial
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    body_tree = world_bvh(bpy.data.objects[BODY], depsgraph)
    collisions = {}
    dimensions = {}
    for side, obj in objects.items():
        tree = world_bvh(obj, depsgraph)
        eye = bpy.data.objects[f"AevryndEye_{side}_Sclera_R249"]
        collisions[side] = {
            "bodyVsCaruncle": len(body_tree.overlap(tree)),
            "eyeVsCaruncle": len(world_bvh(eye, depsgraph).overlap(tree)),
        }
        dimensions[side] = list(obj.dimensions)
    for view_name, location, target, lens in views:
        camera.location = location
        camera.data.lens = lens
        look_at(camera, target)
        scene.render.resolution_x = scene.render.resolution_y = 1000
        scene.render.filepath = str(RENDER_DIR / f"{label}-{view_name}.png")
        bpy.ops.render.render(write_still=True)
    metrics[label] = {
        "scaleXYZ": [sx, sy, sz], "medialShiftM": medial,
        "worldDimensionsM": dimensions, "triangleOverlaps": collisions,
    }

report = {
    "source": str(SOURCE), "renderDirectory": str(RENDER_DIR), "variants": metrics,
    "method": "Scale the existing owned head-bound caruncle mesh into progressively wider tissue while shifting its center toward the nasal canthus; audit body and integrated-eye triangle overlap.",
    "status": "VISUAL_AND_COLLISION_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R338_CARUNCLE_SHAPE=" + json.dumps(report, sort_keys=True))
