import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-delayed-clump-groom-r264.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-runtime-hair-rig-r265.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-runtime-hair-rig-r265.build-report.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r265-runtime-hair-rig"
RIG = "AevryndFemaleRig"
BODY = "AevryndFemaleBody_CC0_R249"
PRIMARY = "AevryndFemalePrimaryClumps_R264"
POINTS = 24
CHAINS = {
    "hair_dyn.L.front": (-0.082, -0.030),
    "hair_dyn.R.front": (0.082, -0.030),
    "hair_dyn.L.back": (-0.065, 0.060),
    "hair_dyn.C.back": (0.000, 0.078),
    "hair_dyn.R.back": (0.065, 0.060),
}
LEVELS = (1.675, 1.585, 1.495, 1.385)


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def smoothstep(edge0, edge1, value):
    t = clamp((value - edge0) / (edge1 - edge0))
    return t * t * (3.0 - 2.0 * t)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def add_chain_bones(rig):
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


def nearest_chain(point):
    candidates = []
    for name, (x, y) in CHAINS.items():
        penalty = 0.0
        if ".front" in name and point.y > 0.020:
            penalty = 0.018
        if ".back" in name and point.y < 0.000:
            penalty = 0.018
        candidates.append(((point.x - x) ** 2 + (point.y - y) ** 2 + penalty, name))
    return min(candidates)[1]


def level_weights(t):
    centers = (0.25, 0.58, 0.90)
    raw = [max(0.0, 1.0 - abs(t - center) / 0.40) for center in centers]
    total = sum(raw) or 1.0
    return [value / total for value in raw]


def card_material():
    material = bpy.data.materials.new("Aevrynd_RuntimeHairCards_R265")
    material.use_nodes = True
    shader = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    shader.inputs["Base Color"].default_value = (0.020, 0.0058, 0.0028, 1.0)
    shader.inputs["Roughness"].default_value = 0.43
    shader.inputs["Specular IOR Level"].default_value = 0.30
    material["aevrynd_layer"] = "material.hair.runtime_cards"
    material["aevrynd_ownership"] = "procedural in-project"
    return material


def build_cards(curves, rig):
    positions = [point.position.copy() for point in curves.data.points]
    curve_count = len(positions) // POINTS
    vertices = []
    faces = []
    assignments = []
    for curve_index in range(curve_count):
        strand = positions[curve_index * POINTS:(curve_index + 1) * POINTS]
        chain = nearest_chain(strand[0])
        for point_index, point in enumerate(strand):
            before = strand[max(0, point_index - 1)]
            after = strand[min(POINTS - 1, point_index + 1)]
            direction = (after - before).normalized()
            radial = Vector((point.x, point.y + 0.010, 0.0))
            if radial.length < 1e-5:
                radial = Vector((1.0, 0.0, 0.0))
            radial.normalize()
            side = direction.cross(radial)
            if side.length < 1e-5:
                side = direction.cross(Vector((0.0, 1.0, 0.0)))
            side.normalize()
            t = point_index / (POINTS - 1)
            width = 0.00175 * (1.0 - 0.72 * smoothstep(0.0, 1.0, t))
            vertices.extend((point - side * width, point + side * width))
            dynamic = smoothstep(0.08, 0.72, t)
            assignments.extend(((chain, t, dynamic), (chain, t, dynamic)))
        base = curve_index * POINTS * 2
        for point_index in range(POINTS - 1):
            a = base + point_index * 2
            faces.append((a, a + 1, a + 3, a + 2))
    mesh = bpy.data.meshes.new("AevryndFemaleRuntimeHairCardsTopology_R265")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(card_material())
    obj = bpy.data.objects.new("AevryndFemaleRuntimeHairCards_R265", mesh)
    bpy.context.scene.collection.objects.link(obj)
    head_group = obj.vertex_groups.new(name="head")
    for chain_name in CHAINS:
        for segment in range(3):
            obj.vertex_groups.new(name=f"{chain_name}.{segment + 1:02d}")
    chain_counts = {name: 0 for name in CHAINS}
    for vertex_index, (chain, t, dynamic) in enumerate(assignments):
        head_group.add([vertex_index], 1.0 - dynamic, "REPLACE")
        for segment, weight in enumerate(level_weights(t)):
            obj.vertex_groups[f"{chain}.{segment + 1:02d}"].add([vertex_index], dynamic * weight, "REPLACE")
        chain_counts[chain] += 1
    modifier = obj.modifiers.new("Aevrynd Hair Secondary Motion", "ARMATURE")
    modifier.object = rig
    obj["aevrynd_layer"] = "hair.runtime_cards.dynamic"
    obj["aevrynd_revision"] = "v249r265"
    obj["aevrynd_source_guides"] = PRIMARY
    obj["aevrynd_root_lock_fraction"] = 0.08
    return obj, curve_count, len(vertices), len(faces), chain_counts


