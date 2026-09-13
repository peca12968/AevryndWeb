import hashlib
import json
import math
import random
import struct
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-open-topology-physical-skin-r446.blend"
MOTION_SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-runtime-anchored-part-root-density-r409.blend"
OUTPUT = ASSETS / "aevrynd-female-authoring-v249-mainline-native-scalp-macro-locks-r450-study.blend"
REPORT = ASSETS / "female-v249-mainline-native-scalp-macro-locks-r450.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r450-native-scalp-macro-locks"
RIG = "AevryndFemaleRig"
BODY = "AevryndFemaleBodyBaseV118"
MATERIAL = "Aevrynd_RuntimeHairCards_R409"
POINTS = 20
PART_X = -0.016
FRAMES = tuple(range(1, 62))
CHAINS = {
    "hair_dyn.L.front": (-0.082, -0.030),
    "hair_dyn.R.front": (0.082, -0.030),
    "hair_dyn.L.back": (-0.065, 0.060),
    "hair_dyn.C.back": (0.000, 0.078),
    "hair_dyn.R.back": (0.065, 0.060),
}
LEVELS = (1.675, 1.585, 1.495, 1.385)


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def smoothstep(value):
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def rest_hash(rig, exclude_hair=False):
    bones = sorted(
        (bone for bone in rig.data.bones if not exclude_hair or not bone.name.startswith("hair_dyn.")),
        key=lambda bone: bone.name,
    )
    digest = hashlib.sha256()
    for bone in bones:
        values = tuple(bone.head_local) + tuple(bone.tail_local) + tuple(value for row in bone.matrix_local for value in row)
        digest.update(bone.name.encode("utf-8") + b"\0" + struct.pack("<22d", *values))
    return digest.hexdigest(), len(bones)


def capture_motion():
    bpy.ops.wm.open_mainfile(filepath=str(MOTION_SOURCE))
    scene = bpy.context.scene
    rig = bpy.data.objects[RIG]
    source_hash, source_count = rest_hash(rig, exclude_hair=True)
    motion = {}
    for frame in FRAMES:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        motion[frame] = {
            bone.name: tuple(bone.rotation_euler)
            for bone in rig.pose.bones
            if bone.name.startswith("hair_dyn.")
        }
    return motion, source_hash, source_count


def add_hair_bones(rig):
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    for chain_name, (x, y) in CHAINS.items():
        parent = rig.data.edit_bones["head"]
        for index in range(3):
            bone = rig.data.edit_bones.new(f"{chain_name}.{index + 1:02d}")
            bone.head = (x, y, LEVELS[index])
            bone.tail = (x, y, LEVELS[index + 1])
            bone.parent = parent
            bone.use_connect = False
            parent = bone
    bpy.ops.object.mode_set(mode="POSE")
    for chain_name in CHAINS:
        for index in range(3):
            bone = rig.pose.bones[f"{chain_name}.{index + 1:02d}"]
            bone.rotation_mode = "XYZ"
            bone["aevrynd_secondary_motion"] = True
            bone["stiffness"] = (0.88, 0.73, 0.57)[index]
            bone["damping"] = (0.84, 0.77, 0.70)[index]
            bone["gravity"] = (0.12, 0.31, 0.53)[index]
            bone["collision_radius_m"] = (0.020, 0.017, 0.014)[index]
            bone["max_swing_deg"] = (7.0, 12.0, 18.0)[index]
    bpy.ops.object.mode_set(mode="OBJECT")
    rig.select_set(False)


def install_motion(scene, rig, motion):
    for frame in FRAMES:
        scene.frame_set(frame)
        for name, rotation in motion[frame].items():
            bone = rig.pose.bones[name]
            bone.rotation_euler = rotation
            bone.keyframe_insert(data_path="rotation_euler", frame=frame)
    scene.frame_set(1)
    bpy.context.view_layer.update()


