import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-fitted-eye-skin-foundation-r602.blend"
RIG_SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-lower-face-clearance-r569.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-retargeted-rig-r603.blend"
REPORT = ASSETS / "female-v249-mainline-cc0-retargeted-rig-r603.build.json"
BODY = "AevryndFemaleCC0Baseline_v259"
RIG = "AevryndFemaleRig"
EYE_PARTS = ("Sclera", "Cornea", "Iris")
DEFORM_BONES = {
    "pelvis", "spine_01", "spine_02", "chest", "neck", "head",
    "clavicle.L", "upper_arm.L", "forearm.L", "hand.L",
    "clavicle.R", "upper_arm.R", "forearm.R", "hand.R",
    "thigh.L", "shin.L", "foot.L", "thigh.R", "shin.R", "foot.R",
}


def weighted_center(obj, group_name):
    group = obj.vertex_groups[group_name]
    total = Vector()
    weight_sum = 0.0
    for vertex in obj.data.vertices:
        try:
            weight = group.weight(vertex.index)
        except RuntimeError:
            continue
        if weight > 0.0:
            total += (obj.matrix_world @ vertex.co) * weight
            weight_sum += weight
    if weight_sum <= 0.0:
        raise RuntimeError(f"empty joint group: {group_name}")
    return total / weight_sum


def append_rig():
    with bpy.data.libraries.load(str(RIG_SOURCE), link=False) as (available, loaded):
        if RIG not in available.objects:
            raise RuntimeError(f"{RIG} missing from {RIG_SOURCE}")
        loaded.objects = [RIG]
    rig = loaded.objects[0]
    bpy.context.scene.collection.objects.link(rig)
    return rig


def fit_rig(rig, body):
    joint = lambda name: weighted_center(body, name)
    centers = {name: joint(name) for name in (
        "joint-ground", "joint-pelvis", "joint-spine-1", "joint-spine-2",
        "joint-spine-3", "joint-spine-4", "joint-neck", "joint-head-2",
        "joint-l-clavicle", "joint-l-shoulder", "joint-l-elbow", "joint-l-hand",
        "joint-l-hand-3", "joint-r-clavicle", "joint-r-shoulder", "joint-r-elbow",
        "joint-r-hand", "joint-r-hand-3", "joint-l-upper-leg", "joint-l-knee",
        "joint-l-ankle", "joint-l-foot-2", "joint-r-upper-leg", "joint-r-knee",
        "joint-r-ankle", "joint-r-foot-2",
    )}
    spans = {
        "root": (centers["joint-ground"], centers["joint-pelvis"]),
        "pelvis": (centers["joint-pelvis"], centers["joint-spine-4"]),
        "spine_01": (centers["joint-spine-4"], centers["joint-spine-3"]),
        "spine_02": (centers["joint-spine-3"], centers["joint-spine-2"]),
        "chest": (centers["joint-spine-2"], centers["joint-spine-1"]),
        "neck": (centers["joint-spine-1"], centers["joint-neck"]),
        "head": (centers["joint-neck"], centers["joint-head-2"]),
        "clavicle.L": (centers["joint-l-clavicle"], centers["joint-l-shoulder"]),
        "upper_arm.L": (centers["joint-l-shoulder"], centers["joint-l-elbow"]),
        "forearm.L": (centers["joint-l-elbow"], centers["joint-l-hand"]),
        "hand.L": (centers["joint-l-hand"], centers["joint-l-hand-3"]),
        "clavicle.R": (centers["joint-r-clavicle"], centers["joint-r-shoulder"]),
        "upper_arm.R": (centers["joint-r-shoulder"], centers["joint-r-elbow"]),
        "forearm.R": (centers["joint-r-elbow"], centers["joint-r-hand"]),
        "hand.R": (centers["joint-r-hand"], centers["joint-r-hand-3"]),
        "thigh.L": (centers["joint-l-upper-leg"], centers["joint-l-knee"]),
        "shin.L": (centers["joint-l-knee"], centers["joint-l-ankle"]),
        "foot.L": (centers["joint-l-ankle"], centers["joint-l-foot-2"]),
        "thigh.R": (centers["joint-r-upper-leg"], centers["joint-r-knee"]),
        "shin.R": (centers["joint-r-knee"], centers["joint-r-ankle"]),
        "foot.R": (centers["joint-r-ankle"], centers["joint-r-foot-2"]),
    }
    inv = rig.matrix_world.inverted()
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    for bone in rig.data.edit_bones:
        bone.use_connect = False
        bone.use_deform = bone.name in DEFORM_BONES
    for name, (head, tail) in spans.items():
        bone = rig.data.edit_bones.get(name)
        if bone is None:
            raise RuntimeError(f"missing rig bone: {name}")
        bone.head = inv @ head
        bone.tail = inv @ tail
    bpy.ops.object.mode_set(mode="OBJECT")
    return spans


