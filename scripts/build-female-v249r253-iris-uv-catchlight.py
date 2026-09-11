import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-eye-optics-skin-r252.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-iris-uv-catchlight-r253.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-iris-uv-catchlight-r253.build-report.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r253-iris-uv-catchlight"
RIG = "AevryndFemaleRig"
HEAD_BONE = "head"


def bind_to_head(obj, rig):
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = HEAD_BONE
    obj.matrix_world = world
    obj["aevrynd_binding"] = "rig.head"


def planar_disc(name, center_x, y, center_z, radius, material, layer, rig):
    segments = 128
    vertices = [(center_x, y, center_z)]
    for index in range(segments):
        angle = 2.0 * math.pi * index / segments
        vertices.append((center_x + radius * math.cos(angle), y, center_z + radius * math.sin(angle)))
    faces = [(0, 1 + index, 1 + (index + 1) % segments) for index in range(segments)]
    mesh = bpy.data.meshes.new(name + "Topology")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    uv = mesh.uv_layers.new(name="AevryndRadialUV")
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            vertex = mesh.vertices[mesh.loops[loop_index].vertex_index].co
            uv.data[loop_index].uv = (
                0.5 + (vertex.x - center_x) / (2.0 * radius),
                0.5 + (vertex.z - center_z) / (2.0 * radius),
            )
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(material)
    obj["aevrynd_layer"] = layer
    obj["aevrynd_revision"] = "v249r253"
    bind_to_head(obj, rig)
    return obj


def replace_layer(side, kind, radius, material_name, layer, y_offset, rig):
    old = bpy.data.objects[f"AevryndEye_{side}_{kind}_R252"]
    center = old.matrix_world.translation.copy()
    sclera = bpy.data.objects[f"AevryndEye_{side}_Sclera_R249"]
    sclera_front = min((sclera.matrix_world @ vertex.co).y for vertex in sclera.data.vertices)
    material = bpy.data.materials[material_name]
    bpy.data.objects.remove(old, do_unlink=True)
    return planar_disc(
        f"AevryndEye_{side}_{kind}_R253", center.x, sclera_front + y_offset, center.z,
        radius, material, layer, rig,
    )


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, frame, name, location, target, lens, size):
    scene = bpy.context.scene
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
rig = bpy.data.objects[RIG]
created = []
for side in ("L", "R"):
    created.append(replace_layer(side, "Limbal", 0.00620, "Aevrynd_Limbal_Physical_R252", f"eye.{side.lower()}.limbal_ring", -0.00012, rig).name)
    created.append(replace_layer(side, "Iris", 0.00570, "Aevrynd_IrisHazel_Owned_R252", f"eye.{side.lower()}.iris_stroma", -0.00019, rig).name)
    created.append(replace_layer(side, "Pupil", 0.00205, "Aevrynd_Pupil_Physical_R252", f"eye.{side.lower()}.pupil", -0.00027, rig).name)

cornea_material = bpy.data.materials["Aevrynd_Cornea_Physical_R252"]
shader = next(node for node in cornea_material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
shader.inputs["Roughness"].default_value = 0.028
shader.inputs["Specular IOR Level"].default_value = 0.34
shader.inputs["Transmission Weight"].default_value = 0.72
shader.inputs["Alpha"].default_value = 0.055
shader.inputs["Coat Weight"].default_value = 0.0

light_metrics = {}
for obj in scene.objects:
    if obj.type != "LIGHT":
        continue
    if hasattr(obj.data, "size"):
        obj.data.size = min(obj.data.size, 0.22)
    light_metrics[obj.name] = {"energy": obj.data.energy, "size": getattr(obj.data, "size", None)}

scene["aevrynd_mainline_revision"] = "v249r253-iris-uv-catchlight"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "EYE_VISUAL_AND_CLEARANCE_REVIEW_PENDING"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
views = (
    (1, "01-face-front", (0.0, -1.02, 1.66), (0.0, 0.0, 1.625), 92, (1100, 1100)),
    (1, "02-face-three-quarter", (0.56, -0.89, 1.65), (0.0, 0.0, 1.615), 92, (1100, 1100)),
    (1, "03-eye-front", (0.0, -0.55, 1.616), (0.0, -0.13, 1.608), 105, (1200, 700)),
    (20, "04-pose-face", (0.56, -0.89, 1.65), (0.0, 0.0, 1.615), 92, (1100, 1100)),
)
for values in views:
    render(camera, *values)
scene.frame_set(1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "createdLayers": created,
    "irisUV": {"type": "explicit radial fan", "segments": 128, "range": [0.0, 1.0]},
    "cornea": {"roughness": 0.028, "specularIorLevel": 0.34, "transmission": 0.72, "alpha": 0.055},
    "lights": light_metrics,
    "renderDirectory": str(RENDER_DIR),
    "status": "EYE_VISUAL_AND_CLEARANCE_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R253_IRIS_UV_CATCHLIGHT=" + json.dumps(report, sort_keys=True))
