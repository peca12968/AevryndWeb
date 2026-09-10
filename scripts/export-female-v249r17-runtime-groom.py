import json
import os
import struct
from pathlib import Path

import bpy
from mathutils import Vector, geometry
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get(
    "AEVRYND_RUNTIME_GROOM_SOURCE",
    ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-r17.blend",
))
OUT = Path(os.environ.get(
    "AEVRYND_RUNTIME_GROOM_OUT",
    ROOT / "assets-source/aevrynd-character/runtime-groom-v249r17",
))
MAIN_OBJECT = os.environ.get("AEVRYND_RUNTIME_GROOM_MAIN_OBJECT", "AevryndFemaleGuideBob_v249r12")
OUT.mkdir(parents=True, exist_ok=True)
LAYERS = (
    {
        "object": MAIN_OBJECT,
        "id": "hair.guide_follow.main",
        "original_curve_count": 14400,
        "family_size": 25,
        "removed": (13953, 13986, 13987, 13992),
        "simulation_guides": 128,
    },
    {
        "object": "AevryndFemaleNapeFiberFill_v249r17",
        "id": "hair.nape.fiber-underlayer",
        "original_curve_count": 616,
        "family_size": 14,
        "removed": (0, 7, 10, 12, 15, 34, 61, 195),
        "simulation_guides": 16,
    },
)


def write_f32(path, values):
    path.write_bytes(struct.pack(f"<{len(values)}f", *values))


def write_u16(path, values):
    path.write_bytes(struct.pack(f"<{len(values)}H", *values))


def write_i8(path, values):
    path.write_bytes(struct.pack(f"<{len(values)}b", *values))


def curve_points(obj, curve):
    return [
        obj.matrix_world @ obj.data.points[curve.first_point_index + index].position
        for index in range(curve.points_length)
    ]


def curve_frame(points, index):
    previous = points[max(0, index - 1)]
    following = points[min(len(points) - 1, index + 1)]
    tangent = (following - previous).normalized()
    reference = Vector((0, 0, 1)) if abs(tangent.z) < 0.92 else Vector((0, 1, 0))
    normal = tangent.cross(reference).normalized()
    binormal = tangent.cross(normal).normalized()
    return tangent, normal, binormal


def surviving_index(original_index, removed):
    if original_index in removed:
        for delta in range(1, 32):
            for candidate in (original_index - delta, original_index + delta):
                if candidate >= 0 and candidate not in removed:
                    original_index = candidate
                    break
            else:
                continue
            break
    return original_index - sum(index < original_index for index in removed)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
bpy.context.scene.frame_set(1)
depsgraph = bpy.context.evaluated_depsgraph_get()


def evaluated_tree(obj):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    polygons = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, polygons, all_triangles=False)


body_object = bpy.data.objects["AevryndFemaleBodyBaseV118"]
collision_trees = [evaluated_tree(body_object)]
head_group = body_object.vertex_groups.get("head")
if head_group is None:
    raise RuntimeError("v249 body has no head vertex group")


def vertex_group_weight(vertex, group_index):
    return next((membership.weight for membership in vertex.groups if membership.group == group_index), 0.0)


body_world_vertices = [body_object.matrix_world @ vertex.co for vertex in body_object.data.vertices]
body_head_weights = [vertex_group_weight(vertex, head_group.index) for vertex in body_object.data.vertices]


def interpolated_head_weight(polygon_index, location):
    indices = tuple(body_object.data.polygons[polygon_index].vertices)
    for triangle_index in range(1, len(indices) - 1):
        triangle = (indices[0], indices[triangle_index], indices[triangle_index + 1])
        barycentric = geometry.barycentric_transform(
            location,
            *(body_world_vertices[index] for index in triangle),
            Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)),
        )
        if min(barycentric) >= -1e-4 and max(barycentric) <= 1.0001:
            return sum(barycentric[axis] * body_head_weights[index] for axis, index in enumerate(triangle))
    inverse = [1.0 / max(1e-8, (body_world_vertices[index] - location).length_squared) for index in indices]
    total = sum(inverse)
    return sum(value * body_head_weights[index] for value, index in zip(inverse, indices)) / total

simulation_guides = []
simulation_layer_ranges = {}
render_curves = []
render_layers = []
render_guide_mappings = []
points_per_curve = None