def clear_old_deform_groups(body):
    removed = []
    for group in list(body.vertex_groups):
        if group.name in DEFORM_BONES:
            removed.append(group.name)
            body.vertex_groups.remove(group)
    return removed


def automatic_weights(body, rig, spans):
    clear_old_deform_groups(body)
    proxy = body.copy()
    proxy.data = body.data.copy()
    proxy.name = "Aevrynd R603 Visible Body Weight Proxy"
    bpy.context.scene.collection.objects.link(proxy)
    while proxy.data.shape_keys:
        proxy.shape_key_remove(proxy.data.shape_keys.key_blocks[-1])
    source_index = proxy.data.attributes.new("aevrynd_source_index", "INT", "POINT")
    for vertex in proxy.data.vertices:
        source_index.data[vertex.index].value = vertex.index
    visible = proxy.vertex_groups.get("body")
    if visible is None:
        raise RuntimeError("MPFB visible body group is missing")
    keep = set()
    for vertex in proxy.data.vertices:
        try:
            if visible.weight(vertex.index) > 0.0:
                keep.add(vertex.index)
        except RuntimeError:
            pass
    bpy.ops.object.select_all(action="DESELECT")
    proxy.select_set(True)
    bpy.context.view_layer.objects.active = proxy
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="DESELECT")
    bpy.ops.object.mode_set(mode="OBJECT")
    for vertex in proxy.data.vertices:
        vertex.select = vertex.index not in keep
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.delete(type="VERT")
    bpy.ops.object.mode_set(mode="OBJECT")
    proxy_indices = [item.value for item in proxy.data.attributes["aevrynd_source_index"].data]
    clear_old_deform_groups(proxy)
    bpy.ops.object.select_all(action="DESELECT")
    proxy.select_set(True)
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    deform_proxy_groups = {
        group.name: group for group in proxy.vertex_groups if group.name in DEFORM_BONES
    }
    proxy_weighted = sum(
        any(entry.group in {group.index for group in deform_proxy_groups.values()} and entry.weight > 0.0 for entry in vertex.groups)
        for vertex in proxy.data.vertices
    )
    if proxy_weighted != len(proxy.data.vertices):
        raise RuntimeError(f"bone heat weighted {proxy_weighted}/{len(proxy.data.vertices)} visible vertices")
    for name in DEFORM_BONES:
        if body.vertex_groups.get(name) is None:
            body.vertex_groups.new(name=name)
    assigned = set()
    for proxy_vertex, original_index in zip(proxy.data.vertices, proxy_indices):
        for entry in proxy_vertex.groups:
            group_name = proxy.vertex_groups[entry.group].name
            if group_name in DEFORM_BONES and entry.weight > 0.0:
                body.vertex_groups[group_name].add([original_index], entry.weight, "REPLACE")
                assigned.add(original_index)
    def distance_squared_to_segment(point, a, b):
        delta = b - a
        length_squared = delta.length_squared
        if length_squared <= 1e-12:
            return (point - a).length_squared
        factor = max(0.0, min(1.0, (point - a).dot(delta) / length_squared))
        return (point - (a + delta * factor)).length_squared
    helper_assigned = 0
    for vertex in body.data.vertices:
        if vertex.index in assigned:
            continue
        point = body.matrix_world @ vertex.co
        nearest = min(
            DEFORM_BONES,
            key=lambda name: distance_squared_to_segment(point, spans[name][0], spans[name][1]),
        )
        body.vertex_groups[nearest].add([vertex.index], 1.0, "REPLACE")
        helper_assigned += 1
    world = body.matrix_world.copy()
    body.parent = rig
    body.matrix_world = world
    modifier = body.modifiers.new("Aevrynd R603 Retargeted Armature", "ARMATURE")
    modifier.object = rig
    modifier.name = "Aevrynd R603 Retargeted Armature"
    bpy.data.objects.remove(proxy, do_unlink=True)
    return {"visibleProxyVertices": len(proxy_indices), "helperVerticesRigidAssigned": helper_assigned}


