import json
import math
import random
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v20.blend"
OUTPUT = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v21.blend"
BUILD = ROOT / ".character-build" / "aevrynd-female-authoring-v21.glb"
LOD1 = ROOT / ".character-build" / "aevrynd-female-authoring-v21-lod1.glb"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "hair-foundation-v21"


def evaluated_body_tree(body):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    polygons = [tuple(polygon.vertices) for polygon in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, polygons, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


def boundary_angle(phi):
    # Front center stops at the natural hairline, sides remain above the ears,
    # and the rear descends to the nape. Smoothstep blending avoids cut facets.
    forward = -math.sin(phi)
    if forward >= 0.0:
        side_mix = forward * forward * (3.0 - 2.0 * forward)
        temple = min(1.0, abs(math.cos(phi)) / 0.82)
        return 1.54 - 0.30 * side_mix - 0.08 * temple * side_mix
    rear = -forward
    rear_mix = rear * rear * (3.0 - 2.0 * rear)
    return 1.54 + 0.47 * rear_mix


def rebuild_scalp(body, rig):
    old = bpy.data.objects.get("HairScalp")
    scalp_material = old.material_slots[0].material if old and old.material_slots else None
    if old:
        old_mesh = old.data
        bpy.data.objects.remove(old, do_unlink=True)
        if old_mesh.users == 0:
            bpy.data.meshes.remove(old_mesh)

    tree = evaluated_body_tree(body)
    center = Vector((0.0, -0.002, 1.625))
    segments = 96
    rings = 26
    clearance = 0.0018
    vertices = []
    faces = []
    misses = 0

    location, normal, _, _ = tree.ray_cast(center, Vector((0.0, 0.0, 1.0)), 0.30)
    if location is None:
        raise RuntimeError("failed to project scalp crown")
    vertices.append(tuple(location + normal.normalized() * clearance))

    for ring in range(1, rings + 1):
        fraction = ring / rings
        for segment in range(segments):
            phi = 2.0 * math.pi * segment / segments
            theta = boundary_angle(phi) * fraction
            direction = Vector((
                0.98 * math.sin(theta) * math.cos(phi),
                1.12 * math.sin(theta) * math.sin(phi),
                1.00 * math.cos(theta),
            )).normalized()
            location, normal, _, _ = tree.ray_cast(center, direction, 0.30)
            if location is None:
                misses += 1
                location = center + direction * 0.102
                normal = direction
            vertices.append(tuple(location + normal.normalized() * clearance))

    first_ring = 1
    for segment in range(segments):
        next_segment = (segment + 1) % segments
        faces.append((0, first_ring + segment, first_ring + next_segment))
    for ring in range(1, rings):
        current = 1 + (ring - 1) * segments
        following = current + segments
        for segment in range(segments):
            next_segment = (segment + 1) % segments
            faces.append((
                current + segment,
                following + segment,
                following + next_segment,
                current + next_segment,
            ))

    mesh = bpy.data.meshes.new("HairScalpMeshV21")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    for polygon in mesh.polygons:
        polygon.use_smooth = True

    scalp = bpy.data.objects.new("HairScalp", mesh)
    bpy.context.scene.collection.objects.link(scalp)
    if scalp_material:
        scalp.data.materials.append(scalp_material)
        bsdf = next((node for node in scalp_material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"), None)
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (0.018, 0.0042, 0.0016, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.48
            anisotropic = bsdf.inputs.get("Anisotropic IOR Level")
            if anisotropic:
                anisotropic.default_value = 0.55
    scalp["aevrynd_role"] = "hair_scalp"
    scalp["aevrynd_hair_revision"] = 21
    scalp["aevrynd_clearance_m"] = clearance
    scalp["aevrynd_projection_misses"] = misses
    scalp.parent = rig
    scalp.parent_type = "BONE"
    scalp.parent_bone = "head"
    scalp.matrix_world = Matrix.Identity(4)
    return scalp, segments, rings, clearance, misses


def build_boundary_clumps(body, rig, scalp_material):
    old = bpy.data.objects.get("HairBoundaryClumps")
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    tree = evaluated_body_tree(body)
    center = Vector((0.0, -0.002, 1.625))
    clearance = 0.00215
    rng = random.Random(20260906)

    def project(phi, theta):
        direction = Vector((
            0.98 * math.sin(theta) * math.cos(phi),
            1.12 * math.sin(theta) * math.sin(phi),
            math.cos(theta),
        )).normalized()
        location, normal, _, _ = tree.ray_cast(center, direction, 0.30)
        if location is None:
            raise RuntimeError("failed to project a boundary clump")
        return tuple(location + normal.normalized() * clearance)

    vertices = []
    faces = []
    clump_count = 0
    candidates = 86
    for index in range(candidates):
        phi = 2.0 * math.pi * (index + 0.5) / candidates
        forward = -math.sin(phi)
        if forward > 0.58:
            continue
        root_theta = boundary_angle(phi) - 0.018
        rear = max(0.0, math.sin(phi))
        length = rng.uniform(0.07, 0.14) + rear * rng.uniform(0.08, 0.18)
        half_width = rng.uniform(0.006, 0.014)
        rows = 5
        base = len(vertices)
        for row in range(rows):
            t = row / (rows - 1)
            theta = root_theta + length * t
            taper = 1.0 - 0.78 * t
            drift = rng.uniform(-0.006, 0.006) * t
            vertices.append(project(phi - half_width * taper + drift, theta))
            vertices.append(project(phi + half_width * taper + drift, theta))
        for row in range(rows - 1):
            a = base + row * 2
            faces.append((a, a + 2, a + 3, a + 1))
        clump_count += 1

    mesh = bpy.data.meshes.new("HairBoundaryClumpsMeshV21")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    obj = bpy.data.objects.new("HairBoundaryClumps", mesh)
    bpy.context.scene.collection.objects.link(obj)
    if scalp_material:
        boundary_material = scalp_material.copy()
        boundary_material.name = "Aevrynd_Hair_Boundary_v21"
        boundary_material.surface_render_method = "DITHERED"
        bsdf = next((node for node in boundary_material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"), None)
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (0.026, 0.0065, 0.0024, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.46
            bsdf.inputs["Alpha"].default_value = 0.52
        obj.data.materials.append(boundary_material)
        warm_material = boundary_material.copy()
        warm_material.name = "Aevrynd_Hair_Boundary_Warm_v21"
        warm_bsdf = next((node for node in warm_material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"), None)
        if warm_bsdf:
            warm_bsdf.inputs["Base Color"].default_value = (0.065, 0.016, 0.0055, 1.0)
            warm_bsdf.inputs["Alpha"].default_value = 0.38
        obj.data.materials.append(warm_material)
        for index, polygon in enumerate(obj.data.polygons):
            polygon.material_index = 1 if index % 13 == 0 else 0
    obj["aevrynd_role"] = "hair_boundary_clumps"
    obj["aevrynd_hair_revision"] = 21
    obj["aevrynd_clearance_m"] = clearance
    obj["aevrynd_clump_count"] = clump_count
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = Matrix.Identity(4)
    return obj, clump_count, clearance


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, location, target, lens=86):
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 900
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    camera.data.lens = lens
    camera.location = location
    look_at(camera, target)
    for obj in bpy.data.objects:
        if obj.get("aevrynd_role") == "cornea":
            obj.hide_render = False
    bpy.ops.render.render(write_still=True)


def export_runtime(path, rig, excluded=()):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in bpy.data.objects:
        if obj.type in {"MESH", "ARMATURE"} and obj.name not in excluded:
            obj.hide_render = False
            obj.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.export_scene.gltf(
        filepath=str(path), export_format="GLB", use_selection=True,
        export_apply=True, export_yup=True, export_extras=True,
        export_animations=True, export_frame_range=True,
        export_attributes=True, export_vertex_color="ACTIVE",
    )


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
bpy.context.preferences.filepaths.save_version = 0
bpy.context.scene.frame_set(1)
RENDER_DIR.mkdir(parents=True, exist_ok=True)
BUILD.parent.mkdir(parents=True, exist_ok=True)
body = bpy.data.objects["AevryndFemaleBodyBase"]
rig = bpy.data.objects["AevryndFemaleRig"]
scalp, segments, rings, clearance, misses = rebuild_scalp(body, rig)
boundary_clumps, boundary_clump_count, boundary_clearance = build_boundary_clumps(
    body, rig, scalp.material_slots[0].material if scalp.material_slots else None
)
bpy.context.scene["aevrynd_hair_revision"] = 21
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

camera = bpy.data.objects["Aevrynd Review Camera"]
render(camera, "female-hair-front", (0.0, -0.72, 1.575), (0.0, -0.005, 1.555))
render(camera, "female-hair-three-quarter", (0.28, -0.64, 1.58), (0.0, 0.0, 1.55))
render(camera, "female-hair-side", (0.66, -0.05, 1.575), (0.0, 0.0, 1.545))
render(camera, "female-hair-back", (0.0, 0.76, 1.575), (0.0, 0.01, 1.545))

multires = next(modifier for modifier in body.modifiers if modifier.type == "MULTIRES")
old_levels = (multires.levels, multires.sculpt_levels, multires.render_levels)
multires.levels = multires.sculpt_levels = multires.render_levels = 0
export_runtime(BUILD, rig)
export_runtime(LOD1, rig, {"HairMain", "HairFlyaways"})
multires.levels, multires.sculpt_levels, multires.render_levels = old_levels

print("AEVRYND_HAIR_FOUNDATION_V21_REPORT=" + json.dumps({
    "state": "AUTHORING",
    "segments": segments,
    "rings": rings,
    "vertices": len(scalp.data.vertices),
    "faces": len(scalp.data.polygons),
    "clearance_m": clearance,
    "projection_misses": misses,
    "boundary_clumps": boundary_clump_count,
    "boundary_clearance_m": boundary_clearance,
    "runtime_glb": str(BUILD),
    "lod1_glb": str(LOD1),
}))
