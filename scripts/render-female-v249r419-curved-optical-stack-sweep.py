import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-broad-medial-aperture-r418.blend"
IRIS_TEXTURE = ROOT / "assets-source/aevrynd-character/textures/aevrynd-iris-hazel-v61.png"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-curved-optical-stack-r419.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r419-curved-optical-stack-sweep"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-layered-optical-stack-r420.blend"
BUILD_REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-layered-optical-stack-r420.build-report.json"
COLLISION_AUDIT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-layered-optical-stack-r420.collision-audit.json"


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def principled_material(name, color, roughness, specular=0.22):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    shader = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Specular IOR Level"].default_value = specular
    return material, shader


def sclera_material():
    material, shader = principled_material(
        "Aevrynd_Sclera_WarmLiving_R419", (0.72, 0.61, 0.54, 1.0), 0.34, 0.24
    )
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    texcoord = nodes.new("ShaderNodeTexCoord")
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 9.0
    noise.inputs["Detail"].default_value = 3.2
    noise.inputs["Roughness"].default_value = 0.62
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.23
    ramp.color_ramp.elements[0].color = (0.52, 0.42, 0.38, 1.0)
    ramp.color_ramp.elements[1].position = 0.79
    ramp.color_ramp.elements[1].color = (0.82, 0.73, 0.65, 1.0)
    links.new(texcoord.outputs["Generated"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], shader.inputs["Base Color"])
    shader.inputs["Subsurface Weight"].default_value = 0.018
    shader.inputs["Subsurface Scale"].default_value = 0.0010
    material["aevrynd_layer"] = "eye.sclera"
    material["aevrynd_revision"] = "v249r419-study"
    return material


def iris_material():
    material, shader = principled_material(
        "Aevrynd_Iris_HazelOwned_R419", (0.10, 0.20, 0.07, 1.0), 0.42, 0.12
    )
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    image = bpy.data.images.load(str(IRIS_TEXTURE), check_existing=True)
    image.colorspace_settings.name = "sRGB"
    texcoord = nodes.new("ShaderNodeTexCoord")
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = image
    texture.interpolation = "Linear"
    texture.extension = "CLIP"
    tone = nodes.new("ShaderNodeHueSaturation")
    tone.inputs["Saturation"].default_value = 0.82
    tone.inputs["Value"].default_value = 0.92
    links.new(texcoord.outputs["UV"], texture.inputs["Vector"])
    links.new(texture.outputs["Color"], tone.inputs["Color"])
    links.new(tone.outputs["Color"], shader.inputs["Base Color"])
    material["aevrynd_layer"] = "eye.iris_stroma"
    material["aevrynd_texture_ownership"] = "Aevrynd-generated"
    material["aevrynd_texture_source"] = IRIS_TEXTURE.name
    return material


def cornea_material():
    material, shader = principled_material(
        "Aevrynd_Cornea_Clear_R419", (0.94, 0.98, 1.0, 1.0), 0.055, 0.20
    )
    shader.inputs["IOR"].default_value = 1.376
    shader.inputs["Transmission Weight"].default_value = 1.0
    shader.inputs["Alpha"].default_value = 0.16
    shader.inputs["Coat Weight"].default_value = 0.04
    shader.inputs["Coat Roughness"].default_value = 0.09
    if hasattr(material, "surface_render_method"):
        material.surface_render_method = "DITHERED"
    if hasattr(material, "use_transparency_overlap"):
        material.use_transparency_overlap = False
    material["aevrynd_layer"] = "eye.cornea"
    material["aevrynd_revision"] = "v249r419-study"
    return material


def mesh_object(name, vertices, faces, uvs, material, template, layer):
    mesh = bpy.data.meshes.new(name + "Topology")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.matrix_world = template.matrix_world.copy()
    world = obj.matrix_world.copy()
    obj.parent = template.parent
    obj.parent_type = template.parent_type
    obj.parent_bone = template.parent_bone
    obj.matrix_world = world
    obj.data.materials.append(material)
    obj["aevrynd_layer"] = layer
    obj["aevrynd_binding"] = "rig.head"
    obj["aevrynd_revision"] = "v249r419-study"
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    if uvs:
        uv_layer = mesh.uv_layers.new(name="Aevrynd Iris UV")
        for polygon in mesh.polygons:
            for loop_index in polygon.loop_indices:
                vertex_index = mesh.loops[loop_index].vertex_index
                uv_layer.data[loop_index].uv = uvs[vertex_index]
    return obj


