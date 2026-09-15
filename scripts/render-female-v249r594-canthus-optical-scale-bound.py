import json
from collections import defaultdict
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-lower-face-clearance-r569.blend"
OUT = ASSETS / "reviews/v249r594-canthus-optical-scale-bound"
REPORT = ASSETS / "female-v249-mainline-canthus-optical-scale-r594.study.json"
BODY = "AevryndFemaleBodyBaseV118"
EYES = {"L": 0.03453, "R": -0.03444}
OPTICAL_SUFFIXES = ("Cornea", "Sclera", "Iris", "Pupil", "Catchlight")
VARIANTS = (
    ("a-r569-current", False, 1.00),
    ("b-canthus-fair-optics-scale-0p92", True, 0.92),
    ("c-canthus-fair-optics-scale-0p90", True, 0.90),
    ("d-canthus-fair-optics-scale-0p88", True, 0.88),
)


def smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def world_mesh(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return vertices, faces


def overlap_count(first, second, depsgraph):
    av, af = world_mesh(first, depsgraph)
    bv, bf = world_mesh(second, depsgraph)
    at = BVHTree.FromPolygons(av, af, all_triangles=False)
    bt = BVHTree.FromPolygons(bv, bf, all_triangles=False)
    return len(at.overlap(bt))


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
body = bpy.data.objects[BODY]
depsgraph = bpy.context.evaluated_depsgraph_get()
evaluated = body.evaluated_get(depsgraph)
mesh = evaluated.to_mesh()
world_points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
evaluated.to_mesh_clear()

adjacency = defaultdict(set)
for edge in body.data.edges:
    first, second = edge.vertices
    adjacency[first].add(second)
    adjacency[second].add(first)
selected = {}
for index, point in enumerate(world_points):
    if point.y > -0.074 or not (1.600 < point.z < 1.620):
        continue
    for center_x in EYES.values():
        outward = 1.0 if center_x > 0.0 else -1.0
        dx = abs(point.x - (center_x + outward * 0.0104))
        dz = abs(point.z - 1.6102)
        if dx < 0.0090 and dz < 0.0100:
            weight = (1.0 - smoothstep((dx - 0.0040) / 0.0050)) * (1.0 - smoothstep((dz - 0.0050) / 0.0050))
            if weight > 0.01:
                selected[index] = weight
            break
current = [point.copy() for point in world_points]
for _ in range(3):
    previous = [point.copy() for point in current]
    for index, weight in selected.items():
        neighbors = adjacency[index]
        if not neighbors:
            continue
        average = sum((previous[neighbor] for neighbor in neighbors), Vector()) / len(neighbors)
        proposal = previous[index].lerp(average, 0.42 * weight)
        proposal.y = previous[index].y
        delta = proposal - world_points[index]
        if delta.length > 0.00135:
            proposal = world_points[index] + delta.normalized() * 0.00135
        current[index] = proposal
canthus_deltas = {index: current[index] - world_points[index] for index in selected if (current[index] - world_points[index]).length > 0.000001}
inverse3 = body.matrix_world.inverted().to_3x3()
shape_keys = list(body.data.shape_keys.key_blocks)
original_body = [[point.co.copy() for point in key.data] for key in shape_keys]
optics = [bpy.data.objects[f"Eye_{side}_{suffix}"] for side in EYES for suffix in OPTICAL_SUFFIXES]
original_optics = {obj.name: [vertex.co.copy() for vertex in obj.data.vertices] for obj in optics}
eye_centers = {}
for side in EYES:
    sclera = bpy.data.objects[f"Eye_{side}_Sclera"]
    points = [sclera.matrix_world @ vertex.co for vertex in sclera.data.vertices]
    eye_centers[side] = sum(points, Vector()) / len(points)

scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
scene.view_settings.gamma = 1.0
scene.render.image_settings.file_format = "PNG"
scene.render.resolution_x = 1400
scene.render.resolution_y = 760
scene.render.resolution_percentage = 100
OUT.mkdir(parents=True, exist_ok=True)
for obj in bpy.data.objects:
    name = obj.name.lower()
    layer = str(obj.get("aevrynd_layer", "")).lower()
    if "hair" in name or layer.startswith("hair"):
        obj.hide_render = True
        obj.hide_viewport = True
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
camera.location = (0.0, -0.405, 1.610)
camera.data.lens = 135
look_at(camera, (0.0, -0.105, 1.610))

variant_report = {}
for label, fair, scale in VARIANTS:
    for key_index, key in enumerate(shape_keys):
        for index, source in enumerate(original_body[key_index]):
            movement = canthus_deltas.get(index) if fair else None
            key.data[index].co = source if movement is None else source + inverse3 @ movement
    for obj in optics:
        side = obj.name.split("_")[1]
        center = eye_centers[side]
        inverse_world = obj.matrix_world.inverted()
        for vertex, source in zip(obj.data.vertices, original_optics[obj.name]):
            source_world = obj.matrix_world @ source
            vertex.co = inverse_world @ (center + (source_world - center) * scale)
        obj.data.update()
    body.data.update()
    scene.frame_set(1)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    overlap = {
        f"Eye_{side}_{suffix}": overlap_count(body, bpy.data.objects[f"Eye_{side}_{suffix}"], depsgraph)
        for side in EYES for suffix in ("Cornea", "Sclera")
    }
    scene.render.filepath = str(OUT / f"{label}.png")
    bpy.ops.render.render(write_still=True)
    variant_report[label] = {
        "canthusFairing": fair,
        "opticalUniformScale": scale,
        "frame1BodyOverlapPairs": overlap,
        "frame1CollisionPass": not any(overlap.values()),
    }

report = {
    "source": str(SOURCE),
    "method": "apply the visually selected three-iteration bounded outer-canthus fairing, then uniformly scale the complete cornea/sclera/iris/pupil/catchlight stack around the shared eye center",
    "canthusMovedVertices": len(canthus_deltas),
    "maximumCanthusMoveM": max((value.length for value in canthus_deltas.values()), default=0.0),
    "shapeKeysMovedTogether": [key.name for key in shape_keys],
    "variants": variant_report,
    "status": "VISUAL_AND_FRAME1_COLLISION_SWEEP_PENDING_REVIEW",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R594_CANTHUS_OPTICAL_SCALE_BOUND=" + json.dumps(report, sort_keys=True))
