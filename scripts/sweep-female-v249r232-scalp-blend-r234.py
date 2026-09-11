import array
import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-collision-safe-smoothed-hair-r232.blend"
RUNTIME = ROOT / "assets-source/aevrynd-character/runtime-groom-v249r94"
OUT = ROOT.parent / "Temp/female-realism/v249r234-scalp-blend-sweep"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-scalp-blend-r234.sweep-report.json"
MAIN = "AevryndFemaleCC0LongHairStudyMain_v249r85"
FLY = "AevryndFemaleCC0LongHairStudyFlyaway_v249r85"
SCALP = "AevryndFemaleDeformMatchedScalp_v249r163"
SAMPLES = 20
CLUMP_STRENGTH = 0.22
VARIANTS = (
    ("a-current-scalp", 0.50, None),
    ("b-soft-alpha", 0.35, None),
    ("c-low-alpha", 0.25, None),
    ("d-warm-low-alpha", 0.25, (0.035, 0.012, 0.007, 1.0)),
)


def smoothstep(edge0, edge1, value):
    value = max(0.0, min(1.0, (value - edge0) / (edge1 - edge0)))
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
    maximum = 0.0
    moved = 0
    for curve_index, curve in enumerate(obj.data.curves):
        centerline = centers[guide_map[curve_index]]
        for local_index in range(1, curve.points_length):
            point = obj.data.points[curve.first_point_index + local_index]
            t = local_index / max(1, curve.points_length - 1)
            weight = CLUMP_STRENGTH * smoothstep(0.06, 0.38, t) * (1.0 - 0.72 * smoothstep(0.72, 1.0, t))
            delta = (sample_curve(centerline, t) - point.position) * weight
            point.position += delta
            if delta.length > 1e-8:
                moved += 1
                maximum = max(maximum, delta.length)
    obj.data.update_tag()
    return moved, maximum


def tune_scalp(obj, opacity, color):
    material = obj.data.materials[0]
    material = material.copy()
    obj.data.materials[0] = material
    math_node = next(node for node in material.node_tree.nodes if node.bl_idname == "ShaderNodeMath")
    free_inputs = [socket for socket in math_node.inputs if not socket.is_linked and hasattr(socket, "default_value")]
    if not free_inputs:
        raise RuntimeError("Scalp alpha multiply input not found")
    free_inputs[0].default_value = opacity
    principled = next(node for node in material.node_tree.nodes if node.bl_idname == "ShaderNodeBsdfPrincipled")
    if color is not None:
        principled.inputs["Base Color"].default_value = color
    return {
        "alphaMultiplier": opacity,
        "baseColor": [float(value) for value in principled.inputs["Base Color"].default_value],
    }


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

for label, opacity, color in VARIANTS:
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
    centers = build_family_centers(hair, guide_map)
    moved, maximum = apply_clumping(hair, guide_map, centers)
    scalp_values = tune_scalp(bpy.data.objects[SCALP], opacity, color)
    camera = bpy.data.objects["Aevrynd Review Camera"]
    for view_name, location, target, lens in (
        ("01-face-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
        ("02-face-three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88),
        ("03-hair-top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
    ):
        render(camera, f"{label}-{view_name}.png", location, target, lens)
    report["variants"][label] = {
        **scalp_values,
        "flyawayHidden": True,
        "pointsMovedByClumping": moved,
        "maximumClumpMoveMm": maximum * 1000.0,
    }

report["status"] = "STRICT_VISUAL_SELECTION_PENDING"
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R234_SCALP_BLEND=" + json.dumps(report, sort_keys=True))
