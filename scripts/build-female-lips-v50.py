import json
import math
from pathlib import Path

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v47.blend"
OUTPUT = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v50.blend"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "lips-v50"


def make_material(name, color, roughness, coat=0.0, subsurface=0.0):
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    shader = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Specular IOR Level"].default_value = 0.21
    shader.inputs["Coat Weight"].default_value = coat
    shader.inputs["Coat Roughness"].default_value = 0.30
    shader.inputs["Subsurface Weight"].default_value = subsurface
    material["aevrynd_runtime_owned"] = True
    return material


def body_tree(body):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    tree = BVHTree.FromPolygons(points, faces, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


def face_point(tree, x, z, clearance):
    location, normal, _, _ = tree.ray_cast(Vector((x, -0.30, z)), Vector((0.0, 1.0, 0.0)), 0.55)
    if location is None:
        raise RuntimeError(f"lip surface ray missed x={x:.5f} z={z:.5f}")
    if normal.y > 0.0:
        normal.negate()
    return location + normal.normalized() * clearance


def delete_object(name):
    old = bpy.data.objects.get(name)
    if old:
        mesh = old.data
        bpy.data.objects.remove(old, do_unlink=True)
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)


def skin_to_body(obj, rig, body, role):
    obj["aevrynd_role"] = role
    obj["aevrynd_face_revision"] = 50
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
        weights = sorted(
            ((element.group, element.weight) for element in body.data.vertices[source_index].groups),
            key=lambda item: item[1], reverse=True,
        )[:4]
        total = sum(weight for _, weight in weights)
        for group_index, weight in weights:
            groups[group_index].add([vertex.index], weight / total, "REPLACE")
    armature = obj.modifiers.new("Aevrynd Lip Skin v50", "ARMATURE")
    armature.object = rig


def enforce_body_clearance(obj, tree, clearance=0.00030):
    adjusted = 0
    maximum = 0.0
    for vertex in obj.data.vertices:
        point = obj.matrix_world @ vertex.co
        location, normal, _, _ = tree.find_nearest(point)
        if location is None:
            continue
        if normal.y > 0.0:
            normal.negate()
        signed = (point - location).dot(normal)
        if signed >= clearance:
            continue
        target = point + normal.normalized() * (clearance - signed)
        vertex.co = obj.matrix_world.inverted() @ target
        adjusted += 1
        maximum = max(maximum, (target - point).length)
    obj.data.update()
    obj["aevrynd_clearance_adjusted_vertices"] = adjusted
    obj["aevrynd_body_clearance_m"] = clearance
    obj["aevrynd_clearance_max_delta_m"] = maximum
    return adjusted


def lip_profile(t, upper):
    envelope = max(0.0, 1.0 - t * t) ** 0.82
    crease = 1.53465 + 0.00008 * math.cos(math.pi * t)
    if upper:
        bow = 0.00100 * math.exp(-((abs(t) - 0.32) / 0.19) ** 2)
        notch = 0.00055 * math.exp(-(t / 0.14) ** 2)
        crest = crease + 0.00355 * envelope + bow - notch
        outer = crest + 0.00105 * envelope
        inner = crease + 0.00017 * envelope
    else:
        center = 0.00042 * math.exp(-(t / 0.38) ** 2)
        crest = crease - 0.00365 * envelope - center
        outer = crest - 0.00118 * envelope
        inner = crease - 0.00016 * envelope
    return envelope, crease, outer, crest, inner


def rebuild_lip(name, upper, body, rig, tree, materials):
    delete_object(name)
    columns, rows = 65, 7
    vertices, faces, material_indices = [], [], []
    sign = 1.0 if upper else -1.0
    for column in range(columns):
        t = column / (columns - 1) * 2.0 - 1.0
        envelope, crease, outer, crest, inner = lip_profile(t, upper)
        corner_gap = sign * 0.00010 * abs(t) ** 12
        crease += corner_gap
        outer += corner_gap
        crest += corner_gap
        inner += corner_gap
        taper = math.sin(math.pi * column / (columns - 1)) ** 0.68
        transition_z = outer + sign * (0.00125 * envelope + 0.00008)
        transition_x = 0.0282 * t
        rim_x = 0.0274 * t
        core_x = 0.0268 * t
        transition = face_point(tree, transition_x, transition_z, 0.00016)
        rim = face_point(tree, rim_x, outer, 0.00022)
        projection = envelope ** 0.72 * taper
        wrinkle = 0.000055 * math.sin(7.0 * math.pi * t + (0.4 if upper else -0.2)) * projection
        shoulder_z = outer + (crest - outer) * 0.48
        mid_z = crest + (inner - crest) * 0.52
        vertices.extend((
            tuple(transition),
            tuple(rim),
            (0.0271 * t, rim.y - 0.00034 * projection, shoulder_z),
            (core_x, rim.y - (0.00102 if upper else 0.00122) * projection + wrinkle, crest),
            (core_x, rim.y - (0.00128 if upper else 0.00148) * projection - wrinkle, mid_z),
            (0.0269 * t, rim.y - 0.00100 * projection, inner + sign * 0.00012 * envelope),
            (0.0267 * t, rim.y - 0.00084 * projection, crease + sign * 0.00012 * envelope),
        ))
    for column in range(columns - 1):
        for row in range(rows - 1):
            a = column * rows + row
            faces.append((a, a + rows, a + rows + 1, a + 1))
            material_indices.append(0 if row < 2 else 1 if row < 5 else 2)
    mesh = bpy.data.meshes.new(name + "MeshV50")
    mesh.from_pydata(vertices, [], faces)
    for material in materials:
        mesh.materials.append(material)
    for polygon, material_index in zip(mesh.polygons, material_indices):
        polygon.material_index = material_index
        polygon.use_smooth = True
    colors = mesh.color_attributes.new(name="AevryndSkinTone", type="BYTE_COLOR", domain="POINT")
    for item in colors.data:
        item.color_srgb = (0.992, 0.986, 0.982, 1.0)
    uv = mesh.uv_layers.new(name="UVMap")
    for loop in mesh.loops:
        point = mesh.vertices[loop.vertex_index].co
        uv.data[loop.index].uv = (0.5 + point.x * 4.5, 0.5 + (point.z - 1.53465) * 8.0)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    smooth = obj.modifiers.new("Aevrynd Lip Continuity v50", "SUBSURF")
    smooth.subdivision_type = "CATMULL_CLARK"
    smooth.levels = 0
    smooth.render_levels = 1
    enforce_body_clearance(obj, tree)
    skin_to_body(obj, rig, body, "upper_lip_integrated" if upper else "lower_lip_integrated")
    obj["aevrynd_profile_rows"] = rows
    obj["aevrynd_skin_transition_rows"] = 2
    obj["aevrynd_commissure_width_m"] = 0.0564
    return obj


