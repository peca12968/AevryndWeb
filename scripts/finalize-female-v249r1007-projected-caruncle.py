"""Finalize the collision-free small r1006 projected caruncle as r1007."""

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-projected-caruncle-patch-r1006-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-projected-caruncle-r1007.blend"
AUDIT = ASSETS / "female-v249-mainline-cc0-projected-caruncle-r1007.collision-audit.json"
REVIEW_DIR = ROOT.parent / "Temp/female-realism/v249r1007-projected-caruncle"
BODY = "AevryndFemaleCC0Baseline_v259"
RINGS = 4
SEGMENTS = 24
RX = 0.00100
RZ = 0.00060
CLEARANCE = 0.00035
FRAMES = (1, 20, 33, 61)


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


def project_patch(obj, side, sclera_tree):
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
        x = center_x + u * RX
        z = 1.4490 + v * RZ
        hit, _normal, _face, _distance = sclera_tree.ray_cast(
            Vector((x, -0.20, z)), Vector((0.0, 1.0, 0.0)), 0.20
        )
        if hit is None:
            misses += 1
            continue
        vertex.co = inverse @ Vector((x, hit.y - CLEARANCE, z))
    obj.data.update()
    return misses


def minimum_vertex_distance(source, target_tree):
    points, _faces = world_geometry(source)
    distances = []
    for point in points:
        _nearest, _normal, _index, distance = target_tree.find_nearest(point)
        distances.append(float(distance))
    return min(distances) if distances else None


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
objects = {side: bpy.data.objects[f"Eye_{side}_CarunclePatch_R1006"] for side in ("L", "R")}
projection_misses = {}
for side, obj in objects.items():
    obj.data = obj.data.copy()
    projection_misses[side] = project_patch(obj, side, world_tree(bpy.data.objects[f"Eye_{side}_Sclera"]))
    obj.name = f"Eye_{side}_CarunclePatch_R1007"
    obj.data.name = f"Aevrynd_ProjectedCarunclePatch_{side}_R1007"
    obj["aevrynd_revision"] = "v249r1007-projected-caruncle"
    obj["aevrynd_selected_radii_m"] = [RX, RZ]
    obj["aevrynd_clearance_m"] = CLEARANCE
material = bpy.data.materials["Aevrynd_ProjectedCaruncle_R1006"].copy()
material.name = "Aevrynd_ProjectedCaruncle_R1007"
material["aevrynd_revision"] = "v249r1007-projected-caruncle"
for obj in objects.values():
    obj.data.materials.clear()
    obj.data.materials.append(material)

frames = {}
failures = []
for frame in FRAMES:
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    body_tree = world_tree(bpy.data.objects[BODY])
    frame_result = {}
    for side, patch in objects.items():
        patch_tree = world_tree(patch)
        targets = {
            "body": body_tree,
            "sclera": world_tree(bpy.data.objects[f"Eye_{side}_Sclera"]),
            "cornea": world_tree(bpy.data.objects[f"Eye_{side}_Cornea"]),
            "upperLashes": world_tree(bpy.data.objects[f"Eye_{side}_UpperLashes"]),
            "lowerLashes": world_tree(bpy.data.objects[f"Eye_{side}_LowerLashes"]),
        }
        values = {
            name: {
                "triangleOverlaps": len(patch_tree.overlap(tree)),
                "minimumPatchVertexDistanceM": minimum_vertex_distance(patch, tree),
            }
            for name, tree in targets.items()
        }
        frame_result[side] = values
        for layer, value in values.items():
            if value["triangleOverlaps"]:
                failures.append(
                    {
                        "frame": frame,
                        "side": side,
                        "layer": layer,
                        "triangleOverlaps": value["triangleOverlaps"],
                    }
                )
    frames[str(frame)] = frame_result

REVIEW_DIR.mkdir(parents=True, exist_ok=True)
scene.render.resolution_x = scene.render.resolution_y = 900
camera = scene.camera
camera.data.lens = 105
views = (
    ("front", 1, (0.0, -0.48, 1.485), (0.0, -0.060, 1.485)),
    ("three-quarter-left", 1, (0.155, -0.445, 1.485), (0.0, -0.060, 1.480)),
    ("three-quarter-right", 1, (-0.155, -0.445, 1.485), (0.0, -0.060, 1.480)),
    ("profile-left", 1, (0.315, -0.250, 1.482), (0.0, -0.060, 1.478)),
    ("profile-right", 1, (-0.315, -0.250, 1.482), (0.0, -0.060, 1.478)),
    ("front-frame20", 20, (0.0, -0.48, 1.485), (0.0, -0.060, 1.485)),
)
rendered = []
for label, frame, location, target in views:
    scene.frame_set(frame)
    camera.location = location
    look_at(camera, target)
    path = REVIEW_DIR / f"r1007-{label}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    rendered.append(str(path))

scene.frame_set(1)
scene["aevrynd_mainline_revision"] = "v249r1007-projected-caruncle"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "TECHNICAL_CANDIDATE_VISUAL_HERO_FAIL"
scene["aevrynd_website_promotion"] = "forbidden"
report = {
    "source": str(SOURCE),
    "model": str(OUTPUT),
    "objects": [obj.name for obj in objects.values()],
    "material": material.name,
    "projectionMisses": projection_misses,
    "radiiM": [RX, RZ],
    "clearanceM": CLEARANCE,
    "frames": frames,
    "failures": failures,
    "rendered": rendered,
    "status": "PASS" if not failures and not any(projection_misses.values()) else "FAIL",
}
AUDIT.write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_R1007_PROJECTED_CARUNCLE=" + json.dumps(report, sort_keys=True))
if report["status"] != "PASS":
    raise SystemExit(2)
