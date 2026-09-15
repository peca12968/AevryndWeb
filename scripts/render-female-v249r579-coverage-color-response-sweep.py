import json
import math
from pathlib import Path

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-lower-face-clearance-r569.blend"
OUT = ASSETS / "reviews/v249r579-coverage-color-response-sweep"
REPORT = ASSETS / "female-v249-mainline-coverage-color-response-r579.study.json"
ATLAS = ASSETS / "textures/aevrynd-r578-tangent-lock-atlas.png"
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
    ("a-r569-current", None),
    ("b-r572-melanin-control", {"outer_locks": 0, "lift": 0.0, "mode": "MELANIN", "melanin": 0.44}),
    ("c-direct-dark-warm", {"outer_locks": 0, "lift": 0.0, "mode": "COLOR", "color": (0.035, 0.012, 0.005, 1.0)}),
    ("d-direct-mid-warm", {"outer_locks": 0, "lift": 0.0, "mode": "COLOR", "color": (0.055, 0.020, 0.008, 1.0)}),
    ("e-direct-light-warm", {"outer_locks": 0, "lift": 0.0, "mode": "COLOR", "color": (0.085, 0.034, 0.015, 1.0)}),
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


def build_primary_guides(tree, rows, base_columns, tail_strength, layering=0.0, asymmetry=0.0, rear_extent=0.076, radius_y_value=0.108, rear_fall=0.0, style_strength=0.0, guide_wave=1.0):
    irregularity = 1.0
    center = Vector((0.0, -0.012, 1.635))
    radius_x, radius_y, radius_z = 0.082, radius_y_value, 0.096
    guides = []
    for row in range(rows):
        row_y = -0.108 + row * ((rear_extent + 0.108) / (rows - 1))
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
            # Regional lob cut: central front locks stop nearer the jaw while
            # temporal and rear families extend toward the shoulder. A small
            # right/left offset prevents a synchronized salon-mannequin edge.
            front_centre = front * (1.0 - clamp(abs(root.x - seam) / 0.080))
            temple = front * smoothstep((abs(root.x) - 0.035) / 0.045)
            end_z += layering * (0.066 * front_centre + 0.024 * temple - 0.016 * rear)
            end_z += asymmetry * (0.012 if side > 0.0 else -0.006) * (0.35 + 0.65 * front)
            end_x += layering * side * (-0.012 * front_centre + 0.006 * rear)
            end_y += asymmetry * side * 0.009 * (0.25 + 0.75 * front)
            rear_fall_weight = rear_fall * smoothstep((rear - 0.18) / 0.72)
            end_x = end_x * (1.0 - rear_fall_weight) + root.x * 0.76 * rear_fall_weight
            end_y += rear_fall_weight * 0.018
            distance_from_part = abs(root.x - seam)
            face_frame = front * math.exp(-((distance_from_part - 0.018) / 0.026) ** 2)
            temple_tuck = front * smoothstep((abs(root.x) - 0.045) / 0.030)
            heavy_side = 1.0 if side > 0.0 else 0.0
            end_z += style_strength * (0.092 * face_frame + 0.026 * temple_tuck + 0.010 * heavy_side * front)
            frame_target_x = side * (0.064 + 0.012 * temple_tuck)
            frame_blend = clamp(style_strength * face_frame * 0.78)
            end_x = end_x * (1.0 - frame_blend) + frame_target_x * frame_blend
            end_y += style_strength * (-0.018 * face_frame + 0.040 * temple_tuck + 0.008 * heavy_side * front)
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
            p1 = release + Vector((side * (0.030 + 0.010 * front) * (1.0 - 0.86 * rear_fall_weight), -0.005 * front + 0.010 * rear, 0.004 + style_strength * (0.014 * crown + 0.005 * front)))
            p2 = Vector((end_x - side * (0.018 + 0.010 * rear) * (1.0 - 0.88 * rear_fall_weight), end_y - 0.010 * front, 1.610 + 0.020 * crown + (character - 0.5) * 0.018 + style_strength * (0.020 * crown + 0.010 * face_frame)))
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
                    point.x += side * math.sin(phase + t * math.pi * 1.15) * (0.0025 + 0.0035 * character) * body * guide_wave
                    point.y += math.cos(phase + t * math.pi) * 0.0022 * body * (0.72 + 0.28 * guide_wave)
                    point.z += (character - 0.5) * 0.008 * smoothstep(t)
                guide.append(point)
            guides.append({"points": guide, "root": root, "normal": normal, "side": side, "index": index})
    return guides



