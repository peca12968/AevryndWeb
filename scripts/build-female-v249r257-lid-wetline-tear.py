import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-brow-microclusters-r256.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-lid-wetline-tear-r257.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-lid-wetline-tear-r257.build-report.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r257-lid-wetline-tear"
RIG = "AevryndFemaleRig"


def principled_material(name, color, roughness, specular=0.24, coat=0.0, coat_roughness=0.12):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    shader = next(node for node in mat.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Specular IOR Level"].default_value = specular
    shader.inputs["Coat Weight"].default_value = coat
    shader.inputs["Coat Roughness"].default_value = coat_roughness
    return mat


def tear_material():
    mat = principled_material("Aevrynd_TearFilm_R257", (0.72, 0.88, 0.94, 1.0), 0.025, 0.34, 0.16, 0.02)
    shader = next(node for node in mat.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    shader.inputs["IOR"].default_value = 1.336
    shader.inputs["Transmission Weight"].default_value = 0.64
    shader.inputs["Alpha"].default_value = 0.12
    if hasattr(mat, "surface_render_method"):
        mat.surface_render_method = "DITHERED"
    mat.use_transparency_overlap = False
    return mat


def bind_head(obj, rig):
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = world
    obj["aevrynd_binding"] = "rig.head"


def make_curve(name, paths, material, layer, bevel_depth, rig):
    data = bpy.data.curves.new(name + "Geometry", "CURVE")
    data.dimensions = "3D"
    data.resolution_u = 2
    data.bevel_depth = bevel_depth
    data.bevel_resolution = 3
    for coords in paths:
        spline = data.splines.new("NURBS")
        spline.points.add(len(coords) - 1)
        for point, co in zip(spline.points, coords):
            point.co = (*co, 1.0)
        spline.order_u = min(3, len(coords))
        spline.use_endpoint_u = True
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    data.materials.append(material)
    obj["aevrynd_layer"] = layer
    obj["aevrynd_revision"] = "v249r257"
    bind_head(obj, rig)
    return obj


def eye_center_and_front(side):
    sclera = bpy.data.objects[f"AevryndEye_{side}_Sclera_R249"]
    points = [sclera.matrix_world @ vertex.co for vertex in sclera.data.vertices]
    return Vector((
        sum(point.x for point in points) / len(points),
        sum(point.y for point in points) / len(points),
        sum(point.z for point in points) / len(points),
    )), min(point.y for point in points)


def eyelid_path(center, front, upper, count=41):
    path = []
    for index in range(count):
        u = -0.96 + 1.92 * index / (count - 1)
        edge = math.sqrt(max(0.0, 1.0 - u * u))
        x = center.x + 0.01025 * u
        z = center.z + (0.00525 * edge if upper else -0.00448 * edge)
        y = front - (0.00030 if upper else 0.00026)
        path.append((x, y, z))
    return path


def tear_path(center, front, count=31):
    path = []
    for index in range(count):
        u = -0.82 + 1.64 * index / (count - 1)
        edge = math.sqrt(max(0.0, 1.0 - u * u))
        x = center.x + 0.01025 * u
        z = center.z - 0.00448 * edge + 0.00020
        y = front - 0.00052
        path.append((x, y, z))
    return path


def caruncle(side, center, front, material, rig):
    sign = 1.0 if side == "L" else -1.0
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1.0, location=(center.x - sign * 0.00955, front - 0.00034, center.z - 0.00065))
    obj = bpy.context.object
    obj.name = f"AevryndEye_{side}_Caruncle_R257"
    obj.scale = (0.00115, 0.00046, 0.00082)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    obj.data.materials.append(material)
    obj["aevrynd_layer"] = f"eye.{side.lower()}.caruncle"
    obj["aevrynd_revision"] = "v249r257"
    bind_head(obj, rig)
    return obj


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, frame, name, location, target, lens, size):
    scene = bpy.context.scene
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
rig = bpy.data.objects[RIG]
margin_mat = principled_material("Aevrynd_LidMargin_R257", (0.19, 0.044, 0.028, 1.0), 0.34, 0.25, 0.07, 0.16)
tear_mat = tear_material()
caruncle_mat = principled_material("Aevrynd_Caruncle_R257", (0.31, 0.055, 0.041, 1.0), 0.28, 0.26, 0.12, 0.10)
created = []
metrics = {}
for side in ("L", "R"):
    center, front = eye_center_and_front(side)
    upper = make_curve(f"AevryndEye_{side}_UpperLidMargin_R257", [eyelid_path(center, front, True)], margin_mat, f"eye.{side.lower()}.upper_lid_margin", 0.00017, rig)
    lower = make_curve(f"AevryndEye_{side}_LowerLidMargin_R257", [eyelid_path(center, front, False)], margin_mat, f"eye.{side.lower()}.lower_lid_margin", 0.00015, rig)
    tear = make_curve(f"AevryndEye_{side}_TearMeniscus_R257", [tear_path(center, front)], tear_mat, f"eye.{side.lower()}.tear_meniscus", 0.00011, rig)
    inner = caruncle(side, center, front, caruncle_mat, rig)
    created.extend([upper.name, lower.name, tear.name, inner.name])
    metrics[side] = {
        "center": list(center),
        "scleraFrontY": front,
        "upperMarginPoints": len(upper.data.splines[0].points),
        "lowerMarginPoints": len(lower.data.splines[0].points),
        "tearMeniscusPoints": len(tear.data.splines[0].points),
        "frontLayerOrder": {"lidMarginOffsetM": 0.00030, "tearOffsetM": 0.00052},
    }

scene["aevrynd_mainline_revision"] = "v249r257-lid-wetline-tear"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "LID_WETLINE_TEAR_VISUAL_AND_COLLISION_REVIEW_PENDING"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
views = (
    (1, "01-face-front", (0.0, -1.02, 1.66), (0.0, 0.0, 1.625), 92, (1100, 1100)),
    (1, "02-face-three-quarter", (0.56, -0.89, 1.65), (0.0, 0.0, 1.615), 92, (1100, 1100)),
    (1, "03-eye-front", (0.0, -0.55, 1.616), (0.0, -0.13, 1.608), 105, (1200, 700)),
    (1, "04-eye-profile", (0.36, -0.49, 1.616), (0.034, -0.13, 1.608), 105, (1000, 800)),
    (20, "05-pose-face", (0.56, -0.89, 1.65), (0.0, 0.0, 1.615), 92, (1100, 1100)),
)
for values in views:
    render(camera, *values)
scene.frame_set(1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE), "output": str(OUTPUT), "createdLayers": created,
    "metrics": metrics, "renderDirectory": str(RENDER_DIR),
    "limitations": ["identity sculpt pending", "eyelid aperture corrective pending", "hair pending"],
    "status": "LID_WETLINE_TEAR_VISUAL_AND_COLLISION_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R257_LID_WETLINE_TEAR=" + json.dumps(report, sort_keys=True))
