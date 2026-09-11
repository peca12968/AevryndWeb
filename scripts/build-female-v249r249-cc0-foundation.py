import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(r"D:\Download\Aevrynd\Temp\female-realism\blender-human-base-meshes-v1.4.1\extracted\human-base-meshes-bundle-v1.4.1\human_base_meshes_bundle.blend")
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cc0-foundation-r249.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-cc0-foundation-r249.build-report.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r249-cc0-foundation"
SOURCE_BODY = "GEO-body_female_realistic"
SOURCE_EYES = ("GEO-body_female_realistic.eye.L", "GEO-body_female_realistic.eye.R")
SOURCE_CENTER_X = -1.3400524854660034


def material(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    return mat, mat.node_tree.nodes, mat.node_tree.links


def skin_material():
    mat, nodes, links = material("Aevrynd_Skin_CC0Foundation_R249")
    shader = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
    texcoord = nodes.new("ShaderNodeTexCoord")
    color_noise = nodes.new("ShaderNodeTexNoise")
    color_noise.inputs["Scale"].default_value = 7.5
    color_noise.inputs["Detail"].default_value = 5.0
    color_noise.inputs["Roughness"].default_value = 0.68
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.22
    ramp.color_ramp.elements[0].color = (0.145, 0.042, 0.025, 1.0)
    ramp.color_ramp.elements[1].position = 0.78
    ramp.color_ramp.elements[1].color = (0.285, 0.105, 0.068, 1.0)
    pore_noise = nodes.new("ShaderNodeTexNoise")
    pore_noise.inputs["Scale"].default_value = 135.0
    pore_noise.inputs["Detail"].default_value = 3.5
    pore_noise.inputs["Roughness"].default_value = 0.72
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.16
    bump.inputs["Distance"].default_value = 0.00022
    links.new(texcoord.outputs["Generated"], color_noise.inputs["Vector"])
    links.new(color_noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], shader.inputs["Base Color"])
    links.new(texcoord.outputs["Generated"], pore_noise.inputs["Vector"])
    links.new(pore_noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    shader.inputs["Roughness"].default_value = 0.49
    shader.inputs["Specular IOR Level"].default_value = 0.28
    if "Subsurface Weight" in shader.inputs:
        shader.inputs["Subsurface Weight"].default_value = 0.075
    if "Coat Weight" in shader.inputs:
        shader.inputs["Coat Weight"].default_value = 0.035
        shader.inputs["Coat Roughness"].default_value = 0.32
    mat["aevrynd_layer"] = "material.skin.base"
    mat["aevrynd_revision"] = "v249r249"
    return mat


def simple_material(name, color, roughness, coat=0.0):
    mat, nodes, _links = material(name)
    shader = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Specular IOR Level"].default_value = 0.30
    if "Coat Weight" in shader.inputs:
        shader.inputs["Coat Weight"].default_value = coat
        shader.inputs["Coat Roughness"].default_value = 0.10
    return mat


def assign(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)


def disc(name, location, radius, depth, mat, layer):
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=radius, depth=depth, location=location, rotation=(math.pi / 2.0, 0.0, 0.0))
    obj = bpy.context.object
    obj.name = name
    assign(obj, mat)
    obj["aevrynd_layer"] = layer
    obj["aevrynd_revision"] = "v249r249"
    return obj


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def add_area(name, location, energy, size, color, target):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    data.color = color
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    look_at(obj, target)


def render(camera, name, location, target, lens, size):
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene = bpy.context.scene
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
body = bpy.data.objects[SOURCE_BODY]
eyes = [bpy.data.objects[name] for name in SOURCE_EYES]
keep = {body, *eyes}
for obj in list(bpy.data.objects):
    if obj not in keep:
        bpy.data.objects.remove(obj, do_unlink=True)

body.location.x -= SOURCE_CENTER_X
body.name = "AevryndFemaleBody_CC0_R249"
body.data.name = "AevryndFemaleBodyTopology_CC0_R249"
body["aevrynd_layer"] = "anatomy.body_head_continuous"
body["aevrynd_revision"] = "v249r249-cc0-foundation"
body["aevrynd_source_license"] = "CC0-1.0"
body["aevrynd_source_bundle"] = "Blender Human Base Meshes 1.4.1"
body["aevrynd_source_sha256"] = "811F43ACCBB31A88266D932F8F5563B2D13586FCA0BA2693AAD1F5FE582B3515"
body.modifiers["Multires"].levels = 2
body.modifiers["Multires"].render_levels = 2
assign(body, skin_material())
bpy.context.view_layer.update()

sclera_mat = simple_material("Aevrynd_EyeSclera_R249", (0.62, 0.56, 0.48, 1.0), 0.24, 0.30)
iris_mat = simple_material("Aevrynd_IrisBrown_R249", (0.075, 0.020, 0.008, 1.0), 0.30, 0.18)
pupil_mat = simple_material("Aevrynd_Pupil_R249", (0.003, 0.002, 0.001, 1.0), 0.18, 0.25)
limbal_mat = simple_material("Aevrynd_LimbalRing_R249", (0.012, 0.004, 0.002, 1.0), 0.34, 0.12)

