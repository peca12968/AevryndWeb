"""Replace the deep disc-like medial caruncles with thin wet anatomical mounds."""
from pathlib import Path
import json
import math
import os

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-recessed-eyelid-wall-r1100-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-anatomical-caruncle-r1101-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1101-anatomical-caruncle-sweep.study.json"
OUT = ROOT.parent / "Temp" / "female-realism" / "v249r1101-anatomical-caruncle"
BODY = "AevryndFemaleCC0PalpebralClosure_R1097"
FRAMES = (1, 20, 33, 61)
# label, half-width x, central outward bulge y, half-height z, sclera clearance (metres)
VARIANTS = (
    ("a-compact", 0.00055, 0.00012, 0.00032, 0.00035),
    ("b-anatomical", 0.00065, 0.00016, 0.00038, 0.00040),
    ("c-broad", 0.00075, 0.00020, 0.00044, 0.00045),
)
SELECTED = "b-anatomical"
REQUESTED_VARIANT = os.environ.get("AEVRYND_VARIANT")


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def world_tree(obj, depsgraph=None):
    if depsgraph is None: depsgraph = bpy.context.evaluated_depsgraph_get(); depsgraph.update()
    evaluated = obj.evaluated_get(depsgraph); mesh = evaluated.to_mesh(); vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    mesh.calc_loop_triangles(); triangles = [tuple(item.vertices) for item in mesh.loop_triangles]; evaluated.to_mesh_clear(); return BVHTree.FromPolygons(vertices, triangles, all_triangles=True)


