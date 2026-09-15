import json
import math
from collections import defaultdict, deque
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-orbital-brow-refit-r526.blend"
OUT = ASSETS / "reviews/v249r561-eyelid-aperture-fairing-sweep"
REPORT = ASSETS / "female-v249-mainline-eyelid-aperture-fairing-r561.study.json"
BODY = "AevryndFemaleBodyBaseV118"
EYES = {"L": (0.03453, 1.60805), "R": (-0.03444, 1.60805)}
VARIANTS = (("a-r526-control", 0.0), ("b-fair-0p25", 0.25), ("c-fair-0p50", 0.50), ("d-fair-0p75", 0.75))


def gaussian(value, sigma):
    return math.exp(-0.5 * (value / sigma) ** 2)


def boundary_components(mesh):
    counts = defaultdict(int)
    adjacency = defaultdict(set)
    for polygon in mesh.polygons:
        vertices = list(polygon.vertices)
        for i, first in enumerate(vertices):
            second = vertices[(i + 1) % len(vertices)]
            counts[tuple(sorted((first, second)))] += 1
    for (first, second), count in counts.items():
        if count == 1:
            adjacency[first].add(second)
            adjacency[second].add(first)
    result, unseen = [], set(adjacency)
    while unseen:
        start = unseen.pop()
        component, queue = {start}, deque([start])
        while queue:
            current = queue.popleft()
            for neighbor in adjacency[current]:
                if neighbor not in component:
                    component.add(neighbor)
                    unseen.discard(neighbor)
                    queue.append(neighbor)
        result.append(component)
    return result


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, camera, label, location, target, lens=112):
    scene.frame_set(1)
    bpy.context.view_layer.update()
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x = scene.render.resolution_y = 1100
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
OUT.mkdir(parents=True, exist_ok=True)
for obj in bpy.data.objects:
    name = obj.name.lower()
    layer = str(obj.get("aevrynd_layer", "")).lower()
    if "hair" in name or layer.startswith("hair"):
        obj.hide_render = True
        obj.hide_viewport = True

body = bpy.data.objects[BODY]
depsgraph = bpy.context.evaluated_depsgraph_get()
evaluated = body.evaluated_get(depsgraph)
mesh = evaluated.to_mesh()
world_points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
evaluated.to_mesh_clear()
components = boundary_components(body.data)
boundaries = {}
for side, (center_x, center_z) in EYES.items():
    matches = []
    for component in components:
        center = sum((world_points[index] for index in component), Vector()) / len(component)
        if abs(center.x - center_x) < 0.018 and center.y < -0.075 and abs(center.z - center_z) < 0.020:
            matches.append(component)
    if len(matches) != 1:
        raise RuntimeError(f"Expected one eye boundary for {side}, found {len(matches)}")
    boundaries[side] = matches[0]

keys = list(body.data.shape_keys.key_blocks)
original = [[point.co.copy() for point in key.data] for key in keys]
inverse3 = body.matrix_world.inverted().to_3x3()


def target_boundary_delta(point, center_x, center_z):
    half_width = 0.01115
    u = max(-1.0, min(1.0, (point.x - center_x) / half_width))
    envelope = max(0.0, 1.0 - abs(u) ** 1.72) ** 0.66
    centre_line = center_z + 0.00048 * u
    if point.z >= center_z:
        target_z = centre_line + 0.00510 * envelope
    else:
        target_z = centre_line - 0.00395 * envelope
    return Vector((0.0, -0.00010 * envelope, target_z - point.z))


base_deltas = {}
for side, (center_x, center_z) in EYES.items():
    boundary = boundaries[side]
    boundary_data = [(world_points[index], target_boundary_delta(world_points[index], center_x, center_z)) for index in boundary]
    for index, point in enumerate(world_points):
        if abs(point.x - center_x) > 0.018 or abs(point.z - center_z) > 0.015 or point.y > -0.074:
            continue
        nearest_point, nearest_delta = min(boundary_data, key=lambda item: (point - item[0]).length)
        distance = (point - nearest_point).length
        if distance > 0.006:
            continue
        weight = gaussian(distance, 0.0031)
        movement = nearest_delta * weight
        if movement.length > 0.000002:
            base_deltas[index] = movement


def apply(strength):
    for key_index, key in enumerate(keys):
        for index, source in enumerate(original[key_index]):
            movement = base_deltas.get(index)
            key.data[index].co = source if movement is None else source + inverse3 @ (movement * strength)
    body.data.update()


camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
variant_report = {}
for label, strength in VARIANTS:
    apply(strength)
    for view, location, target, lens in (
        ("front", (0.0, -0.48, 1.605), (0.0, -0.055, 1.605), 118),
        ("three-quarter", (0.30, -0.47, 1.610), (0.0, -0.045, 1.603), 112),
    ):
        render(scene, camera, f"{label}-{view}", location, target, lens)
    variant_report[label] = {
        "blendStrength": strength,
        "affectedVertices": len(base_deltas),
        "maximumMoveMm": max((movement.length for movement in base_deltas.values()), default=0.0) * strength * 1000.0,
    }

report = {
    "source": str(SOURCE),
    "boundaryVerticesPerEye": {side: len(indices) for side, indices in boundaries.items()},
    "method": "fair the existing 52-point eye apertures toward a tilted almond curve and diffuse the displacement through a 3.1mm Gaussian neighborhood; move only the continuous body and leave all optical layers unchanged",
    "shapeKeysMovedTogether": [key.name for key in keys],
    "variants": variant_report,
    "topologyChanged": False,
    "status": "VISUAL_EYELID_SWEEP_ONLY",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R561_EYELID_FAIRING=" + json.dumps(report, sort_keys=True))
