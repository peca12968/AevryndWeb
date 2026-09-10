import bisect
import json
import math
import random
from pathlib import Path

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-tear-meniscus-r109.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r109-directional-root-undercoat-r121-sweep"
BODY = "AevryndFemaleBodyBaseV118"
RIG = "AevryndFemaleRig"
SCALP = "AevryndFemaleAnatomicalScalpFoundation_v249r101"
MAIN = "AevryndFemaleCC0LongHairStudyMain_v249r85"
DENSITY_ATTRIBUTE = "aevrynd_root_density"
CLEARANCE = 0.0009
POINTS = 7
VARIANTS = (
    ("a-control", 0),
    ("b-light-600", 600),
    ("c-balanced-1200", 1200),
    ("d-dense-2000", 2000),
)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def evaluated_tree(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, faces, all_triangles=False)


def project_clear(tree, point):
    hit = tree.find_nearest(point, 0.030)
    if hit is None or hit[1] is None:
        return point, False
    normal = hit[1].normalized()
    signed = (point - hit[0]).dot(normal)
    if signed >= CLEARANCE:
        return point, False
    return hit[0] + normal * CLEARANCE, True


def main_root_index(main):
    roots = []
    tangents = []
    tree = KDTree(len(main.data.curves))
    matrix = main.matrix_world
    for curve_index, curve in enumerate(main.data.curves):
        first = curve.first_point_index
        last = first + curve.points_length - 1
        sample = min(last, first + 2)
        root = matrix @ main.data.points[first].position
        tangent = matrix.to_3x3() @ (main.data.points[sample].position - main.data.points[first].position)
        if tangent.length_squared < 1.0e-12:
            tangent = Vector((1.0 if root.x >= 0.0 else -1.0, 0.0, -0.1))
        tangent.normalize()
        roots.append(root)
        tangents.append(tangent)
        tree.insert(root, curve_index)
    tree.balance()
    return tree, roots, tangents


def triangle_sampler(scalp):
    mesh = scalp.data
    mesh.calc_loop_triangles()
    density = mesh.attributes[DENSITY_ATTRIBUTE].data
    matrix = scalp.matrix_world
    normal_matrix = matrix.to_3x3()
    records = []
    cumulative = []
    total = 0.0
    for triangle in mesh.loop_triangles:
        ids = triangle.vertices
        a, b, c = (matrix @ mesh.vertices[index].co for index in ids)
        area = (b - a).cross(c - a).length * 0.5
        weights = [float(density[index].value) for index in ids]
        mean_density = sum(weights) / 3.0
        importance = area * max(0.0, mean_density) ** 1.35
        if importance <= 1.0e-12:
            continue
        normal = normal_matrix @ triangle.normal
        normal.normalize()
        total += importance
        records.append((a, b, c, weights, normal))
        cumulative.append(total)
    return records, cumulative, total


def sample_root(rng, records, cumulative, total):
    record = records[bisect.bisect_left(cumulative, rng.random() * total)]
    a, b, c, densities, normal = record
    u = rng.random()
    v = rng.random()
    if u + v > 1.0:
        u = 1.0 - u
        v = 1.0 - v
    w = 1.0 - u - v
    root = a * w + b * u + c * v
    root_density = densities[0] * w + densities[1] * u + densities[2] * v
    return root, normal, root_density


