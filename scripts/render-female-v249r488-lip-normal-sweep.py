import json
import hashlib
import math
import struct
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-balanced-lower-lip-r485.blend"
TEXTURE = ASSETS / "textures/aevrynd-female-lip-normal-v1.png"
OUT = ASSETS / "reviews/v249r488-lip-normal-sweep"
REPORT = ASSETS / "female-v249-mainline-lip-normal-r488.study.json"
OUTPUT = ASSETS / "aevrynd-female-authoring-v249-mainline-owned-lip-normal-r488.blend"
BODY = "AevryndFemaleBodyBaseV118"
UV_NAME = "AevryndLipDetailUV"
STRENGTHS = (0.0, 0.12, 0.22, 0.35, 0.60, 1.00)
SELECTED_STRENGTH = 0.35


def coordinate_hash(body):
    digest = hashlib.sha256()
    for vertex in body.data.vertices:
        digest.update(struct.pack("<3d", *vertex.co))
    if body.data.shape_keys:
        for key in body.data.shape_keys.key_blocks:
            digest.update(key.name.encode("utf-8"))
            for point in key.data:
                digest.update(struct.pack("<3d", *point.co))
    return digest.hexdigest()


def look(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, camera, label, location, target, lens, size):
    camera.location = location
    camera.data.lens = lens
    look(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.filepath = str(OUT / f"{label}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
body = bpy.data.objects[BODY]
coordinate_hash_before = coordinate_hash(body)

# UV positions are derived from the evaluated frame-1 body so the projected
# lip footprint follows the current shape-key state while retaining mesh indices.
depsgraph = bpy.context.evaluated_depsgraph_get()
evaluated = body.evaluated_get(depsgraph)
evaluated_mesh = evaluated.to_mesh()
world_positions = [evaluated.matrix_world @ vertex.co for vertex in evaluated_mesh.vertices]
evaluated.to_mesh_clear()

if UV_NAME in body.data.uv_layers:
    body.data.uv_layers.remove(body.data.uv_layers[UV_NAME])
uv_layer = body.data.uv_layers.new(name=UV_NAME)
mapped_loops = 0
mapped_vertices = set()
mapped_uvs = []
for loop in body.data.loops:
    point = world_positions[loop.vertex_index]
    # Include a neutral perioral gutter around the analytical vermilion mask.
    if abs(point.x) <= 0.061 and -0.155 <= point.y <= -0.090 and 1.490 <= point.z <= 1.553:
        u = max(0.002, min(0.998, 0.5 + point.x * 8.0))
        v = max(0.002, min(0.998, 0.5 + (point.z - 1.522) * 16.0))
        uv_layer.data[loop.index].uv = (u, v)
        mapped_loops += 1
        mapped_vertices.add(loop.vertex_index)
        mapped_uvs.append((u, v))
    else:
        uv_layer.data[loop.index].uv = (0.0, 0.0)

material = body.active_material
nodes = material.node_tree.nodes
links = material.node_tree.links
principled = next(n for n in nodes if n.type == "BSDF_PRINCIPLED")
pore = nodes.get("Aevrynd pore micro-normal")
if pore is None:
    raise RuntimeError("Existing pore micro-normal node is missing")

for name in ("Aevrynd Lip Detail UV R488", "Aevrynd Lip Normal Texture R488", "Aevrynd Lip Normal R488", "Aevrynd Lip Normal Mask R488", "Aevrynd Lip Normal Lower Mask R488", "Aevrynd Lip Normal Upper Normalize R488", "Aevrynd Lip Normal Lower Normalize R488", "Aevrynd Lip Normal Mask Max R488", "Aevrynd Lip Normal Masked RGB R488"):
    old = nodes.get(name)
    if old:
        nodes.remove(old)

image = bpy.data.images.load(str(TEXTURE), check_existing=True)
image.colorspace_settings.name = "Non-Color"
uv_node = nodes.new("ShaderNodeUVMap")
uv_node.name = "Aevrynd Lip Detail UV R488"
uv_node.label = "Dedicated portable lip UV"
uv_node.uv_map = UV_NAME
uv_node.location = (-620, -500)
texture_node = nodes.new("ShaderNodeTexImage")
texture_node.name = "Aevrynd Lip Normal Texture R488"
texture_node.label = "Aevrynd-owned 1024 lip normal"
texture_node.image = image
texture_node.interpolation = "Linear"
texture_node.extension = "CLIP"
texture_node.location = (-400, -500)
normal_node = nodes.new("ShaderNodeNormalMap")
normal_node.name = "Aevrynd Lip Normal R488"
normal_node.label = "Tangent-space lip microrelief"
normal_node.space = "TANGENT"
normal_node.uv_map = UV_NAME
normal_node.location = (-160, -430)
upper_mask = nodes.new("ShaderNodeAttribute")
upper_mask.name = "Aevrynd Lip Normal Mask R488"
upper_mask.attribute_name = "AevryndVermilionPlaneR484_c-defined-280"
upper_mask.location = (-620, -710)
lower_mask = nodes.new("ShaderNodeAttribute")
lower_mask.name = "Aevrynd Lip Normal Lower Mask R488"
lower_mask.attribute_name = "AevryndLowerVermilionR475"
lower_mask.location = (-620, -820)
upper_normalize = nodes.new("ShaderNodeMath")
upper_normalize.name = "Aevrynd Lip Normal Upper Normalize R488"
upper_normalize.operation = "MULTIPLY"
upper_normalize.inputs[1].default_value = 1.0 / 0.34
upper_normalize.use_clamp = True
upper_normalize.location = (-470, -690)
lower_normalize = nodes.new("ShaderNodeMath")
lower_normalize.name = "Aevrynd Lip Normal Lower Normalize R488"
lower_normalize.operation = "MULTIPLY"
lower_normalize.inputs[1].default_value = 10.0
lower_normalize.use_clamp = True
lower_normalize.location = (-470, -820)
mask_max = nodes.new("ShaderNodeMath")
mask_max.name = "Aevrynd Lip Normal Mask Max R488"
mask_max.operation = "MAXIMUM"
mask_max.use_clamp = True
mask_max.location = (-390, -710)
masked_rgb = nodes.new("ShaderNodeMixRGB")
masked_rgb.name = "Aevrynd Lip Normal Masked RGB R488"
masked_rgb.blend_type = "MIX"
masked_rgb.inputs[1].default_value = (0.5, 0.5, 1.0, 1.0)
masked_rgb.location = (-160, -560)
links.new(uv_node.outputs["UV"], texture_node.inputs["Vector"])
links.new(upper_mask.outputs["Color"], upper_normalize.inputs[0])
links.new(lower_mask.outputs["Color"], lower_normalize.inputs[0])
links.new(upper_normalize.outputs[0], mask_max.inputs[0])
links.new(lower_normalize.outputs[0], mask_max.inputs[1])
links.new(mask_max.outputs[0], masked_rgb.inputs[0])
links.new(texture_node.outputs["Color"], masked_rgb.inputs[2])
links.new(masked_rgb.outputs["Color"], normal_node.inputs["Color"])

# Compose the authored normal below the existing procedural pore bump. This is
# Blender preview wiring; the engine contract is recorded separately below.
if pore.inputs["Normal"].is_linked:
    for link in list(pore.inputs["Normal"].links):
        links.remove(link)
links.new(normal_node.outputs["Normal"], pore.inputs["Normal"])
if not principled.inputs["Normal"].is_linked or principled.inputs["Normal"].links[0].from_node != pore:
    for link in list(principled.inputs["Normal"].links):
        links.remove(link)
    links.new(pore.outputs["Normal"], principled.inputs["Normal"])

body["aevrynd_lip_normal_asset"] = "textures/aevrynd-female-lip-normal-v1.png"
body["aevrynd_lip_normal_uv"] = UV_NAME
body["aevrynd_lip_normal_contract"] = "sample tangent-space RGB normal from TEXCOORD_1; blend only on skin material"
body["aevrynd_lip_normal_license"] = "Aevrynd-owned deterministic generation; no external inputs"

scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0
scene.view_settings.gamma = 1
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
OUT.mkdir(parents=True, exist_ok=True)
views = (
    ("mouth", (0, -0.405, 1.528), (0, -0.115, 1.528), 135, (1400, 800)),
    ("oblique", (0.235, -0.405, 1.530), (0, -0.112, 1.528), 135, (1400, 800)),
    ("face", (0, -0.560, 1.585), (0, -0.060, 1.585), 108, (1100, 1100)),
)
for strength in STRENGTHS:
    normal_node.inputs["Strength"].default_value = strength
    for name, location, target, lens, size in views:
        render(scene, camera, f"s{strength:.2f}-{name}-f01", location, target, lens, size)

normal_node.inputs["Strength"].default_value = SELECTED_STRENGTH
image.filepath = bpy.path.relpath(str(TEXTURE))
scene.frame_set(1)
scene["aevrynd_revision"] = "v249r488-owned-lip-normal"
scene["aevrynd_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "OFFLINE_TECHNICAL_CANDIDATE_ENGINE_INTEGRATION_PENDING"
body["aevrynd_lip_normal_strength"] = SELECTED_STRENGTH
coordinate_hash_after = coordinate_hash(body)
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

u_values = [uv[0] for uv in mapped_uvs]
v_values = [uv[1] for uv in mapped_uvs]
report = {
    "revision": "v249r488-study",
    "source": str(SOURCE),
    "texture": str(TEXTURE),
    "uvLayer": UV_NAME,
    "mappedLoops": mapped_loops,
    "mappedVertices": len(mapped_vertices),
    "mappedUvBounds": [min(u_values), min(v_values), max(u_values), max(v_values)],
    "dedicatedResolution": [image.size[0], image.size[1]],
    "strengths": list(STRENGTHS),
    "selectedStrength": SELECTED_STRENGTH,
    "rejectedStrengths": {"0.60": "overstated dry/cracked grooves", "1.00": "severe carved-groove artifact"},
    "output": str(OUTPUT),
    "coordinateHashBefore": coordinate_hash_before,
    "coordinateHashAfter": coordinate_hash_after,
    "coordinateHashExact": coordinate_hash_before == coordinate_hash_after,
    "geometryChanged": False,
    "baseColorChanged": False,
    "blenderComposition": "dedicated tangent normal is confined by separately normalized actual upper/lower vermilion POINT attributes, then feeds existing pore bump Normal input",
    "engineIntegration": "pending; TEXCOORD_1 contract recorded, no website promotion",
    "status": "OFFLINE_TECHNICAL_CANDIDATE_ENGINE_INTEGRATION_PENDING",
    "reviewDirectory": str(OUT),
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R488_SWEEP=" + json.dumps(report, sort_keys=True))
