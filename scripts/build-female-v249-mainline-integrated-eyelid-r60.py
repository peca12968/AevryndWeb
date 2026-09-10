import json
import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-face-r38.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-integrated-eyelid-r60.blend"
OUT = ROOT.parent / "Temp/female-realism/v249-mainline-integrated-eyelid-r60"
OUT.mkdir(parents=True, exist_ok=True)
BODY = "AevryndFemaleBodyBaseV118"
EYES = {"L": (0.034528, -0.10087, 1.607765), "R": (-0.034443, -0.10077, 1.607765)}
GLOBES = {
    "L": {"center": (0.0345275, -0.1003675, 1.6077619), "radii": (0.0109505, 0.0121000, 0.0116765)},
    "R": {"center": (-0.0344431, -0.1001710, 1.6077617), "radii": (0.0108295, 0.0121000, 0.0116765)},
}


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def ellipse(point, center, width=0.0140, upper=0.00560, lower=0.00420):
    dx = (point.x - center[0]) / width
    height = upper if point.z >= center[2] else lower
    dz = (point.z - center[2]) / height
    return dx * dx + dz * dz


def globe_front_y(side, x, z):
    cx, cy, cz = GLOBES[side]["center"]
    rx, ry, rz = GLOBES[side]["radii"]
    radius_term = max(0.012, 1.0 - ((x - cx) / rx) ** 2 - ((z - cz) / rz) ** 2)
    return cy - ry * math.sqrt(radius_term)


