import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v51.blend"
OUTPUT = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v52.blend"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "facial-planes-v52"


def gaussian(value, center, spread):
    return math.exp(-0.5 * ((value - center) / spread) ** 2)


def clamp01(value):
    return max(0.0, min(1.0, value))


def segment_distance(px, pz, ax, az, bx, bz):
    abx, abz = bx - ax, bz - az
    length_squared = abx * abx + abz * abz
    t = clamp01(((px - ax) * abx + (pz - az) * abz) / length_squared)
    qx, qz = ax + abx * t, az + abz * t
    return math.hypot(px - qx, pz - qz)


def reshape_facial_planes(body):
    inverse = body.matrix_world.inverted()
    changed = 0
    maximum = 0.0
    components = {name: 0.0 for name in (
        "supraorbital", "infraorbital", "tear_trough", "zygoma", "temple",
        "buccal", "nasolabial", "alar_groove", "philtrum", "mental_sulcus",
        "chin_pad", "mandible_taper",
    )}
    for vertex in body.data.vertices:
        point = body.matrix_world @ vertex.co
        x_abs = abs(point.x)
        if point.y > -0.045 or x_abs > 0.105 or not (1.455 < point.z < 1.650):
            continue

        front = clamp01((-point.y - 0.055) / 0.075)
        side = 1.0 if point.x >= 0.0 else -1.0
        eye_center_x = 0.0345 if point.x >= 0.0 else -0.0345
        eye_dx = point.x - eye_center_x
        eye_aperture = math.exp(-0.5 * ((eye_dx / 0.0215) ** 2 + ((point.z - 1.6075) / 0.0090) ** 2))
        eye_guard = 1.0 - 0.985 * eye_aperture
        mouth_guard_field = math.exp(-0.5 * ((point.x / 0.039) ** 2 + ((point.z - 1.5345) / 0.0145) ** 2))
        mouth_guard = 1.0 - 0.985 * mouth_guard_field

        supraorbital = gaussian(x_abs, 0.036, 0.027) * gaussian(point.z, 1.630, 0.011) * front
        infraorbital = gaussian(x_abs, 0.038, 0.023) * gaussian(point.z, 1.592, 0.0070) * front * eye_guard
        tear_trough = gaussian(x_abs, 0.039, 0.020) * gaussian(point.z, 1.579, 0.0075) * front
        zygoma = gaussian(x_abs, 0.057, 0.021) * gaussian(point.z, 1.565, 0.025) * front
        temple = gaussian(x_abs, 0.083, 0.016) * gaussian(point.z, 1.600, 0.034) * front
        buccal = gaussian(x_abs, 0.057, 0.023) * gaussian(point.z, 1.522, 0.025) * front

        fold_distance = segment_distance(x_abs, point.z, 0.024, 1.558, 0.043, 1.520)
        nasolabial = math.exp(-0.5 * (fold_distance / 0.0045) ** 2) * front
        nasolabial *= clamp01((x_abs - 0.016) / 0.014) * mouth_guard
        alar_groove = gaussian(x_abs, 0.028, 0.0048) * gaussian(point.z, 1.555, 0.011) * front
        philtrum = gaussian(point.x, 0.0, 0.0048) * gaussian(point.z, 1.550, 0.0090) * front * mouth_guard
        mental = gaussian(x_abs, 0.020, 0.026) * gaussian(point.z, 1.507, 0.0065) * front * mouth_guard
        chin = gaussian(x_abs, 0.019, 0.027) * gaussian(point.z, 1.482, 0.016) * front
        mandible = gaussian(x_abs, 0.068, 0.028) * gaussian(point.z, 1.480, 0.025) * clamp01((0.0 - point.y) / 0.080)

        # Negative Y is forward in the authoring scene.
        y_delta = (
            -0.00048 * supraorbital * eye_guard
            -0.00062 * infraorbital
            +0.00078 * tear_trough
            -0.00155 * zygoma
            +0.00062 * temple
            +0.00112 * buccal
            +0.00062 * nasolabial
            +0.00052 * alar_groove
            +0.00040 * philtrum
            +0.00062 * mental
            -0.00088 * chin
        )
        x_delta = side * (
            +0.00058 * zygoma
            -0.00082 * mandible
        )
        z_delta = (
            +0.00018 * zygoma
            -0.00028 * tear_trough
            +0.00032 * mandible
        )

        # Retain a restrained human asymmetry in the left cheek and right jaw.
        asymmetry = gaussian(x_abs, 0.055, 0.026) * gaussian(point.z, 1.545, 0.043) * front
        y_delta += (-0.00016 if point.x >= 0.0 else 0.00009) * asymmetry
        x_delta += side * (0.00006 if point.x >= 0.0 else -0.00004) * asymmetry

        target = point + Vector((x_delta, y_delta, z_delta))
        delta = (target - point).length
        if delta <= 1e-7:
            continue
        vertex.co = inverse @ target
        changed += 1
        maximum = max(maximum, delta)
        values = {
            "supraorbital": 0.00048 * supraorbital * eye_guard,
            "infraorbital": 0.00062 * infraorbital,
            "tear_trough": 0.00078 * tear_trough,
            "zygoma": 0.00155 * zygoma,
            "temple": 0.00062 * temple,
            "buccal": 0.00112 * buccal,
            "nasolabial": 0.00062 * nasolabial,
            "alar_groove": 0.00052 * alar_groove,
            "philtrum": 0.00040 * philtrum,
            "mental_sulcus": 0.00062 * mental,
            "chin_pad": 0.00088 * chin,
            "mandible_taper": 0.00082 * mandible,
        }
        for name, value in values.items():
            components[name] = max(components[name], value)

    body.data.update()
    body["aevrynd_face_revision"] = 52
    body["aevrynd_facial_plane_vertices"] = changed
    body["aevrynd_facial_plane_max_delta_m"] = maximum
    return changed, maximum, components


