import json
import math
from collections import defaultdict
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-orbital-brow-refit-r526.blend"
OUT = ASSETS / "reviews/v249r533-root-fill-layer-sweep"
REPORT = ASSETS / "female-v249-mainline-root-fill-layer-r533.study.json"
FRONT = "AevryndFemaleRuntimeLayeredLocks_front_R517"
POINTS = 24
STRIDE = POINTS * 2
CHILDREN = 16
VARIANTS = (
    ("a-r526-current", None),
    ("b-four-row-root-fill", 4),
    ("c-seven-row-root-fill", 7),
    ("d-ten-row-root-fill", 10),
)


def smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def rand(index, salt):
    return (math.sin(index * 127.1 + salt * 311.7) * 43758.5453) % 1.0


def bezier(p0, p1, p2, p3, t):
    inverse = 1.0 - t
    return p0 * inverse ** 3 + p1 * (3.0 * inverse ** 2 * t) + p2 * (3.0 * inverse * t ** 2) + p3 * t ** 3


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
    material = bpy.data.materials.new("Aevrynd_FrontStrandGroom_R533")
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
    material["aevrynd_revision"] = "v249r533-study"
    return material


def build_source_data(source):
    cards = int(source.get("aevrynd_card_count", len(source.data.vertices) // STRIDE))
    roots = [center(source.data, card, 0) for card in range(cards)]
    minimum_z, maximum_z = min(root.z for root in roots), max(root.z for root in roots)
    clusters = defaultdict(list)
    card_records = []
    for card, root in enumerate(roots):
        azimuth = math.degrees(math.atan2(root.x, -(root.y + 0.012)))
        azimuth_bin = math.floor((azimuth + 105.0) / 14.0)
        key = azimuth_bin
        clusters[key].append(card)
        card_records.append({
            "key": key,
            "centers": [center(source.data, card, row) for row in range(POINTS)],
            "halves": [half_width(source.data, card, row) for row in range(POINTS)],
        })
    guides = {}
    for key, members in clusters.items():
        root = sum((card_records[card]["centers"][0] for card in members), Vector()) / len(members)
        side = -1.0 if root.x < 0.0 else 1.0
        side_amount = min(1.0, abs(root.x) / 0.080)
        character = rand(key, 9.0)
        p0 = root
        radial = Vector((root.x, root.y + 0.012, 0.0))
        if radial.length < 1e-8:
            radial = Vector((side * 0.25, -1.0, 0.0))
        radial.normalize()
        # Explicit scalp-to-tip silhouette controls. Adjacent regions differ in
        # lift, bow and length, removing the inherited straight card paths.
        p1 = root + radial * (0.018 + 0.007 * character) + Vector((side * (0.006 + 0.004 * side_amount), 0.015, 0.022 - 0.010 * side_amount))
        end_x = side * (0.073 + 0.024 * side_amount) + (character - 0.5) * 0.010
        end_y = -0.010 + 0.026 * side_amount + (character - 0.5) * 0.008
        end_z = 1.475 + 0.065 * character - 0.020 * side_amount
        p2 = Vector((side * (0.060 + 0.020 * side_amount) + (character - 0.5) * 0.012,
                     -0.004 + 0.020 * side_amount,
                     1.625 + (character - 0.5) * 0.025))
        p3 = Vector((end_x, end_y, end_z))
        guides[key] = [bezier(p0, p1, p2, p3, row / (POINTS - 1)) for row in range(POINTS)]
    return cards, clusters, card_records, guides


def make_strands(card_records, guides, strength):
    strands = []
    for card, record in enumerate(card_records):
        guide = guides[record["key"]]
        azimuth_bin = record["key"]
        group_phase = rand(azimuth_bin * 11, 8.0) * math.tau
        group_character = rand(azimuth_bin * 17, 9.0)
        root_x = record["centers"][0].x
        part_side = -1.0 if root_x < 0.0 else 1.0
        for child in range(CHILDREN):
            index = card * CHILDREN + child
            across = ((child + 0.5) / CHILDREN) * 2.0 - 1.0
            across += (rand(index, 1.0) - 0.5) * (1.5 / CHILDREN)
            phase = rand(index, 2.0) * math.tau
            # Shared length hierarchy makes neighbouring fibres terminate as a
            # lock. Per-fibre jitter keeps the end from forming a cut edge.
            length_scale = 0.94 + 0.060 * rand(index, 3.0)
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
                gather = strength * (math.sin(math.pi * t) ** 0.82)
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
                s_curve = math.sin(group_phase + t * math.pi * 1.05) * 0.0018 * body
                tail_fan = math.sin(group_phase) * 0.0038 * tip_release
                point += lateral * (s_curve + tail_fan)
                point += radial * (0.0012 + 0.0014 * group_character) * body
                fine = math.sin(phase + t * math.tau * (0.85 + 0.28 * rand(index, 4.0)))
                point += lateral * fine * 0.00055 * root_lock
                point += radial * math.cos(phase + t * math.tau) * 0.00024 * root_lock
                point += lateral * (rand(index, 5.0) - 0.5) * 0.0017 * tip_release
                point.z += (rand(index, 6.0) - 0.5) * 0.0065 * tip_release
                strand.append(point)
            strands.append(strand)
    return strands


def create_curve_object(source, strands, material):
    data = bpy.data.hair_curves.new("AevryndFemaleFrontStrandClumps_R533_Data")
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
    obj = bpy.data.objects.new("AevryndFemaleFrontStrandClumps_R533", data)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = source.parent
    obj.parent_type = source.parent_type
    obj.parent_bone = source.parent_bone
    obj.matrix_parent_inverse = source.matrix_parent_inverse.copy()
    obj.matrix_world = source.matrix_world.copy()
    obj["aevrynd_layer"] = "hair.source_groom.front.study"
    obj["aevrynd_revision"] = "v249r533-study"
    obj["aevrynd_curve_count"] = len(strands)
    return obj


def create_root_fill(source, rows):
    vertices, faces, source_polygons = [], [], []
    cards = int(source.get("aevrynd_card_count", len(source.data.vertices) // STRIDE))
    for card in range(cards):
        output_base = len(vertices)
        for row in range(rows + 1):
            input_base = card * STRIDE + row * 2
            vertices.extend((source.data.vertices[input_base].co.copy(), source.data.vertices[input_base + 1].co.copy()))
        for row in range(rows):
            local = output_base + row * 2
            faces.append((local, local + 1, local + 3, local + 2))
            source_polygons.append(card * (POINTS - 1) + row)
    mesh = bpy.data.meshes.new(f"AevryndFemaleFrontRootFill_R533_{rows}_Data")
    mesh.from_pydata(vertices, [], faces)
    for material_slot in source.data.materials:
        mesh.materials.append(material_slot)
    source_uv = source.data.uv_layers.active
    if source_uv is not None:
        target_uv = mesh.uv_layers.new(name=source_uv.name)
        for polygon, source_polygon_index in zip(mesh.polygons, source_polygons):
            original = source.data.polygons[source_polygon_index]
            for target_loop, original_loop in zip(polygon.loop_indices, original.loop_indices):
                target_uv.data[target_loop].uv = source_uv.data[original_loop].uv
        target_uv.active_render = True
    obj = bpy.data.objects.new(f"AevryndFemaleFrontRootFill_R533_{rows}", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = source.parent
    obj.parent_type = source.parent_type
    obj.parent_bone = source.parent_bone
    obj.matrix_parent_inverse = source.matrix_parent_inverse.copy()
    obj.matrix_world = source.matrix_world.copy()
    obj["aevrynd_layer"] = "hair.runtime_root_fill.front.study"
    obj["aevrynd_revision"] = "v249r533-study"
    obj["aevrynd_source_rows"] = rows
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
root_fill = None
variant_report = {}
for label, rows in VARIANTS:
    if study_object is not None:
        bpy.data.objects.remove(study_object, do_unlink=True)
        study_object = None
    if root_fill is not None:
        bpy.data.objects.remove(root_fill, do_unlink=True)
        root_fill = None
    source.hide_render = rows is not None
    source.hide_viewport = rows is not None
    curve_count = 0
    if rows is not None:
        strands = make_strands(card_records, guides, 0.45)
        study_object = create_curve_object(source, strands, material)
        root_fill = create_root_fill(source, rows)
        curve_count = len(strands)
    for view, location, target, lens in (
        ("front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
        ("three-quarter", (0.45, -0.66, 1.60), (0.0, -0.005, 1.56), 84),
        ("profile", (0.72, -0.03, 1.61), (0.0, 0.0, 1.58), 88),
        ("top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
    ):
        render(scene, camera, f"{label}-{view}", location, target, lens)
    variant_report[label] = {"clumpStrength": None if rows is None else 0.45, "rootFillRows": rows, "curves": curve_count}

report = {
    "source": str(SOURCE),
    "sourceFrontCards": cards,
    "macroClusters": len(clusters),
    "childrenPerCard": CHILDREN,
    "method": "pair the r532 soft manual-guide strand groom with only 4/7/10 original root segments to restore part and crown coverage without reinstating the full planar curtain",
    "variants": variant_report,
    "ownership": "Aevrynd-derived procedural source groom only",
    "status": "VISUAL_SWEEP_ONLY",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R533_FRONT_STRAND_SWEEP=" + json.dumps(report, sort_keys=True))
