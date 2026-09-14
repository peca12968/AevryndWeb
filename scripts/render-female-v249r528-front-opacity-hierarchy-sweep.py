import json
import math
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-orbital-brow-refit-r526.blend"
OUT = ASSETS / "reviews/v249r528-front-opacity-hierarchy-sweep"
REPORT = ASSETS / "female-v249-mainline-front-opacity-hierarchy-r528.study.json"
OBJECT = "AevryndFemaleRuntimeLayeredLocks_front_R517"
POINTS = 24
STRIDE = POINTS * 2
VARIANTS = (
    ("a-r526-current", 0.0, (1.0, 1.0, 1.0), (1.0, 1.0, 1.0)),
    ("b-soft-hierarchy", 0.75, (1.20, 1.00, 0.88), (1.0, 0.78, 0.52)),
    ("c-readable-hierarchy", 1.00, (1.32, 1.00, 0.78), (1.0, 0.68, 0.35)),
    ("d-sparse-hierarchy", 1.10, (1.40, 0.98, 0.70), (1.0, 0.58, 0.18)),
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


def interpolate(points, position):
    low = int(math.floor(position))
    high = min(len(points) - 1, low + 1)
    return points[low].lerp(points[high], position - low)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
scene.view_settings.gamma = 1.0
scene.render.image_settings.file_format = "PNG"
obj = bpy.data.objects[OBJECT]
cards = int(obj.get("aevrynd_card_count", len(obj.data.vertices) // STRIDE))
original = [vertex.co.copy() for vertex in obj.data.vertices]

# Use one material and one draw call. The per-card hierarchy is encoded as a
# vertex-color alpha multiplier so it can be carried into Aevrynd's runtime.
material = obj.active_material.copy()
material.name = "Aevrynd_RuntimeHairCards_R528_HierarchyStudy"
obj.data.materials.clear()
obj.data.materials.append(material)
colors = obj.data.color_attributes.get("AevryndHairHierarchy") or obj.data.color_attributes.new(
    name="AevryndHairHierarchy", type="BYTE_COLOR", domain="POINT"
)
principled = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
alpha_input = principled.inputs["Alpha"]
source_socket = alpha_input.links[0].from_socket
material.node_tree.links.remove(alpha_input.links[0])
vertex_color = material.node_tree.nodes.new("ShaderNodeVertexColor")
vertex_color.name = "Aevrynd Hair Hierarchy R528"
vertex_color.layer_name = colors.name
multiply = material.node_tree.nodes.new("ShaderNodeMath")
multiply.name = "Aevrynd Hair Alpha Hierarchy R528"
multiply.operation = "MULTIPLY"
material.node_tree.links.new(source_socket, multiply.inputs[0])
material.node_tree.links.new(vertex_color.outputs["Alpha"], multiply.inputs[1])
material.node_tree.links.new(multiply.outputs[0], alpha_input)
card_data = []
for card in range(cards):
    centers, halves = [], []
    for row in range(POINTS):
        base = card * STRIDE + row * 2
        left, right = original[base], original[base + 1]
        centers.append((left + right) * 0.5)
        halves.append((right - left) * 0.5)
    root = centers[0]
    azimuth = math.degrees(math.atan2(root.x, -(root.y + 0.012)))
    group = math.floor((azimuth + 96.0) / 14.0)
    hierarchy_hash = (card * 37 + group * 11) % 10
    hierarchy = 0 if hierarchy_hash < 2 else (1 if hierarchy_hash < 6 else 2)
    card_data.append((centers, halves, azimuth, group, hierarchy))


def apply(strength, width_levels, opacity_levels):
    for card, (centers, halves, azimuth, group, hierarchy) in enumerate(card_data):
        group_wave = 0.5 + 0.5 * math.sin(group * 1.913 + 0.37)
        secondary = 0.5 + 0.5 * math.sin(group * 3.117 + 1.1)
        length_scale = 1.0 - strength * (0.035 + 0.105 * group_wave)
        width_scale = width_levels[hierarchy]
        opacity = opacity_levels[hierarchy]
        for row in range(POINTS):
            t = row / (POINTS - 1)
            source_position = (POINTS - 1) * t * length_scale
            center = interpolate(centers, source_position)
            half = interpolate(halves, source_position) * width_scale
            radial = Vector((center.x, center.y + 0.012, 0.0))
            if radial.length < 1e-8:
                radial = Vector((0.0, -1.0, 0.0))
            radial.normalize()
            lateral = Vector((-radial.y, radial.x, 0.0))
            body = math.sin(math.pi * t) ** 2
            tail = smoothstep((t - 0.48) / 0.52)
            root_release = smoothstep(t / 0.24)
            depth = strength * (0.0010 + 0.0042 * group_wave + 0.0012 * (hierarchy == 0)) * body
            lateral_curve = strength * (0.0020 + 0.0055 * secondary) * math.sin(math.pi * t) * math.sin(math.pi * 0.92 * t + group * 0.73)
            tail_fan = strength * (group_wave - 0.5) * 0.0070 * tail
            part_weight = smoothstep((24.0 - abs(azimuth)) / 18.0)
            part_direction = -1.0 if group % 3 == 0 else 1.0
            asymmetric_part = strength * part_weight * part_direction * 0.0035 * root_release * (1.0 - 0.35 * t)
            offset = radial * depth + lateral * (lateral_curve + tail_fan + asymmetric_part)
            base = card * STRIDE + row * 2
            obj.data.vertices[base].co = center - half + offset
            obj.data.vertices[base + 1].co = center + half + offset
            colors.data[base].color = (1.0, 1.0, 1.0, opacity)
            colors.data[base + 1].color = (1.0, 1.0, 1.0, opacity)
    obj.data.update()


OUT.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
for label, strength, width_levels, opacity_levels in VARIANTS:
    apply(strength, width_levels, opacity_levels)
    for view, location, target, lens in (
        ("front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
        ("three-quarter", (0.45, -0.66, 1.60), (0.0, -0.005, 1.56), 84),
        ("profile", (0.72, -0.03, 1.61), (0.0, 0.0, 1.58), 88),
        ("top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
    ):
        render(scene, camera, f"{label}-{view}", location, target, lens)

report = {
    "source": str(SOURCE),
    "object": OBJECT,
    "cardsRetained": cards,
    "method": "14-degree coherent macro geometry plus primary/secondary/fill width and vertex-alpha hierarchy in one material/draw call",
    "variants": {
        label: {"strength": strength, "widthLevels": width, "opacityLevels": opacity}
        for label, strength, width, opacity in VARIANTS
    },
    "topologyChanged": False,
    "weightsChanged": False,
    "materialsChanged": True,
    "materialCountDelta": 0,
    "drawCallUpperBoundDelta": 0,
    "status": "VISUAL_SWEEP_ONLY",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R528_FRONT_OPACITY_SWEEP=" + json.dumps(report, sort_keys=True))