def evaluated_surface(body):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    tree = BVHTree.FromPolygons(points, faces, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


def enforce_attachment_clearance(body, names, clearance=0.00045):
    tree = evaluated_surface(body)
    reports = {}
    for name in names:
        obj = bpy.data.objects[name]
        inverse = obj.matrix_world.inverted()
        adjusted = 0
        maximum = 0.0
        for vertex in obj.data.vertices:
            point = obj.matrix_world @ vertex.co
            location, normal, _, _ = tree.find_nearest(point)
            if location is None:
                continue
            if normal.y > 0.0:
                normal.negate()
            signed = (point - location).dot(normal)
            if signed >= clearance:
                continue
            target = location + normal.normalized() * clearance
            vertex.co = inverse @ target
            adjusted += 1
            maximum = max(maximum, (target - point).length)
        obj.data.update()
        obj["aevrynd_face_revision"] = 52
        obj["aevrynd_surface_clearance_m"] = clearance
        obj["aevrynd_clearance_adjusted_vertices"] = adjusted
        obj["aevrynd_clearance_max_delta_m"] = maximum
        reports[name] = {"adjusted_vertices": adjusted, "maximum_delta_m": maximum}
    return reports


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, location, target, lens=96, width=1000, height=1000):
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    camera.data.lens = lens
    camera.location = location
    look_at(camera, target)
    for obj in bpy.data.objects:
        if obj.get("aevrynd_role") == "cornea":
            obj.hide_render = False
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
bpy.context.preferences.filepaths.save_version = 0
bpy.context.scene.frame_set(1)
RENDER_DIR.mkdir(parents=True, exist_ok=True)
body = bpy.data.objects["AevryndFemaleBodyBase"]
changed, maximum, components = reshape_facial_planes(body)
attachments = enforce_attachment_clearance(body, (
    "Brow_L_Density", "Brow_R_Density",
    "Eye_L_UpperFold", "Eye_R_UpperFold",
    "Eye_L_TearMeniscus", "Eye_R_TearMeniscus",
))
bpy.context.scene["aevrynd_face_revision"] = 52
bpy.context.scene["aevrynd_release_state"] = "AUTHORING"
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

camera = bpy.data.objects["Aevrynd Review Camera"]
render(camera, "female-face-front", (0.0, -0.72, 1.575), (0.0, -0.005, 1.555), 96)
render(camera, "female-face-three-quarter", (0.28, -0.64, 1.58), (0.0, 0.0, 1.55), 96)
render(camera, "female-face-left", (-0.62, -0.05, 1.57), (0.0, 0.0, 1.545), 96)
render(camera, "female-face-right", (0.62, -0.05, 1.57), (0.0, 0.0, 1.545), 96)
render(camera, "female-face-close", (0.0, -0.50, 1.565), (0.0, -0.075, 1.56), 108)
print("AEVRYND_FACIAL_PLANES_V52=" + json.dumps({
    "state": "AUTHORING",
    "changed_vertices": changed,
    "maximum_delta_m": maximum,
    "component_maxima_m": components,
    "attachment_clearance": attachments,
}))
