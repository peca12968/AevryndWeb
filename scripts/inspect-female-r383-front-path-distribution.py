from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-continuous-crown-field-r383.blend"
POINTS = 24


def curve_paths(obj):
    matrix = obj.matrix_world
    count = len(obj.data.points) // POINTS
    return [[matrix @ obj.data.points[curve * POINTS + point].position for point in range(POINTS)] for curve in range(count)]


def feature(path):
    values = []
    for index, weight in ((0, 5.0), (5, 2.5), (12, 1.4), (23, 1.0)):
        point = path[index]
        values.extend((point.x * weight, point.y * weight, point.z * weight))
    return values


def farthest_paths(paths, count):
    if len(paths) <= count:
        return paths
    features = [feature(path) for path in paths]
    chosen = [min(range(len(paths)), key=lambda i: features[i][0])]
    distances = [sum((a - b) ** 2 for a, b in zip(item, features[chosen[0]])) for item in features]
    while len(chosen) < count:
        candidate = max(range(len(paths)), key=distances.__getitem__)
        chosen.append(candidate)
        center = features[candidate]
        for index, item in enumerate(features):
            distance = sum((a - b) ** 2 for a, b in zip(item, center))
            if distance < distances[index]:
                distances[index] = distance
    return [paths[index] for index in chosen]


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
paths = farthest_paths(curve_paths(bpy.data.objects["AevryndFemaleFrontSurfaceFlow_R383"]), 260)
for point_index in (0, 5, 12, 23):
    for axis in "xyz":
        values = sorted(getattr(path[point_index], axis) for path in paths)
        picks = [values[round((len(values) - 1) * q)] for q in (0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0)]
        print(f"P{point_index}_{axis}=" + ",".join(f"{v:.6f}" for v in picks))

for y_limit in (-0.12, -0.10, -0.08, -0.06, -0.04):
    count = sum(
        any(abs(point.x) < 0.11 and point.y < y_limit and point.z > 1.61 for point in path[2:18])
        for path in paths
    )
    print(f"CENTRAL_FOREHEAD_y<{y_limit:.2f}={count}")

for point_index in (5, 12, 23):
    crossing = sum(path[0].x * path[point_index].x <= 0.0 for path in paths)
    print(f"SIGN_CROSS_ROOT_TO_P{point_index}={crossing}")
for delta in (0.04, 0.06, 0.08, 0.10):
    count = sum(abs(path[12].x - path[0].x) > delta for path in paths)
    print(f"LATERAL_DELTA_P12_GT_{delta:.2f}={count}")
for index, path in enumerate(paths):
    if path[0].x * path[12].x <= 0.0 or abs(path[12].x - path[0].x) > 0.08:
        print(
            f"CANDIDATE_{index}: "
            f"root=({path[0].x:.4f},{path[0].y:.4f},{path[0].z:.4f}) "
            f"p12=({path[12].x:.4f},{path[12].y:.4f},{path[12].z:.4f})"
        )
