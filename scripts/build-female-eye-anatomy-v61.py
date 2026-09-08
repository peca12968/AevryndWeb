import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v57.blend"
OUTPUT = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v61.blend"
TEXTURES = ROOT / "assets-source" / "aevrynd-character" / "textures"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "eye-anatomy-v61"


def clamp01(value):
    return max(0.0, min(1.0, value))


def gaussian(value, center, spread):
    return math.exp(-0.5 * ((value - center) / spread) ** 2)


def smoothstep(value):
    value = clamp01(value)
    return value * value * (3.0 - 2.0 * value)


def eye_curves(x, center_x):
    t = (x - center_x) / 0.01735
    envelope = math.sqrt(max(0.0, 1.0 - min(1.0, abs(t)) ** 2))
    asymmetry = (-0.00012 if center_x > 0.0 else 0.00010) * t
    return t, 1.60735 + 0.00505 * envelope + asymmetry, 1.60735 - 0.00395 * envelope + asymmetry * 0.55


def sculpt_integrated_lids(body):
    inverse = body.matrix_world.inverted()
    normal_matrix = body.matrix_world.to_3x3()
    changed = 0
    maximum = 0.0
    for vertex in body.data.vertices:
        point = body.matrix_world @ vertex.co
        if point.y > -0.100 or not (1.597 < point.z < 1.619):
            continue
        center_x = 0.0345 if point.x >= 0.0 else -0.0345
        t, upper, lower = eye_curves(point.x, center_x)
        if abs(t) >= 1.02:
            continue
        normal = (normal_matrix @ vertex.normal).normalized()
        gate = clamp01((-point.y - 0.1015) / 0.0125)
        gate *= clamp01((-normal.y - 0.04) / 0.48)
        gate *= smoothstep((1.02 - abs(t)) / 0.20)
        if gate <= 1e-5:
            continue
        side_scale = 1.0 if center_x > 0.0 else 0.94
        roll = (
            0.00066 * gaussian(point.z, upper + 0.00018, 0.00078)
            + 0.00049 * gaussian(point.z, lower - 0.00010, 0.00082)
        )
        crease = (
            0.00027 * gaussian(point.z, upper + 0.00205, 0.00074)
            + 0.00014 * gaussian(point.z, lower - 0.00155, 0.00078)
        )
        y_delta = max(-0.00070, min(0.00070, (-roll + crease) * gate * side_scale))
        if abs(y_delta) <= 1e-7:
            continue
        target = point + Vector((0.0, y_delta, 0.0))
        vertex.co = inverse @ target
        changed += 1
        maximum = max(maximum, abs(y_delta))
    body.data.update()
    body["aevrynd_eye_revision"] = 61
    body["aevrynd_palpebral_mode"] = "body_integrated"
    body["aevrynd_palpebral_changed_vertices"] = changed
    body["aevrynd_palpebral_max_delta_m"] = maximum
    return {"changed_vertices": changed, "maximum_delta_m": maximum}


