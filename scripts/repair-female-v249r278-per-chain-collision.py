import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-dense-layered-hair-cards-r276.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-per-chain-collision-r278.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-per-chain-collision-r278.build-report.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r278-per-chain-collision"
BODY = "AevryndFemaleBody_CC0_R249"
RIG = "AevryndFemaleRig"
CARDS = "AevryndFemaleRuntimeHairCards_R276"
POINTS = 24
STRIDE = POINTS * 2


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def body_tree():
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    evaluated = bpy.data.objects[BODY].evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(points, faces, all_triangles=False)


def penetration(cards, tree):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    evaluated = cards.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    minimum, penetrating = math.inf, []
    for vertex in mesh.vertices:
        if vertex.index % STRIDE < 6:
            continue
        world = evaluated.matrix_world @ vertex.co
        hit = tree.find_nearest(world, 0.20)
        if hit is None or hit[1] is None:
            continue
        signed = (world - hit[0]).dot(hit[1].normalized())
        minimum = min(minimum, signed)
        if signed < 0.0:
            penetrating.append(vertex.index)
    evaluated.to_mesh_clear()
    return penetrating, minimum if math.isfinite(minimum) else None


def vertex_chains(cards):
    group_names = {group.index: group.name for group in cards.vertex_groups}
    result = {}
    for vertex in cards.data.vertices:
        candidates = []
        for membership in vertex.groups:
            name = group_names[membership.group]
            if name.startswith("hair_dyn."):
                candidates.append((membership.weight, name.rsplit(".", 1)[0]))
        result[vertex.index] = max(candidates)[1] if candidates else None
    return result


def collision_clamp(scene, rig, cards):
    bone_names = [bone.name for bone in rig.pose.bones if bone.name.startswith("hair_dyn.")]
    chains = sorted({name.rsplit(".", 1)[0] for name in bone_names})
    candidates = (0.94, 0.88, 0.82, 0.74, 0.66, 0.56, 0.46, 0.34, 0.22, 0.10, 0.0)
    ownership = vertex_chains(cards)
    results = {}
    for frame in range(scene.frame_start, scene.frame_end + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        raw = {name: rig.pose.bones[name].rotation_euler.copy() for name in bone_names}
        tree = body_tree()
        chain_scales = {chain: 1.0 for chain in chains}

        def apply_scales():
            for name in bone_names:
                bone = rig.pose.bones[name]
                scale = chain_scales[name.rsplit(".", 1)[0]]
                bone.rotation_euler = tuple(value * scale for value in raw[name])
            bpy.context.view_layer.update()

        apply_scales()
        penetrating, final_minimum = penetration(cards, tree)
        for _ in range(12):
            if not penetrating:
                break
            counts = {chain: 0 for chain in chains}
            for index in penetrating:
                if ownership[index]:
                    counts[ownership[index]] += 1
            affected = [chain for chain in chains if counts[chain]]
            if not affected:
                break
            improved = False
            for chain in sorted(affected, key=lambda name: counts[name], reverse=True):
                old_scale = chain_scales[chain]
                old_count = len(penetrating)
                best = (old_count, old_scale, penetrating, final_minimum)
                for candidate in candidates:
                    if candidate >= old_scale:
                        continue
                    chain_scales[chain] = candidate
                    apply_scales()
                    trial, trial_minimum = penetration(cards, tree)
                    score = (sum(1 for index in trial if ownership[index] == chain), len(trial))
                    best_score = (sum(1 for index in best[2] if ownership[index] == chain), best[0])
                    if score < best_score:
                        best = (len(trial), candidate, trial, trial_minimum)
                    if score[0] == 0:
                        break
                chain_scales[chain] = best[1]
                penetrating, final_minimum = best[2], best[3]
                apply_scales()
                improved = improved or best[0] < old_count
                if not penetrating:
                    break
            if not improved:
                break
        for name in bone_names:
            rig.pose.bones[name].keyframe_insert("rotation_euler", frame=frame)
        results[str(frame)] = {
            "chainScales": chain_scales, "penetratingVertices": len(penetrating),
            "minimumSignedM": final_minimum, "sample": penetrating[:24],
        }
    return results


def render(camera, frame, name, location):
    scene = bpy.context.scene
    scene.frame_set(frame)
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    camera.location = location
    camera.data.lens = 82
    look_at(camera, (0.0, 0.0, 1.56))
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
rig = bpy.data.objects[RIG]
cards = bpy.data.objects[CARDS]
collision = collision_clamp(scene, rig, cards)
remaining = sum(item["penetratingVertices"] for item in collision.values())
minimum_scale = min(scale for item in collision.values() for scale in item["chainScales"].values())
cards["aevrynd_revision"] = "v249r278"
scene["aevrynd_mainline_revision"] = "v249r278-per-chain-collision"
scene["aevrynd_release_state"] = "PER_CHAIN_COLLISION_CLAMPED_PENDING_INDEPENDENT_AUDIT"
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 800
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
for frame, name, location in (
    (1, "front-f01", (0.0, -0.90, 1.59)), (33, "front-f33", (0.0, -0.90, 1.59)),
    (1, "left-f01", (-0.72, -0.55, 1.59)), (1, "right-f01", (0.72, -0.55, 1.59)),
    (1, "back-f01", (0.0, 0.90, 1.59)), (33, "back-f33", (0.0, 0.90, 1.59)),
):
    render(camera, frame, name, location)
scene.frame_set(1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE), "output": str(OUTPUT), "cardObject": CARDS,
    "frames": [1, 17, 25, 33, 41, 61], "collisionClamp": collision,
    "remainingPenetratingVertexFrames": remaining, "minimumAngleScale": minimum_scale,
    "geometryChanged": False, "materialChanged": False, "ownedAssetOnly": True,
    "renderDirectory": str(RENDER_DIR),
    "status": "COLLISION_CLAMPED_PENDING_INDEPENDENT_AUDIT" if remaining == 0 else "COLLISION_CLAMP_FAILED",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R278_PER_CHAIN_COLLISION=" + json.dumps(report, sort_keys=True))
if remaining:
    raise SystemExit(2)

