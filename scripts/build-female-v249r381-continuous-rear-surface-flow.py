import json
import math
from pathlib import Path

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-canthus-fitted-wedge-r345.blend"
OUTPUT = ASSETS / "aevrynd-female-authoring-v249-mainline-continuous-rear-surface-flow-r381.blend"
REPORT = ASSETS / "female-v249-mainline-continuous-rear-surface-flow-r381.build-report.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r381-continuous-rear-surface-flow"
BODY = "AevryndFemaleBody_CC0_R249"
RIG = "AevryndFemaleRig"
POINTS = 24
FOLLOWERS = 42
CLEARANCE = 0.0020
FRONT_FLOW_CLEARANCE = 0.0038
SCALP_DENSITY_ATTRIBUTE = "aevrynd_scalp_density"
SCALP_MAX_ALPHA = 0.50
OLD_HAIR = (
    "AevryndFemaleScalpUnderlayer_R280",
    "AevryndFemalePrimaryClumps_R264",
    "AevryndFemaleSecondaryFill_R264",
    "AevryndFemaleFlyaways_R264",
    "AevryndFemaleHairlineTransitionCards_R285",
    "AevryndFemaleRuntimeHairCards_R276",
)


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def smoothstep(value):
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def fract(value):
    return value - math.floor(value)


def rand(index, salt=0.0):
    return fract(math.sin(index * 12.9898 + salt * 78.233) * 43758.5453)


def part_x(y):
    return -0.026 + 0.020 * smoothstep((y + 0.105) / 0.180)


def natural_hairline_z(x):
    """Female hairline contour with a small center peak and lower sideburns."""
    absolute_x = abs(x)
    center_peak = -0.010 * math.exp(-((x / 0.018) ** 2))
    temple_recession = 0.018 * smoothstep((absolute_x - 0.025) / 0.040)
    sideburn_descent = 0.055 * smoothstep((absolute_x - 0.065) / 0.020)
    asymmetry = 0.003 * (x / 0.085)
    return 1.655 + center_peak + temple_recession - sideburn_descent + asymmetry


def scalp_density(point):
    if point.y < -0.045:
        depth_lift = 0.006 * clamp((-point.y - 0.045) / 0.080)
        edge = natural_hairline_z(point.x) + depth_lift
        boundary_fade = smoothstep((point.z - edge) / 0.022)
    else:
        boundary_fade = smoothstep((point.z - 1.585) / 0.026)
    part_distance = abs(point.x - part_x(point.y))
    # A narrow, softly darkened scalp part prevents the exposed body surface
    # from turning into a broad white highlight in top views.
    part_fade = 0.55 + 0.45 * smoothstep((part_distance - 0.00045) / 0.0050)
    lateral_fade = 1.0 - 0.55 * smoothstep((abs(point.x) - 0.085) / 0.030)
    return SCALP_MAX_ALPHA * boundary_fade * part_fade * lateral_fade


