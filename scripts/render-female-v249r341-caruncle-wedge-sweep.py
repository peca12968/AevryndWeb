import json
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-integrated-caruncle-r340.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-caruncle-wedge-r341.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r341-caruncle-wedge-sweep"
BODY = "AevryndFemaleBody_CC0_R249"
VARIANTS = (("a-r340-ellipsoid", 0.0), ("b-soft-wedge", 0.25), ("c-medium-wedge", 0.40), ("d-strong-wedge", 0.55))


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


def apply_wedge(side, obj, coordinates, taper):
    lateral_sign = 1.0 if side == "L" else -1.0
    half_width = 0.00058
    maximum = 0.0
    for vertex, source in zip(obj.data.vertices, coordinates):
        u = max(-1.0, min(1.0, lateral_sign * source.x / half_width))  # -1 nasal, +1 globe
        along = (u + 1.0) * 0.5
        cross = 1.0 - taper * along
        target = source.copy()
        target.y *= cross
        target.z *= cross
        # Bias the mass toward the nasal base while retaining the two endpoint locations.
        target.x -= lateral_sign * taper * 0.00008 * (1.0 - u * u)
        maximum = max(maximum, (target - source).length)
        vertex.co = target
    obj.data.update()
    return maximum


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
objects = {side: bpy.data.objects[f"AevryndEye_{side}_Caruncle_R258"] for side in ("L", "R")}
originals = {}
for side, obj in objects.items():
    obj.data = obj.data.copy()
    originals[side] = [vertex.co.copy() for vertex in obj.data.vertices]

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
for label, taper in VARIANTS:
    displacement = {side: apply_wedge(side, obj, originals[side], taper) for side, obj in objects.items()}
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    body_tree = world_bvh(bpy.data.objects[BODY], depsgraph)
    overlaps = {}
    for side, obj in objects.items():
        caruncle_tree = world_bvh(obj, depsgraph)
        eye_tree = world_bvh(bpy.data.objects[f"AevryndEye_{side}_Sclera_R249"], depsgraph)
        overlaps[side] = {"bodyVsCaruncle": len(body_tree.overlap(caruncle_tree)), "eyeVsCaruncle": len(eye_tree.overlap(caruncle_tree))}
    for view_name, location, target, lens in views:
        camera.location = location
        camera.data.lens = lens
        look_at(camera, target)
        scene.render.resolution_x = scene.render.resolution_y = 1000
        scene.render.filepath = str(RENDER_DIR / f"{label}-{view_name}.png")
        bpy.ops.render.render(write_still=True)
    metrics[label] = {"lateralTaper": taper, "maximumLocalDisplacementM": displacement, "triangleOverlaps": overlaps}

report = {
    "source": str(SOURCE), "renderDirectory": str(RENDER_DIR), "variants": metrics,
    "method": "Deform the 482-vertex owned ellipsoid into a nasal-base/globe-tip wedge by progressively tapering its lateral cross-section and shifting internal mass toward the nasal base.",
    "status": "VISUAL_AND_COLLISION_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R341_CARUNCLE_WEDGE=" + json.dumps(report, sort_keys=True))