def append_occipital_fill_guides(tree, guides, rows, columns):
    if rows <= 0 or columns <= 0:
        return guides
    for row in range(rows):
        y = 0.050 + (0.066 * row / max(1, rows - 1))
        y_norm = (y + 0.012) / 0.140
        half_x = 0.052 * math.sqrt(max(0.16, 1.0 - y_norm * y_norm))
        for column in range(columns):
            unit = (column + 0.5 + (0.22 if row % 2 else 0.0)) / columns
            x = -half_x + 2.0 * half_x * unit
            index = len(guides)
            x += (rand(index, 61.0) - 0.5) * 0.004
            z = 1.635 + 0.100 * math.sqrt(max(0.0, 1.0 - (x / 0.082) ** 2 - y_norm ** 2))
            root_hit = nearest_root(tree, Vector((x, y, z)))
            if root_hit is None:
                continue
            root, normal = root_hit
            surface_points = []
            for surface_index in range(8):
                u = surface_index / 7.0
                query = root + Vector(((rand(index, 62.0) - 0.5) * 0.005 * u, 0.007 * u, -0.013 * u))
                hit = nearest_root(tree, query)
                surface_points.append(root.lerp(query, u) if hit is None else hit[0])
            release = surface_points[-1]
            end = Vector((root.x * 0.88 + (rand(index, 63.0) - 0.5) * 0.012,
                          0.095 + (rand(index, 64.0) - 0.5) * 0.018,
                          1.465 + (rand(index, 65.0) - 0.5) * 0.075))
            p1 = release + Vector(((rand(index, 66.0) - 0.5) * 0.010, 0.014, -0.014))
            p2 = Vector((end.x * 0.96, end.y + 0.006, 1.575 + (rand(index, 67.0) - 0.5) * 0.025))
            points = []
            for point_index in range(POINTS):
                if point_index < 8:
                    point = surface_points[point_index].copy()
                else:
                    t = (point_index - 7) / (POINTS - 8)
                    point = bezier(release, p1, p2, end, t)
                    point.x += math.sin(rand(index, 68.0) * math.tau + t * math.pi) * 0.003 * math.sin(math.pi * t)
                points.append(point)
            guides.append({"points": points, "root": root, "normal": normal, "side": -1.0 if root.x < 0 else 1.0, "index": index, "family": "occipital_fill"})
    return guides


