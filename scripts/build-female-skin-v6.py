import json
import math
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v5.blend"
OUTPUT = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v6.blend"
BUILD = ROOT / ".character-build" / "aevrynd-female-authoring-v6.glb"
TEXTURE_DIR = ROOT / "assets-source" / "aevrynd-character" / "textures"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "skin-v6"


def periodic_noise(x, y):
    return (
        np.sin(x * math.tau * 7.0 + np.sin(y * math.tau * 3.0) * 1.3) * 0.42
        + np.sin(y * math.tau * 11.0 + x * math.tau * 2.0) * 0.27
        + np.sin((x + y) * math.tau * 29.0) * 0.18
        + np.sin((x * 47.0 - y * 37.0) * math.tau) * 0.13
    )


def save_image(name, path, rgba, non_color=False):
    height, width, _ = rgba.shape
    image = bpy.data.images.new(name, width=width, height=height, alpha=True)
    image.pixels.foreach_set(np.asarray(rgba, dtype=np.float32).ravel())
    if non_color:
        image.colorspace_settings.name = "Non-Color"
    image.filepath_raw = str(path)
    image.file_format = "PNG"
    image.save()
    return image


def generate_skin_maps(size=1024):
    axis = np.linspace(0.0, 1.0, size, endpoint=False, dtype=np.float32)
    x, y = np.meshgrid(axis, axis)
    macro = periodic_noise(x, y)
    pores = (
        np.sin(x * math.tau * 173.0 + np.sin(y * math.tau * 19.0))
        * np.sin(y * math.tau * 191.0 + np.sin(x * math.tau * 23.0))
    )
    mottling = np.clip(pores * 0.82 + np.sin((x + y) * math.tau * 97.0) * 0.18, -1.0, 1.0)

    base = np.empty((size, size, 4), dtype=np.float32)
    # PNG color channels are sRGB encoded. These values decode to the source
    # material's linear 0.47 / 0.22 / 0.16 skin base.
    base[..., 0] = np.clip(0.715 + mottling * 0.004, 0.70, 0.73)
    base[..., 1] = np.clip(0.506 + mottling * 0.003, 0.495, 0.517)
    base[..., 2] = np.clip(0.437 + mottling * 0.0025, 0.427, 0.447)
    base[..., 3] = 1.0

    rough_value = np.clip(0.54 + mottling * 0.018, 0.50, 0.58)
    rough = np.stack((rough_value, rough_value, rough_value, np.ones_like(rough_value)), axis=-1)

    height = mottling
    gradient_y, gradient_x = np.gradient(height)
    nx = -gradient_x * 0.42
    ny = -gradient_y * 0.42
    nz = np.ones_like(nx)
    length = np.sqrt(nx * nx + ny * ny + nz * nz)
    normal = np.stack(
        (nx / length * 0.5 + 0.5, ny / length * 0.5 + 0.5, nz / length * 0.5 + 0.5, np.ones_like(nx)),
        axis=-1,
    )

    return (
        save_image("Aevrynd_Skin_BaseColor_v1", TEXTURE_DIR / "aevrynd-skin-basecolor-v1.png", base),
        save_image("Aevrynd_Skin_Roughness_v1", TEXTURE_DIR / "aevrynd-skin-roughness-v1.png", rough, True),
        save_image("Aevrynd_Skin_Normal_v1", TEXTURE_DIR / "aevrynd-skin-normal-v1.png", normal, True),
    )


def generate_sclera_map(width=1024, height=512):
    u = np.linspace(0.0, 1.0, width, endpoint=False, dtype=np.float32)
    v = np.linspace(0.0, 1.0, height, endpoint=False, dtype=np.float32)
    x, y = np.meshgrid(u, v)
    noise = periodic_noise(x, y)
    image = np.empty((height, width, 4), dtype=np.float32)
    image[..., 0] = 0.70 + noise * 0.018
    image[..., 1] = 0.63 + noise * 0.013
    image[..., 2] = 0.57 + noise * 0.010
    vein = np.zeros((height, width), dtype=np.float32)
    for index in range(15):
        baseline = 0.08 + index * 0.061
        curve = baseline + 0.020 * np.sin(x * math.tau * (1.0 + index % 4) + index * 1.37)
        curve += 0.006 * np.sin(x * math.tau * (7.0 + index % 3) + index * 0.83)
        distance = np.abs(y - curve)
        vein += np.exp(-((distance / (0.0009 + 0.00025 * (index % 3))) ** 2))
    vein = np.clip(vein, 0.0, 1.0)
    image[..., 0] = np.clip(image[..., 0] + vein * 0.075, 0.0, 1.0)
    image[..., 1] = np.clip(image[..., 1] - vein * 0.025, 0.0, 1.0)
    image[..., 2] = np.clip(image[..., 2] - vein * 0.030, 0.0, 1.0)
    image[..., 3] = 1.0
    return save_image("Aevrynd_Sclera_BaseColor_v1", TEXTURE_DIR / "aevrynd-sclera-basecolor-v1.png", image)


