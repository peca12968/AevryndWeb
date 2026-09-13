import json
import math
from pathlib import Path

import bpy
from mathutils import Matrix, Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-tail-collision-envelope-r452-study.blend"
MATERIAL_SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-runtime-anchored-part-root-density-r409.blend"
OUTPUT = ASSETS / "aevrynd-female-authoring-v249-mainline-authored-alpha-lock-cards-r456-study.blend"
REPORT = ASSETS / "female-v249-mainline-authored-alpha-lock-cards-r456.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r456-authored-alpha-lock-cards"
RIG = "AevryndFemaleRig"
POINTS = 24
SLOTS = 4
BASE = {
    "front": "AevryndFemaleFrontSurfaceFlow_R383",
    "crown": "AevryndFemaleCrownSurfaceFlow_R383",
    "rear": "AevryndFemaleRearSurfaceFlow_R383",
}
CHAINS = {
    "hair_dyn.L.front": (-0.082, -0.030),
    "hair_dyn.R.front": (0.082, -0.030),
    "hair_dyn.L.back": (-0.065, 0.060),
    "hair_dyn.C.back": (0.000, 0.078),
    "hair_dyn.R.back": (0.065, 0.060),
}


def smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def targets(region):
    if region == "front":
        return [(side * x, y) for side in (-1, 1) for y, x in ((-0.102, 0.018), (-0.082, 0.030), (-0.060, 0.045), (-0.040, 0.060))]
    if region == "crown":
        return [(side * x, y) for side in (-1, 1) for y in (-0.030, -0.010, 0.010) for x in (0.018, 0.047)]
    return [(x, y) for y in (0.016, 0.042, 0.068) for x in (-0.058, -0.022, 0.022, 0.058)]


