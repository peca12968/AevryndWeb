import json
import math
import random
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-rest-clearance-repair-r271.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-owned-alpha-hair-cards-r272.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-owned-alpha-hair-cards-r272.build-report.json"
TEXTURE = ROOT / "assets-source/aevrynd-character/textures/aevrynd-owned-hair-card-alpha-r272.png"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r272-owned-alpha-hair-cards"
CARDS = "AevryndFemaleRuntimeHairCards_R271"
POINTS = 24


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def smoothstep(value):
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def create_owned_atlas():
    width, height = 256, 1024
    rng = random.Random(272031)
    fibers = [
        {
            "center": (index + 0.5) / 15.0 + rng.uniform(-0.010, 0.010),
            "width": rng.uniform(0.0060, 0.0130),
            "phase": rng.uniform(-math.pi, math.pi),
            "wave": rng.uniform(0.004, 0.015),
            "tone": rng.uniform(0.72, 1.0),
        }
        for index in range(15)
    ]
    pixels = [0.0] * (width * height * 4)
    for y in range(height):
        v = y / (height - 1)
        root = 0.48 + 0.52 * smoothstep(v / 0.13)
        tip = 1.0 - smoothstep((v - 0.82) / 0.18)
        length_noise = 0.90 + 0.10 * math.sin(v * math.tau * 7.0 + 0.4)
        for x in range(width):
            u = x / (width - 1)
            edge = 1.0 - smoothstep((abs(u - 0.5) - 0.43) / 0.07)
            fiber_value = 0.0
            fiber_tone = 0.0
            for fiber in fibers:
                center = fiber["center"] + fiber["wave"] * math.sin(v * math.tau * 1.35 + fiber["phase"])
                strength = math.exp(-((u - center) / fiber["width"]) ** 2)
                fiber_value = max(fiber_value, strength)
                fiber_tone = max(fiber_tone, strength * fiber["tone"])
            alpha = edge * root * tip * length_noise * min(1.0, 0.10 + 0.96 * fiber_value)
            shade = 0.62 + 0.38 * fiber_tone
            offset = (y * width + x) * 4
            pixels[offset:offset + 4] = (0.024 * shade, 0.0062 * shade, 0.0032 * shade, alpha)
    old = bpy.data.images.get("AevryndOwnedHairCardAlpha_R272")
    if old:
        bpy.data.images.remove(old)
    image = bpy.data.images.new("AevryndOwnedHairCardAlpha_R272", width=width, height=height, alpha=True)
    image.pixels.foreach_set(pixels)
    TEXTURE.parent.mkdir(parents=True, exist_ok=True)
    image.filepath_raw = str(TEXTURE)
    image.file_format = "PNG"
    image.save()
    image.pack()
    image["aevrynd_ownership"] = "procedurally generated in-project"
    image["aevrynd_license"] = "Aevrynd-owned"
    image["aevrynd_revision"] = "v249r272"
    return image, width, height, len(fibers)


def assign_uv(mesh):
    old = mesh.uv_layers.get("AevryndRuntimeHairCardUV")
    if old:
        mesh.uv_layers.remove(old)
    layer = mesh.uv_layers.new(name="AevryndRuntimeHairCardUV")
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            vertex_index = mesh.loops[loop_index].vertex_index
            local = vertex_index % (POINTS * 2)
            point_index = local // 2
            side = local % 2
            layer.data[loop_index].uv = (float(side), point_index / (POINTS - 1))
    layer.active_render = True
    mesh.uv_layers.active = layer
    return len(layer.data)


def make_material(image):
    material = bpy.data.materials.new("Aevrynd_RuntimeHairCards_Alpha_R272")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = image
    shader.inputs["Roughness"].default_value = 0.60
    shader.inputs["Specular IOR Level"].default_value = 0.08
    if shader.inputs.get("Anisotropic IOR Level"):
        shader.inputs["Anisotropic IOR Level"].default_value = 0.62
    links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    links.new(texture.outputs["Alpha"], shader.inputs["Alpha"])
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    material.surface_render_method = "DITHERED"
    material.use_transparency_overlap = False
    material["aevrynd_layer"] = "material.hair.runtime_cards.alpha"
    material["aevrynd_ownership"] = "procedurally generated in-project"
    material["aevrynd_revision"] = "v249r272"
    return material


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, frame, name, location, target):
    scene = bpy.context.scene
    scene.frame_set(frame)
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    camera.location = location
    camera.data.lens = 82
    look_at(camera, target)
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
cards = bpy.data.objects[CARDS]
image, texture_width, texture_height, fiber_count = create_owned_atlas()
uv_loops = assign_uv(cards.data)
cards.data.materials.clear()
cards.data.materials.append(make_material(image))
cards["aevrynd_layer"] = "hair.runtime_cards.dynamic.alpha"
cards["aevrynd_revision"] = "v249r272"
scene["aevrynd_mainline_revision"] = "v249r272-owned-alpha-hair-cards"
scene["aevrynd_hair_layers"] = "primary_clumps.authoring|secondary_fill|flyaways|runtime_cards.dynamic.alpha"
scene["aevrynd_release_state"] = "ALPHA_CARD_VISUAL_AND_DYNAMIC_REAUDIT_PENDING"
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 800
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
for frame in (1, 25, 33, 41):
    render(camera, frame, f"front-f{frame:02d}", (0.0, -0.90, 1.59), (0.0, -0.01, 1.56))
for frame in (1, 33):
    render(camera, frame, f"back-f{frame:02d}", (0.0, 0.90, 1.59), (0.0, 0.01, 1.56))
scene.frame_set(1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE), "output": str(OUTPUT), "texture": str(TEXTURE),
    "textureSize": [texture_width, texture_height], "fiberCount": fiber_count,
    "uvLoops": uv_loops, "cardObject": CARDS,
    "geometryChanged": False, "animationChanged": False, "collisionContractChanged": False,
    "ownership": "Aevrynd-owned procedural texture and material",
    "renderDirectory": str(RENDER_DIR), "status": "ALPHA_CARD_VISUAL_AND_DYNAMIC_REAUDIT_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R272_OWNED_ALPHA_HAIR_CARDS=" + json.dumps(report, sort_keys=True))
