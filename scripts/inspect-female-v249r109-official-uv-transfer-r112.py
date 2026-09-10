import json
import math
from collections import Counter
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "assets-source/reference/blender-official-hair/hair_nodes-female_hair_styles.blend"
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-tear-meniscus-r109.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/female-v249r109-official-uv-transfer-r112.json"
REFERENCE_MAIN = "long hair main"
REFERENCE_SURFACE = "long hair growth mesh"
MAIN = "AevryndFemaleCC0LongHairStudyMain_v249r85"
BODY = "AevryndFemaleBodyBaseV118"
GRID_SIZE = 128


def attribute_values(attribute):
    if attribute.data_type in {"INT", "INT8", "BOOLEAN"}:
        return [item.value for item in attribute.data]
    if attribute.data_type in {"FLOAT", "FLOAT2", "FLOAT_VECTOR", "FLOAT_COLOR", "BYTE_COLOR"}:
        field = "vector" if hasattr(attribute.data[0], "vector") else ("color" if hasattr(attribute.data[0], "color") else "value")
        values = []
        for item in attribute.data:
            value = getattr(item, field)
            values.append(list(value) if hasattr(value, "__len__") else value)
        return values
    return []


def attribute_summary(data):
    result = []
    for attribute in data.attributes:
        values = attribute_values(attribute)
        entry = {
            "name": attribute.name,
            "domain": attribute.domain,
            "dataType": attribute.data_type,
            "count": len(attribute.data),
        }
        if values and isinstance(values[0], (int, float, bool)):
            entry.update({"minimum": min(values), "maximum": max(values), "unique": len(set(values))})
        elif values and isinstance(values[0], list):
            entry["componentMinimum"] = [min(value[i] for value in values) for i in range(len(values[0]))]
            entry["componentMaximum"] = [max(value[i] for value in values) for i in range(len(values[0]))]
        result.append(entry)
    return result


def curve_uvs(data):
    attribute = data.attributes.get("surface_uv_coordinate")
    if attribute is None or attribute.domain != "CURVE":
        raise RuntimeError("surface_uv_coordinate is missing from the official evaluated groom")
    return [Vector(item.vector[:2]) for item in attribute.data]


def percentile(values, fraction):
    ordered = sorted(values)
    if not ordered:
        return None
    position = fraction * (len(ordered) - 1)
    low = int(math.floor(position))
    high = min(len(ordered) - 1, low + 1)
    return ordered[low] * (high - position) + ordered[high] * (position - low)


def metric_summary(values):
    return {
        "minimum": min(values) if values else None,
        "p50": percentile(values, 0.50),
        "p90": percentile(values, 0.90),
        "p99": percentile(values, 0.99),
        "maximum": max(values) if values else None,
        "average": sum(values) / len(values) if values else None,
    }


def barycentric_2d(point, a, b, c):
    v0 = b - a
    v1 = c - a
    v2 = point - a
    denominator = v0.x * v1.y - v1.x * v0.y
    if abs(denominator) < 1.0e-12:
        return None
    v = (v2.x * v1.y - v1.x * v2.y) / denominator
    w = (v0.x * v2.y - v2.x * v0.y) / denominator
    u = 1.0 - v - w
    if min(u, v, w) < -2.0e-5 or max(u, v, w) > 1.00002:
        return None
    return u, v, w


def cell(value):
    return max(0, min(GRID_SIZE - 1, int(math.floor(value * GRID_SIZE))))


