import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.kdtree import KDTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cc0-scalp-foundation-r101.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r101-flow-aware-clumps-r103-sweep"
MAIN = "AevryndFemaleCC0LongHairStudyMain_v249r85"
GUIDE_COUNT = 144


def smooth(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def curve_points(obj, curve):
    return [obj.data.points[curve.first_point_index + index].position.copy() for index in range(curve.points_length)]


def sample_curve(points, unit):
    position = unit * (len(points) - 1)
    index = min(len(points) - 2, int(position))
    blend = position - index
    return points[index].lerp(points[index + 1], blend)


def farthest_guides(records, count):
    roots = [record[0] for record in records]
    selected = [min(range(len(roots)), key=lambda index: roots[index].x)]
    distances = [(root - roots[selected[0]]).length_squared for root in roots]
    for _ in range(1, count):
        next_index = max(range(len(roots)), key=distances.__getitem__)
        selected.append(next_index)
        center = roots[next_index]
        for index, root in enumerate(roots):
            distances[index] = min(distances[index], (root - center).length_squared)
    return selected


def guide_assignments(records, guide_indices):
    tree = KDTree(len(guide_indices))
    for local_index, record_index in enumerate(guide_indices):
        tree.insert(records[record_index][0], local_index)
    tree.balance()
    assignments = []
    for record in records:
        tangent = (sample_curve(record, 0.24) - record[0]).normalized()
        endpoint = record[-1]
        candidates = tree.find_n(record[0], min(24, len(guide_indices)))
        best = None
        best_score = math.inf
        for _, local_index, root_distance in candidates:
            guide = records[guide_indices[local_index]]
            guide_tangent = (sample_curve(guide, 0.24) - guide[0]).normalized()
            direction_penalty = 0.030 * (1.0 - max(-1.0, min(1.0, tangent.dot(guide_tangent))))
            endpoint_penalty = 0.10 * (endpoint - guide[-1]).length
            score = root_distance + direction_penalty + endpoint_penalty
            if score < best_score:
                best_score = score
                best = local_index
        assignments.append(best)
    return assignments


def apply_clumping(obj, records, guides, assignments, strength):
    changed = 0
    maximum = 0.0
    for curve_index, curve in enumerate(obj.data.curves):
        source = records[curve_index]
        guide = records[guides[assignments[curve_index]]]
        for local_index, original in enumerate(source):
            unit = local_index / max(1, len(source) - 1)
            # Roots remain seated.  Mid lengths gather into a readable primary
            # lock while the final quarter opens again to avoid rope tips.
            gather = smooth(unit / 0.20) * (1.0 - 0.58 * smooth((unit - 0.72) / 0.28))
            target = sample_curve(guide, unit)
            candidate = original.lerp(target, strength * gather)
            point = obj.data.points[curve.first_point_index + local_index]
            point.position = candidate
            delta = (candidate - original).length
            if delta > 1.0e-9:
                changed += 1
                maximum = max(maximum, delta)
    obj.data.update_tag()
    return changed, maximum


def render(camera, name, location, target, lens):
    scene = bpy.context.scene
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
OUT.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
main = bpy.data.objects[MAIN]
records = [curve_points(main, curve) for curve in main.data.curves]
guides = farthest_guides(records, GUIDE_COUNT)
assignments = guide_assignments(records, guides)
camera = bpy.data.objects["Aevrynd Review Camera"]
report = {"source": str(SOURCE), "curves": len(records), "guides": len(guides), "variants": []}
for strength in (0.0, 0.08, 0.14, 0.20, 0.26):
    changed, maximum = apply_clumping(main, records, guides, assignments, strength)
    for suffix, location, target, lens in (
        ("front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
        ("three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88),
        ("top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
        ("back", (0.0, 2.10, 1.56), (0.0, 0.02, 1.54), 82),
    ):
        render(camera, f"{strength:.2f}-{suffix}", location, target, lens)
    report["variants"].append({"strength": strength, "changedPoints": changed, "maximumDisplacementM": maximum})

(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R103_FLOW_AWARE_CLUMP_SWEEP=" + json.dumps(report, sort_keys=True))
