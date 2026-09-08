import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-cc0-base-v1.blend"
OUTPUT = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v2.blend"
BUILD = ROOT / ".character-build" / "aevrynd-female-authoring-v2.glb"
TEXTURE_DIR = ROOT / "assets-source" / "aevrynd-character" / "textures"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "cc0-eyes-v2"


def set_input(shader, name, value):
    socket = shader.inputs.get(name)
    if socket is not None:
        socket.default_value = value


def material(name, color, roughness, metallic=0.0, transmission=0.0, alpha=1.0):
    result = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    result.use_nodes = True
    shader = result.node_tree.nodes.get("Principled BSDF")
    set_input(shader, "Base Color", color)
    set_input(shader, "Roughness", roughness)
    set_input(shader, "Metallic", metallic)
    set_input(shader, "IOR", 1.376)
    set_input(shader, "Transmission Weight", transmission)
    set_input(shader, "Alpha", alpha)
    if alpha < 1.0:
        result.surface_render_method = "DITHERED"
    return result


def make_iris_texture(path, size=512):
    image = bpy.data.images.new("Aevrynd_Iris_Hazel", width=size, height=size, alpha=True)
    pixels = [0.0] * (size * size * 4)
    for y in range(size):
        py = (y + 0.5) / size * 2.0 - 1.0
        for x in range(size):
            px = (x + 0.5) / size * 2.0 - 1.0
            radius = math.sqrt(px * px + py * py)
            angle = math.atan2(py, px)
            index = (y * size + x) * 4
            if radius > 1.0:
                pixels[index : index + 4] = (0.0, 0.0, 0.0, 0.0)
                continue
            fiber = (
                math.sin(angle * 73.0 + radius * 31.0)
                + 0.55 * math.sin(angle * 137.0 - radius * 47.0)
                + 0.25 * math.sin(angle * 233.0 + radius * 91.0)
            ) / 1.8
            radial = max(0.0, 1.0 - abs(radius - 0.58) * 1.7)
            limbal = 1.0 - 0.58 * max(0.0, (radius - 0.78) / 0.22)
            crypt = 0.12 * math.sin(angle * 19.0 + radius * 17.0) * max(0.0, 1.0 - radius)
            brightness = max(0.18, min(1.0, 0.5 + 0.22 * fiber + 0.2 * radial + crypt)) * limbal
            pixels[index : index + 4] = (
                0.18 * brightness,
                0.075 * brightness,
                0.025 * brightness,
                1.0,
            )
    image.pixels.foreach_set(pixels)
    image.filepath_raw = str(path)
    image.file_format = "PNG"
    image.save()
    return image


def textured_iris_material(image):
    result = material("Aevrynd_Eye_Iris", (1, 1, 1, 1), 0.42)
    nodes = result.node_tree.nodes
    links = result.node_tree.links
    texture = nodes.get("Aevrynd Iris Texture") or nodes.new("ShaderNodeTexImage")
    texture.name = "Aevrynd Iris Texture"
    texture.image = image
    shader = nodes.get("Principled BSDF")
    for link in list(shader.inputs["Base Color"].links):
        links.remove(link)
    links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    return result


def cornea_material():
    result = material("Aevrynd_Eye_Cornea", (0.93, 0.97, 1.0, 1.0), 0.035, transmission=1.0)
    nodes = result.node_tree.nodes
    links = result.node_tree.links
    shader = nodes.get("Principled BSDF")
    output = nodes.get("Material Output")
    for link in list(output.inputs["Surface"].links):
        links.remove(link)
    transparent = nodes.new("ShaderNodeBsdfTransparent")
    mix = nodes.new("ShaderNodeMixShader")
    mix.inputs[0].default_value = 0.13
    links.new(transparent.outputs[0], mix.inputs[1])
    links.new(shader.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], output.inputs["Surface"])
    result.surface_render_method = "DITHERED"
    return result


def make_disk(name, center, radius, material_value, y_offset, segments=96):
    vertices = [(0.0, 0.0, 0.0)]
    vertices.extend(
        (math.cos(i * math.tau / segments) * radius, 0.0, math.sin(i * math.tau / segments) * radius)
        for i in range(segments)
    )
    faces = [(0, i + 1, (i + 1) % segments + 1) for i in range(segments)]
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(vertices, [], faces)
    uv = mesh.uv_layers.new(name="UVMap")
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            vertex = mesh.vertices[mesh.loops[loop_index].vertex_index].co
            uv.data[loop_index].uv = (vertex.x / (radius * 2.0) + 0.5, vertex.z / (radius * 2.0) + 0.5)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = (center.x, center.y + y_offset, center.z)
    obj.data.materials.append(material_value)
    obj["aevrynd_role"] = name.split("_")[-1].lower()
    return obj