def ordered_boundary(edges):
    all_adjacency = {}
    for edge in edges:
        first, second = edge.verts
        all_adjacency.setdefault(first, []).append(second)
        all_adjacency.setdefault(second, []).append(first)
    components = []
    remaining = set(all_adjacency)
    while remaining:
        seed = remaining.pop()
        component = {seed}
        stack = [seed]
        while stack:
            current = stack.pop()
            for neighbor in all_adjacency[current]:
                if neighbor not in component:
                    component.add(neighbor)
                    remaining.discard(neighbor)
                    stack.append(neighbor)
        components.append(component)
    chosen = max(components, key=len)
    adjacency = {
        vertex: [neighbor for neighbor in all_adjacency[vertex] if neighbor in chosen]
        for vertex in chosen
    }
    invalid = {vertex.index: len(neighbors) for vertex, neighbors in adjacency.items() if len(neighbors) != 2}
    if invalid:
        raise RuntimeError(f"Eye boundary is not a single manifold cycle: {invalid}")
    start = min(adjacency, key=lambda vertex: (vertex.co.x, vertex.co.z))
    result = [start]
    previous = None
    current = start
    while True:
        candidates = [neighbor for neighbor in adjacency[current] if neighbor is not previous]
        following = candidates[0]
        if following is start:
            break
        if following in result:
            raise RuntimeError("Eye boundary traversal closed on the wrong vertex")
        result.append(following)
        previous, current = current, following
    if len(result) != len(adjacency):
        raise RuntimeError(f"Eye boundary traversal missed vertices: {len(result)} != {len(adjacency)}")
    return result, sorted((len(component) for component in components), reverse=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
body = bpy.data.objects[BODY]
body.data = body.data.copy()

lid_material = body.data.materials[0].copy()
lid_material.name = "Aevrynd_EyelidSkin_r60"
principled = next(node for node in lid_material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
for input_name in ("Base Color", "Roughness", "Normal"):
    socket = principled.inputs[input_name]
    for link in tuple(socket.links):
        lid_material.node_tree.links.remove(link)
principled.inputs["Base Color"].default_value = (0.405, 0.247, 0.202, 1.0)
principled.inputs["Roughness"].default_value = 0.46
body.data.materials.append(lid_material)
lid_material_index = len(body.data.materials) - 1

bm = bmesh.new()
bm.from_mesh(body.data)
bm.faces.ensure_lookup_table()
deleted = {}
for side, center in EYES.items():
    faces = [
        face for face in bm.faces
        if face.calc_center_median().y < -0.090 and ellipse(face.calc_center_median(), center) < 1.0
    ]
    deleted[side] = len(faces)
    bmesh.ops.delete(bm, geom=faces, context="FACES")

deform_layer = bm.verts.layers.deform.verify()
head_group = body.vertex_groups.get("head")
if head_group is None:
    raise RuntimeError("Body has no head deformation group")

topology = {}
for side, center in EYES.items():
    boundary_edges = []
    for edge in bm.edges:
        if len(edge.link_faces) != 1:
            continue
        midpoint = (edge.verts[0].co + edge.verts[1].co) * 0.5
        if abs(midpoint.x - center[0]) < 0.021 and abs(midpoint.z - center[2]) < 0.012:
            boundary_edges.append(edge)
    outer, boundary_components = ordered_boundary(boundary_edges)
    mid = []
    margin = []
    back = []
    lateral_sign = 1.0 if side == "L" else -1.0
    for outer_vertex in outer:
        normalized_x = (outer_vertex.co.x - center[0]) / 0.0140
        normalized_z = (outer_vertex.co.z - center[2]) / (
            0.00560 if outer_vertex.co.z >= center[2] else 0.00420
        )
        theta = math.atan2(normalized_z, normalized_x)
        sine = math.sin(theta)
        cosine = math.cos(theta)
        inner_height = 0.00360 if sine >= 0.0 else 0.00265
        inner_x = center[0] + 0.00990 * cosine
        inner_z = center[2] + inner_height * sine + lateral_sign * 0.023 * (inner_x - center[0])
        inner_y = globe_front_y(side, inner_x, inner_z) - 0.00018
        margin_point = Vector((inner_x, inner_y, inner_z))
        mid_point = outer_vertex.co.lerp(margin_point, 0.56)
        mid_point.y -= 0.00016
        mid_vertex = bm.verts.new(mid_point)
        margin_vertex = bm.verts.new(margin_point)
        back_point = margin_point.copy()
        back_point.x = center[0] + (back_point.x - center[0]) * 0.992
        back_point.z = center[2] + (back_point.z - center[2]) * 0.982
        back_point.y += 0.00032
        back_vertex = bm.verts.new(back_point)
        for vertex in (mid_vertex, margin_vertex, back_vertex):
            vertex[deform_layer][head_group.index] = 1.0
        mid.append(mid_vertex)
        margin.append(margin_vertex)
        back.append(back_vertex)

    new_faces = []
    for first_ring, second_ring in ((outer, mid), (mid, margin), (margin, back)):
        for index in range(len(outer)):
            following = (index + 1) % len(outer)
            face = bm.faces.new((
                first_ring[index], first_ring[following],
                second_ring[following], second_ring[index],
            ))
            face.material_index = lid_material_index
            face.smooth = True
            new_faces.append(face)
    bm.normal_update()
    for face in new_faces:
        if face.normal.y > 0.0:
            face.normal_flip()
    topology[side] = {
        "boundary_vertices": len(outer),
        "boundary_components": boundary_components,
        "new_vertices": len(mid) + len(margin) + len(back),
        "new_faces": len(new_faces),
    }

bm.normal_update()
bm.to_mesh(body.data)
bm.free()
body.data.update()

for side in EYES:
    for part in ("UpperLashes", "LowerLashes", "TearMeniscus"):
        accessory = bpy.data.objects.get(f"Eye_{side}_{part}")
        if accessory is not None:
            accessory.hide_render = True
            accessory["aevrynd_retired_for_revision"] = "v249-mainline-integrated-eyelid-r60"

body["aevrynd_mainline_baseline"] = "v249"
body["aevrynd_face_revision"] = "v249-mainline-integrated-eyelid-r60"
body["aevrynd_eye_topology"] = "body-integrated boundary/mid/margin/tarsal quad rings"
scene = bpy.context.scene
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_mainline_revision"] = "integrated-eyelid-r60"
scene["aevrynd_release_state"] = "R60_STRICT_VISUAL_REVIEW_REQUIRED"

scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1100
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
camera = bpy.data.objects["Aevrynd Review Camera"]
views = (
    ("01-eye-close", (0.0, -0.47, 1.610), (0.0, -0.065, 1.608), 112),
    ("02-face-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
    ("03-face-three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88),
)
for name, location, target, lens in views:
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)

report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "deleted_body_faces": deleted,
    "topology": topology,
    "integrated_into_body_mesh": True,
    "visible_aperture_width_mm": 19.8,
    "visible_aperture_upper_mm": 3.60,
    "visible_aperture_lower_mm": 2.65,
    "tarsal_depth_mm": 0.32,
    "status": "STRICT_VISUAL_REVIEW_REQUIRED",
}
(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249_INTEGRATED_EYELID_R60=" + json.dumps(report, sort_keys=True))
