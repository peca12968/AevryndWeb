import json
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v16.blend"
OUTPUT = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v17.blend"
BUILD = ROOT / ".character-build" / "aevrynd-female-authoring-v17.glb"
LOD1 = ROOT / ".character-build" / "aevrynd-female-authoring-v17-lod1.glb"
TEXTURE_DIR = ROOT / "assets-source" / "aevrynd-character" / "textures"
NORMAL_PATH = TEXTURE_DIR / "aevrynd-skin-normal-v2.png"
ROUGHNESS_PATH = TEXTURE_DIR / "aevrynd-skin-roughness-v2.png"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "skin-v17"


def save_image(name, path, rgb):
    old = bpy.data.images.get(name)
    if old:
        bpy.data.images.remove(old)
    height, width, _ = rgb.shape
    rgba = np.ones((height, width, 4), dtype=np.float32)
    rgba[:, :, :3] = np.clip(rgb, 0.0, 1.0)
    image = bpy.data.images.new(name, width=width, height=height, alpha=True, float_buffer=False)
    image.colorspace_settings.name = "Non-Color"
    image.pixels.foreach_set(rgba.ravel())
    image.filepath_raw = str(path)
    image.file_format = "PNG"
    image.save()
    return image


def generate_skin_maps(size=256):
    rng = np.random.default_rng(171017)

    def blur(values, iterations):
        result = values.astype(np.float32)
        for _ in range(iterations):
            result = (
                result * 4.0
                + np.roll(result, 1, 0) + np.roll(result, -1, 0)
                + np.roll(result, 1, 1) + np.roll(result, -1, 1)
            ) / 8.0
        return result

    source = rng.standard_normal((size, size), dtype=np.float32)
    pore_height = blur(source, 2)
    pore_height = (pore_height - pore_height.mean()) / max(1e-6, pore_height.std())
    nx = -(np.roll(pore_height, -1, 1) - np.roll(pore_height, 1, 1)) * 0.040
    ny = -(np.roll(pore_height, -1, 0) - np.roll(pore_height, 1, 0)) * 0.040
    length = np.sqrt(nx * nx + ny * ny + 1.0)
    normal = np.stack((nx / length * 0.5 + 0.5, ny / length * 0.5 + 0.5, 1.0 / length * 0.5 + 0.5), axis=2)
    rough_micro = blur(source, 5)
    rough_micro = (rough_micro - rough_micro.mean()) / max(1e-6, rough_micro.std())
    rough_broad = blur(source, 32)
    rough_broad = (rough_broad - rough_broad.mean()) / max(1e-6, rough_broad.std())
    rough = np.clip(0.540 + rough_micro * 0.018 + rough_broad * 0.012, 0.47, 0.61)
    normal[:, -1] = normal[:, 0]
    normal[-1, :] = normal[0, :]
    rough[:, -1] = rough[:, 0]
    rough[-1, :] = rough[0, :]
    roughness = np.repeat(rough[:, :, None], 3, axis=2)
    return save_image("Aevrynd_SkinNormal_v2", NORMAL_PATH, normal), save_image("Aevrynd_SkinRoughness_v2", ROUGHNESS_PATH, roughness), {
        "normal_min": float(normal.min()),
        "normal_max": float(normal.max()),
        "roughness_min": float(rough.min()),
        "roughness_max": float(rough.max()),
        "normal_horizontal_edge_delta": float(np.max(np.abs(normal[:, 0] - normal[:, -1]))),
        "normal_vertical_edge_delta": float(np.max(np.abs(normal[0] - normal[-1]))),
        "roughness_horizontal_edge_delta": float(np.max(np.abs(rough[:, 0] - rough[:, -1]))),
        "roughness_vertical_edge_delta": float(np.max(np.abs(rough[0] - rough[-1]))),
    }


