import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cc0-normalized-rig-r251.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-eye-optics-skin-r252.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-eye-optics-skin-r252.build-report.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r252-eye-optics-skin"
IRIS_TEXTURE = ROOT / "assets-source/aevrynd-character/textures/aevrynd-iris-hazel-v5.png"
BODY = "AevryndFemaleBody_CC0_R249"
RIG = "AevryndFemaleRig"
HEAD_BONE = "head"


def new_principled(name):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
    return material, nodes, links, shader


def set_layer(obj, layer):
    obj["aevrynd_layer"] = layer
    obj["aevrynd_revision"] = "v249r252"


def assign(obj, material):
    obj.data.materials.clear()
    obj.data.materials.append(material)


def bind_to_head(obj, rig):
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = HEAD_BONE
    obj.matrix_world = world
    obj["aevrynd_binding"] = "rig.head"


def skin_material():
    material, nodes, links, shader = new_principled("Aevrynd_Skin_Physical_R252")
    texcoord = nodes.new("ShaderNodeTexCoord")
    macro = nodes.new("ShaderNodeTexNoise")
    macro.name = "Aevrynd anatomical tone breakup"
    macro.inputs["Scale"].default_value = 34.0
    macro.inputs["Detail"].default_value = 3.0
    macro.inputs["Roughness"].default_value = 0.58
    macro.inputs["Distortion"].default_value = 0.08
    tone = nodes.new("ShaderNodeValToRGB")
    tone.name = "Aevrynd restrained melanin range"
    tone.color_ramp.elements[0].position = 0.20
    tone.color_ramp.elements[0].color = (0.085, 0.021, 0.012, 1.0)
    tone.color_ramp.elements[1].position = 0.80
    tone.color_ramp.elements[1].color = (0.185, 0.061, 0.035, 1.0)
    pores = nodes.new("ShaderNodeTexNoise")
    pores.name = "Aevrynd isotropic pore field"
    pores.inputs["Scale"].default_value = 1550.0
    pores.inputs["Detail"].default_value = 2.2
    pores.inputs["Roughness"].default_value = 0.64
    bump = nodes.new("ShaderNodeBump")
    bump.name = "Aevrynd pore micro-normal"
    bump.inputs["Strength"].default_value = 0.075
    bump.inputs["Distance"].default_value = 0.00009
    links.new(texcoord.outputs["Object"], macro.inputs["Vector"])
    links.new(macro.outputs["Fac"], tone.inputs["Fac"])
    links.new(tone.outputs["Color"], shader.inputs["Base Color"])
    links.new(texcoord.outputs["Object"], pores.inputs["Vector"])
    links.new(pores.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    shader.inputs["Roughness"].default_value = 0.52
    shader.inputs["Specular IOR Level"].default_value = 0.23
    shader.inputs["Subsurface Weight"].default_value = 0.055
    shader.inputs["Subsurface Radius"].default_value = (1.0, 0.42, 0.22)
    shader.inputs["Subsurface Scale"].default_value = 0.0065
    shader.inputs["Coat Weight"].default_value = 0.018
    shader.inputs["Coat Roughness"].default_value = 0.38
    material["aevrynd_layer"] = "material.skin.base"
    material["aevrynd_coordinate_contract"] = "object-space isotropic; no generated-coordinate body stretching"
    return material


def sclera_material():
    material, nodes, links, shader = new_principled("Aevrynd_EyeSclera_Physical_R252")
    texcoord = nodes.new("ShaderNodeTexCoord")
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 105.0
    noise.inputs["Detail"].default_value = 2.0
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.46, 0.39, 0.32, 1.0)
    ramp.color_ramp.elements[1].color = (0.78, 0.70, 0.61, 1.0)
    links.new(texcoord.outputs["Object"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], shader.inputs["Base Color"])
    shader.inputs["Roughness"].default_value = 0.30
    shader.inputs["Specular IOR Level"].default_value = 0.27
    shader.inputs["Subsurface Weight"].default_value = 0.035
    shader.inputs["Subsurface Scale"].default_value = 0.0012
    return material


