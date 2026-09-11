import json
import math
import os
import struct
from pathlib import Path

import bpy
from mathutils import Vector, geometry
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get(
    "AEVRYND_RUNTIME_GROOM_SOURCE",
    ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cc0-root-density-r90.blend",
))
OUT = Path(os.environ.get(
    "AEVRYND_RUNTIME_GROOM_DIR",
    ROOT / "assets-source/aevrynd-character/runtime-groom-v249r90",
))
MAIN_OBJECTS = tuple(name.strip() for name in os.environ.get(
    "AEVRYND_RUNTIME_GROOM_MAIN_OBJECTS",
    "AevryndFemaleHair_ContinuousFlow_v317_L,AevryndFemaleHair_ContinuousFlow_v317_R,"
    "AevryndFemaleHair_ShapedOverlay_v319_L,AevryndFemaleHair_ShapedOverlay_v319_R",
).split(",") if name.strip())
FLY = os.environ.get("AEVRYND_RUNTIME_GROOM_FLY_OBJECT", "AevryndFemaleCC0LongHairFitFlyaway_v249r86")
ROOT_LAYER = os.environ.get("AEVRYND_RUNTIME_GROOM_ROOT_OBJECT", "AevryndFemaleCC0LongHairRootDensity_v249r90")
POINTS = 20
MAIN_GUIDES = int(os.environ.get("AEVRYND_RUNTIME_GROOM_GUIDES", "256"))
LICENSE = os.environ.get(
    "AEVRYND_RUNTIME_GROOM_LICENSE",
    "Aevrynd-owned procedural layered flow hair; no runtime third-party dependency",
)
OUT.mkdir(parents=True, exist_ok=True)


def write_f32(path, values):
    path.write_bytes(struct.pack(f"<{len(values)}f", *values))


def write_u16(path, values):
    path.write_bytes(struct.pack(f"<{len(values)}H", *values))


def write_i8(path, values):
    path.write_bytes(struct.pack(f"<{len(values)}b", *values))


def curve_world_points(obj, curve):
    return [obj.matrix_world @ obj.data.points[curve.first_point_index + index].position for index in range(curve.points_length)]


def evaluated_world_curves(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    return [
        resample([
            evaluated.matrix_world @ evaluated.data.points[curve.first_point_index + index].position
            for index in range(curve.points_length)
        ])
        for curve in evaluated.data.curves
    ]


def resample(points, count=POINTS):
    if len(points) == count:
        return [point.copy() for point in points]
    lengths = [0.0]
    for index in range(1, len(points)):
        lengths.append(lengths[-1] + (points[index] - points[index - 1]).length)
    total = lengths[-1]
    if total <= 1.0e-9:
        return [points[0].copy() for _ in range(count)]
    output = []
    segment = 0
    for sample in range(count):
        target = total * sample / (count - 1)
        while segment + 1 < len(lengths) - 1 and lengths[segment + 1] < target:
            segment += 1
        span = max(1.0e-9, lengths[segment + 1] - lengths[segment])
        factor = (target - lengths[segment]) / span
        output.append(points[segment].lerp(points[segment + 1], factor))
    return output


def curve_frame(points, index):
    previous = points[max(0, index - 1)]
    following = points[min(len(points) - 1, index + 1)]
    tangent = (following - previous).normalized()
    reference = Vector((0, 0, 1)) if abs(tangent.z) < 0.92 else Vector((0, 1, 0))
    normal = tangent.cross(reference).normalized()
    binormal = tangent.cross(normal).normalized()
    return tangent, normal, binormal


def evaluated_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, faces, all_triangles=False)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
depsgraph = bpy.context.evaluated_depsgraph_get()
main_objects = [bpy.data.objects[name] for name in MAIN_OBJECTS]
main_object_counts = {}
main_curves = []
for obj in main_objects:
    curves = evaluated_world_curves(obj, depsgraph)
    main_object_counts[obj.name] = len(curves)
    main_curves.extend(curves)
