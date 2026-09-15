import json
import math
from pathlib import Path

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-orbital-brow-refit-r526.blend"
OUT = ASSETS / "reviews/v249r534-owned-scalp-guide-groom-sweep"
REPORT = ASSETS / "female-v249-mainline-owned-scalp-guide-groom-r534.study.json"
BODY = "AevryndFemaleBodyBaseV118"
RIG = "AevryndFemaleRig"
POINTS = 24
CLEARANCE = 0.0020
VISIBLE_LONG_HAIR = (
    "AevryndFemaleRuntimeCards_crown_R467",
    "AevryndFemaleRuntimeCards_hairline_R467",
    "AevryndFemaleRuntimeLayeredLocks_front_R517",
    "AevryndFemaleRuntimeLayeredLocks_rear_R506",
)
VARIANTS = (
    ("a-r526-current", None),
    ("b-owned-scalp-24", 24),
    ("c-owned-scalp-40", 40),
    ("d-owned-scalp-56", 56),
)


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def smoothstep(value):
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def rand(index, salt=0.0):
    return (math.sin(index * 12.9898 + salt * 78.233) * 43758.5453) % 1.0


def part_x(y):
    # An asymmetric part that closes before the rear crown.
    return -0.021 + 0.017 * smoothstep((y + 0.105) / 0.155)


def natural_hairline_z(x):
    absolute_x = abs(x)
    center_peak = -0.009 * math.exp(-((x / 0.019) ** 2))
    temple = 0.016 * smoothstep((absolute_x - 0.028) / 0.038)
    sideburn = 0.052 * smoothstep((absolute_x - 0.064) / 0.020)
    return 1.655 + center_peak + temple - sideburn + 0.003 * (x / 0.085)


def bezier(p0, p1, p2, p3, t):
    u = 1.0 - t
    return p0 * u ** 3 + p1 * (3.0 * u * u * t) + p2 * (3.0 * u * t * t) + p3 * t ** 3