def keyframe_motion(rig):
    fps, substeps, end = 30, 4, 61
    dt = 1.0 / (fps * substeps)
    knots = ((1, 0), (9, 14), (17, 28), (25, 7), (33, -22), (41, -9), (49, 4), (61, 0))
    def yaw_at(frame_time):
        for (f0, a0), (f1, a1) in zip(knots, knots[1:]):
            if frame_time <= f1:
                t = smoothstep(f0, f1, frame_time)
                return math.radians(a0 + (a1 - a0) * t)
        return 0.0
    states = {name: [[0.0, 0.0] for _ in range(3)] for name in CHAINS}
    previous_yaw = yaw_at(1.0)
    previous_velocity = 0.0
    rig.rotation_mode = "XYZ"
    for step in range((end - 1) * substeps + 1):
        frame_time = 1.0 + step / substeps
        yaw = yaw_at(frame_time)
        velocity = (yaw - previous_yaw) / dt if step else 0.0
        acceleration = (velocity - previous_velocity) / dt if step else 0.0
        previous_yaw, previous_velocity = yaw, velocity
        for chain_index, chain_name in enumerate(CHAINS):
            parent_angle = 0.0
            for segment in range(3):
                angle, angular_velocity = states[chain_name][segment]
                omega = math.tau * (4.4, 3.4, 2.6)[segment] * (0.97 + chain_index * 0.015)
                angular_acceleration = (-(omega * omega) * (angle - parent_angle * (0.08, 0.19, 0.28)[segment])
                                        - 2.0 * (0.84, 0.77, 0.70)[segment] * omega * angular_velocity
                                        - (0.18, 0.34, 0.52)[segment] * acceleration)
                angular_velocity += angular_acceleration * dt
                angle += angular_velocity * dt
                limit = math.radians((7.0, 12.0, 18.0)[segment])
                angle = clamp(angle, -limit, limit)
                states[chain_name][segment] = [angle, angular_velocity]
                parent_angle = angle
        if step % substeps == 0:
            frame = 1 + step // substeps
            rig.rotation_euler.z = yaw
            rig.keyframe_insert("rotation_euler", frame=frame)
            for chain_name in CHAINS:
                for segment in range(3):
                    bone = rig.pose.bones[f"{chain_name}.{segment + 1:02d}"]
                    angle = states[chain_name][segment][0]
                    bone.rotation_euler.x = abs(angle) * (0.06 if ".front" in chain_name else 0.10)
                    bone.rotation_euler.z = angle
                    bone.keyframe_insert("rotation_euler", frame=frame)
    rig["aevrynd_hair_bake_solver"] = "fixed-step-angular-spring-v2"
    rig["aevrynd_hair_bake_fixed_step_hz"] = 120


def render(camera, frame, name, location, target):
    scene = bpy.context.scene
    scene.frame_set(frame)
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    camera.location = location
    camera.data.lens = 82
    look_at(camera, target)
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
for obj in bpy.data.objects:
    if obj.animation_data:
        obj.animation_data_clear()
rig = bpy.data.objects[RIG]
add_chain_bones(rig)
cards, guide_count, vertex_count, face_count, chain_counts = build_cards(bpy.data.objects[PRIMARY], rig)
bpy.data.objects[PRIMARY].hide_render = True
keyframe_motion(rig)
colliders = [
    {"id": "head", "shape": "sphere", "bone": "head", "center": [0, -0.002, 1.64], "radius": 0.108},
    {"id": "neck", "shape": "capsule", "bone": "neck", "a": [0, 0.02, 1.43], "b": [0, 0.02, 1.56], "radius": 0.054},
    {"id": "shoulders", "shape": "capsule", "bone": "chest", "a": [-0.21, 0.02, 1.40], "b": [0.21, 0.02, 1.40], "radius": 0.070},
    {"id": "upper_chest", "shape": "capsule", "bone": "chest", "a": [-0.13, 0.02, 1.34], "b": [0.13, 0.02, 1.34], "radius": 0.088},
]
scene["aevrynd_hair_collision_manifest"] = json.dumps(colliders, separators=(",", ":"))
scene["aevrynd_hair_solver"] = "fixed-step angular spring v2; 120Hz; capsule collision contract"
scene["aevrynd_hair_layers"] = "primary_clumps.authoring|secondary_fill|flyaways|runtime_cards.dynamic"
scene["aevrynd_mainline_revision"] = "v249r265-runtime-hair-rig"
scene["aevrynd_release_state"] = "DYNAMIC_RUNTIME_PROXY_PENDING_COLLISION_AUDIT"
scene.frame_start, scene.frame_end, scene.render.fps = 1, 61, 30
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 800
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
for frame in (1, 17, 25, 33, 41, 61):
    render(camera, frame, f"front-f{frame:02d}", (0.0, -0.90, 1.59), (0.0, -0.01, 1.56))
for frame in (1, 17, 33, 41, 61):
    render(camera, frame, f"back-f{frame:02d}", (0.0, 0.90, 1.59), (0.0, 0.01, 1.56))
scene.frame_set(1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE), "output": str(OUTPUT), "authoringPrimaryGuides": guide_count,
    "runtimeCards": {"vertices": vertex_count, "faces": face_count, "chainVertexCounts": chain_counts},
    "dynamicChains": len(CHAINS), "dynamicSegments": len(CHAINS) * 3,
    "fixedStepHz": 120, "frames": [1, 17, 25, 33, 41, 61], "colliders": colliders,
    "layers": ["hair.primary_clumps.authoring", "hair.secondary_fill", "hair.flyaways", "hair.runtime_cards.dynamic"],
    "renderDirectory": str(RENDER_DIR), "status": "DYNAMIC_RUNTIME_PROXY_PENDING_COLLISION_AUDIT",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R265_RUNTIME_HAIR_RIG=" + json.dumps(report, sort_keys=True))
