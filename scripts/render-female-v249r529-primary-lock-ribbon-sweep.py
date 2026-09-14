import json
import math
from collections import defaultdict
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-orbital-brow-refit-r526.blend"
OUT = ASSETS / "reviews/v249r529-primary-lock-ribbon-sweep"
REPORT = ASSETS / "female-v249-mainline-primary-lock-ribbons-r529.study.json"
FRONT = "AevryndFemaleRuntimeLayeredLocks_front_R517"
POINTS = 24
STRIDE = POINTS * 2
VARIANTS = (
    ("a-r526-current", None),
    ("b-28-guides", {"azimuth": 20.0, "zBands": 2, "ribbons": 3, "fillAlpha": 0.52, "widthMm": 9.0}),
    ("c-42-guides", {"azimuth": 15.0, "zBands": 3, "ribbons": 3, "fillAlpha": 0.38, "widthMm": 8.0}),
    ("d-56-guides", {"azimuth": 12.0, "zBands": 4, "ribbons": 2, "fillAlpha": 0.30, "widthMm": 7.0}),
)


def smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


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


def center(mesh, card, row):
    base = card * STRIDE + row * 2
    return (mesh.vertices[base].co + mesh.vertices[base + 1].co) * 0.5


def make_fill_material(source):
    material = source.copy()
    material.name = "Aevrynd_RuntimeHairCards_R529_FillStudy"
    principled = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    alpha = principled.inputs["Alpha"]
    source_socket = alpha.links[0].from_socket
    material.node_tree.links.remove(alpha.links[0])
    multiply = material.node_tree.nodes.new("ShaderNodeMath")
    multiply.name = "Aevrynd R529 Fill Alpha"
    multiply.operation = "MULTIPLY"
    material.node_tree.links.new(source_socket, multiply.inputs[0])
    material.node_tree.links.new(multiply.outputs[0], alpha)
    return material, multiply.inputs[1]


def build_locks(source, configuration, index):
    cards = int(source.get("aevrynd_card_count", len(source.data.vertices) // STRIDE))
    roots = [center(source.data, card, 0) for card in range(cards)]
    minimum_z, maximum_z = min(root.z for root in roots), max(root.z for root in roots)
    clusters = defaultdict(list)
    for card, root in enumerate(roots):
        azimuth = math.degrees(math.atan2(root.x, -(root.y + 0.012)))
        azimuth_bin = math.floor((azimuth + 105.0) / configuration["azimuth"])
        normalized_z = (root.z - minimum_z) / max(1e-6, maximum_z - minimum_z)
        z_band = min(configuration["zBands"] - 1, int(normalized_z * configuration["zBands"]))
        clusters[(azimuth_bin, z_band)].append(card)

    vertices, faces = [], []
    guide_count = 0
    for (azimuth_bin, z_band), members in sorted(clusters.items()):
        if len(members) < 2:
            continue
        guide_count += 1
        guide = []
        for row in range(POINTS):
            guide.append(sum((center(source.data, card, row) for card in members), Vector()) / len(members))
        phase = azimuth_bin * 1.71 + z_band * 0.83
        length_scale = 0.84 + 0.13 * (0.5 + 0.5 * math.sin(phase))
        for ribbon in range(configuration["ribbons"]):
            layer = ribbon - (configuration["ribbons"] - 1) * 0.5
            output_base = len(vertices)
            for row in range(POINTS):
                t = row / (POINTS - 1)
                position = (POINTS - 1) * t * length_scale
                low = int(math.floor(position))
                high = min(POINTS - 1, low + 1)
                point = guide[low].lerp(guide[high], position - low)
                radial = Vector((point.x, point.y + 0.012, 0.0))
                if radial.length < 1e-8:
                    radial = Vector((0.0, -1.0, 0.0))
                radial.normalize()
                lateral = Vector((-radial.y, radial.x, 0.0))
                root_release = smoothstep(t / 0.20)
                body = math.sin(math.pi * t) ** 2
                tail = smoothstep((t - 0.52) / 0.48)
                flow = math.sin(math.pi * t) * math.sin(math.pi * 0.92 * t + phase)
                point += radial * ((0.0015 + ribbon * 0.0017) * body)
                point += lateral * (0.0045 * flow + layer * 0.0030 * root_release + 0.0035 * math.sin(phase) * tail)
                width_profile = 0.22 + 0.78 * smoothstep(t / 0.25)
                width_profile *= 1.0 - 0.72 * smoothstep((t - 0.70) / 0.30)
                ribbon_scale = 1.0 if abs(layer) < 0.25 else 0.68
                half_width = configuration["widthMm"] * 0.0005 * width_profile * ribbon_scale
                vertices.extend((point - lateral * half_width, point + lateral * half_width))
            for row in range(POINTS - 1):
                a = output_base + row * 2
                faces.append((a, a + 1, a + 3, a + 2))
    mesh = bpy.data.meshes.new(f"AevryndFemalePrimaryLockRibbons_R529_{index}_Data")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(source.active_material)
    uv = mesh.uv_layers.new(name="AevryndPrimaryLockUV")
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            vertex_index = mesh.loops[loop_index].vertex_index
            local = vertex_index % STRIDE
            row = local // 2
            side = local % 2
            slot = 2 + ((vertex_index // STRIDE) % 2)
            uv.data[loop_index].uv = ((slot + (0.04 if side == 0 else 0.96)) / 4.0, row / (POINTS - 1))
    uv.active_render = True
    obj = bpy.data.objects.new(f"AevryndFemalePrimaryLockRibbons_R529_{index}", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = source.parent
    obj.matrix_parent_inverse = source.matrix_parent_inverse.copy()
    obj["aevrynd_layer"] = "hair.runtime_primary_lock_ribbons.front.study"
    obj["aevrynd_ownership"] = "derived from Aevrynd-owned r517 card centerlines and atlas"
    return obj, guide_count, len(vertices) // STRIDE


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
scene.view_settings.gamma = 1.0
scene.render.image_settings.file_format = "PNG"
front = bpy.data.objects[FRONT]
original_material = front.active_material
fill_material, fill_factor = make_fill_material(original_material)
front.data.materials[0] = fill_material
OUT.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
variant_report = {}
previous = None
for index, (label, configuration) in enumerate(VARIANTS):
    if previous:
        bpy.data.objects.remove(previous, do_unlink=True)
        previous = None
    fill_factor.default_value = 1.0 if configuration is None else configuration["fillAlpha"]
    if configuration is not None:
        front.data.materials[0] = fill_material
        previous, guides, ribbons = build_locks(front, configuration, index)
    else:
        front.data.materials[0] = original_material
        guides = ribbons = 0
    for view, location, target, lens in (
        ("front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
        ("three-quarter", (0.45, -0.66, 1.60), (0.0, -0.005, 1.56), 84),
        ("profile", (0.72, -0.03, 1.61), (0.0, 0.0, 1.58), 88),
        ("top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
    ):
        render(scene, camera, f"{label}-{view}", location, target, lens)
    variant_report[label] = {"configuration": configuration, "guides": guides, "ribbons": ribbons}

report = {
    "source": str(SOURCE),
    "method": "cluster existing r517 card centerlines into azimuth/height guides; build layered tapered primary ribbons over low-opacity fill",
    "variants": variant_report,
    "ownership": "Aevrynd-derived geometry and existing owned atlas only",
    "status": "VISUAL_SWEEP_ONLY",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R529_PRIMARY_LOCK_SWEEP=" + json.dumps(report, sort_keys=True))
