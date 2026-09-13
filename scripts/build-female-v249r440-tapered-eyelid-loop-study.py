import json
from math import pi, sin
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-layered-optical-stack-r420.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-tapered-eyelid-loops-r440-study.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-tapered-eyelid-loops-r440.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r440-tapered-eyelid-loop-study"
BODY = "AevryndFemaleBody_CC0_R249"
RING_COUNT = 4


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def curve_points(name):
    obj = bpy.data.objects[name]
    spline = obj.data.splines[0]
    if spline.type == "BEZIER":
        return [obj.matrix_world @ point.co for point in spline.bezier_points]
    return [obj.matrix_world @ point.co.xyz for point in spline.points]


def aperture_loop(side):
    upper = curve_points(f"AevryndEye_{side}_UpperLidMargin_R258")
    lower = curve_points(f"AevryndEye_{side}_LowerLidMargin_R258")
    if upper[0].x > upper[-1].x:
        upper.reverse()
        lower.reverse()
    first = (upper[0] + lower[0]) * 0.5
    last = (upper[-1] + lower[-1]) * 0.5
    points = [first] + upper[1:-1] + [last] + list(reversed(lower[1:-1]))
    upper_flags = [True] * (len(upper)) + [False] * (len(lower) - 2)
    upper_t = [index / (len(upper) - 1) for index in range(len(upper))]
    lower_t = [index / (len(lower) - 1) for index in reversed(range(1, len(lower) - 1))]
    return points, upper_flags, upper_t + lower_t


def project_body_surface(body, point):
    local = body.matrix_world.inverted() @ point
    found, location, _normal, _face = body.closest_point_on_mesh(local, distance=0.05)
    if not found:
        return point
    projected = body.matrix_world @ location
    if projected.y > -0.105:
        return point
    return projected


