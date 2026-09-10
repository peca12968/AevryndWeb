import bisect
import json
import math
import random
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.kdtree import KDTree


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "assets-source/reference/blender-official-hair/hair_nodes-female_hair_styles.blend"
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-owned-hair-material-r129.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-owned-hybrid-guides-r146.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r129-owned-hybrid-guides-r146"
TARGET_SCALP = "AevryndFemaleAnatomicalScalpFoundation_v249r101"
TARGET_MATERIAL = "AevryndOwnedLayeredHairMaterial_v249r129"
SAMPLES = 22
FOLLOWERS_PER_GUIDE = 75
CLUMPS_PER_GUIDE = 4
FLYAWAY_COUNT = 100
SEED = 249146


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def object_bounds(obj):
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return (
        Vector(tuple(min(p[i] for p in points) for i in range(3))),
        Vector(tuple(max(p[i] for p in points) for i in range(3))),
    )


def raw_curves(name):
    obj = bpy.data.objects[name]
    curves = []
    for curve in obj.data.curves:
        start = curve.first_point_index
        curves.append([obj.matrix_world @ obj.data.points[start + i].position for i in range(curve.points_length)])
    return curves


def normalized_root(point, bounds):
    minimum, maximum = bounds
    size = maximum - minimum
    return Vector(((point.x - minimum.x) / size.x, (point.y - minimum.y) / size.y, (point.z - minimum.z) / size.z))


def transform_point(point, source_bounds, target_bounds):
    source_min, source_max = source_bounds
    target_min, target_max = target_bounds
    source_center = (source_min + source_max) * 0.5
    target_center = (target_min + target_max) * 0.5
    scale = Vector(tuple((target_max[i] - target_min[i]) / (source_max[i] - source_min[i]) for i in range(3)))
    delta = point - source_center
    return target_center + Vector((delta.x * scale.x, delta.y * scale.y, delta.z * scale.z))


def resample_polyline(points, count):
    if len(points) == 1:
        return [points[0].copy() for _ in range(count)]
    lengths = [(points[i + 1] - points[i]).length for i in range(len(points) - 1)]
    total = sum(lengths)
    cumulative = [0.0]
    for length in lengths:
        cumulative.append(cumulative[-1] + length)
    result = []
    segment = 0
    for sample in range(count):
        distance = total * sample / max(1, count - 1)
        while segment + 1 < len(cumulative) - 1 and cumulative[segment + 1] < distance:
            segment += 1
        span = max(1e-12, cumulative[segment + 1] - cumulative[segment])
        result.append(points[segment].lerp(points[segment + 1], (distance - cumulative[segment]) / span))
    return result


