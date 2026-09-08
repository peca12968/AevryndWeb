import json
import math
import random
from pathlib import Path

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v19.blend"
OUTPUT = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v20.blend"
BUILD = ROOT / ".character-build" / "aevrynd-female-authoring-v20.glb"
LOD1 = ROOT / ".character-build" / "aevrynd-female-authoring-v20-lod1.glb"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "eyes-v20"


def gaussian(value, center, spread):
    return math.exp(-0.5 * ((value - center) / spread) ** 2)


def clamp01(value):
    return max(0.0, min(1.0, value))


def sculpt_orbits(body):
    inverse = body.matrix_world.inverted()
    changed = 0
    maximum = 0.0
    upper_maximum = 0.0
    lower_maximum = 0.0
    for vertex in body.data.vertices:
        point = body.matrix_world @ vertex.co
        if point.y > -0.078 or not (1.584 <= point.z <= 1.630):
            continue
        center_x = 0.0345 if point.x >= 0.0 else -0.0345
        dx = point.x - center_x
        dz = point.z - 1.6077
        if abs(dx) > 0.031 or abs(dz) > 0.023:
            continue
        front = clamp01((-point.y - 0.078) / 0.050)
        horizontal = gaussian(dx, 0.0, 0.019)
        upper = gaussian(dz, 0.0060, 0.0065) * horizontal * front if dz >= -0.001 else 0.0
        lower = gaussian(dz, -0.0060, 0.0048) * horizontal * front if dz <= 0.001 else 0.0
        outer_sign = 1.0 if center_x > 0.0 else -1.0
        outer_corner = gaussian(dx, outer_sign * 0.018, 0.006) * gaussian(dz, 0.0, 0.007) * front
        z_delta = -0.00145 * upper + 0.00062 * lower + 0.00034 * outer_corner
        y_delta = -0.00052 * upper - 0.00022 * lower
        target = point + Vector((0.0, y_delta, z_delta))
        delta = (target - point).length
        if delta <= 1e-7:
            continue
        vertex.co = inverse @ target
        changed += 1
        maximum = max(maximum, delta)
        upper_maximum = max(upper_maximum, abs(0.00145 * upper))
        lower_maximum = max(lower_maximum, abs(0.00062 * lower))
    body.data.update()
    body["aevrynd_eye_revision"] = 20
    body["aevrynd_orbit_vertices"] = changed
    body["aevrynd_orbit_max_delta_m"] = maximum
    return changed, maximum, upper_maximum, lower_maximum


def move_layer(obj, z_delta, y_delta):
    inverse = obj.matrix_world.inverted()
    for vertex in obj.data.vertices:
        world = obj.matrix_world @ vertex.co
        world.z += z_delta
        world.y += y_delta
        vertex.co = inverse @ world
    obj.data.update()
    obj["aevrynd_eye_revision"] = 20
    obj["aevrynd_eye_z_delta_m"] = z_delta
    obj["aevrynd_eye_y_delta_m"] = y_delta


def tune_eye_layers():
    movements = {
        "Eye_L_UpperLashes": (-0.00090, -0.00135),
        "Eye_R_UpperLashes": (-0.00090, -0.00135),
        "Eye_L_UpperFold": (-0.00072, 0.0),
        "Eye_R_UpperFold": (-0.00072, 0.0),
        "Eye_L_LowerLashes": (0.00034, -0.00135),
        "Eye_R_LowerLashes": (0.00034, -0.00135),
        "Eye_L_TearMeniscus": (0.00018, -0.00110),
        "Eye_R_TearMeniscus": (0.00018, -0.00110),
    }
    for name, (z_delta, y_delta) in movements.items():
        move_layer(bpy.data.objects[name], z_delta, y_delta)
    for name in ("Eye_L_Catchlight", "Eye_R_Catchlight"):
        obj = bpy.data.objects[name]
        obj.scale *= 0.58
        obj["aevrynd_eye_revision"] = 20
    for name in ("Eye_L_Cornea", "Eye_R_Cornea"):
        obj = bpy.data.objects[name]
        obj.hide_render = False
        obj["aevrynd_eye_revision"] = 20
    return movements


