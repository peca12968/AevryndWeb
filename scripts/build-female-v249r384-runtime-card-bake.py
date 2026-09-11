import json
import math
import random
from pathlib import Path

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-continuous-crown-field-r383.blend"
OUTPUT = ASSETS / "aevrynd-female-authoring-v249-mainline-runtime-card-bake-r384.blend"
REPORT = ASSETS / "female-v249-mainline-runtime-card-bake-r384.build-report.json"
TEXTURE = ASSETS / "textures/aevrynd-owned-hair-card-atlas-r384.png"
RUNTIME_DIR = ASSETS / "runtime-groom-r384"
GLB = RUNTIME_DIR / "aevrynd-female-hair-runtime-r384.glb"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r384-runtime-card-bake"
BODY = "AevryndFemaleBody_CC0_R249"
RIG = "AevryndFemaleRig"
POINTS = 24
SLOTS = 4
REGIONS = {
    "front": ("AevryndFemaleFrontSurfaceFlow_R383", 180, 0.0027),
    "crown": ("AevryndFemaleCrownSurfaceFlow_R383", 180, 0.0029),
    "rear": ("AevryndFemaleRearSurfaceFlow_R383", 220, 0.0031),
    "hairline": ("AevryndFemaleHairlineTransition_R383", 48, 0.0012),
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
        rng = random.Random(384100 + slot)
        count = (7, 11, 15, 19)[slot]
        fibers = []
        for index in range(count):
            center = (index + 0.5) / count + rng.uniform(-0.018, 0.018)
            fibers.append((center, rng.uniform(0.010, 0.024), rng.uniform(0.004, 0.024), rng.uniform(-math.pi, math.pi), rng.uniform(0.72, 1.0)))
        alpha_sum = 0.0
        coverage = 0
        for y in range(height):
            v = y / (height - 1)
            root_fade = 0.40 + 0.60 * smoothstep(v / 0.10)
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
                root_veil = (0.20 + 0.06 * slot) * (1.0 - smoothstep((v - 0.02) / 0.24))
                alpha = clamp((alpha + root_veil) * edge * root_fade * tip_fade)
                shade = 0.60 + 0.40 * tone
                x = slot * slot_width + local_x
                offset = (y * width + x) * 4
                pixels[offset:offset + 4] = (0.085 * shade, 0.028 * shade, 0.014 * shade, alpha)
                alpha_sum += alpha
                coverage += int(alpha > 0.08)
        slot_reports.append({"slot": slot, "fibers": count, "meanAlpha": alpha_sum / (height * slot_width), "coverageAbove008": coverage / (height * slot_width)})
    old = bpy.data.images.get("AevryndOwnedHairCardAtlas_R384")
    if old:
        bpy.data.images.remove(old)
    image = bpy.data.images.new("AevryndOwnedHairCardAtlas_R384", width=width, height=height, alpha=True)
    image.pixels.foreach_set(pixels)
    TEXTURE.parent.mkdir(parents=True, exist_ok=True)
    image.filepath_raw = str(TEXTURE)
    image.file_format = "PNG"
    image.save()
    image.pack()
    image["aevrynd_ownership"] = "procedurally generated in-project"
    image["aevrynd_license"] = "Aevrynd-owned"
    image["aevrynd_revision"] = "v249r384"
    return image, [width, height], slot_reports


def make_material(image):
    material = bpy.data.materials.new("Aevrynd_RuntimeHairCards_R384")
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
    shader.inputs["Roughness"].default_value = 0.46
    shader.inputs["Specular IOR Level"].default_value = 0.12
    if shader.inputs.get("Anisotropic IOR Level"):
        shader.inputs["Anisotropic IOR Level"].default_value = 0.56
    links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    links.new(texture.outputs["Alpha"], shader.inputs["Alpha"])
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    material["aevrynd_ownership"] = "procedurally generated in-project"
    material["aevrynd_layer"] = "material.hair.runtime_cards.alpha"
    material["aevrynd_revision"] = "v249r384"
    return material


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


def build_region_cards(region, source_name, card_count, half_width, material, rig):
    source = bpy.data.objects[source_name]
    paths = farthest_paths(curve_paths(source), card_count)
    vertices, faces, weight_data = [], [], []
    slot_ids = []
    stride = POINTS * 2
    for card_index, path in enumerate(paths):
        chain = nearest_chain(path[0], region)
        slot = card_index % SLOTS
        slot_ids.append(slot)
        width_jitter = 0.88 + 0.22 * ((card_index * 37) % 101) / 100.0
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
            t = point_index / (POINTS - 1)
            root_taper = 0.72 + 0.28 * smoothstep(t / 0.12)
            tip_taper = 1.0 - 0.80 * smoothstep((t - 0.72) / 0.28)
            width = half_width * width_jitter * root_taper * tip_taper
            lift = outward * (0.0005 + 0.0008 * (card_index % 3) / 2.0) * math.sin(math.pi * t) ** 2
            center = point + lift
            vertices.extend((center - side * width, center + side * width))
            dynamic = smoothstep((t - 0.06) / 0.72)
            weight_data.extend(((chain, t, dynamic), (chain, t, dynamic)))
        base = card_index * stride
        for point_index in range(POINTS - 1):
            a = base + point_index * 2
            faces.append((a, a + 1, a + 3, a + 2))
    mesh = bpy.data.meshes.new(f"AevryndFemaleRuntimeCards_{region}_R384_Data")
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
    obj = bpy.data.objects.new(f"AevryndFemaleRuntimeCards_{region}_R384", mesh)
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
    obj["aevrynd_revision"] = "v249r384"
    obj["aevrynd_source"] = source_name
    obj["aevrynd_card_count"] = len(paths)
    return obj


def body_tree():
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = bpy.data.objects[BODY].evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(points, faces, all_triangles=False)


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


def render(camera, frame, label, location, target, lens):
    scene = bpy.context.scene
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(RENDER_DIR / f"{label}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
image, texture_size, slot_reports = create_owned_atlas()
material = make_material(image)
rig = bpy.data.objects[RIG]
card_objects = []
for region, (source_name, card_count, half_width) in REGIONS.items():
    card_objects.append(build_region_cards(region, source_name, card_count, half_width, material, rig))
clearance = repair_clearance(card_objects)
for source_name, _count, _width in REGIONS.values():
    source = bpy.data.objects[source_name]
    source.hide_render = True
    source.hide_viewport = True
scene["aevrynd_mainline_revision"] = "v249r384-runtime-card-bake"
scene["aevrynd_release_state"] = "RUNTIME_CARD_VISUAL_COLLISION_AND_PERFORMANCE_AUDITS_REQUIRED"
scene["aevrynd_hair_layers"] = "scalp_density|runtime_cards.front|runtime_cards.crown|runtime_cards.rear|runtime_cards.hairline"
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
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
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=str(GLB), export_format="GLB", use_selection=True, export_apply=False, export_animations=True)

report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "runtimeGlb": str(GLB),
    "texture": str(TEXTURE),
    "textureSize": texture_size,
    "atlasSlots": slot_reports,
    "layers": [obj.get("aevrynd_layer") for obj in card_objects],
    "cards": {obj.name: obj.get("aevrynd_card_count") for obj in card_objects},
    "totals": {
        "cards": sum(obj.get("aevrynd_card_count") for obj in card_objects),
        "vertices": sum(len(obj.data.vertices) for obj in card_objects),
        "faces": sum(len(obj.data.polygons) for obj in card_objects),
    },
    "clearanceRepair": clearance,
    "blendBytes": OUTPUT.stat().st_size,
    "glbBytes": GLB.stat().st_size,
    "ownedAssetOnly": True,
    "websitePromotionApproved": False,
    "renderDirectory": str(RENDER_DIR),
    "status": "VISUAL_COLLISION_MOTION_AND_PERFORMANCE_AUDITS_REQUIRED",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R384_RUNTIME_CARD_BAKE=" + json.dumps(report, sort_keys=True))