def evaluated_surface(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    result = BVHTree.FromPolygons(points, faces, all_triangles=False)
    evaluated.to_mesh_clear()
    return result


def outward(normal):
    normal = normal.normalized()
    if normal.y > 0.0:
        normal.negate()
    return normal


def reproject_attachment(tree, obj, clearance):
    inverse = obj.matrix_world.inverted()
    adjusted = 0
    maximum = 0.0
    for vertex in obj.data.vertices:
        point = obj.matrix_world @ vertex.co
        location, normal, _, _ = tree.find_nearest(point)
        if location is None:
            continue
        normal = outward(normal)
        signed = (point - location).dot(normal)
        if signed >= clearance:
            continue
        target = location + normal * clearance
        vertex.co = inverse @ target
        adjusted += 1
        maximum = max(maximum, (target - point).length)
    obj.data.update()
    obj["aevrynd_eye_revision"] = 61
    obj["aevrynd_surface_clearance_m"] = clearance
    return {"adjusted_vertices": adjusted, "maximum_delta_m": maximum, "clearance_m": clearance}


def reproject_lashes(tree, obj, clearance):
    inverse = obj.matrix_world.inverted()
    count = int(obj.get("aevrynd_fiber_count", 0))
    if count <= 0 or len(obj.data.vertices) % count:
        raise RuntimeError(f"Unexpected lash topology: {obj.name}")
    stride = len(obj.data.vertices) // count
    adjusted = 0
    maximum = 0.0
    for fiber in range(count):
        start = fiber * stride
        root = sum((obj.matrix_world @ obj.data.vertices[start + index].co for index in range(3)), Vector()) / 3.0
        location, normal, _, _ = tree.find_nearest(root)
        if location is None:
            continue
        normal = outward(normal)
        signed = (root - location).dot(normal)
        if signed >= clearance:
            continue
        translation = normal * (clearance - signed)
        for index in range(start, start + stride):
            point = obj.matrix_world @ obj.data.vertices[index].co
            obj.data.vertices[index].co = inverse @ (point + translation)
        adjusted += stride
        maximum = max(maximum, translation.length)
    obj.data.update()
    obj["aevrynd_eye_revision"] = 61
    obj["aevrynd_root_clearance_m"] = clearance
    return {"adjusted_vertices": adjusted, "maximum_delta_m": maximum, "clearance_m": clearance}


def shader(material):
    return next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")


def replace_image(material_name, node_name, path):
    material = bpy.data.materials[material_name]
    node = material.node_tree.nodes[node_name]
    image = bpy.data.images.load(str(path), check_existing=False)
    image.name = path.stem
    image.colorspace_settings.name = "sRGB"
    node.image = image
    material["aevrynd_eye_revision"] = 61
    material["aevrynd_texture_source"] = path.name


def tune_materials():
    replace_image("Aevrynd_Eye_Sclera", "Aevrynd Sclera BaseColor", TEXTURES / "aevrynd-sclera-basecolor-v61.png")
    replace_image("Aevrynd_Eye_Iris", "Aevrynd Iris Texture", TEXTURES / "aevrynd-iris-hazel-v61.png")

    sclera = shader(bpy.data.materials["Aevrynd_Eye_Sclera"])
    sclera.inputs["Roughness"].default_value = 0.29
    sclera.inputs["Specular IOR Level"].default_value = 0.28
    sclera.inputs["Subsurface Weight"].default_value = 0.032
    sclera.inputs["Subsurface Scale"].default_value = 0.0012
    sclera.inputs["Coat Weight"].default_value = 0.08
    sclera.inputs["Coat Roughness"].default_value = 0.11

    iris_material = bpy.data.materials["Aevrynd_Eye_Iris"]
    iris = shader(iris_material)
    iris.inputs["Roughness"].default_value = 0.46
    iris.inputs["Specular IOR Level"].default_value = 0.16
    tone = iris_material.node_tree.nodes["Aevrynd Iris Tone Revision 5"]
    tone.inputs["Saturation"].default_value = 0.96
    tone.inputs["Value"].default_value = 1.38

    limbal = shader(bpy.data.materials["Aevrynd_Eye_LimbalRing"])
    limbal.inputs["Base Color"].default_value = (0.012, 0.018, 0.008, 1.0)
    limbal.inputs["Roughness"].default_value = 0.42

    cornea_material = bpy.data.materials["Aevrynd_Eye_Cornea"]
    cornea = shader(cornea_material)
    cornea.inputs["Roughness"].default_value = 0.035
    cornea.inputs["IOR"].default_value = 1.376
    cornea_material.node_tree.nodes["Mix Shader"].inputs[0].default_value = 0.17

    tear_material = bpy.data.materials["Aevrynd_TearFilm_v37"]
    tear = shader(tear_material)
    tear.inputs["Base Color"].default_value = (0.28, 0.075, 0.055, 1.0)
    tear.inputs["Roughness"].default_value = 0.11
    tear.inputs["Specular IOR Level"].default_value = 0.34
    tear.inputs["Coat Weight"].default_value = 0.30
    tear.inputs["Coat Roughness"].default_value = 0.08
    tear.inputs["Alpha"].default_value = 0.34
    tear_material.surface_render_method = "DITHERED"

    caruncle = shader(bpy.data.materials["Aevrynd_Caruncle_v37"])
    caruncle.inputs["Base Color"].default_value = (0.18, 0.040, 0.032, 1.0)
    caruncle.inputs["Roughness"].default_value = 0.48
    caruncle.inputs["Specular IOR Level"].default_value = 0.18
    caruncle.inputs["Subsurface Weight"].default_value = 0.045
    caruncle.inputs["Subsurface Scale"].default_value = 0.0007
    return {
        "sclera_sss": 0.032,
        "iris_value": 1.38,
        "cornea_mix": 0.17,
        "tear_alpha": 0.34,
    }


def reshape_eye_layers():
    report = {}

    def translate_world(obj, delta):
        inverse = obj.matrix_world.inverted()
        for vertex in obj.data.vertices:
            vertex.co = inverse @ (obj.matrix_world @ vertex.co + delta)
        obj.data.update()

    for side in ("L", "R"):
        cornea = bpy.data.objects[f"Eye_{side}_Cornea"]
        center = sum((cornea.matrix_world @ Vector(corner) for corner in cornea.bound_box), Vector()) / 8.0
        inverse = cornea.matrix_world.inverted()
        maximum = 0.0
        for vertex in cornea.data.vertices:
            point = cornea.matrix_world @ vertex.co
            frontness = clamp01((center.y - point.y) / 0.01235)
            delta = 0.00155 * frontness * frontness * smoothstep(frontness)
            point.y -= delta
            vertex.co = inverse @ point
            maximum = max(maximum, delta)
        cornea.data.update()
        cornea["aevrynd_eye_revision"] = 61
        cornea["aevrynd_cornea_apex_delta_m"] = maximum
        report[cornea.name] = {"apex_delta_m": maximum}

        catchlight = bpy.data.objects[f"Eye_{side}_Catchlight"]
        translate_world(catchlight, Vector((0.0, -0.00155, 0.0)))
        catchlight.scale.x *= 0.78
        catchlight.scale.z *= 0.58
        catchlight["aevrynd_eye_revision"] = 61

        caruncle = bpy.data.objects[f"Eye_{side}_Caruncle"]
        points = [caruncle.matrix_world @ vertex.co for vertex in caruncle.data.vertices]
        center = sum(points, Vector()) / len(points)
        inverse = caruncle.matrix_world.inverted()
        for vertex in caruncle.data.vertices:
            point = caruncle.matrix_world @ vertex.co
            point.x = center.x + (point.x - center.x) * 0.76
            point.z = center.z + (point.z - center.z) * 0.72
            vertex.co = inverse @ point
        caruncle.data.update()
        caruncle["aevrynd_eye_revision"] = 61
        caruncle["aevrynd_scale_x"] = 0.76
        caruncle["aevrynd_scale_z"] = 0.72
    return report


def retire_flat_overlays():
    retired = []
    for side in ("L", "R"):
        for kind in ("IrisFibers", "LimbalRing", "UpperFold"):
            name = f"Eye_{side}_{kind}"
            obj = bpy.data.objects.get(name)
            if obj:
                obj.hide_render = True
                obj.hide_set(True)
                obj["aevrynd_retired_revision"] = 61
                obj["aevrynd_runtime_exclude"] = True
                retired.append(name)
    return retired


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, location, target, lens, width=1400, height=700):
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
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
bpy.context.preferences.filepaths.save_version = 0
bpy.context.scene.frame_set(1)
RENDER_DIR.mkdir(parents=True, exist_ok=True)
body = bpy.data.objects["AevryndFemaleBodyBase"]
lid_report = sculpt_integrated_lids(body)
material_report = tune_materials()
geometry_report = reshape_eye_layers()
retired = retire_flat_overlays()