for layer in LAYERS:
    obj = bpy.data.objects[layer["object"]]
    if points_per_curve is None:
        points_per_curve = obj.data.curves[0].points_length
    if any(curve.points_length != points_per_curve for curve in obj.data.curves):
        raise RuntimeError(f"{obj.name} has non-uniform curve point counts")

    family_count = layer["original_curve_count"] // layer["family_size"]
    family_guides = []
    for family in range(family_count):
        family_start = family * layer["family_size"]
        original_curve = next(
            index for index in range(family_start, family_start + layer["family_size"])
            if index not in layer["removed"]
        )
        current_curve = surviving_index(original_curve, layer["removed"])
        family_guides.append(curve_points(obj, obj.data.curves[current_curve]))

    selected_families = sorted({
        round(index * (family_count - 1) / (layer["simulation_guides"] - 1))
        for index in range(layer["simulation_guides"])
    })
    start = len(simulation_guides)
    simulation_guides.extend(family_guides[index] for index in selected_families)
    simulation_layer_ranges[layer["id"]] = (start, len(simulation_guides))

    sample_points = (0, 5, 10, 15, points_per_curve - 1)
    family_mapping = []
    for guide in family_guides:
        best_local = min(range(len(selected_families)), key=lambda local: sum(
            (guide[point] - family_guides[selected_families[local]][point]).length_squared
            * (4.0 if point == 0 else 1.0)
            for point in sample_points
        ))
        family_mapping.append(start + best_local)

    current_curve = 0
    for original_curve in range(layer["original_curve_count"]):
        if original_curve in layer["removed"]:
            continue
        curve = obj.data.curves[current_curve]
        render_curves.append(curve_points(obj, curve))
        render_layers.append(layer["id"])
        render_guide_mappings.append(family_mapping[original_curve // layer["family_size"]])
        current_curve += 1

guide_values = [coordinate for guide in simulation_guides for point in guide for coordinate in point]
follow_mapping = []
follow_offsets = []
follow_collision_normals = []
follow_contact_head_weights = []
maximum_reconstruction_error = 0.0

for points, layer_id, simulation_index in zip(render_curves, render_layers, render_guide_mappings):
    simulation = simulation_guides[simulation_index]
    follow_mapping.append(simulation_index)
    for point_index, point in enumerate(points):
        tangent, normal, binormal = curve_frame(simulation, point_index)
        delta = point - simulation[point_index]
        u, v, w = delta.dot(normal), delta.dot(binormal), delta.dot(tangent)
        follow_offsets.extend((u, v, w))
        reconstructed = simulation[point_index] + normal * u + binormal * v + tangent * w
        maximum_reconstruction_error = max(maximum_reconstruction_error, (reconstructed - point).length)
        nearest = collision_trees[0].find_nearest(point)
        if nearest is None or nearest[1] is None or nearest[3] > 0.065:
            follow_collision_normals.extend((0, 0, 0))
            follow_contact_head_weights.append(0)
        else:
            surface_normal = nearest[1].normalized()
            signed = (point - nearest[0]).dot(surface_normal)
            if signed < -0.0005:
                follow_collision_normals.extend((0, 0, 0))
                follow_contact_head_weights.append(0)
            else:
                follow_collision_normals.extend(tuple(max(-127, min(127, round(axis * 127))) for axis in surface_normal))
                weight = interpolated_head_weight(nearest[2], nearest[0])
                follow_contact_head_weights.append(round(max(0.0, min(1.0, weight)) * 255))

write_f32(OUT / "simulation-guides.f32", guide_values)
write_u16(OUT / "follow-guide.u16", follow_mapping)
write_f32(OUT / "follow-offsets.f32", follow_offsets)
write_i8(OUT / "follow-collision-normal.i8", follow_collision_normals)
(OUT / "follow-contact-head-weight.u8").write_bytes(bytes(follow_contact_head_weights))

manifest = {
    "format": "aevrynd-runtime-groom-v1",
    "source": str(SOURCE),
    "license": "Aevrynd project-authored geometry",
    "coordinateSystem": "Blender world metres, Z up",
    "simulation": {
        "fixedStepHz": 120,
        "guideCount": len(simulation_guides),
        "pointsPerGuide": points_per_curve,
        "constraintIterations": 24,
        "gravity": [0, 0, -2.0],
    },
    "render": {
        "curveCount": len(render_curves),
        "pointsPerCurve": points_per_curve,
        "offsetComponents": ["normal", "binormal", "tangent"],
    },
    "files": {
        "guides": "simulation-guides.f32",
        "followGuide": "follow-guide.u16",
        "followOffsets": "follow-offsets.f32",
        "followCollisionNormals": "follow-collision-normal.i8",
        "followContactHeadWeights": "follow-contact-head-weight.u8",
    },
    "layers": [
        {"id": "hair.scalp.root_shadow", "simulated": False},
        {"id": "hair.scalp.visible_part", "simulated": False},
        {"id": "hair.guide_follow.main", "simulated": True, "curveCount": 14396, "simulationGuides": 128},
        {"id": "hair.nape.fiber-underlayer", "simulated": True, "curveCount": 608, "simulationGuides": 16},
    ],
    "collision": [
        {"id": "head", "shape": "sphere", "center": [0, -0.010, 1.620], "radius": 0.150},
        {"id": "neck", "shape": "capsule", "a": [0, 0.025, 1.43], "b": [0, 0.025, 1.56], "radius": 0.052},
        {"id": "shoulders", "shape": "capsule", "a": [-0.205, 0.025, 1.405], "b": [0.205, 0.025, 1.405], "radius": 0.065},
        {"id": "upperChest", "shape": "capsule", "a": [-0.12, 0.02, 1.35], "b": [0.12, 0.02, 1.35], "radius": 0.085},
    ],
    "maximumRestReconstructionErrorM": maximum_reconstruction_error,
    "followSurfaceConstraint": "65mm head-turn sweep lock using nearest v249 head-bone skin weight",
    "contactPose": {"pivot": [0, 0, 1.47]},
    "releaseState": "AUTHORING_CANDIDATE_NOT_WEBSITE_ASSET",
}
(OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print("AEVRYND_RUNTIME_GROOM_V249R17=" + json.dumps(manifest, sort_keys=True))
