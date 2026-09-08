import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE_COLLECTION = "Body Female - Realistic"
BUILD_DIR = ROOT / ".character-build"
SOURCE_DIR = ROOT / "assets-source" / "aevrynd-character"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "cc0-base"


def set_input(shader, name, value):
    socket = shader.inputs.get(name)
    if socket is not None:
        socket.default_value = value


def make_material(name, color, roughness, subsurface=0.0):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    set_input(shader, "Base Color", color)
    set_input(shader, "Roughness", roughness)
    set_input(shader, "IOR", 1.4)
    set_input(shader, "Subsurface Weight", subsurface)
    return material


def keep_collection(name):
    collection = bpy.data.collections[name]
    keep = set(collection.all_objects)
    for obj in list(bpy.data.objects):
        if obj not in keep:
            bpy.data.objects.remove(obj, do_unlink=True)
    for other in list(bpy.data.collections):
        if other != collection and other.users == 0:
            bpy.data.collections.remove(other)
    return collection


def world_bounds(objects):
    points = [obj.matrix_world @ Vector(corner) for obj in objects for corner in obj.bound_box]
    low = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    high = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    return low, high


def normalize_scale(objects, target_height=1.72):
    low, high = world_bounds(objects)
    scale = target_height / (high.z - low.z)
    center = (low + high) * 0.5
    roots = [obj for obj in objects if obj.parent not in objects]
    for obj in roots:
        obj.location.x = (obj.location.x - center.x) * scale
        obj.location.y = (obj.location.y - center.y) * scale
        obj.location.z = (obj.location.z - low.z) * scale
        obj.scale *= scale
    bpy.context.view_layer.update()


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def add_area(name, location, energy, size, color):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    data.color = color
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    look_at(obj, (0, 0, 1.05))


def prepare_scene(body, eyes):
    skin = make_material("Aevrynd_Skin_Clay", (0.47, 0.22, 0.16, 1.0), 0.56, 0.08)
    eye = make_material("Aevrynd_Eye_Clay", (0.72, 0.77, 0.78, 1.0), 0.2)
    body.data.materials.clear()
    body.data.materials.append(skin)
    for obj in eyes:
        obj.data.materials.clear()
        obj.data.materials.append(eye)

    world = bpy.context.scene.world or bpy.data.worlds.new("Aevrynd World")
    bpy.context.scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.025, 0.035, 0.05, 1.0)
    background.inputs["Strength"].default_value = 0.35

    add_area("Key", (-2.2, -3.0, 2.8), 380, 2.0, (1.0, 0.78, 0.66))
    add_area("Fill", (2.4, -1.8, 1.7), 220, 1.7, (0.55, 0.7, 1.0))
    add_area("Rim", (0.4, 2.5, 2.5), 480, 1.5, (0.75, 0.85, 1.0))

    camera_data = bpy.data.cameras.new("Aevrynd Review Camera")
    camera = bpy.data.objects.new("Aevrynd Review Camera", camera_data)
    bpy.context.scene.collection.objects.link(camera)
    bpy.context.scene.camera = camera
    camera_data.lens = 60

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False
    scene.render.resolution_percentage = 100
    scene.render.image_settings.color_depth = "8"
    scene.view_settings.look = "Medium High Contrast"
    scene.view_settings.exposure = -1.0
    return camera


def render(camera, name, location, target, resolution):
    camera.location = location
    look_at(camera, target)
    scene = bpy.context.scene
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)


def export_runtime(objects, body):
    multires = next((m for m in body.modifiers if m.type == "MULTIRES"), None)
    old_levels = None
    if multires:
        old_levels = (multires.levels, multires.sculpt_levels, multires.render_levels)
        multires.levels = 0
        multires.sculpt_levels = 0
        multires.render_levels = 0
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.export_scene.gltf(
        filepath=str(BUILD_DIR / "aevrynd-female-cc0-base-v1.glb"),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_yup=True,
    )
    if multires and old_levels:
        multires.levels, multires.sculpt_levels, multires.render_levels = old_levels


BUILD_DIR.mkdir(parents=True, exist_ok=True)
SOURCE_DIR.mkdir(parents=True, exist_ok=True)
RENDER_DIR.mkdir(parents=True, exist_ok=True)
bpy.context.preferences.filepaths.save_version = 0

collection = keep_collection(SOURCE_COLLECTION)
objects = list(collection.all_objects)
body = bpy.data.objects["GEO-body_female_realistic"]
eyes = [
    bpy.data.objects["GEO-body_female_realistic.eye.L"],
    bpy.data.objects["GEO-body_female_realistic.eye.R"],
]
body.name = "AevryndFemaleBodyBase"
eyes[0].name = "AevryndFemaleEye.L"
eyes[1].name = "AevryndFemaleEye.R"
collection.name = "Aevrynd Female CC0 Base"
normalize_scale(objects)

for obj in objects:
    obj["aevrynd_source"] = "Blender Human Base Meshes 1.4.1"
    obj["aevrynd_source_license"] = "CC0-1.0"
    obj["aevrynd_role"] = "authoring-base"

camera = prepare_scene(body, eyes)
bpy.context.scene["aevrynd_source_sha256"] = "811F43ACCBB31A88266D932F8F5563B2D13586FCA0BA2693AAD1F5FE582B3515"
bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE_DIR / "aevrynd-female-cc0-base-v1.blend"))
export_runtime(objects, body)

render(camera, "female-base-front", (0, -4.25, 0.91), (0, 0, 0.87), (560, 840))
render(camera, "female-base-side", (4.25, 0, 0.91), (0, 0, 0.87), (560, 840))
render(camera, "female-base-back", (0, 4.25, 0.91), (0, 0, 0.87), (560, 840))
render(camera, "female-base-face", (0, -0.82, 1.56), (0, 0, 1.54), (720, 720))

low, high = world_bounds(objects)
report = {
    "source": "Blender Human Base Meshes 1.4.1 / Body Female - Realistic",
    "license": "CC0-1.0",
    "height_m": high.z - low.z,
    "base_vertices": len(body.data.vertices),
    "base_polygons": len(body.data.polygons),
    "uv_layers": [layer.name for layer in body.data.uv_layers],
    "multires_levels": next(m.total_levels for m in body.modifiers if m.type == "MULTIRES"),
    "runtime_glb": str(BUILD_DIR / "aevrynd-female-cc0-base-v1.glb"),
}
print("AEVRYND_BASE_REPORT=" + json.dumps(report))
