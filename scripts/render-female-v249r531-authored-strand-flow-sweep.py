import json
import math
from collections import defaultdict
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-orbital-brow-refit-r526.blend"
OUT = ASSETS / "reviews/v249r531-authored-strand-flow-sweep"
REPORT = ASSETS / "female-v249-mainline-authored-strand-flow-r531.study.json"
FRONT = "AevryndFemaleRuntimeLayeredLocks_front_R517"
POINTS = 24
STRIDE = POINTS * 2
CHILDREN = 16
VARIANTS = (
    ("a-r526-current", None),
    ("b-natural-flow", 0.70),
    ("c-defined-flow", 1.00),
    ("d-strong-flow", 1.30),
)


def smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def rand(index, salt):
    return (math.sin(index * 127.1 + salt * 311.7) * 43758.5453) % 1.0


def center(mesh, card, row):
    base = card * STRIDE + row * 2
    return (mesh.vertices[base].co + mesh.vertices[base + 1].co) * 0.5


def half_width(mesh, card, row):
    base = card * STRIDE + row * 2
    return (mesh.vertices[base + 1].co - mesh.vertices[base].co) * 0.5


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


def make_hair_material():
    material = bpy.data.materials.new("Aevrynd_FrontStrandGroom_R531")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    hair = nodes.new("ShaderNodeBsdfHairPrincipled")
    info = nodes.new("ShaderNodeHairInfo")
    hair.parametrization = "MELANIN"
    hair.inputs["Melanin"].default_value = 0.72
    hair.inputs["Melanin Redness"].default_value = 0.46
    hair.inputs["Tint"].default_value = (0.82, 0.58, 0.42, 1.0)
    hair.inputs["Roughness"].default_value = 0.39
    hair.inputs["Radial Roughness"].default_value = 0.52
    hair.inputs["Coat"].default_value = 0.055
    hair.inputs["IOR"].default_value = 1.52
    hair.inputs["Random Color"].default_value = 0.11
    hair.inputs["Random Roughness"].default_value = 0.08
    material.node_tree.links.new(info.outputs["Random"], hair.inputs["Random"])
    material.node_tree.links.new(hair.outputs["BSDF"], output.inputs["Surface"])
    material["aevrynd_ownership"] = "procedural in-project from Aevrynd-owned card centerlines"
    material["aevrynd_revision"] = "v249r531-study"
    return material


