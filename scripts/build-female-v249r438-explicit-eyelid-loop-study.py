import json
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-layered-optical-stack-r420.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-explicit-eyelid-loops-r438-study.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-explicit-eyelid-loops-r438.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r438-explicit-eyelid-loop-study"
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
    return points, upper_flags


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
    inner, upper_flags = aperture_loop(side)
    center_x = sum(point.x for point in inner) / len(inner)
    center_z = sum(point.z for point in inner) / len(inner)
    center = Vector((center_x, sum(point.y for point in inner) / len(inner), center_z))
    ring_vertices = []
    for ring_index in range(RING_COUNT):
        ring = []
        for point, is_upper in zip(inner, upper_flags):
            dx = point.x - center_x
            dz = point.z - center_z
            if ring_index == 0:
                target = point.copy()
                target.y -= 0.00018
            else:
                x_scales = (1.0, 1.075, 1.18, 1.36)
                upper_z_scales = (1.0, 1.22, 1.78, 2.55)
                lower_z_scales = (1.0, 1.18, 1.52, 2.12)
                target = Vector((
                    center_x + dx * x_scales[ring_index],
                    point.y,
                    center_z + dz * (upper_z_scales[ring_index] if is_upper else lower_z_scales[ring_index]),
                ))
                target = project_body_surface(body, target)
                target.y -= (0.00062 if ring_index == 1 else 0.00024 if ring_index == 2 else 0.00012)
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
    mesh = bpy.data.meshes.new(f"AevryndEye_{side}_ExplicitLidLoops_R438Geometry")
    mesh.from_pydata(vertices, [], faces)
    mesh.validate(verbose=True, clean_customdata=True)
    mesh.update(calc_edges=True)
    obj = bpy.data.objects.new(f"AevryndEye_{side}_ExplicitLidLoops_R438", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj["aevrynd_layer"] = f"body.face.eye_{side.lower()}.explicit_lid_loops.study"
    obj["aevrynd_revision"] = "v249r438-study"
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
    material = bpy.data.materials.new("Aevrynd_R438_ExplicitLoopWire")
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
    modifier = patch.modifiers.new("Aevrynd R438 Loop Wire Review", "WIREFRAME")
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
    scene.render.filepath = str(RENDER_DIR / f"r438-{name}.png")
    bpy.ops.render.render(write_still=True)

for patch in patches.values():
    for modifier in patch.modifiers:
        modifier.show_viewport = False
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
status = "TECHNICAL_PASS_VISUAL_FAIL_CANTHUS_TAPER_REQUIRED" if topology_pass and collision_pass else "REJECTED_EXPLICIT_LOOP_GATE_FAIL"
scene["aevrynd_explicit_lid_loop_study"] = "v249r438"
scene["aevrynd_release_state"] = status
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "renderDirectory": str(RENDER_DIR),
    "method": "Four explicit concentric loops derived from the authored upper/lower lid margins, with outer rings projected to the owned body surface.",
    "topology": topology,
    "frame1TriangleOverlap": collision,
    "gates": {"topologyPass": topology_pass, "collisionPass": collision_pass},
    "derivedOnlyFromOwnedCC0Mainline": True,
    "integratedIntoHeadCage": False,
    "rigTransferred": False,
    "websitePromotionApproved": False,
    "status": status,
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R438_EXPLICIT_EYELID_LOOPS=" + json.dumps(report, sort_keys=True))