def build_lid_patch(body, side):
    inner, upper_flags, lid_t = aperture_loop(side)
    center_x = sum(point.x for point in inner) / len(inner)
    x_offsets = (0.0, 0.00035, 0.00080, 0.00145)
    upper_offsets = (0.0, 0.00100, 0.00220, 0.00400)
    lower_offsets = (0.0, 0.00075, 0.00155, 0.00280)
    surface_offsets = (-0.00018, -0.00048, -0.00020, -0.00010)
    ring_vertices = []
    for ring_index in range(RING_COUNT):
        ring = []
        for point, is_upper, parameter in zip(inner, upper_flags, lid_t):
            if ring_index == 0:
                target = point.copy()
            else:
                vertical_weight = sin(pi * parameter)
                horizontal_weight = 1.0 - vertical_weight
                horizontal_direction = -1.0 if point.x < center_x else 1.0
                vertical_offset = upper_offsets[ring_index] if is_upper else -lower_offsets[ring_index]
                target = point + Vector((
                    horizontal_direction * x_offsets[ring_index] * horizontal_weight,
                    0.0,
                    vertical_offset * vertical_weight,
                ))
                target = project_body_surface(body, target)
            target.y += surface_offsets[ring_index]
            ring.append(target)
        ring_vertices.append(ring)

    vertices = [point for ring in ring_vertices for point in ring]
    count = len(inner)
    faces = []
    for ring_index in range(RING_COUNT - 1):
        start = ring_index * count
        next_start = (ring_index + 1) * count
        for index in range(count):
            following = (index + 1) % count
            faces.append((start + index, start + following, next_start + following, next_start + index))
    mesh = bpy.data.meshes.new(f"AevryndEye_{side}_TaperedLidLoops_R440Geometry")
    mesh.from_pydata(vertices, [], faces)
    mesh.validate(verbose=True, clean_customdata=True)
    mesh.update(calc_edges=True)
    obj = bpy.data.objects.new(f"AevryndEye_{side}_TaperedLidLoops_R440", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj["aevrynd_layer"] = f"body.face.eye_{side.lower()}.tapered_lid_loops.study"
    obj["aevrynd_revision"] = "v249r440-study"
    obj["aevrynd_ring_count"] = RING_COUNT
    obj["aevrynd_vertices_per_ring"] = count
    return obj


def topology_stats(obj):
    mesh = obj.data
    edge_use = {tuple(sorted(edge.vertices)): 0 for edge in mesh.edges}
    for polygon in mesh.polygons:
        vertices = list(polygon.vertices)
        for index, vertex in enumerate(vertices):
            edge_use[tuple(sorted((vertex, vertices[(index + 1) % len(vertices)])))] += 1
    return {
        "vertices": len(mesh.vertices),
        "edges": len(mesh.edges),
        "faces": len(mesh.polygons),
        "quads": sum(1 for polygon in mesh.polygons if len(polygon.vertices) == 4),
        "boundaryEdges": sum(1 for count in edge_use.values() if count == 1),
        "verticesPerRing": obj["aevrynd_vertices_per_ring"],
        "ringCount": obj["aevrynd_ring_count"],
    }


def bvh_overlap_count(a, b, depsgraph):
    tree_a = BVHTree.FromObject(a, depsgraph, epsilon=0.0)
    tree_b = BVHTree.FromObject(b, depsgraph, epsilon=0.0)
    if tree_a is None or tree_b is None:
        return None
    return len(tree_a.overlap(tree_b))


def make_wire_material():
    material = bpy.data.materials.new("Aevrynd_R440_TaperedLoopWire")
    material.diffuse_color = (0.01, 0.55, 1.0, 1.0)
    material.use_nodes = True
    bsdf = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (0.005, 0.22, 0.9, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.25
    bsdf.inputs["Emission Color"].default_value = (0.0, 0.14, 1.0, 1.0)
    bsdf.inputs["Emission Strength"].default_value = 2.0
    return material


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
body = bpy.data.objects[BODY]
patches = {side: build_lid_patch(body, side) for side in ("L", "R")}
wire_material = make_wire_material()
for patch in patches.values():
    patch.data.materials.append(wire_material)
    modifier = patch.modifiers.new("Aevrynd R440 Loop Wire Review", "WIREFRAME")
    modifier.thickness = 0.00016
    modifier.offset = 1.0
    modifier.use_replace = True

for obj in bpy.data.objects:
    name = obj.name.lower()
    if obj in patches.values() or obj == body:
        obj.hide_render = False
    elif any(token in name for token in ("eye", "caruncle", "tear", "brow", "lash")):
        obj.hide_render = False
    elif obj.type in {"MESH", "CURVES", "CURVE"}:
        obj.hide_render = True

scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
scene.camera = camera
views = (
    ("front", (0.0, -0.63, 1.607), (0.0, -0.035, 1.607), 105),
    ("three-quarter", (0.31, -0.57, 1.618), (0.0, -0.025, 1.605), 100),
    ("eyes-close", (0.0, -0.44, 1.607), (0.0, -0.045, 1.607), 118),
)
for name, location, target, lens in views:
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x = scene.render.resolution_y = 1200
    scene.render.filepath = str(RENDER_DIR / f"r440-wire-{name}.png")
    bpy.ops.render.render(write_still=True)

for patch in patches.values():
    for modifier in list(patch.modifiers):
        patch.modifiers.remove(modifier)
    patch.data.materials.clear()
    patch.data.materials.append(body.data.materials[0])
    for polygon in patch.data.polygons:
        polygon.use_smooth = True

for name, location, target, lens in views:
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(RENDER_DIR / f"r440-shaded-{name}.png")
    bpy.ops.render.render(write_still=True)

bpy.context.view_layer.update()
depsgraph = bpy.context.evaluated_depsgraph_get()
collision = {}
for side, patch in patches.items():
    collision[side] = {
        "sclera": bvh_overlap_count(patch, bpy.data.objects[f"AevryndEye_{side}_ScleraOpen_R420"], depsgraph),
        "cornea": bvh_overlap_count(patch, bpy.data.objects[f"AevryndEye_{side}_CorneaConvex_R420"], depsgraph),
    }
topology = {side: topology_stats(patch) for side, patch in patches.items()}
topology_pass = all(item["faces"] == item["quads"] and item["ringCount"] == RING_COUNT for item in topology.values())
collision_pass = all(value == 0 for side in collision.values() for value in side.values())
status = "REJECTED_DETACHED_FRAME_SURFACE" if topology_pass and collision_pass else "REJECTED_TAPERED_LOOP_GATE_FAIL"
scene["aevrynd_tapered_lid_loop_study"] = "v249r440"
scene["aevrynd_release_state"] = status
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "renderDirectory": str(RENDER_DIR),
    "method": "Four explicit concentric loops derived from the authored upper/lower lid margins. Vertical loop width follows a sine taper to zero at both canthi while horizontal width expands only at the canthi, then outer rings project to the owned body surface.",
    "topology": topology,
    "frame1TriangleOverlap": collision,
    "gates": {"topologyPass": topology_pass, "collisionPass": collision_pass},
    "derivedOnlyFromOwnedCC0Mainline": True,
    "integratedIntoHeadCage": False,
    "rigTransferred": False,
    "websitePromotionApproved": False,
    "colorManagement": {"viewTransform": "Standard", "look": "None", "exposureEV": 0.0},
    "status": status,
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R440_TAPERED_EYELID_LOOPS=" + json.dumps(report, sort_keys=True))