def build_uv_index(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    mesh.calc_loop_triangles()
    uv_layer = mesh.uv_layers.get("UVMap") or mesh.uv_layers.active
    if uv_layer is None:
        raise RuntimeError("Aevrynd body has no UV map")
    uv_layer_name = uv_layer.name
    normal_matrix = evaluated.matrix_world.to_3x3().inverted().transposed()
    triangles = []
    grid = {}
    for triangle in mesh.loop_triangles:
        positions = [evaluated.matrix_world @ mesh.vertices[index].co for index in triangle.vertices]
        center = sum(positions, Vector()) / 3.0
        # Hair roots can only bind to the cranial and temple region.  Filtering
        # here also disambiguates overlapping body UV islands.
        if center.z < 1.43 or abs(center.x) > 0.18 or abs(center.y) > 0.18:
            continue
        uvs = [Vector(uv_layer.data[index].uv) for index in triangle.loops]
        normals = [(normal_matrix @ mesh.vertices[index].normal).normalized() for index in triangle.vertices]
        index = len(triangles)
        triangles.append((uvs, positions, normals))
        min_u, max_u = min(uv.x for uv in uvs), max(uv.x for uv in uvs)
        min_v, max_v = min(uv.y for uv in uvs), max(uv.y for uv in uvs)
        for x in range(cell(min_u), cell(max_u) + 1):
            for y in range(cell(min_v), cell(max_v) + 1):
                grid.setdefault((x, y), []).append(index)
    evaluated.to_mesh_clear()
    return triangles, grid, uv_layer_name


def uv_to_surface(uv, triangles, grid):
    matches = []
    for index in grid.get((cell(uv.x), cell(uv.y)), []):
        triangle_uvs, positions, normals = triangles[index]
        bary = barycentric_2d(uv, *triangle_uvs)
        if bary is None:
            continue
        position = sum((positions[i] * bary[i] for i in range(3)), Vector())
        normal = sum((normals[i] * bary[i] for i in range(3)), Vector()).normalized()
        matches.append((position, normal))
    if not matches:
        return None
    return max(matches, key=lambda item: item[0].z)


bpy.ops.wm.open_mainfile(filepath=str(REFERENCE))
scene = bpy.context.scene
scene.frame_set(1)
raw = bpy.data.objects[REFERENCE_MAIN]
raw_attributes = attribute_summary(raw.data)
raw_curve_count = len(raw.data.curves)
raw_point_count = len(raw.data.points)
raw_uvs = curve_uvs(raw.data)
surface = bpy.data.objects[REFERENCE_SURFACE]
surface_uv_layers = [layer.name for layer in surface.data.uv_layers]

evaluated = raw.evaluated_get(bpy.context.evaluated_depsgraph_get())
evaluated_attributes = attribute_summary(evaluated.data)
evaluated_uvs = curve_uvs(evaluated.data)
evaluated_roots = [
    evaluated.matrix_world @ evaluated.data.points[curve.first_point_index].position
    for curve in evaluated.data.curves
]
guide_attribute = evaluated.data.attributes.get("guide_curve_index")
guide_mapping = [item.value for item in guide_attribute.data]
family_sizes = Counter(guide_mapping)

bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
body = bpy.data.objects[BODY]
main = bpy.data.objects[MAIN]
if len(main.data.curves) != len(evaluated_uvs):
    raise RuntimeError(f"official/current curve mismatch: {len(evaluated_uvs)} vs {len(main.data.curves)}")
triangles, grid, body_uv_name = build_uv_index(body)
mapped = [uv_to_surface(uv, triangles, grid) for uv in evaluated_uvs]
current_roots = [main.matrix_world @ main.data.points[curve.first_point_index].position for curve in main.data.curves]

root_distances_mm = []
root_delta_x_mm = []
root_delta_y_mm = []
root_delta_z_mm = []
mapped_indices = []
for index, (current, target) in enumerate(zip(current_roots, mapped)):
    if target is None:
        continue
    delta = target[0] - current
    mapped_indices.append(index)
    root_distances_mm.append(delta.length * 1000.0)
    root_delta_x_mm.append(delta.x * 1000.0)
    root_delta_y_mm.append(delta.y * 1000.0)
    root_delta_z_mm.append(delta.z * 1000.0)

report = {
    "reference": str(REFERENCE),
    "source": str(SOURCE),
    "referenceRaw": {
        "curveCount": raw_curve_count,
        "pointCount": raw_point_count,
        "attributes": raw_attributes,
        "surface": REFERENCE_SURFACE,
        "surfaceUvLayers": surface_uv_layers,
        "rootUvBounds": {
            "minimum": [min(uv.x for uv in raw_uvs), min(uv.y for uv in raw_uvs)],
            "maximum": [max(uv.x for uv in raw_uvs), max(uv.y for uv in raw_uvs)],
        },
    },
    "referenceEvaluated": {
        "curveCount": len(evaluated_uvs),
        "rootCount": len(evaluated_roots),
        "attributes": evaluated_attributes,
        "familyCount": len(family_sizes),
        "familySize": metric_summary(list(family_sizes.values())),
    },
    "target": {
        "body": BODY,
        "bodyUvLayer": body_uv_name,
        "candidateTriangleCount": len(triangles),
        "mappedRootCount": len(mapped_indices),
        "unmappedRootCount": len(mapped) - len(mapped_indices),
        "mappedFraction": len(mapped_indices) / len(mapped),
        "currentToUvSurfaceDistanceMm": metric_summary(root_distances_mm),
        "currentToUvSurfaceDeltaXMm": metric_summary(root_delta_x_mm),
        "currentToUvSurfaceDeltaYMm": metric_summary(root_delta_y_mm),
        "currentToUvSurfaceDeltaZMm": metric_summary(root_delta_z_mm),
    },
    "conclusionGate": "UV_ROOT_TRANSFER_VALID" if len(mapped_indices) / len(mapped) >= 0.98 else "UV_ROOT_TRANSFER_INCOMPLETE",
}
OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_OFFICIAL_UV_TRANSFER_R112=" + json.dumps(report, sort_keys=True))
