import json
import math
import struct
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-tear-meniscus-r109.blend"
RUNTIME = ROOT / "assets-source/aevrynd-character/runtime-groom-v249r94"
OUT = ROOT.parent / "Temp/female-realism/v249r109-runtime-family-clumps-r110-sweep"
MAIN = "AevryndFemaleCC0LongHairStudyMain_v249r85"
POINTS_PER_GUIDE = 20
MAIN_GUIDES = 192
VARIANTS = (("a-control", 0.0), ("b-fine-1p5mm", 0.0015), ("c-balanced-3p0mm", 0.0030), ("d-strong-4p5mm", 0.0045))


def smoothstep(edge0, edge1, value):
    value = max(0.0, min(1.0, (value - edge0) / (edge1 - edge0)))
    return value * value * (3.0 - 2.0 * value)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def guides_and_mapping():
    manifest = json.loads((RUNTIME / "manifest.json").read_text(encoding="utf-8"))
    guide_count = manifest["simulation"]["guideCount"]
    curve_count = manifest["render"]["curveCount"]
    guide_values = struct.unpack(f"<{guide_count * POINTS_PER_GUIDE * 3}f", (RUNTIME / "simulation-guides.f32").read_bytes())
    mapping = struct.unpack(f"<{curve_count}H", (RUNTIME / "follow-guide.u16").read_bytes())
    guides = []
    cursor = 0
    for _guide in range(guide_count):
        points = []
        for _point in range(POINTS_PER_GUIDE):
            points.append(Vector(guide_values[cursor:cursor + 3]))
            cursor += 3
        guides.append(points)
    return guides, mapping, manifest


def sample_guide(points, unit):
    position = unit * (len(points) - 1)
    index = min(len(points) - 2, int(position))
    blend = position - index
    return points[index].lerp(points[index + 1], blend)


def apply_clumps(obj, guides, mapping, cap):
    inverse = obj.matrix_world.inverted()
    moved = 0
    maximum = 0.0
    total = 0.0
    family_counts = [0] * MAIN_GUIDES
    for curve_index, curve in enumerate(obj.data.curves):
        guide_index = mapping[curve_index]
        if guide_index >= MAIN_GUIDES:
            raise RuntimeError(f"main curve {curve_index} mapped to flyaway guide {guide_index}")
        family_counts[guide_index] += 1
        count = curve.points_length
        for local_index in range(count):
            unit = local_index / max(1, count - 1)
            envelope = smoothstep(0.08, 0.30, unit) * (1.0 - smoothstep(0.72, 0.98, unit))
            if envelope <= 0.0001:
                continue
            point = obj.data.points[curve.first_point_index + local_index]
            world = obj.matrix_world @ point.position
            target = sample_guide(guides[guide_index], unit)
            delta = target - world
            distance = delta.length
            if distance <= 1.0e-9:
                continue
            displacement = delta * min(0.58 * envelope, cap * envelope / distance)
            point.position = inverse @ (world + displacement)
            moved += 1
            maximum = max(maximum, displacement.length)
            total += displacement.length
    bpy.context.view_layer.update()
    return {
        "curves": len(obj.data.curves),
        "movedPoints": moved,
        "maximumDisplacementMm": maximum * 1000.0,
        "averageMovedDisplacementMm": (total / moved * 1000.0) if moved else 0.0,
        "familySizeMin": min(family_counts),
        "familySizeMax": max(family_counts),
        "familySizeAverage": sum(family_counts) / len(family_counts),
    }


def render(camera, name, location, target, lens):
    scene = bpy.context.scene
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    guides, mapping, manifest = guides_and_mapping()
    report = {"runtime": str(RUNTIME), "mainGuides": MAIN_GUIDES, "variants": {}}
    for label, cap in VARIANTS:
        bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
        scene = bpy.context.scene
        scene.frame_set(1)
        scene.render.engine = "BLENDER_EEVEE"
        scene.render.resolution_x = scene.render.resolution_y = 1000
        scene.render.resolution_percentage = 100
        scene.render.image_settings.file_format = "PNG"
        geometry = apply_clumps(bpy.data.objects[MAIN], guides, mapping, cap) if cap else None
        camera = bpy.data.objects["Aevrynd Review Camera"]
        render(camera, f"{label}-01-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88)
        render(camera, f"{label}-02-three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88)
        render(camera, f"{label}-03-top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78)
        render(camera, f"{label}-04-back", (0.0, 2.10, 1.56), (0.0, 0.02, 1.54), 82)
        report["variants"][label] = {"capMm": cap * 1000.0, "geometry": geometry}
    (OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("AEVRYND_V249_R109_RUNTIME_FAMILY_CLUMPS_R110=" + json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