new_layers = []
for side, eye in zip(("L", "R"), eyes):
    eye.name = f"AevryndEye_{side}_Sclera_R249"
    eye.data.name = f"AevryndEye_{side}_ScleraTopology_R249"
    eye["aevrynd_layer"] = f"eye.{side.lower()}.sclera"
    eye["aevrynd_revision"] = "v249r249"
    assign(eye, sclera_mat)
    world_center = eye.matrix_world.translation.copy()
    front_y = min((eye.matrix_world @ vertex.co).y for vertex in eye.data.vertices)
    ring = disc(f"AevryndEye_{side}_LimbalRing_R249", (world_center.x, front_y - 0.00020, world_center.z), 0.00595, 0.00022, limbal_mat, f"eye.{side.lower()}.limbal")
    iris = disc(f"AevryndEye_{side}_Iris_R249", (world_center.x, front_y - 0.00034, world_center.z), 0.00535, 0.00020, iris_mat, f"eye.{side.lower()}.iris")
    pupil = disc(f"AevryndEye_{side}_Pupil_R249", (world_center.x, front_y - 0.00047, world_center.z), 0.00235, 0.00018, pupil_mat, f"eye.{side.lower()}.pupil")
    for layer in (ring, iris, pupil):
        layer.parent = body
        layer.matrix_parent_inverse = body.matrix_world.inverted()
        new_layers.append(layer.name)

scene["aevrynd_mainline_revision"] = "v249r249-cc0-foundation"
scene["aevrynd_source_license"] = "CC0-1.0"
scene["aevrynd_source_url"] = "https://www.blender.org/download/demo-files/"
scene["aevrynd_release_state"] = "FOUNDATION_VISUAL_REVIEW_PENDING_NO_RIG_NO_CLOTHING_NO_HAIR"
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False
world = bpy.data.worlds.new("Aevrynd_R249_World")
scene.world = world
world.use_nodes = True
background = next((node for node in world.node_tree.nodes if node.type == "BACKGROUND"), None)
output = next((node for node in world.node_tree.nodes if node.type == "OUTPUT_WORLD"), None)
if background is None:
    background = world.node_tree.nodes.new("ShaderNodeBackground")
if output is None:
    output = world.node_tree.nodes.new("ShaderNodeOutputWorld")
if not output.inputs["Surface"].is_linked:
    world.node_tree.links.new(background.outputs["Background"], output.inputs["Surface"])
background.inputs["Color"].default_value = (0.010, 0.014, 0.020, 1.0)
background.inputs["Strength"].default_value = 0.18

camera_data = bpy.data.cameras.new("Aevrynd R249 Review Camera")
camera = bpy.data.objects.new("Aevrynd R249 Review Camera", camera_data)
scene.collection.objects.link(camera)
scene.camera = camera
add_area("Aevrynd R249 Key", (-0.62, -1.0, 1.88), 75, 0.72, (1.0, 0.74, 0.63), (0.0, 0.0, 1.42))
add_area("Aevrynd R249 Fill", (0.72, -0.60, 1.68), 42, 0.78, (0.62, 0.74, 1.0), (0.0, 0.0, 1.42))
add_area("Aevrynd R249 Rim", (0.0, 0.70, 1.82), 85, 0.62, (1.0, 0.83, 0.70), (0.0, 0.0, 1.48))

RENDER_DIR.mkdir(parents=True, exist_ok=True)
views = (
    ("01-full-front", (0.0, -4.25, 1.05), (0.0, 0.0, 0.95), 76, (900, 1200)),
    ("02-face-front", (0.0, -1.05, 1.58), (0.0, 0.0, 1.55), 88, (1000, 1000)),
    ("03-face-three-quarter", (0.58, -0.88, 1.60), (0.0, 0.0, 1.55), 88, (1000, 1000)),
    ("04-face-profile", (1.05, -0.02, 1.58), (0.0, 0.0, 1.54), 92, (1000, 1000)),
    ("05-full-back", (0.0, 4.25, 1.05), (0.0, 0.0, 0.95), 76, (900, 1200)),
)
for values in views:
    render(camera, *values)

bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "license": "CC0-1.0",
    "sourceUrl": "https://www.blender.org/download/demo-files/",
    "sourceSha256": "811F43ACCBB31A88266D932F8F5563B2D13586FCA0BA2693AAD1F5FE582B3515",
    "body": {"vertices": len(body.data.vertices), "polygons": len(body.data.polygons), "multiresLevel": 2},
    "layers": [body.name, *(eye.name for eye in eyes), *new_layers],
    "limitations": ["no rig", "no clothing", "no hair", "eye cornea and tear layers pending"],
    "status": "FOUNDATION_VISUAL_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R249_CC0_FOUNDATION=" + json.dumps(report, sort_keys=True))
