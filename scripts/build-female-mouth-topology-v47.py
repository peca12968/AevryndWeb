import json
import math
from pathlib import Path

import bpy
import bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v46.blend"
OUTPUT = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v47.blend"
BUILD = ROOT / ".character-build" / "aevrynd-female-authoring-v47.glb"
LOD1 = ROOT / ".character-build" / "aevrynd-female-authoring-v47-lod1.glb"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "mouth-topology-v47"


def material(name, color, roughness, coat=0.0):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    shader = next(node for node in mat.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Specular IOR Level"].default_value = 0.20
    shader.inputs["Coat Weight"].default_value = coat
    shader.inputs["Coat Roughness"].default_value = 0.24
    mat["aevrynd_runtime_owned"] = True
    return mat


def surface(body):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    result = BVHTree.FromPolygons(points, faces, all_triangles=False)
    evaluated.to_mesh_clear()
    return result


def bake_subdivision_and_open_mouth(body):
    multires = next(modifier for modifier in body.modifiers if modifier.type == "MULTIRES")
    multires.levels = 1
    multires.sculpt_levels = 1
    multires.render_levels = 1
    bpy.ops.object.select_all(action="DESELECT")
    body.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.modifier_apply(modifier=multires.name)
    before = len(body.data.polygons)
    bm = bmesh.new()
    bm.from_mesh(body.data)
    world = body.matrix_world
    selected = []
    for face in bm.faces:
        center = world @ face.calc_center_median()
        nx = abs(center.x) / 0.0265
        nz = abs(center.z - 1.53465) / 0.00120
        if center.y < -0.126 and nx * nx + nz * nz < 1.0:
            selected.append(face)
    if len(selected) < 8:
        raise RuntimeError(f"mouth opening selected only {len(selected)} faces")
    bmesh.ops.delete(bm, geom=selected, context="FACES_ONLY")
    bm.to_mesh(body.data)
    bm.free()
    for polygon in body.data.polygons:
        polygon.use_smooth = True
    body.data.update()
    trimmed = 0
    unweighted = 0
    maximum_influences = 0
    for vertex in body.data.vertices:
        weights = sorted(((element.group, element.weight) for element in vertex.groups), key=lambda item: item[1], reverse=True)
        if not weights:
            unweighted += 1
            continue
        maximum_influences = max(maximum_influences, len(weights))
        keep = weights[:4]
        for group_index, _ in weights[4:]:
            body.vertex_groups[group_index].remove([vertex.index])
            trimmed += 1
        total = sum(weight for _, weight in keep)
        if total > 0.0:
            for group_index, weight in keep:
                body.vertex_groups[group_index].add([vertex.index], weight / total, "REPLACE")
    body["aevrynd_mouth_topology_revision"] = 47
    body["aevrynd_mouth_opening_faces_removed"] = len(selected)
    body["aevrynd_subdivision_baked_level"] = 1
    return {"faces_before": before, "faces_after": len(body.data.polygons), "opening_faces_removed": len(selected), "trimmed_weight_entries": trimmed, "unweighted_vertices": unweighted, "maximum_source_influences": maximum_influences}


def face_point(tree, x, z, clearance=0.00010):
    location, normal, _, _ = tree.ray_cast(Vector((x, -0.30, z)), Vector((0.0, 1.0, 0.0)), 0.55)
    if location is None:
        raise RuntimeError(f"mouth surface ray missed x={x:.5f} z={z:.5f}")
    if normal.y > 0.0:
        normal.negate()
    return location + normal.normalized() * clearance


def bind(obj, rig, role):
    obj["aevrynd_role"] = role
    obj["aevrynd_face_revision"] = 47
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = Matrix.Identity(4)


def skin_to_body(obj, rig, body, role):
    obj["aevrynd_role"] = role
    obj["aevrynd_face_revision"] = 47
    obj.parent = rig
    obj.parent_type = "OBJECT"
    obj.matrix_world = Matrix.Identity(4)
    groups = [obj.vertex_groups.new(name=group.name) for group in body.vertex_groups]
    kd = KDTree(len(body.data.vertices))
    for vertex in body.data.vertices:
        kd.insert(body.matrix_world @ vertex.co, vertex.index)
    kd.balance()
    for vertex in obj.data.vertices:
        _, source_index, _ = kd.find(obj.matrix_world @ vertex.co)
        for element in body.data.vertices[source_index].groups:
            groups[element.group].add([vertex.index], element.weight, "REPLACE")
    armature = obj.modifiers.new("Aevrynd Mouth Skin v47", "ARMATURE")
    armature.object = rig


def delete_object(name):
    old = bpy.data.objects.get(name)
    if old is not None:
        old_mesh = old.data
        bpy.data.objects.remove(old, do_unlink=True)
        if old_mesh.users == 0:
            bpy.data.meshes.remove(old_mesh)


def lip_profile(t, upper):
    envelope = max(0.0, 1.0 - abs(t) ** 1.72)
    crease = 1.53465 + 0.00010 * math.cos(math.pi * t)
    if upper:
        bow = 0.00118 * math.exp(-((abs(t) - 0.34) / 0.19) ** 2)
        notch = 0.00058 * math.exp(-(t / 0.13) ** 2)
        height = envelope * 0.00335 + bow - notch
        outer = crease + height + 0.00135 * envelope
        crest = crease + height
        inner = crease + 0.00020 * envelope
    else:
        center_fullness = 0.00048 * math.exp(-(t / 0.34) ** 2)
        height = envelope * 0.00345 + center_fullness
        outer = crease - height - 0.00115 * envelope
        crest = crease - height
        inner = crease - 0.00018 * envelope
    return envelope, crease, outer, crest, inner


def rebuild_lip(name, upper, body, body_tree, transition_material, lip_material, inner_material, rig):
    delete_object(name)
    columns = 65
    rows = 5
    vertices = []
    material_indices = []
    for column in range(columns):
        t = column / (columns - 1) * 2.0 - 1.0
        x = 0.0274 * t
        envelope, crease, outer, crest, inner = lip_profile(t, upper)
        corner_offset = (0.00010 if upper else -0.00010) * abs(t) ** 8
        crease += corner_offset
        outer += corner_offset
        crest += corner_offset
        inner += corner_offset
        transition_z = outer + (0.00100 if upper else -0.00100) * envelope
        outer_point = face_point(body_tree, x, transition_z, 0.00008)
        rim_point = face_point(body_tree, x, outer, 0.00012)
        # Profile depth is zero at the commissures and strongest near the centre.
        projection = envelope ** 0.72
        crest_y = rim_point.y - 0.00095 * projection
        mid_z = crest + (inner - crest) * 0.52
        mid_y = rim_point.y - 0.00118 * projection
        inner_y = rim_point.y - 0.00082 * projection
        wet_y = rim_point.y - 0.00088 * projection
        wet_z = crease + (0.00022 if upper else -0.00022) * envelope
        vertices.extend((
            tuple(outer_point),
            tuple(rim_point),
            (x, crest_y, crest),
            (x, mid_y, mid_z),
            (x, wet_y, wet_z),
        ))
    faces = []
    for column in range(columns - 1):
        for row in range(rows - 1):
            a = column * rows + row
            faces.append((a, a + rows, a + rows + 1, a + 1))
            material_indices.append(0 if row == 0 else 1 if row < 3 else 2)
    mesh = bpy.data.meshes.new(name + "MeshV47")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(transition_material)
    mesh.materials.append(lip_material)
    mesh.materials.append(inner_material)
    for polygon, index in zip(mesh.polygons, material_indices):
        polygon.material_index = index
        polygon.use_smooth = True
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    smooth = obj.modifiers.new("Aevrynd Lip Profile Smooth v47", "SUBSURF")
    smooth.subdivision_type = "CATMULL_CLARK"
    smooth.levels = 1
    smooth.render_levels = 2
    skin_to_body(obj, rig, body, "upper_lip_integrated" if upper else "lower_lip_integrated")
    obj["aevrynd_profile_rows"] = rows
    obj["aevrynd_skin_transition_rows"] = 1
    obj["aevrynd_commissure_width_m"] = 0.0548
    return obj


def rebuild_wetline(rig):
    delete_object("Mouth_WetLine")
    columns = 65
    vertices = []
    faces = []
    for column in range(columns):
        t = column / (columns - 1) * 2.0 - 1.0
        taper = max(0.0, 1.0 - abs(t) ** 2.8)
        x = 0.0270 * t
        center = 1.53465 + 0.00010 * math.cos(math.pi * t)
        half = (0.000025 + 0.000080 * taper) * math.sin(math.pi * column / (columns - 1)) ** 0.65
        y = -0.14138 - 0.00028 * taper
        vertices.extend(((x, y, center - half), (x, y, center + half)))
        if column:
            a = (column - 1) * 2
            faces.append((a, a + 2, a + 3, a + 1))
    mesh = bpy.data.meshes.new("Mouth_WetLineMeshV47")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(material("Aevrynd_MouthWetLine_v47", (0.050, 0.006, 0.008), 0.31, 0.05))
    obj = bpy.data.objects.new("Mouth_WetLine", mesh)
    bpy.context.scene.collection.objects.link(obj)
    bind(obj, rig, "mouth_wet_margin")
    obj["aevrynd_max_half_width_m"] = 0.000105
    return obj


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, location, target, lens=96, width=900, height=900):
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
topology = bake_subdivision_and_open_mouth(body)
body_tree = surface(body)
transition = material("Aevrynd_LipSkinTransition_v47", (0.355, 0.145, 0.120), 0.61)
next(node for node in transition.node_tree.nodes if node.type == "BSDF_PRINCIPLED").inputs["Subsurface Weight"].default_value = 0.06
lip = material("Aevrynd_LipVermilion_v47", (0.205, 0.052, 0.047), 0.46, 0.025)
inner = material("Aevrynd_LipInner_v47", (0.145, 0.025, 0.028), 0.38, 0.045)
upper = rebuild_lip("Lip_Upper", True, body, body_tree, transition, lip, inner, rig)
lower = rebuild_lip("Lip_Lower", False, body, body_tree, transition, lip, inner, rig)
wetline = rebuild_wetline(rig)
body["aevrynd_mouth_opening_state"] = "open_subdivided_topology"
bpy.context.scene["aevrynd_face_revision"] = 47
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