def make_ring(name, center, inner_radius, outer_radius, material_value, y_offset, segments=96):
    vertices = []
    for i in range(segments):
        angle = i * math.tau / segments
        direction = (math.cos(angle), math.sin(angle))
        vertices.append((direction[0] * inner_radius, 0.0, direction[1] * inner_radius))
        vertices.append((direction[0] * outer_radius, 0.0, direction[1] * outer_radius))
    faces = []
    for i in range(segments):
        current = i * 2
        following = ((i + 1) % segments) * 2
        faces.append((current, following, following + 1, current + 1))
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(vertices, [], faces)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = (center.x, center.y + y_offset, center.z)
    obj.data.materials.append(material_value)
    obj["aevrynd_role"] = name.split("_")[-1].lower()
    return obj


def make_sphere(name, center, radius, material_value, scale=(1.0, 1.0, 1.0)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=radius, location=center)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    obj.data.materials.append(material_value)
    obj["aevrynd_role"] = name.split("_")[-1].lower()
    return obj


def object_center(obj):
    return sum((obj.matrix_world @ Vector(corner) for corner in obj.bound_box), Vector()) / 8.0


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def export_runtime(objects, body):
    multires = next(m for m in body.modifiers if m.type == "MULTIRES")
    old = (multires.levels, multires.sculpt_levels, multires.render_levels)
    multires.levels = multires.sculpt_levels = multires.render_levels = 0
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.export_scene.gltf(
        filepath=str(BUILD),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_yup=True,
    )
    multires.levels, multires.sculpt_levels, multires.render_levels = old


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
bpy.context.preferences.filepaths.save_version = 0
TEXTURE_DIR.mkdir(parents=True, exist_ok=True)
RENDER_DIR.mkdir(parents=True, exist_ok=True)
BUILD.parent.mkdir(parents=True, exist_ok=True)

body = bpy.data.objects["AevryndFemaleBodyBase"]
old_eyes = [bpy.data.objects["AevryndFemaleEye.L"], bpy.data.objects["AevryndFemaleEye.R"]]
centers = [object_center(obj) for obj in old_eyes]
for obj in old_eyes:
    bpy.data.objects.remove(obj, do_unlink=True)

sclera_material = material("Aevrynd_Eye_Sclera", (0.73, 0.68, 0.62, 1.0), 0.32)
pupil_material = material("Aevrynd_Eye_Pupil", (0.004, 0.002, 0.001, 1.0), 0.2)
cornea_material = cornea_material()
limbal_material = material("Aevrynd_Eye_LimbalRing", (0.018, 0.006, 0.002, 1.0), 0.3)
iris_image = make_iris_texture(TEXTURE_DIR / "aevrynd-iris-hazel-v1.png")
iris_material = textured_iris_material(iris_image)

eye_objects = []
for side, center in zip(("L", "R"), centers):
    eye_objects.append(make_sphere(f"Eye_{side}_Sclera", center, 0.0121, sclera_material))
    eye_objects.append(make_disk(f"Eye_{side}_Iris", center, 0.00565, iris_material, -0.01222))
    eye_objects.append(make_disk(f"Eye_{side}_Pupil", center, 0.00215, pupil_material, -0.01234))
    eye_objects.append(make_sphere(f"Eye_{side}_Cornea", center + Vector((0, -0.00055, 0)), 0.01235, cornea_material))
    limbal = make_ring(f"Eye_{side}_LimbalRing", center, 0.00558, 0.00572, limbal_material, -0.01236)
    limbal.scale.z = 0.96
    eye_objects.append(limbal)

for obj in eye_objects:
    obj["aevrynd_source"] = "Aevrynd authored from CC0 female base eye placement"
    obj["aevrynd_source_license"] = "Aevrynd-owned geometry / CC0 placement reference"

bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
runtime_objects = [body] + eye_objects
export_runtime(runtime_objects, body)

camera = bpy.data.objects["Aevrynd Review Camera"]
camera.data.lens = 70
camera.location = (0, -0.78, 1.555)
look_at(camera, (0, 0, 1.535))
bpy.context.scene.render.resolution_x = 800
bpy.context.scene.render.resolution_y = 800
bpy.context.scene.render.resolution_percentage = 100
bpy.context.scene.render.filepath = str(RENDER_DIR / "female-eyes-face.png")
for obj in eye_objects:
    if obj["aevrynd_role"] == "cornea":
        obj.hide_render = True
bpy.ops.render.render(write_still=True)

report = {
    "state": "AUTHORING",
    "body": body.name,
    "eye_layers": [obj.name for obj in eye_objects],
    "eye_centers": [[round(value, 6) for value in center] for center in centers],
    "runtime_glb": str(BUILD),
}
print("AEVRYND_EYE_REPORT=" + json.dumps(report))
