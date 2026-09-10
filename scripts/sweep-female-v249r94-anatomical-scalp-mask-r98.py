import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cc0-natural-long-hair-r94.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r94-anatomical-scalp-mask-r98-sweep"
MAIN = "AevryndFemaleCC0LongHairStudyMain_v249r85"
BODY = "AevryndFemaleBodyBaseV118"
LAYER = "AevryndFemaleAnatomicalScalpMaskSweep_v249r98"
ATTRIBUTE = "aevrynd_root_density"


def smooth(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def anatomical_density(point):
    side = abs(point.x) / 0.112
    if side >= 1.12:
        return 0.0
    # A shallow M-shaped frontal boundary.  The 22 mm transition is wide enough
    # to read as fine follicle density rather than a painted edge.
    if point.y <= -0.035:
        threshold = 1.678 + 0.027 * min(1.0, side) ** 1.65
        vertical = smooth((point.z - threshold) / 0.022)
    else:
        # Crown, temporal and occipital scalp remain continuous behind the
        # frontal boundary, with a lower fade toward ears and nape.
        threshold = 1.545 + 0.020 * smooth((abs(point.y) - 0.060) / 0.060)
        vertical = smooth((point.z - threshold) / 0.026)
    lateral = 1.0 - smooth((side - 0.94) / 0.18)
    return vertical * lateral


def build_scalp(body):
    evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    world_vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    normal_matrix = evaluated.matrix_world.to_3x3()
    density = [anatomical_density(point) for point in world_vertices]
    selected_faces = []
    for polygon in mesh.polygons:
        center = evaluated.matrix_world @ polygon.center
        if center.z < 1.535 or abs(center.x) > 0.135 or center.y < -0.155 or center.y > 0.120:
            continue
        if max(density[index] for index in polygon.vertices) <= 0.001:
            continue
        selected_faces.append(tuple(polygon.vertices))
    used = sorted({index for face in selected_faces for index in face})
    remap = {old: new for new, old in enumerate(used)}
    vertices = []
    for index in used:
        normal = (normal_matrix @ mesh.vertices[index].normal).normalized()
        vertices.append(world_vertices[index] + normal * 0.00025)
    faces = [tuple(remap[index] for index in face) for face in selected_faces]
    values = [density[index] for index in used]
    evaluated.to_mesh_clear()

    data = bpy.data.meshes.new(LAYER + "Data")
    data.from_pydata(vertices, [], faces)
    data.update()
    attribute = data.attributes.new(ATTRIBUTE, "FLOAT", "POINT")
    for index, value in enumerate(values):
        attribute.data[index].value = value
    obj = bpy.data.objects.new(LAYER, data)
    bpy.context.scene.collection.objects.link(obj)
    obj["aevrynd_layer"] = "hair.scalp.anatomical_density_mask"
    obj["aevrynd_revision"] = "v249r98-opacity-sweep"
    return obj, min(values), max(values)


def make_material():
    material = bpy.data.materials.new("AevryndAnatomicalScalpMaskMaterial_v249r98")
    material.use_nodes = True
    if hasattr(material, "surface_render_method"):
        material.surface_render_method = "DITHERED"
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    attribute = nodes.new("ShaderNodeAttribute")
    attribute.attribute_name = ATTRIBUTE
    strength = nodes.new("ShaderNodeMath")
    strength.operation = "MULTIPLY"
    strength.name = "Aevrynd Density Strength"
    strength.inputs[1].default_value = 0.45
    bsdf.inputs["Base Color"].default_value = (0.012, 0.0028, 0.0012, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.88
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.18
    links.new(attribute.outputs["Fac"], strength.inputs[0])
    links.new(strength.outputs[0], bsdf.inputs["Alpha"])
    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    return material, strength


def render(camera, name, location, target, lens):
    scene = bpy.context.scene
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
OUT.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
main = bpy.data.objects[MAIN]
scalp, minimum_density, maximum_density = build_scalp(bpy.data.objects[BODY])
material, strength = make_material()
scalp.data.materials.append(material)
camera = bpy.data.objects["Aevrynd Review Camera"]
report = {
    "source": str(SOURCE), "vertices": len(scalp.data.vertices), "faces": len(scalp.data.polygons),
    "densityRange": [minimum_density, maximum_density], "variants": [],
}
for opacity in (0.28, 0.46, 0.64, 1.0):
    strength.inputs[1].default_value = opacity
    for suffix, location, target, lens in (
        ("front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
        ("three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88),
        ("top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
    ):
        render(camera, f"{opacity:.2f}-{suffix}", location, target, lens)
    report["variants"].append({"opacity": opacity})

strength.inputs[1].default_value = 1.0
main.hide_render = True
render(camera, "1.00-scalp-isolation", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88)
main.hide_render = False

(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R98_ANATOMICAL_SCALP_SWEEP=" + json.dumps(report, sort_keys=True))
