"""Separate lip-edge geometry, micro-bump and specular causes under asymmetric light."""
import hashlib
import json
import math
import struct
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-commissure-falloff-r1074-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1075-lip-edge-lighting.diagnostic.json"
OUT = ROOT.parent / "Temp/female-realism/v249r1075-lip-edge-lighting"
BODY = "AevryndFemaleCC0CommissureFalloff_R1074"
ATTRIBUTE = "aevrynd_inner_rim_r1074"
OPEN_KEY = "Aevrynd_MouthOpenTest_R1030"
SMILE_KEY = "Aevrynd_SmileTest_R1030"
MODES = ("a-current", "b-no-micro-bump", "c-matte-no-bump")
SIDES = ("left-key", "right-key")
POSES = ("neutral", "smile")


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def digest_geometry(body):
    digest = hashlib.sha256()
    for block in body.data.shape_keys.key_blocks:
        digest.update(block.name.encode("utf-8"))
        for item in block.data:
            digest.update(struct.pack("<3f", item.co.x, item.co.y, item.co.z))
    return digest.hexdigest()


def digest_weights(body):
    digest = hashlib.sha256()
    for vertex in body.data.vertices:
        for group in sorted(vertex.groups, key=lambda item: item.group):
            digest.update(struct.pack("<If", group.group, group.weight))
    return digest.hexdigest()


def active_coordinates(body, smile):
    blocks = body.data.shape_keys.key_blocks
    coords = [item.co.copy() for item in blocks[0].data]
    for block in blocks[1:]:
        if block.mute:
            continue
        value = 1.0 if block.name == SMILE_KEY and smile else (0.0 if block.name in (SMILE_KEY, OPEN_KEY) else block.value)
        if abs(value) < 1e-8:
            continue
        for index, item in enumerate(block.data):
            coords[index] += value * (item.co - block.relative_key.data[index].co)
    return coords


def curvature_metrics(body, smile):
    coords = active_coordinates(body, smile)
    vertex_faces = [[] for _ in body.data.vertices]
    face_normals = []
    for poly in body.data.polygons:
        vertices = list(poly.vertices)
        origin = coords[vertices[0]]
        normal = Vector((0.0, 0.0, 0.0))
        for index in range(1, len(vertices) - 1):
            normal += (coords[vertices[index]] - origin).cross(coords[vertices[index + 1]] - origin)
        if normal.length_squared > 1e-20:
            normal.normalize()
        face_normals.append(normal)
        for vertex in vertices:
            vertex_faces[vertex].append(poly.index)

    mask = body.data.attributes[ATTRIBUTE].data
    regions = {"central": [], "commissure": []}
    records = {"central": [], "commissure": []}
    for vertex in body.data.vertices:
        if mask[vertex.index].value <= 0.05:
            continue
        world = body.matrix_world @ coords[vertex.index]
        region = "commissure" if abs(world.x) > 0.014 else "central"
        normals = [face_normals[index] for index in vertex_faces[vertex.index] if face_normals[index].length_squared > 0.5]
        if len(normals) < 2:
            continue
        mean = sum(normals, Vector()).normalized()
        spread = max(math.degrees(mean.angle(normal)) for normal in normals)
        regions[region].append(spread)
        records[region].append({
            "vertexIndex": vertex.index,
            "worldCoordinate": [float(value) for value in world],
            "maskWeight": float(mask[vertex.index].value),
            "adjacentFaces": len(normals),
            "normalSpreadDeg": spread,
        })

    result = {}
    for name, values in regions.items():
        ordered = sorted(values)
        percentile = lambda fraction: ordered[min(len(ordered) - 1, int(round((len(ordered) - 1) * fraction)))]
        result[name] = {
            "vertices": len(values),
            "meanAdjacentFaceNormalSpreadDeg": sum(values) / len(values),
            "p95AdjacentFaceNormalSpreadDeg": percentile(0.95),
            "maximumAdjacentFaceNormalSpreadDeg": max(values),
            "highestSpreadVertices": sorted(records[name], key=lambda item: item["normalSpreadDeg"], reverse=True)[:8],
        }
    return result