def clear_input_links(material, socket):
    for link in list(socket.links):
        material.node_tree.links.remove(link)


def attach_skin_maps(body, base_image, rough_image, normal_image):
    material = body.data.materials[0]
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = nodes.get("Principled BSDF")
    for name in ("Aevrynd Runtime BaseColor", "Aevrynd Runtime Roughness", "Aevrynd Runtime Normal", "Aevrynd Runtime Normal Map"):
        old = nodes.get(name)
        if old:
            nodes.remove(old)

    base = nodes.new("ShaderNodeTexImage")
    base.name = "Aevrynd Runtime BaseColor"
    base.image = base_image
    rough = nodes.new("ShaderNodeTexImage")
    rough.name = "Aevrynd Runtime Roughness"
    rough.image = rough_image
    normal = nodes.new("ShaderNodeTexImage")
    normal.name = "Aevrynd Runtime Normal"
    normal.image = normal_image
    normal_map = nodes.new("ShaderNodeNormalMap")
    normal_map.name = "Aevrynd Runtime Normal Map"
    normal_map.inputs["Strength"].default_value = 0.08

    clear_input_links(material, shader.inputs["Base Color"])
    clear_input_links(material, shader.inputs["Roughness"])
    clear_input_links(material, shader.inputs["Normal"])
    links.new(base.outputs["Color"], shader.inputs["Base Color"])
    shader.inputs["Roughness"].default_value = 0.54
    # Keep the authored normal map as a source texture. The current body UV
    # tangent basis is not yet continuous enough to use it safely at runtime.
    normal_map.inputs["Strength"].default_value = 0.0
    if shader.inputs.get("Specular IOR Level"):
        shader.inputs["Specular IOR Level"].default_value = 0.20
    if shader.inputs.get("Coat Weight"):
        shader.inputs["Coat Weight"].default_value = 0.0
    body["aevrynd_skin_texture_revision"] = 6
    body["aevrynd_skin_texture_resolution"] = 1024


def attach_sclera_map(image):
    material = bpy.data.materials["Aevrynd_Eye_Sclera"]
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = nodes.get("Principled BSDF")
    texture = nodes.new("ShaderNodeTexImage")
    texture.name = "Aevrynd Sclera BaseColor"
    texture.image = image
    clear_input_links(material, shader.inputs["Base Color"])
    links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    shader.inputs["Roughness"].default_value = 0.37
    if shader.inputs.get("Specular IOR Level"):
        shader.inputs["Specular IOR Level"].default_value = 0.24
    for side in ("L", "R"):
        bpy.data.objects[f"Eye_{side}_Sclera"]["aevrynd_sclera_texture_revision"] = 6


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
TEXTURE_DIR.mkdir(parents=True, exist_ok=True)
RENDER_DIR.mkdir(parents=True, exist_ok=True)
BUILD.parent.mkdir(parents=True, exist_ok=True)
body = bpy.data.objects["AevryndFemaleBodyBase"]

base_image, rough_image, normal_image = generate_skin_maps()
sclera_image = generate_sclera_map()
attach_skin_maps(body, base_image, rough_image, normal_image)
attach_sclera_map(sclera_image)
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
render(camera, "female-skin-front", (0, -0.78, 1.56), (0, -0.01, 1.545))
render(camera, "female-skin-three-quarter", (0.30, -0.68, 1.57), (0, -0.005, 1.54))

print(
    "AEVRYND_SKIN_V6_REPORT="
    + json.dumps({
        "state": "AUTHORING",
        "skin_maps": [base_image.name, rough_image.name, normal_image.name],
        "sclera_map": sclera_image.name,
        "texture_resolution": 1024,
        "runtime_objects": len(runtime),
        "runtime_glb": str(BUILD),
    })
)