def caruncle_material():
    material = bpy.data.materials.new("Aevrynd_WetCaruncle_R1101"); material.use_nodes = True
    bsdf = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (0.20, 0.036, 0.032, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.36
    bsdf.inputs["Specular IOR Level"].default_value = 0.22
    bsdf.inputs["Subsurface Weight"].default_value = 0.075
    bsdf.inputs["Subsurface Radius"].default_value = (1.0, 0.38, 0.24)
    bsdf.inputs["Subsurface Scale"].default_value = 0.00065
    if bsdf.inputs.get("Coat Weight"): bsdf.inputs["Coat Weight"].default_value = 0.07
    if bsdf.inputs.get("Coat Roughness"): bsdf.inputs["Coat Roughness"].default_value = 0.24
    material["aevrynd_ownership"] = "procedural-in-project"; material["aevrynd_revision"] = "v249r1101"
    return material


def ellipsoid_topology(segments=24, rings=10):
    vertices = [(0.0, 0.0, -1.0)]; faces = []
    for ring in range(1, rings):
        latitude = -0.5 * math.pi + math.pi * ring / rings; radial = math.cos(latitude); z = math.sin(latitude)
        for segment in range(segments):
            angle = math.tau * segment / segments; vertices.append((radial * math.cos(angle), radial * math.sin(angle), z))
    top = len(vertices); vertices.append((0.0, 0.0, 1.0))
    for segment in range(segments): faces.append((0, 1 + (segment + 1) % segments, 1 + segment))
    for ring in range(rings - 2):
        first = 1 + ring * segments; second = first + segments
        for segment in range(segments):
            nxt = (segment + 1) % segments; faces.append((first + segment, first + nxt, second + nxt, second + segment))
    last = 1 + (rings - 2) * segments
    for segment in range(segments): faces.append((last + segment, last + (segment + 1) % segments, top))
    return vertices, faces


def parent_to_head(obj, rig):
    world = obj.matrix_world.copy(); obj.parent = rig; obj.parent_type = "BONE"; obj.parent_bone = "head"; obj.matrix_world = world


def build_caruncle(side, rx, bulge, rz, clearance, optical_trees, material, rig):
    sign = 1.0 if side == "L" else -1.0; center_x = sign * 0.01845; center_z = 1.44858
    rings, segments = 4, 24; coordinates = [(0.0, 0.0, 0.0)]; faces = []
    for ring in range(1, rings + 1):
        radius = ring / rings
        for segment in range(segments):
            angle = math.tau * segment / segments; coordinates.append((radius * math.cos(angle), radius * math.sin(angle), radius))
    for segment in range(segments): faces.append((0, 1 + segment, 1 + (segment + 1) % segments))
    for ring in range(2, rings + 1):
        previous = 1 + (ring - 2) * segments; current = 1 + (ring - 1) * segments
        for segment in range(segments):
            nxt = (segment + 1) % segments; faces.append((previous + segment, current + segment, current + nxt, previous + nxt))
    vertices = []; misses = 0
    for u, v, radius in coordinates:
        shoulder = 1.0 + 0.10 * u
        x = center_x + sign * rx * u; z = center_z + rz * v * shoulder
        hits = [tree.ray_cast(Vector((x, -0.20, z)), Vector((0.0, 1.0, 0.0)), 0.20)[0] for tree in optical_trees]
        hits = [item for item in hits if item is not None]
        if not hits: misses += 1; hit = Vector((x, -0.111, z))
        else: hit = min(hits, key=lambda item: item.y)
        y = hit.y - clearance - bulge * (1.0 - radius * radius)
        vertices.append((x, y, z))
    mesh = bpy.data.meshes.new(f"Eye_{side}_AnatomicalCaruncle_R1101Mesh"); mesh.from_pydata(vertices, [], faces); mesh.materials.append(material)
    for polygon in mesh.polygons: polygon.use_smooth = True
    obj = bpy.data.objects.new(f"Eye_{side}_AnatomicalCaruncle_R1101", mesh); bpy.context.collection.objects.link(obj); parent_to_head(obj, rig)
    obj["aevrynd_layer"] = "eye.medial-caruncle"; obj["aevrynd_revision"] = "v249r1101-anatomical-caruncle"; obj["aevrynd_ownership"] = "procedural-in-project"
    return obj, {"halfWidthMm": rx * 1000.0, "centralBulgeMm": bulge * 1000.0, "halfHeightMm": rz * 1000.0, "clearanceMm": clearance * 1000.0, "centerXZWorld": [center_x, center_z], "projectionMisses": misses, "vertices": len(vertices), "faces": len(faces)}


def collision_frames(body, caruncles):
    results, failures = {}, []
    for frame in FRAMES:
        bpy.context.scene.frame_set(frame); deps = bpy.context.evaluated_depsgraph_get(); deps.update(); body_tree = world_tree(body, deps); result = {}
        for side, obj in caruncles.items():
            patch = world_tree(obj, deps); values = {"body": len(patch.overlap(body_tree))}
            for layer in ("Sclera", "Cornea", "Iris", "UpperLashes", "LowerLashes"):
                values[layer] = len(patch.overlap(world_tree(bpy.data.objects[f"Eye_{side}_{layer}"], deps)))
            result[side] = values
            for target, count in values.items():
                if count: failures.append({"frame": frame, "side": side, "target": target, "triangleOverlapCount": count})
        results[str(frame)] = result
    return results, failures


def render(scene, label, view):
    camera = scene.camera
    if view == "eye-front": camera.location, target, camera.data.lens, size = (0.0, -0.405, 1.449), (0.0, -0.105, 1.449), 135, (1400, 760)
    elif view == "eye-oblique": camera.location, target, camera.data.lens, size = (0.235, -0.405, 1.451), (0.0, -0.105, 1.449), 135, (1400, 900)
    else: camera.location, target, camera.data.lens, size = (0.0, -0.72, 1.445), (0.0, -0.025, 1.445), 88, (1000, 1000)
    look_at(camera, target); scene.render.resolution_x, scene.render.resolution_y = size; scene.render.resolution_percentage = 100
    path = OUT / f"{label}-{view}.png"; scene.render.filepath = str(path); bpy.ops.render.render(write_still=True); return str(path)


OUT.mkdir(parents=True, exist_ok=True); variants = []
active_variants = tuple(item for item in VARIANTS if REQUESTED_VARIANT in (None, item[0]))
if not active_variants: raise RuntimeError(f"unknown AEVRYND_VARIANT={REQUESTED_VARIANT}")
for label, rx, bulge, rz, clearance in active_variants:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE)); scene = bpy.context.scene; scene.frame_set(1); body = bpy.data.objects[BODY]; rig = bpy.data.objects["AevryndFemaleRig"]
    for side in ("L", "R"):
        old = bpy.data.objects.get(f"Eye_{side}_MedialCaruncle_R1023")
        if old: bpy.data.objects.remove(old, do_unlink=True)
    material = caruncle_material(); caruncles = {}; geometry = {}
    for side in ("L", "R"):
        optical_trees = (world_tree(bpy.data.objects[f"Eye_{side}_Sclera"]), world_tree(bpy.data.objects[f"Eye_{side}_Cornea"]))
        caruncles[side], geometry[side] = build_caruncle(side, rx, bulge, rz, clearance, optical_trees, material, rig)
    for obj in scene.objects:
        name = obj.name.lower()
        if obj.type == "CURVES" or any(token in name for token in ("groom", "scalp", "haircard", "hairfiber")):
            if not any(token in name for token in ("brow", "lash")): obj.hide_render = True
    bpy.context.view_layer.update(); collisions, failures = collision_frames(body, caruncles); scene.frame_set(1); bpy.context.view_layer.update(); renders = [render(scene, label, view) for view in ("eye-front", "eye-oblique", "face-front")]
    status = "TECHNICAL_PASS" if not failures and all(item["projectionMisses"] == 0 for item in geometry.values()) else "TECHNICAL_FAIL"; variants.append({"label": label, "geometry": geometry, "collisionFrames": collisions, "collisionFailures": failures, "renders": renders, "status": status})
    if label == SELECTED and status == "TECHNICAL_PASS":
        body["aevrynd_revision"] = "v249r1101-anatomical-caruncle"; body["aevrynd_source"] = SOURCE.name
        scene["aevrynd_release_state"] = "VISUAL_REVIEW_PENDING"; scene["aevrynd_website_promotion"] = "forbidden"; bpy.context.preferences.filepaths.save_version = 0; bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {"revision": "v249r1101-anatomical-caruncle-sweep", "source": str(SOURCE), "output": str(OUTPUT), "method": "replace each deep disc patch with a shallow procedural tear-shaped surface projected to the owned sclera, retaining a small central mound and moist soft-tissue response", "variants": variants, "selectedVariant": SELECTED, "externalDependencies": [], "websitePromotionApproved": False, "candidateStatus": "VISUAL_REVIEW_PENDING"}
REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print("AEVRYND_R1101_CARUNCLE=" + json.dumps({"selected": SELECTED, "variants": [{"label": item["label"], "geometry": item["geometry"], "failures": len(item["collisionFailures"]), "status": item["status"]} for item in variants]}, sort_keys=True))
