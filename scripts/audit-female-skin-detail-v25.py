import hashlib
import json
import math
import struct
import sys

import bpy


def input_paths():
    if "--" not in sys.argv:
        raise SystemExit("usage: blender --background --python audit-female-skin-detail-v25.py -- baseline.blend candidate.blend")
    values = sys.argv[sys.argv.index("--") + 1:]
    if len(values) != 2:
        raise SystemExit("expected baseline and candidate Blender files")
    return values


def feed_floats(digest, values):
    for value in values:
        digest.update(struct.pack("<d", float(value)))


def mesh_signatures():
    result = {}
    for obj in sorted((item for item in bpy.data.objects if item.type == "MESH"), key=lambda item: item.name):
        digest = hashlib.sha256()
        feed_floats(digest, [value for row in obj.matrix_world for value in row])
        for vertex in obj.data.vertices:
            feed_floats(digest, vertex.co)
        for polygon in obj.data.polygons:
            digest.update(struct.pack("<I", len(polygon.vertices)))
            for index in polygon.vertices:
                digest.update(struct.pack("<I", index))
        digest.update((obj.parent.name if obj.parent else "").encode())
        digest.update(obj.parent_bone.encode())
        result[obj.name] = {
            "vertices": len(obj.data.vertices),
            "faces": len(obj.data.polygons),
            "digest": digest.hexdigest(),
        }
    return result


def rig_signature():
    rig = bpy.data.objects["AevryndFemaleRig"]
    digest = hashlib.sha256()
    for bone in sorted(rig.data.bones, key=lambda item: item.name):
        digest.update(bone.name.encode())
        digest.update((bone.parent.name if bone.parent else "").encode())
        feed_floats(digest, bone.head_local)
        feed_floats(digest, bone.tail_local)
        digest.update(bytes([int(bone.use_deform)]))
    action = rig.animation_data.action if rig.animation_data else None
    action_summary = None
    if action:
        action_summary = {
            "name": action.name,
            "frame_range": [float(value) for value in action.frame_range],
            "slots": len(action.slots),
            "layers": len(action.layers),
        }
        digest.update(json.dumps(action_summary, sort_keys=True).encode())
    return {"bones": len(rig.data.bones), "action": action_summary, "digest": digest.hexdigest()}


baseline_path, candidate_path = input_paths()
bpy.ops.wm.open_mainfile(filepath=baseline_path)
baseline_meshes = mesh_signatures()
baseline_rig = rig_signature()

bpy.ops.wm.open_mainfile(filepath=candidate_path)
candidate_meshes = mesh_signatures()
candidate_rig = rig_signature()
failures = []
if baseline_meshes != candidate_meshes:
    failures.append("candidate geometry, transforms, parenting, or topology differ from collision-approved v21")
if baseline_rig != candidate_rig:
    failures.append("candidate rig or animation differs from collision-approved v21")

scene = bpy.context.scene
body = bpy.data.objects["AevryndFemaleBodyBase"]
material = bpy.data.materials["Aevrynd_Skin_Clay"]
nodes = material.node_tree.nodes
links = material.node_tree.links
attribute = body.data.color_attributes.get("AevryndSkinTone")
if scene.get("aevrynd_skin_revision") != 25:
    failures.append("skin revision is not 25")
if not attribute or attribute.domain != "POINT":
    failures.append("AevryndSkinTone point attribute is missing")

colors = [tuple(item.color_srgb) for item in attribute.data] if attribute else []
color_report = {
    "minimum": [min(color[channel] for color in colors) for channel in range(3)] if colors else [],
    "maximum": [max(color[channel] for color in colors) for channel in range(3)] if colors else [],
    "average": [sum(color[channel] for color in colors) / len(colors) for channel in range(3)] if colors else [],
    "unique_rgb": len({tuple(round(color[channel], 4) for channel in range(3)) for color in colors}),
}
if colors and (color_report["unique_rgb"] < 20 or color_report["minimum"][2] > 0.94):
    failures.append("skin tone variation is missing or too weak")

def linked(from_node, from_socket, to_node, to_socket):
    return any(
        link.from_node.name == from_node and link.from_socket.name == from_socket
        and link.to_node.name == to_node and link.to_socket.name == to_socket
        for link in links
    )

required_links = [
    ("Aevrynd Runtime Normal Map", "Normal", "Aevrynd Skin Micro Bump", "Normal"),
    ("Aevrynd Skin Micro Bump", "Normal", "Principled BSDF", "Normal"),
    ("Aevrynd Pore Roughness v25", "Factor", "Aevrynd Roughness Range v25", "Value"),
    ("Aevrynd Roughness Add v25", "Value", "Principled BSDF", "Roughness"),
]
missing_links = [entry for entry in required_links if not linked(*entry)]
if missing_links:
    failures.append(f"skin shader links missing: {missing_links}")

non_finite = sum(
    1 for obj in bpy.data.objects if obj.type == "MESH"
    for vertex in obj.data.vertices if not all(math.isfinite(value) for value in vertex.co)
)
if non_finite:
    failures.append(f"candidate contains {non_finite} non-finite mesh vertices")

report = {
    "geometry_matches_v21": baseline_meshes == candidate_meshes,
    "mesh_objects": len(candidate_meshes),
    "rig_matches_v21": baseline_rig == candidate_rig,
    "rig": candidate_rig,
    "skin_colors": color_report,
    "shader_links_verified": len(required_links) - len(missing_links),
    "non_finite_vertices": non_finite,
}
print("AEVRYND_SKIN_DETAIL_V25_AUDIT=" + json.dumps(report))
if failures:
    raise SystemExit("; ".join(failures))