def normalize_deform_weights(body):
    deform_indices = {body.vertex_groups[name].index for name in DEFORM_BONES if body.vertex_groups.get(name)}
    changed = 0
    unweighted = []
    before = []
    for vertex in body.data.vertices:
        values = [(entry.group, entry.weight) for entry in vertex.groups if entry.group in deform_indices and entry.weight > 0.0]
        total = sum(weight for _group, weight in values)
        before.append(total)
        if total <= 1e-12:
            unweighted.append(vertex.index)
            continue
        for group_index, weight in values:
            body.vertex_groups[group_index].add([vertex.index], weight / total, "REPLACE")
        if abs(total - 1.0) > 1e-7:
            changed += 1
    if unweighted:
        raise RuntimeError(f"{len(unweighted)} unweighted body vertices; first={unweighted[:20]}")
    after = [
        sum(entry.weight for entry in vertex.groups if entry.group in deform_indices)
        for vertex in body.data.vertices
    ]
    return {
        "deformGroups": len(deform_indices),
        "vertices": len(body.data.vertices),
        "changed": changed,
        "beforeMin": min(before),
        "beforeMax": max(before),
        "afterMin": min(after),
        "afterMax": max(after),
        "unweighted": 0,
    }


def bind_eyes(rig):
    bound = []
    for side in ("L", "R"):
        for part in EYE_PARTS:
            obj = bpy.data.objects[f"Eye_{side}_{part}"]
            world = obj.matrix_world.copy()
            obj.parent = rig
            obj.parent_type = "BONE"
            obj.parent_bone = "head"
            obj.matrix_world = world
            obj["aevrynd_binding"] = "AevryndFemaleRig.head"
            bound.append(obj.name)
    return bound


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
body = bpy.data.objects[BODY]
rig = append_rig()
spans = fit_rig(rig, body)
weight_method = automatic_weights(body, rig, spans)
weights = normalize_deform_weights(body)
eyes = bind_eyes(rig)
body["aevrynd_revision"] = "v249r603"
body["aevrynd_weight_method"] = "retargeted Aevrynd rig plus Blender bone-heat weights and explicit normalization"
rig["aevrynd_revision"] = "v249r603"
rig["aevrynd_fit"] = "retargeted to MPFB CC0 joint marker groups without scaling the body"
scene["aevrynd_mainline_revision"] = "v249r603-cc0-retargeted-rig"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_rig_source"] = RIG_SOURCE.name
scene["aevrynd_release_state"] = "DEFORMATION_AND_DYNAMIC_COLLISION_AUDIT_PENDING"
scene.frame_set(1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
report = {
    "source": str(SOURCE),
    "rigSource": str(RIG_SOURCE),
    "output": str(OUTPUT),
    "bodyScale": list(body.scale),
    "bodyDimensions": list(body.dimensions),
    "retargetedBoneSpans": {
        name: {"head": list(head), "tail": list(tail)}
        for name, (head, tail) in spans.items()
    },
    "weightMethod": weight_method,
    "weights": weights,
    "eyesBound": eyes,
    "shapeKeysPreserved": len(body.data.shape_keys.key_blocks) if body.data.shape_keys else 0,
    "status": "DEFORMATION_AND_DYNAMIC_COLLISION_AUDIT_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R603_RETARGETED_RIG=" + json.dumps({
    "output": str(OUTPUT), "weights": weights, "eyes": len(eyes),
    "shapeKeys": report["shapeKeysPreserved"], "status": report["status"],
}, sort_keys=True))