def enforce_eye_layer_clearance(body, names, clearance=0.00032):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    polygons = [tuple(polygon.vertices) for polygon in mesh.polygons]
    tree = BVHTree.FromPolygons(points, polygons, all_triangles=False)
    report = {}
    for name in names:
        obj = bpy.data.objects[name]
        inverse = obj.matrix_world.inverted()
        adjusted = 0
        maximum = 0.0
        for vertex in obj.data.vertices:
            world = obj.matrix_world @ vertex.co
            location, normal, _, distance = tree.find_nearest(world)
            if location is None:
                continue
            if normal.y > 0.0:
                normal = -normal
            signed = (world - location).dot(normal)
            if signed >= clearance:
                continue
            target = location + normal * clearance
            delta = (target - world).length
            vertex.co = inverse @ target
            adjusted += 1
            maximum = max(maximum, delta)
        obj.data.update()
        obj["aevrynd_clearance_m"] = clearance
        report[name] = {"adjusted_vertices": adjusted, "maximum_delta_m": maximum}
    evaluated.to_mesh_clear()
    return report


def material(name, color, roughness):
    result = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    result.use_nodes = True
    bsdf = next((node for node in result.node_tree.nodes if node.type == "BSDF_PRINCIPLED"), None)
    if not bsdf:
        bsdf = result.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
        output = next((node for node in result.node_tree.nodes if node.type == "OUTPUT_MATERIAL"), None)
        if not output:
            output = result.node_tree.nodes.new("ShaderNodeOutputMaterial")
        result.node_tree.links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    return result


def build_iris_fibers(rig):
    for old_name in ("Eye_L_IrisFibers", "Eye_R_IrisFibers"):
        old = bpy.data.objects.get(old_name)
        if old:
            bpy.data.objects.remove(old, do_unlink=True)
    dark = material("Aevrynd_IrisFiber_Dark", (0.032, 0.008, 0.0025), 0.34)
    amber = material("Aevrynd_IrisFiber_Amber", (0.16, 0.055, 0.012), 0.31)
    rng = random.Random(20260905)
    counts = {}
    for side, iris_name in (("L", "Eye_L_Iris"), ("R", "Eye_R_Iris")):
        iris = bpy.data.objects[iris_name]
        corners = [iris.matrix_world @ Vector(corner) for corner in iris.bound_box]
        center_x = (min(p.x for p in corners) + max(p.x for p in corners)) * 0.5
        center_z = (min(p.z for p in corners) + max(p.z for p in corners)) * 0.5
        plane_y = min(p.y for p in corners) - 0.00046
        vertices = []
        faces = []
        material_indices = []
        ray_count = 52
        for index in range(ray_count):
            angle = 2.0 * math.pi * index / ray_count + rng.uniform(-0.018, 0.018)
            inner = rng.uniform(0.00185, 0.00235)
            outer = rng.uniform(0.00370, 0.00425)
            width = rng.uniform(0.000035, 0.000075)
            tangent_x, tangent_z = -math.sin(angle) * width, math.cos(angle) * width
            radial_x, radial_z = math.cos(angle), math.sin(angle)
            base = len(vertices)
            vertices.extend([
                (center_x + radial_x * inner - tangent_x, plane_y, center_z + radial_z * inner - tangent_z),
                (center_x + radial_x * inner + tangent_x, plane_y, center_z + radial_z * inner + tangent_z),
                (center_x + radial_x * outer + tangent_x * 0.45, plane_y, center_z + radial_z * outer + tangent_z * 0.45),
                (center_x + radial_x * outer - tangent_x * 0.45, plane_y, center_z + radial_z * outer - tangent_z * 0.45),
            ])
            faces.append((base, base + 1, base + 2, base + 3))
            material_indices.append(1 if index % 5 in (0, 1) else 0)
        mesh = bpy.data.meshes.new(f"Eye_{side}_IrisFibersMesh")
        mesh.from_pydata(vertices, [], faces)
        mesh.materials.append(dark)
        mesh.materials.append(amber)
        for polygon, material_index in zip(mesh.polygons, material_indices):
            polygon.material_index = material_index
        obj = bpy.data.objects.new(f"Eye_{side}_IrisFibers", mesh)
        bpy.context.scene.collection.objects.link(obj)
        obj["aevrynd_role"] = "iris_fibers"
        obj["aevrynd_eye_revision"] = 20
        obj.parent = rig
        obj.parent_type = "BONE"
        obj.parent_bone = "head"
        obj.matrix_world = Matrix.Identity(4)
        counts[obj.name] = {"rays": ray_count, "vertices": len(vertices), "faces": len(faces)}
    return counts


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, location, target, lens=96):
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 900
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    camera.data.lens = lens
    camera.location = location
    look_at(camera, target)
    for obj in bpy.data.objects:
        if obj.get("aevrynd_role") == "cornea":
            obj.hide_render = False
    bpy.ops.render.render(write_still=True)


