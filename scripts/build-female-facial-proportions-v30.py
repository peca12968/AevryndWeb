import json
import math
from pathlib import Path

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v25.blend"
OUTPUT = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v30.blend"
BUILD = ROOT / ".character-build" / "aevrynd-female-authoring-v30.glb"
LOD1 = ROOT / ".character-build" / "aevrynd-female-authoring-v30-lod1.glb"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "facial-proportions-v30"


def gaussian(value, center, spread):
    return math.exp(-0.5 * ((value - center) / spread) ** 2)


def clamp01(value):
    return max(0.0, min(1.0, value))


def segment_distance(px, pz, ax, az, bx, bz):
    abx, abz = bx - ax, bz - az
    length_squared = abx * abx + abz * abz
    t = clamp01(((px - ax) * abx + (pz - az) * abz) / length_squared)
    qx, qz = ax + abx * t, az + abz * t
    return math.hypot(px - qx, pz - qz)


def sculpt_transitions(body):
    inverse = body.matrix_world.inverted()
    changed = 0
    maximum = 0.0
    components = {name: 0.0 for name in (
        "brow_ridge", "lower_lid_support", "tear_trough", "alar_groove",
        "alar_taper", "philtrum_groove", "philtrum_columns",
        "nasolabial_transition", "oral_commissure", "mental_sulcus", "chin_pad",
        "upper_lid", "lower_lid", "columella", "nose_base",
    )}
    for vertex in body.data.vertices:
        point = body.matrix_world @ vertex.co
        x_abs = abs(point.x)
        if point.y > -0.064 or not (1.468 <= point.z <= 1.646) or x_abs > 0.096:
            continue

        front = clamp01((-point.y - 0.064) / 0.068)
        side = 1.0 if point.x >= 0.0 else -1.0

        # The orbit needs a shallow bony rim, lid support and a soft trough below it.
        brow_ridge = gaussian(x_abs, 0.036, 0.026) * gaussian(point.z, 1.632, 0.010) * front
        lower_lid = gaussian(x_abs, 0.035, 0.020) * gaussian(point.z, 1.594, 0.0060) * front
        tear_trough = gaussian(x_abs, 0.040, 0.023) * gaussian(point.z, 1.579, 0.0080) * front
        outer_orbit = gaussian(x_abs, 0.058, 0.016) * gaussian(point.z, 1.602, 0.021) * front

        # Model the nose-to-cheek transition. The groove is a recessed crescent,
        # while the ala itself is only narrowed enough to reduce the round plug shape.
        alar_groove = gaussian(x_abs, 0.028, 0.0055) * gaussian(point.z, 1.555, 0.012) * front
        ala = gaussian(x_abs, 0.021, 0.010) * gaussian(point.z, 1.558, 0.012) * front

        # The philtrum is a central depression bounded by two low columns. These
        # amplitudes stay below a millimetre so the lip attachments remain dominant.
        philtrum_groove = gaussian(point.x, 0.0, 0.0048) * gaussian(point.z, 1.548, 0.012) * front
        philtrum_columns = gaussian(x_abs, 0.0068, 0.0036) * gaussian(point.z, 1.548, 0.012) * front
        fold_distance = segment_distance(x_abs, point.z, 0.021, 1.557, 0.040, 1.524)
        nasolabial = math.exp(-0.5 * (fold_distance / 0.0048) ** 2) * front
        nasolabial *= clamp01((x_abs - 0.014) / 0.015)
        commissure = gaussian(x_abs, 0.043, 0.0085) * gaussian(point.z, 1.523, 0.010) * front

        mental = gaussian(x_abs, 0.018, 0.025) * gaussian(point.z, 1.506, 0.0065) * front
        chin = gaussian(x_abs, 0.017, 0.026) * gaussian(point.z, 1.486, 0.015) * front

        eye_center_x = 0.0345 if point.x >= 0.0 else -0.0345
        eye_dx = point.x - eye_center_x
        eye_horizontal = gaussian(eye_dx, 0.0, 0.020) * front
        upper_lid = gaussian(point.z, 1.6150, 0.0065) * eye_horizontal
        lower_lid_close = gaussian(point.z, 1.6010, 0.0055) * eye_horizontal
        inner_sign = -1.0 if point.x >= 0.0 else 1.0
        inner_canthus = gaussian(eye_dx, inner_sign * 0.017, 0.0050) * gaussian(point.z, 1.607, 0.006) * front

        columella = gaussian(point.x, 0.0, 0.0065) * gaussian(point.z, 1.553, 0.010) * front
        nose_base = gaussian(x_abs, 0.018, 0.014) * gaussian(point.z, 1.551, 0.010) * front

        y_delta = (
            -0.00055 * brow_ridge
            -0.00042 * lower_lid
            +0.00055 * tear_trough
            +0.00024 * outer_orbit
            +0.00058 * alar_groove
            +0.00048 * philtrum_groove
            -0.00030 * philtrum_columns
            +0.00040 * nasolabial
            +0.00052 * commissure
            +0.00058 * mental
            -0.00046 * chin
            -0.00020 * columella
        )
        x_delta = side * (-0.00062 * ala + 0.00015 * outer_orbit)
        z_delta = -0.00105 * upper_lid + 0.00072 * lower_lid_close
        z_delta += -0.00135 * columella - 0.00045 * nose_base + 0.00020 * inner_canthus

        # Break perfect bilateral symmetry without changing the silhouette.
        asymmetry = gaussian(x_abs, 0.052, 0.030) * gaussian(point.z, 1.557, 0.055) * front
        y_delta += (-0.00010 if point.x >= 0.0 else 0.00006) * asymmetry

        target = point + Vector((x_delta, y_delta, z_delta))
        delta = (target - point).length
        if delta <= 1e-7:
            continue
        vertex.co = inverse @ target
        changed += 1
        maximum = max(maximum, delta)
        values = {
            "brow_ridge": 0.00055 * brow_ridge,
            "lower_lid_support": 0.00042 * lower_lid,
            "tear_trough": 0.00055 * tear_trough,
            "alar_groove": 0.00058 * alar_groove,
            "alar_taper": 0.00062 * ala,
            "philtrum_groove": 0.00048 * philtrum_groove,
            "philtrum_columns": 0.00030 * philtrum_columns,
            "nasolabial_transition": 0.00040 * nasolabial,
            "oral_commissure": 0.00052 * commissure,
            "mental_sulcus": 0.00058 * mental,
            "chin_pad": 0.00046 * chin,
            "upper_lid": 0.00105 * upper_lid,
            "lower_lid": 0.00072 * lower_lid_close,
            "columella": 0.00135 * columella,
            "nose_base": 0.00045 * nose_base,
        }
        for name, value in values.items():
            components[name] = max(components[name], value)

    body.data.update()
    body["aevrynd_face_revision"] = 30
    body["aevrynd_facial_transition_vertices"] = changed
    body["aevrynd_facial_transition_max_delta_m"] = maximum
    return changed, maximum, components


