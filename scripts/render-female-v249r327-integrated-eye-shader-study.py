import json
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-unified-dense-upper-eyelids-r323.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-integrated-eye-shader-r327.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r327-integrated-eye-shader"
BODY = "AevryndFemaleBody_CC0_R249"
REMOVED_PARTS = ("Cornea_R252", "Limbal_R253", "Iris_R253", "Pupil_R253")


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def math_node(nodes, operation, value=None):
    node = nodes.new("ShaderNodeMath")
    node.operation = operation
    if value is not None:
        node.inputs[1].default_value = value
    return node


def build_eye_material(side):
    material = bpy.data.materials.new(f"Aevrynd_IntegratedEye_{side}_R327")
    material.use_nodes = True
    material["aevrynd_ownership"] = "procedural in-project"
    material["aevrynd_revision"] = "v249r327"
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    shader.inputs["Roughness"].default_value = 0.22
    if "IOR" in shader.inputs:
        shader.inputs["IOR"].default_value = 1.376
    if "Coat Weight" in shader.inputs:
        shader.inputs["Coat Weight"].default_value = 0.18
        shader.inputs["Coat Roughness"].default_value = 0.12
    if "Subsurface Weight" in shader.inputs:
        shader.inputs["Subsurface Weight"].default_value = 0.018
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])

    texcoord = nodes.new("ShaderNodeTexCoord")
    separate = nodes.new("ShaderNodeSeparateXYZ")
    links.new(texcoord.outputs["Generated"], separate.inputs["Vector"])
    x = math_node(nodes, "SUBTRACT", 0.5)
    z = math_node(nodes, "SUBTRACT", 0.5)
    links.new(separate.outputs["X"], x.inputs[0])
    links.new(separate.outputs["Z"], z.inputs[0])
    x2 = math_node(nodes, "MULTIPLY")
    z2 = math_node(nodes, "MULTIPLY")
    links.new(x.outputs[0], x2.inputs[0]); links.new(x.outputs[0], x2.inputs[1])
    links.new(z.outputs[0], z2.inputs[0]); links.new(z.outputs[0], z2.inputs[1])
    radius2 = math_node(nodes, "ADD")
    radius = math_node(nodes, "SQRT")
    links.new(x2.outputs[0], radius2.inputs[0]); links.new(z2.outputs[0], radius2.inputs[1])
    links.new(radius2.outputs[0], radius.inputs[0])

    front = math_node(nodes, "LESS_THAN", 0.24)
    links.new(separate.outputs["Y"], front.inputs[0])
    iris_radial = math_node(nodes, "LESS_THAN", 0.192)
    pupil_radial = math_node(nodes, "LESS_THAN", 0.067)
    limbal_inner = math_node(nodes, "GREATER_THAN", 0.168)
    limbal_outer = math_node(nodes, "LESS_THAN", 0.200)
    for node in (iris_radial, pupil_radial, limbal_inner, limbal_outer):
        links.new(radius.outputs[0], node.inputs[0])
    iris_mask = math_node(nodes, "MULTIPLY")
    pupil_mask = math_node(nodes, "MULTIPLY")
    ring_band = math_node(nodes, "MULTIPLY")
    ring_mask = math_node(nodes, "MULTIPLY")
    links.new(iris_radial.outputs[0], iris_mask.inputs[0]); links.new(front.outputs[0], iris_mask.inputs[1])
    links.new(pupil_radial.outputs[0], pupil_mask.inputs[0]); links.new(front.outputs[0], pupil_mask.inputs[1])
    links.new(limbal_inner.outputs[0], ring_band.inputs[0]); links.new(limbal_outer.outputs[0], ring_band.inputs[1])
    links.new(ring_band.outputs[0], ring_mask.inputs[0]); links.new(front.outputs[0], ring_mask.inputs[1])

    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 34.0
    noise.inputs["Detail"].default_value = 5.0
    noise.inputs["Roughness"].default_value = 0.72
    links.new(texcoord.outputs["Generated"], noise.inputs["Vector"])
    angle = math_node(nodes, "ARCTAN2")
    links.new(z.outputs[0], angle.inputs[0]); links.new(x.outputs[0], angle.inputs[1])
    spokes = math_node(nodes, "MULTIPLY", 46.0)
    links.new(angle.outputs[0], spokes.inputs[0])
    spoke_sine = math_node(nodes, "SINE")
    spoke_abs = math_node(nodes, "ABSOLUTE")
    links.new(spokes.outputs[0], spoke_sine.inputs[0]); links.new(spoke_sine.outputs[0], spoke_abs.inputs[0])
    fiber_mix = nodes.new("ShaderNodeMixRGB")
    fiber_mix.blend_type = "MULTIPLY"
    fiber_mix.inputs[0].default_value = 0.62
    links.new(noise.outputs["Fac"], fiber_mix.inputs[1]); links.new(spoke_abs.outputs[0], fiber_mix.inputs[2])
    iris_ramp = nodes.new("ShaderNodeValToRGB")
    iris_ramp.color_ramp.elements[0].position = 0.18
    iris_ramp.color_ramp.elements[0].color = (0.004, 0.018, 0.009, 1.0)
    iris_ramp.color_ramp.elements[1].position = 0.82
    iris_ramp.color_ramp.elements[1].color = (0.07, 0.26, 0.14, 1.0)
    links.new(fiber_mix.outputs[0], iris_ramp.inputs["Fac"])

    sclera_noise = nodes.new("ShaderNodeTexNoise")
    sclera_noise.inputs["Scale"].default_value = 7.0
    sclera_noise.inputs["Detail"].default_value = 3.0
    links.new(texcoord.outputs["Generated"], sclera_noise.inputs["Vector"])
    sclera_ramp = nodes.new("ShaderNodeValToRGB")
    sclera_ramp.color_ramp.elements[0].color = (0.58, 0.46, 0.42, 1.0)
    sclera_ramp.color_ramp.elements[1].color = (0.94, 0.86, 0.76, 1.0)
    links.new(sclera_noise.outputs["Fac"], sclera_ramp.inputs["Fac"])

    iris_mix = nodes.new("ShaderNodeMixRGB")
    links.new(iris_mask.outputs[0], iris_mix.inputs[0])
    links.new(sclera_ramp.outputs["Color"], iris_mix.inputs[1])
    links.new(iris_ramp.outputs["Color"], iris_mix.inputs[2])
    ring_mix = nodes.new("ShaderNodeMixRGB")
    ring_mix.inputs[2].default_value = (0.008, 0.020, 0.015, 1.0)
    links.new(ring_mask.outputs[0], ring_mix.inputs[0]); links.new(iris_mix.outputs[0], ring_mix.inputs[1])
    pupil_mix = nodes.new("ShaderNodeMixRGB")
    pupil_mix.inputs[2].default_value = (0.001, 0.001, 0.001, 1.0)
    links.new(pupil_mask.outputs[0], pupil_mix.inputs[0]); links.new(ring_mix.outputs[0], pupil_mix.inputs[1])
    links.new(pupil_mix.outputs[0], shader.inputs["Base Color"])
    return material


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
removed = []
for side in ("L", "R"):
    sclera = bpy.data.objects[f"AevryndEye_{side}_Sclera_R249"]
    material = build_eye_material(side)
    sclera.data = sclera.data.copy()
    sclera.data.materials.clear()
    sclera.data.materials.append(material)
    sclera["aevrynd_layer"] = f"eye.{side.lower()}.integrated_sclera_iris_pupil_cornea"
    for part in REMOVED_PARTS:
        obj = bpy.data.objects.get(f"AevryndEye_{side}_{part}")
        if obj:
            obj.hide_render = True
            removed.append(obj.name)