def export_runtime(path, rig, excluded=()):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in bpy.data.objects:
        if obj.type in {"MESH", "ARMATURE"} and obj.name not in excluded:
            obj.hide_render = False
            obj.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.export_scene.gltf(
        filepath=str(path), export_format="GLB", use_selection=True,
        export_apply=True, export_yup=True, export_extras=True,
        export_animations=True, export_frame_range=True,
        export_attributes=True, export_vertex_color="ACTIVE",
    )


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
bpy.context.preferences.filepaths.save_version = 0
bpy.context.scene.frame_set(1)
RENDER_DIR.mkdir(parents=True, exist_ok=True)
BUILD.parent.mkdir(parents=True, exist_ok=True)
body = bpy.data.objects["AevryndFemaleBodyBase"]
rig = bpy.data.objects["AevryndFemaleRig"]
changed, maximum, upper_maximum, lower_maximum = sculpt_orbits(body)
movements = tune_eye_layers()
clearance = enforce_eye_layer_clearance(body, (
    "Eye_L_UpperLashes", "Eye_R_UpperLashes",
    "Eye_L_LowerLashes", "Eye_R_LowerLashes",
    "Eye_L_TearMeniscus", "Eye_R_TearMeniscus",
))
fibers = build_iris_fibers(rig)
bpy.context.scene["aevrynd_eye_revision"] = 20
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

camera = bpy.data.objects["Aevrynd Review Camera"]
render(camera, "female-eyes-front", (0.0, -0.72, 1.575), (0.0, -0.005, 1.555), 86)
render(camera, "female-eyes-three-quarter", (0.28, -0.64, 1.58), (0.0, 0.0, 1.55), 86)
render(camera, "female-eyes-close", (0.0, -0.48, 1.592), (0.0, -0.075, 1.592), 108)

multires = next(modifier for modifier in body.modifiers if modifier.type == "MULTIRES")
old_levels = (multires.levels, multires.sculpt_levels, multires.render_levels)
multires.levels = multires.sculpt_levels = multires.render_levels = 0
export_runtime(BUILD, rig)
export_runtime(LOD1, rig, {"HairMain", "HairFlyaways"})
multires.levels, multires.sculpt_levels, multires.render_levels = old_levels

print("AEVRYND_EYES_V20_REPORT=" + json.dumps({
    "state": "AUTHORING",
    "orbit_vertices": changed,
    "maximum_orbit_delta_m": maximum,
    "maximum_upper_lid_delta_m": upper_maximum,
    "maximum_lower_lid_delta_m": lower_maximum,
    "layer_movements_m": movements,
    "clearance": clearance,
    "iris_fibers": fibers,
    "runtime_glb": str(BUILD),
    "lod1_glb": str(LOD1),
}))
