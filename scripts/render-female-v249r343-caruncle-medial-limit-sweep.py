import json
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-integrated-caruncle-r340.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-caruncle-medial-limit-r343.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r343-caruncle-medial-limit-sweep"
BODY = "AevryndFemaleBody_CC0_R249"
TAPER = 0.25
VARIANTS = (("a-plus-1p00mm", 0.00100), ("b-plus-1p25mm", 0.00125), ("c-plus-1p50mm", 0.00150), ("d-plus-1p75mm", 0.00175))


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


def wedge(side, obj):
    sign = 1.0 if side == "L" else -1.0
    for vertex in obj.data.vertices:
        source = vertex.co.copy()
        u = max(-1.0, min(1.0, sign * source.x / 0.00058))
        cross = 1.0 - TAPER * (u + 1.0) * 0.5
        vertex.co.y *= cross
        vertex.co.z *= cross
        vertex.co.x -= sign * TAPER * 0.00008 * (1.0 - u * u)
    obj.data.update()


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
objects = {side: bpy.data.objects[f"AevryndEye_{side}_Caruncle_R258"] for side in ("L", "R")}
matrices = {}
for side, obj in objects.items():
    obj.data = obj.data.copy()
    wedge(side, obj)
    matrices[side] = obj.matrix_world.copy()

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
for label, additional in VARIANTS:
    for side, obj in objects.items():
        obj.matrix_world = matrices[side].copy()
        obj.matrix_world.translation.x += -additional if side == "L" else additional
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
    metrics[label] = {"additionalMedialShiftM": additional, "totalMedialShiftFromR337M": 0.00035 + additional, "triangleOverlaps": overlaps}

report = {
    "source": str(SOURCE), "renderDirectory": str(RENDER_DIR), "variants": metrics,
    "fixedShape": {"worldWidthM": 0.001855999, "lateralTaper": TAPER},
    "method": "Hold the selected small soft wedge and move it toward the nasal canthus until visual integration or the first body/eye overlap.",
    "status": "VISUAL_AND_COLLISION_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R343_CARUNCLE_MEDIAL_LIMIT=" + json.dumps(report, sort_keys=True))
