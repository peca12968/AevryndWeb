import json
import math
from pathlib import Path

import bpy
from mathutils import Quaternion, Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v7.blend"
OUTPUT = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v8.blend"
BUILD = ROOT / ".character-build" / "aevrynd-female-authoring-v8.glb"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "rig-v8"


BONES = {
    "root": ((0.0, 0.0, 0.02), (0.0, 0.0, 0.14), None, False),
    "pelvis": ((0.0, 0.0, 0.86), (0.0, 0.0, 0.98), "root", True),
    "spine_01": ((0.0, 0.0, 0.98), (0.0, 0.0, 1.10), "pelvis", True),
    "spine_02": ((0.0, 0.0, 1.10), (0.0, 0.0, 1.23), "spine_01", True),
    "chest": ((0.0, 0.0, 1.23), (0.0, 0.0, 1.36), "spine_02", True),
    "neck": ((0.0, 0.0, 1.36), (0.0, 0.0, 1.47), "chest", True),
    "head": ((0.0, 0.0, 1.47), (0.0, 0.0, 1.68), "neck", True),
    "clavicle.L": ((0.0, 0.0, 1.345), (0.138, 0.0, 1.342), "chest", True),
    "upper_arm.L": ((0.138, 0.0, 1.342), (0.235, -0.006, 1.12), "clavicle.L", True),
    "forearm.L": ((0.235, -0.006, 1.12), (0.335, -0.012, 0.91), "upper_arm.L", True),
    "hand.L": ((0.335, -0.012, 0.91), (0.395, -0.018, 0.82), "forearm.L", True),
    "clavicle.R": ((0.0, 0.0, 1.345), (-0.138, 0.0, 1.342), "chest", True),
    "upper_arm.R": ((-0.138, 0.0, 1.342), (-0.235, -0.006, 1.12), "clavicle.R", True),
    "forearm.R": ((-0.235, -0.006, 1.12), (-0.335, -0.012, 0.91), "upper_arm.R", True),
    "hand.R": ((-0.335, -0.012, 0.91), (-0.395, -0.018, 0.82), "forearm.R", True),
    "thigh.L": ((0.083, 0.0, 0.91), (0.078, -0.002, 0.52), "pelvis", True),
    "shin.L": ((0.078, -0.002, 0.52), (0.074, -0.005, 0.115), "thigh.L", True),
    "foot.L": ((0.074, -0.005, 0.115), (0.074, -0.125, 0.065), "shin.L", True),
    "thigh.R": ((-0.083, 0.0, 0.91), (-0.078, -0.002, 0.52), "pelvis", True),
    "shin.R": ((-0.078, -0.002, 0.52), (-0.074, -0.005, 0.115), "thigh.R", True),
    "foot.R": ((-0.074, -0.005, 0.115), (-0.074, -0.125, 0.065), "shin.R", True),
}


def build_armature():
    data = bpy.data.armatures.new("AevryndFemaleSkeleton")
    rig = bpy.data.objects.new("AevryndFemaleRig", data)
    bpy.context.scene.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    created = {}
    for name, (head, tail, parent, deform) in BONES.items():
        bone = data.edit_bones.new(name)
        bone.head = head
        bone.tail = tail
        bone.use_deform = deform
        created[name] = bone
        if parent:
            bone.parent = created[parent]
            bone.use_connect = (Vector(head) - Vector(BONES[parent][1])).length <= 1e-5
    bpy.ops.object.mode_set(mode="OBJECT")
    rig["aevrynd_role"] = "female_skeleton"
    rig["aevrynd_rig_revision"] = 8
    rig["aevrynd_bone_count"] = len(BONES)
    return rig


def bind_body(body, rig):
    bpy.ops.object.select_all(action="DESELECT")
    body.select_set(True)
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    modifier = next((value for value in body.modifiers if value.type == "ARMATURE"), None)
    if modifier is None:
        raise RuntimeError("automatic weights did not create an armature modifier")
    modifier.name = "Aevrynd Skin Deform"
    body["aevrynd_skin_binding_revision"] = 8
    body["aevrynd_weight_group_count"] = len(body.vertex_groups)
    return modifier


def limit_and_normalize_weights(body, maximum=4):
    trimmed = 0
    for vertex in body.data.vertices:
        influences = sorted(
            ((entry.group, entry.weight) for entry in vertex.groups if entry.weight > 1e-8),
            key=lambda value: value[1],
            reverse=True,
        )
        kept = influences[:maximum]
        removed = influences[maximum:]
        for group_index, _ in removed:
            body.vertex_groups[group_index].remove([vertex.index])
            trimmed += 1
        total = sum(weight for _, weight in kept)
        if total > 0:
            for group_index, weight in kept:
                body.vertex_groups[group_index].add([vertex.index], weight / total, "REPLACE")
    body["aevrynd_weight_limit"] = maximum
    body["aevrynd_trimmed_weight_entries"] = trimmed
    return trimmed