def rebuild_wetline(upper, lower, rig, body):
    delete_object("Mouth_WetLine")
    columns = 65
    rows = 7
    vertices, faces = [], []
    for column in range(columns):
        t = column / (columns - 1) * 2.0 - 1.0
        taper = math.sin(math.pi * column / (columns - 1)) ** 0.78
        upper_inner = upper.data.vertices[column * rows + 6].co
        lower_inner = lower.data.vertices[column * rows + 6].co
        x = 0.0224 * t
        center_z = (upper_inner.z + lower_inner.z) * 0.5
        half = 0.000005 + 0.000065 * taper
        # Recess the moisture strip behind both lip margins so it cannot project
        # beyond the mouth silhouette in side views.
        y = max(upper_inner.y, lower_inner.y) + 0.00034
        vertices.extend(((x, y, center_z - half), (x, y, center_z + half)))
        if column:
            a = (column - 1) * 2
            faces.append((a, a + 2, a + 3, a + 1))
    mesh = bpy.data.meshes.new("MouthWetLineMeshV50")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(make_material("Aevrynd_MouthWetLine_v50", (0.050, 0.006, 0.008), 0.30, coat=0.045))
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    obj = bpy.data.objects.new("Mouth_WetLine", mesh)
    bpy.context.scene.collection.objects.link(obj)
    skin_to_body(obj, rig, body, "mouth_wet_margin")
    obj["aevrynd_commissure_width_m"] = 0.0448
    return obj


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, location, target, lens=110, width=1000, height=900):
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


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
bpy.context.preferences.filepaths.save_version = 0
bpy.context.scene.frame_set(1)
RENDER_DIR.mkdir(parents=True, exist_ok=True)
body = bpy.data.objects["AevryndFemaleBodyBase"]
rig = bpy.data.objects["AevryndFemaleRig"]
tree = body_tree(body)
materials = (
    bpy.data.materials["Aevrynd_Skin_Clay"],
    make_material("Aevrynd_LipVermilion_v50", (0.30, 0.095, 0.082), 0.51, coat=0.010, subsurface=0.035),
    make_material("Aevrynd_LipInner_v50", (0.17, 0.035, 0.037), 0.43, coat=0.025),
)
upper = rebuild_lip("Lip_Upper", True, body, rig, tree, materials)
lower = rebuild_lip("Lip_Lower", False, body, rig, tree, materials)
wetline = rebuild_wetline(upper, lower, rig, body)
bpy.context.scene["aevrynd_face_revision"] = 50
bpy.context.scene["aevrynd_release_state"] = "AUTHORING"
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
camera = bpy.data.objects["Aevrynd Review Camera"]
render(camera, "female-mouth-close", (0.0, -0.44, 1.535), (0.0, -0.120, 1.534), 122)
render(camera, "female-face-front", (0.0, -0.72, 1.575), (0.0, -0.005, 1.555), 96, 900, 900)
render(camera, "female-face-three-quarter", (0.28, -0.64, 1.58), (0.0, 0.0, 1.55), 96, 900, 900)
render(camera, "female-mouth-side", (0.38, -0.32, 1.54), (0.0, -0.105, 1.535), 118)
print("AEVRYND_LIPS_V50=" + json.dumps({
    "state": "AUTHORING",
    "upper": {"vertices": len(upper.data.vertices), "faces": len(upper.data.polygons)},
    "lower": {"vertices": len(lower.data.vertices), "faces": len(lower.data.polygons)},
    "profile_rows": 7,
    "skin_transition_rows": 2,
    "wetline": {"vertices": len(wetline.data.vertices), "faces": len(wetline.data.polygons)},
}))