def scalp_surface_distribution(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    mesh.calc_loop_triangles()
    matrix = evaluated.matrix_world
    normal_matrix = matrix.to_3x3().inverted().transposed()
    vertices = [matrix @ vertex.co for vertex in mesh.vertices]
    normals = [(normal_matrix @ vertex.normal).normalized() for vertex in mesh.vertices]
    density_attr = mesh.attributes.get("aevrynd_root_density")
    densities = [density_attr.data[i].value for i in range(len(mesh.vertices))] if density_attr and density_attr.domain == "POINT" else [1.0] * len(mesh.vertices)
    triangles = []
    cumulative = []
    total = 0.0
    for triangle in mesh.loop_triangles:
        indices = tuple(triangle.vertices)
        a, b, c = (vertices[i] for i in indices)
        area = (b - a).cross(c - a).length * 0.5
        density = max(0.0, sum(densities[i] for i in indices) / 3.0)
        weight = area * density
        if weight <= 1e-12:
            continue
        triangles.append((indices, a, b, c))
        total += weight
        cumulative.append(total)
    evaluated.to_mesh_clear()
    return {"triangles": triangles, "cumulative": cumulative, "total": total, "normals": normals}


def sample_surface(distribution, rng):
    index = bisect.bisect_left(distribution["cumulative"], rng.random() * distribution["total"])
    indices, a, b, c = distribution["triangles"][min(index, len(distribution["triangles"]) - 1)]
    su = math.sqrt(rng.random())
    v = rng.random()
    wa, wb, wc = 1.0 - su, su * (1.0 - v), su * v
    point = a * wa + b * wb + c * wc
    normals = distribution["normals"]
    normal = (normals[indices[0]] * wa + normals[indices[1]] * wb + normals[indices[2]] * wc).normalized()
    return point + normal * 0.00075, normal


def narrow_part(root, center_x):
    dx = root.x - center_x
    influence = max(0.0, 1.0 - abs(dx) / 0.040)
    shift = min(abs(dx) * 0.55, 0.0045 * influence)
    root.x -= math.copysign(shift, dx) if abs(dx) > 1e-9 else 0.0
    return root


def hermite(p0, p1, m0, m1, t):
    t2, t3 = t * t, t * t * t
    return p0 * (2 * t3 - 3 * t2 + 1) + m0 * (t3 - 2 * t2 + t) + p1 * (-2 * t3 + 3 * t2) + m1 * (t3 - t2)


def build_hybrid_guides(braid_curves, braid_bounds, long_curves, long_bounds, target_bounds):
    long_roots = [normalized_root(curve[0], long_bounds) for curve in long_curves]
    target_center_x = (target_bounds[0].x + target_bounds[1].x) * 0.5
    guides = []
    mappings = []
    for braid_index, braid in enumerate(braid_curves):
        root_uv = normalized_root(braid[0], braid_bounds)
        long_index = min(range(len(long_curves)), key=lambda i: (long_roots[i].x - root_uv.x) ** 2 + (long_roots[i].y - root_uv.y) ** 2)
        long_path = [transform_point(point, long_bounds, target_bounds) for point in resample_polyline(long_curves[long_index], SAMPLES)]
        root = narrow_part(transform_point(braid[0], braid_bounds, target_bounds), target_center_x)
        second = transform_point(braid[min(2, len(braid) - 1)], braid_bounds, target_bounds)
        braid_tangent = (second - transform_point(braid[0], braid_bounds, target_bounds)).normalized()
        delta = root - long_path[0]
        shifted = [point + delta * ((1.0 - i / (SAMPLES - 1)) ** 2) for i, point in enumerate(long_path)]
        join = 8
        anchor = shifted[join]
        anchor_tangent = (shifted[join + 1] - shifted[join - 1]).normalized()
        distance = (anchor - root).length
        guide = []
        for i in range(SAMPLES):
            if i <= join:
                t = i / join
                guide.append(hermite(root, anchor, braid_tangent * distance * 0.78, anchor_tangent * distance * 0.55, t))
            else:
                guide.append(shifted[i])
        guides.append(guide)
        mappings.append({"braidGuide": braid_index, "longGuide": long_index})
    return guides, mappings


def make_curve_object(name, curves, material, layer, root_radius, tip_radius, visible=True):
    data = bpy.data.hair_curves.new(name + "Data")
    data.add_curves([len(curve) for curve in curves])
    index = 0
    for curve in curves:
        for point in curve:
            data.points[index].position = point
            index += 1
    radius = data.attributes.new("radius", "FLOAT", "POINT")
    for curve in data.curves:
        for local_index in range(curve.points_length):
            t = local_index / max(1, curve.points_length - 1)
            radius.data[curve.first_point_index + local_index].value = root_radius * (1.0 - t) + tip_radius * t
    family = data.attributes.new("aevrynd_family_id", "INT", "CURVE")
    for i in range(len(data.curves)):
        family.data[i].value = i
    if material:
        data.materials.append(material)
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.hide_render = not visible
    obj["aevrynd_layer"] = layer
    obj["aevrynd_revision"] = "v249-mainline-owned-hybrid-guides-r146"
    obj["aevrynd_source"] = "Aevrynd-owned generated geometry; root-flow reference derived offline from Blender CC0 guides"
    obj["aevrynd_runtime_dependency"] = "none"
    return obj


def generate_followers(guides, distribution, count, rng, kind):
    result = []
    roots = [guide[0] for guide in guides]
    tree = KDTree(len(roots))
    for index, root in enumerate(roots):
        tree.insert(root, index)
    tree.balance()
    for _ in range(count):
        root, normal = sample_surface(distribution, rng)
        neighbors = list(tree.find_n(root, 3))
        inverse = [1.0 / max(1e-6, distance) for _, _, distance in neighbors]
        weight_sum = sum(inverse)
        weights = [value / weight_sum for value in inverse]
        guide = []
        for point_index in range(len(guides[0])):
            relative = Vector((0.0, 0.0, 0.0))
            for weight, (_, guide_index, _) in zip(weights, neighbors):
                relative += (guides[guide_index][point_index] - guides[guide_index][0]) * weight
            guide.append(root + relative)
        tangent = (guide[2] - guide[0]).normalized()
        side = tangent.cross(normal)
        if side.length < 1e-6:
            side = Vector((1.0, 0.0, 0.0))
        side.normalize()
        phase = rng.random() * math.tau
        frequency = rng.uniform(0.65, 1.25)
        wave_amp = rng.uniform(0.0005, 0.0018) if kind == "follow" else rng.uniform(0.0010, 0.0030)
        end_spread = side * rng.uniform(-0.016, 0.016)
        vertical_spread = Vector((0.0, 0.0, rng.uniform(-0.010, 0.008)))
        curve = []
        for i, point in enumerate(guide):
            t = i / (len(guide) - 1)
            offset = side * (math.sin(phase + t * math.tau * frequency) * wave_amp * math.sin(math.pi * t))
            offset += (end_spread + vertical_spread) * (t ** 2.2)
            curve.append(point + offset)
        result.append(curve)
    return result


def generate_flyaways(guides, rng, count):
    result = []
    for _ in range(count):
        guide = guides[rng.randrange(len(guides))]
        length = rng.randint(10, 18)
        side = Vector((rng.uniform(-1.0, 1.0), rng.uniform(-1.0, 1.0), rng.uniform(-0.2, 0.8))).normalized()
        curve = []
        for i in range(length):
            t = i / (length - 1)
            source_t = min(1.0, t * rng.uniform(0.35, 0.85))
            source_index = min(len(guide) - 1, int(source_t * (len(guide) - 1)))
            curve.append(guide[source_index] + side * (0.002 + 0.020 * t * t))
        result.append(curve)
    return result


def is_hair_layer(obj):
    layer = str(obj.get("aevrynd_layer", ""))
    name = obj.name.lower()
    return layer.startswith("hair.") or any(token in name for token in ("hair", "groom", "scalp"))


def render(camera, name, location, target, lens):
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    bpy.context.scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(REFERENCE))
braid_bounds = object_bounds(bpy.data.objects["Braids growth mesh"])
long_bounds = object_bounds(bpy.data.objects["long hair growth mesh"])
braid_curves = raw_curves("braided hair")
long_curves = raw_curves("long hair main")

bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
OUT.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
scene.frame_set(1)
scalp = bpy.data.objects[TARGET_SCALP]
target_bounds = object_bounds(scalp)
distribution = scalp_surface_distribution(scalp)
guides, mappings = build_hybrid_guides(braid_curves, braid_bounds, long_curves, long_bounds, target_bounds)
rng = random.Random(SEED)
followers = generate_followers(guides, distribution, FOLLOWERS_PER_GUIDE * len(guides), rng, "follow")
clumps = generate_followers(guides, distribution, CLUMPS_PER_GUIDE * len(guides), rng, "clump")
flyaways = generate_flyaways(guides, rng, FLYAWAY_COUNT)

for obj in bpy.data.objects:
    if is_hair_layer(obj):
        obj.hide_render = True
        obj.hide_viewport = True
material = bpy.data.materials[TARGET_MATERIAL]
guide_obj = make_curve_object("AevryndFemaleOwnedHairGuides_v249r146", guides, material, "hair.guides.primary", 0.000028, 0.000008, False)
follow_obj = make_curve_object("AevryndFemaleOwnedHairFollow_v249r146", followers, material, "hair.follow.family", 0.000034, 0.000008, True)
clump_obj = make_curve_object("AevryndFemaleOwnedHairClump_v249r146", clumps, material, "hair.clump.structure", 0.000042, 0.000010, True)
fly_obj = make_curve_object("AevryndFemaleOwnedHairFlyaway_v249r146", flyaways, material, "hair.flyaway.independent", 0.000025, 0.000006, True)
rig = bpy.data.objects.get("AevryndFemaleRig")
for obj in (guide_obj, follow_obj, clump_obj, fly_obj):
    if rig:
        world = obj.matrix_world.copy()
        obj.parent = rig
        obj.matrix_parent_inverse = rig.matrix_world.inverted()
        obj.matrix_world = world

scalp.hide_render = False
scalp.hide_viewport = False
scene["aevrynd_mainline_revision"] = "owned-hybrid-guides-r146"
scene["aevrynd_release_state"] = "R146_VISUAL_STUDY_ONLY"
scene["aevrynd_runtime_dependency"] = "none"
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
camera = bpy.data.objects["Aevrynd Review Camera"]
views = (
    ("01-front", (0.0, -2.15, 1.55), (0.0, 0.0, 1.55), 82),
    ("02-three-quarter", (1.28, -1.72, 1.57), (0.0, 0.0, 1.55), 82),
    ("03-profile", (2.15, 0.0, 1.57), (0.0, 0.0, 1.55), 86),
    ("04-back", (0.0, 2.10, 1.56), (0.0, 0.02, 1.54), 82),
    ("05-top", (0.0, -0.30, 2.35), (0.0, 0.0, 1.66), 78),
    ("06-face-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
)
for args in views:
    render(camera, *args)

report = {
    "reference": str(REFERENCE),
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "license": "CC0 reference; generated geometry is Aevrynd-owned",
    "runtimeDependency": "none",
    "seed": SEED,
    "layers": {
        "guides": {"curves": len(guides), "points": sum(len(c) for c in guides), "rendered": False},
        "follow": {"curves": len(followers), "points": sum(len(c) for c in followers)},
        "clump": {"curves": len(clumps), "points": sum(len(c) for c in clumps)},
        "flyaway": {"curves": len(flyaways), "points": sum(len(c) for c in flyaways)},
    },
    "mappingCount": len(mappings),
    "status": "STRICT_VISUAL_REVIEW_REQUIRED",
}
(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249R129_OWNED_HYBRID_GUIDES_R146=" + json.dumps(report, sort_keys=True))
