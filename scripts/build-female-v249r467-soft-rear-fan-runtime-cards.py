import json
import math
import random
from pathlib import Path

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-tail-collision-envelope-r452-study.blend"
OUTPUT = ASSETS / "aevrynd-female-authoring-v249-mainline-runtime-soft-rear-fan-cards-r467.blend"
REPORT = ASSETS / "female-v249-mainline-runtime-soft-rear-fan-cards-r467.build-report.json"
TEXTURE = ASSETS / "textures/aevrynd-owned-hair-card-atlas-r467.png"
PART_TEXTURE = ASSETS / "textures/aevrynd-owned-part-root-density-r467.png"
RUNTIME_DIR = ASSETS / "runtime-groom-r467"
GLB = RUNTIME_DIR / "aevrynd-female-hair-runtime-r467.glb"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r467-runtime-soft-rear-fan-cards"
BODY = "AevryndFemaleBodyBaseV118"
RIG = "AevryndFemaleRig"
POINTS = 24
SLOTS = 4
REGIONS = {
    "front": ("AevryndFemaleFrontSurfaceFlow_R383", 420, 0.0017),
    "crown": ("AevryndFemaleCrownSurfaceFlow_R383", 420, 0.0019),
    "rear": ("AevryndFemaleRearSurfaceFlow_R383", 480, 0.0021),
    "hairline": ("AevryndFemaleHairlineTransition_R383", 72, 0.00022),
}
CHAINS = {
    "hair_dyn.L.front": (-0.082, -0.030),
    "hair_dyn.R.front": (0.082, -0.030),
    "hair_dyn.L.back": (-0.065, 0.060),
    "hair_dyn.C.back": (0.000, 0.078),
    "hair_dyn.R.back": (0.065, 0.060),
}


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def smoothstep(value):
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def create_owned_atlas():
    width, height = 512, 1024
    slot_width = width // SLOTS
    pixels = [0.0] * (width * height * 4)
    slot_reports = []
    for slot in range(SLOTS):
        rng = random.Random(385100 + slot)
        count = (5, 7, 9, 12)[slot]
        fibers = []
        for index in range(count):
            center = (index + 0.5) / count + rng.uniform(-0.018, 0.018)
            fibers.append((center, rng.uniform(0.010, 0.024), rng.uniform(0.004, 0.024), rng.uniform(-math.pi, math.pi), rng.uniform(0.72, 1.0)))
        alpha_sum = 0.0
        coverage = 0
        for y in range(height):
            v = y / (height - 1)
            root_fade = 0.34 + 0.66 * smoothstep(v / 0.055)
            tip_fade = 1.0 - smoothstep((v - (0.76 + 0.035 * slot)) / (0.24 - 0.035 * slot))
            for local_x in range(slot_width):
                u = local_x / (slot_width - 1)
                edge = 1.0 - smoothstep((abs(u - 0.5) - 0.43) / 0.07)
                alpha = 0.0
                tone = 0.0
                for center, radius, wave, phase, fiber_tone in fibers:
                    path = center + wave * math.sin(v * math.tau * (0.72 + 0.12 * slot) + phase)
                    strength = math.exp(-((u - path) / radius) ** 2)
                    alpha = 1.0 - (1.0 - alpha) * (1.0 - strength * 0.88)
                    tone = max(tone, strength * fiber_tone)
                root_veil = (0.025 + 0.012 * slot) * (1.0 - smoothstep((v - 0.01) / 0.12))
                alpha = clamp((alpha + root_veil) * edge * root_fade * tip_fade)
                shade = 0.60 + 0.40 * tone
                x = slot * slot_width + local_x
                offset = (y * width + x) * 4
                pixels[offset:offset + 4] = (0.155 * shade, 0.058 * shade, 0.030 * shade, alpha)
                alpha_sum += alpha
                coverage += int(alpha > 0.08)
        slot_reports.append({"slot": slot, "fibers": count, "meanAlpha": alpha_sum / (height * slot_width), "coverageAbove008": coverage / (height * slot_width)})
    old = bpy.data.images.get("AevryndOwnedHairCardAtlas_R467")
    if old:
        bpy.data.images.remove(old)
    image = bpy.data.images.new("AevryndOwnedHairCardAtlas_R467", width=width, height=height, alpha=True)
    image.pixels.foreach_set(pixels)
    TEXTURE.parent.mkdir(parents=True, exist_ok=True)
    image.filepath_raw = str(TEXTURE)
    image.file_format = "PNG"
    image.save()
    image.pack()
    image["aevrynd_ownership"] = "procedurally generated in-project"
    image["aevrynd_license"] = "Aevrynd-owned"
    image["aevrynd_revision"] = "v249r467"
    return image, [width, height], slot_reports


def make_material(image):
    material = bpy.data.materials.new("Aevrynd_RuntimeHairCards_R467")
    material.use_nodes = True
    material.surface_render_method = "DITHERED"
    material.use_transparency_overlap = False
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = image
    shader.inputs["Roughness"].default_value = 0.72
    shader.inputs["Specular IOR Level"].default_value = 0.05
    if shader.inputs.get("Anisotropic IOR Level"):
        shader.inputs["Anisotropic IOR Level"].default_value = 0.18
    links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    links.new(texture.outputs["Alpha"], shader.inputs["Alpha"])
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    material["aevrynd_ownership"] = "procedurally generated in-project"
    material["aevrynd_layer"] = "material.hair.runtime_cards.alpha"
    material["aevrynd_revision"] = "v249r467"
    return material


