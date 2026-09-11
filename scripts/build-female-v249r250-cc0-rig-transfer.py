import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cc0-foundation-r249.blend"
RIG_SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-baked-seam-clearance-r247.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cc0-rig-transfer-r250.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-cc0-rig-transfer-r250.build-report.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r250-cc0-rig-transfer"
BODY = "AevryndFemaleBody_CC0_R249"
SOURCE_BODY = "AevryndFemaleBodyBaseV118"
RIG = "AevryndFemaleRig"
HEAD_BONE = "head"
SCALE = 1.7199828624725342 / 1.6414071321487427


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, location, target, lens, size):
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene = bpy.context.scene
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)


def append_objects(filepath, names):
    with bpy.data.libraries.load(str(filepath), link=False) as (available, loaded):
        loaded.objects = [name for name in names if name in available.objects]
    for obj in loaded.objects:
        if obj is not None and obj.name not in bpy.context.scene.objects:
            bpy.context.scene.collection.objects.link(obj)
    return loaded.objects


def scale_foundation(body):
    children = list(body.children)
    for child in children:
        world = child.matrix_world.copy()
        child.parent = None
        child.matrix_world = world
    for vertex in body.data.vertices:
        vertex.co *= SCALE
    body.data.update()
    for child in children:
        world = child.matrix_world.copy()
        world.translation *= SCALE
        child.matrix_world = world
        child.scale *= SCALE
    return children


def transfer_weights(body, source_body):
    before = len(body.vertex_groups)
    for source_group in source_body.vertex_groups:
        if body.vertex_groups.get(source_group.name) is None:
            body.vertex_groups.new(name=source_group.name)
    modifier = body.modifiers.new("Aevrynd R250 Surface Weight Transfer", "DATA_TRANSFER")
    modifier.object = source_body
    modifier.use_vert_data = True
    modifier.data_types_verts = {"VGROUP_WEIGHTS"}
    modifier.vert_mapping = "POLYINTERP_NEAREST"
    modifier.layers_vgroup_select_src = "ALL"
    modifier.layers_vgroup_select_dst = "NAME"
    bpy.context.view_layer.objects.active = body
    body.select_set(True)
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    return {"groupsBefore": before, "groupsAfter": len(body.vertex_groups)}


def bind_to_head(objects, rig):
    for obj in objects:
        world = obj.matrix_world.copy()
        obj.parent = rig
        obj.parent_type = "BONE"
        obj.parent_bone = HEAD_BONE
        obj.matrix_world = world
        obj["aevrynd_binding"] = "rig.head"


def weight_audit(body):
    sums = [sum(group.weight for group in vertex.groups) for vertex in body.data.vertices]
    return {
        "vertexGroups": len(body.vertex_groups),
        "unweightedVertices": sum(value <= 1e-8 for value in sums),
        "minimumWeightSum": min(sums),
        "maximumWeightSum": max(sums),
        "meanWeightSum": sum(sums) / len(sums),
    }


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
body = bpy.data.objects[BODY]
eye_layers = scale_foundation(body)
appended = append_objects(RIG_SOURCE, (RIG, SOURCE_BODY))
rig = bpy.data.objects[RIG]
source_body = bpy.data.objects[SOURCE_BODY]
source_body.hide_render = True
source_body.hide_viewport = True
source_body["aevrynd_role"] = "weight_transfer_source_only"

weight_transfer = transfer_weights(body, source_body)
bpy.data.objects.remove(source_body, do_unlink=True)
armature = body.modifiers.new("Aevrynd R250 Armature", "ARMATURE")
armature.object = rig
body.parent = rig
body["aevrynd_layer"] = "anatomy.body_head_continuous.rigged"
body["aevrynd_revision"] = "v249r250-cc0-rig-transfer"
bind_to_head(eye_layers, rig)
weights = weight_audit(body)

scene["aevrynd_mainline_revision"] = "v249r250-cc0-rig-transfer"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_rig_source"] = RIG_SOURCE.name
scene["aevrynd_release_state"] = "DEFORMATION_AND_COLLISION_REVIEW_PENDING"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
views = (
    (1, "01-neutral-full", (0.0, -4.45, 1.10), (0.0, 0.0, 1.00), 76, (900, 1200)),
    (1, "02-neutral-face", (0.0, -1.10, 1.66), (0.0, 0.0, 1.625), 88, (1000, 1000)),
    (20, "03-pose-full", (0.0, -4.45, 1.10), (0.0, 0.0, 1.00), 76, (900, 1200)),
    (20, "04-pose-three-quarter", (0.62, -1.0, 1.64), (0.0, 0.0, 1.60), 88, (1000, 1000)),
)
for frame, name, location, target, lens, size in views:
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    render(camera, name, location, target, lens, size)

scene.frame_set(1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE),
    "rigSource": str(RIG_SOURCE),
    "output": str(OUTPUT),
    "uniformScale": SCALE,
    "weightTransfer": weight_transfer,
    "weightAudit": weights,
    "eyeLayersBoundTo": HEAD_BONE,
    "limitations": ["surface-proximity weight transfer requires deformation review", "no clothing", "no hair"],
    "status": "DEFORMATION_AND_COLLISION_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R250_CC0_RIG_TRANSFER=" + json.dumps(report, sort_keys=True))
