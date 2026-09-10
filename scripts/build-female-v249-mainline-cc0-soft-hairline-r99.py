import json
import math
import random
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cc0-natural-long-hair-r94.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cc0-soft-hairline-r99.blend"
OUT = ROOT.parent / "Temp/female-realism/v249-mainline-cc0-soft-hairline-r99"
MAIN = "AevryndFemaleCC0LongHairStudyMain_v249r85"
BODY = "AevryndFemaleBodyBaseV118"
RIG = "AevryndFemaleRig"
LAYER = "AevryndFemaleAnatomicalScalpMask_v249r99"
BABY_LAYER = "AevryndFemaleHairlineBabyFibers_v249r99"
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
        threshold = 1.662 + 0.027 * min(1.0, side) ** 1.65
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
    obj["aevrynd_revision"] = "v249r99"
    return obj, min(values), max(values)


def make_material():
    material = bpy.data.materials.new("AevryndAnatomicalScalpMaskMaterial_v249r99")
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


def evaluated_body_tree(body):
    evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, faces, all_triangles=False)


def surface_point(tree, seed, clearance=0.00055):
    hit = tree.find_nearest(seed)
    if hit is None or hit[1] is None:
        raise RuntimeError("Unable to project hairline fiber")
    return hit[0] + hit[1].normalized() * clearance


def build_baby_fibers(main, tree, count=280):
    strands = []
    for index in range(count):
        rng = random.Random(24999000 + index)
        unit = ((index + 0.5) * 0.6180339887498949) % 1.0
        x = -0.090 + unit * 0.180 + rng.uniform(-0.0015, 0.0015)
        side = min(1.0, abs(x) / 0.090)
        line_z = 1.660 + 0.025 * side ** 1.55
        root_z = line_z + (rng.random() ** 1.8) * 0.015
        root = surface_point(tree, Vector((x, -0.150, root_z)))
        destination = Vector((-0.024 + rng.uniform(-0.012, 0.012), -0.125, 1.724 + rng.uniform(-0.008, 0.012)))
        reach = rng.uniform(0.24, 0.52)
        points = []
        phase = rng.uniform(0.0, math.tau)
        for step in range(10):
            t = step / 9
            path_t = reach * (t ** 0.92)
            seed = root.lerp(destination, path_t)
            seed.x += math.sin(phase + t * math.pi) * 0.0012 * math.sin(math.pi * t)
            point = surface_point(tree, seed, 0.00055 + 0.0018 * smooth((t - 0.55) / 0.45))
            points.append(point)
        strands.append(points)

    data = bpy.data.hair_curves.new(BABY_LAYER + "Data")
    data.add_curves([len(strand) for strand in strands])
    radius = data.attributes.get("radius") or data.attributes.new("radius", "FLOAT", "POINT")
    flat = 0
    for strand_index, strand in enumerate(strands):
        width = 0.000014 + (strand_index % 9) * 0.00000055
        for point_index, point in enumerate(strand):
            data.points[flat].position = point
            t = point_index / max(1, len(strand) - 1)
            radius.data[flat].value = width * (1.0 - 0.88 * t) + 0.000001
            flat += 1
    if main.data.materials:
        data.materials.append(main.data.materials[0])
    obj = bpy.data.objects.new(BABY_LAYER, data)
    bpy.context.scene.collection.objects.link(obj)
    obj["aevrynd_layer"] = "hair.hairline.baby_fibers"
    obj["aevrynd_revision"] = "v249r99"
    return obj, len(strands), len(data.points)


def bone_parent(obj, rig):
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = world


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
strength.inputs[1].default_value = 0.64
baby, baby_curves, baby_points = build_baby_fibers(main, evaluated_body_tree(bpy.data.objects[BODY]))
rig = bpy.data.objects[RIG]
bone_parent(scalp, rig)
bone_parent(baby, rig)
camera = bpy.data.objects["Aevrynd Review Camera"]
report = {
    "source": str(SOURCE), "output": str(OUTPUT),
    "scalpVertices": len(scalp.data.vertices), "scalpFaces": len(scalp.data.polygons),
    "densityRange": [minimum_density, maximum_density], "opacity": 0.64,
    "babyFiberCurves": baby_curves, "babyFiberPoints": baby_points,
    "status": "VISUAL_AND_COLLISION_REVIEW_REQUIRED",
}
for suffix, location, target, lens in (
    ("01-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
    ("02-three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88),
    ("03-profile", (0.70, -0.03, 1.61), (0.0, -0.005, 1.595), 88),
    ("04-top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
    ("05-back", (0.0, 2.10, 1.56), (0.0, 0.02, 1.54), 82),
):
    render(camera, suffix, location, target, lens)

(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_mainline_revision"] = "cc0-soft-hairline-r99"
scene["aevrynd_release_state"] = "R99_VISUAL_AND_COLLISION_REVIEW_REQUIRED"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249R99_SOFT_HAIRLINE=" + json.dumps(report, sort_keys=True))
