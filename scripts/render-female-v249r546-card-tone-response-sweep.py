import json
import math
from pathlib import Path

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-orbital-brow-refit-r526.blend"
OUT = ASSETS / "reviews/v249r546-card-tone-response-sweep"
REPORT = ASSETS / "female-v249-mainline-card-tone-response-r546.study.json"
ATLAS = ASSETS / "textures/aevrynd-owned-hair-clump-colour-alpha-r544.png"
NORMAL_ATLAS = ASSETS / "textures/aevrynd-owned-hair-clump-normal-r544.png"
ROUGHNESS_ATLAS = ASSETS / "textures/aevrynd-owned-hair-clump-roughness-r544.png"
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
    ("b-tone-factor-0p18", 0.18),
    ("c-tone-factor-0p28", 0.28),
    ("d-tone-factor-0p40", 0.40),
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


def build_primary_guides(tree, rows, base_columns, tail_strength):
    irregularity = 1.0
    center = Vector((0.0, -0.012, 1.635))
    radius_x, radius_y, radius_z = 0.082, 0.108, 0.096
    guides = []
    for row in range(rows):
        row_y = -0.108 + row * (0.184 / (rows - 1))
        row_y_norm = (row_y - center.y) / radius_y
        half_x = radius_x * math.sqrt(max(0.05, 1.0 - row_y_norm * row_y_norm))
        columns = max(7, round(base_columns * half_x / radius_x))
        for column in range(columns):
            unit = (column + 0.5 + (0.31 if row % 2 else 0.0)) / columns
            sample_index = row * (base_columns + 11) + column
            y = row_y + (rand(sample_index, 11.0) - 0.5) * 0.010 * irregularity
            y_norm = (y - center.y) / radius_y
            x = -half_x + 2.0 * half_x * unit
            x += (rand(sample_index, 12.0) - 0.5) * 0.007 * irregularity
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
            macro_id = (row // 3) * 101 + (column // 3) * 17
            medium_id = (row // 2) * 137 + (column // 2) * 23
            macro = rand(macro_id, 21.0)
            medium = rand(medium_id, 22.0)
            detail = rand(index, 1.0)
            character = 0.62 * macro + 0.28 * medium + 0.10 * detail
            crown = clamp((root.z - 1.665) / 0.070)
            # Layered shoulder-length lob: front locks finish forward of the
            # shoulder, rear locks wrap back, and crown locks overlap both.
            end_x = side * (0.088 + 0.026 * crown + 0.012 * front)
            end_x += tail_strength * ((macro - 0.5) * 0.020 + (medium - 0.5) * 0.009)
            end_y = -0.020 * front + 0.050 * rear
            end_y += tail_strength * ((macro - 0.5) * 0.016 + (medium - 0.5) * 0.007)
            end_z = 1.490 + 0.018 * rear
            end_z += tail_strength * ((macro - 0.5) * 0.105 + (medium - 0.5) * 0.036 + (detail - 0.5) * 0.010)
            surface_points = []
            release_distance = (0.030 + 0.010 * front) * (0.78 + 0.48 * rand(index, 13.0))
            surface_y_flow = (rand(index, 14.0) - 0.5) * 0.034 * irregularity
            for surface_index in range(8):
                u = surface_index / 7.0
                arc = math.sin(math.pi * u)
                query = root + Vector((side * release_distance * u,
                                       (0.006 * rear - 0.005 * front) * u + surface_y_flow * (0.35 * u + 0.65 * arc),
                                       0.007 * u + 0.003 * (rand(index, 15.0) - 0.5) * arc * irregularity))
                surface_hit = nearest_root(tree, query)
                surface_points.append(root.lerp(query, u) if surface_hit is None else surface_hit[0])
            release = surface_points[-1]
            p0 = release
            p1 = release + Vector((side * (0.030 + 0.010 * front), -0.005 * front + 0.010 * rear, 0.004))
            p2 = Vector((end_x - side * (0.018 + 0.010 * rear), end_y - 0.010 * front, 1.610 + 0.020 * crown + (character - 0.5) * 0.018))
            p3 = Vector((end_x, end_y, end_z))
            phase = rand(index, 2.0) * math.tau
            guide = []
            for point_index in range(POINTS):
                if point_index < 8:
                    point = surface_points[point_index].copy()
                else:
                    t = (point_index - 7) / (POINTS - 8)
                    point = bezier(p0, p1, p2, p3, t)
                    body = math.sin(math.pi * t) ** 1.25
                    point.x += side * math.sin(phase + t * math.pi * 1.15) * (0.0025 + 0.0035 * character) * body
                    point.y += math.cos(phase + t * math.pi) * 0.0022 * body
                    point.z += (character - 0.5) * 0.008 * smoothstep(t)
                guide.append(point)
            guides.append({"points": guide, "root": root, "normal": normal, "side": side, "index": index})
    return guides


def build_strands(tree, guides, spread, children):
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
                root_release = 1.0 - 0.45 * smoothstep(t / 0.52)
                tip_release = smoothstep((t - 0.55) / 0.45)
                point = base + root_delta * root_release
                point += tangent * (rand(index, 7.0) - 0.5) * 0.0055 * spread * (1.0 - 0.42 * math.sin(math.pi * t))
                point += bitangent * (rand(index, 8.0) - 0.5) * 0.0045 * spread * (1.0 - 0.48 * math.sin(math.pi * t))
                point.z += tail_jitter * tip_release
                fine = math.sin(phase + t * math.tau * (0.9 + 0.3 * rand(index, 9.0)))
                point.x += fine * 0.00048 * smoothstep(t)
                point.y += fine * 0.00020 * smoothstep(t)
                strand.append(point)
            strands.append(strand)
    return strands


def make_material():
    material = bpy.data.materials.new("Aevrynd_OwnedScalpGuideHair_R546")
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
    material["aevrynd_revision"] = "v249r546-study"
    return material


def create_curve_object(strands, material):
    data = bpy.data.hair_curves.new("AevryndFemaleOwnedScalpGuideGroom_R546_Data")
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
    obj = bpy.data.objects.new("AevryndFemaleOwnedScalpGuideGroom_R546", data)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = bpy.data.objects[RIG]
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = Matrix.Identity(4)
    obj["aevrynd_layer"] = "hair.source_groom.primary_and_fill.study"
    obj["aevrynd_revision"] = "v249r546-study"
    obj["aevrynd_curve_count"] = len(strands)
    obj["aevrynd_root_source"] = "evaluated owned scalp/body surface"
    return obj


def make_card_material():
    material = bpy.data.materials.new("Aevrynd_OwnedHairCards_R546")
    material.use_nodes = True
    material.surface_render_method = "DITHERED"
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = bpy.data.images.load(str(ATLAS), check_existing=True)
    texture.interpolation = "Linear"
    normal_texture = nodes.new("ShaderNodeTexImage")
    normal_texture.image = bpy.data.images.load(str(NORMAL_ATLAS), check_existing=True)
    normal_texture.image.colorspace_settings.name = "Non-Color"
    normal_map = nodes.new("ShaderNodeNormalMap")
    normal_map.space = "TANGENT"
    normal_map.inputs["Strength"].default_value = 0.08
    roughness_texture = nodes.new("ShaderNodeTexImage")
    roughness_texture.image = bpy.data.images.load(str(ROUGHNESS_ATLAS), check_existing=True)
    roughness_texture.image.colorspace_settings.name = "Non-Color"
    multiply = nodes.new("ShaderNodeMixRGB")
    multiply.name = "Aevrynd R546 Hair Tone Multiplier"
    multiply.blend_type = "MULTIPLY"
    multiply.inputs[0].default_value = 1.0
    shader.inputs["Specular IOR Level"].default_value = 0.15
    shader.inputs["Coat Weight"].default_value = 0.0
    links.new(texture.outputs["Color"], multiply.inputs[1])
    links.new(multiply.outputs["Color"], shader.inputs["Base Color"])
    links.new(texture.outputs["Alpha"], shader.inputs["Alpha"])
    links.new(normal_texture.outputs["Color"], normal_map.inputs["Color"])
    links.new(normal_map.outputs["Normal"], shader.inputs["Normal"])
    links.new(roughness_texture.outputs["Color"], shader.inputs["Roughness"])
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    material["aevrynd_ownership"] = "Aevrynd procedural atlas r546"
    material["aevrynd_revision"] = "v249r546-study"
    return material


def create_card_object(guides, material, layers, width_mm):
    vertices, faces = [], []
    for guide_index, guide in enumerate(guides):
        for layer_index in range(layers):
            output_base = len(vertices)
            layer_sign = -0.5 if layer_index == 0 else 0.5
            for point_index, point_source in enumerate(guide["points"]):
                t = point_index / (POINTS - 1)
                point = point_source.copy()
                radial = Vector((point.x, point.y + 0.012, 0.0))
                if radial.length < 1e-8:
                    radial = Vector((0.0, -1.0, 0.0))
                radial.normalize()
                lateral = Vector((-radial.y, radial.x, 0.0))
                point += radial * (0.0007 + layer_index * 0.0010)
                point += lateral * layer_sign * 0.0008
                root_growth = 0.38 + 0.62 * smoothstep(t / 0.18)
                tip_taper = 1.0 - 0.82 * smoothstep((t - 0.68) / 0.32)
                half_width = width_mm * 0.0005 * root_growth * tip_taper
                vertices.extend((point - lateral * half_width, point + lateral * half_width))
            for point_index in range(POINTS - 1):
                base = output_base + point_index * 2
                faces.append((base, base + 1, base + 3, base + 2))
    mesh = bpy.data.meshes.new("AevryndFemaleOwnedGroomCards_R546_Data")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(material)
    uv = mesh.uv_layers.new(name="AevryndOwnedGroomCardUV")
    for polygon in mesh.polygons:
        card_index = polygon.index // (POINTS - 1)
        row = polygon.index % (POINTS - 1)
        slot = card_index % 4
        for loop_index in polygon.loop_indices:
            local_vertex = mesh.loops[loop_index].vertex_index % (POINTS * 2)
            local_row = local_vertex // 2
            side = local_vertex % 2
            uv.data[loop_index].uv = ((slot + (0.05 if side == 0 else 0.95)) / 4.0, local_row / (POINTS - 1))
    uv.active_render = True
    obj = bpy.data.objects.new("AevryndFemaleOwnedGroomCards_R546", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = bpy.data.objects[RIG]
    obj.parent_type = "OBJECT"
    obj.matrix_world = Matrix.Identity(4)
    obj["aevrynd_layer"] = "hair.runtime_cards.owned_groom_bake.study"
    obj["aevrynd_revision"] = "v249r546-study"
    obj["aevrynd_card_count"] = len(guides) * layers
    obj["aevrynd_source_guides"] = len(guides)
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
card_material = make_card_material()
OUT.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
study_object = None
variant_report = {}
guide_count = 0
tone_multiply = card_material.node_tree.nodes["Aevrynd R546 Hair Tone Multiplier"].inputs[2]
for label, tone_factor in VARIANTS:
    if study_object is not None:
        bpy.data.objects.remove(study_object, do_unlink=True)
        study_object = None
    for name in VISIBLE_LONG_HAIR:
        obj = bpy.data.objects.get(name)
        if obj:
            obj.hide_render = tone_factor is not None
            obj.hide_viewport = tone_factor is not None
    card_count = 0
    if tone_factor is not None:
        layers, width_mm = 2, 3.5
        tone_multiply.default_value = (tone_factor, tone_factor, tone_factor, 1.0)
        rows, base_columns, children = 23, 23, 14
        guides = build_primary_guides(body_tree, rows, base_columns, 1.35)
        guide_count = len(guides)
        study_object = create_card_object(guides, card_material, layers, width_mm)
        card_count = len(guides) * layers
    for view, location, target, lens in (
        ("front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
        ("three-quarter", (0.45, -0.66, 1.60), (0.0, -0.005, 1.56), 84),
        ("profile", (0.72, -0.03, 1.61), (0.0, 0.0, 1.58), 88),
        ("top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
    ):
        render(scene, camera, f"{label}-{view}", location, target, lens)
    variant_report[label] = {"toneFactor": tone_factor, "guides": 0 if tone_factor is None else guide_count, "cards": card_count}

report = {
    "source": str(SOURCE),
    "primaryGuides": guide_count,
    "collisionClearanceM": CLEARANCE,
    "method": "hold r545 two-layer 3.5mm card geometry and dense atlas alpha fixed; reduce tangent-normal strength to 0.08, specular to 0.15, remove coat and sweep RGB multiplier",
    "atlas": str(ATLAS),
    "normalAtlas": str(NORMAL_ATLAS),
    "roughnessAtlas": str(ROUGHNESS_ATLAS),
    "variants": variant_report,
    "ownership": "Aevrynd procedural groom on owned CC0-derived body; no external runtime or asset dependency",
    "status": "VISUAL_AND_ROOT_FIELD_SWEEP_ONLY",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R546_OWNED_SCALP_GROOM=" + json.dumps(report, sort_keys=True))