def build_source_data(source):
    cards = int(source.get("aevrynd_card_count", len(source.data.vertices) // STRIDE))
    roots = [center(source.data, card, 0) for card in range(cards)]
    minimum_z, maximum_z = min(root.z for root in roots), max(root.z for root in roots)
    clusters = defaultdict(list)
    card_records = []
    for card, root in enumerate(roots):
        azimuth = math.degrees(math.atan2(root.x, -(root.y + 0.012)))
        azimuth_bin = math.floor((azimuth + 105.0) / 12.0)
        normalized_z = (root.z - minimum_z) / max(1e-6, maximum_z - minimum_z)
        z_band = min(3, int(normalized_z * 4))
        key = (azimuth_bin, z_band)
        clusters[key].append(card)
        card_records.append({
            "key": key,
            "centers": [center(source.data, card, row) for row in range(POINTS)],
            "halves": [half_width(source.data, card, row) for row in range(POINTS)],
        })
    guides = {}
    for key, members in clusters.items():
        guides[key] = [
            sum((card_records[card]["centers"][row] for card in members), Vector()) / len(members)
            for row in range(POINTS)
        ]
    return cards, clusters, card_records, guides


def make_strands(card_records, guides, strength):
    strands = []
    for card, record in enumerate(card_records):
        guide = guides[record["key"]]
        azimuth_bin, z_band = record["key"]
        group_phase = rand(azimuth_bin * 11 + z_band * 37, 8.0) * math.tau
        group_character = rand(azimuth_bin * 17 + z_band * 43, 9.0)
        root_x = record["centers"][0].x
        part_side = -1.0 if root_x < 0.0 else 1.0
        for child in range(CHILDREN):
            index = card * CHILDREN + child
            across = ((child + 0.5) / CHILDREN) * 2.0 - 1.0
            across += (rand(index, 1.0) - 0.5) * (1.5 / CHILDREN)
            phase = rand(index, 2.0) * math.tau
            # Shared length hierarchy makes neighbouring fibres terminate as a
            # lock. Per-fibre jitter keeps the end from forming a cut edge.
            length_scale = 0.80 + 0.18 * group_character + 0.035 * rand(index, 3.0)
            strand = []
            for row in range(POINTS):
                t = row / (POINTS - 1)
                source_position = t * (POINTS - 1) * length_scale
                low = int(math.floor(source_position))
                high = min(POINTS - 1, low + 1)
                mix = source_position - low
                source_center = record["centers"][low].lerp(record["centers"][high], mix)
                source_half = record["halves"][low].lerp(record["halves"][high], mix)
                macro = guide[low].lerp(guide[high], mix)
                # Hair roots remain distributed. Fibres gather through the body
                # of the lock and reopen near the tip instead of becoming ropes.
                body = math.sin(math.pi * t) ** 1.35
                gather = min(0.44, 0.25 * strength) * body
                reopen = 1.0 - 0.48 * gather
                point = source_center.lerp(macro, gather)
                point += source_half * (across * reopen)
                radial = Vector((point.x, point.y + 0.012, 0.0))
                if radial.length < 1e-8:
                    radial = Vector((0.0, -1.0, 0.0))
                radial.normalize()
                lateral = Vector((-radial.y, radial.x, 0.0))
                root_lock = smoothstep(t / 0.12)
                tip_release = smoothstep((t - 0.58) / 0.42)
                # Coherent hand-authored flow: each macro region has its own
                # bow, depth and tail direction, while all roots stay fixed.
                outward_bow = part_side * (0.0035 + 0.0040 * group_character) * body
                s_curve = math.sin(group_phase + t * math.pi * 1.15) * (0.0025 + 0.0035 * group_character) * body
                depth_bow = (0.0018 + 0.0032 * (1.0 - group_character)) * body
                tail_fan = math.sin(group_phase) * 0.0055 * tip_release
                point += lateral * strength * (outward_bow + s_curve + tail_fan)
                point += radial * strength * depth_bow
                fine = math.sin(phase + t * math.tau * (0.85 + 0.28 * rand(index, 4.0)))
                point += lateral * fine * 0.00055 * root_lock
                point += radial * math.cos(phase + t * math.tau) * 0.00024 * root_lock
                point += lateral * (rand(index, 5.0) - 0.5) * 0.0017 * tip_release
                point.z += (rand(index, 6.0) - 0.5) * 0.0065 * tip_release
                strand.append(point)
            strands.append(strand)
    return strands


def create_curve_object(source, strands, material):
    data = bpy.data.hair_curves.new("AevryndFemaleFrontStrandClumps_R531_Data")
    data.add_curves([POINTS] * len(strands))
    data.points.foreach_set("position", [coordinate for strand in strands for point in strand for coordinate in point])
    radius = data.attributes.new("radius", "FLOAT", "POINT")
    radii = []
    for strand_index, _strand in enumerate(strands):
        base = 0.000045 + 0.000010 * rand(strand_index, 7.0)
        for row in range(POINTS):
            t = row / (POINTS - 1)
            radii.append(base * (1.0 - 0.76 * smoothstep((t - 0.52) / 0.48)))
    radius.data.foreach_set("value", radii)
    data.materials.append(material)
    obj = bpy.data.objects.new("AevryndFemaleFrontStrandClumps_R531", data)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = source.parent
    obj.parent_type = source.parent_type
    obj.parent_bone = source.parent_bone
    obj.matrix_parent_inverse = source.matrix_parent_inverse.copy()
    obj.matrix_world = source.matrix_world.copy()
    obj["aevrynd_layer"] = "hair.source_groom.front.study"
    obj["aevrynd_revision"] = "v249r531-study"
    obj["aevrynd_curve_count"] = len(strands)
    return obj


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
scene.view_settings.gamma = 1.0
scene.render.image_settings.file_format = "PNG"
source = bpy.data.objects[FRONT]
cards, clusters, card_records, guides = build_source_data(source)
material = make_hair_material()
OUT.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
study_object = None
variant_report = {}
for label, strength in VARIANTS:
    if study_object is not None:
        bpy.data.objects.remove(study_object, do_unlink=True)
        study_object = None
    source.hide_render = strength is not None
    source.hide_viewport = strength is not None
    curve_count = 0
    if strength is not None:
        strands = make_strands(card_records, guides, strength)
        study_object = create_curve_object(source, strands, material)
        curve_count = len(strands)
    for view, location, target, lens in (
        ("front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
        ("three-quarter", (0.45, -0.66, 1.60), (0.0, -0.005, 1.56), 84),
        ("profile", (0.72, -0.03, 1.61), (0.0, 0.0, 1.58), 88),
        ("top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
    ):
        render(scene, camera, f"{label}-{view}", location, target, lens)
    variant_report[label] = {"clumpStrength": strength, "curves": curve_count}

report = {
    "source": str(SOURCE),
    "sourceFrontCards": cards,
    "macroClusters": len(clusters),
    "childrenPerCard": CHILDREN,
    "method": "retain distributed card roots; apply coherent nonparallel macro bows, depth and staggered group lengths; softly converge fibres through midshaft and reopen tips",
    "variants": variant_report,
    "ownership": "Aevrynd-derived procedural source groom only",
    "status": "VISUAL_SWEEP_ONLY",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R531_FRONT_STRAND_SWEEP=" + json.dumps(report, sort_keys=True))