def build_open_sclera(side, template, material, center, radius_xyz, opening_radius):
    vertices = [tuple(vertex.co) for vertex in template.data.vertices]
    faces = []
    removed = 0
    for polygon in template.data.polygons:
        polygon_center = sum((template.data.vertices[index].co for index in polygon.vertices), Vector()) / len(polygon.vertices)
        radial = math.hypot(polygon_center.x - center.x, polygon_center.z - center.z)
        if polygon_center.y < center.y and radial < opening_radius * 1.035:
            removed += 1
            continue
        faces.append(tuple(polygon.vertices))
    opening_angle = math.asin(opening_radius / ((radius_xyz[0] + radius_xyz[2]) * 0.5))
    obj = mesh_object(
        f"AevryndEye_{side}_ScleraOpen_R419", vertices, faces, None, material, template,
        f"eye.{side.lower()}.sclera_open_limbus",
    )
    obj["aevrynd_opening_radius_local_m"] = opening_radius
    obj["aevrynd_removed_front_polygons"] = removed
    return obj, opening_angle


def build_radial_layer(name, template, center, outer_radius, inner_radius, edge_y, center_depth,
                       material, layer, rings=12, segments=128):
    vertices, faces, uvs = [], [], []
    has_center = inner_radius <= 1e-8
    ring_start = 0 if has_center else 1
    if has_center:
        vertices.append((center.x, edge_y + center_depth, center.z))
        uvs.append((0.5, 0.5))
    radii = []
    if not has_center:
        radii.append(inner_radius)
    for ring in range(ring_start, rings + 1):
        t = ring / rings
        radius = outer_radius * t if has_center else inner_radius + (outer_radius - inner_radius) * (ring - 1) / (rings - 1)
        radii.append(radius)
    offsets = []
    for radius in radii:
        t = radius / outer_radius
        y = edge_y + center_depth * (1.0 - t * t)
        offsets.append(len(vertices))
        for segment in range(segments):
            phi = 2.0 * math.pi * segment / segments
            x = center.x + radius * math.cos(phi)
            z = center.z + radius * math.sin(phi)
            vertices.append((x, y, z))
            uvs.append((0.5 + 0.5 * x / outer_radius - 0.5 * center.x / outer_radius,
                        0.5 + 0.5 * z / outer_radius - 0.5 * center.z / outer_radius))
    if has_center:
        first = offsets[0]
        for segment in range(segments):
            faces.append((0, first + segment, first + (segment + 1) % segments))
    for index in range(len(offsets) - 1):
        a, b = offsets[index], offsets[index + 1]
        for segment in range(segments):
            nxt = (segment + 1) % segments
            faces.append((a + segment, b + segment, b + nxt, a + nxt))
    return mesh_object(name, vertices, faces, uvs, material, template, layer)


def build_cornea(side, template, center, opening_radius, edge_y, apex_y, material):
    rings, segments = 18, 128
    vertices = [(center.x, apex_y, center.z)]
    faces = []
    for ring in range(1, rings + 1):
        t = ring / rings
        radius = opening_radius * math.sin(t * math.pi * 0.5)
        y = apex_y + (edge_y - apex_y) * (1.0 - math.cos(t * math.pi * 0.5))
        for segment in range(segments):
            phi = 2.0 * math.pi * segment / segments
            vertices.append((center.x + radius * math.cos(phi), y, center.z + radius * math.sin(phi)))
    for segment in range(segments):
        faces.append((0, 1 + segment, 1 + (segment + 1) % segments))
    for ring in range(1, rings):
        a = 1 + (ring - 1) * segments
        b = 1 + ring * segments
        for segment in range(segments):
            nxt = (segment + 1) % segments
            faces.append((a + segment, b + segment, b + nxt, a + nxt))
    return mesh_object(
        f"AevryndEye_{side}_CorneaConvex_R419", vertices, faces, None, material, template,
        f"eye.{side.lower()}.cornea_convex",
    )


def hide_large_hair():
    hidden = []
    preserve = ("brow", "lash", "lid", "tear", "caruncle", "eye")
    for obj in bpy.data.objects:
        name = obj.name.lower()
        if any(token in name for token in preserve):
            continue
        materials = getattr(obj.data, "materials", ()) if hasattr(obj, "data") else ()
        material_names = " ".join(m.name.lower() for m in materials if m)
        if any(token in name or token in material_names for token in ("hair", "scalp", "groom", "flyaway", "root", "lock", "fiber")):
            if obj.type in {"MESH", "CURVES", "CURVE"}:
                obj.hide_render = True
                hidden.append(obj.name)
    return hidden


