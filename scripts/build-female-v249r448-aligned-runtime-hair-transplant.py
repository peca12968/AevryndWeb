import hashlib
import json
import math
import struct
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-open-topology-physical-skin-r446.blend"
HAIR_SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-runtime-anchored-part-root-density-r409.blend"
OUTPUT = ASSETS / "aevrynd-female-authoring-v249-mainline-open-topology-runtime-hair-r448-study.blend"
REPORT = ASSETS / "female-v249-mainline-aligned-runtime-hair-r448.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r448-aligned-runtime-hair"
RIG = "AevryndFemaleRig"
BODY = "AevryndFemaleBodyBaseV118"
HAIR_OBJECTS = tuple(
    [f"AevryndFemaleRuntimeCards_{region}_R409" for region in ("front", "crown", "rear", "hairline")]
    + [
        "AevryndFemaleRuntimeScalpCap_R409",
        "AevryndFemaleRuntimeHairlineDensity_R409",
        "AevryndFemaleRuntimePartRootDensity_R409",
    ]
)
CHAINS = {
    "hair_dyn.L.front": (-0.082, -0.030),
    "hair_dyn.R.front": (0.082, -0.030),
    "hair_dyn.L.back": (-0.065, 0.060),
    "hair_dyn.C.back": (0.000, 0.078),
    "hair_dyn.R.back": (0.065, 0.060),
}
LEVELS = (1.675, 1.585, 1.495, 1.385)
FRAMES = tuple(range(1, 62))
ALIGNMENT_WORLD = Vector((0.0, 0.025521, 0.0))


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def rest_hash(rig, exclude_hair=False):
    bones = sorted(
        (bone for bone in rig.data.bones if not exclude_hair or not bone.name.startswith("hair_dyn.")),
        key=lambda bone: bone.name,
    )
    digest = hashlib.sha256()
    for bone in bones:
        digest.update(bone.name.encode("utf-8") + b"\0")
        values = tuple(bone.head_local) + tuple(bone.tail_local) + tuple(value for row in bone.matrix_local for value in row)
        digest.update(struct.pack("<22d", *values))
    return digest.hexdigest(), len(bones)


def capture_hair_motion():
    bpy.ops.wm.open_mainfile(filepath=str(HAIR_SOURCE))
    scene = bpy.context.scene
    rig = bpy.data.objects[RIG]
    source_hash, source_count = rest_hash(rig, exclude_hair=True)
    motion = {}
    for frame in FRAMES:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        motion[frame] = {
            bone.name: tuple(bone.rotation_euler)
            for bone in rig.pose.bones
            if bone.name.startswith("hair_dyn.")
        }
    return motion, source_hash, source_count


def add_hair_bones(rig):
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    for chain_name, (x, y) in CHAINS.items():
        parent = rig.data.edit_bones.get("head")
        for index in range(3):
            name = f"{chain_name}.{index + 1:02d}"
            bone = rig.data.edit_bones.get(name) or rig.data.edit_bones.new(name)
            bone.head = (x, y, LEVELS[index])
            bone.tail = (x, y, LEVELS[index + 1])
            bone.parent = parent
            bone.use_connect = False
            parent = bone
    bpy.ops.object.mode_set(mode="POSE")
    for chain_name in CHAINS:
        for index in range(3):
            bone = rig.pose.bones[f"{chain_name}.{index + 1:02d}"]
            bone.rotation_mode = "XYZ"
            bone["aevrynd_secondary_motion"] = True
            bone["stiffness"] = (0.88, 0.73, 0.57)[index]
            bone["damping"] = (0.84, 0.77, 0.70)[index]
            bone["gravity"] = (0.12, 0.31, 0.53)[index]
            bone["collision_radius_m"] = (0.020, 0.017, 0.014)[index]
            bone["max_swing_deg"] = (7.0, 12.0, 18.0)[index]
    bpy.ops.object.mode_set(mode="OBJECT")
    rig.select_set(False)


def install_hair_motion(scene, rig, motion):
    for frame in FRAMES:
        scene.frame_set(frame)
        for name, rotation in motion[frame].items():
            bone = rig.pose.bones[name]
            bone.rotation_euler = rotation
            bone.keyframe_insert(data_path="rotation_euler", frame=frame)
    scene.frame_set(1)
    bpy.context.view_layer.update()


