"""Sweep sclera-projected, owned caruncle patches on r1001."""

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-mixed-space-eyelid-relief-r1001.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-projected-caruncle-patch-r1006-study.blend"
REPORT = ASSETS / "female-v249-mainline-cc0-projected-caruncle-patch-r1006.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r1006-projected-caruncle-patch"
BODY = "AevryndFemaleCC0Baseline_v259"
RINGS = 4
SEGMENTS = 24
VARIANTS = (
    ("a-none", 0.0, 0.0, 0.00035),
    ("b-small", 0.00100, 0.00060, 0.00035),
    ("c-medium", 0.00140, 0.00080, 0.00045),
    ("d-wide", 0.00180, 0.00100, 0.00055),
)
VIEWS = (
    ("front", (0.0, -0.48, 1.485), (0.0, -0.060, 1.485)),
    ("three-quarter-left", (0.155, -0.445, 1.485), (0.0, -0.060, 1.480)),
    ("three-quarter-right", (-0.155, -0.445, 1.485), (0.0, -0.060, 1.480)),
)


def world_geometry(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    polygons = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return vertices, polygons


def world_tree(obj):
    vertices, polygons = world_geometry(obj)
    return BVHTree.FromPolygons(vertices, polygons, all_triangles=False)


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def topology():
    vertices = [(0.0, 0.0, 0.0)]
    for ring in range(1, RINGS + 1):
        for segment in range(SEGMENTS):
            angle = 2.0 * math.pi * segment / SEGMENTS
            radius = ring / RINGS
            vertices.append((radius * math.cos(angle), 0.0, radius * math.sin(angle)))
    faces = []
    for segment in range(SEGMENTS):
        faces.append((0, 1 + segment, 1 + (segment + 1) % SEGMENTS))
    for ring in range(2, RINGS + 1):
        previous = 1 + (ring - 2) * SEGMENTS
        current = 1 + (ring - 1) * SEGMENTS
        for segment in range(SEGMENTS):
            nxt = (segment + 1) % SEGMENTS
            faces.append((previous + segment, current + segment, current + nxt, previous + nxt))
    return vertices, faces


def create_patch(side, material, rig):
    vertices, faces = topology()
    mesh = bpy.data.meshes.new(f"Aevrynd_ProjectedCarunclePatch_{side}_R1006")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(material)
    obj = bpy.data.objects.new(f"Eye_{side}_CarunclePatch_R1006", mesh)
    bpy.context.collection.objects.link(obj)
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = world
    obj["aevrynd_revision"] = "v249r1006-projected-caruncle-patch-study"
    obj["aevrynd_layer"] = "caruncle"
    obj["aevrynd_ownership"] = "procedural-in-project"
    return obj


def project_patch(obj, side, rx, rz, clearance, sclera_tree):
    center_x = 0.0190 if side == "L" else -0.0190
    inverse = obj.matrix_world.inverted()
    coordinates = [(0.0, 0.0)]
    for ring in range(1, RINGS + 1):
        for segment in range(SEGMENTS):
            angle = 2.0 * math.pi * segment / SEGMENTS
            radius = ring / RINGS
            coordinates.append((radius * math.cos(angle), radius * math.sin(angle)))
    misses = 0
    for vertex, (u, v) in zip(obj.data.vertices, coordinates):
        x = center_x + u * rx
        z = 1.4490 + v * rz
        hit, _normal, _face, _distance = sclera_tree.ray_cast(
            Vector((x, -0.20, z)), Vector((0.0, 1.0, 0.0)), 0.20
        )
        if hit is None:
            misses += 1
            hit = Vector((x, -0.1195, z))
        point = Vector((x, hit.y - clearance, z))
        vertex.co = inverse @ point
    obj.data.update()
    return misses


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
rig = bpy.data.objects["AevryndFemaleRig"]

material = bpy.data.materials.get("Aevrynd_ProjectedCaruncle_R1006") or bpy.data.materials.new(
    "Aevrynd_ProjectedCaruncle_R1006"
)
material.use_nodes = True
shader = next(node for node in material.node_tree.nodes if node.bl_idname == "ShaderNodeBsdfPrincipled")
shader.inputs["Base Color"].default_value = (0.19, 0.045, 0.038, 1.0)
shader.inputs["Roughness"].default_value = 0.48
shader.inputs["Specular IOR Level"].default_value = 0.20
shader.inputs["Subsurface Weight"].default_value = 0.025
material["aevrynd_ownership"] = "procedural-in-project"

objects = {side: create_patch(side, material, rig) for side in ("L", "R")}
RENDER_DIR.mkdir(parents=True, exist_ok=True)
scene.render.resolution_x = scene.render.resolution_y = 800
camera = scene.camera
camera.data.lens = 105

hidden = []
for obj in scene.objects:
    if obj.name.startswith(("Groom_", "AevryndFemaleTargetScalp")) or obj.type in {"CURVES", "CURVE"}:
        if not obj.hide_render:
            obj.hide_render = True
            hidden.append(obj.name)

results = []
for label, rx, rz, clearance in VARIANTS:
    misses = {}
    for side, obj in objects.items():
        obj.hide_render = rx == 0.0
        if rx:
            misses[side] = project_patch(
                obj, side, rx, rz, clearance, world_tree(bpy.data.objects[f"Eye_{side}_Sclera"])
            )
    bpy.context.view_layer.update()
    collisions = {}
    if rx:
        body_tree = world_tree(bpy.data.objects[BODY])
        for side, obj in objects.items():
            patch_tree = world_tree(obj)
            collisions[side] = {
                "body": len(body_tree.overlap(patch_tree)),
                "sclera": len(world_tree(bpy.data.objects[f"Eye_{side}_Sclera"]).overlap(patch_tree)),
                "cornea": len(world_tree(bpy.data.objects[f"Eye_{side}_Cornea"]).overlap(patch_tree)),
                "upperLashes": len(world_tree(bpy.data.objects[f"Eye_{side}_UpperLashes"]).overlap(patch_tree)),
                "lowerLashes": len(world_tree(bpy.data.objects[f"Eye_{side}_LowerLashes"]).overlap(patch_tree)),
            }
    rendered = []
    for view_name, location, target in VIEWS:
        camera.location = location
        look_at(camera, target)
        path = RENDER_DIR / f"{label}-{view_name}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        rendered.append(str(path))
    total = sum(value for side in collisions.values() for value in side.values())
    results.append(
        {
            "label": label,
            "radiiM": [rx, rz],
            "clearanceM": clearance,
            "projectionMisses": misses,
            "triangleOverlaps": collisions,
            "totalTriangleOverlaps": total,
            "rendered": rendered,
            "status": "PASS" if total == 0 and all(value == 0 for value in misses.values()) else "FAIL",
        }
    )

for name in hidden:
    bpy.data.objects[name].hide_render = False
for obj in objects.values():
    obj.hide_render = False
scene["aevrynd_mainline_revision"] = "v249r1006-projected-caruncle-patch-study"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "STUDY_ONLY_VISUAL_REVIEW_REQUIRED"
scene["aevrynd_website_promotion"] = "forbidden"
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "objects": [obj.name for obj in objects.values()],
    "material": material.name,
    "topology": {"rings": RINGS, "segments": SEGMENTS, "verticesPerSide": 1 + RINGS * SEGMENTS},
    "variants": results,
    "selected": None,
    "status": "VISUAL_REVIEW_REQUIRED",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_R1006_PROJECTED_CARUNCLE_PATCH=" + json.dumps(report, sort_keys=True))