def neutral_lights(scene):
    for obj in list(bpy.data.objects):
        if obj.type == "LIGHT":
            bpy.data.objects.remove(obj, do_unlink=True)
    target = (0.0, -0.025, 1.60)
    for name, location, energy, size in (
        ("Aevrynd Neutral Key R419", (-0.42, -0.82, 1.82), 39.0, 0.56),
        ("Aevrynd Neutral Fill R419", (0.48, -0.62, 1.70), 24.0, 0.68),
        ("Aevrynd Neutral Top R419", (0.00, -0.08, 2.28), 22.0, 0.52),
    ):
        data = bpy.data.lights.new(name, "AREA")
        data.energy, data.color, data.shape, data.size = energy, (1.0, 1.0, 1.0), "DISK", size
        obj = bpy.data.objects.new(name, data)
        bpy.context.collection.objects.link(obj)
        obj.location = location
        look_at(obj, target)
    scene.world.use_nodes = True
    background = next((node for node in scene.world.node_tree.nodes if node.type == "BACKGROUND"), None)
    if background is None:
        nodes = scene.world.node_tree.nodes
        links = scene.world.node_tree.links
        background = nodes.new("ShaderNodeBackground")
        output = next((node for node in nodes if node.type == "OUTPUT_WORLD"), None) or nodes.new("ShaderNodeOutputWorld")
        links.new(background.outputs["Background"], output.inputs["Surface"])
    background.inputs["Color"].default_value = (0.018, 0.018, 0.018, 1.0)
    background.inputs["Strength"].default_value = 0.35


def render(camera, label, location, target, lens, size=(1000, 1000)):
    scene = bpy.context.scene
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.filepath = str(RENDER_DIR / f"{label}.png")
    bpy.ops.render.render(write_still=True)


