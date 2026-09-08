import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v14.blend"
OUTPUT = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v15.blend"
BUILD = ROOT / ".character-build" / "aevrynd-female-authoring-v15.glb"
LOD1 = ROOT / ".character-build" / "aevrynd-female-authoring-v15-lod1.glb"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "mouth-v15"


def gaussian(value, center, spread):
    return math.exp(-0.5 * ((value - center) / spread) ** 2)


def sculpt_mouth_foundation(body):
    inverse = body.matrix_world.inverted()
    changed = 0
    maximum = 0.0
    for vertex in body.data.vertices:
        point = body.matrix_world @ vertex.co
        if point.y > -0.095 or abs(point.x) > 0.040 or not (1.523 <= point.z <= 1.547):
            continue
        groove = gaussian(point.z, 1.5350, 0.00165) * gaussian(point.x, 0.0, 0.024)
        corner = gaussian(abs(point.x), 0.030, 0.0042) * gaussian(point.z, 1.5350, 0.0030)
        philtrum_base = gaussian(point.x, 0.0, 0.007) * gaussian(point.z, 1.5445, 0.0045)
        moved = point.copy()
        moved.y += 0.00115 * groove + 0.00065 * corner
        moved.y -= 0.00028 * philtrum_base
        delta = (moved - point).length
        if delta > 1e-8:
            vertex.co = inverse @ moved
            changed += 1
            maximum = max(maximum, delta)
    body.data.update()
    body["aevrynd_mouth_revision"] = 15
    body["aevrynd_mouth_foundation_vertices"] = changed
    body["aevrynd_mouth_foundation_max_delta_m"] = maximum
    return changed, maximum


def body_surface(body):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(depsgraph)
    return BVHTree.FromObject(evaluated, depsgraph), evaluated.matrix_world, evaluated.matrix_world.inverted()


def front_surface(surface, x, z, clearance):
    tree, matrix, inverse = surface
    origin = Vector((x, -0.35, z))
    direction = Vector((0.0, 1.0, 0.0))
    location, normal, _, _ = tree.ray_cast(
        inverse @ origin, (inverse.to_3x3() @ direction).normalized(), 0.6,
    )
    if location is None:
        raise RuntimeError(f"face ray missed at x={x:.5f}, z={z:.5f}")
    point = matrix @ location
    normal_world = (matrix.inverted().transposed().to_3x3() @ normal).normalized()
    if normal_world.y > 0.0:
        normal_world.negate()
    return point + normal_world * clearance


def material(name, color, roughness, specular, subsurface=0.0, coat=0.0):
    result = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    result.use_nodes = True
    shader = result.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Roughness"].default_value = roughness
    if shader.inputs.get("Specular IOR Level"):
        shader.inputs["Specular IOR Level"].default_value = specular
    if shader.inputs.get("Subsurface Weight"):
        shader.inputs["Subsurface Weight"].default_value = subsurface
    if shader.inputs.get("Coat Weight"):
        shader.inputs["Coat Weight"].default_value = coat
    return result


def parent_to_rig(obj, rig):
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "OBJECT"
    obj.matrix_world = world


def skin_from_body(obj, body, rig):
    tree = KDTree(len(body.data.vertices))
    for vertex in body.data.vertices:
        tree.insert(body.matrix_world @ vertex.co, vertex.index)
    tree.balance()
    groups = {group.index: obj.vertex_groups.new(name=group.name) for group in body.vertex_groups}
    for vertex in obj.data.vertices:
        point = obj.matrix_world @ vertex.co
        _, source_index, _ = tree.find(point)
        assignments = sorted(
            ((entry.group, entry.weight) for entry in body.data.vertices[source_index].groups if entry.weight > 1e-8),
            key=lambda item: item[1], reverse=True,
        )[:4]
        total = sum(weight for _, weight in assignments)
        for group_index, weight in assignments:
            groups[group_index].add([vertex.index], weight / total, "REPLACE")
    modifier = obj.modifiers.new("Aevrynd Mouth Layer Deform", "ARMATURE")
    modifier.object = rig
    parent_to_rig(obj, rig)
    obj["aevrynd_skin_binding_revision"] = 15
    obj["aevrynd_weight_limit"] = 4


def add_dynamic_clearance(obj, strength):
    for vertex in obj.data.vertices:
        vertex.co.y -= strength
    obj.data.update()
    obj["aevrynd_dynamic_clearance_m"] = strength
    obj["aevrynd_clearance_direction"] = "character_front_negative_y"


def lip_boundary(t, upper):
    envelope = max(0.0, 1.0 - abs(t) ** 1.72)
    crease = 1.5350 + 0.00030 * math.cos(t * math.pi)
    if upper:
        cupid = 0.00135 * math.exp(-((abs(t) - 0.34) / 0.18) ** 2)
        center_notch = 0.00090 * math.exp(-(t / 0.13) ** 2)
        outer = crease + 0.0049 * envelope + cupid - center_notch
    else:
        outer = crease - 0.0061 * envelope - 0.00072 * math.exp(-(t / 0.34) ** 2)
    return crease, outer, envelope