def parent_head_layers(body, rig):
    attached = []
    for obj in bpy.data.objects:
        if obj == body or obj == rig or obj.type != "MESH":
            continue
        world = obj.matrix_world.copy()
        obj.parent = rig
        obj.parent_type = "BONE"
        obj.parent_bone = "head"
        obj.matrix_world = world
        obj["aevrynd_rigid_parent"] = "head"
        attached.append(obj.name)
    return attached


def local_world_axis_rotation(rig, bone_name, axis, angle):
    rest = rig.data.bones[bone_name].matrix_local.to_quaternion()
    world = Quaternion(axis, angle)
    return rest.inverted() @ world @ rest


def build_pose_action(rig):
    action = bpy.data.actions.new("Aevrynd_Female_DeformationSuite_v1")
    rig.animation_data_create()
    rig.animation_data.action = action
    for pose_bone in rig.pose.bones:
        pose_bone.rotation_mode = "QUATERNION"
        pose_bone.rotation_quaternion = Quaternion()
        pose_bone.keyframe_insert("rotation_quaternion", frame=1, group=pose_bone.name)

    rig.pose.bones["upper_arm.L"].rotation_quaternion = local_world_axis_rotation(
        rig, "upper_arm.L", (0, 1, 0), math.radians(-38)
    )
    rig.pose.bones["upper_arm.R"].rotation_quaternion = local_world_axis_rotation(
        rig, "upper_arm.R", (0, 1, 0), math.radians(38)
    )
    rig.pose.bones["clavicle.L"].rotation_quaternion = local_world_axis_rotation(
        rig, "clavicle.L", (0, 1, 0), math.radians(-10)
    )
    rig.pose.bones["clavicle.R"].rotation_quaternion = local_world_axis_rotation(
        rig, "clavicle.R", (0, 1, 0), math.radians(10)
    )
    rig.pose.bones["head"].rotation_quaternion = local_world_axis_rotation(
        rig, "head", (0, 0, 1), math.radians(12)
    )
    animated = ("clavicle.L", "clavicle.R", "upper_arm.L", "upper_arm.R", "head")
    for name in animated:
        rig.pose.bones[name].keyframe_insert("rotation_quaternion", frame=20, group=name)

    for pose_bone in rig.pose.bones:
        if pose_bone.name not in animated:
            pose_bone.rotation_quaternion = Quaternion()
            pose_bone.keyframe_insert("rotation_quaternion", frame=20, group=pose_bone.name)
    action["aevrynd_role"] = "deformation_test_suite"
    action["aevrynd_frames"] = "1=neutral;20=arms_raised_head_turn"
    return action


def weight_audit(body):
    unweighted = 0
    maximum_influences = 0
    for vertex in body.data.vertices:
        influences = [group for group in vertex.groups if group.weight > 1e-5]
        maximum_influences = max(maximum_influences, len(influences))
        if not influences:
            unweighted += 1
    return unweighted, maximum_influences


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
RENDER_DIR.mkdir(parents=True, exist_ok=True)
BUILD.parent.mkdir(parents=True, exist_ok=True)
body = bpy.data.objects["AevryndFemaleBodyBase"]
rig = build_armature()
bind_body(body, rig)
trimmed_weights = limit_and_normalize_weights(body)
head_layers = parent_head_layers(body, rig)
action = build_pose_action(rig)
unweighted, maximum_influences = weight_audit(body)
body["aevrynd_unweighted_vertices"] = unweighted
body["aevrynd_maximum_influences"] = maximum_influences
bpy.context.scene.frame_start = 1
bpy.context.scene.frame_end = 20
bpy.context.scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

camera = bpy.data.objects["Aevrynd Review Camera"]
render(camera, "female-rig-neutral", 1, (0, -3.05, 0.92), (0, 0, 0.90))
render(camera, "female-rig-pose-20", 20, (0, -3.05, 0.98), (0, 0, 0.96))

multires = next(modifier for modifier in body.modifiers if modifier.type == "MULTIRES")
old_multires = (multires.levels, multires.sculpt_levels, multires.render_levels)
multires.levels = multires.sculpt_levels = multires.render_levels = 0
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
multires.levels, multires.sculpt_levels, multires.render_levels = old_multires

print(
    "AEVRYND_RIG_V8_REPORT="
    + json.dumps({
        "state": "AUTHORING",
        "bone_count": len(BONES),
        "head_layers": len(head_layers),
        "weight_groups": len(body.vertex_groups),
        "unweighted_vertices": unweighted,
        "maximum_influences": maximum_influences,
        "trimmed_weight_entries": trimmed_weights,
        "action": action.name,
        "runtime_glb": str(BUILD),
    })
)