def world_bvh(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, faces, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
original_visibility = {obj.name: obj.hide_render for obj in bpy.data.objects}
original_lights = [(obj.name, obj.data.copy(), obj.matrix_world.copy()) for obj in bpy.data.objects if obj.type == "LIGHT"]
original_background = next((node for node in scene.world.node_tree.nodes if node.type == "BACKGROUND"), None) if scene.world and scene.world.use_nodes else None
original_world = {
    "color": tuple(original_background.inputs["Color"].default_value) if original_background else None,
    "strength": original_background.inputs["Strength"].default_value if original_background else None,
}
original_render = {
    "engine": scene.render.engine, "resolution_x": scene.render.resolution_x, "resolution_y": scene.render.resolution_y,
    "resolution_percentage": scene.render.resolution_percentage, "view_transform": scene.view_settings.view_transform,
    "look": scene.view_settings.look, "exposure": scene.view_settings.exposure,
}
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Base Contrast"
scene.view_settings.exposure = 0.0
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
original_camera_matrix = camera.matrix_world.copy()
original_camera_lens = camera.data.lens
scene.camera = camera

sclera_mat = sclera_material()
iris_mat = iris_material()
pupil_mat, _ = principled_material("Aevrynd_Pupil_Depth_R419", (0.0004, 0.0003, 0.0002, 1.0), 0.31, 0.08)
limbal_mat, _ = principled_material("Aevrynd_Limbal_Soft_R419", (0.006, 0.013, 0.006, 1.0), 0.44, 0.10)
cornea_mat = cornea_material()

metrics = {}
corneas = {}
for side in ("L", "R"):
    old = bpy.data.objects[f"AevryndEye_{side}_Sclera_R249"]
    points = [v.co.copy() for v in old.data.vertices]
    mins = [min(p[i] for p in points) for i in range(3)]
    maxs = [max(p[i] for p in points) for i in range(3)]
    center = Vector(((mins[0] + maxs[0]) * 0.5, (mins[1] + maxs[1]) * 0.5, (mins[2] + maxs[2]) * 0.5))
    radii = ((maxs[0] - mins[0]) * 0.5, (maxs[1] - mins[1]) * 0.5, (maxs[2] - mins[2]) * 0.5)
    opening = 0.00630
    sclera, angle = build_open_sclera(side, old, sclera_mat, center, radii, opening)
    edge_y = center.y - radii[1] * math.cos(angle)
    limbal = build_radial_layer(
        f"AevryndEye_{side}_LimbalAnnulus_R419", old, center, opening, 0.00558,
        edge_y - 0.00002, 0.00010, limbal_mat, f"eye.{side.lower()}.limbal_annulus", rings=5,
    )
    iris = build_radial_layer(
        f"AevryndEye_{side}_IrisConcave_R419", old, center, 0.00578, 0.00178,
        edge_y + 0.00005, 0.00028, iris_mat, f"eye.{side.lower()}.iris_concave", rings=15,
    )
    pupil = build_radial_layer(
        f"AevryndEye_{side}_PupilRecessed_R419", old, center, 0.00186, 0.0,
        edge_y + 0.00031, 0.00004, pupil_mat, f"eye.{side.lower()}.pupil_recessed", rings=5,
    )
    apex_y = center.y - radii[1] - 0.00055
    cornea = build_cornea(side, old, center, opening, edge_y - 0.00005, apex_y, cornea_mat)
    corneas[side] = (cornea, center, edge_y, radii[1])
    bpy.data.objects.remove(old, do_unlink=True)
    metrics[side] = {
        "centerLocalM": list(center), "radiusLocalM": list(radii), "openingRadiusLocalM": opening,
        "irisRadiusLocalM": 0.00578, "pupilRadiusLocalM": 0.00186,
        "layers": [sclera.name, limbal.name, iris.name, pupil.name, cornea.name],
    }

hidden_hair = hide_large_hair()
neutral_lights(scene)
views = (
    ("face", (0.0, -0.68, 1.605), (0.0, -0.035, 1.606), 92, (1000, 1000)),
    ("eyes", (0.0, -0.46, 1.615), (0.0, -0.035, 1.610), 105, (1200, 760)),
    ("three-quarter", (0.44, -0.63, 1.62), (0.0, -0.02, 1.595), 88, (1000, 1000)),
)
variants = (("a-low", 0.00035), ("b-balanced", 0.00055), ("c-deep", 0.00075))
for label, bulge in variants:
    for side, (cornea, center, edge_y, ry) in corneas.items():
        apex = center.y - ry - bulge
        rings, segments = 18, 128
        cornea.data.vertices[0].co.y = apex
        for ring in range(1, rings + 1):
            t = ring / rings
            y = apex + ((edge_y - 0.00005) - apex) * (1.0 - math.cos(t * math.pi * 0.5))
            start = 1 + (ring - 1) * segments
            for segment in range(segments):
                cornea.data.vertices[start + segment].co.y = y
        cornea.data.update()
        cornea["aevrynd_cornea_bulge_local_m"] = bulge
    for view_name, location, target, lens, size in views:
        render(camera, f"{label}-{view_name}", location, target, lens, size)

report = {
    "source": str(SOURCE), "renderDirectory": str(RENDER_DIR), "ownedIrisTexture": str(IRIS_TEXTURE),
    "geometry": metrics, "variants": {label: {"corneaBulgeLocalM": bulge} for label, bulge in variants},
    "fixedConditions": {"neutralWhiteLights": True, "AgX": "Base Contrast", "exposureEV": 0.0, "largeHairHidden": True},
    "status": "VISUAL_REVIEW_PENDING", "promoted": False,
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")

# Promote the balanced optical geometry to a technical candidate only after the visual sweep.
selected_bulge = 0.00055
selected_recess = 0.00100
for side, (cornea, center, edge_y, ry) in corneas.items():
    apex = center.y - ry - selected_bulge
    rings, segments = 18, 128
    cornea.data.vertices[0].co.y = apex
    for ring in range(1, rings + 1):
        t = ring / rings
        y = apex + ((edge_y - 0.00005) - apex) * (1.0 - math.cos(t * math.pi * 0.5))
        start = 1 + (ring - 1) * segments
        for segment in range(segments):
            cornea.data.vertices[start + segment].co.y = y
    cornea.data.update()
    cornea["aevrynd_cornea_bulge_local_m"] = selected_bulge
    for layer_name in metrics[side]["layers"]:
        layer = bpy.data.objects[layer_name]
        if "ScleraOpen" in layer_name:
            layer["aevrynd_additional_optical_recess_local_m"] = 0.0
            continue
        for vertex in layer.data.vertices:
            vertex.co.y += selected_recess
        layer.data.update()
        layer["aevrynd_additional_optical_recess_local_m"] = selected_recess

for obj in bpy.data.objects:
    if obj.get("aevrynd_revision") == "v249r419-study":
        obj["aevrynd_revision"] = "v249r420-layered-optical-stack"
for material in bpy.data.materials:
    if material.get("aevrynd_revision") == "v249r419-study":
        material["aevrynd_revision"] = "v249r420-layered-optical-stack"

for view_name, location, target, lens, size in views:
    render(camera, f"r420-selected-{view_name}", location, target, lens, size)

collision = {"frames": {}, "violations": []}
body = bpy.data.objects["AevryndFemaleBody_CC0_R249"]
for frame in (1, 20):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    body_tree = world_bvh(body, depsgraph)
    collision["frames"][str(frame)] = {}
    for side in ("L", "R"):
        layer_names = metrics[side]["layers"]
        layer_trees = {name: world_bvh(bpy.data.objects[name], depsgraph) for name in layer_names}
        caruncle = bpy.data.objects[f"AevryndEye_{side}_Caruncle_R258"]
        caruncle_tree = world_bvh(caruncle, depsgraph)
        result = {"bodyVs" + name.split("_")[-2]: len(body_tree.overlap(tree)) for name, tree in layer_trees.items()}
        result["caruncleVsCornea"] = len(caruncle_tree.overlap(layer_trees[f"AevryndEye_{side}_CorneaConvex_R419"]))
        result["scleraVsIris"] = len(layer_trees[f"AevryndEye_{side}_ScleraOpen_R419"].overlap(layer_trees[f"AevryndEye_{side}_IrisConcave_R419"]))
        result["irisVsPupil"] = len(layer_trees[f"AevryndEye_{side}_IrisConcave_R419"].overlap(layer_trees[f"AevryndEye_{side}_PupilRecessed_R419"]))
        result["corneaVsIris"] = len(layer_trees[f"AevryndEye_{side}_CorneaConvex_R419"].overlap(layer_trees[f"AevryndEye_{side}_IrisConcave_R419"]))
        collision["frames"][str(frame)][side] = result
        for check, count in result.items():
            if count:
                collision["violations"].append({"frame": frame, "side": side, "check": check, "triangleOverlaps": count})
collision["status"] = "PASS" if not collision["violations"] else "FAIL"
COLLISION_AUDIT.write_text(json.dumps(collision, indent=2), encoding="utf-8")

# Freeze selected layer and material identifiers at the promoted revision.
for side in ("L", "R"):
    promoted_names = []
    for old_name in metrics[side]["layers"]:
        obj = bpy.data.objects[old_name]
        new_name = old_name.replace("_R419", "_R420")
        obj.name = new_name
        obj.data.name = obj.data.name.replace("_R419", "_R420")
        promoted_names.append(new_name)
    metrics[side]["layers"] = promoted_names
for material in bpy.data.materials:
    if material.name.endswith("_R419"):
        material.name = material.name[:-5] + "_R420"

# Restore the authoring scene; neutral lighting and hidden hair belong only to the review renders.
for obj in bpy.data.objects:
    if obj.name in original_visibility:
        obj.hide_render = original_visibility[obj.name]
for obj in list(bpy.data.objects):
    if obj.type == "LIGHT":
        bpy.data.objects.remove(obj, do_unlink=True)
for name, light_data, matrix in original_lights:
    light_obj = bpy.data.objects.new(name, light_data)
    bpy.context.scene.collection.objects.link(light_obj)
    light_obj.matrix_world = matrix
camera.matrix_world = original_camera_matrix
camera.data.lens = original_camera_lens
scene.render.engine = original_render["engine"]
scene.render.resolution_x = original_render["resolution_x"]
scene.render.resolution_y = original_render["resolution_y"]
scene.render.resolution_percentage = original_render["resolution_percentage"]
scene.view_settings.view_transform = original_render["view_transform"]
scene.view_settings.look = original_render["look"]
scene.view_settings.exposure = original_render["exposure"]
restored_background = next((node for node in scene.world.node_tree.nodes if node.type == "BACKGROUND"), None) if scene.world and scene.world.use_nodes else None
if restored_background and original_world["color"] is not None:
    restored_background.inputs["Color"].default_value = original_world["color"]
    restored_background.inputs["Strength"].default_value = original_world["strength"]

scene.frame_set(1)
scene["aevrynd_mainline_revision"] = "v249r420-layered-optical-stack"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "TECHNICAL_PASS_VISUAL_REVIEW_PENDING" if collision["status"] == "PASS" else "COLLISION_FAIL"
build_report = {
    "source": str(SOURCE), "output": str(OUTPUT), "selectedStudy": "r419-b-balanced",
    "additionalOpticalRecessLocalM": selected_recess,
    "ownedIrisTexture": str(IRIS_TEXTURE), "createdLayers": metrics,
    "collisionAudit": str(COLLISION_AUDIT), "collisionStatus": collision["status"],
    "websitePromoted": False,
    "status": "TECHNICAL_PASS_VISUAL_REVIEW_PENDING" if collision["status"] == "PASS" else "COLLISION_FAIL",
}
BUILD_REPORT.write_text(json.dumps(build_report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_R419_OPTICAL_SWEEP=" + json.dumps(report, sort_keys=True))
print("AEVRYND_R420_OPTICAL_BUILD=" + json.dumps(build_report, sort_keys=True))
if collision["status"] != "PASS":
    raise SystemExit(2)
