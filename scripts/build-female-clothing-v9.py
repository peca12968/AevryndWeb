import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v8.blend"
OUTPUT = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v9.blend"
BUILD = ROOT / ".character-build" / "aevrynd-female-authoring-v9.glb"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "clothing-v9"


def cloth_material(name, color, roughness):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Roughness"].default_value = roughness
    if shader.inputs.get("Specular IOR Level"):
        shader.inputs["Specular IOR Level"].default_value = 0.24
    noise = material.node_tree.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 210.0
    noise.inputs["Detail"].default_value = 1.5
    bump = material.node_tree.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.08
    bump.inputs["Distance"].default_value = 0.00018
    material.node_tree.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    material.node_tree.links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    material["aevrynd_requires_runtime_bake"] = True
    return material


def repair_body_normals(body):
    bpy.ops.object.select_all(action="DESELECT")
    body.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    body["aevrynd_normal_revision"] = 9


def top_region(center):
    return 1.135 <= center.z <= 1.275 and abs(center.x) <= 0.145


def shorts_region(center):
    # Keep the pelvis shell continuous through the crotch.  The earlier
    # curved threshold removed the central body faces and produced two leg
    # panels rather than a wearable pair of shorts.
    return 0.735 <= center.z <= 1.005 and abs(center.x) <= 0.185


def make_garment(body, rig, name, role, predicate, material, clearance=0.0070, thickness=0.0012):
    source = body.data
    selected = [
        polygon for polygon in source.polygons
        if all(predicate(source.vertices[index].co) for index in polygon.vertices)
    ]
    used = sorted({index for polygon in selected for index in polygon.vertices})
    remap = {source_index: target_index for target_index, source_index in enumerate(used)}
    vertices = [source.vertices[index].co + source.vertices[index].normal * clearance for index in used]
    faces = [tuple(remap[index] for index in polygon.vertices) for polygon in selected]

    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(vertices, [], faces)
    if source.uv_layers.active:
        target_uv = mesh.uv_layers.new(name="UVMap")
        source_uv = source.uv_layers.active.data
        for target_polygon, source_polygon in zip(mesh.polygons, selected):
            for target_loop, source_loop in zip(target_polygon.loop_indices, source_polygon.loop_indices):
                target_uv.data[target_loop].uv = source_uv[source_loop].uv

    garment = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(garment)
    garment.matrix_world = body.matrix_world.copy()
    garment.data.materials.append(material)
    for polygon in garment.data.polygons:
        polygon.use_smooth = True

    group_map = {}
    for source_group in body.vertex_groups:
        group_map[source_group.index] = garment.vertex_groups.new(name=source_group.name)
    for target_index, source_index in enumerate(used):
        for assignment in source.vertices[source_index].groups:
            if assignment.weight > 1e-8:
                group_map[assignment.group].add([target_index], assignment.weight, "REPLACE")

    source_vertices = len(used)
    source_faces = len(selected)
    subdivision = garment.modifiers.new("Aevrynd Cloth Subdivision", "SUBSURF")
    subdivision.levels = 1
    subdivision.render_levels = 1
    solidify = garment.modifiers.new("Aevrynd Cloth Thickness", "SOLIDIFY")
    solidify.thickness = thickness
    solidify.offset = 0.0
    solidify.use_even_offset = True
    bpy.ops.object.select_all(action="DESELECT")
    garment.select_set(True)
    bpy.context.view_layer.objects.active = garment
    bpy.ops.object.modifier_apply(modifier=subdivision.name)
    bpy.ops.object.modifier_apply(modifier=solidify.name)
    armature = garment.modifiers.new("Aevrynd Cloth Deform", "ARMATURE")
    armature.object = rig
    world = garment.matrix_world.copy()
    garment.parent = rig
    garment.matrix_world = world
    garment["aevrynd_role"] = role
    garment["aevrynd_source"] = "Aevrynd derived from CC0 female base topology"
    garment["aevrynd_clothing_revision"] = 9
    garment["aevrynd_body_clearance_m"] = clearance - thickness * 0.5
    garment["aevrynd_thickness_m"] = thickness
    garment["aevrynd_source_vertices"] = source_vertices
    garment["aevrynd_source_faces"] = source_faces
    return garment


