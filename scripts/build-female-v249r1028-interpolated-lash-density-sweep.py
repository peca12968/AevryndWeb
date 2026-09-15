"""Interpolate lash fill fibres without adding objects, materials or draw calls."""

import itertools
import json
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-lash-path-hierarchy-r1027-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-interpolated-lash-density-r1028-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1028-interpolated-lash-density-sweep.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r1028-interpolated-lash-density-sweep"
BODY = "AevryndFemaleCC0Baseline_v259"
FRAMES = (1, 20, 33, 61)
VARIANTS = (
    ("a-half-gaps", "half", (0.5,)),
    ("b-every-gap", "all", (0.5,)),
    ("c-double-fill", "all", (1.0 / 3.0, 2.0 / 3.0)),
)


def strand_rings(obj):
    adjacency = {vertex.index: set() for vertex in obj.data.vertices}; edges = set()
    for edge in obj.data.edges:
        first, second = edge.vertices; adjacency[first].add(second); adjacency[second].add(first); edges.add(tuple(sorted((first, second))))
    remaining = set(adjacency); strands = []
    while remaining:
        seed = remaining.pop(); stack = [seed]; component = {seed}
        while stack:
            current = stack.pop(); fresh = adjacency[current] & remaining; remaining.difference_update(fresh); component.update(fresh); stack.extend(fresh)
        rings = []
        for triple in itertools.combinations(component, 3):
            if all(tuple(sorted(pair)) in edges for pair in itertools.combinations(triple, 2)):
                center = sum((obj.data.vertices[index].co for index in triple), Vector()) / 3.0; rings.append((center, tuple(sorted(triple))))
        rings.sort(key=lambda item: item[0].y, reverse=True); strands.append(rings)
    strands.sort(key=lambda rings: (obj.matrix_world @ rings[0][0]).x)
    return strands


def fibre_faces(offset):
    faces = []
    for ring in range(6):
        first = offset + ring * 3; second = first + 3
        for corner in range(3):
            nxt = (corner + 1) % 3; faces.append((first + corner, first + nxt, second + nxt, second + corner))
    return faces


def add_interpolated_fibres(obj, gap_mode, fractions, static_targets):
    strands = strand_rings(obj); original_vertices = [vertex.co.copy() for vertex in obj.data.vertices]; original_faces = [tuple(poly.vertices) for poly in obj.data.polygons]
    candidates = []
    for gap in range(len(strands) - 1):
        if gap_mode == "half" and gap % 2:
            continue
        left, right = strands[gap], strands[gap + 1]
        for fraction in fractions:
            strand_vertices = []
            for (_left_center, left_ring), (_right_center, right_ring) in zip(left, right):
                for left_index, right_index in zip(left_ring, right_ring):
                    strand_vertices.append(original_vertices[left_index].lerp(original_vertices[right_index], fraction))
            candidates.append({"vertices": strand_vertices, "faces": fibre_faces(0), "gap": gap, "fraction": fraction})
    retained = []; rejected = []
    for candidate in candidates:
        tree = tree_from_local(obj, candidate["vertices"], candidate["faces"]); hits = {name: len(tree.overlap(target)) for name, target in static_targets.items()}
        if any(hits.values()): rejected.append({"gap": candidate["gap"], "fraction": candidate["fraction"], "triangleOverlaps": hits})
        else: retained.append(candidate)
    new_vertices = []; new_faces = []
    for candidate in retained:
        offset = len(original_vertices) + len(new_vertices); new_faces.extend(tuple(offset + index for index in face) for face in candidate["faces"]); new_vertices.extend(candidate["vertices"])
    materials = list(obj.data.materials); mesh = obj.data; mesh.clear_geometry(); mesh.from_pydata(original_vertices + new_vertices, [], original_faces + new_faces)
    for material in materials:
        if material.name not in [item.name for item in mesh.materials]: mesh.materials.append(material)
    for polygon in mesh.polygons: polygon.use_smooth = True
    mesh.update()
    return {"originalStrands": len(strands), "candidateStrands": len(candidates), "addedStrands": len(retained), "rejectedStaticCollisionStrands": rejected, "finalStrands": len(strands) + len(retained), "beforeVertices": len(original_vertices), "afterVertices": len(mesh.vertices), "beforePolygons": len(original_faces), "afterPolygons": len(mesh.polygons), "newVertices": len(new_vertices), "newPolygons": len(new_faces)}, original_vertices, original_faces, retained


