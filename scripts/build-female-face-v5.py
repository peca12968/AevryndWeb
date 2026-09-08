import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v4.blend"
OUTPUT = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v5.blend"
BUILD = ROOT / ".character-build" / "aevrynd-female-authoring-v5.glb"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "face-v5"


def material(name, color, roughness, metallic=0.0):
    value = bpy.data.materials.new(name)
    value.use_nodes = True
    shader = value.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic
    if shader.inputs.get("Specular IOR Level"):
        shader.inputs["Specular IOR Level"].default_value = 0.42
    if shader.inputs.get("Coat Weight"):
        shader.inputs["Coat Weight"].default_value = 0.18
    return value


def tube_mesh(name, points, radius, material_value, sides=6):
    vertices = []
    faces = []
    for index, point in enumerate(points):
        previous = points[max(0, index - 1)]
        following = points[min(len(points) - 1, index + 1)]
        tangent = (following - previous).normalized()
        reference = Vector((0, 0, 1)) if abs(tangent.z) < 0.85 else Vector((0, 1, 0))
        axis_a = tangent.cross(reference).normalized()
        axis_b = tangent.cross(axis_a).normalized()
        end_fade = min(1.0, index / 4.0, (len(points) - 1 - index) / 4.0)
        width = radius * (0.18 + 0.82 * end_fade)
        for side in range(sides):
            angle = side * math.tau / sides
            vertices.append(point + axis_a * math.cos(angle) * width + axis_b * math.sin(angle) * width)
    for row in range(len(points) - 1):
        for side in range(sides):
            a = row * sides + side
            b = row * sides + (side + 1) % sides
            c = (row + 1) * sides + (side + 1) % sides
            d = (row + 1) * sides + side
            faces.append((a, b, c, d))
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(vertices, [], faces)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(material_value)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    return obj


def body_surface(body):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(depsgraph)
    return BVHTree.FromObject(evaluated, depsgraph), body.matrix_world, body.matrix_world.inverted()


def face_hit(surface, x, z):
    tree, matrix, inverse = surface
    origin = inverse @ Vector((x, -0.36, z))
    direction = (inverse.to_3x3() @ Vector((0, 1, 0))).normalized()
    location, normal, _, _ = tree.ray_cast(origin, direction, 0.7)
    if location is None:
        return None
    world_location = matrix @ location
    world_normal = (matrix.inverted().transposed().to_3x3() @ normal).normalized()
    return world_location, world_normal


def object_center(obj):
    return sum((obj.matrix_world @ Vector(corner) for corner in obj.bound_box), Vector()) / 8.0


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, location, target):
    camera.data.lens = 78
    camera.location = location
    look_at(camera, target)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 800
    scene.render.resolution_y = 800
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    for obj in bpy.data.objects:
        if obj.get("aevrynd_role") == "cornea":
            obj.hide_render = True
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
bpy.context.preferences.filepaths.save_version = 0
RENDER_DIR.mkdir(parents=True, exist_ok=True)
BUILD.parent.mkdir(parents=True, exist_ok=True)
body = bpy.data.objects["AevryndFemaleBodyBase"]

# The source iris was slightly undersized in neutral close-ups and produced a
# startled scleral ratio. Preserve the eye sockets and enlarge only the discs.
for side in ("L", "R"):
    for layer, scale in (("Iris", 1.075), ("Pupil", 1.035), ("LimbalRing", 1.075)):
        obj = bpy.data.objects[f"Eye_{side}_{layer}"]
        obj.scale.x *= scale
        obj.scale.z *= scale
        obj["aevrynd_eye_scale_revision"] = 5

iris_material = bpy.data.materials["Aevrynd_Eye_Iris"]
iris_nodes = iris_material.node_tree.nodes
iris_links = iris_material.node_tree.links
iris_shader = iris_nodes.get("Principled BSDF")
iris_source = iris_shader.inputs["Base Color"].links[0].from_socket
for link in list(iris_shader.inputs["Base Color"].links):
    iris_links.remove(link)
