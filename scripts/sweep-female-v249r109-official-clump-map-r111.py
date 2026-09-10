import collections
import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "assets-source/reference/blender-official-hair/hair_nodes-female_hair_styles.blend"
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-tear-meniscus-r109.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r109-official-clump-map-r111-sweep"
REFERENCE_MAIN = "long hair main"
MAIN = "AevryndFemaleCC0LongHairStudyMain_v249r85"
VARIANTS = (("a-control", 0.0), ("b-fine-1p0mm", 0.0010), ("c-balanced-2p5mm", 0.0025), ("d-strong-4p0mm", 0.0040))


def smoothstep(edge0, edge1, value):
    value = max(0.0, min(1.0, (value - edge0) / (edge1 - edge0)))
    return value * value * (3.0 - 2.0 * value)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def official_mapping():
    bpy.ops.wm.open_mainfile(filepath=str(REFERENCE))
    obj = bpy.data.objects[REFERENCE_MAIN].evaluated_get(bpy.context.evaluated_depsgraph_get())
    attribute = obj.data.attributes.get("guide_curve_index")
    if attribute is None or attribute.domain != "CURVE":
        raise RuntimeError("official evaluated groom has no curve-domain guide_curve_index")
    mapping = [item.value for item in attribute.data]
    counts = collections.Counter(mapping)
    return mapping, {
        "curveCount": len(mapping), "familyCount": len(counts),
        "familySizeMin": min(counts.values()), "familySizeMax": max(counts.values()),
        "familySizeAverage": sum(counts.values()) / len(counts),
    }


def curve_snapshot(obj):
    return [
        [obj.matrix_world @ obj.data.points[curve.first_point_index + index].position for index in range(curve.points_length)]
        for curve in obj.data.curves
    ]


def sample(points, unit):
    position = unit * (len(points) - 1)
    index = min(len(points) - 2, int(position))
    blend = position - index
    return points[index].lerp(points[index + 1], blend)


def apply_clumps(obj, mapping, cap):
    if len(mapping) != len(obj.data.curves):
        raise RuntimeError(f"official/current curve mismatch: {len(mapping)} vs {len(obj.data.curves)}")
    original = curve_snapshot(obj)
    inverse = obj.matrix_world.inverted()
    moved = 0
    maximum = total = 0.0
    for curve_index, curve in enumerate(obj.data.curves):
        target_index = mapping[curve_index]
        if not (0 <= target_index < len(original)):
            raise RuntimeError(f"invalid official guide index {target_index} for curve {curve_index}")
        guide = original[target_index]
        for local_index in range(curve.points_length):
            unit = local_index / max(1, curve.points_length - 1)
            envelope = smoothstep(0.10, 0.32, unit) * (1.0 - smoothstep(0.72, 0.97, unit))
            if envelope <= 0.0001:
                continue
            point = obj.data.points[curve.first_point_index + local_index]
            world = original[curve_index][local_index]
            delta = sample(guide, unit) - world
            distance = delta.length
            if distance <= 1.0e-9:
                continue
            displacement = delta * min(0.62 * envelope, cap * envelope / distance)
            point.position = inverse @ (world + displacement)
            moved += 1
            maximum = max(maximum, displacement.length)
            total += displacement.length
    bpy.context.view_layer.update()
    return {
        "movedPoints": moved,
        "maximumDisplacementMm": maximum * 1000.0,
        "averageMovedDisplacementMm": total / moved * 1000.0 if moved else 0.0,
    }


def add_family_attribute(obj, mapping):
    attribute = obj.data.attributes.get("aevrynd_clump_family") or obj.data.attributes.new(
        "aevrynd_clump_family", "INT", "CURVE"
    )
    for item, value in zip(attribute.data, mapping):
        item.value = value


def render(camera, name, location, target, lens):
    scene = bpy.context.scene
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    mapping, mapping_stats = official_mapping()
    report = {"reference": str(REFERENCE), "mapping": mapping_stats, "variants": {}}
    for label, cap in VARIANTS:
        bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
        scene = bpy.context.scene
        scene.frame_set(1)
        scene.render.engine = "BLENDER_EEVEE"
        scene.render.resolution_x = scene.render.resolution_y = 1000
        scene.render.resolution_percentage = 100
        scene.render.image_settings.file_format = "PNG"
        main = bpy.data.objects[MAIN]
        add_family_attribute(main, mapping)
        geometry = apply_clumps(main, mapping, cap) if cap else None
        camera = bpy.data.objects["Aevrynd Review Camera"]
        render(camera, f"{label}-01-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88)
        render(camera, f"{label}-02-three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88)
        render(camera, f"{label}-03-top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78)
        render(camera, f"{label}-04-back", (0.0, 2.10, 1.56), (0.0, 0.02, 1.54), 82)
        report["variants"][label] = {"capMm": cap * 1000.0, "geometry": geometry}
    (OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("AEVRYND_V249_R109_OFFICIAL_CLUMP_MAP_R111=" + json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