body_tree = evaluated_surface(body)
clearance_report = {}
for side in ("L", "R"):
    for kind, clearance in (("TearMeniscus", 0.00030), ("Caruncle", 0.00039)):
        name = f"Eye_{side}_{kind}"
        clearance_report[name] = reproject_attachment(body_tree, bpy.data.objects[name], clearance)
    for kind, clearance in (("UpperLashes", 0.00056), ("LowerLashes", 0.00072)):
        name = f"Eye_{side}_{kind}"
        clearance_report[name] = reproject_lashes(body_tree, bpy.data.objects[name], clearance)

# Corneal bulging changes the anterior eye envelope.  Re-establish a small
# nonzero gap for every mobile wet/keratin layer after the body clearance pass.
for side in ("L", "R"):
    cornea_tree = evaluated_surface(bpy.data.objects[f"Eye_{side}_Cornea"])
    for kind in ("TearMeniscus", "Caruncle"):
        name = f"Eye_{side}_{kind}"
        obj = bpy.data.objects[name]
        body_clearance = 0.00030 if kind == "TearMeniscus" else 0.00039
        cornea_report = reproject_attachment(cornea_tree, obj, 0.00010)
        obj["aevrynd_surface_clearance_m"] = body_clearance
        obj["aevrynd_cornea_clearance_m"] = 0.00010
        clearance_report[name]["cornea"] = cornea_report
    for kind in ("UpperLashes", "LowerLashes"):
        name = f"Eye_{side}_{kind}"
        obj = bpy.data.objects[name]
        body_clearance = 0.00056 if kind == "UpperLashes" else 0.00072
        cornea_report = reproject_lashes(cornea_tree, obj, 0.00010)
        obj["aevrynd_root_clearance_m"] = body_clearance
        obj["aevrynd_cornea_clearance_m"] = 0.00010
        clearance_report[name]["cornea"] = cornea_report

bpy.context.scene["aevrynd_eye_revision"] = 61
bpy.context.scene["aevrynd_eye_method"] = "body_integrated_lids_pbr_layered_eye"
bpy.context.scene["aevrynd_release_state"] = "AUTHORING"
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

camera = bpy.data.objects["Aevrynd Review Camera"]
render(camera, "eyes-front-close", (0.0, -0.42, 1.608), (0.0, -0.09, 1.607), 122)
render(camera, "eye-left-three-quarter", (0.14, -0.39, 1.610), (0.0345, -0.095, 1.607), 132)
render(camera, "eye-right-three-quarter", (-0.14, -0.39, 1.610), (-0.0345, -0.095, 1.607), 132)
render(camera, "face-front", (0.0, -0.69, 1.61), (0.0, -0.01, 1.59), 92, 1000, 1000)
render(camera, "face-three-quarter", (0.29, -0.62, 1.63), (0.0, -0.005, 1.59), 92, 1000, 1000)
render(camera, "face-left", (-0.62, -0.05, 1.57), (0.0, 0.0, 1.545), 96, 1000, 1000)
render(camera, "face-right", (0.62, -0.05, 1.57), (0.0, 0.0, 1.545), 96, 1000, 1000)

print("AEVRYND_EYE_ANATOMY_V61=" + json.dumps({
    "state": "AUTHORING",
    "integrated_lids": lid_report,
    "materials": material_report,
    "geometry": geometry_report,
    "retired_overlays": retired,
    "clearance": clearance_report,
}))
