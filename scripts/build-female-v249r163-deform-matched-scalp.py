import json
from collections import defaultdict, deque
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-curly-collision-prune-r162.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-deform-matched-scalp-r163.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-deform-matched-scalp-r163.build-report.json"
BODY = "AevryndFemaleBodyBaseV118"
REGION_GUIDE = "AevryndFemaleAnatomicalScalpFoundation_v249r101"
SCALP = "AevryndFemaleDeformMatchedScalp_v249r163"
RIG = "AevryndFemaleRig"
REGION_DISTANCE = 0.006
CLEARANCE = 0.0012


def evaluated_mesh_data(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [vertex.co.copy() for vertex in mesh.vertices]
    normals = [vertex.normal.copy() for vertex in mesh.vertices]
    faces = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return vertices, normals, faces


def evaluated_world_tree(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, faces, all_triangles=False)


def boundary_distance(vertex_count, faces):
    edge_faces = defaultdict(int)
    neighbors = [set() for _ in range(vertex_count)]
    for face in faces:
        for index in range(len(face)):
            a, b = face[index], face[(index + 1) % len(face)]
            edge = (min(a, b), max(a, b))
            edge_faces[edge] += 1
            neighbors[a].add(b)
            neighbors[b].add(a)
    boundary = set()
    for (a, b), count in edge_faces.items():
        if count == 1:
            boundary.add(a)
            boundary.add(b)
    distance = [999] * vertex_count
    queue = deque()
    for index in boundary:
        distance[index] = 0
        queue.append(index)
    while queue:
        current = queue.popleft()
        if distance[current] >= 8:
            continue
        for neighbor in neighbors[current]:
            if distance[neighbor] > distance[current] + 1:
                distance[neighbor] = distance[current] + 1
                queue.append(neighbor)
    return distance, len(boundary)


def make_material():
    material = bpy.data.materials.new("AevryndDeformMatchedScalpMaterial_v249r163")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    attribute = nodes.new("ShaderNodeAttribute")
    attribute.attribute_name = "aevrynd_root_density"
    texcoord = nodes.new("ShaderNodeTexCoord")
    noise = nodes.new("ShaderNodeTexNoise")
    noise.noise_dimensions = "3D"
    noise.inputs["Scale"].default_value = 165.0
    noise.inputs["Detail"].default_value = 2.5
    noise.inputs["Roughness"].default_value = 0.62
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.28
    ramp.color_ramp.elements[0].color = (0.46, 0.46, 0.46, 1.0)
    ramp.color_ramp.elements[1].position = 0.72
    ramp.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
    multiply = nodes.new("ShaderNodeMath")
    multiply.operation = "MULTIPLY"
    shader.inputs["Base Color"].default_value = (0.018, 0.0055, 0.0028, 1.0)
    shader.inputs["Roughness"].default_value = 0.78
    shader.inputs["Specular IOR Level"].default_value = 0.20
    links.new(texcoord.outputs["Generated"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(attribute.outputs["Fac"], multiply.inputs[0])
    links.new(ramp.outputs["Color"], multiply.inputs[1])
    links.new(multiply.outputs["Value"], shader.inputs["Alpha"])
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    if hasattr(material, "surface_render_method"):
        material.surface_render_method = "DITHERED"
    material["aevrynd_revision"] = "v249r163"
    material["aevrynd_runtime_dependency"] = "none"
    return material


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
body = bpy.data.objects[BODY]
guide = bpy.data.objects[REGION_GUIDE]
guide.hide_viewport = False
guide.hide_set(False)
guide_tree = evaluated_world_tree(guide)

armature_modifiers = [modifier for modifier in body.modifiers if modifier.type == "ARMATURE"]
modifier_states = [(modifier, modifier.show_viewport, modifier.show_render) for modifier in armature_modifiers]
for modifier, _, _ in modifier_states:
    modifier.show_viewport = False
    modifier.show_render = False
bpy.context.view_layer.update()
vertices, normals, faces = evaluated_mesh_data(body)
for modifier, viewport, render in modifier_states:
    modifier.show_viewport = viewport
    modifier.show_render = render
bpy.context.view_layer.update()

selected_faces = []
for face in faces:
    center_local = sum((vertices[index] for index in face), Vector()) / len(face)
    center_world = body.matrix_world @ center_local
    hit = guide_tree.find_nearest(center_world)
    # The concave temple/ear transition can make an averaged vertex normal point
    # through an adjacent body triangle. Keep the scalp shell above that crease;
    # the visible curl silhouette covers this lower boundary.
    touches_temple_crease = any(
        abs(vertices[index].x) > 0.068
        and vertices[index].z < 1.595
        and -0.055 < vertices[index].y < 0.005
        for index in face
    )
    if hit is not None and hit[3] <= REGION_DISTANCE and not touches_temple_crease:
        selected_faces.append(face)

used_source_indices = sorted({index for face in selected_faces for index in face})
source_to_target = {source: target for target, source in enumerate(used_source_indices)}
target_vertices = [vertices[index] + normals[index] * CLEARANCE for index in used_source_indices]
target_faces = [tuple(source_to_target[index] for index in face) for face in selected_faces]
mesh = bpy.data.meshes.new(SCALP + "Data")
mesh.from_pydata(target_vertices, [], target_faces)
mesh.update()
scalp = bpy.data.objects.new(SCALP, mesh)
scene.collection.objects.link(scalp)
scalp.matrix_world = body.matrix_world.copy()

for source_group in body.vertex_groups:
    scalp.vertex_groups.new(name=source_group.name)
for target_index, source_index in enumerate(used_source_indices):
    for assignment in body.data.vertices[source_index].groups:
        group_name = body.vertex_groups[assignment.group].name
        scalp.vertex_groups[group_name].add([target_index], assignment.weight, "REPLACE")

armature = scalp.modifiers.new("Aevrynd Scalp Body-Matched Deform", "ARMATURE")
armature.object = bpy.data.objects[RIG]
armature.use_vertex_groups = True
armature.use_deform_preserve_volume = True
world = scalp.matrix_world.copy()
scalp.parent = body.parent
scalp.matrix_parent_inverse = body.matrix_parent_inverse.copy()
scalp.matrix_world = world

distances, boundary_count = boundary_distance(len(target_vertices), target_faces)
density = mesh.attributes.new("aevrynd_root_density", "FLOAT", "POINT")
for index, rings in enumerate(distances):
    t = min(1.0, rings / 7.0)
    density.data[index].value = 0.04 + 0.88 * t * t * (3.0 - 2.0 * t)
mesh.materials.append(make_material())

guide.hide_render = True
guide.hide_viewport = True
scalp["aevrynd_layer"] = "hair.scalp.foundation"
scalp["aevrynd_revision"] = "v249r163"
scalp["aevrynd_source"] = "Aevrynd body-matched scalp shell with copied skin weights"
scalp["aevrynd_runtime_dependency"] = "none"
scalp["aevrynd_collision_clearance_m"] = CLEARANCE
scalp["aevrynd_collision_status"] = "PENDING_STRICT_AUDIT"
scene["aevrynd_revision"] = "v249r163"
scene["aevrynd_candidate_status"] = "COLLISION_AND_VISUAL_REVIEW_PENDING"
scene["aevrynd_hair_layers"] = ["hair.scalp.foundation", "hair.follow.curly.main"]
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "source": str(SOURCE), "output": str(OUTPUT),
    "object": SCALP, "layer": "hair.scalp.foundation",
    "regionGuide": REGION_GUIDE, "regionDistanceM": REGION_DISTANCE,
    "clearanceM": CLEARANCE, "vertices": len(target_vertices),
    "faces": len(target_faces), "boundaryVertices": boundary_count,
    "copiedVertexGroups": len(scalp.vertex_groups),
    "armatureModifier": armature.name, "runtimeDependency": "none",
    "status": "COLLISION_AND_VISUAL_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R163_BUILD=" + json.dumps(report, sort_keys=True))