def tree_from_local(obj, vertices, faces):
    world = [obj.matrix_world @ vertex for vertex in vertices]; return BVHTree.FromPolygons(world, faces, all_triangles=False)


def audit_fill_self(obj, original_vertices, original_faces, fills):
    original_tree = tree_from_local(obj, original_vertices, original_faces); fill_trees = [tree_from_local(obj, item["vertices"], item["faces"]) for item in fills]
    original_overlaps = []
    for index, tree in enumerate(fill_trees):
        count = len(tree.overlap(original_tree))
        if count: original_overlaps.append({"fillStrand": index, "triangleOverlapCount": count})
    fill_overlaps = []
    for first in range(len(fill_trees)):
        for second in range(first + 1, len(fill_trees)):
            count = len(fill_trees[first].overlap(fill_trees[second]))
            if count: fill_overlaps.append({"firstFillStrand": first, "secondFillStrand": second, "triangleOverlapCount": count})
    return {"newVsOriginal": original_overlaps, "newVsNew": fill_overlaps, "status": "PASS" if not original_overlaps and not fill_overlaps else "FAIL"}


def world_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph); mesh = evaluated.to_mesh(); vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]; polygons = [tuple(poly.vertices) for poly in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, polygons, all_triangles=False); evaluated.to_mesh_clear(); return tree


def collision_frames():
    scene = bpy.context.scene; results = {}; failures = []
    for frame in FRAMES:
        scene.frame_set(frame); depsgraph = bpy.context.evaluated_depsgraph_get(); depsgraph.update(); body = world_tree(bpy.data.objects[BODY], depsgraph); frame_result = {}
        for side in ("L", "R"):
            upper = world_tree(bpy.data.objects[f"Eye_{side}_UpperLashes"], depsgraph); lower = world_tree(bpy.data.objects[f"Eye_{side}_LowerLashes"], depsgraph); sclera = world_tree(bpy.data.objects[f"Eye_{side}_Sclera"], depsgraph); cornea = world_tree(bpy.data.objects[f"Eye_{side}_Cornea"], depsgraph)
            values = {"upperBody": len(upper.overlap(body)), "lowerBody": len(lower.overlap(body)), "upperSclera": len(upper.overlap(sclera)), "lowerSclera": len(lower.overlap(sclera)), "upperCornea": len(upper.overlap(cornea)), "lowerCornea": len(lower.overlap(cornea)), "upperLower": len(upper.overlap(lower))}; frame_result[side] = values
            for pair, count in values.items():
                if count: failures.append({"frame": frame, "side": side, "pair": pair, "triangleOverlapCount": count})
        results[str(frame)] = frame_result
    return results, failures


def look_at(camera, target): camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


