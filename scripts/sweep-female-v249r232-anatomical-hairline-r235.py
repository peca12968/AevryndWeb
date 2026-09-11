import array
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-collision-safe-smoothed-hair-r232.blend"
RUNTIME = ROOT / "assets-source/aevrynd-character/runtime-groom-v249r94"
OUT = ROOT.parent / "Temp/female-realism/v249r235-anatomical-hairline-sweep"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-anatomical-hairline-r235.sweep-report.json"
MAIN = "AevryndFemaleCC0LongHairStudyMain_v249r85"
FLY = "AevryndFemaleCC0LongHairStudyFlyaway_v249r85"
SCALP = "AevryndFemaleDeformMatchedScalp_v249r163"
SAMPLES = 20
CLUMP_STRENGTH = 0.22
VARIANTS = (
    ("a-current", "current", False),
    ("b-zero-current-boundary", "existing", False),
    ("c-natural-m-boundary", "natural", False),
    ("d-natural-m-pruned-roots", "natural", True),
)


def clamp01(value):
    return max(0.0, min(1.0, value))


def smoothstep(edge0, edge1, value):
    value = clamp01((value - edge0) / (edge1 - edge0))
    return value * value * (3.0 - 2.0 * value)


def sample_curve(points, t):
    position = t * (len(points) - 1)
    first = min(len(points) - 2, int(position))
    blend = position - first
    return points[first].lerp(points[first + 1], blend)


def build_family_centers(obj, guide_map):
    totals = {}
    counts = {}
    for curve_index, curve in enumerate(obj.data.curves):
        family = guide_map[curve_index]
        points = [obj.data.points[curve.first_point_index + index].position.copy() for index in range(curve.points_length)]
        if family not in totals:
            totals[family] = [Vector((0.0, 0.0, 0.0)) for _ in range(SAMPLES)]
            counts[family] = 0
        for sample_index in range(SAMPLES):
            totals[family][sample_index] += sample_curve(points, sample_index / (SAMPLES - 1))
        counts[family] += 1
    return {family: [value / counts[family] for value in values] for family, values in totals.items()}


def apply_clumping(obj, guide_map, centers):
    for curve_index, curve in enumerate(obj.data.curves):
        centerline = centers[guide_map[curve_index]]
        for local_index in range(1, curve.points_length):
            point = obj.data.points[curve.first_point_index + local_index]
            t = local_index / max(1, curve.points_length - 1)
            weight = CLUMP_STRENGTH * smoothstep(0.06, 0.38, t) * (1.0 - 0.72 * smoothstep(0.72, 1.0, t))
            point.position += (sample_curve(centerline, t) - point.position) * weight
    obj.data.update_tag()


def hairline_height(x, mode):
    lateral = clamp01(abs(x) / 0.090)
    center = math.exp(-0.5 * (x / 0.026) ** 2)
    if mode == "existing":
        return 1.666 - 0.008 * lateral + 0.010 * center
    # A shallow M-shaped female hairline: central peak is 4 mm lower than the
    # temple shoulders, without a ruler-straight forehead edge.
    irregularity = 0.0014 * math.sin(x * 113.0) + 0.0008 * math.sin(x * 251.0)
    return 1.666 + 0.012 * lateral - 0.004 * center + irregularity


def apply_scalp_mask(obj, mode):
    if mode == "current":
        return {"verticesChanged": 0, "zeroVertices": 0}
    density = obj.data.attributes["aevrynd_root_density"]
    changed = 0
    zeros = 0
    for vertex, item in zip(obj.data.vertices, density.data):
        x, y, z = vertex.co
        frontness = smoothstep(-0.040, -0.105, y)
        if frontness <= 0.0:
            continue
        threshold = hairline_height(x, mode)
        boundary = smoothstep(threshold - 0.002, threshold + 0.012, z)
        multiplier = (1.0 - frontness) + frontness * boundary
        old = item.value
        item.value = old * multiplier
        if item.value < 1e-6:
            item.value = 0.0
            zeros += 1
        if abs(item.value - old) > 1e-7:
            changed += 1
    obj.data.update()
    return {"verticesChanged": changed, "zeroVertices": zeros}


def prune_low_roots(obj):
    radius = obj.data.attributes["radius"]
    matrix = obj.matrix_world
    excluded = 0
    for curve in obj.data.curves:
        root = matrix @ obj.data.points[curve.first_point_index].position
        threshold = hairline_height(root.x, "natural")
        if root.y < -0.055 and abs(root.x) < 0.105 and root.z < threshold - 0.001:
            excluded += 1
            for index in range(curve.first_point_index, curve.first_point_index + curve.points_length):
                radius.data[index].value = 0.0
    obj.data.update_tag()
    return excluded


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, filename, location, target, lens):
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    bpy.context.scene.render.filepath = str(OUT / filename)
    bpy.ops.render.render(write_still=True)


mapping = array.array("H")
mapping.frombytes((RUNTIME / "follow-guide.u16").read_bytes())
OUT.mkdir(parents=True, exist_ok=True)
report = {"source": str(SOURCE), "clumpStrength": CLUMP_STRENGTH, "variants": {}}

for label, mode, prune in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    hair = bpy.data.objects[MAIN]
    fly = bpy.data.objects.get(FLY)
    if fly:
        fly.hide_render = True
        fly.hide_viewport = True
    guide_map = mapping[:len(hair.data.curves)]
    apply_clumping(hair, guide_map, build_family_centers(hair, guide_map))
    scalp_metrics = apply_scalp_mask(bpy.data.objects[SCALP], mode)
    excluded = prune_low_roots(hair) if prune else 0
    camera = bpy.data.objects["Aevrynd Review Camera"]
    for view_name, location, target, lens in (
        ("01-face-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
        ("02-face-three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88),
        ("03-hair-top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
    ):
        render(camera, f"{label}-{view_name}.png", location, target, lens)
    report["variants"][label] = {
        "mode": mode,
        "flyawayHidden": True,
        "lowRootCurvesHidden": excluded,
        **scalp_metrics,
    }

report["status"] = "STRICT_VISUAL_SELECTION_PENDING"
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R235_ANATOMICAL_HAIRLINE=" + json.dumps(report, sort_keys=True))