def iris_material():
    material, nodes, links, shader = new_principled("Aevrynd_IrisHazel_Owned_R252")
    image = bpy.data.images.load(str(IRIS_TEXTURE), check_existing=True)
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = image
    texture.interpolation = "Linear"
    texture.extension = "CLIP"
    links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    shader.inputs["Roughness"].default_value = 0.42
    shader.inputs["Specular IOR Level"].default_value = 0.16
    material["aevrynd_texture_ownership"] = "Aevrynd-generated"
    return material


def solid_material(name, color, roughness):
    material, _nodes, _links, shader = new_principled(name)
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Specular IOR Level"].default_value = 0.18
    return material


def cornea_material():
    material, _nodes, _links, shader = new_principled("Aevrynd_Cornea_Physical_R252")
    shader.inputs["Base Color"].default_value = (0.92, 0.97, 1.0, 1.0)
    shader.inputs["Roughness"].default_value = 0.018
    shader.inputs["IOR"].default_value = 1.376
    shader.inputs["Transmission Weight"].default_value = 1.0
    shader.inputs["Alpha"].default_value = 0.12
    shader.inputs["Coat Weight"].default_value = 0.12
    shader.inputs["Coat Roughness"].default_value = 0.025
    if hasattr(material, "surface_render_method"):
        material.surface_render_method = "DITHERED"
    material.use_transparency_overlap = False
    return material


def replace_disc(old, name, radius, depth, y, material, layer, rig):
    center = old.matrix_world.translation.copy()
    bpy.data.objects.remove(old, do_unlink=True)
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=128,
        radius=radius,
        depth=depth,
        location=(center.x, y, center.z),
        rotation=(math.pi / 2.0, 0.0, 0.0),
    )
    obj = bpy.context.object
    obj.name = name
    assign(obj, material)
    set_layer(obj, layer)
    for polygon in obj.data.polygons:
        polygon.use_smooth = False
    bind_to_head(obj, rig)
    return obj


def make_cornea_cap(name, center, radius, max_angle, material, layer, rig):
    rings = 14
    segments = 96
    vertices = [(center.x, center.y - radius, center.z)]
    for ring in range(1, rings + 1):
        angle = max_angle * ring / rings
        radial = radius * math.sin(angle)
        y = center.y - radius * math.cos(angle)
        for segment in range(segments):
            phi = 2.0 * math.pi * segment / segments
            vertices.append((center.x + radial * math.cos(phi), y, center.z + radial * math.sin(phi)))
    faces = []
    for segment in range(segments):
        faces.append((0, 1 + segment, 1 + (segment + 1) % segments))
    for ring in range(1, rings):
        start_a = 1 + (ring - 1) * segments
        start_b = 1 + ring * segments
        for segment in range(segments):
            nxt = (segment + 1) % segments
            faces.append((start_a + segment, start_b + segment, start_b + nxt, start_a + nxt))
    mesh = bpy.data.meshes.new(name + "Topology")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    assign(obj, material)
    set_layer(obj, layer)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    bind_to_head(obj, rig)
    return obj


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, frame, name, location, target, lens, size):
    scene = bpy.context.scene
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
body = bpy.data.objects[BODY]
rig = bpy.data.objects[RIG]
assign(body, skin_material())
for polygon in body.data.polygons:
    polygon.use_smooth = True
body["aevrynd_revision"] = "v249r252-eye-optics-skin"

sclera_mat = sclera_material()
iris_mat = iris_material()
pupil_mat = solid_material("Aevrynd_Pupil_Physical_R252", (0.0012, 0.0008, 0.0005, 1.0), 0.32)
limbal_mat = solid_material("Aevrynd_Limbal_Physical_R252", (0.010, 0.013, 0.008, 1.0), 0.38)
cornea_mat = cornea_material()