def limit_and_normalize_weights(garment, maximum=4):
    trimmed = 0
    for vertex in garment.data.vertices:
        influences = sorted(
            ((entry.group, entry.weight) for entry in vertex.groups if entry.weight > 1e-8),
            key=lambda value: value[1],
            reverse=True,
        )
        kept = influences[:maximum]
        for group_index, _ in influences[maximum:]:
            garment.vertex_groups[group_index].remove([vertex.index])
            trimmed += 1
        total = sum(weight for _, weight in kept)
        if total > 0:
            for group_index, weight in kept:
                garment.vertex_groups[group_index].add([vertex.index], weight / total, "REPLACE")
    garment["aevrynd_weight_limit"] = maximum
    garment["aevrynd_trimmed_weight_entries"] = trimmed
    return trimmed


def weight_audit(garment):
    unweighted = 0
    maximum = 0
    for vertex in garment.data.vertices:
        influences = [entry for entry in vertex.groups if entry.weight > 1e-5]
        maximum = max(maximum, len(influences))
        if not influences:
            unweighted += 1
    return unweighted, maximum


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, frame, location, target):
    scene = bpy.context.scene
    scene.frame_set(frame)
    camera.data.lens = 58
    camera.location = location
    look_at(camera, target)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 700
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    for obj in bpy.data.objects:
        if obj.get("aevrynd_role") == "cornea":
            obj.hide_render = True
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
bpy.context.preferences.filepaths.save_version = 0
bpy.context.scene.frame_set(1)
RENDER_DIR.mkdir(parents=True, exist_ok=True)
BUILD.parent.mkdir(parents=True, exist_ok=True)
body = bpy.data.objects["AevryndFemaleBodyBase"]
rig = bpy.data.objects["AevryndFemaleRig"]
repair_body_normals(body)
top = make_garment(
    body, rig, "Clothing_InnerTop", "inner_clothing_top", top_region,
    cloth_material("Aevrynd_Cloth_DeepBlue", (0.018, 0.045, 0.095, 1.0), 0.72),
)
shorts = make_garment(
    body, rig, "Clothing_InnerShorts", "inner_clothing_bottom", shorts_region,
    cloth_material("Aevrynd_Cloth_Graphite", (0.028, 0.032, 0.040, 1.0), 0.76),
    clearance=0.0200,
)
garments = [top, shorts]
trimmed = {garment.name: limit_and_normalize_weights(garment) for garment in garments}
audits = {garment.name: weight_audit(garment) for garment in garments}
for garment in garments:
    garment["aevrynd_unweighted_vertices"] = audits[garment.name][0]
    garment["aevrynd_maximum_influences"] = audits[garment.name][1]

bpy.context.scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
camera = bpy.data.objects["Aevrynd Review Camera"]
render(camera, "female-clothing-neutral", 1, (0, -3.05, 0.92), (0, 0, 0.90))
render(camera, "female-clothing-pose-20", 20, (0, -3.05, 0.98), (0, 0, 0.96))
render(camera, "female-clothing-back", 1, (0, 3.05, 0.94), (0, 0, 0.92))

body_multires = next(modifier for modifier in body.modifiers if modifier.type == "MULTIRES")
old_multires = (body_multires.levels, body_multires.sculpt_levels, body_multires.render_levels)
body_multires.levels = body_multires.sculpt_levels = body_multires.render_levels = 0
bpy.context.scene.frame_set(1)
bpy.ops.object.select_all(action="DESELECT")
for obj in [rig] + [value for value in bpy.data.objects if value.type == "MESH"]:
    obj.hide_render = False
    obj.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(
    filepath=str(BUILD), export_format="GLB", use_selection=True,
    export_apply=True, export_yup=True, export_extras=True,
    export_animations=True, export_frame_range=True,
)
body_multires.levels, body_multires.sculpt_levels, body_multires.render_levels = old_multires

print(
    "AEVRYND_CLOTHING_V9_REPORT="
    + json.dumps({
        "state": "AUTHORING",
        "garments": {
            garment.name: {
                "role": garment["aevrynd_role"],
                "vertices": len(garment.data.vertices),
                "faces": len(garment.data.polygons),
                "unweighted": audits[garment.name][0],
                "maximum_influences": audits[garment.name][1],
                "trimmed_weight_entries": trimmed[garment.name],
                "minimum_authored_clearance_m": garment["aevrynd_body_clearance_m"],
            }
            for garment in garments
        },
        "runtime_glb": str(BUILD),
    })
)