def append_hair_objects(rig):
    with bpy.data.libraries.load(str(HAIR_SOURCE), link=False) as (data_from, data_to):
        missing = [name for name in HAIR_OBJECTS if name not in data_from.objects]
        if missing:
            raise RuntimeError(f"Missing r409 runtime hair objects: {missing}")
        data_to.objects = list(HAIR_OBJECTS)
    appended = list(data_to.objects)
    for obj in appended:
        if obj is None:
            continue
        if obj.name not in bpy.context.scene.collection.objects:
            bpy.context.scene.collection.objects.link(obj)
        world = obj.matrix_world.copy()
        world.translation += ALIGNMENT_WORLD
        obj.parent = rig
        obj.matrix_parent_inverse = rig.matrix_world.inverted()
        obj.matrix_world = world
        for modifier in obj.modifiers:
            if modifier.type == "ARMATURE":
                modifier.object = rig
        obj["aevrynd_transplant_revision"] = "v249r448"
        obj["aevrynd_transplant_source"] = HAIR_SOURCE.name
    return appended


def is_old_large_hair(obj):
    if obj.name in HAIR_OBJECTS:
        return False
    name = obj.name.lower()
    if any(token in name for token in ("brow", "lash", "lid", "tear", "caruncle", "eye")):
        return False
    materials = getattr(obj.data, "materials", ()) if hasattr(obj, "data") else ()
    material_names = " ".join(material.name.lower() for material in materials if material)
    return obj.type in {"MESH", "CURVES", "CURVE"} and any(
        token in name or token in material_names
        for token in ("hair", "scalp", "groom", "flyaway", "lock", "fiber")
    )


def render(scene, camera, frame, label, location, target, lens):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(RENDER_DIR / f"{label}.png")
    bpy.ops.render.render(write_still=True)


motion, source_rest_hash, source_rest_count = capture_hair_motion()
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
rig = bpy.data.objects[RIG]
target_rest_hash, target_rest_count = rest_hash(rig)
if (target_rest_hash, target_rest_count) != (source_rest_hash, source_rest_count):
    raise RuntimeError("r409 and r446 base skeletons are not rest-pose identical")
for obj in bpy.data.objects:
    if is_old_large_hair(obj):
        obj.hide_render = True
        obj.hide_viewport = True
add_hair_bones(rig)
install_hair_motion(scene, rig, motion)
appended = append_hair_objects(rig)
scene["aevrynd_mainline_revision"] = "v249r448-aligned-runtime-hair-transplant-study"
scene["aevrynd_release_state"] = "R448_ALIGNED_HAIR_TRANSPLANT_COLLISION_AND_VISUAL_REVIEW_REQUIRED"
scene["aevrynd_hair_layers"] = "|".join(obj.get("aevrynd_layer", obj.name) for obj in appended)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
for frame, label, location, target, lens in (
    (1, "01-front-f01", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
    (1, "02-hairline-f01", (0.0, -0.57, 1.76), (0.0, -0.02, 1.64), 92),
    (1, "03-top-f01", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
    (1, "04-three-quarter-f01", (0.45, -0.66, 1.60), (0.0, -0.005, 1.56), 84),
    (1, "05-back-f01", (0.0, 0.90, 1.59), (0.0, 0.0, 1.56), 82),
    (33, "06-front-f33", (0.0, -0.76, 1.58), (0.0, -0.015, 1.56), 84),
    (33, "07-back-f33", (0.0, 0.90, 1.59), (0.0, 0.0, 1.56), 82),
):
    render(scene, camera, frame, label, location, target, lens)
scene.frame_set(1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE),
    "hairSource": str(HAIR_SOURCE),
    "output": str(OUTPUT),
    "renderDirectory": str(RENDER_DIR),
    "baseSkeletonRestHashR446": target_rest_hash,
    "baseSkeletonRestHashR409": source_rest_hash,
    "baseSkeletonRestIdentical": True,
    "baseBoneCount": target_rest_count,
    "addedHairBoneCount": sum(1 for bone in rig.data.bones if bone.name.startswith("hair_dyn.")),
    "hairLayers": [obj.get("aevrynd_layer", obj.name) for obj in appended],
    "cards": sum(int(obj.get("aevrynd_card_count", 0)) for obj in appended),
    "alignmentWorldM": list(ALIGNMENT_WORLD),
    "ownedAssetOnly": True,
    "websitePromotionApproved": False,
    "colorManagement": {"viewTransform": "Standard", "look": "None", "exposureEV": 0.0},
    "status": "COLLISION_AND_VISUAL_REVIEW_REQUIRED",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R448_ALIGNED_RUNTIME_HAIR=" + json.dumps(report, sort_keys=True))