RENDER_DIR.mkdir(parents=True, exist_ok=True); variants = []
for label, gap_mode, fractions in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE)); scene = bpy.context.scene; scene.frame_set(1); bpy.context.view_layer.update(); edits = {}; self_audits = {}
    depsgraph = bpy.context.evaluated_depsgraph_get(); depsgraph.update(); body_static = world_tree(bpy.data.objects[BODY], depsgraph)
    before_pairs = sum(len(obj.data.materials) for obj in bpy.data.objects if obj.name.endswith(("UpperLashes", "LowerLashes")))
    for side in ("L", "R"):
        for layer in ("UpperLashes", "LowerLashes"):
            name = f"Eye_{side}_{layer}"; obj = bpy.data.objects[name]
            static_targets = {"body": body_static, "sclera": world_tree(bpy.data.objects[f"Eye_{side}_Sclera"], depsgraph), "cornea": world_tree(bpy.data.objects[f"Eye_{side}_Cornea"], depsgraph)}
            edit, original_vertices, original_faces, fills = add_interpolated_fibres(obj, gap_mode, fractions, static_targets); edits[name] = edit; self_audits[name] = audit_fill_self(obj, original_vertices, original_faces, fills)
    bpy.context.view_layer.update(); collisions, failures = collision_frames(); scene.frame_set(1); bpy.context.view_layer.update(); after_pairs = sum(len(obj.data.materials) for obj in bpy.data.objects if obj.name.endswith(("UpperLashes", "LowerLashes")))
    hidden = []
    for obj in scene.objects:
        is_hair = obj.name.startswith(("Groom_", "AevryndFemaleTargetScalp")) or obj.type == "CURVES"; is_brow_or_lash = "Brow" in obj.name or obj.name.endswith(("UpperLashes", "LowerLashes"))
        if is_hair and not is_brow_or_lash and not obj.hide_render: obj.hide_render = True; hidden.append(obj.name)
    scene.render.resolution_x = scene.render.resolution_y = 1000; camera = scene.camera; camera.data.lens = 105; rendered = []
    for view, location, target in (("front", (0.0, -0.48, 1.485), (0.0, -0.060, 1.484)), ("three-quarter-left", (0.205, -0.425, 1.490), (0.0, -0.057, 1.482)), ("three-quarter-right", (-0.205, -0.425, 1.490), (0.0, -0.057, 1.482))):
        camera.location = location; look_at(camera, target); path = RENDER_DIR / f"{label}-{view}.png"; scene.render.filepath = str(path); bpy.ops.render.render(write_still=True); rendered.append(str(path))
    for name in hidden: bpy.data.objects[name].hide_render = False
    self_pass = all(item["status"] == "PASS" for item in self_audits.values()); status = "TECHNICAL_PASS" if not failures and self_pass and before_pairs == after_pairs else "TECHNICAL_FAIL"
    variants.append({"label": label, "gapMode": gap_mode, "fractions": list(fractions), "edits": edits, "selfCollision": self_audits, "fourFrameCollision": collisions, "collisionFailures": failures, "lashObjectMaterialPairsBefore": before_pairs, "lashObjectMaterialPairsAfter": after_pairs, "rendered": rendered, "status": status})
    if label == "b-every-gap" and status == "TECHNICAL_PASS":
        scene["aevrynd_mainline_revision"] = "v249r1028-interpolated-human-lash-density"; scene["aevrynd_mainline_parent"] = SOURCE.name; scene["aevrynd_release_state"] = "TECHNICAL_PASS_VISUAL_REVIEW_REQUIRED"; scene["aevrynd_website_promotion"] = "forbidden"; bpy.context.preferences.filepaths.save_version = 0; bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {"source": str(SOURCE), "output": str(OUTPUT), "method": "interpolate complete seven-ring triangular fibres between adjacent root-fixed r1027 paths and append them to the existing four lash meshes", "variants": variants, "selectedVariant": None, "status": "VISUAL_REVIEW_REQUIRED", "websitePromotionApproved": False}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1028_INTERPOLATED_LASH_DENSITY=" + json.dumps({"output": str(OUTPUT), "variants": [{"label": item["label"], "counts": {name: edit["finalStrands"] for name, edit in item["edits"].items()}, "selfPass": all(value["status"] == "PASS" for value in item["selfCollision"].values()), "collisionFailures": len(item["collisionFailures"]), "drawPairs": [item["lashObjectMaterialPairsBefore"], item["lashObjectMaterialPairsAfter"]], "status": item["status"]} for item in variants]}, sort_keys=True))