def evaluated_tree(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, faces, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


def nearest_root(tree, query):
    hit = tree.find_nearest(query, 0.060)
    if hit is None or hit[1] is None:
        return None
    location, normal, _face, _distance = hit
    normal.normalize()
    if normal.z < -0.10:
        return None
    return location + normal * CLEARANCE, normal


def build_primary_guides(tree):
    center = Vector((0.0, -0.012, 1.635))
    radius_x, radius_y, radius_z = 0.082, 0.108, 0.096
    guides = []
    for row in range(13):
        y = -0.108 + row * (0.184 / 12.0)
        y_norm = (y - center.y) / radius_y
        half_x = radius_x * math.sqrt(max(0.05, 1.0 - y_norm * y_norm))
        columns = max(7, round(12 * half_x / radius_x))
        for column in range(columns):
            unit = (column + 0.5 + (0.31 if row % 2 else 0.0)) / columns
            x = -half_x + 2.0 * half_x * unit
            seam = part_x(y)
            if y < 0.035 and abs(x - seam) < 0.0032:
                continue
            x_norm = x / radius_x
            z = center.z + radius_z * math.sqrt(max(0.0, 1.0 - x_norm * x_norm - y_norm * y_norm))
            root_hit = nearest_root(tree, Vector((x, y, z)))
            if root_hit is None:
                continue
            root, normal = root_hit
            front = clamp((-y - 0.005) / 0.100)
            rear = clamp((y - 0.005) / 0.075)
            if front > 0.20 and root.z < natural_hairline_z(root.x) + 0.003:
                continue
            side = -1.0 if root.x < seam else 1.0
            index = len(guides)
            character = rand(index, 1.0)
            crown = clamp((root.z - 1.665) / 0.070)
            # Layered shoulder-length lob: front locks finish forward of the
            # shoulder, rear locks wrap back, and crown locks overlap both.
            end_x = side * (0.088 + 0.026 * crown + 0.012 * front)
            end_x += (character - 0.5) * 0.018
            end_y = -0.020 * front + 0.050 * rear + 0.008 * (character - 0.5)
            end_z = 1.455 + 0.075 * character + 0.018 * rear
            p0 = root
            root_lift = 0.010 + 0.010 * crown
            p1 = root + normal * root_lift + Vector((side * (0.010 + 0.012 * front), -0.004 * front + 0.005 * rear, 0.010))
            p2 = Vector((end_x - side * (0.018 + 0.010 * rear), end_y - 0.010 * front, 1.610 + 0.020 * crown + (character - 0.5) * 0.018))
            p3 = Vector((end_x, end_y, end_z))
            phase = rand(index, 2.0) * math.tau
            guide = []
            for point_index in range(POINTS):
                t = point_index / (POINTS - 1)
                point = bezier(p0, p1, p2, p3, t)
                flow = smoothstep((t - 0.12) / 0.88)
                body = math.sin(math.pi * t) ** 1.25
                point.x += side * math.sin(phase + t * math.pi * 1.15) * (0.0025 + 0.0035 * character) * body
                point.y += math.cos(phase + t * math.pi) * 0.0022 * body
                point.z += (character - 0.5) * 0.008 * flow
                guide.append(point)
            guides.append({"points": guide, "root": root, "normal": normal, "side": side, "index": index})
    return guides


def build_strands(tree, guides, children):
    strands = []
    for guide in guides:
        normal = guide["normal"]
        tangent = Vector((normal.z, 0.0, -normal.x))
        if tangent.length < 1e-8:
            tangent = Vector((1.0, 0.0, 0.0))
        tangent.normalize()
        bitangent = normal.cross(tangent).normalized()
        for child in range(children):
            index = guide["index"] * children + child
            angle = math.tau * rand(index, 3.0)
            radius = 0.0005 + 0.0052 * math.sqrt(rand(index, 4.0))
            root_query = guide["root"] + tangent * math.cos(angle) * radius + bitangent * math.sin(angle) * radius * 0.78
            root_hit = nearest_root(tree, root_query)
            root = guide["root"] if root_hit is None else root_hit[0]
            root_delta = root - guide["points"][0]
            tail_jitter = (rand(index, 5.0) - 0.5) * 0.021
            phase = rand(index, 6.0) * math.tau
            strand = []
            for point_index, base in enumerate(guide["points"]):
                t = point_index / (POINTS - 1)
                root_release = 1.0 - smoothstep(t / 0.42)
                tip_release = smoothstep((t - 0.55) / 0.45)
                point = base + root_delta * root_release
                point += tangent * (rand(index, 7.0) - 0.5) * 0.0035 * (1.0 - 0.58 * math.sin(math.pi * t))
                point += bitangent * (rand(index, 8.0) - 0.5) * 0.0030 * (1.0 - 0.62 * math.sin(math.pi * t))
                point.z += tail_jitter * tip_release
                fine = math.sin(phase + t * math.tau * (0.9 + 0.3 * rand(index, 9.0)))
                point.x += fine * 0.00048 * smoothstep(t)
                point.y += fine * 0.00020 * smoothstep(t)
                strand.append(point)
            strands.append(strand)
    return strands


def make_material():
    material = bpy.data.materials.new("Aevrynd_OwnedScalpGuideHair_R534")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    hair = nodes.new("ShaderNodeBsdfHairPrincipled")
    info = nodes.new("ShaderNodeHairInfo")
    hair.parametrization = "MELANIN"
    hair.inputs["Melanin"].default_value = 0.60
    hair.inputs["Melanin Redness"].default_value = 0.40
    hair.inputs["Tint"].default_value = (0.90, 0.72, 0.58, 1.0)
    hair.inputs["Roughness"].default_value = 0.43
    hair.inputs["Radial Roughness"].default_value = 0.55
    hair.inputs["Coat"].default_value = 0.045
    hair.inputs["IOR"].default_value = 1.52
    hair.inputs["Random Color"].default_value = 0.10
    hair.inputs["Random Roughness"].default_value = 0.08
    material.node_tree.links.new(info.outputs["Random"], hair.inputs["Random"])
    material.node_tree.links.new(hair.outputs["BSDF"], output.inputs["Surface"])
    material["aevrynd_ownership"] = "procedural in-project; roots sampled from owned CC0-derived body"
    material["aevrynd_revision"] = "v249r534-study"
    return material


def create_curve_object(strands, material):
    data = bpy.data.hair_curves.new("AevryndFemaleOwnedScalpGuideGroom_R534_Data")
    data.add_curves([POINTS] * len(strands))
    data.points.foreach_set("position", [coordinate for strand in strands for point in strand for coordinate in point])
    radius = data.attributes.new("radius", "FLOAT", "POINT")
    radii = []
    for strand_index, _strand in enumerate(strands):
        base = 0.000037 + 0.000012 * rand(strand_index, 10.0)
        for point_index in range(POINTS):
            t = point_index / (POINTS - 1)
            radii.append(base * (1.0 - 0.76 * smoothstep((t - 0.55) / 0.45)))
    radius.data.foreach_set("value", radii)
    data.materials.append(material)
    obj = bpy.data.objects.new("AevryndFemaleOwnedScalpGuideGroom_R534", data)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = bpy.data.objects[RIG]
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = Matrix.Identity(4)
    obj["aevrynd_layer"] = "hair.source_groom.primary_and_fill.study"
    obj["aevrynd_revision"] = "v249r534-study"
    obj["aevrynd_curve_count"] = len(strands)
    obj["aevrynd_root_source"] = "evaluated owned scalp/body surface"
    return obj


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, camera, label, location, target, lens):
    scene.frame_set(1)
    bpy.context.view_layer.update()
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x = scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(OUT / f"{label}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
scene.view_settings.gamma = 1.0
scene.render.image_settings.file_format = "PNG"
body_tree = evaluated_tree(bpy.data.objects[BODY])
guides = build_primary_guides(body_tree)
material = make_material()
OUT.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
study_object = None
variant_report = {}
for label, children in VARIANTS:
    if study_object is not None:
        bpy.data.objects.remove(study_object, do_unlink=True)
        study_object = None
    for name in VISIBLE_LONG_HAIR:
        obj = bpy.data.objects.get(name)
        if obj:
            obj.hide_render = children is not None
            obj.hide_viewport = children is not None
    curve_count = 0
    if children is not None:
        strands = build_strands(body_tree, guides, children)
        study_object = create_curve_object(strands, material)
        curve_count = len(strands)
    for view, location, target, lens in (
        ("front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
        ("three-quarter", (0.45, -0.66, 1.60), (0.0, -0.005, 1.56), 84),
        ("profile", (0.72, -0.03, 1.61), (0.0, 0.0, 1.58), 88),
        ("top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
    ):
        render(scene, camera, f"{label}-{view}", location, target, lens)
    variant_report[label] = {"childrenPerGuide": children, "curves": curve_count}

report = {
    "source": str(SOURCE),
    "primaryGuides": len(guides),
    "collisionClearanceM": CLEARANCE,
    "method": "sample roots directly from evaluated owned scalp/body surface; 13 staggered rows; asymmetric closing part; regional layered-lob cubic guides; project every child root back to scalp; separate primary/fill source groom",
    "variants": variant_report,
    "ownership": "Aevrynd procedural groom on owned CC0-derived body; no external runtime or asset dependency",
    "status": "VISUAL_AND_ROOT_FIELD_SWEEP_ONLY",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R534_OWNED_SCALP_GROOM=" + json.dumps(report, sort_keys=True))
