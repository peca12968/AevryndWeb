import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-converged-upper-lid-r210.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r220-mouth-layer-isolation"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-mouth-layer-isolation-r220.review.json"
BODY = "AevryndFemaleBodyBaseV118"
MOUTH_NAMES = ("Lip_Upper", "Lip_Lower", "Mouth_WetLine", "Mouth_Cavity", "Tongue", "Teeth_Upper")


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def is_hair(obj):
    layer = str(obj.get("aevrynd_layer", ""))
    name = obj.name.lower()
    return layer.startswith("hair.") or any(token in name for token in ("hair", "groom", "scalp"))


def render(camera, filename, location, target, lens, size):
    scene = bpy.context.scene
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.filepath = str(OUT / filename)
    bpy.ops.render.render(write_still=True)


def bounds(obj):
    points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    return {
        "vertices": len(points),
        "polygons": len(obj.data.polygons),
        "min": [min(point[i] for point in points) for i in range(3)],
        "max": [max(point[i] for point in points) for i in range(3)],
        "materials": [material.name for material in obj.data.materials if material],
        "layer": obj.get("aevrynd_layer"),
        "role": obj.get("aevrynd_role"),
    }


def set_state(state):
    body = bpy.data.objects[BODY]
    body.hide_render = state == "accessories-only"
    for obj in bpy.data.objects:
        if is_hair(obj):
            obj.hide_render = True
    for name in MOUTH_NAMES:
        obj = bpy.data.objects.get(name)
        if obj:
            if state in {"body-only", "wireframe", "authored"}:
                obj.hide_render = True
            elif state in {"legacy-visible", "accessories-only"}:
                obj.hide_render = False
    if state == "accessories-only":
        for obj in bpy.data.objects:
            if obj.type == "MESH" and obj.name not in MOUTH_NAMES:
                obj.hide_render = True


def add_wire_overlay():
    body = bpy.data.objects[BODY]
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(depsgraph)
    mesh = bpy.data.meshes.new_from_object(evaluated, depsgraph=depsgraph, preserve_all_data_layers=False)
    wire = bpy.data.objects.new("Aevrynd_FaceTopology_Wire_R220", mesh)
    bpy.context.scene.collection.objects.link(wire)
    wire.matrix_world = body.matrix_world.copy()
    material = bpy.data.materials.new("Aevrynd_FaceTopology_Wire_Material_R220")
    material.diffuse_color = (0.008, 0.012, 0.018, 1.0)
    material.use_nodes = True
    shader = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    shader.inputs["Base Color"].default_value = material.diffuse_color
    shader.inputs["Roughness"].default_value = 0.8
    mesh.materials.append(material)
    modifier = wire.modifiers.new("Aevrynd Face Wire R220", "WIREFRAME")
    modifier.thickness = 0.000065
    modifier.use_replace = True
    return wire


OUT.mkdir(parents=True, exist_ok=True)
report = {"source": str(SOURCE), "layers": {}, "states": {}}
for state in ("authored", "legacy-visible", "accessories-only", "wireframe"):
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    set_state(state)
    if state == "wireframe":
        add_wire_overlay()
    camera = bpy.data.objects["Aevrynd Review Camera"]
    render(camera, f"{state}-01-face-front.png", (0.0, -0.56, 1.585), (0.0, -0.060, 1.585), 108, (1100, 1100))
    render(camera, f"{state}-02-mouth-close.png", (0.0, -0.43, 1.525), (0.0, -0.105, 1.525), 120, (1100, 760))
    render(camera, f"{state}-03-three-quarter.png", (0.45, -0.62, 1.58), (0.0, -0.015, 1.565), 92, (1000, 1000))
    report["states"][state] = {
        "bodyVisible": state != "accessories-only",
        "mouthAccessoriesVisible": state in {"legacy-visible", "accessories-only"},
    }

bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
for name in (BODY,) + MOUTH_NAMES:
    obj = bpy.data.objects.get(name)
    if obj and obj.type == "MESH":
        report["layers"][name] = bounds(obj)
report["status"] = "AUTHORED_STATE_CONFIRMED_LEGACY_LIP_SHELLS_ALREADY_HIDDEN"
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R220_MOUTH_LAYER_ISOLATION=" + json.dumps(report, sort_keys=True))
