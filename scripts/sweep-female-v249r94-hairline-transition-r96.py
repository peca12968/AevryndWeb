import json
import math
import random
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cc0-natural-long-hair-r94.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r94-hairline-transition-r96-sweep"
MAIN = "AevryndFemaleCC0LongHairStudyMain_v249r85"
BODY = "AevryndFemaleBodyBaseV118"
LAYER = "AevryndFemaleHairlineTransitionSweep_v249r96"
TARGET = 0.0015


def smooth(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def body_tree(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, faces, all_triangles=False)


def project_clear(tree, point):
    hit = tree.find_nearest(point)
    if hit is None or hit[1] is None or hit[3] > 0.035:
        return point
    normal = hit[1].normalized()
    signed = (point - hit[0]).dot(normal)
    return point if signed >= TARGET else hit[0] + normal * TARGET


def source_records(obj):
    records = []
    for curve in obj.data.curves:
        points = [
            obj.matrix_world @ obj.data.points[curve.first_point_index + index].position
            for index in range(curve.points_length)
        ]
        if len(points) >= 4 and points[0].y <= -0.055:
            records.append(points)
    return records


def target_root(tree, rng, index, count):
    unit = ((index + 0.5) * 0.6180339887498949) % 1.0
    x = -0.088 + 0.176 * unit + rng.uniform(-0.0018, 0.0018)
    side = min(1.0, abs(x) / 0.088)
    line_z = 1.684 + 0.028 * (1.0 - side ** 1.45)
    band = (rng.random() ** 1.35) * 0.038
    z = line_z + band + rng.uniform(-0.0015, 0.0015)
    seed = Vector((x, -0.150, z))
    hit = tree.find_nearest(seed)
    if hit is None or hit[1] is None:
        raise RuntimeError("Unable to project hairline root")
    return hit[0] + hit[1].normalized() * TARGET


def create_layer(count, main, tree, records):
    old = bpy.data.objects.get(LAYER)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    index = KDTree(len(records))
    for record_index, points in enumerate(records):
        index.insert(points[0], record_index)
    index.balance()
    strands = []
    maximum_shift = 0.0
    for strand_index in range(count):
        rng = random.Random(24996000 + count * 17 + strand_index)
        root = target_root(tree, rng, strand_index, count)
        nearest = list(index.find_n(root, 14))
        _, record_index, _ = nearest[rng.randrange(min(8, len(nearest)))]
        source = records[record_index]
        delta = root - source[0]
        maximum_shift = max(maximum_shift, delta.length)
        strand = []
        lateral_phase = rng.uniform(0.0, math.tau)
        for point_index, point in enumerate(source):
            t = point_index / max(1, len(source) - 1)
            blend = 1.0 - smooth(t / 0.32)
            candidate = point + delta * blend
            if 0.0 < t < 0.65:
                candidate.x += math.sin(lateral_phase + t * math.tau) * 0.00045 * math.sin(math.pi * t)
            strand.append(project_clear(tree, candidate))
        strands.append(strand)

    data = bpy.data.hair_curves.new(LAYER + "Data")
    data.add_curves([len(strand) for strand in strands])
    radius = data.attributes.get("radius") or data.attributes.new("radius", "FLOAT", "POINT")
    flat = 0
    for strand_index, strand in enumerate(strands):
        width = 0.000020 + (strand_index % 7) * 0.0000007
        for point_index, point in enumerate(strand):
            data.points[flat].position = point
            t = point_index / max(1, len(strand) - 1)
            radius.data[flat].value = width * (1.0 - 0.76 * t) + 0.000002
            flat += 1
    if main.data.materials:
        data.materials.append(main.data.materials[0])
    obj = bpy.data.objects.new(LAYER, data)
    bpy.context.scene.collection.objects.link(obj)
    obj["aevrynd_layer"] = "hair.hairline.transition"
    obj["aevrynd_revision"] = "v249r96-density-sweep"
    return obj, maximum_shift, len(data.points)


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
camera = bpy.data.objects["Aevrynd Review Camera"]
main = bpy.data.objects[MAIN]
tree = body_tree(bpy.data.objects[BODY])
records = source_records(main)
report = {"source": str(SOURCE), "eligibleSourceCurves": len(records), "variants": []}
for count in (320, 640, 960):
    _, maximum_shift, points = create_layer(count, main, tree, records)
    for suffix, location, target, lens in (
        ("front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
        ("three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88),
        ("top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
    ):
        render(camera, f"{count:04d}-{suffix}", location, target, lens)
    report["variants"].append({"curves": count, "points": points, "maximumRootShiftM": maximum_shift})

(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R96_HAIRLINE_SWEEP=" + json.dumps(report, sort_keys=True))