def bezier(p0, p1, p2, p3, t):
    u = 1.0 - t
    return p0 * (u**3) + p1 * (3.0 * u * u * t) + p2 * (3.0 * u * t * t) + p3 * (t**3)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def evaluated_tree(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, faces, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


def make_hair_material():
    material = bpy.data.materials.new("Aevrynd_SemanticGuideHair_R381")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    hair = nodes.new("ShaderNodeBsdfHairPrincipled")
    hair_info = nodes.new("ShaderNodeHairInfo")
    hair.parametrization = "MELANIN"
    hair.inputs["Melanin"].default_value = 0.68
    hair.inputs["Melanin Redness"].default_value = 0.54
    hair.inputs["Tint"].default_value = (0.92, 0.72, 0.58, 1.0)
    hair.inputs["Roughness"].default_value = 0.36
    hair.inputs["Radial Roughness"].default_value = 0.48
    hair.inputs["Coat"].default_value = 0.075
    hair.inputs["IOR"].default_value = 1.52
    hair.inputs["Random Color"].default_value = 0.14
    hair.inputs["Random Roughness"].default_value = 0.09
    material.node_tree.links.new(hair_info.outputs["Random"], hair.inputs["Random"])
    material.node_tree.links.new(hair.outputs["BSDF"], output.inputs["Surface"])
    material["aevrynd_ownership"] = "procedural in-project"
    material["aevrynd_revision"] = "v249r381"
    material["aevrynd_shader_model"] = "principled_hair_melanin"
    return material


def make_scalp_material():
    material = bpy.data.materials.new("Aevrynd_AnatomicalScalpDensity_R381")
    material.use_nodes = True
    material.surface_render_method = "DITHERED"
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    attribute = nodes.new("ShaderNodeAttribute")
    attribute.attribute_name = SCALP_DENSITY_ATTRIBUTE
    shader.inputs["Base Color"].default_value = (0.012, 0.0032, 0.0015, 1.0)
    shader.inputs["Roughness"].default_value = 0.76
    shader.inputs["Specular IOR Level"].default_value = 0.17
    links.new(attribute.outputs["Fac"], shader.inputs["Alpha"])
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    material.diffuse_color = (0.012, 0.0032, 0.0015, SCALP_MAX_ALPHA)
    material["aevrynd_ownership"] = "procedural in-project"
    material["aevrynd_revision"] = "v249r381"
    return material


def create_curve_object(name, strands, layer, material, motion_group=None, root_radius=0.000060):
    data = bpy.data.hair_curves.new(f"{name}Data")
    data.add_curves([POINTS] * len(strands))
    data.points.foreach_set("position", [value for strand in strands for point in strand for value in point])
    radius = data.attributes.new("radius", "FLOAT", "POINT")
    radii = []
    for _strand in strands:
        for point_index in range(POINTS):
            t = point_index / (POINTS - 1)
            radii.append(root_radius * (1.0 - 0.72 * smoothstep((t - 0.58) / 0.42)))
    radius.data.foreach_set("value", radii)
    data.materials.append(material)
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = bpy.data.objects[RIG]
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = Matrix.Identity(4)
    if motion_group is not None:
        modifier = obj.modifiers.new("Aevrynd Semantic Groom Secondary Motion R381", "NODES")
        modifier.node_group = motion_group
    obj["aevrynd_layer"] = layer
    obj["aevrynd_revision"] = "v249r381"
    obj["aevrynd_curve_count"] = len(strands)
    obj["aevrynd_root_locked"] = True
    obj["aevrynd_collision_clearance_m"] = CLEARANCE
    return obj


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
body = bpy.data.objects[BODY]
body_tree = evaluated_tree(body)
motion_group = bpy.data.objects["AevryndFemalePrimaryClumps_R264"].modifiers[0].node_group
for name in OLD_HAIR:
    obj = bpy.data.objects.get(name)
    if obj:
        obj.hide_render = True
        obj.hide_viewport = True

hair_material = make_hair_material()
scalp_material = make_scalp_material()

# Owned scalp shadow shell, extracted from the current evaluated CC0 body.
depsgraph = bpy.context.evaluated_depsgraph_get()
evaluated_body = body.evaluated_get(depsgraph)
base_mesh = evaluated_body.to_mesh()
dense_source_data = base_mesh.copy()
dense_source = bpy.data.objects.new("AevryndScalpDenseSource_R381", dense_source_data)
scene.collection.objects.link(dense_source)
dense_source.matrix_world = evaluated_body.matrix_world.copy()
evaluated_body.to_mesh_clear()
dense_modifier = dense_source.modifiers.new("Aevrynd Scalp Boundary Densify R381", "SUBSURF")
dense_modifier.subdivision_type = "SIMPLE"
dense_modifier.levels = 2
dense_modifier.render_levels = 2
bpy.context.view_layer.update()
evaluated_dense_source = dense_source.evaluated_get(depsgraph)
evaluated_mesh = evaluated_dense_source.to_mesh()
world_vertices = [evaluated_dense_source.matrix_world @ vertex.co for vertex in evaluated_mesh.vertices]
world_normals = [(evaluated_dense_source.matrix_world.to_3x3() @ vertex.normal).normalized() for vertex in evaluated_mesh.vertices]
selected_polygons = []
for polygon in evaluated_mesh.polygons:
    center = evaluated_body.matrix_world @ polygon.center
    if center.y < -0.045:
        depth_lift = 0.006 * clamp((-center.y - 0.045) / 0.080)
        threshold = natural_hairline_z(center.x) + depth_lift
    else:
        threshold = 1.585
    if center.z >= threshold:
        selected_polygons.append(tuple(polygon.vertices))
used = sorted({index for polygon in selected_polygons for index in polygon})
remap = {source: destination for destination, source in enumerate(used)}
scalp_vertices = [world_vertices[index] + world_normals[index] * 0.0009 for index in used]
scalp_faces = [tuple(remap[index] for index in polygon) for polygon in selected_polygons]
scalp_density_values = [scalp_density(world_vertices[index]) for index in used]
scalp_data = bpy.data.meshes.new("AevryndFemaleSemanticScalpData_R381")
scalp_data.from_pydata(scalp_vertices, [], scalp_faces)
scalp_density_attribute = scalp_data.attributes.new(SCALP_DENSITY_ATTRIBUTE, "FLOAT", "POINT")
for index, value in enumerate(scalp_density_values):
    scalp_density_attribute.data[index].value = value
scalp_data.materials.append(scalp_material)
scalp = bpy.data.objects.new("AevryndFemaleSemanticScalp_R381", scalp_data)
scene.collection.objects.link(scalp)
scalp.parent = bpy.data.objects[RIG]
scalp.parent_type = "BONE"
scalp.parent_bone = "head"
scalp.matrix_world = Matrix.Identity(4)
scalp["aevrynd_layer"] = "hair.scalp_density_foundation.head_bound"
scalp["aevrynd_revision"] = "v249r381"
scalp["aevrynd_clearance_m"] = 0.0009
scalp.hide_render = False
scalp.hide_viewport = False
scalp["aevrynd_density_attribute"] = SCALP_DENSITY_ATTRIBUTE
scalp["aevrynd_density_alpha_max"] = SCALP_MAX_ALPHA
evaluated_dense_source.to_mesh_clear()
bpy.data.objects.remove(dense_source, do_unlink=True)
if dense_source_data.users == 0:
    bpy.data.meshes.remove(dense_source_data)

# Semantic guide families are generated by region, with shared low-frequency flow.
center = Vector((0.0, -0.012, 1.635))
radius_x, radius_y, radius_z = 0.083, 0.108, 0.096
guides = []
guide_regions = []
guide_index = 0
root_rows = 46
for row in range(root_rows):
    row_y = -0.110 + row * (0.190 / (root_rows - 1))
    base_y_norm = (row_y - center.y) / radius_y
    base_half_x = radius_x * math.sqrt(max(0.05, 1.0 - base_y_norm * base_y_norm))
    columns = max(8, round(15 * base_half_x / radius_x))
    for column in range(columns):
        root_seed = row * 53 + column
        y = row_y + (rand(root_seed, 39.0) - 0.5) * (0.190 / (root_rows - 1)) * 0.88
        y = max(-0.110, min(0.080, y))
        y_norm = (y - center.y) / radius_y
        half_x = radius_x * math.sqrt(max(0.05, 1.0 - y_norm * y_norm))
        unit = (column + 0.5 + (0.42 if row % 2 else 0.0)) / columns
        x = -half_x + 2.0 * half_x * unit
        x += (rand(root_seed, 40.0) - 0.5) * (2.0 * half_x / columns) * 0.72
        x = max(-half_x + 0.0003, min(half_x - 0.0003, x))
        seam = part_x(y)
        if abs(x - seam) < 0.0006:
            continue
        x_norm = x / radius_x
        z = center.z + radius_z * math.sqrt(max(0.0, 1.0 - x_norm * x_norm - y_norm * y_norm))
        nearest = body_tree.find_nearest(Vector((x, y, z)), 0.055)
        if nearest is None or nearest[1] is None:
            continue
        location, normal, _face, _distance = nearest
        normal = normal.normalized()
        if normal.z < -0.05:
            continue
        root = location + normal * CLEARANCE
        side = -1.0 if x < seam else 1.0
        front = clamp((-y - 0.010) / 0.100)
        back = clamp((y - 0.005) / 0.080)
        crown = clamp((z - 1.665) / 0.075)
        if front > 0.20 and root.z < natural_hairline_z(root.x) + 0.002:
            continue
        region = "front" if front > 0.30 else ("rear" if back > 0.35 else "crown")
        grouped_length = 0.010 * math.sin(root.x * 45.0 + root.y * 17.0)
        grouped_length += 0.006 * math.sin(root.x * 21.0 - root.y * 31.0 + 0.8)
        length = 0.225 + 0.050 * crown + 0.030 * back + 0.025 * (rand(guide_index, 1.0) - 0.5)
        length += grouped_length * (0.35 + 0.65 * back)
        lateral = (0.050 + 0.035 * crown + 0.030 * front) * (1.0 - 0.82 * back) + 0.006 * back
        silhouette_breakup = 0.008 * math.sin(root.y * 38.0 + root.x * 16.0)
        silhouette_breakup += 0.004 * math.sin(root.y * 71.0 - 0.6)
        end_x = clamp(root.x + side * (lateral - 0.006 * back + silhouette_breakup), -0.150, 0.150)
        end_y = root.y + 0.025 * back - 0.006 * front
        end_z = root.z - length
        p0 = root
        part_blend = 0.18 + 0.82 * smoothstep(abs(root.x - seam) / 0.025)
        root_spread = ((0.014 + 0.014 * front) * (1.0 - 0.65 * back) + 0.004 * back) * part_blend
        p1 = root + normal * (0.007 + 0.004 * crown) + Vector((side * root_spread, 0.0, 0.004))
        p2 = Vector((end_x - side * 0.012, end_y, end_z + 0.082))
        p3 = Vector((end_x, end_y, end_z))
        phase = rand(guide_index, 2.0) * math.tau
        wave_amp = 0.0035 + 0.0055 * rand(guide_index, 3.0)
        guide = []
        for point_index in range(POINTS):
            t = point_index / (POINTS - 1)
            point = bezier(p0, p1, p2, p3, t)
            flow_weight = smoothstep((t - 0.18) / 0.82)
            wave = math.sin(phase + t * math.tau * (0.62 + 0.25 * rand(guide_index, 4.0)))
            point.x += side * wave_amp * wave * flow_weight
            point.y += wave_amp * 0.38 * math.cos(phase + t * math.tau) * flow_weight
            if front > 0.25:
                avoid = 0.92 * front * smoothstep((t - 0.10) / 0.52)
                safe_x = side * (0.068 + 0.025 * smoothstep(t))
                point.x = min(point.x, point.x * (1.0 - avoid) + safe_x * avoid) if side < 0 else max(point.x, point.x * (1.0 - avoid) + safe_x * avoid)
            guide.append(point)
        guides.append(guide)
        guide_regions.append((root, normal, side, region, guide_index))
        guide_index += 1

# The visible center part ends near the crown.  Alternating bridge guides cross
# the rear seam and then fall toward the nape, preventing the split from opening
# into the large triangular gap seen in r360/r361 back views.
rear_bridge_guides = 0
for row in range(11):
    y = 0.000 + row * (0.078 / 10.0)
    y_norm = (y - center.y) / radius_y
    seam = part_x(y)
    for band in range(4):
        side = -1.0 if band < 2 else 1.0
        distance = 0.0035 + (band % 2) * 0.0040
        x = seam + side * distance
        x_norm = x / radius_x
        z = center.z + radius_z * math.sqrt(max(0.0, 1.0 - x_norm * x_norm - y_norm * y_norm))
        nearest = body_tree.find_nearest(Vector((x, y, z)), 0.050)
        if nearest is None or nearest[1] is None:
            continue
        location, normal, _face, _distance = nearest
        normal = normal.normalized()
        root = location + normal * CLEARANCE
        crossing = -side if (row + band) % 2 else side
        end_x = seam + crossing * (0.005 + 0.004 * rand(row * 9 + band, 13.0))
        end_y = root.y + 0.018
        end_z = root.z - (0.205 + 0.025 * rand(row * 9 + band, 14.0))
        p0 = root
        p1 = root + normal * 0.008 + Vector((crossing * 0.004, 0.004, 0.003))
        p2 = Vector((end_x - crossing * 0.003, end_y, end_z + 0.078))
        p3 = Vector((end_x, end_y, end_z))
        guide = []
        phase = rand(row * 9 + band, 15.0) * math.tau
        for point_index in range(POINTS):
            t = point_index / (POINTS - 1)
            point = bezier(p0, p1, p2, p3, t)
            point.x += 0.0018 * math.sin(phase + t * math.tau * 0.7) * smoothstep(t)
            guide.append(point)
        guides.append(guide)
        guide_regions.append((root, normal, crossing, "rear_bridge", guide_index))
        guide_index += 1
        rear_bridge_guides += 1

primary = []
fill = []
pruned_front_guides = 0
pruned_rear_guides = 0
for guide, (root, normal, side, region, index) in zip(guides, guide_regions):
    if region == "front":
        pruned_front_guides += 1
        continue
    if region == "rear":
        pruned_rear_guides += 1
        continue
    primary.append([point.copy() for point in guide])
    tangent = Vector((normal.z, 0.0, -normal.x)).normalized()
    bitangent = normal.cross(tangent).normalized()
    for follower in range(1, FOLLOWERS):
        angle = math.tau * rand(index * 31 + follower, 5.0)
        radius = 0.0007 + 0.0025 * math.sqrt(rand(index * 31 + follower, 6.0))
        offset = tangent * (math.cos(angle) * radius) + bitangent * (math.sin(angle) * radius)
        length_jitter = (rand(index * 31 + follower, 7.0) - 0.5) * 0.026
        phase = rand(index * 31 + follower, 8.0) * math.tau
        strand = []
        for point_index, base in enumerate(guide):
            t = point_index / (POINTS - 1)
            point = base + offset * (0.84 + 0.16 * smoothstep(t))
            point.z += length_jitter * smoothstep(t)
            fine = math.sin(phase + t * math.tau * 1.18) * 0.00065 * smoothstep(t)
            point.x += side * fine
            point.y += fine * 0.35
            strand.append(point)
        fill.append(strand)

# Staggered short roots erase the polygonal scalp boundary and establish a
# readable, asymmetric hairline before the long guide families take over.
transition = []
for sample in range(61):
    x = -0.080 + sample * (0.160 / 60.0)
    side = -1.0 if x < part_x(-0.090) else 1.0
    for layer in range(2):
        jitter = (rand(sample * 7 + layer, 11.0) - 0.5) * 0.0024
        target_z = natural_hairline_z(x) + jitter - layer * 0.0015
        nearest = body_tree.find_nearest(Vector((x, -0.105, target_z)), 0.060)
        if nearest is None or nearest[1] is None:
            continue
        location, normal, _face, _distance = nearest
        normal = normal.normalized()
        if normal.y > -0.15:
            continue
        root = location + normal * (CLEARANCE + 0.0004)
        temple = smoothstep((abs(x) - 0.058) / 0.022)
        length = 0.006 + 0.006 * rand(sample * 7 + layer, 12.0) + 0.006 * temple
        strand = []
        for point_index in range(POINTS):
            t = point_index / (POINTS - 1)
            ease = smoothstep(t)
            point = root + normal * (0.0018 * math.sin(math.pi * t))
            point.x += side * (0.002 + 0.004 * temple) * ease
            point.y += (0.004 + 0.004 * (1.0 - temple)) * ease
            # Center hairs rise into the hairline.  Temple hairs turn downward
            # into sideburns instead of becoming vertical antenna-like spikes.
            point.z += length * (1.0 - 1.80 * temple) * ease - 0.008 * temple * ease
            strand.append(point)
        transition.append(strand)

# A continuous front field replaces both the regular scalp rows and the 14
# discrete lock buckets.  Roots use deterministic low-discrepancy-like random
# sampling over the anatomical front scalp.  Each fibre owns its path; no row
# or parent follower family can appear as a dark band.
front_surface_flow = []
front_attempts = 9200
for sample in range(front_attempts):
    y = -0.110 + 0.086 * rand(sample, 41.0)
    y_norm = (y - center.y) / radius_y
    half_x = radius_x * math.sqrt(max(0.05, 1.0 - y_norm * y_norm))
    seam = part_x(y)
    x = -half_x + 2.0 * half_x * rand(sample, 42.0)
    if abs(x - seam) < 0.00045:
        continue
    x_norm = x / radius_x
    z = center.z + radius_z * math.sqrt(max(0.0, 1.0 - x_norm * x_norm - y_norm * y_norm))
    nearest = body_tree.find_nearest(Vector((x, y, z)), 0.055)
    if nearest is None or nearest[1] is None:
        continue
    location, normal, _face, _distance = nearest
    normal = normal.normalized()
    if normal.z < -0.05 or normal.y > 0.12:
        continue
    if location.z < natural_hairline_z(location.x) + 0.0015:
        continue
    root = location + normal * (CLEARANCE + 0.00035 + 0.00035 * rand(sample, 43.0))
    side = -1.0 if root.x < seam else 1.0
    front = clamp((-root.y - 0.006) / 0.104)
    crown = clamp((root.z - 1.660) / 0.075)
    temple = smoothstep((abs(root.x) - 0.055) / 0.025)

    # Spatially continuous waves create broad locks without assigning fibres to
    # a finite set of guides.  Nearby roots correlate; boundaries never jump.
    field_phase = root.x * 83.0 + root.y * 37.0
    lock_wave = math.sin(field_phase) * 0.007 + math.sin(field_phase * 0.47 + 1.3) * 0.004
    length = 0.205 + 0.042 * crown + 0.020 * front + 0.018 * (rand(sample, 44.0) - 0.5)
    lateral = 0.058 + 0.030 * crown + 0.022 * front + lock_wave
    end_x = max(-0.145, min(0.145, root.x + side * lateral))
    end_y = root.y - 0.005 * front + 0.005 * (rand(sample, 45.0) - 0.5)
    end_z = root.z - length - 0.008 * temple
    root_spread = (0.010 + 0.012 * front) * (0.35 + 0.65 * smoothstep(abs(root.x - seam) / 0.026))
    p0 = root
    p1 = root + normal * (0.006 + 0.003 * crown) + Vector((side * root_spread, 0.001 * math.sin(field_phase), 0.006 + 0.004 * crown))
    p2 = Vector((end_x - side * (0.010 + 0.006 * crown), end_y, end_z + 0.074 + 0.018 * crown))
    p3 = Vector((end_x, end_y, end_z))
    phase = field_phase + (rand(sample, 46.0) - 0.5) * 0.65
    strand = []
    for point_index in range(POINTS):
        t = point_index / (POINTS - 1)
        point = bezier(p0, p1, p2, p3, t)
        flow_weight = smoothstep((t - 0.12) / 0.88)
        point.x += side * (0.0018 * math.sin(phase + t * math.tau * 0.68) + 0.00035 * math.sin(phase * 1.9 + t * math.tau * 1.4)) * flow_weight
        point.y += 0.0007 * math.cos(phase + t * math.tau) * flow_weight
        if front > 0.25:
            avoid = 0.90 * front * smoothstep((t - 0.10) / 0.55)
            safe_x = side * (0.067 + 0.026 * smoothstep(t))
            point.x = min(point.x, point.x * (1.0 - avoid) + safe_x * avoid) if side < 0 else max(point.x, point.x * (1.0 - avoid) + safe_x * avoid)
        strand.append(point)
    front_surface_flow.append(strand)

# Continuous rear roots replace the cloned rear follower rows.  Smooth spatial
# functions correlate neighboring strands into locks without discrete buckets.
rear_surface_flow = []
rear_attempts = 9200
for sample in range(rear_attempts):
    y = 0.004 + 0.080 * rand(sample, 51.0)
    y_norm = (y - center.y) / radius_y
    half_x = radius_x * math.sqrt(max(0.05, 1.0 - y_norm * y_norm))
    seam = part_x(y)
    x = -half_x + 2.0 * half_x * rand(sample, 52.0)
    if abs(x - seam) < 0.00055:
        continue
    x_norm = x / radius_x
    z = center.z + radius_z * math.sqrt(max(0.0, 1.0 - x_norm * x_norm - y_norm * y_norm))
    nearest = body_tree.find_nearest(Vector((x, y, z)), 0.055)
    if nearest is None or nearest[1] is None:
        continue
    location, normal, _face, _distance = nearest
    normal = normal.normalized()
    if normal.z < -0.08:
        continue
    root = location + normal * (CLEARANCE + 0.00035 + 0.00035 * rand(sample, 53.0))
    side = -1.0 if root.x < seam else 1.0
    back = clamp((root.y - 0.002) / 0.084)
    crown = clamp((root.z - 1.655) / 0.080)
    spatial_phase = root.x * 39.0 + root.y * 27.0
    grouped_length = 0.010 * math.sin(spatial_phase) + 0.006 * math.sin(spatial_phase * 0.53 + 1.1)
    length = 0.232 + 0.042 * crown + 0.025 * back + grouped_length
    lateral = 0.010 + 0.014 * crown + 0.006 * math.sin(spatial_phase * 0.72)
    end_x = max(-0.132, min(0.132, root.x + side * lateral))
    end_y = root.y + 0.020 + 0.012 * back + 0.004 * (rand(sample, 54.0) - 0.5)
    end_z = root.z - length + 0.006 * (rand(sample, 55.0) - 0.5)
    p0 = root
    p1 = root + normal * (0.007 + 0.003 * crown) + Vector((side * (0.003 + 0.003 * crown), 0.006, 0.005))
    p2 = Vector((end_x - side * 0.004, end_y - 0.006, end_z + 0.082 + 0.014 * crown))
    p3 = Vector((end_x, end_y, end_z))
    phase = spatial_phase + (rand(sample, 56.0) - 0.5) * 0.72
    strand = []
    for point_index in range(POINTS):
        t = point_index / (POINTS - 1)
        point = bezier(p0, p1, p2, p3, t)
        flow = smoothstep((t - 0.14) / 0.86)
        point.x += side * (0.0017 * math.sin(phase + t * math.tau * 0.72) + 0.00035 * math.sin(phase * 1.8 + t * math.tau * 1.35)) * flow
        point.y += 0.0008 * math.cos(phase + t * math.tau) * flow
        strand.append(point)
    rear_surface_flow.append(strand)

primary_obj = create_curve_object("AevryndFemaleSemanticPrimary_R381", primary, "hair.primary_semantic_guides.dynamic", hair_material, motion_group, root_radius=0.000046)
fill_obj = create_curve_object("AevryndFemaleSemanticFill_R381", fill, "hair.secondary_semantic_followers.dynamic", hair_material, motion_group, root_radius=0.000018)
transition_obj = create_curve_object("AevryndFemaleHairlineTransition_R381", transition, "hair.hairline_microclumps.head_bound", hair_material, root_radius=0.000010)
front_flow_obj = create_curve_object("AevryndFemaleFrontSurfaceFlow_R381", front_surface_flow, "hair.front_surface_flow.dynamic", hair_material, motion_group, root_radius=0.000016)
rear_flow_obj = create_curve_object("AevryndFemaleRearSurfaceFlow_R381", rear_surface_flow, "hair.rear_surface_flow.dynamic", hair_material, motion_group, root_radius=0.000016)
hair_objects = (primary_obj, fill_obj, transition_obj, front_flow_obj, rear_flow_obj)

# Alternating pose projection keeps all raw strands outside the current body in both review poses.
projection_counts = {}
for iteration in range(3):
    for frame in (1, 20):
        scene.frame_set(frame)
        tree = evaluated_tree(body)
        moved = 0
        for obj in hair_objects:
            target_clearance = FRONT_FLOW_CLEARANCE if obj in (front_flow_obj, rear_flow_obj) else CLEARANCE
            inverse = obj.matrix_world.inverted()
            for point in obj.data.points:
                world = obj.matrix_world @ point.position
                nearest = tree.find_nearest(world, 0.18)
                if nearest is None or nearest[1] is None:
                    continue
                location, normal, _face, _distance = nearest
                normal = normal.normalized()
                if (world - location).dot(normal) < target_clearance:
                    point.position = inverse @ (location + normal * target_clearance)
                    moved += 1
            obj.data.update_tag()
        projection_counts[f"iteration_{iteration + 1}_frame_{frame}"] = moved

for name in ("Aevrynd R249 Key", "Aevrynd R249 Fill", "Aevrynd R249 Rim"):
    bpy.data.objects[name].data.energy *= 1.35

# The denser semantic groom blocks substantially more of the key/fill rig than
# the previous card groom.  Add a very low-energy, broad frontal bounce so the
# face keeps the accepted r351 skin exposure while retaining hair contact
# shadows.  This light belongs to the review rig; it is not a runtime asset.
face_fill_data = bpy.data.lights.get("Aevrynd R381 Face Bounce")
if face_fill_data is None:
    face_fill_data = bpy.data.lights.new("Aevrynd R381 Face Bounce", "AREA")
face_fill_data.energy = 8.0
face_fill_data.shape = "DISK"
face_fill_data.size = 0.45
face_fill_data.color = (0.86, 0.92, 1.0)
face_fill = bpy.data.objects.get("Aevrynd R381 Face Bounce")
if face_fill is None:
    face_fill = bpy.data.objects.new("Aevrynd R381 Face Bounce", face_fill_data)
    scene.collection.objects.link(face_fill)
face_fill.location = (0.0, -0.90, 1.48)
look_at(face_fill, (0.0, -0.01, 1.52))
face_fill["aevrynd_layer"] = "review.lighting.face_bounce"
face_fill["aevrynd_runtime_asset"] = False
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.view_settings.exposure = 0.0
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
views = (
    ("01-front-f01", 1, (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
    ("02-hairline-f01", 1, (0.0, -0.57, 1.76), (0.0, -0.02, 1.64), 92),
    ("03-top-f01", 1, (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
    ("04-three-quarter-f01", 1, (0.45, -0.66, 1.60), (0.0, -0.005, 1.56), 84),
    ("05-profile-f01", 1, (0.68, -0.03, 1.60), (0.0, 0.0, 1.56), 88),
    ("06-back-f01", 1, (0.0, 0.90, 1.59), (0.0, 0.0, 1.56), 82),
    ("07-front-f20", 20, (0.0, -0.76, 1.58), (0.0, -0.015, 1.56), 84),
    ("08-three-quarter-f20", 20, (0.45, -0.66, 1.60), (0.0, -0.005, 1.56), 84),
)
for label, frame, location, target, lens in views:
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(RENDER_DIR / f"{label}.png")
    bpy.ops.render.render(write_still=True)

scene.frame_set(1)
scene["aevrynd_mainline_revision"] = "v249r381-continuous-rear-surface-flow"
scene["aevrynd_release_state"] = "TECHNICAL_AND_VISUAL_AUDITS_REQUIRED"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "renderDirectory": str(RENDER_DIR),
    "guideCount": len(guides),
    "visiblePrimaryGuideCount": len(primary),
    "prunedFrontGridGuides": pruned_front_guides,
    "prunedRearGridGuides": pruned_rear_guides,
    "staggeredRootRows": root_rows,
    "primaryCurves": len(primary),
    "fillCurves": len(fill),
    "pointCount": (len(primary) + len(fill) + len(transition) + len(front_surface_flow) + len(rear_surface_flow)) * POINTS,
    "followersPerGuideIncludingPrimary": FOLLOWERS,
    "transitionCurves": len(transition),
    "frontSurfaceFlowCurves": len(front_surface_flow),
    "frontSurfaceFlowAttempts": front_attempts,
    "rearSurfaceFlowCurves": len(rear_surface_flow),
    "rearSurfaceFlowAttempts": rear_attempts,
    "fiberRootRadiiM": {
        "primary": 0.000046,
        "secondary": 0.000018,
        "hairline": 0.000010,
        "frontSurfaceFlow": 0.000016,
        "rearSurfaceFlow": 0.000016,
    },
    "scalpRendered": True,
    "visibleScalpSource": BODY,
    "scalpDensityAttribute": SCALP_DENSITY_ATTRIBUTE,
    "scalpDensityAlphaRange": [min(scalp_density_values), max(scalp_density_values)],
    "rearBridgeGuides": rear_bridge_guides,
    "layers": [scalp.get("aevrynd_layer"), primary_obj.get("aevrynd_layer"), fill_obj.get("aevrynd_layer"), transition_obj.get("aevrynd_layer"), front_flow_obj.get("aevrynd_layer"), rear_flow_obj.get("aevrynd_layer")],
    "collisionClearanceM": CLEARANCE,
    "frontFlowCollisionClearanceM": FRONT_FLOW_CLEARANCE,
    "crownPartDensityMinimum": 0.55,
    "groupedEndSilhouette": True,
    "templeTransitionDirection": "downward_sideburn",
    "poseProjectionCounts": projection_counts,
    "secondaryMotionNodeGroup": motion_group.name,
    "reviewFaceBounce": {
        "object": face_fill.name,
        "energy": face_fill_data.energy,
        "sizeM": face_fill_data.size,
        "runtimeAsset": False,
        "reason": "Calibrated against the r358 accepted skin mean after adding the translucent density foundation.",
    },
    "ownedAssetOnly": True,
    "websitePromotionApproved": False,
    "status": "TECHNICAL_AND_VISUAL_AUDITS_REQUIRED",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R381_CONTINUOUS_REAR_SURFACE_FLOW=" + json.dumps(report, sort_keys=True))




