fly_obj = bpy.data.objects.get(FLY) if FLY else None
fly_curves = evaluated_world_curves(fly_obj, depsgraph) if fly_obj else []

selected = sorted({round(index * (len(main_curves) - 1) / (MAIN_GUIDES - 1)) for index in range(MAIN_GUIDES)})
simulation_guides = [main_curves[index] for index in selected] + fly_curves
main_guide_count = len(selected)
kdtree = KDTree(main_guide_count)
for guide_index, curve_index in enumerate(selected):
    kdtree.insert(main_curves[curve_index][0], guide_index)
kdtree.balance()


def map_main(curve):
    candidates = kdtree.find_n(curve[0], min(10, main_guide_count))
    return min(
        (entry[1] for entry in candidates),
        key=lambda index: 5.0 * (curve[0] - simulation_guides[index][0]).length_squared
        + 2.0 * (curve[7] - simulation_guides[index][7]).length_squared
        + (curve[-1] - simulation_guides[index][-1]).length_squared,
    )


render_curves = main_curves + fly_curves
follow_mapping = [map_main(curve) for curve in main_curves] + [main_guide_count + index for index in range(len(fly_curves))]

body = bpy.data.objects["AevryndFemaleBodyBaseV118"]
body_tree = evaluated_tree(body, depsgraph)
head_group = body.vertex_groups["head"]
body_vertices = [body.matrix_world @ vertex.co for vertex in body.data.vertices]

# Arc-length resampling replaces each original polyline segment with a new
# chord.  On the tightly fitted hairline a chord can cut through the curved
# forehead even though both source samples are outside the body.  Repair the
# runtime samples against the evaluated body before deriving guide offsets.
RUNTIME_CLEARANCE = float(os.environ.get("AEVRYND_RUNTIME_GROOM_REST_CLEARANCE", "0.0015"))
projection_count = 0
minimum_before_projection = math.inf
minimum_after_projection = math.inf
for curve in render_curves:
    for point_index, point in enumerate(curve):
        nearest = body_tree.find_nearest(point)
        if nearest is None or nearest[1] is None or nearest[3] > 0.065:
            continue
        surface_normal = nearest[1].normalized()
        signed = (point - nearest[0]).dot(surface_normal)
        minimum_before_projection = min(minimum_before_projection, signed)
        if signed < RUNTIME_CLEARANCE:
            curve[point_index] = nearest[0] + surface_normal * RUNTIME_CLEARANCE
            projection_count += 1
            signed = RUNTIME_CLEARANCE
        minimum_after_projection = min(minimum_after_projection, signed)


def group_weight(vertex):
    return next((membership.weight for membership in vertex.groups if membership.group == head_group.index), 0.0)


body_weights = [group_weight(vertex) for vertex in body.data.vertices]


def interpolated_head_weight(polygon_index, location):
    indices = tuple(body.data.polygons[polygon_index].vertices)
    for tri_index in range(1, len(indices) - 1):
        tri = (indices[0], indices[tri_index], indices[tri_index + 1])
        bary = geometry.barycentric_transform(
            location, *(body_vertices[index] for index in tri),
            Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)),
        )
        if min(bary) >= -1.0e-4 and max(bary) <= 1.0001:
            return sum(bary[axis] * body_weights[index] for axis, index in enumerate(tri))
    inverse = [1.0 / max(1.0e-8, (body_vertices[index] - location).length_squared) for index in indices]
    total = sum(inverse)
    return sum(value * body_weights[index] for value, index in zip(inverse, indices)) / total


