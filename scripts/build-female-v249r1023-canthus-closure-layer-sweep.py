"""Integrate the owned r1007 medial caruncle and test lateral closure wedges on r1022."""

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-wetline-optics-r1022-study.blend"
CARUNCLE_SOURCE = ASSETS / "aevrynd-female-cc0-projected-caruncle-r1007.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-canthus-closure-r1023-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1023-canthus-closure-layer-sweep.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r1023-canthus-closure-layer-sweep"
BODY = "AevryndFemaleCC0Baseline_v259"
RINGS = 4
SEGMENTS = 24
FRAMES = (1, 20, 33, 61)
VARIANTS = (
    ("a-medial-only", 0.0, 0.0, 0.00035),
    ("b-small-lateral", 0.00060, 0.00034, 0.00034),
    ("c-medium-lateral", 0.00082, 0.00046, 0.00036),
)


def evaluated_world_geometry(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get(); depsgraph.update(); evaluated = obj.evaluated_get(depsgraph); mesh = evaluated.to_mesh()
    vertices = [tuple(evaluated.matrix_world @ vertex.co) for vertex in mesh.vertices]
    faces = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear(); return vertices, faces


def capture_medial_source():
    bpy.ops.wm.open_mainfile(filepath=str(CARUNCLE_SOURCE)); bpy.context.scene.frame_set(1); bpy.context.view_layer.update()
    return {side: evaluated_world_geometry(bpy.data.objects[f"Eye_{side}_CarunclePatch_R1007"]) for side in ("L", "R")}


def disc_topology():
    vertices = [(0.0, 0.0, 0.0)]
    for ring in range(1, RINGS + 1):
        for segment in range(SEGMENTS):
            angle = 2.0 * math.pi * segment / SEGMENTS; radius = ring / RINGS
            vertices.append((radius * math.cos(angle), 0.0, radius * math.sin(angle)))
    faces = []
    for segment in range(SEGMENTS): faces.append((0, 1 + segment, 1 + (segment + 1) % SEGMENTS))
    for ring in range(2, RINGS + 1):
        previous = 1 + (ring - 2) * SEGMENTS; current = 1 + (ring - 1) * SEGMENTS
        for segment in range(SEGMENTS):
            nxt = (segment + 1) % SEGMENTS; faces.append((previous + segment, current + segment, current + nxt, previous + nxt))
    return vertices, faces


def parent_to_head(obj, rig):
    world = obj.matrix_world.copy(); obj.parent = rig; obj.parent_type = "BONE"; obj.parent_bone = "head"; obj.matrix_world = world


def create_world_mesh(name, vertices, faces, material, rig, layer):
    mesh = bpy.data.meshes.new(name + "Mesh"); mesh.from_pydata(vertices, [], faces); mesh.materials.append(material)
    for polygon in mesh.polygons: polygon.use_smooth = True
    obj = bpy.data.objects.new(name, mesh); bpy.context.collection.objects.link(obj); parent_to_head(obj, rig)
    obj["aevrynd_revision"] = "v249r1023-canthus-closure-layer-study"; obj["aevrynd_layer"] = layer; obj["aevrynd_ownership"] = "procedural-in-project"
    return obj


def world_tree(obj, depsgraph=None):
    if depsgraph is None: depsgraph = bpy.context.evaluated_depsgraph_get(); depsgraph.update()
    evaluated = obj.evaluated_get(depsgraph); mesh = evaluated.to_mesh(); vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]; polygons = [tuple(poly.vertices) for poly in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, polygons, all_triangles=False); evaluated.to_mesh_clear(); return tree


def project_lateral(obj, side, rx, rz, clearance, sclera_tree):
    sign = 1.0 if side == "L" else -1.0; center_x = sign * 0.03775; inverse = obj.matrix_world.inverted(); coordinates = [(0.0, 0.0)]
    for ring in range(1, RINGS + 1):
        for segment in range(SEGMENTS):
            angle = 2.0 * math.pi * segment / SEGMENTS; radius = ring / RINGS; coordinates.append((radius * math.cos(angle), radius * math.sin(angle)))
    misses = 0
    for vertex, (u, v) in zip(obj.data.vertices, coordinates):
        x = center_x + u * rx; z = 1.4490 + v * rz
        hit, _normal, _face, _distance = sclera_tree.ray_cast(Vector((x, -0.20, z)), Vector((0.0, 1.0, 0.0)), 0.20)
        if hit is None: misses += 1; hit = Vector((x, -0.1195, z))
        vertex.co = inverse @ Vector((x, hit.y - clearance, z))
    obj.data.update(); return misses