def create_part_root_texture():
    width, height = 256, 512
    rng = random.Random(405771)
    fibers = {side: [] for side in (-1, 1)}
    for side in (-1, 1):
        for index in range(300):
            root_v = (index + 0.18 + rng.random() * 0.64) / 300.0
            sweep = rng.uniform(0.030, 0.115)
            wave = rng.uniform(0.0007, 0.0042)
            phase = rng.uniform(-math.pi, math.pi)
            thickness = rng.uniform(0.00034, 0.00086)
            strength = rng.uniform(0.38, 0.70)
            fibers[side].append((root_v, sweep, wave, phase, thickness, strength))
    pixels = [0.0] * (width * height * 4)
    for y in range(height):
        v = y / (height - 1)
        end_fade = smoothstep(v / 0.18) * (1.0 - smoothstep((v - 0.82) / 0.18))
        for x in range(width):
            u = x / (width - 1)
            signed = (u - 0.5) * 2.0
            side = -1 if signed < 0.0 else 1
            distance = abs(signed)
            # Preserve a narrow, slightly irregular visible scalp part.
            gap = 0.040 + 0.010 * math.sin(v * 19.0) + 0.006 * math.sin(v * 47.0 + 0.8)
            part_fade = smoothstep((distance - gap) / 0.055)
            edge_fade = 1.0 - smoothstep((distance - 0.82) / 0.18)
            fiber_alpha = 0.0
            for root_v, sweep, wave, phase, thickness, strength in fibers[side]:
                predicted_v = root_v + sweep * distance + wave * math.sin(distance * math.tau * 1.7 + phase)
                strand = math.exp(-((v - predicted_v) / thickness) ** 2)
                fiber_alpha = 1.0 - (1.0 - fiber_alpha) * (1.0 - strand * strength)
            undercoat = 0.36 * smoothstep((distance - gap) / 0.11)
            alpha = clamp((fiber_alpha + undercoat) * part_fade * edge_fade * end_fade)
            shade = 0.72 + 0.22 * fiber_alpha
            offset = (y * width + x) * 4
            pixels[offset:offset + 4] = (0.142 * shade, 0.052 * shade, 0.027 * shade, alpha)
    image = bpy.data.images.new("AevryndOwnedPartRootDensity_R467", width=width, height=height, alpha=True)
    image.pixels.foreach_set(pixels)
    image.filepath_raw = str(PART_TEXTURE)
    image.file_format = "PNG"
    image.save()
    image.pack()
    image["aevrynd_ownership"] = "procedurally generated in-project"
    image["aevrynd_license"] = "Aevrynd-owned"
    image["aevrynd_revision"] = "v249r467"
    return image, [width, height]


