import json
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-fitted-upper-lip-r475.blend"
OUTPUT = ASSETS / "aevrynd-female-authoring-v249-mainline-fitted-wetline-r476.blend"
REPORT = ASSETS / "female-v249-mainline-fitted-wetline-r476.build-report.json"
REVIEW_DIR = ASSETS / "reviews/v249r476-fitted-wetline"
BODY = "AevryndFemaleBodyBaseV118"
WETLINE = "Mouth_WetLine"
CLEARANCE = 0.00055


def outward(normal):
    normal = normal.normalized()
    if normal.y > 0.0:
        normal.negate()
    return normal


def evaluated_geometry(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return points, faces


def tree(obj, depsgraph):
    points, faces = evaluated_geometry(obj, depsgraph)
    return BVHTree.FromPolygons(points, faces, all_triangles=False)


def fit_at_frame(scene, body, wetline, frame, margin=0.00006):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    body_tree = tree(body, depsgraph)
    points, _faces = evaluated_geometry(wetline, depsgraph)
    if len(points) != len(wetline.data.vertices):
        raise RuntimeError("wetline evaluated/base vertex count mismatch")
    inverse3 = wetline.matrix_world.inverted().to_3x3()
    moved = 0
    maximum = 0.0
    minimum_before = float("inf")
    for index, point in enumerate(points):
        hit = body_tree.find_nearest(point, 0.008)
        if hit is None or hit[1] is None:
            continue
        normal = outward(hit[1])
        signed = (point - hit[0]).dot(normal)
        minimum_before = min(minimum_before, signed)
        if signed >= CLEARANCE:
            continue
        translation = normal * (CLEARANCE - signed + margin)
        wetline.data.vertices[index].co += inverse3 @ translation
        moved += 1
        maximum = max(maximum, translation.length)
    wetline.data.update()
    bpy.context.view_layer.update()
    return {
        "frame": frame,
        "verticesMoved": moved,
        "minimumSignedBeforeMm": minimum_before * 1000.0,
        "maximumTranslationMm": maximum * 1000.0,
    }


def overlap_counts(scene, body, upper, wetline, frames=(1, 20)):
    result = {}
    for frame in frames:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        body_tree = tree(body, depsgraph)
        upper_tree = tree(upper, depsgraph)
        wetline_tree = tree(wetline, depsgraph)
        result[str(frame)] = {
            "bodyWetlineFaces": len(body_tree.overlap(wetline_tree)),
            "upperLipWetlineFaces": len(upper_tree.overlap(wetline_tree)),
            "bodyUpperLipFaces": len(body_tree.overlap(upper_tree)),
        }
    return result


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, camera, label, location, target, lens, size, frame=1):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.filepath = str(REVIEW_DIR / f"{label}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
body = bpy.data.objects[BODY]
upper = bpy.data.objects["Lip_Upper"]
wetline = bpy.data.objects[WETLINE]
wetline.hide_render = False
repairs = [fit_at_frame(scene, body, wetline, frame) for frame in (1, 20, 1, 20)]
material = wetline.active_material.copy()
material.name = "Aevrynd_MouthWetLine_Fitted_R476"
wetline.data.materials.clear()
wetline.data.materials.append(material)
shader = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
shader.inputs["Base Color"].default_value = (0.055, 0.006, 0.010, 1.0)
shader.inputs["Roughness"].default_value = 0.30
shader.inputs["Coat Weight"].default_value = 0.075
wetline["aevrynd_layer"] = "ANATOMY_MOUTH_WET_MARGIN_FITTED"
wetline["aevrynd_clearance_m"] = CLEARANCE
overlaps = overlap_counts(scene, body, upper, wetline)
scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene["aevrynd_character_revision"] = "v249r476"
scene.frame_set(1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

REVIEW_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
views = (
    ("01-face-front-f01", (0.0, -0.56, 1.585), (0.0, -0.060, 1.585), 108, (1100, 1100), 1),
    ("02-mouth-close-f01", (0.0, -0.405, 1.528), (0.0, -0.115, 1.528), 135, (1400, 800), 1),
    ("03-mouth-oblique-f01", (0.235, -0.405, 1.53), (0.0, -0.112, 1.528), 135, (1400, 800), 1),
    ("04-three-quarter-f01", (0.40, -0.57, 1.58), (0.0, -0.030, 1.56), 92, (1000, 1000), 1),
    ("05-face-front-f20", (0.0, -0.56, 1.585), (0.0, -0.060, 1.585), 108, (1100, 1100), 20),
)
for args in views:
    render(scene, camera, *args)
scene.frame_set(1)
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "wetline": {"vertices": len(wetline.data.vertices), "polygons": len(wetline.data.polygons), "clearanceMm": CLEARANCE * 1000.0},
    "repairs": repairs,
    "layerOverlapAudit": overlaps,
    "reviewDirectory": str(REVIEW_DIR),
    "status": "STRICT_VISUAL_AND_FULL_COLLISION_REVIEW_REQUIRED",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R476_FITTED_WETLINE=" + json.dumps(report, sort_keys=True))