def body_geometry(body):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    normal_matrix = evaluated.matrix_world.to_3x3().inverted().transposed()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    normals = [(normal_matrix @ vertex.normal).normalized() for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    evaluated.to_mesh_clear()
    return vertices, normals, faces


def append_material():
    with bpy.data.libraries.load(str(MOTION_SOURCE), link=False) as (data_from, data_to):
        if MATERIAL not in data_from.materials:
            raise RuntimeError("Owned r409 hair-card material is missing")
        data_to.materials = [MATERIAL]
    material = data_to.materials[0]
    material.name = "Aevrynd_NativeMacroLockCards_R450"
    material["aevrynd_revision"] = "v249r450"
    material["aevrynd_ownership"] = "Aevrynd-owned procedural atlas"
    return material


def scalp_hit(tree, x, y):
    hit = tree.ray_cast(Vector((x, y, 2.02)), Vector((0.0, 0.0, -1.0)), 0.55)
    return None if hit[0] is None else hit[0] + hit[1].normalized() * 0.0016


def hairline_hit(tree, x, z):
    hit = tree.ray_cast(Vector((x, -0.30, z)), Vector((0.0, 1.0, 0.0)), 0.45)
    return None if hit[0] is None else hit[0] + hit[1].normalized() * 0.0014


def bezier(a, b, c, d, t):
    u = 1.0 - t
    return a * (u ** 3) + b * (3.0 * u * u * t) + c * (3.0 * u * t * t) + d * (t ** 3)


def protect_from_body(path, tree, clearance=0.0012):
    protected = []
    for point in path:
        hit = tree.find_nearest(point, 0.055)
        if hit is not None and hit[1] is not None:
            normal = hit[1].normalized()
            signed = (point - hit[0]).dot(normal)
            if signed < clearance:
                point = hit[0] + normal * clearance
        protected.append(point)
    return protected


def nearest_chain(root, region):
    candidates = []
    for name, (x, y) in CHAINS.items():
        penalty = 0.022 if ((region in ("front", "hairline") and ".back" in name) or (region in ("crown", "rear") and ".front" in name)) else 0.0
        candidates.append(((root.x - x) ** 2 + (root.y - y) ** 2 + penalty, name))
    return min(candidates)[1]


def level_weights(t):
    raw = [max(0.0, 1.0 - abs(t - center) / 0.42) for center in (0.24, 0.57, 0.89)]
    total = sum(raw) or 1.0
    return [value / total for value in raw]


def generate_paths(tree):
    paths = {region: [] for region in ("front", "crown", "rear", "hairline")}
    rng = random.Random(450249)
    for region, count in (("front", 128), ("crown", 184), ("rear", 144)):
        attempts = 0
        while len(paths[region]) < count and attempts < count * 12:
            attempts += 1
            if region == "front":
                side = -1 if len(paths[region]) % 2 == 0 else 1
                x = PART_X + side * rng.uniform(0.006, 0.092)
                y = rng.uniform(-0.080, 0.020)
                end = Vector((side * rng.uniform(0.145, 0.178), rng.uniform(-0.045, 0.015), rng.uniform(1.245, 1.390)))
            elif region == "crown":
                x = rng.uniform(-0.108, 0.108)
                if abs(x - PART_X) < 0.005:
                    continue
                side = -1 if x < PART_X else 1
                y = rng.uniform(-0.025, 0.085)
                end = Vector((side * rng.uniform(0.140, 0.174), rng.uniform(0.015, 0.080), rng.uniform(1.220, 1.390)))
            else:
                x = rng.uniform(-0.102, 0.102)
                side = -1 if x < 0.0 else 1
                y = rng.uniform(0.055, 0.105)
                end = Vector((side * rng.uniform(0.085, 0.155), rng.uniform(0.095, 0.135), rng.uniform(1.205, 1.365)))
            root = scalp_hit(tree, x, y)
            if root is None or root.z < 1.625:
                continue
            outward = Vector((side * rng.uniform(0.024, 0.043), rng.uniform(0.008, 0.030), rng.uniform(0.010, 0.032)))
            p1 = root + outward
            p2 = Vector((end.x * rng.uniform(0.82, 0.95), end.y + rng.uniform(-0.010, 0.018), rng.uniform(1.44, 1.56)))
            path = [bezier(root, p1, p2, end, index / (POINTS - 1)) for index in range(POINTS)]
            wave = rng.uniform(0.0012, 0.0040)
            phase = rng.uniform(-math.pi, math.pi)
            for index, point in enumerate(path):
                t = index / (POINTS - 1)
                point.x += side * wave * math.sin(math.pi * t) * math.sin(math.tau * t + phase)
                point.y += wave * 0.55 * math.sin(math.pi * t) * math.cos(math.tau * 0.7 * t + phase)
            paths[region].append(protect_from_body(path, tree))
    for index in range(56):
        u = (index + 0.5) / 56.0
        x = -0.086 + 0.172 * u + 0.0008 * math.sin(index * 2.17)
        normalized = abs(x) / 0.086
        z = 1.674 - 0.050 * normalized ** 1.55 + 0.0012 * math.sin(index * 0.91)
        root = hairline_hit(tree, x, z)
        if root is None:
            continue
        side = -1 if x < PART_X else 1
        length = rng.uniform(0.022, 0.052)
        p1 = root + Vector((side * length * 0.20, 0.003, rng.uniform(0.003, 0.011)))
        p2 = root + Vector((side * length * 0.68, 0.009, rng.uniform(-0.002, 0.009)))
        end = root + Vector((side * length, 0.014, rng.uniform(-0.010, 0.004)))
        path = [bezier(root, p1, p2, end, point / (POINTS - 1)) for point in range(POINTS)]
        paths["hairline"].append(protect_from_body(path, tree, 0.0010))
    return paths


def build_cards(region, paths, material, rig):
    vertices, faces, slots, assignments = [], [], [], []
    stride = POINTS * 2
    rng = random.Random(450900 + sum(ord(char) for char in region))
    for card_index, path in enumerate(paths):
        chain = nearest_chain(path[0], region)
        slot = (card_index * 7 + (0 if region == "hairline" else 1)) % 4
        slots.append(slot)
        half_width = (0.0011 if region == "hairline" else rng.uniform(0.0026, 0.0043))
        roll = rng.uniform(-0.20, 0.20)
        for point_index, point in enumerate(path):
            before = path[max(0, point_index - 1)]
            after = path[min(POINTS - 1, point_index + 1)]
            tangent = (after - before).normalized()
            outward = Vector((point.x, point.y + 0.022, point.z - 1.58))
            if outward.length < 1e-6:
                outward = Vector((0.0, -1.0, 0.0))
            outward.normalize()
            side_vector = tangent.cross(outward)
            if side_vector.length < 1e-6:
                side_vector = tangent.cross(Vector((0.0, 1.0, 0.0)))
            side_vector.normalize()
            normal = tangent.cross(side_vector).normalized()
            t = point_index / (POINTS - 1)
            taper = (0.56 + 0.44 * smoothstep(t / 0.12)) * (1.0 - 0.86 * smoothstep((t - 0.74) / 0.26))
            width = half_width * taper
            center = point + normal * roll * 0.0015 * math.sin(math.pi * t)
            vertices.extend((center - side_vector * width, center + side_vector * width))
            dynamic = smoothstep((t - 0.08) / 0.68)
            assignments.extend(((chain, t, dynamic), (chain, t, dynamic)))
        base = card_index * stride
        for segment in range(POINTS - 1):
            a = base + segment * 2
            faces.append((a, a + 1, a + 3, a + 2))
    mesh = bpy.data.meshes.new(f"AevryndFemaleNativeMacroLocks_{region}_R450_Data")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(material)
    uv = mesh.uv_layers.new(name="AevryndNativeMacroLockUV")
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            vertex_index = mesh.loops[loop_index].vertex_index
            card_index = vertex_index // stride
            local = vertex_index % stride
            point_index = local // 2
            side_index = local % 2
            slot = slots[card_index]
            uv.data[loop_index].uv = ((slot + (0.03 if side_index == 0 else 0.97)) / 4.0, point_index / (POINTS - 1))
    uv.active_render = True
    obj = bpy.data.objects.new(f"AevryndFemaleNativeMacroLocks_{region}_R450", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = rig
    obj.matrix_parent_inverse = rig.matrix_world.inverted()
    groups = {"head": obj.vertex_groups.new(name="head")}
    for chain_name in CHAINS:
        for segment in range(3):
            name = f"{chain_name}.{segment + 1:02d}"
            groups[name] = obj.vertex_groups.new(name=name)
    for vertex_index, (chain, t, dynamic) in enumerate(assignments):
        groups["head"].add([vertex_index], 1.0 - dynamic, "REPLACE")
        for segment, weight in enumerate(level_weights(t)):
            groups[f"{chain}.{segment + 1:02d}"].add([vertex_index], dynamic * weight, "REPLACE")
    modifier = obj.modifiers.new("Aevrynd Native Macro Lock Armature", "ARMATURE")
    modifier.object = rig
    obj["aevrynd_layer"] = f"hair.native_macro_locks.{region}.dynamic.alpha"
    obj["aevrynd_revision"] = "v249r450"
    obj["aevrynd_card_count"] = len(paths)
    return obj


def build_scalp_cap(body, vertices, normals, faces, rig):
    selected = []
    for face in faces:
        center = sum((vertices[index] for index in face), Vector()) / len(face)
        if center.z < 1.615:
            continue
        if center.y < -0.045:
            hairline = 1.674 - 0.050 * (abs(center.x) / 0.086) ** 1.55
            if center.z < hairline:
                continue
        selected.append(face)
    remap, new_vertices, new_faces = {}, [], []
    for face in selected:
        mapped = []
        for old_index in face:
            if old_index not in remap:
                remap[old_index] = len(new_vertices)
                new_vertices.append(vertices[old_index] + normals[old_index] * 0.0010)
            mapped.append(remap[old_index])
        new_faces.append(tuple(mapped))
    mesh = bpy.data.meshes.new("AevryndFemaleNativeScalpCap_R450_Data")
    mesh.from_pydata(new_vertices, [], new_faces)
    material = bpy.data.materials.new("Aevrynd_NativeScalpShadow_R450")
    material.use_nodes = True
    shader = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    shader.inputs["Base Color"].default_value = (0.022, 0.0065, 0.0032, 1.0)
    shader.inputs["Roughness"].default_value = 0.94
    shader.inputs["Specular IOR Level"].default_value = 0.02
    material["aevrynd_ownership"] = "Aevrynd-owned procedural material"
    material["aevrynd_layer"] = "material.hair.native_scalp_shadow"
    mesh.materials.append(material)
    obj = bpy.data.objects.new("AevryndFemaleNativeScalpCap_R450", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = rig
    obj.matrix_parent_inverse = rig.matrix_world.inverted()
    head = obj.vertex_groups.new(name="head")
    head.add(list(range(len(new_vertices))), 1.0, "REPLACE")
    modifier = obj.modifiers.new("Aevrynd Native Scalp Armature", "ARMATURE")
    modifier.object = rig
    obj["aevrynd_layer"] = "hair.native_scalp_shadow.head_bound"
    obj["aevrynd_revision"] = "v249r450"
    return obj


def is_old_large_hair(obj):
    name = obj.name.lower()
    if any(token in name for token in ("brow", "lash", "lid", "tear", "caruncle", "eye")):
        return False
    materials = getattr(obj.data, "materials", ()) if hasattr(obj, "data") else ()
    material_names = " ".join(material.name.lower() for material in materials if material)
    return obj.type in {"MESH", "CURVES", "CURVE"} and any(
        token in name or token in material_names for token in ("hair", "scalp", "groom", "flyaway", "lock", "fiber")
    )


def render(scene, camera, frame, label, location, target, lens):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(RENDER_DIR / f"{label}.png")
    bpy.ops.render.render(write_still=True)


motion, source_hash, source_count = capture_motion()
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
rig = bpy.data.objects[RIG]
target_hash, target_count = rest_hash(rig)
if (target_hash, target_count) != (source_hash, source_count):
    raise RuntimeError("r409 and r446 base skeleton rest states differ")
for obj in bpy.data.objects:
    if is_old_large_hair(obj):
        obj.hide_render = True
        obj.hide_viewport = True
add_hair_bones(rig)
install_motion(scene, rig, motion)
body = bpy.data.objects[BODY]
world_vertices, world_normals, body_faces = body_geometry(body)
tree = BVHTree.FromPolygons(world_vertices, body_faces, all_triangles=False)
material = append_material()
paths = generate_paths(tree)
cards = [build_cards(region, paths[region], material, rig) for region in ("front", "crown", "rear", "hairline")]
scalp = build_scalp_cap(body, world_vertices, world_normals, body_faces, rig)
scene["aevrynd_mainline_revision"] = "v249r450-native-scalp-macro-locks-study"
scene["aevrynd_release_state"] = "R450_COLLISION_AND_STRICT_VISUAL_REVIEW_REQUIRED"
scene["aevrynd_hair_layers"] = "|".join([scalp.get("aevrynd_layer")] + [obj.get("aevrynd_layer") for obj in cards])
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
for frame, label, location, target, lens in (
    (1, "01-front-f01", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
    (1, "02-hairline-f01", (0.0, -0.57, 1.76), (0.0, -0.02, 1.64), 92),
    (1, "03-top-f01", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
    (1, "04-three-quarter-f01", (0.45, -0.66, 1.60), (0.0, -0.005, 1.56), 84),
    (1, "05-profile-f01", (0.68, -0.10, 1.59), (0.0, -0.005, 1.56), 88),
    (1, "06-back-f01", (0.0, 0.90, 1.59), (0.0, 0.0, 1.56), 82),
    (33, "07-front-f33", (0.0, -0.76, 1.58), (0.0, -0.015, 1.56), 84),
    (33, "08-back-f33", (0.0, 0.90, 1.59), (0.0, 0.0, 1.56), 82),
):
    render(scene, camera, frame, label, location, target, lens)
scene.frame_set(1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE),
    "motionSource": str(MOTION_SOURCE),
    "output": str(OUTPUT),
    "renderDirectory": str(RENDER_DIR),
    "baseSkeletonRestHash": target_hash,
    "baseSkeletonRestIdentical": True,
    "cardCounts": {region: len(paths[region]) for region in paths},
    "totalCards": sum(len(region_paths) for region_paths in paths.values()),
    "pointsPerCard": POINTS,
    "partX": PART_X,
    "layers": [scalp.get("aevrynd_layer")] + [obj.get("aevrynd_layer") for obj in cards],
    "geometrySource": "New deterministic macro-lock paths rooted by BVH projection on the r446 evaluated scalp; no r409 hair geometry is reused.",
    "ownedAssetOnly": True,
    "websitePromotionApproved": False,
    "strictHairScore100": 28,
    "strictVisualFinding": "Rejected before collision promotion: the low-polygon scalp cap creates a sawtooth helmet edge, root coverage is sparse, the top exposes the proxy scalp, and outer cards read as radial wires rather than groomed locks.",
    "status": "REJECTED_VISUAL_FAIL_GUIDE_CURVES_REQUIRED",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R450_NATIVE_SCALP_MACRO_LOCKS=" + json.dumps(report, sort_keys=True))