def collision_frames(patches):
    scene = bpy.context.scene; results = {}; failures = []
    for frame in FRAMES:
        scene.frame_set(frame); depsgraph = bpy.context.evaluated_depsgraph_get(); depsgraph.update(); body = world_tree(bpy.data.objects[BODY], depsgraph); frame_result = {}
        for patch in patches:
            patch_tree = world_tree(patch, depsgraph); values = {"body": len(patch_tree.overlap(body))}
            side = "L" if "_L_" in patch.name else "R"
            for layer in ("Sclera", "Cornea", "UpperLashes", "LowerLashes"):
                values[layer] = len(patch_tree.overlap(world_tree(bpy.data.objects[f"Eye_{side}_{layer}"], depsgraph)))
            frame_result[patch.name] = values
            for target, count in values.items():
                if count: failures.append({"frame": frame, "patch": patch.name, "target": target, "triangleOverlapCount": count})
        results[str(frame)] = frame_result
    return results, failures


def look_at(camera, target): camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


medial_geometry = capture_medial_source(); RENDER_DIR.mkdir(parents=True, exist_ok=True); variants = []
for label, rx, rz, clearance in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE)); scene = bpy.context.scene; scene.frame_set(1); bpy.context.view_layer.update(); rig = bpy.data.objects["AevryndFemaleRig"]
    medial_material = bpy.data.materials.new("Aevrynd_MedialCaruncle_R1023"); medial_material.use_nodes = True; medial_bsdf = next(node for node in medial_material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    medial_bsdf.inputs["Base Color"].default_value = (0.19, 0.045, 0.038, 1.0); medial_bsdf.inputs["Roughness"].default_value = 0.48
    if "IOR Level" in medial_bsdf.inputs: medial_bsdf.inputs["IOR Level"].default_value = 0.20
    wetline_material = bpy.data.materials.get("Aevrynd_EyelidWetline_R1022")
    patches = [create_world_mesh(f"Eye_{side}_MedialCaruncle_R1023", *medial_geometry[side], medial_material, rig, "medial-caruncle") for side in ("L", "R")]
    misses = {}
    if rx:
        template_vertices, template_faces = disc_topology()
        for side in ("L", "R"):
            patch = create_world_mesh(f"Eye_{side}_LateralCanthusWedge_R1023", template_vertices, template_faces, wetline_material, rig, "lateral-canthus-wedge")
            misses[side] = project_lateral(patch, side, rx, rz, clearance, world_tree(bpy.data.objects[f"Eye_{side}_Sclera"])); patches.append(patch)
    bpy.context.view_layer.update(); collisions, failures = collision_frames(patches); scene.frame_set(1); bpy.context.view_layer.update(); hidden = []
    for obj in scene.objects:
        is_hair = obj.name.startswith(("Groom_", "AevryndFemaleTargetScalp")) or obj.type == "CURVES"; is_brow_or_lash = "Brow" in obj.name or obj.name.endswith(("UpperLashes", "LowerLashes"))
        if is_hair and not is_brow_or_lash and not obj.hide_render: obj.hide_render = True; hidden.append(obj.name)
    scene.render.resolution_x = scene.render.resolution_y = 1000; camera = scene.camera; camera.data.lens = 105; rendered = []
    for view, location, target in (("front", (0.0, -0.48, 1.485), (0.0, -0.060, 1.484)), ("three-quarter-left", (0.205, -0.425, 1.490), (0.0, -0.057, 1.482)), ("three-quarter-right", (-0.205, -0.425, 1.490), (0.0, -0.057, 1.482)), ("profile-left", (0.43, -0.115, 1.490), (0.020, -0.055, 1.482))):
        camera.location = location; look_at(camera, target); path = RENDER_DIR / f"{label}-{view}.png"; scene.render.filepath = str(path); bpy.ops.render.render(write_still=True); rendered.append(str(path))
    for name in hidden: bpy.data.objects[name].hide_render = False
    status = "TECHNICAL_PASS" if not failures and all(value == 0 for value in misses.values()) else "TECHNICAL_FAIL"
    variants.append({"label": label, "lateralRadiiM": [rx, rz], "clearanceM": clearance, "objects": [patch.name for patch in patches], "projectionMisses": misses, "collisionFrames": collisions, "collisionFailures": failures, "rendered": rendered, "status": status})
    if label == "a-medial-only" and status == "TECHNICAL_PASS":
        scene["aevrynd_mainline_revision"] = "v249r1023-medial-caruncle-integration"; scene["aevrynd_mainline_parent"] = SOURCE.name; scene["aevrynd_release_state"] = "LOCAL_TECHNICAL_PASS_VISUAL_HERO_FAIL"; scene["aevrynd_website_promotion"] = "forbidden"; bpy.context.preferences.filepaths.save_version = 0; bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {"source": str(SOURCE), "caruncleSource": str(CARUNCLE_SOURCE), "output": str(OUTPUT), "ownership": "all closure meshes and materials procedural in Aevrynd project; r1007 source already tracked", "variants": variants, "selectedVariant": None, "status": "VISUAL_REVIEW_REQUIRED", "websitePromotionApproved": False}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1023_CANTHUS_CLOSURE=" + json.dumps({"output": str(OUTPUT), "variants": [{"label": item["label"], "misses": item["projectionMisses"], "collisionFailures": len(item["collisionFailures"]), "status": item["status"]} for item in variants]}, sort_keys=True))