def build_part_root_density(rig, image):
    tree = body_tree()
    columns, rows = 35, 49
    vertices, valid = [], []
    for row in range(rows):
        v = row / (rows - 1)
        y = -0.115 + 0.210 * v
        for column in range(columns):
            u = column / (columns - 1)
            x = -0.036 + 0.072 * u
            hit = tree.ray_cast(Vector((x, y, 1.92)), Vector((0.0, 0.0, -1.0)), 0.50)
            if hit[0] is None or hit[0].z < 1.657:
                point, normal = Vector((x, y, 1.60)), Vector((0.0, 0.0, 1.0))
                valid.append(False)
            else:
                point, normal = hit[0], hit[1].normalized()
                valid.append(True)
            vertices.append(point + normal * 0.0026)
    faces = []
    for row in range(rows - 1):
        for column in range(columns - 1):
            a = row * columns + column
            face = (a, a + 1, a + columns + 1, a + columns)
            if all(valid[index] for index in face):
                faces.append(face)
    mesh = bpy.data.meshes.new("AevryndFemaleRuntimePartRootDensity_R467_Data")
    mesh.from_pydata(vertices, [], faces)
    uv = mesh.uv_layers.new(name="AevryndPartRootDensityUV")
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            vertex_index = mesh.loops[loop_index].vertex_index
            row, column = divmod(vertex_index, columns)
            uv.data[loop_index].uv = (column / (columns - 1), row / (rows - 1))
    uv.active_render = True
    material = bpy.data.materials.new("Aevrynd_RuntimePartRootDensity_R467")
    material.use_nodes = True
    material.surface_render_method = "DITHERED"
    material.use_transparency_overlap = False
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = image
    shader.inputs["Roughness"].default_value = 0.91
    shader.inputs["Specular IOR Level"].default_value = 0.025
    links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    links.new(texture.outputs["Alpha"], shader.inputs["Alpha"])
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    material["aevrynd_ownership"] = "procedurally generated in-project"
    material["aevrynd_layer"] = "material.hair.runtime_part_root_density"
    material["aevrynd_revision"] = "v249r467"
    mesh.materials.append(material)
    obj = bpy.data.objects.new("AevryndFemaleRuntimePartRootDensity_R467", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = rig
    obj.matrix_parent_inverse = rig.matrix_world.inverted()
    head = obj.vertex_groups.new(name="head")
    head.add(list(range(len(vertices))), 1.0, "REPLACE")
    modifier = obj.modifiers.new("Aevrynd Runtime Part Root Armature", "ARMATURE")
    modifier.object = rig
    obj["aevrynd_layer"] = "hair.runtime_part_root_density.head_bound.alpha"
    obj["aevrynd_revision"] = "v249r467"
    obj["aevrynd_source"] = BODY
    obj["aevrynd_face_count"] = len(faces)
    return obj


def curve_paths(obj):
    data = obj.data
    matrix = obj.matrix_world
    count = len(data.points) // POINTS
    return [[matrix @ data.points[curve * POINTS + point].position for point in range(POINTS)] for curve in range(count)]


def feature(path):
    values = []
    for index, weight in ((0, 5.0), (5, 2.5), (12, 1.4), (23, 1.0)):
        point = path[index]
        values.extend((point.x * weight, point.y * weight, point.z * weight))
    return values


def farthest_paths(paths, count):
    if len(paths) <= count:
        return paths
    features = [feature(path) for path in paths]
    chosen = [min(range(len(paths)), key=lambda i: features[i][0])]
    distances = [sum((a - b) ** 2 for a, b in zip(item, features[chosen[0]])) for item in features]
    while len(chosen) < count:
        candidate = max(range(len(paths)), key=distances.__getitem__)
        chosen.append(candidate)
        center = features[candidate]
        for index, item in enumerate(features):
            distance = sum((a - b) ** 2 for a, b in zip(item, center))
            if distance < distances[index]:
                distances[index] = distance
    return [paths[index] for index in chosen]


def centered_root_weave_paths(paths, count, near_count):
    near_limit = 0.010
    near_left = [path for path in paths if -near_limit <= path[0].x < 0.0]
    near_right = [path for path in paths if 0.0 < path[0].x <= near_limit]
    half = near_count // 2
    # First restrict the pool to roots physically closest to the part, then
    # distribute those roots along the scalp.  The former farthest-only pass
    # preserved spatial diversity but could omit the roots that actually close
    # the broad runtime gap.
    left_pool = sorted(near_left, key=lambda path: abs(path[0].x))[: max(half * 6, half)]
    right_quota = near_count - half
    right_pool = sorted(near_right, key=lambda path: abs(path[0].x))[: max(right_quota * 6, right_quota)]
    selected_near = farthest_paths(left_pool, half) + farthest_paths(right_pool, right_quota)
    outer = [path for path in paths if abs(path[0].x) > near_limit]
    return selected_near + farthest_paths(outer, max(0, count - len(selected_near)))


def nearest_chain(point, region):
    choices = []
    for name, (x, y) in CHAINS.items():
        penalty = 0.020 if ((region in ("front", "hairline") and ".back" in name) or (region in ("rear", "crown") and ".front" in name)) else 0.0
        choices.append(((point.x - x) ** 2 + (point.y - y) ** 2 + penalty, name))
    return min(choices)[1]


def level_weights(t):
    raw = [max(0.0, 1.0 - abs(t - center) / 0.42) for center in (0.24, 0.57, 0.89)]
    total = sum(raw) or 1.0
    return [value / total for value in raw]


def synthetic_hairline_paths(count):
    tree = body_tree()
    rng = random.Random(391210)
    paths = []
    for index in range(count):
        u = (index + 0.5) / count
        root_x = -0.078 + 0.156 * u + rng.uniform(-0.00035, 0.00035)
        normalized_x = abs(root_x) / 0.078
        root_z = (
            1.674
            - 0.055 * normalized_x ** 1.55
            + 0.00035 * math.sin(index * 2.399)
            + 0.00022 * math.sin(index * 0.731)
            + rng.uniform(-0.00018, 0.00018)
        )
        hit = tree.ray_cast(Vector((root_x, -0.30, root_z)), Vector((0.0, 1.0, 0.0)), 0.50)
        if hit[0] is None:
            continue
        root = hit[0] + hit[1].normalized() * rng.uniform(0.0013, 0.0019)
        side_sign = -1.0 if root_x < 0.0 else 1.0
        if abs(root_x) < 0.004:
            side_sign = -1.0 if index % 2 == 0 else 1.0
        # Most visible edge fibers are short miniaturized hairs.  A small
        # transition population connects the edge into the primary groom.
        baby_hair = rng.random() < 0.92
        if baby_hair:
            sweep = rng.uniform(0.001, 0.006)
            rise = rng.uniform(0.001, 0.006)
            back = rng.uniform(0.005, 0.012)
        else:
            sweep = rng.uniform(0.004, 0.012)
            rise = rng.uniform(0.008, 0.018)
            back = rng.uniform(0.014, 0.028)
        path = []
        for point_index in range(POINTS):
            t = point_index / (POINTS - 1)
            ease = smoothstep(t)
            candidate = Vector((
                root.x + side_sign * sweep * ease,
                root.y + back * ease,
                root.z + rise * math.sin(0.78 * math.pi * t) + rng.uniform(-0.00035, 0.00035) * math.sin(math.pi * t),
            ))
            nearest = tree.find_nearest(candidate, 0.08)
            if nearest[0] is not None:
                offset = 0.00125 + 0.00075 * smoothstep(t) + 0.00025 * rng.random()
                candidate = nearest[0] + nearest[1].normalized() * offset
            path.append(candidate)
        paths.append(path)
    return paths


def resample_path_length(path, scale):
    if scale >= 0.999:
        return path
    source_position = [(len(path) - 1) * (point_index / (POINTS - 1)) * scale for point_index in range(POINTS)]
    result = []
    for position in source_position:
        low = int(math.floor(position))
        high = min(len(path) - 1, low + 1)
        blend = position - low
        result.append(path[low].lerp(path[high], blend))
    return result


def build_region_cards(region, source_name, card_count, half_width, material, rig):
    source = bpy.data.objects[source_name]
    if region == "hairline":
        paths = synthetic_hairline_paths(card_count)
    else:
        source_paths = curve_paths(source)
        if region == "front":
            source_paths = [path for path in source_paths if path[0].x * path[12].x > 0.0]
            paths = centered_root_weave_paths(source_paths, card_count, 120)
        elif region == "crown":
            paths = centered_root_weave_paths(source_paths, card_count, 144)
        else:
            paths = farthest_paths(source_paths, card_count)
    vertices, faces, weight_data = [], [], []
    slot_ids = []
    stride = POINTS * 2
    for card_index, path in enumerate(paths):
        root = path[0]
        near_part = region in ("front", "crown") and abs(root.x) <= 0.010
        if region == "front":
            cluster = 0.5 + 0.5 * math.sin(root.x * 52.0 + root.y * 19.0)
            scale = 0.82 + 0.17 * cluster
            path = resample_path_length(path, scale)
        elif region == "rear":
            phase = root.x * 43.0 + 1.35 * math.sin(root.y * 31.0)
            cluster = 0.5 + 0.5 * math.sin(phase)
            scale = 0.78 + 0.21 * cluster
            path = resample_path_length(path, scale)
        if region in ("front", "crown", "rear"):
            # Introduce coherent low-frequency bends without moving roots or
            # tail endpoints. Narrow crossed cards then overlap as soft locks
            # instead of reading as broad parallel sheets.
            phase = root.x * 37.0 + root.y * 23.0
            lateral = 0.0034 * math.sin(phase)
            depth = 0.0018 * math.sin(phase * 0.71 + 1.2)
            path = [
                point + Vector((lateral, depth, 0.0)) * math.sin(math.pi * (index / (POINTS - 1))) ** 2
                for index, point in enumerate(path)
            ]
        if region == "rear":
            # The source rear guides converge toward the nape and previously
            # formed one rectangular center veil. Fan central tails farther
            # than outer tails and add coherent lock-level depth variation.
            side_sign = -1.0 if root.x < -0.003 else 1.0 if root.x > 0.003 else (-1.0 if card_index % 2 else 1.0)
            root_u = clamp(abs(root.x) / 0.085)
            fan_amount = side_sign * (0.003 + 0.003 * (1.0 - root_u))
            lock_group = round(root.x / 0.016)
            lock_shift = 0.0035 * math.sin(lock_group * 1.91 + root.y * 17.0)
            depth_shift = 0.0022 * math.sin(lock_group * 2.47 + 0.8)
            spread_path = []
            for index, point in enumerate(path):
                t = index / (POINTS - 1)
                tail_weight = smoothstep((t - 0.24) / 0.76)
                middle_weight = math.sin(math.pi * t) ** 2
                spread_path.append(point + Vector((fan_amount * tail_weight + lock_shift * middle_weight, depth_shift * middle_weight, 0.0)))
            path = spread_path
        chain = nearest_chain(path[0], region)
        if region == "hairline":
            slot = 0
        elif region == "front" or near_part:
            # Dense atlas slots make each wide runtime card read as a lock,
            # rather than exposing four isolated parallel fibers.
            slot = 2 + ((card_index * 7) % 2)
        else:
            slot = (card_index * 3 + 1) % SLOTS
        slot_ids.append(slot)
        width_jitter = 0.90 + 0.20 * ((card_index * 37) % 101) / 100.0 if near_part else 0.84 + 0.28 * ((card_index * 37) % 101) / 100.0
        angle_limit = 10.0 if near_part else 24.0
        crossing_angle = math.radians(-angle_limit + 2.0 * angle_limit * ((card_index * 17) % 97) / 96.0)
        for point_index, point in enumerate(path):
            before = path[max(0, point_index - 1)]
            after = path[min(POINTS - 1, point_index + 1)]
            tangent = (after - before).normalized()
            outward = Vector((point.x, point.y + 0.012, point.z - 1.62))
            if outward.length < 1e-6:
                outward = Vector((0.0, -1.0, 0.0))
            outward.normalize()
            side = tangent.cross(outward)
            if side.length < 1e-6:
                side = tangent.cross(Vector((0.0, 1.0, 0.0)))
            side.normalize()
            side = Matrix.Rotation(crossing_angle, 4, tangent) @ side
            t = point_index / (POINTS - 1)
            root_floor = 0.82 if near_part else 0.48
            root_taper = root_floor + (1.0 - root_floor) * smoothstep(t / 0.15)
            tip_taper = 1.0 - 0.84 * smoothstep((t - 0.70) / 0.30)
            width = half_width * width_jitter * root_taper * tip_taper
            layer_max = 0.00065 if near_part else 0.00120
            layer = 0.00035 + layer_max * ((card_index * 29) % 89) / 88.0
            lift = outward * layer * math.sin(math.pi * t) ** 2
            center = point + lift
            vertices.extend((center - side * width, center + side * width))
            dynamic = smoothstep((t - 0.06) / 0.72)
            if region == "crown":
                dynamic *= 0.16
            elif near_part:
                # Part-adjacent roots must stay seated on the scalp while the
                # distal half still participates in the front hair motion.
                dynamic *= 0.42
            dynamic = min(dynamic * 1.20, 1.0)
            weight_data.extend(((chain, t, dynamic), (chain, t, dynamic)))
        base = card_index * stride
        for point_index in range(POINTS - 1):
            a = base + point_index * 2
            faces.append((a, a + 1, a + 3, a + 2))
    mesh = bpy.data.meshes.new(f"AevryndFemaleRuntimeCards_{region}_R467_Data")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(material)
    uv = mesh.uv_layers.new(name="AevryndRuntimeHairCardUV")
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            vertex_index = mesh.loops[loop_index].vertex_index
            card_index = vertex_index // stride
            local = vertex_index % stride
            point_index = local // 2
            side_index = local % 2
            slot = slot_ids[card_index]
            u = (slot + (0.03 if side_index == 0 else 0.97)) / SLOTS
            uv.data[loop_index].uv = (u, point_index / (POINTS - 1))
    uv.active_render = True
    obj = bpy.data.objects.new(f"AevryndFemaleRuntimeCards_{region}_R467", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = rig
    obj.matrix_parent_inverse = rig.matrix_world.inverted()
    head = obj.vertex_groups.new(name="head")
    for chain in CHAINS:
        for segment in range(3):
            obj.vertex_groups.new(name=f"{chain}.{segment + 1:02d}")
    for vertex_index, (chain, t, dynamic) in enumerate(weight_data):
        head.add([vertex_index], 1.0 - dynamic, "REPLACE")
        for segment, weight in enumerate(level_weights(t)):
            obj.vertex_groups[f"{chain}.{segment + 1:02d}"].add([vertex_index], dynamic * weight, "REPLACE")
    modifier = obj.modifiers.new("Aevrynd Runtime Hair Armature", "ARMATURE")
    modifier.object = rig
    obj["aevrynd_layer"] = f"hair.runtime_cards.{region}.dynamic.alpha"
    obj["aevrynd_revision"] = "v249r467"
    obj["aevrynd_source"] = source_name
    obj["aevrynd_card_count"] = len(paths)
    return obj


def build_runtime_scalp_cap(rig):
    roots = []
    hairline_roots = []
    for source_name, _count, _width in REGIONS.values():
        source = bpy.data.objects[source_name]
        source_roots = [source.matrix_world @ source.data.points[index].position for index in range(0, len(source.data.points), POINTS)]
        roots.extend(source_roots)
        if source_name == "AevryndFemaleHairlineTransition_R383":
            hairline_roots = source_roots
    root_tree = KDTree(len(roots))
    for index, point in enumerate(roots):
        root_tree.insert(point, index)
    root_tree.balance()

    body = bpy.data.objects[BODY]
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(depsgraph)
    source_mesh = evaluated.to_mesh()
    normal_matrix = evaluated.matrix_world.to_3x3().inverted().transposed()
    world_points = [evaluated.matrix_world @ vertex.co for vertex in source_mesh.vertices]
    world_normals = [(normal_matrix @ vertex.normal).normalized() for vertex in source_mesh.vertices]
    selected = []
    for polygon in source_mesh.polygons:
        center = sum((world_points[index] for index in polygon.vertices), Vector()) / len(polygon.vertices)
        if center.y < -0.075:
            local_samples = sorted(hairline_roots, key=lambda point: abs(point.x - center.x))[:12]
            local_hairline = max(local_samples, key=lambda point: point.z)
            if center.z < local_hairline.z - 0.004 or center.y < local_hairline.y - 0.004:
                continue
        nearest = root_tree.find(center)
        if center.z >= 1.605 and nearest and nearest[2] <= 0.028:
            selected.append(tuple(polygon.vertices))
    remap = {}
    vertices = []
    faces = []
    for face in selected:
        mapped = []
        for source_index in face:
            if source_index not in remap:
                remap[source_index] = len(vertices)
                vertices.append(world_points[source_index] + world_normals[source_index] * 0.0015)
            mapped.append(remap[source_index])
        faces.append(tuple(mapped))
    evaluated.to_mesh_clear()

    mesh = bpy.data.meshes.new("AevryndFemaleRuntimeScalpCap_R467_Data")
    mesh.from_pydata(vertices, [], faces)
    density = mesh.color_attributes.new(name="AevryndScalpDensity", type="FLOAT_COLOR", domain="POINT")
    for index, point in enumerate(vertices):
        local_samples = sorted(hairline_roots, key=lambda root: abs(root.x - point.x))[:12]
        local_hairline = max(local_samples, key=lambda root: root.z)
        vertical = smoothstep((point.z - (local_hairline.z - 0.004)) / 0.004)
        depth = smoothstep((point.y - (local_hairline.y - 0.004)) / 0.004)
        value = min(vertical, depth)
        density.data[index].color = (0.032, 0.011, 0.006, value)
    material = bpy.data.materials.new("Aevrynd_RuntimeScalpDensity_R467")
    material.diffuse_color = (0.032, 0.011, 0.006, 1.0)
    material.use_nodes = True
    material.surface_render_method = "DITHERED"
    material.use_transparency_overlap = False
    shader = next(node for node in material.node_tree.nodes if node.bl_idname == "ShaderNodeBsdfPrincipled")
    shader.inputs["Base Color"].default_value = material.diffuse_color
    shader.inputs["Roughness"].default_value = 0.93
    shader.inputs["Specular IOR Level"].default_value = 0.04
    vertex_color = material.node_tree.nodes.new("ShaderNodeVertexColor")
    vertex_color.layer_name = "AevryndScalpDensity"
    material.node_tree.links.new(vertex_color.outputs["Color"], shader.inputs["Base Color"])
    material.node_tree.links.new(vertex_color.outputs["Alpha"], shader.inputs["Alpha"])
    material["aevrynd_ownership"] = "procedurally generated in-project"
    material["aevrynd_layer"] = "material.hair.runtime_scalp_density"
    material["aevrynd_revision"] = "v249r467"
    mesh.materials.append(material)
    obj = bpy.data.objects.new("AevryndFemaleRuntimeScalpCap_R467", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = rig
    obj.matrix_parent_inverse = rig.matrix_world.inverted()
    head = obj.vertex_groups.new(name="head")
    head.add(list(range(len(vertices))), 1.0, "REPLACE")
    modifier = obj.modifiers.new("Aevrynd Runtime Scalp Armature", "ARMATURE")
    modifier.object = rig
    obj["aevrynd_layer"] = "hair.runtime_scalp_density.head_bound"
    obj["aevrynd_revision"] = "v249r467"
    obj["aevrynd_source"] = BODY
    obj["aevrynd_face_count"] = len(faces)
    return obj


def build_hairline_density_ribbon(rig):
    tree = body_tree()
    columns = 72
    rows = 9
    vertices = []
    alpha_values = []
    edge_rng = random.Random(466310)
    raw_edge = [edge_rng.uniform(-0.024, 0.024) for _ in range(columns)]
    edge_offsets = []
    for column in range(columns):
        neighbors = raw_edge[max(0, column - 3):min(columns, column + 4)]
        edge_offsets.append(sum(neighbors) / len(neighbors) + 0.010 * math.sin(column * 0.377 + 0.6))
    for row in range(rows):
        v = row / (rows - 1)
        for column in range(columns):
            u = column / (columns - 1)
            x = -0.079 + 0.158 * u
            normalized_x = abs(x) / 0.079
            edge_z = 1.6665 - 0.053 * normalized_x ** 1.55
            z = edge_z + 0.035 * v
            hit = tree.ray_cast(Vector((x, -0.30, z)), Vector((0.0, 1.0, 0.0)), 0.50)
            if hit[0] is None:
                point = Vector((x, -0.09, z))
            else:
                point = hit[0] + hit[1].normalized() * 0.00135
            vertices.append(point)
            edge_noise = edge_offsets[column]
            alpha_values.append(clamp(smoothstep((v - 0.035 - edge_noise) / 0.64) * 0.90))
    faces = []
    for row in range(rows - 1):
        for column in range(columns - 1):
            a = row * columns + column
            b = a + 1
            c = a + columns + 1
            d = a + columns
            faces.append((a, b, c, d))
    mesh = bpy.data.meshes.new("AevryndFemaleRuntimeHairlineDensity_R467_Data")
    mesh.from_pydata(vertices, [], faces)
    color = mesh.color_attributes.new(name="AevryndHairlineDensity", type="FLOAT_COLOR", domain="POINT")
    for index, alpha in enumerate(alpha_values):
        color.data[index].color = (0.032, 0.011, 0.006, alpha)
    material = bpy.data.materials.new("Aevrynd_RuntimeHairlineDensity_R467")
    material.use_nodes = True
    material.surface_render_method = "DITHERED"
    material.use_transparency_overlap = False
    shader = next(node for node in material.node_tree.nodes if node.bl_idname == "ShaderNodeBsdfPrincipled")
    shader.inputs["Roughness"].default_value = 0.94
    shader.inputs["Specular IOR Level"].default_value = 0.035
    vertex_color = material.node_tree.nodes.new("ShaderNodeVertexColor")
    vertex_color.layer_name = "AevryndHairlineDensity"
    material.node_tree.links.new(vertex_color.outputs["Color"], shader.inputs["Base Color"])
    material.node_tree.links.new(vertex_color.outputs["Alpha"], shader.inputs["Alpha"])
    material["aevrynd_ownership"] = "procedurally generated in-project"
    material["aevrynd_layer"] = "material.hair.runtime_hairline_density"
    material["aevrynd_revision"] = "v249r467"
    mesh.materials.append(material)
    obj = bpy.data.objects.new("AevryndFemaleRuntimeHairlineDensity_R467", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = rig
    obj.matrix_parent_inverse = rig.matrix_world.inverted()
    head = obj.vertex_groups.new(name="head")
    head.add(list(range(len(vertices))), 1.0, "REPLACE")
    modifier = obj.modifiers.new("Aevrynd Runtime Hairline Density Armature", "ARMATURE")
    modifier.object = rig
    obj["aevrynd_layer"] = "hair.runtime_scalp_hairline_density.head_bound.alpha"
    obj["aevrynd_revision"] = "v249r467"
    obj["aevrynd_source"] = BODY
    obj["aevrynd_face_count"] = len(faces)
    return obj


def body_tree():
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = bpy.data.objects[BODY].evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(points, faces, all_triangles=False)


def evaluated_points(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    return [evaluated.matrix_world @ vertex.co for vertex in evaluated.data.vertices]


def repair_clearance(objects, target=0.0010):
    tree = body_tree()
    result = {}
    for obj in objects:
        matrix, inverse = obj.matrix_world.copy(), obj.matrix_world.inverted()
        repaired = 0
        before = math.inf
        for vertex in obj.data.vertices:
            world = matrix @ vertex.co
            hit = tree.find_nearest(world, 0.20)
            if hit is None or hit[1] is None:
                continue
            normal = hit[1].normalized()
            signed = (world - hit[0]).dot(normal)
            before = min(before, signed)
            if signed < target:
                vertex.co = inverse @ (hit[0] + normal * target)
                repaired += 1
        obj.data.update()
        result[obj.name] = {"targetM": target, "beforeMinimumSignedM": before, "repairedVertices": repaired}
    return result


def repair_dynamic_card_envelope(scene, rig, objects, frames=(1, 20, 33, 61), target=0.0020, max_passes=4):
    """Move complete card tails in head space using the deepest animated collision."""
    body = bpy.data.objects[BODY]
    passes = []
    for pass_index in range(1, max_passes + 1):
        corrections = {obj.name: {} for obj in objects}
        frame_stats = {}
        for frame in frames:
            scene.frame_set(frame)
            bpy.context.view_layer.update()
            tree = body_tree()
            head_world = rig.matrix_world @ rig.pose.bones["head"].matrix
            world_to_head = head_world.inverted().to_3x3()
            frame_stats[str(frame)] = {}
            for obj in objects:
                points = evaluated_points(obj)
                penetrating = 0
                minimum = None
                for vertex_index, point in enumerate(points):
                    hit = tree.find_nearest(point, 0.025)
                    if hit is None or hit[1] is None:
                        continue
                    signed = (point - hit[0]).dot(hit[1].normalized())
                    if signed >= -0.0005:
                        continue
                    penetrating += 1
                    minimum = signed if minimum is None else min(minimum, signed)
                    card_index = vertex_index // (POINTS * 2)
                    segment = (vertex_index % (POINTS * 2)) // 2
                    head_delta = world_to_head @ (hit[1].normalized() * (target - signed))
                    previous = corrections[obj.name].get(card_index)
                    if previous is None or signed < previous[0]:
                        corrections[obj.name][card_index] = (signed, segment, head_delta)
                frame_stats[str(frame)][obj.name] = {
                    "penetratingVertices": penetrating,
                    "minimumSignedM": minimum,
                }
        affected = sum(len(value) for value in corrections.values())
        if not affected:
            passes.append({"pass": pass_index, "affectedCards": 0, "frames": frame_stats})
            break
        scene.frame_set(1)
        bpy.context.view_layer.update()
        head_world = rig.matrix_world @ rig.pose.bones["head"].matrix
        applied = {}
        for obj in objects:
            local_delta_matrix = obj.matrix_world.inverted().to_3x3() @ head_world.to_3x3()
            maximum = 0.0
            for card_index, (_signed, hit_segment, head_delta) in corrections[obj.name].items():
                local_delta = local_delta_matrix @ head_delta
                maximum = max(maximum, local_delta.length)
                ramp_end = max(5, hit_segment)
                for segment in range(4, POINTS):
                    weight = smoothstep((segment - 4) / (ramp_end - 4)) if segment < ramp_end else 1.0
                    base = card_index * POINTS * 2 + segment * 2
                    obj.data.vertices[base].co += local_delta * weight
                    obj.data.vertices[base + 1].co += local_delta * weight
            obj.data.update()
            applied[obj.name] = {"correctedCards": len(corrections[obj.name]), "maximumDisplacementM": maximum}
        passes.append({"pass": pass_index, "affectedCards": affected, "frames": frame_stats, "applied": applied})
    scene.frame_set(1)
    bpy.context.view_layer.update()
    return passes


def render(camera, frame, label, location, target, lens):
    scene = bpy.context.scene
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(RENDER_DIR / f"{label}.png")
    bpy.ops.render.render(write_still=True)


def enforce_hair_bone_settle(scene, rig):
    hair_bones = [bone for bone in rig.pose.bones if bone.name.startswith("hair_dyn.")]
    scene.frame_set(1)
    bpy.context.view_layer.update()
    rest = {bone.name: bone.matrix_basis.copy() for bone in hair_bones}
    scene.frame_set(61)
    for bone in hair_bones:
        bone.matrix_basis = rest[bone.name]
        bone.keyframe_insert(data_path="location", frame=61)
        if bone.rotation_mode == "QUATERNION":
            bone.keyframe_insert(data_path="rotation_quaternion", frame=61)
        elif bone.rotation_mode == "AXIS_ANGLE":
            bone.keyframe_insert(data_path="rotation_axis_angle", frame=61)
        else:
            bone.keyframe_insert(data_path="rotation_euler", frame=61)
        bone.keyframe_insert(data_path="scale", frame=61)
    scene.frame_set(1)
    bpy.context.view_layer.update()


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
image, texture_size, slot_reports = create_owned_atlas()
part_image, part_texture_size = create_part_root_texture()
material = make_material(image)
rig = bpy.data.objects[RIG]
enforce_hair_bone_settle(scene, rig)
card_objects = []
for region, (source_name, card_count, half_width) in REGIONS.items():
    card_objects.append(build_region_cards(region, source_name, card_count, half_width, material, rig))
scalp_cap = build_runtime_scalp_cap(rig)
hairline_density = build_hairline_density_ribbon(rig)
part_root_density = build_part_root_density(rig, part_image)
clearance = repair_clearance([obj for obj in card_objects if "crown" in obj.name], target=0.0025)
clearance.update(repair_clearance(
    [obj for obj in card_objects if "crown" not in obj.name] + [hairline_density, part_root_density],
    target=0.0010,
))
collision_envelope_passes = repair_dynamic_card_envelope(scene, rig, card_objects)
for source_name, _count, _width in REGIONS.values():
    source = bpy.data.objects[source_name]
    source.hide_render = True
    source.hide_viewport = True
bpy.data.objects["AevryndFemaleSemanticScalp_R383"].hide_render = True
bpy.data.objects["AevryndFemaleSemanticScalp_R383"].hide_viewport = True
scene["aevrynd_mainline_revision"] = "v249r467-runtime-soft-rear-fan-cards"
scene["aevrynd_release_state"] = "RUNTIME_DISTRIBUTED_CARD_VISUAL_COLLISION_AND_PERFORMANCE_AUDITS_REQUIRED"
scene["aevrynd_hair_layers"] = "runtime_scalp_density|runtime_scalp_hairline_density|runtime_part_root_density|runtime_cards.front|runtime_cards.crown|runtime_cards.rear|runtime_cards.hairline"
scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
for frame, label, location, target, lens in (
    (1, "01-front-f01", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
    (1, "02-hairline-f01", (0.0, -0.57, 1.76), (0.0, -0.02, 1.64), 92),
    (1, "03-top-f01", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
    (1, "04-three-quarter-f01", (0.45, -0.66, 1.60), (0.0, -0.005, 1.56), 84),
    (1, "05-back-f01", (0.0, 0.90, 1.59), (0.0, 0.0, 1.56), 82),
    (33, "06-front-f33", (0.0, -0.76, 1.58), (0.0, -0.015, 1.56), 84),
    (33, "07-back-f33", (0.0, 0.90, 1.59), (0.0, 0.0, 1.56), 82),
):
    render(camera, frame, label, location, target, lens)
scene.frame_set(1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action="DESELECT")
rig.select_set(True)
for obj in card_objects:
    obj.select_set(True)
scalp_cap.select_set(True)
hairline_density.select_set(True)
part_root_density.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=str(GLB), export_format="GLB", use_selection=True, export_apply=False, export_animations=True)

report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "runtimeGlb": str(GLB),
    "texture": str(TEXTURE),
    "textureSize": texture_size,
    "partRootTexture": str(PART_TEXTURE),
    "partRootTextureSize": part_texture_size,
    "atlasSlots": slot_reports,
    "layers": [scalp_cap.get("aevrynd_layer"), hairline_density.get("aevrynd_layer"), part_root_density.get("aevrynd_layer")] + [obj.get("aevrynd_layer") for obj in card_objects],
    "scalpCap": {"object": scalp_cap.name, "vertices": len(scalp_cap.data.vertices), "faces": len(scalp_cap.data.polygons)},
    "hairlineDensity": {"object": hairline_density.name, "vertices": len(hairline_density.data.vertices), "faces": len(hairline_density.data.polygons)},
    "partRootDensity": {"object": part_root_density.name, "vertices": len(part_root_density.data.vertices), "faces": len(part_root_density.data.polygons)},
    "cards": {obj.name: obj.get("aevrynd_card_count") for obj in card_objects},
    "totals": {
        "cards": sum(obj.get("aevrynd_card_count") for obj in card_objects),
        "vertices": sum(len(obj.data.vertices) for obj in card_objects),
        "faces": sum(len(obj.data.polygons) for obj in card_objects),
    },
    "clearanceRepair": clearance,
    "dynamicCollisionEnvelopePasses": collision_envelope_passes,
    "blendBytes": OUTPUT.stat().st_size,
    "glbBytes": GLB.stat().st_size,
    "ownedAssetOnly": True,
    "websitePromotionApproved": False,
    "renderDirectory": str(RENDER_DIR),
    "status": "VISUAL_COLLISION_MOTION_AND_PERFORMANCE_AUDITS_REQUIRED",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R467_RUNTIME_IRREGULAR_HAIRLINE_ENDS=" + json.dumps(report, sort_keys=True))