offsets = []
normals = []
contact_weights = []
maximum_error = 0.0
for curve, guide_index in zip(render_curves, follow_mapping):
    guide = simulation_guides[guide_index]
    for point_index, point in enumerate(curve):
        tangent, normal, binormal = curve_frame(guide, point_index)
        delta = point - guide[point_index]
        u, v, w = delta.dot(normal), delta.dot(binormal), delta.dot(tangent)
        offsets.extend((u, v, w))
        reconstructed = guide[point_index] + normal * u + binormal * v + tangent * w
        maximum_error = max(maximum_error, (reconstructed - point).length)
        nearest = body_tree.find_nearest(point)
        if nearest is None or nearest[1] is None or nearest[3] > 0.065:
            normals.extend((0, 0, 0))
            contact_weights.append(0)
        else:
            surface_normal = nearest[1].normalized()
            signed = (point - nearest[0]).dot(surface_normal)
            if signed < -0.0005:
                raise RuntimeError(f"source collision at curve point: {signed}")
            normals.extend(tuple(max(-127, min(127, round(axis * 127))) for axis in surface_normal))
            weight = interpolated_head_weight(nearest[2], nearest[0])
            contact_weights.append(round(max(0.0, min(1.0, weight)) * 255))

write_f32(OUT / "simulation-guides.f32", [axis for guide in simulation_guides for point in guide for axis in point])
write_u16(OUT / "follow-guide.u16", follow_mapping)
write_f32(OUT / "follow-offsets.f32", offsets)
write_i8(OUT / "follow-collision-normal.i8", normals)
(OUT / "follow-contact-head-weight.u8").write_bytes(bytes(contact_weights))

manifest = {
    "format": "aevrynd-runtime-groom-v1",
    "source": str(SOURCE),
    "license": LICENSE,
    "coordinateSystem": "Blender world metres, Z up",
    "simulation": {
        "fixedStepHz": 120, "guideCount": len(simulation_guides), "pointsPerGuide": POINTS,
        "constraintIterations": 24, "gravity": [0, 0, -2.0],
        "shapeStiffnessRoot": 0.13, "shapeStiffnessTip": 0.014,
    },
    "render": {"curveCount": len(render_curves), "pointsPerCurve": POINTS, "offsetComponents": ["normal", "binormal", "tangent"]},
    "files": {
        "guides": "simulation-guides.f32", "followGuide": "follow-guide.u16",
        "followOffsets": "follow-offsets.f32", "followCollisionNormals": "follow-collision-normal.i8",
        "followContactHeadWeights": "follow-contact-head-weight.u8",
    },
    "layers": [
        {"id": "hair.layered-flow.dynamic", "simulated": True, "curveCount": len(main_curves),
         "simulationGuides": main_guide_count, "sourceObjects": main_object_counts},
        {"id": "hair.flyaway", "simulated": True, "curveCount": len(fly_curves), "simulationGuides": len(fly_curves)},
    ] + ([{"id": "hair.root_density.short-fibers", "simulated": False,
            "curveCount": len(bpy.data.objects[ROOT_LAYER].data.curves)}]
          if ROOT_LAYER and ROOT_LAYER in bpy.data.objects else []),
    "collision": [
        {"id": "head", "shape": "sphere", "center": [0, -0.010, 1.620], "radius": 0.150},
        {"id": "neck", "shape": "capsule", "a": [0, 0.025, 1.43], "b": [0, 0.025, 1.56], "radius": 0.059},
        {"id": "shoulders", "shape": "capsule", "a": [-0.205, 0.025, 1.405], "b": [0.205, 0.025, 1.405], "radius": 0.065},
        {"id": "upperChest", "shape": "capsule", "a": [-0.12, 0.02, 1.35], "b": [0.12, 0.02, 1.35], "radius": 0.085},
    ],
    "maximumRestReconstructionErrorM": maximum_error,
    "resamplingProjection": {
        "clearanceM": RUNTIME_CLEARANCE,
        "correctedPointCount": projection_count,
        "minimumSignedBeforeM": minimum_before_projection,
        "minimumSignedAfterM": minimum_after_projection,
    },
    "followSurfaceConstraint": "65mm head-turn sweep lock using nearest v249 head-bone skin weight",
    "contactPose": {"pivot": [0, 0, 1.47]},
    "releaseState": "AUTHORING_CANDIDATE_NOT_WEBSITE_ASSET_DYNAMIC_AUDIT_PENDING",
}
(OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print("AEVRYND_RUNTIME_GROOM_V249R244=" + json.dumps(manifest, sort_keys=True))