def set_pose(body, pose):
    keys = body.data.shape_keys.key_blocks
    keys[OPEN_KEY].value = 0.0
    keys[SMILE_KEY].value = 1.0 if pose == "smile" else 0.0


def render(scene, label, oblique=False):
    camera = scene.camera
    camera.data.lens = 135
    camera.location = ((-0.105 if oblique else 0.0), -0.43, 1.391)
    look_at(camera, (0.0, -0.115, 1.386))
    scene.render.resolution_x, scene.render.resolution_y = 1100, 720
    scene.render.resolution_percentage = 100
    path = OUT / f"{label}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return str(path)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
body = bpy.data.objects[BODY]
OUT.mkdir(parents=True, exist_ok=True)
for obj in scene.objects:
    name = obj.name.lower()
    if obj.type == "CURVES" or any(token in name for token in ("groom", "scalp", "haircard", "hairfiber")):
        if not any(token in name for token in ("brow", "lash")):
            obj.hide_render = True

material = body.data.materials[0]
nodes, links = material.node_tree.nodes, material.node_tree.links
shader = next(node for node in nodes if node.bl_idname == "ShaderNodeBsdfPrincipled")
bump = next(node for node in nodes if node.bl_idname == "ShaderNodeBump")
roughness, specular = shader.inputs["Roughness"], shader.inputs["Specular IOR Level"]
rough_source = roughness.links[0].from_socket
specular_source = specular.links[0].from_socket
base_bump_strength = bump.inputs["Strength"].default_value
lights = {obj.name: obj for obj in scene.objects if obj.type == "LIGHT"}
key, fill, rim = lights["Aevrynd Key"], lights["Aevrynd Fill"], lights["Aevrynd Rim"]
rim.data.energy = 0.0


def ensure_link(source, target):
    for link in list(target.links):
        links.remove(link)
    links.new(source, target)


renders = []
for side in SIDES:
    if side == "left-key":
        key.data.energy, fill.data.energy = 1350.0, 90.0
    else:
        key.data.energy, fill.data.energy = 90.0, 1350.0
    for pose in POSES:
        set_pose(body, pose)
        for mode in MODES:
            if mode == "a-current":
                bump.inputs["Strength"].default_value = base_bump_strength
                ensure_link(rough_source, roughness)
                ensure_link(specular_source, specular)
            elif mode == "b-no-micro-bump":
                bump.inputs["Strength"].default_value = 0.0
                ensure_link(rough_source, roughness)
                ensure_link(specular_source, specular)
            else:
                bump.inputs["Strength"].default_value = 0.0
                for socket in (roughness, specular):
                    for link in list(socket.links):
                        links.remove(link)
                roughness.default_value, specular.default_value = 1.0, 0.0
            renders.append({"side": side, "pose": pose, "mode": mode, "front": render(scene, f"{side}-{pose}-{mode}-front")})
        # Current material gets an extra oblique diagnostic for each pose/side.
        bump.inputs["Strength"].default_value = base_bump_strength
        ensure_link(rough_source, roughness)
        ensure_link(specular_source, specular)
        renders.append({"side": side, "pose": pose, "mode": "a-current", "oblique": render(scene, f"{side}-{pose}-a-current-oblique", oblique=True)})

set_pose(body, "neutral")
report = {
    "revision": "v249r1075-lip-edge-lighting-diagnostic",
    "source": str(SOURCE),
    "method": "asymmetric left/right key lighting crossed with neutral/smile pose and current/no-bump/matte-no-bump material isolation",
    "baseMicroBumpStrength": base_bump_strength,
    "baseMicroBumpDistanceMm": bump.inputs["Distance"].default_value * 1000.0,
    "geometryDigest": digest_geometry(body), "weightDigest": digest_weights(body),
    "curvature": {"neutral": curvature_metrics(body, False), "smile": curvature_metrics(body, True)},
    "renders": renders,
    "modelModified": False, "websitePromotionApproved": False,
    "diagnosticStatus": "IMAGE_AND_PIXEL_AUDIT_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1075_LIGHTING=" + json.dumps({"curvature": report["curvature"], "renders": len(renders)}, sort_keys=True))