def build_undercoat(body_tree, scalp, main, count):
    rng = random.Random(249121000 + count * 17)
    records, cumulative, total = triangle_sampler(scalp)
    root_tree, _roots, tangents = main_root_index(main)
    fibers = []
    projected = 0
    lengths = []
    for fiber_index in range(count):
        root, normal, root_density = sample_root(rng, records, cumulative, total)
        _co, nearest_index, _distance = root_tree.find(root)
        tangent = tangents[nearest_index].copy()
        tangent -= normal * tangent.dot(normal)
        if tangent.length_squared < 1.0e-10:
            tangent = Vector((1.0 if root.x >= -0.018 else -1.0, -0.2, -0.1))
            tangent -= normal * tangent.dot(normal)
        tangent.normalize()
        jitter_axis = normal.cross(tangent).normalized()
        tangent = Matrix.Rotation(rng.uniform(-0.10, 0.10), 4, jitter_axis) @ tangent
        length = rng.uniform(0.0040, 0.0120) * (0.78 + 0.30 * root_density)
        lengths.append(length)
        phase = rng.uniform(0.0, math.tau)
        points = []
        for point_index in range(POINTS):
            unit = point_index / (POINTS - 1)
            point = root + tangent * (length * unit)
            point += normal * (0.00045 + 0.00075 * math.sin(math.pi * unit) + 0.00020 * unit)
            point += jitter_axis * math.sin(phase + unit * math.pi) * 0.00018 * math.sin(math.pi * unit)
            point, changed = project_clear(body_tree, point)
            projected += int(changed)
            points.append(point)
        fibers.append((points, nearest_index, root_density))
    return fibers, projected, lengths


def make_curves(records, material):
    data = bpy.data.hair_curves.new("AevryndFemaleDirectionalRootUndercoat_v249r121Data")
    data.add_curves([len(points) for points, _source, _density in records])
    radius = data.attributes.new("radius", "FLOAT", "POINT")
    source = data.attributes.new("aevrynd_source_curve", "INT", "CURVE")
    density = data.attributes.new("aevrynd_root_density", "FLOAT", "CURVE")
    stiffness = data.attributes.new("aevrynd_stiffness", "FLOAT", "CURVE")
    damping = data.attributes.new("aevrynd_damping", "FLOAT", "CURVE")
    cursor = 0
    for curve_index, (points, source_index, root_density) in enumerate(records):
        source.data[curve_index].value = source_index
        density.data[curve_index].value = root_density
        stiffness.data[curve_index].value = 0.96
        damping.data[curve_index].value = 0.64
        curve = data.curves[curve_index]
        for local_index, point in enumerate(points):
            data.points[curve.first_point_index + local_index].position = point
            unit = local_index / (len(points) - 1)
            radius.data[cursor].value = 0.0000060 * (1.0 - unit) + 0.0000012 * unit
            cursor += 1
    data.materials.append(material)
    obj = bpy.data.objects.new("AevryndFemaleDirectionalRootUndercoat_v249r121", data)
    bpy.context.scene.collection.objects.link(obj)
    obj["aevrynd_layer"] = "hair.root_undercoat.directional"
    obj["aevrynd_revision"] = "v249r121-sweep"
    obj["aevrynd_asset_schema"] = "aevrynd.hair-root-undercoat.v1"
    world = obj.matrix_world.copy()
    rig = bpy.data.objects[RIG]
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = world
    return obj


def render(camera, name, location, target, lens):
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    bpy.context.scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


OUT.mkdir(parents=True, exist_ok=True)
report = {"source": str(SOURCE), "variants": []}
for name, count in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    projected = 0
    lengths = []
    obj = None
    if count:
        fibers, projected, lengths = build_undercoat(
            evaluated_tree(bpy.data.objects[BODY]),
            bpy.data.objects[SCALP],
            bpy.data.objects[MAIN],
            count,
        )
        main = bpy.data.objects[MAIN]
        obj = make_curves(fibers, main.data.materials[0])
    camera = bpy.data.objects["Aevrynd Review Camera"]
    for suffix, location, target, lens in (
        ("01-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
        ("02-three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88),
        ("03-top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
    ):
        render(camera, f"{name}-{suffix}", location, target, lens)
    report["variants"].append({
        "name": name,
        "fibers": len(obj.data.curves) if obj else 0,
        "points": len(obj.data.points) if obj else 0,
        "collisionProjectedPoints": projected,
        "minimumLengthMm": min(lengths) * 1000.0 if lengths else 0.0,
        "maximumLengthMm": max(lengths) * 1000.0 if lengths else 0.0,
    })

(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_DIRECTIONAL_ROOT_UNDERCOAT_R121=" + json.dumps(report, sort_keys=True))