def evaluated_surface(body):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(poly.vertices) for poly in mesh.polygons]
    tree = BVHTree.FromPolygons(points, faces, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


def front_point(tree, x, z, clearance):
    location, normal, _, _ = tree.ray_cast(Vector((x, -0.36, z)), Vector((0.0, 1.0, 0.0)), 0.7)
    if location is None:
        raise RuntimeError(f"face ray missed at x={x:.5f}, z={z:.5f}")
    if normal.y > 0.0:
        normal.negate()
    return location + normal.normalized() * clearance


def parent_to_head(obj, rig):
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = world


def rebuild_upper_folds(body, rig):
    tree = evaluated_surface(body)
    material = bpy.data.materials.get("Aevrynd_EyelidFold")
    shader = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    shader.inputs["Base Color"].default_value = (0.47, 0.22, 0.16, 1.0)
    shader.inputs["Roughness"].default_value = 0.54
    reports = {}
    for side, center_x in (("L", 0.0345), ("R", -0.0345)):
        name = f"Eye_{side}_UpperFold"
        old = bpy.data.objects.get(name)
        if old:
            bpy.data.objects.remove(old, do_unlink=True)
        columns = 37
        vertices = []
        faces = []
        for index in range(columns):
            t = index / (columns - 1) * 2.0 - 1.0
            x = center_x + t * 0.0178
            arc = math.sqrt(max(0.0, 1.0 - t * t))
            asymmetry = 0.00022 * t * (1.0 if side == "L" else -0.55)
            center_z = 1.6110 + 0.0044 * arc + asymmetry
            taper = math.sin(math.pi * index / (columns - 1)) ** 0.72
            half_width = 0.000035 + 0.000145 * taper
            vertices.append(front_point(tree, x, center_z - half_width, 0.00013))
            vertices.append(front_point(tree, x, center_z + half_width, 0.00013))
            if index:
                a = (index - 1) * 2
                faces.append((a, a + 1, a + 3, a + 2))
        mesh = bpy.data.meshes.new(name + "Mesh")
        mesh.from_pydata(vertices, [], faces)
        mesh.materials.append(material)
        for polygon in mesh.polygons:
            polygon.use_smooth = True
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(obj)
        obj["aevrynd_role"] = "upper_eyelid_fold"
        obj["aevrynd_face_revision"] = 30
        obj["aevrynd_surface_offset_m"] = 0.00013
        parent_to_head(obj, rig)
        reports[name] = {"vertices": len(vertices), "faces": len(faces)}
    return reports


def enforce_clearance(body, names, clearance=0.00024):
    tree = evaluated_surface(body)
    reports = {}
    for name in names:
        obj = bpy.data.objects[name]
        inverse = obj.matrix_world.inverted()
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
            target = location + normal.normalized() * clearance
            delta = (target - point).length
            vertex.co = inverse @ target
            adjusted += 1
            maximum = max(maximum, delta)
        obj.data.update()
        reports[name] = {"adjusted_vertices": adjusted, "maximum_delta_m": maximum}
    return reports


def rebuild_lips_on_face(body):
    tree = evaluated_surface(body)
    reports = {}
    for name, upper in (("Lip_Upper", True), ("Lip_Lower", False)):
        obj = bpy.data.objects[name]
        inverse = obj.matrix_world.inverted()
        columns, rows = 49, 5
        if len(obj.data.vertices) != columns * rows:
            raise RuntimeError(f"{name} topology no longer matches the authored lip grid")
        maximum = 0.0
        for column in range(columns):
            t = column / (columns - 1) * 2.0 - 1.0
            x = t * 0.0277
            envelope = max(0.0, 1.0 - abs(t) ** 1.62)
            crease = 1.5348 + 0.00022 * math.cos(t * math.pi)
            if upper:
                cupid = 0.00102 * math.exp(-((abs(t) - 0.34) / 0.18) ** 2)
                notch = 0.00068 * math.exp(-(t / 0.14) ** 2)
                outer = crease + 0.00445 * envelope + cupid - notch
                inner = crease + 0.00020 * envelope
                peak = 0.00126
            else:
                outer = crease - 0.00555 * envelope - 0.00056 * math.exp(-(t / 0.34) ** 2)
                inner = crease - 0.00020 * envelope
                peak = 0.00152
            for row in range(rows):
                index = column * rows + row
                old = obj.matrix_world @ obj.data.vertices[index].co
                u = row / (rows - 1)
                z = inner + (outer - inner) * u
                profile = math.sin(math.pi * u) ** 0.82
                center = 0.72 + 0.28 * gaussian(t, 0.0, 0.40)
                clearance = 0.00027 + peak * profile * envelope * center
                target = front_point(tree, x, z, clearance)
                obj.data.vertices[index].co = inverse @ target
                maximum = max(maximum, (target - old).length)
        obj.data.update()
        obj["aevrynd_face_revision"] = 30
        obj["aevrynd_surface_clearance_min_m"] = 0.00027
        obj["aevrynd_surface_clearance_peak_m"] = 0.00027 + peak
        obj["aevrynd_dynamic_clearance_m"] = 0.0
        reports[name] = {"vertices_rebuilt": columns * rows, "maximum_delta_m": maximum}

        material = obj.data.materials[0]
        shader = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
        shader.inputs["Roughness"].default_value = 0.56
        if shader.inputs.get("Coat Weight"):
            shader.inputs["Coat Weight"].default_value = 0.018

    wet = bpy.data.objects["Mouth_WetLine"]
    inverse = wet.matrix_world.inverted()
    columns = 65
    if len(wet.data.vertices) != columns * 2:
        raise RuntimeError("Mouth_WetLine topology no longer matches the authored grid")
    maximum = 0.0
    for column in range(columns):
        t = column / (columns - 1) * 2.0 - 1.0
        x = t * 0.0271
        envelope = max(0.0, 1.0 - abs(t) ** 1.62)
        crease = 1.5348 + 0.00022 * math.cos(t * math.pi)
        half = 0.00018 * envelope + 0.000018
        for row, z in enumerate((crease - half, crease + half)):
            index = column * 2 + row
            old = wet.matrix_world @ wet.data.vertices[index].co
            target = front_point(tree, x, z, 0.00040)
            wet.data.vertices[index].co = inverse @ target
            maximum = max(maximum, (target - old).length)
    wet.data.update()
    wet["aevrynd_face_revision"] = 30
    wet["aevrynd_dynamic_clearance_m"] = 0.0
    reports["Mouth_WetLine"] = {"vertices_rebuilt": columns * 2, "maximum_delta_m": maximum}
    wet_shader = next(node for node in wet.data.materials[0].node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    wet_shader.inputs["Roughness"].default_value = 0.34
    if wet_shader.inputs.get("Coat Weight"):
        wet_shader.inputs["Coat Weight"].default_value = 0.12
    return reports


def apply_thin_layer_safety_offsets():
    offsets = {
        "Eye_L_IrisFibers": 0.00072,
        "Eye_R_IrisFibers": 0.00072,
        "Lip_Upper": 0.00135,
        "Mouth_WetLine": 0.00092,
    }
    for name, distance in offsets.items():
        obj = bpy.data.objects[name]
        inverse = obj.matrix_world.inverted()
        for vertex in obj.data.vertices:
            point = obj.matrix_world @ vertex.co
            point.y -= distance
            vertex.co = inverse @ point
        obj.data.update()
        obj["aevrynd_safety_offset_m"] = distance
    return offsets


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, location, target, lens=96):
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1000
    scene.render.resolution_y = 1000
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
changed, maximum, components = sculpt_transitions(body)
folds = rebuild_upper_folds(body, rig)
lip_blending = rebuild_lips_on_face(body)
clearance = enforce_clearance(body, (
    "Eye_L_UpperFold", "Eye_R_UpperFold",
    "Eye_L_UpperLashes", "Eye_R_UpperLashes",
    "Eye_L_LowerLashes", "Eye_R_LowerLashes",
    "Eye_L_TearMeniscus", "Eye_R_TearMeniscus",
    "Lip_Upper", "Lip_Lower", "Mouth_WetLine",
))
safety_offsets = apply_thin_layer_safety_offsets()
bpy.context.scene["aevrynd_face_revision"] = 30
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

camera = bpy.data.objects["Aevrynd Review Camera"]
render(camera, "female-face-front", (0.0, -0.67, 1.565), (0.0, -0.004, 1.555), 92)
render(camera, "female-face-three-quarter", (0.25, -0.60, 1.57), (0.0, 0.0, 1.55), 92)
render(camera, "female-face-left", (-0.62, -0.05, 1.57), (0.0, 0.0, 1.545), 92)
render(camera, "female-face-right", (0.62, -0.05, 1.57), (0.0, 0.0, 1.545), 92)
render(camera, "female-face-close", (0.0, -0.49, 1.57), (0.0, -0.072, 1.56), 108)

multires = next(modifier for modifier in body.modifiers if modifier.type == "MULTIRES")
old_levels = (multires.levels, multires.sculpt_levels, multires.render_levels)
multires.levels = multires.sculpt_levels = multires.render_levels = 0
export_runtime(BUILD, rig)
export_runtime(LOD1, rig, {"HairMain", "HairFlyaways"})
multires.levels, multires.sculpt_levels, multires.render_levels = old_levels

print("AEVRYND_FACIAL_PROPORTIONS_V30_REPORT=" + json.dumps({
    "state": "AUTHORING",
    "changed_vertices": changed,
    "maximum_delta_m": maximum,
    "component_maxima_m": components,
    "folds": folds,
    "lip_blending": lip_blending,
    "clearance": clearance,
    "safety_offsets_m": safety_offsets,
    "runtime_glb": str(BUILD),
    "lod1_glb": str(LOD1),
}))