def assign_sparse_guide_targets(guides, stride=7):
    """Map dense surface roots to a small, explicit guide set.

    Roots never move.  Shape offsets are interpolated from the three nearest
    compatible sparse guides, while the closest guide supplies the optional
    mid-length clump target.  This mirrors Blender's guide-index workflow but
    keeps the generated curves as an owned, dependency-free output.
    """
    primary = [guide for guide in guides if guide.get("family") != "occipital_fill"]
    occipital = [guide for guide in guides if guide.get("family") == "occipital_fill"]
    anchors = primary[::stride] + occipital[::max(1, stride // 2)]
    for guide in guides:
        is_occipital = guide.get("family") == "occipital_fill"
        compatible = [
            anchor for anchor in anchors
            if (anchor.get("family") == "occipital_fill") == is_occipital
            and (is_occipital or anchor["side"] == guide["side"])
        ]
        nearest = sorted(
            compatible,
            key=lambda anchor: (anchor["root"].x - guide["root"].x) ** 2
            + 0.70 * (anchor["root"].y - guide["root"].y) ** 2,
        )[:3]
        weights = []
        for anchor in nearest:
            distance = max(0.0004, (anchor["root"] - guide["root"]).length)
            weights.append(1.0 / (distance * distance))
        total = sum(weights)
        interpolated = []
        for point_index in range(POINTS):
            offset = sum(
                ((anchor["points"][point_index] - anchor["root"]) * weight for anchor, weight in zip(nearest, weights)),
                Vector(),
            ) / total
            interpolated.append(guide["root"] + offset)
        interpolated[0] = guide["root"].copy()
        main = nearest[0]
        macro_target = []
        root_delta = guide["root"] - main["root"]
        for point_index, point in enumerate(main["points"]):
            t = point_index / (POINTS - 1)
            root_hold = 1.0 - smoothstep(t / 0.38)
            macro_target.append(point + root_delta * root_hold)
        guide["points"] = interpolated
        guide["macro_target"] = macro_target
        guide["macro_guide_index"] = main["index"]
        guide["macro_region"] = 0.0 if is_occipital else clamp((-guide["root"].y + 0.015) / 0.105)
    return guides, len(anchors)


def apply_light_side_tuck(guides, strength):
    for guide in guides:
        if guide.get("family") == "occipital_fill" or guide["side"] > 0.0:
            continue
        front = clamp((-guide["root"].y + 0.005) / 0.105)
        temple = smoothstep((abs(guide["root"].x) - 0.030) / 0.045)
        amount = strength * front * temple
        if amount <= 0.001:
            continue
        for point_index in range(POINTS):
            t = point_index / (POINTS - 1)
            route = smoothstep((t - 0.18) / 0.42)
            behind = smoothstep((t - 0.42) / 0.44)
            delta = Vector((
                guide["side"] * 0.020 * route,
                0.060 * behind,
                0.040 * behind,
            )) * amount
            guide["points"][point_index] += delta
            guide["macro_target"][point_index] += delta
    return guides

def build_strands(tree, guides, spread, children, clump_strength, tip_spread, noise_strength, macro_strength=0.0):
    strands = []
    for guide in guides:
        normal = guide["normal"]
        tangent = Vector((normal.z, 0.0, -normal.x))
        if tangent.length < 1e-8:
            tangent = Vector((1.0, 0.0, 0.0))
        tangent.normalize()
        bitangent = normal.cross(tangent).normalized()
        cluster_offsets = []
        for cluster in range(3):
            cluster_index = guide["index"] * 3 + cluster
            cluster_offsets.append(((rand(cluster_index, 41.0) - 0.5) * 0.0052 * spread,
                                    (rand(cluster_index, 42.0) - 0.5) * 0.0042 * spread))
        for child in range(children):
            index = guide["index"] * children + child
            angle = math.tau * rand(index, 3.0)
            radius = 0.0005 + 0.0052 * math.sqrt(rand(index, 4.0))
            root_query = guide["root"] + tangent * math.cos(angle) * radius + bitangent * math.sin(angle) * radius * 0.78
            root_hit = nearest_root(tree, root_query)
            root = guide["root"] if root_hit is None else root_hit[0]
            root_delta = root - guide["points"][0]
            individual_x = (rand(index, 7.0) - 0.5) * 0.0055 * spread
            individual_y = (rand(index, 8.0) - 0.5) * 0.0045 * spread
            cluster_x, cluster_y = cluster_offsets[child % 3]
            tail_jitter = (rand(index, 5.0) - 0.5) * 0.028 * tip_spread
            phase = rand(index, 6.0) * math.tau
            macro_phase = rand(guide["index"] // 7, 43.0) * math.tau
            strand = []
            for point_index, base in enumerate(guide["points"]):
                t = point_index / (POINTS - 1)
                root_release = 1.0 - 0.45 * smoothstep(t / 0.52)
                tip_release = smoothstep((t - 0.58) / 0.42)
                clump_window = smoothstep((t - 0.10) / 0.30) * (1.0 - 0.82 * smoothstep((t - 0.68) / 0.32))
                pull = clump_strength * clump_window
                fan = 1.0 + (tip_spread - 1.0) * tip_release
                offset_x = (individual_x * (1.0 - pull) + cluster_x * pull) * fan
                offset_y = (individual_y * (1.0 - pull) + cluster_y * pull) * fan
                point = base + root_delta * root_release + tangent * offset_x + bitangent * offset_y
                macro_window = smoothstep((t - 0.18) / 0.34) * (1.0 - 0.42 * smoothstep((t - 0.78) / 0.22))
                point = point.lerp(guide["macro_target"][point_index], macro_strength * guide["macro_region"] * macro_window)
                point.z += tail_jitter * tip_release
                low = math.sin(macro_phase + t * math.pi * 1.35) * 0.00115 * noise_strength * math.sin(math.pi * t)
                fine = math.sin(phase + t * math.tau * (0.9 + 0.3 * rand(index, 9.0)))
                point.x += guide["side"] * low + fine * 0.00055 * noise_strength * smoothstep(t)
                point.y += low * 0.42 + fine * 0.00024 * noise_strength * smoothstep(t)
                strand.append(point)
            strands.append(strand)
    return strands


def make_material():
    material = bpy.data.materials.new("Aevrynd_OwnedScalpGuideHair_R578")
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
    material["aevrynd_revision"] = "v249r578-study"
    return material


def make_card_material():
    material = bpy.data.materials.new("Aevrynd_TangentOuterHairCards_R578")
    material.use_nodes = True
    material.surface_render_method = "DITHERED"
    material.use_backface_culling = False
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = bpy.data.images.load(str(ATLAS), check_existing=True)
    texture.interpolation = "Linear"
    shader.inputs["Base Color"].default_value = (0.16, 0.060, 0.027, 1.0)
    shader.inputs["Roughness"].default_value = 0.50
    shader.inputs["Specular IOR Level"].default_value = 0.18
    shader.inputs["Coat Weight"].default_value = 0.018
    if "Anisotropic IOR Level" in shader.inputs:
        shader.inputs["Anisotropic IOR Level"].default_value = 0.28
    links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    links.new(texture.outputs["Alpha"], shader.inputs["Alpha"])
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    material["aevrynd_ownership"] = "Aevrynd procedural RGBA atlas r578"
    material["aevrynd_revision"] = "v249r578-study"
    return material


def create_curve_object(strands, material, root_scale, suffix="Coverage", radius_multiplier=1.0):
    data = bpy.data.hair_curves.new(f"AevryndFemaleOwnedScalpGuideGroom_R578_{suffix}_Data")
    data.add_curves([POINTS] * len(strands))
    data.points.foreach_set("position", [coordinate for strand in strands for point in strand for coordinate in point])
    radius = data.attributes.new("radius", "FLOAT", "POINT")
    radii = []
    for strand_index, _strand in enumerate(strands):
        base = (0.000037 + 0.000012 * rand(strand_index, 10.0)) * radius_multiplier
        for point_index in range(POINTS):
            t = point_index / (POINTS - 1)
            root_transition = root_scale + (1.0 - root_scale) * smoothstep(t / 0.16)
            radii.append(base * root_transition * (1.0 - 0.76 * smoothstep((t - 0.55) / 0.45)))
    radius.data.foreach_set("value", radii)
    data.materials.append(material)
    obj = bpy.data.objects.new(f"AevryndFemaleOwnedScalpGuideGroom_R578_{suffix}", data)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = bpy.data.objects[RIG]
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = Matrix.Identity(4)
    obj["aevrynd_layer"] = f"hair.source_groom.{suffix.lower()}.study"
    obj["aevrynd_revision"] = "v249r578-study"
    obj["aevrynd_curve_count"] = len(strands)
    obj["aevrynd_root_source"] = "evaluated owned scalp/body surface"
    return obj


def lift_outer_strands(strands, amount):
    center = Vector((0.0, -0.012, 1.635))
    lifted = []
    for strand in strands:
        result = []
        for point_index, source in enumerate(strand):
            t = point_index / (POINTS - 1)
            radial = Vector((source.x - center.x, source.y - center.y, max(0.012, source.z - center.z)))
            radial.normalize()
            envelope = smoothstep(t / 0.30) * (1.0 - 0.25 * smoothstep((t - 0.80) / 0.20))
            result.append(source + radial * amount * envelope)
        lifted.append(result)
    return lifted


def build_manual_outer_guides(tree, count, lift):
    # Interleaved front, side, crown and rear controls. Every prefix therefore
    # retains bilateral and front/back coverage, and none of these trajectories
    # is sampled from the dense coverage layer.
    specs = (
        (-0.010, -0.090, -0.070, -0.040, 1.555, -0.014, 0.010),
        ( 0.012, -0.090,  0.068, -0.050, 1.535, -0.010, 0.012),
        (-0.044, -0.066, -0.100,  0.020, 1.495,  0.014, 0.018),
        ( 0.045, -0.066,  0.103, -0.005, 1.475,  0.004, 0.020),
        (-0.030,  0.010, -0.074,  0.098, 1.465,  0.020, 0.022),
        ( 0.032,  0.010,  0.077,  0.100, 1.445,  0.020, 0.022),
        (-0.065, -0.025, -0.110,  0.060, 1.455,  0.020, 0.018),
        ( 0.066, -0.025,  0.112,  0.050, 1.485,  0.014, 0.018),
        (-0.018,  0.050, -0.042,  0.112, 1.425,  0.028, 0.024),
        ( 0.020,  0.050,  0.045,  0.114, 1.455,  0.028, 0.024),
        (-0.072,  0.018, -0.096,  0.092, 1.505,  0.024, 0.020),
        ( 0.073,  0.018,  0.098,  0.090, 1.475,  0.024, 0.020),
        (-0.004, -0.045, -0.088,  0.005, 1.585, -0.004, 0.030),
        ( 0.006, -0.035,  0.090,  0.015, 1.560,  0.004, 0.030),
        (-0.052,  0.045, -0.070,  0.118, 1.440,  0.030, 0.020),
        ( 0.054,  0.045,  0.073,  0.118, 1.470,  0.030, 0.020),
        (-0.025, -0.002, -0.105,  0.045, 1.520,  0.010, 0.026),
        ( 0.028, -0.002,  0.107,  0.030, 1.500,  0.006, 0.026),
        (-0.005,  0.078, -0.020,  0.125, 1.455,  0.032, 0.022),
        ( 0.008,  0.078,  0.023,  0.126, 1.435,  0.032, 0.022),
    )
    center = Vector((0.0, -0.012, 1.635))
    guides = []
    for index, (root_x, root_y, end_x, end_y, end_z, bend_y, arch) in enumerate(specs[:count]):
        y_norm = (root_y + 0.012) / 0.140
        z = 1.635 + 0.100 * math.sqrt(max(0.0, 1.0 - (root_x / 0.082) ** 2 - y_norm ** 2))
        hit = nearest_root(tree, Vector((root_x, root_y, z)))
        if hit is None:
            continue
        root, normal = hit
        side = -1.0 if end_x < 0.0 else 1.0
        end = Vector((end_x, end_y, end_z))
        radial = root - center
        radial.normalize()
        # Keep the visible ribbon close to the scalp at release.  r576's large
        # vertical control offsets made round bundles read as crown cables.
        p1 = root + radial * (0.0035 + lift * 0.20) + Vector((side * 0.010, bend_y * 0.32, 0.003 + arch * 0.06))
        p2 = root.lerp(end, 0.66) + radial * (0.0035 + lift * 0.40) + Vector((-side * 0.006, bend_y * 0.20, 0.022 + arch * 0.08))
        points = []
        for point_index in range(POINTS):
            t = point_index / (POINTS - 1)
            point = bezier(root, p1, p2, end, t)
            point += radial * lift * smoothstep(t / 0.32) * (1.0 - 0.20 * smoothstep((t - 0.82) / 0.18))
            point.x += side * math.sin(math.pi * t) * (0.0025 + 0.0015 * rand(index, 91.0))
            points.append(point)
        guides.append({
            "points": points,
            "macro_target": [point.copy() for point in points],
            "macro_region": 1.0,
            "macro_guide_index": 1000 + index,
            "root": root,
            "normal": normal,
            "side": side,
            "index": 1000 + index,
            "family": "independent_outer_lock",
        })
    return guides


def create_card_object(guides, material, width_mm, layers, spacing_mm):
    vertices, faces = [], []
    for guide_index, guide in enumerate(guides):
        for layer_index in range(layers):
            output_base = len(vertices)
            lateral_mm = (layer_index - (layers - 1) * 0.5) * spacing_mm
            for point_index, point_source in enumerate(guide["points"]):
                t = point_index / (POINTS - 1)
                point = point_source.copy()
                before = guide["points"][max(0, point_index - 1)]
                after = guide["points"][min(POINTS - 1, point_index + 1)]
                tangent = (after - before).normalized()
                scalp_width = tangent.cross(guide["normal"])
                if scalp_width.length < 1e-8:
                    scalp_width = Vector((1.0, 0.0, 0.0))
                scalp_width.normalize()
                camera_facing = Vector((-point.x, -point.y - 0.20, 0.0))
                if camera_facing.length < 1e-8:
                    camera_facing = Vector((0.0, -1.0, 0.0))
                camera_facing.normalize()
                free_width = tangent.cross(camera_facing)
                if free_width.length < 1e-8:
                    free_width = scalp_width.copy()
                free_width.normalize()
                if free_width.dot(scalp_width) < 0.0:
                    free_width.negate()
                release = smoothstep((t - 0.20) / 0.42)
                width_vector = scalp_width.lerp(free_width, release).normalized()
                root_growth = 0.18 + 0.82 * smoothstep(t / 0.24)
                tip_taper = 1.0 - 0.90 * smoothstep((t - 0.68) / 0.32)
                half_width = width_mm * 0.0005 * root_growth * tip_taper
                point += width_vector * lateral_mm * 0.001 * smoothstep(t / 0.20)
                point += guide["normal"] * (0.00035 + 0.00030 * layer_index) * (1.0 - smoothstep(t / 0.42))
                vertices.extend((point - width_vector * half_width, point + width_vector * half_width))
            for point_index in range(POINTS - 1):
                base = output_base + point_index * 2
                faces.append((base, base + 1, base + 3, base + 2))
    mesh = bpy.data.meshes.new("AevryndTangentOuterHairCards_R578_Data")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(material)
    uv = mesh.uv_layers.new(name="AevryndIndependentOuterHairCardUV")
    for polygon in mesh.polygons:
        guide_index = polygon.index // (POINTS - 1)
        slot = guide_index % 4
        for loop_index in polygon.loop_indices:
            local_vertex = mesh.loops[loop_index].vertex_index % (POINTS * 2)
            local_row = local_vertex // 2
            side = local_vertex % 2
            uv.data[loop_index].uv = ((slot + (0.04 if side == 0 else 0.96)) / 4.0, local_row / (POINTS - 1))
    uv.active_render = True
    obj = bpy.data.objects.new("AevryndFemaleTangentOuterHairCards_R578", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = bpy.data.objects[RIG]
    obj.parent_type = "OBJECT"
    obj.matrix_world = Matrix.Identity(4)
    obj["aevrynd_layer"] = "hair.source_groom.outer_macro_cards.study"
    obj["aevrynd_revision"] = "v249r578-study"
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
material = make_material()
outer_material = make_card_material()
OUT.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
study_object = None
outer_object = None
variant_report = {}
guide_count = 0
sparse_guide_count = 0
hair_node = next(node for node in material.node_tree.nodes if node.type == "BSDF_HAIR_PRINCIPLED")
hair_node.inputs["Melanin"].default_value = 0.52
for label, config in VARIANTS:
    if study_object is not None:
        bpy.data.objects.remove(study_object, do_unlink=True)
        study_object = None
    if outer_object is not None:
        bpy.data.objects.remove(outer_object, do_unlink=True)
        outer_object = None
    for name in VISIBLE_LONG_HAIR:
        obj = bpy.data.objects.get(name)
        if obj:
            obj.hide_render = config is not None
            obj.hide_viewport = config is not None
    curve_count = 0
    if config is not None:
        rows, base_columns, children = 23, 23, 14
        guides = build_primary_guides(body_tree, rows, base_columns, 1.35, 0.75, 0.65, 0.118, 0.140, 1.0, 0.65, 1.0)
        guides = append_occipital_fill_guides(body_tree, guides, 6, 11)
        guides, sparse_guide_count = assign_sparse_guide_targets(guides, 7)
        guides = apply_light_side_tuck(guides, 0.55)
        hair_node.parametrization = config["mode"]
        if config["mode"] == "MELANIN":
            hair_node.inputs["Melanin"].default_value = config["melanin"]
            hair_node.inputs["Melanin Redness"].default_value = 0.44
            hair_node.inputs["Tint"].default_value = (0.94, 0.76, 0.62, 1.0)
        else:
            hair_node.inputs["Color"].default_value = config["color"]
        guide_count = len(guides)
        strands = build_strands(body_tree, guides, 1.45, 12, 0.72, 1.95, 0.90, 0.22)
        study_object = create_curve_object(strands, material, 0.15, "Coverage", 1.0)
        curve_count = len(strands)
        outer_count = 0
        if config["outer_locks"]:
            outer_guides = build_manual_outer_guides(body_tree, config["outer_locks"], config["lift"])
            outer_object = create_card_object(outer_guides, outer_material, config["width_mm"], config["layers"], config["spacing_mm"])
            outer_count = len(outer_guides)
    for view, location, target, lens in (
        ("front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
        ("three-quarter", (0.45, -0.66, 1.60), (0.0, -0.005, 1.56), 84),
        ("profile", (0.72, -0.03, 1.61), (0.0, 0.0, 1.58), 88),
        ("top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
        ("back", (0.0, 0.72, 1.60), (0.0, 0.025, 1.58), 88),
    ):
        render(scene, camera, f"{label}-{view}", location, target, lens)
    variant_report[label] = {"config": config, "rootRadiusScale": None if config is None else 0.15, "tailHierarchyStrength": None if config is None else 1.35, "surfaceRoots": 0 if config is None else guide_count, "sparseGuides": 0 if config is None else sparse_guide_count, "outerGuides": 0, "coverageCurves": curve_count, "outerCards": 0}

report = {
    "source": str(SOURCE),
    "surfaceRoots": guide_count,
    "sparseGuides": sparse_guide_count,
    "collisionClearanceM": CLEARANCE,
    "method": "hold r572 geometry, roots, curve radius, lights and Standard color management fixed; compare the melanin control against three explicit linear-RGBA warm-brown Hair BSDF responses so hair luminance can be calibrated independently of face exposure",
    "variants": variant_report,
    "ownership": "Aevrynd procedural groom on owned CC0-derived body; no external runtime or asset dependency",
    "status": "VISUAL_AND_ROOT_FIELD_SWEEP_ONLY",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R579_COVERAGE_COLOR_RESPONSE=" + json.dumps(report, sort_keys=True))
