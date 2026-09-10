import json
import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-converged-upper-lid-r210.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-local-mouth-retopology-r226.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-local-mouth-retopology-r226.build-report.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r226-local-mouth-retopology"
BODY = "AevryndFemaleBodyBaseV118"
TARGET_COLOR = (0.42, 0.105, 0.085, 1.0)


def smoothstep(edge0, edge1, value):
    t = max(0.0, min(1.0, (value - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def gaussian(value, center, sigma):
    return math.exp(-0.5 * ((value - center) / sigma) ** 2)


def lip_bounds(p):
    ax = abs(p.x)
    corner = smoothstep(0.026, 0.044, ax)
    cupid = gaussian(ax, 0.0115, 0.0052)
    notch = gaussian(ax, 0.0, 0.0048)
    slit = 1.5295
    top = (1.5370 + 0.0015 * cupid - 0.00065 * notch) * (1.0 - corner) + 1.5302 * corner
    bottom = 1.5200 * (1.0 - corner) + 1.5283 * corner
    return slit, top, bottom, corner, cupid, notch


def apply_authoring_mix(body):
    shape_names = [key.name for key in body.data.shape_keys.key_blocks] if body.data.shape_keys else []
    bpy.ops.object.select_all(action="DESELECT")
    body.select_set(True)
    bpy.context.view_layer.objects.active = body
    if body.data.shape_keys:
        bpy.ops.object.shape_key_remove(all=True, apply_mix=True)
    return shape_names


def subdivide_mouth(body):
    before = (len(body.data.vertices), len(body.data.polygons))
    bm = bmesh.new()
    bm.from_mesh(body.data)
    selected_faces = []
    for face in bm.faces:
        center = body.matrix_world @ face.calc_center_median()
        if abs(center.x) < 0.060 and center.y < -0.102 and 1.510 < center.z < 1.551:
            selected_faces.append(face)
    edges = {edge for face in selected_faces for edge in face.edges}
    result = bmesh.ops.subdivide_edges(bm, edges=list(edges), cuts=1, use_grid_fill=True)
    new_vertices = [item for item in result.get("geom_inner", []) if isinstance(item, bmesh.types.BMVert)]
    bm.to_mesh(body.data)
    bm.free()
    body.data.update()
    after = (len(body.data.vertices), len(body.data.polygons))
    return {
        "verticesBefore": before[0],
        "polygonsBefore": before[1],
        "selectedFaces": len(selected_faces),
        "selectedEdges": len(edges),
        "newVerticesReported": len(new_vertices),
        "verticesAfter": after[0],
        "polygonsAfter": after[1],
    }


def sculpt_lips(body):
    moved = 0
    maximum = 0.0
    upper_count = 0
    corner_count = 0
    for vertex in body.data.vertices:
        p = body.matrix_world @ vertex.co
        ax = abs(p.x)
        if ax >= 0.046 or p.y >= -0.104 or not (1.516 < p.z < 1.544):
            continue
        slit, top, _bottom, corner, cupid, notch = lip_bounds(p)
        if not (slit - 0.00015 < p.z < top + 0.0005):
            continue
        width = 1.0 - smoothstep(0.030, 0.045, ax)
        front = 1.0 - smoothstep(-0.120, -0.104, p.y)
        height = max(0.0005, top - slit)
        t = max(0.0, min(1.0, (p.z - slit) / height))
        profile = math.sin(math.pi * t) * width * front
        profile *= smoothstep(slit - 0.0001, slit + 0.0008, p.z)
        profile *= 1.0 - smoothstep(top - 0.0010, top + 0.0003, p.z)
        if profile <= 0.004:
            continue
        delta = Vector((0.0, -0.00125 * profile + 0.00012 * corner * profile, 0.00028 * cupid * profile - 0.00016 * notch * profile))
        vertex.co += body.matrix_world.inverted().to_3x3() @ delta
        moved += 1
        upper_count += 1
        if corner > 0.05:
            corner_count += 1
        maximum = max(maximum, delta.length)
    body.data.update()
    return {"verticesMoved": moved, "upperVerticesMoved": upper_count, "cornerVerticesMoved": corner_count, "maximumDeltaMm": maximum * 1000.0}


def anatomical_mask(p):
    ax = abs(p.x)
    if ax >= 0.046 or p.y >= -0.104 or not (1.516 < p.z < 1.544):
        return 0.0, "none"
    slit, top, bottom, _corner, _cupid, _notch = lip_bounds(p)
    width = 1.0 - smoothstep(0.030, 0.045, ax)
    front = 1.0 - smoothstep(-0.120, -0.104, p.y)
    upper = smoothstep(slit - 0.0003, slit + 0.0008, p.z) * (1.0 - smoothstep(top - 0.0009, top + 0.0003, p.z))
    lower = smoothstep(bottom - 0.0004, bottom + 0.0009, p.z) * (1.0 - smoothstep(slit - 0.0007, slit + 0.00025, p.z))
    return width * front * max(upper, lower), "upper" if upper >= lower else "lower"


def add_lip_material(body):
    name = "AevryndAnatomicalVermilionR226"
    field = body.data.color_attributes.new(name=name, type="FLOAT_COLOR", domain="POINT")
    counts = {"upper": 0, "lower": 0}
    for vertex in body.data.vertices:
        p = body.matrix_world @ vertex.co
        mask, region = anatomical_mask(p)
        factor = 0.36 * mask
        field.data[vertex.index].color = (factor, factor, factor, 1.0)
        if region != "none" and factor > 0.002:
            counts[region] += 1
    material = body.active_material.copy()
    material.name = "Aevrynd_Skin_LocalMouthRetopology_R226"
    body.data.materials.clear()
    body.data.materials.append(material)
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
    base = shader.inputs["Base Color"]
    source = base.links[0].from_socket
    for link in list(base.links):
        links.remove(link)
    color = nodes.new("ShaderNodeVertexColor")
    color.name = "Aevrynd Anatomical Vermilion Field R226"
    color.layer_name = field.name
    mix = nodes.new("ShaderNodeMixRGB")
    mix.name = "Aevrynd Anatomical Vermilion Mix R226"
    mix.blend_type = "MIX"
    mix.inputs[2].default_value = TARGET_COLOR
    links.new(color.outputs["Color"], mix.inputs[0])
    links.new(source, mix.inputs[1])
    links.new(mix.outputs["Color"], base)
    material["aevrynd_skin_revision"] = "v249r226"
    return {"attribute": name, "verticesTinted": counts, "mixStrength": 0.36, "targetColorLinear": TARGET_COLOR}


def weight_audit(body):
    unweighted = 0
    min_total = float("inf")
    for vertex in body.data.vertices:
        total = sum(group.weight for group in vertex.groups)
        min_total = min(min_total, total)
        if total <= 1e-6:
            unweighted += 1
    return {"vertexGroups": len(body.vertex_groups), "unweightedVertices": unweighted, "minimumWeightSum": min_total}


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, filename, location, target, lens, size, wireframe=False):
    scene = bpy.context.scene
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.filepath = str(RENDER_DIR / filename)
    scene.render.film_transparent = False
    body = bpy.data.objects[BODY]
    body.show_wire = wireframe
    body.show_all_edges = wireframe
    bpy.ops.render.render(write_still=True)
    body.show_wire = False


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
body = bpy.data.objects[BODY]
source_shapes = apply_authoring_mix(body)
topology = subdivide_mouth(body)
sculpt = sculpt_lips(body)
material = add_lip_material(body)
weights = weight_audit(body)
body["aevrynd_authoring_revision"] = "v249r226-local-mouth-retopology"
body["aevrynd_layer"] = "ANATOMY_BODY_HEAD_CONTINUOUS"
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd Review Camera"]
render(camera, "01-face-front.png", (0.0, -0.56, 1.585), (0.0, -0.060, 1.585), 108, (1100, 1100))
render(camera, "02-mouth-close.png", (0.0, -0.43, 1.525), (0.0, -0.105, 1.525), 120, (1100, 760))
render(camera, "03-three-quarter.png", (0.45, -0.62, 1.58), (0.0, -0.015, 1.565), 92, (1000, 1000))
render(camera, "04-profile.png", (0.70, -0.03, 1.57), (0.0, -0.010, 1.555), 96, (1000, 1000))
render(camera, "05-mouth-wireframe.png", (0.0, -0.43, 1.525), (0.0, -0.105, 1.525), 120, (1100, 760), wireframe=True)
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "sourceShapeKeysApplied": source_shapes,
    "topology": topology,
    "sculpt": sculpt,
    "material": material,
    "weights": weights,
    "legacyMouthAccessoriesVisible": any(not bpy.data.objects[name].hide_render for name in ("Lip_Upper", "Lip_Lower", "Mouth_WetLine")),
    "status": "VISUAL_AND_COLLISION_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R226_LOCAL_MOUTH_RETOPOLOGY=" + json.dumps(report, sort_keys=True))
