import json
import math
from pathlib import Path

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v36.blend"
OUTPUT = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v37.blend"
BUILD = ROOT / ".character-build" / "aevrynd-female-authoring-v37.glb"
LOD1 = ROOT / ".character-build" / "aevrynd-female-authoring-v37-lod1.glb"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "eye-margins-v37"


def material(name, color, roughness, coat=0.0):
    result = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    result.use_nodes = True
    nodes = result.node_tree.nodes
    links = result.node_tree.links
    shader = next((node for node in nodes if node.type == "BSDF_PRINCIPLED"), None)
    if not shader:
        shader = nodes.new("ShaderNodeBsdfPrincipled")
        output = next((node for node in nodes if node.type == "OUTPUT_MATERIAL"), None) or nodes.new("ShaderNodeOutputMaterial")
        links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Specular IOR Level"].default_value = 0.23
    if shader.inputs.get("Coat Weight"):
        shader.inputs["Coat Weight"].default_value = coat
        shader.inputs["Coat Roughness"].default_value = 0.12
    result["aevrynd_runtime_owned"] = True
    return result


def surface(body):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    tree = BVHTree.FromPolygons(points, faces, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


def front_point(tree, x, z, clearance):
    location, normal, _, _ = tree.ray_cast(Vector((x, -0.36, z)), Vector((0.0, 1.0, 0.0)), 0.7)
    if location is None:
        raise RuntimeError(f"eye-margin ray missed at {x:.5f}, {z:.5f}")
    if normal.y > 0.0:
        normal.negate()
    return location + normal.normalized() * clearance


def parent_to_head(obj, rig):
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = Matrix.Identity(4)


def rebuild_meniscus(tree, rig, side, center_x, mat):
    name = f"Eye_{side}_TearMeniscus"
    old = bpy.data.objects.get(name)
    if old:
        old_mesh = old.data
        bpy.data.objects.remove(old, do_unlink=True)
        if old_mesh.users == 0:
            bpy.data.meshes.remove(old_mesh)
    columns = 47
    vertices = []
    faces = []
    for column in range(columns):
        t = column / (columns - 1) * 2.0 - 1.0
        x = center_x + t * 0.01775
        arc = math.sqrt(max(0.0, 1.0 - t * t))
        center_z = 1.60715 - 0.00415 * arc + 0.00016 * t
        taper = math.sin(math.pi * column / (columns - 1)) ** 0.72
        half_width = 0.000035 + 0.00018 * taper
        vertices.append(front_point(tree, x, center_z - half_width, 0.00030))
        vertices.append(front_point(tree, x, center_z + half_width, 0.00034))
        if column:
            a = (column - 1) * 2
            faces.append((a, a + 1, a + 3, a + 2))
    mesh = bpy.data.meshes.new(name + "MeshV37")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(mat)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj["aevrynd_role"] = "tear_meniscus"
    obj["aevrynd_eye_revision"] = 37
    obj["aevrynd_surface_clearance_m"] = 0.00030
    parent_to_head(obj, rig)
    return obj


def build_caruncle(tree, rig, side, center_x, mat):
    name = f"Eye_{side}_Caruncle"
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    inward = -1.0 if center_x > 0.0 else 1.0
    cx = center_x + inward * 0.01715
    cz = 1.60655
    vertices = [front_point(tree, cx, cz, 0.00039)]
    faces = []
    ring = 14
    for index in range(ring):
        angle = math.tau * index / ring
        # The pointed outer end and fuller medial base create a small teardrop.
        radial = 0.72 + 0.28 * (0.5 + 0.5 * math.cos(angle))
        x = cx + math.cos(angle) * 0.00120 * radial
        z = cz + math.sin(angle) * 0.00072
        vertices.append(front_point(tree, x, z, 0.00040))
    for index in range(ring):
        faces.append((0, 1 + index, 1 + (index + 1) % ring))
    mesh = bpy.data.meshes.new(name + "MeshV37")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(mat)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj["aevrynd_role"] = "lacrimal_caruncle"
    obj["aevrynd_eye_revision"] = 37
    obj["aevrynd_surface_clearance_m"] = 0.00039
    parent_to_head(obj, rig)
    return obj


def tune_upper_fold():
    mat = bpy.data.materials["Aevrynd_EyelidFold"]
    shader = next(node for node in mat.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    shader.inputs["Base Color"].default_value = (0.33, 0.105, 0.068, 1.0)
    shader.inputs["Roughness"].default_value = 0.67
    shader.inputs["Specular IOR Level"].default_value = 0.18
    mat["aevrynd_eye_revision"] = 37


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, location, target, lens, width=900, height=900):
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = width
    scene.render.resolution_y = height
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
tree = surface(body)
meniscus_mat = material("Aevrynd_TearFilm_v37", (0.30, 0.105, 0.070), 0.24, 0.12)
caruncle_mat = material("Aevrynd_Caruncle_v37", (0.34, 0.075, 0.052), 0.36, 0.05)
objects = []
for side, center_x in (("L", 0.0345), ("R", -0.0345)):
    objects.append(rebuild_meniscus(tree, rig, side, center_x, meniscus_mat))
    objects.append(build_caruncle(tree, rig, side, center_x, caruncle_mat))
tune_upper_fold()
bpy.context.scene["aevrynd_eye_revision"] = 37
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

camera = bpy.data.objects["Aevrynd Review Camera"]
render(camera, "female-eyes-front", (0.0, -0.72, 1.575), (0.0, -0.005, 1.555), 96)
render(camera, "female-eyes-three-quarter", (0.28, -0.64, 1.58), (0.0, 0.0, 1.55), 96)
render(camera, "female-eyes-close", (0.0, -0.43, 1.603), (0.0, -0.09, 1.605), 115, 1000, 700)

multires = next(modifier for modifier in body.modifiers if modifier.type == "MULTIRES")
old_levels = (multires.levels, multires.sculpt_levels, multires.render_levels)
multires.levels = multires.sculpt_levels = multires.render_levels = 0
export_runtime(BUILD, rig)
export_runtime(LOD1, rig, {"HairMain", "HairFlyaways"})
multires.levels, multires.sculpt_levels, multires.render_levels = old_levels

print("AEVRYND_EYE_MARGINS_V37_REPORT=" + json.dumps({
    "state": "AUTHORING",
    "layers": {obj.name: {"vertices": len(obj.data.vertices), "faces": len(obj.data.polygons)} for obj in objects},
    "runtime_glb": str(BUILD),
    "lod1_glb": str(LOD1),
}))