def select_paths(obj, region):
    paths = []
    roots = []
    for curve in range(len(obj.data.points) // POINTS):
        path = [obj.matrix_world @ obj.data.points[curve * POINTS + segment].position for segment in range(POINTS)]
        paths.append(path)
        roots.append(path[0])
    selected = []
    used = set()
    for target_x, target_y in targets(region):
        index = min(
            (index for index in range(len(roots)) if index not in used),
            key=lambda item: (roots[item].x - target_x) ** 2 + 1.6 * (roots[item].y - target_y) ** 2,
        )
        used.add(index)
        selected.append((index, paths[index]))
    return selected


def nearest_chain(point, region):
    choices = []
    for name, (x, y) in CHAINS.items():
        penalty = 0.020 if ((region == "front" and ".back" in name) or (region in ("rear", "crown") and ".front" in name)) else 0.0
        choices.append(((point.x - x) ** 2 + (point.y - y) ** 2 + penalty, name))
    return min(choices)[1]


def level_weights(t):
    raw = [max(0.0, 1.0 - abs(t - center) / 0.42) for center in (0.24, 0.57, 0.89)]
    total = sum(raw) or 1.0
    return [value / total for value in raw]


def build_cards(region, source_obj, material, rig, half_width):
    selected = select_paths(source_obj, region)
    vertices = []
    faces = []
    weight_data = []
    slot_ids = []
    source_indices = []
    stride = POINTS * 2
    for guide_index, (source_index, source_path) in enumerate(selected):
        for crossing in (-1.0, 1.0):
            path = [point.copy() for point in source_path]
            card_index = len(slot_ids)
            source_indices.append(source_index)
            slot_ids.append(2 + card_index % 2)
            chain = nearest_chain(path[0], region)
            crossing_angle = math.radians(11.0 * crossing)
            width_jitter = 0.86 + 0.24 * ((guide_index * 37 + (1 if crossing > 0 else 0)) % 97) / 96.0
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
                root_taper = 0.48 + 0.52 * smoothstep(t / 0.16)
                tip_taper = 1.0 - 0.86 * smoothstep((t - 0.68) / 0.32)
                width = half_width * width_jitter * root_taper * tip_taper
                center = point + outward * (0.00065 + 0.00055 * math.sin(math.pi * t) ** 2)
                vertices.extend((center - side * width, center + side * width))
                dynamic = smoothstep((t - 0.06) / 0.72)
                if region == "crown":
                    dynamic *= 0.10
                weight_data.extend(((chain, t, dynamic), (chain, t, dynamic)))
            base = card_index * stride
            for point_index in range(POINTS - 1):
                a = base + point_index * 2
                faces.append((a, a + 1, a + 3, a + 2))

    mesh = bpy.data.meshes.new(f"AevryndFemaleAuthoredAlphaCards_{region}_R456_Data")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(material)
    uv = mesh.uv_layers.new(name="AevryndAuthoredLockUV")
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            vertex_index = mesh.loops[loop_index].vertex_index
            card_index = vertex_index // stride
            local = vertex_index % stride
            point_index = local // 2
            side_index = local % 2
            slot = slot_ids[card_index]
            uv.data[loop_index].uv = ((slot + (0.03 if side_index == 0 else 0.97)) / SLOTS, point_index / (POINTS - 1))
    uv.active_render = True
    obj = bpy.data.objects.new(f"AevryndFemaleAuthoredAlphaCards_{region.title()}_R456", mesh)
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
    modifier = obj.modifiers.new("Aevrynd Authored Alpha Lock Armature", "ARMATURE")
    modifier.object = rig
    obj["aevrynd_layer"] = f"hair.authored_alpha_locks.{region}.dynamic"
    obj["aevrynd_revision"] = "v249r456"
    obj["aevrynd_card_count"] = len(slot_ids)
    obj["aevrynd_points_per_card"] = stride
    obj["aevrynd_source_curve_indices"] = "|".join(map(str, source_indices))
    return obj


def render(scene, camera, frame, label, location, target, lens):
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
rig = bpy.data.objects[RIG]
base_objects = {region: bpy.data.objects[name] for region, name in BASE.items()}
for obj in base_objects.values():
    for radius in obj.data.attributes["radius"].data:
        radius.value *= 0.58

with bpy.data.libraries.load(str(MATERIAL_SOURCE), link=False) as (data_from, data_to):
    data_to.materials = ["Aevrynd_RuntimeHairCards_R409"]
material = data_to.materials[0]
material.name = "Aevrynd_AuthoredAlphaLocks_R456"
material["aevrynd_layer"] = "material.hair.authored_alpha_locks"
material["aevrynd_revision"] = "v249r456"
if material.use_nodes:
    image = next((node for node in material.node_tree.nodes if node.type == "TEX_IMAGE"), None)
    shader = next((node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"), None)
    if image and shader:
        for link in list(material.node_tree.links):
            if link.from_node == image and link.from_socket.name == "Color" and link.to_node == shader:
                material.node_tree.links.remove(link)
        value = material.node_tree.nodes.new("ShaderNodeHueSaturation")
        value.name = "Aevrynd Card Value R456"
        value.inputs["Value"].default_value = 1.42
        material.node_tree.links.new(image.outputs["Color"], value.inputs["Color"])
        material.node_tree.links.new(value.outputs["Color"], shader.inputs["Base Color"])
        shader.inputs["Roughness"].default_value = 0.56

widths = {"front": 0.0060, "crown": 0.0070, "rear": 0.0080}
cards = [build_cards(region, obj, material, rig, widths[region]) for region, obj in base_objects.items()]
scene["aevrynd_mainline_revision"] = "v249r456-authored-alpha-lock-cards-study"
scene["aevrynd_release_state"] = "R456_VISUAL_REVIEW_REQUIRED_BEFORE_COLLISION_AUDIT"
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
    render(scene, camera, frame, label, location, target, lens)
scene.frame_set(1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE),
    "materialSource": str(MATERIAL_SOURCE),
    "output": str(OUTPUT),
    "renderDirectory": str(RENDER_DIR),
    "baseCurveRadiusScale": 0.58,
    "layers": [obj.get("aevrynd_layer") for obj in cards],
    "cards": {obj.name: obj.get("aevrynd_card_count") for obj in cards},
    "totalCards": sum(obj.get("aevrynd_card_count") for obj in cards),
    "widthHalfM": widths,
    "ownedPackedAlphaAtlas": "textures/aevrynd-owned-hair-card-atlas-r409.png",
    "ownedAssetOnly": True,
    "websitePromotionApproved": False,
    "status": "VISUAL_REVIEW_REQUIRED_BEFORE_COLLISION_AUDIT",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R456_AUTHORED_ALPHA_LOCK_CARDS=" + json.dumps(report, sort_keys=True))