iris_tone = iris_nodes.new("ShaderNodeHueSaturation")
iris_tone.name = "Aevrynd Iris Tone Revision 5"
iris_tone.inputs["Saturation"].default_value = 1.12
iris_tone.inputs["Value"].default_value = 2.05
iris_links.new(iris_source, iris_tone.inputs["Color"])
iris_links.new(iris_tone.outputs["Color"], iris_shader.inputs["Base Color"])

tear_material = material("Aevrynd_TearFilm", (0.52, 0.34, 0.28, 1.0), 0.06)
tear_layers = []
for side in ("L", "R"):
    center = object_center(bpy.data.objects[f"Eye_{side}_Sclera"])
    points = []
    for index in range(45):
        t = index / 44
        angle = math.radians(202 + 136 * t)
        point = center + Vector((math.cos(angle) * 0.0099, -0.01230, math.sin(angle) * 0.0052))
        points.append(point)
    tear = tube_mesh(f"Eye_{side}_TearMeniscus", points, 0.00018, tear_material)
    tear["aevrynd_role"] = "tear_meniscus"
    tear["aevrynd_source"] = "Aevrynd authored facial wetline"
    tear_layers.append(tear)

mouth_material = material("Aevrynd_MouthCrease", (0.145, 0.045, 0.032, 1.0), 0.58)
surface = body_surface(body)
mouth_points = []
missed_mouth_samples = 0
for index in range(65):
    t = index / 64 * 2.0 - 1.0
    x = t * 0.0275
    z = 1.5355 + 0.00105 * math.cos(t * math.pi) - 0.00035 * abs(t)
    hit = face_hit(surface, x, z)
    if hit is None:
        missed_mouth_samples += 1
        continue
    point, normal = hit
    mouth_points.append(point + normal * 0.00022)
mouth = tube_mesh("Mouth_Crease", mouth_points, 0.00013, mouth_material)
mouth["aevrynd_role"] = "mouth_crease"
mouth["aevrynd_source"] = "Aevrynd authored from CC0 facial surface"

skin_material = body.data.materials[0]
skin_shader = skin_material.node_tree.nodes.get("Principled BSDF")
if skin_shader.inputs.get("Subsurface Weight"):
    skin_shader.inputs["Subsurface Weight"].default_value = 0.055
if skin_shader.inputs.get("Specular IOR Level"):
    skin_shader.inputs["Specular IOR Level"].default_value = 0.32
body["aevrynd_face_detail_revision"] = 5
body["aevrynd_missed_mouth_samples"] = missed_mouth_samples

bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

multires = next(modifier for modifier in body.modifiers if modifier.type == "MULTIRES")
old_multires = (multires.levels, multires.sculpt_levels, multires.render_levels)
multires.levels = multires.sculpt_levels = multires.render_levels = 0
bpy.ops.object.select_all(action="DESELECT")
runtime = [obj for obj in bpy.data.objects if obj.type == "MESH"]
for obj in runtime:
    obj.hide_render = False
    obj.select_set(True)
bpy.context.view_layer.objects.active = body
bpy.ops.export_scene.gltf(
    filepath=str(BUILD), export_format="GLB", use_selection=True,
    export_apply=True, export_yup=True, export_extras=True,
)
multires.levels, multires.sculpt_levels, multires.render_levels = old_multires

camera = bpy.data.objects["Aevrynd Review Camera"]
render(camera, "female-face-front", (0, -0.78, 1.56), (0, -0.01, 1.545))
render(camera, "female-face-three-quarter", (0.30, -0.68, 1.57), (0, -0.005, 1.54))

print(
    "AEVRYND_FACE_V5_REPORT="
    + json.dumps({
        "state": "AUTHORING",
        "tear_layers": [obj.name for obj in tear_layers],
        "mouth_layer": mouth.name,
        "missed_mouth_samples": missed_mouth_samples,
        "runtime_objects": len(runtime),
        "runtime_glb": str(BUILD),
    })
)