def lip_mesh(name, surface, upper, lip_material, body, rig, columns=49, rows=5):
    vertices = []
    for column in range(columns):
        t = column / (columns - 1) * 2.0 - 1.0
        x = t * 0.0295
        crease, outer, envelope = lip_boundary(t, upper)
        inner = crease + (0.00026 if upper else -0.00026) * envelope
        for row in range(rows):
            u = row / (rows - 1)
            z = inner + (outer - inner) * u
            profile = math.sin(math.pi * u) ** 0.78
            center_emphasis = 0.72 + 0.28 * gaussian(t, 0.0, 0.38)
            maximum = 0.00130 if upper else 0.00170
            clearance = 0.00034 + maximum * profile * envelope * center_emphasis
            point = front_surface(surface, x, z, clearance)
            if upper:
                corner_separation = max(0.0, min(1.0, (abs(t) - 0.55) / 0.35))
                point.y -= 0.00250 * corner_separation * corner_separation
            vertices.append(point)
    faces = []
    for column in range(columns - 1):
        for row in range(rows - 1):
            a = column * rows + row
            face = (a, a + 1, a + rows + 1, a + rows)
            faces.append(tuple(reversed(face)) if upper else face)
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(vertices, [], faces)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(lip_material)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    obj["aevrynd_role"] = "upper_lip_volume" if upper else "lower_lip_volume"
    obj["aevrynd_mouth_revision"] = 15
    obj["aevrynd_surface_clearance_min_m"] = 0.00034
    obj["aevrynd_surface_clearance_peak_m"] = 0.00164 if upper else 0.00204
    obj["aevrynd_source"] = "Aevrynd surface-integrated lip volume"
    skin_from_body(obj, body, rig)
    add_dynamic_clearance(obj, 0.00300 if upper else 0.00130)
    return obj


def wet_line(surface, wet_material, body, rig, columns=65):
    vertices = []
    for column in range(columns):
        t = column / (columns - 1) * 2.0 - 1.0
        x = t * 0.0288
        crease, _, envelope = lip_boundary(t, True)
        half = 0.00022 * envelope + 0.000025
        vertices.append(front_surface(surface, x, crease - half, 0.00050))
        vertices.append(front_surface(surface, x, crease + half, 0.00050))
    faces = []
    for column in range(columns - 1):
        a = column * 2
        faces.append((a, a + 1, a + 3, a + 2))
    mesh = bpy.data.meshes.new("Mouth_WetLineMesh")
    mesh.from_pydata(vertices, [], faces)
    obj = bpy.data.objects.new("Mouth_WetLine", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(wet_material)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    obj["aevrynd_role"] = "mouth_wet_line"
    obj["aevrynd_mouth_revision"] = 15
    obj["aevrynd_surface_clearance_m"] = 0.00050
    skin_from_body(obj, body, rig)
    add_dynamic_clearance(obj, 0.00230)
    return obj


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, location, target, lens=86, size=900):
    scene = bpy.context.scene
    scene.frame_set(1)
    camera.data.lens = lens
    camera.location = location
    look_at(camera, target)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = size
    scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    for obj in bpy.data.objects:
        if obj.get("aevrynd_role") == "cornea":
            obj.hide_render = True
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
for name in ("Lip_Upper", "Lip_Lower", "Mouth_Crease", "Mouth_WetLine"):
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)

changed, maximum = sculpt_mouth_foundation(body)
surface = body_surface(body)
upper_material = material("Aevrynd_LipUpper_v15", (0.245, 0.069, 0.050, 1.0), 0.48, 0.18, 0.07)
lower_material = material("Aevrynd_LipLower_v15", (0.285, 0.078, 0.056, 1.0), 0.42, 0.20, 0.08)
wet_material = material("Aevrynd_MouthWetLine_v15", (0.055, 0.006, 0.004, 1.0), 0.16, 0.32, 0.0, 0.18)
upper = lip_mesh("Lip_Upper", surface, True, upper_material, body, rig)
lower = lip_mesh("Lip_Lower", surface, False, lower_material, body, rig)
wet = wet_line(surface, wet_material, body, rig)

bpy.context.scene["aevrynd_mouth_revision"] = 15
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
camera = bpy.data.objects["Aevrynd Review Camera"]
render(camera, "female-face-front", (0.0, -0.72, 1.575), (0.0, -0.005, 1.555))
render(camera, "female-face-three-quarter", (0.28, -0.64, 1.58), (0.0, 0.0, 1.55))
render(camera, "female-face-side", (0.66, -0.05, 1.575), (0.0, 0.0, 1.545))
render(camera, "female-mouth-close", (0.0, -0.39, 1.535), (0.0, -0.105, 1.535), 105, 900)

body_multires = next(modifier for modifier in body.modifiers if modifier.type == "MULTIRES")
old_multires = (body_multires.levels, body_multires.sculpt_levels, body_multires.render_levels)
body_multires.levels = body_multires.sculpt_levels = body_multires.render_levels = 0
export_runtime(BUILD, rig)
export_runtime(LOD1, rig, {"HairMain", "HairlineFine", "HairFlyaways"})
body_multires.levels, body_multires.sculpt_levels, body_multires.render_levels = old_multires

print("AEVRYND_MOUTH_V15_REPORT=" + json.dumps({
    "state": "AUTHORING",
    "foundation_vertices": changed,
    "foundation_max_delta_m": maximum,
    "lip_vertices": {upper.name: len(upper.data.vertices), lower.name: len(lower.data.vertices)},
    "wet_line_vertices": len(wet.data.vertices),
    "runtime_glb": str(BUILD),
    "lod1_glb": str(LOD1),
}))
