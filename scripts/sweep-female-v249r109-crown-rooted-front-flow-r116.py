import json
import math
import random
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-tear-meniscus-r109.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r109-crown-rooted-front-flow-r116-sweep"
BODY = "AevryndFemaleBodyBaseV118"
RIG = "AevryndFemaleRig"
MAIN = "AevryndFemaleCC0LongHairStudyMain_v249r85"
PART_X = -0.018
HAIRLINE_X = (-0.089, -0.078, -0.067, -0.056, -0.045, -0.034, -0.023, -0.011,
              0.002, 0.016, 0.030, 0.045, 0.060, 0.074, 0.086)
POINTS = 22
CLEARANCE = 0.0016
VARIANTS = (
    ("a-control", 0),
    ("b-light-12", 12),
    ("c-balanced-22", 22),
    ("d-dense-34", 34),
)


def smooth(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def cubic(p0, p1, p2, p3, t):
    u = 1.0 - t
    return p0 * u**3 + p1 * 3.0 * u * u * t + p2 * 3.0 * u * t * t + p3 * t**3


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def evaluated_tree(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, faces, all_triangles=False)


def surface_point(tree, seed, clearance=CLEARANCE):
    hit = tree.find_nearest(seed, 0.120)
    if hit is None or hit[1] is None:
        raise RuntimeError(f"could not trace scalp at {tuple(seed)}")
    return hit[0] + hit[1].normalized() * clearance


def project_clear(tree, point):
    hit = tree.find_nearest(point, 0.055)
    if hit is None or hit[1] is None:
        return point, False
    normal = hit[1].normalized()
    signed = (point - hit[0]).dot(normal)
    if signed >= CLEARANCE:
        return point, False
    return hit[0] + normal * CLEARANCE, True


def hairline_height(x):
    side = min(1.0, abs(x - PART_X) / 0.108)
    return 1.692 + 0.020 * math.sin(math.pi * side) - 0.008 * side + 0.0011 * math.sin(67.0 * x + 0.5)


def path_for(tree, guide_index, child_index, children):
    rng = random.Random(249116000 + guide_index * 1013 + child_index * 59 + children * 11)
    hairline_x = HAIRLINE_X[guide_index] + rng.uniform(-0.0026, 0.0026)
    side = -1.0 if hairline_x < PART_X else 1.0
    rank = min(1.0, abs(hairline_x - PART_X) / 0.108)
    # Roots live behind the visible edge, clustered around the part and crown.
    root_seed = Vector((
        PART_X + (hairline_x - PART_X) * (0.30 + 0.10 * rank) + rng.uniform(-0.0025, 0.0025),
        -0.012 + 0.050 * rank + rng.uniform(-0.004, 0.005),
        1.733 - 0.012 * rank + rng.uniform(-0.004, 0.005),
    ))
    root = surface_point(tree, root_seed)
    edge_seed = Vector((
        hairline_x,
        -0.151 + rng.uniform(-0.0015, 0.0020),
        hairline_height(hairline_x) + rng.uniform(-0.0015, 0.0045),
    ))
    edge = surface_point(tree, edge_seed)

    if side < 0.0:
        endpoint = Vector((
            -0.104 - rng.uniform(0.000, 0.018),
            -0.012 + rng.uniform(-0.016, 0.026),
            1.390 + rng.uniform(-0.045, 0.065) + 0.016 * rank,
        ))
    else:
        endpoint = Vector((
            0.098 + rng.uniform(0.000, 0.017),
            0.008 + rng.uniform(-0.014, 0.034),
            1.425 + rng.uniform(-0.038, 0.058) + 0.010 * rank,
        ))
    p1 = edge + Vector((side * rng.uniform(0.020, 0.032), -0.004, -rng.uniform(0.010, 0.022)))
    p2 = endpoint + Vector((-side * rng.uniform(0.005, 0.015), 0.026 + rng.uniform(-0.008, 0.012), 0.122 + rng.uniform(-0.018, 0.028)))
    phase = rng.uniform(0.0, math.tau)
    amplitude = rng.uniform(0.0007, 0.0028)
    points = []
    projected = 0
    for point_index in range(POINTS):
        t = point_index / (POINTS - 1)
        if t <= 0.54:
            surface_t = smooth(t / 0.54)
            seed = root_seed.lerp(edge_seed, surface_t)
            seed.z += math.sin(math.pi * surface_t) * rng.uniform(0.003, 0.009)
            point = surface_point(tree, seed)
        else:
            fall_t = (t - 0.54) / 0.46
            point = cubic(edge, p1, p2, endpoint, fall_t)
        envelope = smooth(t / 0.25) * math.sin(math.pi * t)
        point.x += side * math.sin(phase + t * math.pi * 1.15) * amplitude * envelope
        point.y += math.sin(phase * 0.67 + t * math.pi) * amplitude * 0.42 * envelope
        point, changed = project_clear(tree, point)
        projected += int(changed)
        points.append(point)
    return points, projected, 0 if side < 0 else 1


def make_curves(name, records, material, layer, renderable):
    data = bpy.data.hair_curves.new(name + "Data")
    data.add_curves([len(points) for points, _guide, _family in records])
    radius = data.attributes.new("radius", "FLOAT", "POINT")
    guide_id = data.attributes.new("aevrynd_guide_id", "INT", "CURVE")
    family = data.attributes.new("aevrynd_family", "INT", "CURVE")
    stiffness = data.attributes.new("aevrynd_stiffness", "FLOAT", "CURVE")
    damping = data.attributes.new("aevrynd_damping", "FLOAT", "CURVE")
    cursor = 0
    for curve_index, (points, source_guide, family_id) in enumerate(records):
        guide_id.data[curve_index].value = source_guide
        family.data[curve_index].value = family_id
        stiffness.data[curve_index].value = 0.76 if family_id == 0 else 0.82
        damping.data[curve_index].value = 0.42
        curve = data.curves[curve_index]
        for local_index, point in enumerate(points):
            data.points[curve.first_point_index + local_index].position = point
            unit = local_index / max(1, len(points) - 1)
            radius.data[cursor].value = 0.0000135 * (1.0 - unit) + 0.0000032 * unit
            cursor += 1
    if material:
        data.materials.append(material)
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.hide_render = not renderable
    obj.display_type = "WIRE" if not renderable else "TEXTURED"
    obj["aevrynd_layer"] = layer
    obj["aevrynd_revision"] = "v249r116-sweep"
    obj["aevrynd_asset_schema"] = "aevrynd.hair-guide-follow.v1"
    world = obj.matrix_world.copy()
    rig = bpy.data.objects[RIG]
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = world
    return obj


def build_layers(tree, main, children):
    guides = []
    follows = []
    projected = 0
    for guide_index in range(len(HAIRLINE_X)):
        points, count, family = path_for(tree, guide_index, 0, max(children, 1))
        guides.append((points, guide_index, family))
        projected += count
        for child_index in range(children):
            points, count, family = path_for(tree, guide_index, child_index + 1, children)
            follows.append((points, guide_index, family))
            projected += count
    material = main.data.materials[0] if main.data.materials else None
    guide_obj = make_curves(
        "AevryndFemaleCrownRootedFrontGuides_v249r116", guides, material,
        "hair.guides.crown_rooted_front", False,
    )
    follow_obj = make_curves(
        "AevryndFemaleCrownRootedFrontFollow_v249r116", follows, material,
        "hair.follow.crown_rooted_front", True,
    )
    return guide_obj, follow_obj, projected


def render(camera, name, location, target, lens):
    scene = bpy.context.scene
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


OUT.mkdir(parents=True, exist_ok=True)
report = {"source": str(SOURCE), "guideCount": len(HAIRLINE_X), "variants": []}
for name, children in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    guides = follows = None
    projected = 0
    if children:
        guides, follows, projected = build_layers(
            evaluated_tree(bpy.data.objects[BODY]), bpy.data.objects[MAIN], children,
        )
    camera = bpy.data.objects["Aevrynd Review Camera"]
    for suffix, location, target, lens in (
        ("01-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
        ("02-three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88),
        ("03-top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
    ):
        render(camera, f"{name}-{suffix}", location, target, lens)
    report["variants"].append({
        "name": name,
        "childrenPerGuide": children,
        "guideCurves": len(guides.data.curves) if guides else 0,
        "followCurves": len(follows.data.curves) if follows else 0,
        "followPoints": len(follows.data.points) if follows else 0,
        "collisionProjectedPoints": projected,
    })

(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_CROWN_ROOTED_FRONT_FLOW_R116=" + json.dumps(report, sort_keys=True))
