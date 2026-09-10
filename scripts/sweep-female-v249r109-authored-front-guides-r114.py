import json
import math
import random
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-tear-meniscus-r109.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r109-authored-front-guides-r114-sweep"
BODY = "AevryndFemaleBodyBaseV118"
RIG = "AevryndFemaleRig"
MAIN = "AevryndFemaleCC0LongHairStudyMain_v249r85"
GUIDE_X = (-0.089, -0.079, -0.070, -0.060, -0.049, -0.037, -0.025, -0.014,
           -0.002, 0.011, 0.024, 0.038, 0.053, 0.067, 0.080, 0.090)
PART_X = -0.018
POINTS = 20
CLEARANCE = 0.0015
VARIANTS = (
    ("a-control", 0),
    ("b-light-14", 14),
    ("c-balanced-24", 24),
    ("d-dense-36", 36),
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


def hairline_height(x):
    side = min(1.0, abs(x - PART_X) / 0.105)
    # Adult hairline: a slightly lower central point, a higher frontal arch,
    # then a controlled descent into the temples.  This is deliberately above
    # the r101 optical scalp-mask fade, which is not the anatomical root line.
    return 1.692 + 0.020 * math.sin(math.pi * side) - 0.008 * side + 0.0012 * math.sin(71.0 * x + 0.8)


def scalp_root(tree, x, vertical_offset=0.0, forward_offset=0.0):
    seed = Vector((x, -0.150 + forward_offset, hairline_height(x) + vertical_offset))
    hit = tree.find_nearest(seed, 0.100)
    if hit is None or hit[1] is None:
        raise RuntimeError(f"could not place authored guide root at {tuple(seed)}")
    return hit[0] + hit[1].normalized() * CLEARANCE


def project_clear(tree, point):
    hit = tree.find_nearest(point, 0.050)
    if hit is None or hit[1] is None:
        return point, False
    normal = hit[1].normalized()
    signed = (point - hit[0]).dot(normal)
    if signed >= CLEARANCE:
        return point, False
    return hit[0] + normal * CLEARANCE, True


def surface_point(tree, seed):
    hit = tree.find_nearest(seed, 0.110)
    if hit is None or hit[1] is None:
        raise RuntimeError(f"could not trace scalp surface at {tuple(seed)}")
    return hit[0] + hit[1].normalized() * CLEARANCE


def path_for(tree, guide_index, child_index, children):
    rng = random.Random(249114000 + guide_index * 1009 + child_index * 53 + children * 7)
    base_x = GUIDE_X[guide_index]
    side = -1.0 if base_x < PART_X else 1.0
    rank = abs(base_x - PART_X) / 0.108
    root_x = base_x + rng.uniform(-0.0026, 0.0026)
    root = scalp_root(
        tree, root_x,
        rng.uniform(-0.0018, 0.0065),
        rng.uniform(-0.0015, 0.0020),
    )
    # The heavier left side falls lower; the light side turns behind the ear.
    if side < 0.0:
        end_x = -0.101 - rng.uniform(0.000, 0.018)
        end_y = -0.020 + rng.uniform(-0.018, 0.022)
        end_z = 1.390 + rng.uniform(-0.045, 0.060) + 0.018 * rank
        sweep = 0.014 + 0.010 * (1.0 - rank)
    else:
        end_x = 0.096 + rng.uniform(0.000, 0.016)
        end_y = 0.005 + rng.uniform(-0.012, 0.034)
        end_z = 1.425 + rng.uniform(-0.035, 0.055) + 0.012 * rank
        sweep = 0.010 + 0.008 * (1.0 - rank)
    endpoint = Vector((end_x, end_y, end_z))
    crown_seed = Vector((
        side * (0.045 + 0.030 * rank) + rng.uniform(-0.003, 0.003),
        -0.014 + 0.022 * rank + rng.uniform(-0.004, 0.004),
        1.733 - 0.013 * rank + rng.uniform(-0.004, 0.005),
    ))
    crown = surface_point(tree, crown_seed)
    p1 = crown + Vector((side * (0.020 + 0.010 * rank), 0.020, -0.006))
    p2 = endpoint + Vector((-side * rng.uniform(0.005, 0.014), 0.032 + rng.uniform(-0.008, 0.010), 0.130 + rng.uniform(-0.018, 0.025)))
    phase = rng.uniform(0.0, math.tau)
    amplitude = rng.uniform(0.0008, 0.0032)
    points = []
    projected = 0
    for point_index in range(POINTS):
        t = point_index / (POINTS - 1)
        if t <= 0.48:
            scalp_t = smooth(t / 0.48)
            seed = root.lerp(crown_seed, scalp_t)
            seed.z += math.sin(math.pi * scalp_t) * (0.010 + 0.006 * (1.0 - rank))
            point = surface_point(tree, seed)
        else:
            fall_t = (t - 0.48) / 0.52
            point = cubic(crown, p1, p2, endpoint, fall_t)
        # Children share a broad guide flow but retain different phase, length,
        # and lateral response.  Noise fades at the root to preserve attachment.
        envelope = smooth(t / 0.22) * math.sin(math.pi * t)
        point.x += side * math.sin(phase + t * math.pi * 1.35) * amplitude * envelope
        point.y += math.sin(phase * 0.63 + t * math.pi) * amplitude * 0.48 * envelope
        point, changed = project_clear(tree, point)
        projected += int(changed)
        points.append(point)
    return points, projected


def make_curves(name, records, material, layer, renderable):
    data = bpy.data.hair_curves.new(name + "Data")
    data.add_curves([len(points) for points, _guide_id, _family in records])
    radius = data.attributes.new("radius", "FLOAT", "POINT")
    guide_id = data.attributes.new("aevrynd_guide_id", "INT", "CURVE")
    family = data.attributes.new("aevrynd_family", "INT", "CURVE")
    stiffness = data.attributes.new("aevrynd_stiffness", "FLOAT", "CURVE")
    damping = data.attributes.new("aevrynd_damping", "FLOAT", "CURVE")
    cursor = 0
    for curve_index, (points, source_guide, family_id) in enumerate(records):
        guide_id.data[curve_index].value = source_guide
        family.data[curve_index].value = family_id
        stiffness.data[curve_index].value = 0.72 if family_id == 0 else 0.78
        damping.data[curve_index].value = 0.40
        curve = data.curves[curve_index]
        for local_index, point in enumerate(points):
            data.points[curve.first_point_index + local_index].position = point
            unit = local_index / max(1, len(points) - 1)
            radius.data[cursor].value = 0.0000145 * (1.0 - unit) + 0.0000035 * unit
            cursor += 1
    if material:
        data.materials.append(material)
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.hide_render = not renderable
    obj.hide_viewport = False
    obj.display_type = "WIRE" if not renderable else "TEXTURED"
    obj["aevrynd_layer"] = layer
    obj["aevrynd_revision"] = "v249r114-sweep"
    obj["aevrynd_asset_schema"] = "aevrynd.hair-guide-follow.v1"
    world = obj.matrix_world.copy()
    rig = bpy.data.objects[RIG]
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = world
    return obj


def build_layers(tree, main, children):
    guide_records = []
    follow_records = []
    projected = 0
    for guide_index in range(len(GUIDE_X)):
        guide_points, guide_projected = path_for(tree, guide_index, 0, max(children, 1))
        family_id = 0 if GUIDE_X[guide_index] < PART_X else 1
        guide_records.append((guide_points, guide_index, family_id))
        projected += guide_projected
        for child_index in range(children):
            points, child_projected = path_for(tree, guide_index, child_index + 1, children)
            follow_records.append((points, guide_index, family_id))
            projected += child_projected
    material = main.data.materials[0] if main.data.materials else None
    guide = make_curves(
        "AevryndFemaleAuthoredFrontGuides_v249r114", guide_records, material,
        "hair.guides.front_frame", False,
    )
    follow = make_curves(
        "AevryndFemaleAuthoredFrontFollow_v249r114", follow_records, material,
        "hair.follow.front_frame", True,
    )
    return guide, follow, projected


def render(camera, name, location, target, lens):
    scene = bpy.context.scene
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


OUT.mkdir(parents=True, exist_ok=True)
report = {"source": str(SOURCE), "guideCount": len(GUIDE_X), "variants": []}
for name, children in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    guide = follow = None
    projected = 0
    if children:
        guide, follow, projected = build_layers(
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
        "guideCurves": len(guide.data.curves) if guide else 0,
        "followCurves": len(follow.data.curves) if follow else 0,
        "followPoints": len(follow.data.points) if follow else 0,
        "collisionProjectedPoints": projected,
    })

(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_AUTHORED_FRONT_GUIDES_R114=" + json.dumps(report, sort_keys=True))