camera = bpy.data.objects["Aevrynd Review Camera"]
render(camera, "female-mouth-close", (0.0, -0.43, 1.525), (0.0, -0.105, 1.525), 120, 1000, 700)
render(camera, "female-face-front", (0.0, -0.72, 1.575), (0.0, -0.005, 1.555))
render(camera, "female-face-three-quarter", (0.28, -0.64, 1.58), (0.0, 0.0, 1.55))
render(camera, "female-mouth-side", (0.56, -0.18, 1.545), (0.0, -0.105, 1.535), 105)

export_runtime(BUILD, rig)
export_runtime(LOD1, rig, {
    "HairMain", "HairFlyaways", "HairGuides", "HairClumpsMediumCards", "HairlineBaby", "HairTempleClumps", "HairNapeClumps", "HairBoundaryClumps", "HairUndercutScalp",
    "Brow_L_Density", "Brow_R_Density",
    "Eye_L_Catchlight", "Eye_R_Catchlight", "Eye_L_IrisFibers", "Eye_R_IrisFibers",
    "Eye_L_LimbalRing", "Eye_R_LimbalRing", "Eye_L_TearMeniscus", "Eye_R_TearMeniscus",
    "Eye_L_Caruncle", "Eye_R_Caruncle", "Eye_L_UpperFold", "Eye_R_UpperFold",
    "Eye_L_UpperLashes", "Eye_R_UpperLashes", "Eye_L_LowerLashes", "Eye_R_LowerLashes",
})
print("AEVRYND_MOUTH_TOPOLOGY_V47=" + json.dumps({
    "state": "AUTHORING",
    "topology": topology,
    "upper": {"vertices": len(upper.data.vertices), "faces": len(upper.data.polygons)},
    "lower": {"vertices": len(lower.data.vertices), "faces": len(lower.data.polygons)},
    "wetline": {"vertices": len(wetline.data.vertices), "faces": len(wetline.data.polygons)},
    "runtime_glb": str(BUILD),
    "lod1_glb": str(LOD1),
}))