def connect_skin_maps(body, normal_image, roughness_image):
    material = body.data.materials[0]
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = nodes.get("Principled BSDF")
    normal_texture = nodes.get("Aevrynd Runtime Normal") or nodes.new("ShaderNodeTexImage")
    normal_texture.name = "Aevrynd Runtime Normal"
    normal_texture.image = normal_image
    normal_texture.interpolation = "Linear"
    normal_map = nodes.get("Aevrynd Runtime Normal Map") or nodes.new("ShaderNodeNormalMap")
    normal_map.name = "Aevrynd Runtime Normal Map"
    normal_map.inputs["Strength"].default_value = 0.28
    roughness_texture = nodes.get("Aevrynd Runtime Roughness") or nodes.new("ShaderNodeTexImage")
    roughness_texture.name = "Aevrynd Runtime Roughness"
    roughness_texture.image = roughness_image
    roughness_texture.interpolation = "Linear"
    for socket in (shader.inputs["Normal"], shader.inputs["Roughness"], normal_map.inputs["Color"]):
        for link in tuple(socket.links):
            links.remove(link)
    links.new(normal_texture.outputs["Color"], normal_map.inputs["Color"])
    links.new(normal_map.outputs["Normal"], shader.inputs["Normal"])
    links.new(roughness_texture.outputs["Color"], shader.inputs["Roughness"])
    if shader.inputs.get("Specular IOR Level"):
        shader.inputs["Specular IOR Level"].default_value = 0.24
    if shader.inputs.get("Subsurface Weight"):
        shader.inputs["Subsurface Weight"].default_value = 0.055
    if shader.inputs.get("Coat Weight"):
        shader.inputs["Coat Weight"].default_value = 0.015
    material["aevrynd_skin_revision"] = 17
    material["aevrynd_skin_maps"] = "normal-v2,roughness-v2"


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, location, target, lens=86):
    scene = bpy.context.scene
    scene.frame_set(1)
    camera.data.lens = lens
    camera.location = location
    look_at(camera, target)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 900
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    for obj in bpy.data.objects:
        if obj.get("aevrynd_role") == "cornea":
            obj.hide_render = True
    bpy.ops.render.render(write_still=True)


def export_runtime(path, rig, excluded=()):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in bpy.data.objects:
        if obj.type in {"MESH", "ARMATURE"} and obj.name not in excluded:
            obj.hide_render = False
            obj.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.export_scene.gltf(
        filepath=str(path), export_format="GLB", use_selection=True,
        export_apply=True, export_yup=True, export_extras=True,
        export_animations=True, export_frame_range=True,
        export_attributes=True, export_vertex_color="ACTIVE",
    )


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
bpy.context.preferences.filepaths.save_version = 0
bpy.context.scene.frame_set(1)
TEXTURE_DIR.mkdir(parents=True, exist_ok=True)
RENDER_DIR.mkdir(parents=True, exist_ok=True)
BUILD.parent.mkdir(parents=True, exist_ok=True)
body = bpy.data.objects["AevryndFemaleBodyBase"]
rig = bpy.data.objects["AevryndFemaleRig"]
normal_image, roughness_image, map_report = generate_skin_maps()
connect_skin_maps(body, normal_image, roughness_image)
body["aevrynd_skin_revision"] = 17
bpy.context.scene["aevrynd_skin_revision"] = 17
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

camera = bpy.data.objects["Aevrynd Review Camera"]
render(camera, "female-skin-front", (0.0, -0.72, 1.575), (0.0, -0.005, 1.555))
render(camera, "female-skin-three-quarter", (0.28, -0.64, 1.58), (0.0, 0.0, 1.55))
render(camera, "female-skin-side", (0.66, -0.05, 1.575), (0.0, 0.0, 1.545))
render(camera, "female-skin-close", (0.0, -0.48, 1.575), (0.0, -0.075, 1.565), 102)

body_multires = next(modifier for modifier in body.modifiers if modifier.type == "MULTIRES")
old_multires = (body_multires.levels, body_multires.sculpt_levels, body_multires.render_levels)
body_multires.levels = body_multires.sculpt_levels = body_multires.render_levels = 0
export_runtime(BUILD, rig)
export_runtime(LOD1, rig, {"HairMain", "HairFlyaways"})
body_multires.levels, body_multires.sculpt_levels, body_multires.render_levels = old_multires

print("AEVRYND_SKIN_V17_REPORT=" + json.dumps({
    "state": "AUTHORING",
    "normal_texture": str(NORMAL_PATH),
    "roughness_texture": str(ROUGHNESS_PATH),
    **map_report,
    "runtime_glb": str(BUILD),
    "lod1_glb": str(LOD1),
}))
