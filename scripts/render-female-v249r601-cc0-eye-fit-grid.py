import json
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-eye-composite-v260.blend"
OUT = ASSETS / "reviews/v249r601-cc0-eye-fit-grid"
REPORT = ASSETS / "female-v249-mainline-cc0-eye-fit-r601.study.json"
BODY = "AevryndFemaleCC0Baseline_v259"
PARTS = ("Sclera", "Cornea", "Iris")
SCALES = (0.90, 0.80, 0.70)
DEPTHS_M = (-0.002, 0.0, 0.002)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, faces, all_triangles=False)


OUT.mkdir(parents=True, exist_ok=True)
results = {}
for scale in SCALES:
    for depth in DEPTHS_M:
        bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
        scene = bpy.context.scene
        scene.frame_set(1)
        body = bpy.data.objects[BODY]
        eye_centers = {}
        for side in ("L", "R"):
            sclera = bpy.data.objects[f"Eye_{side}_Sclera"]
            points = [sclera.matrix_world @ vertex.co for vertex in sclera.data.vertices]
            eye_centers[side] = sum(points, Vector()) / len(points)
        for side in ("L", "R"):
            center = eye_centers[side]
            for part in PARTS:
                obj = bpy.data.objects[f"Eye_{side}_{part}"]
                inverse = obj.matrix_world.inverted()
                original = [vertex.co.copy() for vertex in obj.data.vertices]
                for vertex, source in zip(obj.data.vertices, original):
                    world = obj.matrix_world @ source
                    fitted = center + (world - center) * scale + Vector((0.0, depth, 0.0))
                    vertex.co = inverse @ fitted
                obj.data.update()
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        body_tree = tree(body, depsgraph)
        overlap = {
            f"Eye_{side}_{part}": len(body_tree.overlap(tree(bpy.data.objects[f"Eye_{side}_{part}"], depsgraph)))
            for side in ("L", "R") for part in PARTS
        }
        label = f"scale-{scale:.2f}-depth-{depth * 1000:+.0f}mm".replace(".", "p").replace("+", "plus").replace("-", "minus")
        scene.render.engine = "BLENDER_EEVEE"
        scene.view_settings.view_transform = "Standard"
        scene.view_settings.look = "None"
        scene.view_settings.exposure = 0.0
        scene.view_settings.gamma = 1.0
        scene.render.image_settings.file_format = "PNG"
        scene.render.resolution_x = scene.render.resolution_y = 700
        scene.render.resolution_percentage = 100
        camera = bpy.data.objects["Aevrynd Baseline Camera"]
        scene.camera = camera
        camera.location = (0.0, -1.22, 1.55)
        camera.data.lens = 105
        look_at(camera, (0.0, -0.01, 1.55))
        scene.render.filepath = str(OUT / f"{label}.png")
        bpy.ops.render.render(write_still=True)
        results[label] = {
            "relativeScaleFromV260": scale,
            "worldDepthShiftM": depth,
            "overlapPairs": overlap,
            "totalOverlapPairs": sum(overlap.values()),
            "collisionPass": not any(overlap.values()),
        }

report = {
    "source": str(SOURCE),
    "v260ImportedEyeScale": 1.08,
    "method": "uniformly scale each complete sclera/cornea/iris stack around its shared center, then translate it along world Y; audit evaluated body overlap before visual selection",
    "variants": results,
    "status": "GRID_COMPLETE_PENDING_STRICT_VISUAL_SELECTION",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R601_CC0_EYE_FIT_GRID=" + json.dumps(report, sort_keys=True))