created = []
metrics = {}
for side in ("L", "R"):
    sclera = bpy.data.objects[f"AevryndEye_{side}_Sclera_R249"]
    for polygon in sclera.data.polygons:
        polygon.use_smooth = True
    assign(sclera, sclera_mat)
    set_layer(sclera, f"eye.{side.lower()}.sclera")
    points = [sclera.matrix_world @ vertex.co for vertex in sclera.data.vertices]
    center = Vector((
        sum(point.x for point in points) / len(points),
        sum(point.y for point in points) / len(points),
        sum(point.z for point in points) / len(points),
    ))
    sclera_front = min(point.y for point in points)
    eye_radius = max(max(point.x for point in points) - min(point.x for point in points), max(point.z for point in points) - min(point.z for point in points)) / 2.0
    limbal = replace_disc(
        bpy.data.objects[f"AevryndEye_{side}_LimbalRing_R249"],
        f"AevryndEye_{side}_Limbal_R252", 0.00625, 0.00010, sclera_front - 0.00013,
        limbal_mat, f"eye.{side.lower()}.limbal_ring", rig,
    )
    iris = replace_disc(
        bpy.data.objects[f"AevryndEye_{side}_Iris_R249"],
        f"AevryndEye_{side}_Iris_R252", 0.00572, 0.00012, sclera_front - 0.00020,
        iris_mat, f"eye.{side.lower()}.iris_stroma", rig,
    )
    pupil = replace_disc(
        bpy.data.objects[f"AevryndEye_{side}_Pupil_R249"],
        f"AevryndEye_{side}_Pupil_R252", 0.00215, 0.00012, sclera_front - 0.00028,
        pupil_mat, f"eye.{side.lower()}.pupil", rig,
    )
    cornea = make_cornea_cap(
        f"AevryndEye_{side}_Cornea_R252", center, eye_radius + 0.00056, math.radians(29.0),
        cornea_mat, f"eye.{side.lower()}.cornea", rig,
    )
    created.extend([limbal.name, iris.name, pupil.name, cornea.name])
    cornea_front = min((cornea.matrix_world @ vertex.co).y for vertex in cornea.data.vertices)
    iris_front = min((iris.matrix_world @ vertex.co).y for vertex in iris.data.vertices)
    metrics[side] = {
        "center": list(center),
        "eyeRadiusM": eye_radius,
        "scleraFrontY": sclera_front,
        "irisFrontY": iris_front,
        "corneaFrontY": cornea_front,
        "corneaAheadOfIrisM": iris_front - cornea_front,
        "irisDiameterM": 0.01144,
        "pupilDiameterM": 0.00430,
    }

for obj in scene.objects:
    if obj.type == "LIGHT":
        obj.data.energy *= 0.52
if scene.world and scene.world.use_nodes:
    background = next((node for node in scene.world.node_tree.nodes if node.type == "BACKGROUND"), None)
    if background:
        background.inputs["Strength"].default_value = 0.10

scene["aevrynd_mainline_revision"] = "v249r252-eye-optics-skin"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "EYE_OPTICS_VISUAL_AND_CLEARANCE_REVIEW_PENDING"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
views = (
    (1, "01-face-front", (0.0, -1.02, 1.66), (0.0, 0.0, 1.625), 92, (1100, 1100)),
    (1, "02-face-three-quarter", (0.56, -0.89, 1.65), (0.0, 0.0, 1.615), 92, (1100, 1100)),
    (1, "03-eye-front", (0.0, -0.55, 1.616), (0.0, -0.13, 1.608), 105, (1200, 700)),
    (1, "04-full-front", (0.0, -4.45, 1.10), (0.0, 0.0, 1.00), 76, (900, 1200)),
    (20, "05-pose-face", (0.56, -0.89, 1.65), (0.0, 0.0, 1.615), 92, (1100, 1100)),
)
for values in views:
    render(camera, *values)
scene.frame_set(1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "ownedIrisTexture": str(IRIS_TEXTURE),
    "bodySmoothPolygons": sum(polygon.use_smooth for polygon in body.data.polygons),
    "bodyPolygonCount": len(body.data.polygons),
    "createdLayers": created,
    "eyeMetrics": metrics,
    "renderDirectory": str(RENDER_DIR),
    "limitations": ["brows, eyelashes, lid wetline and tear meniscus pending", "identity sculpt pending"],
    "status": "EYE_OPTICS_VISUAL_AND_CLEARANCE_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R252_EYE_OPTICS_SKIN=" + json.dumps(report, sort_keys=True))