scene.frame_set(1)
bpy.context.view_layer.update()
depsgraph = bpy.context.evaluated_depsgraph_get()
body = bpy.data.objects[BODY]
collision = {}
for side in ("L", "R"):
    sclera = bpy.data.objects[f"AevryndEye_{side}_Sclera_R249"]
    collision[side] = len(world_bvh(body, depsgraph).overlap(world_bvh(sclera, depsgraph)))

scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
views = (
    ("face-close", (0.0, -0.68, 1.605), (0.0, -0.035, 1.606), 92),
    ("three-quarter", (0.45, -0.62, 1.62), (0.0, -0.02, 1.605), 90),
    ("profile", (-0.72, -0.55, 1.59), (0.0, 0.0, 1.56), 82),
)
for name, location, target, lens in views:
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x = scene.render.resolution_y = 1000
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)

report = {
    "source": str(SOURCE), "renderDirectory": str(RENDER_DIR), "hiddenGeometryLayers": removed,
    "integratedLayers": ["sclera", "iris", "limbal ring", "pupil", "corneal coat"],
    "bodyScleraTriangleOverlaps": collision,
    "ownedAssetOnly": True, "status": "VISUAL_REVIEW_PENDING" if not any(collision.values()) else "COLLISION_FAIL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R327_INTEGRATED_EYE_SHADER=" + json.dumps(report, sort_keys=True))
