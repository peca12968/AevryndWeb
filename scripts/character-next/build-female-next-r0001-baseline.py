"""Create the traceable Aevrynd female-next r0001 baseline from the owned r1128 study."""
from pathlib import Path
import json
import math

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(r"D:\Download\Aevrynd")
SOURCE = ROOT / "sites-engine-journey" / "assets-source" / "aevrynd-character" / "aevrynd-female-cc0-brow-density-r1128-study.blend"
SOURCE_DIR = ROOT / "engine" / "assets" / "characters" / "female-next" / "source"
RUNTIME_DIR = ROOT / "engine" / "assets" / "characters" / "female-next" / "runtime"
EVIDENCE = ROOT / "Evidence" / "character-female-next" / "r0001-baseline"
OUTPUT = SOURCE_DIR / "aevrynd-female-next-r0001-baseline.blend"
REPORT = EVIDENCE / "female-next-r0001-baseline.report.json"
BODY = "AevryndFemaleCC0PalpebralClosure_R1097"
HAIR = "AevryndFemaleGradedHairlineGroom_R1081"
BROWS = ("Brow_L", "Brow_R", "Brow_L_Density", "Brow_R_Density")
FRAMES = (1, 20, 33, 61)


def ensure_collection(parent, name):
    existing = bpy.data.collections.get(name)
    collection = existing or bpy.data.collections.new(name)
    if collection.name not in {child.name for child in parent.children}:
        parent.children.link(collection)
    return collection


def classify(obj):
    name = obj.name.lower()
    if obj.type == "ARMATURE" or any(token in name for token in ("rig", "armature")):
        return "RIG"
    if any(token in name for token in ("collision", "collider", "proxy")):
        return "COLLISION"
    if any(token in name for token in ("hair", "scalp", "brow", "lash")):
        return "HAIR"
    if any(token in name for token in ("cornea", "sclera", "iris", "pupil", "eye", "wetline", "caruncle", "tear")):
        return "EYES"
    if any(token in name for token in ("tooth", "teeth", "tongue", "oral", "mouth")):
        return "ORAL"
    if any(token in name for token in ("cloth", "shirt", "dress", "skirt", "bandeau", "underwear", "garment", "shoe")):
        return "CLOTHING"
    if obj.type in {"LIGHT", "CAMERA"}:
        return "PRESENTATION"
    return "BODY"


def organize_layers(scene):
    root = ensure_collection(scene.collection, "AEVRYND_FEMALE_NEXT")
    layers = {name: ensure_collection(root, "AFN_" + name) for name in
              ("BODY", "EYES", "ORAL", "HAIR", "CLOTHING", "RIG", "COLLISION", "PRESENTATION")}
    counts = {name: 0 for name in layers}
    for obj in list(bpy.data.objects):
        layer = classify(obj)
        target = layers[layer]
        if target.objects.get(obj.name) is None:
            target.objects.link(obj)
        obj["aevrynd_layer"] = layer
        obj["aevrynd_character"] = "female-next"
        counts[layer] += 1
    return counts


def body_tree(body, depsgraph):
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    tree = BVHTree.FromPolygons(
        [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices],
        [tuple(poly.vertices) for poly in mesh.polygons],
        all_triangles=False,
    )
    evaluated.to_mesh_clear()
    return tree


def signed_clearance(tree, world):
    hit = tree.find_nearest(world)
    if not hit or hit[1] is None:
        return None
    return (world - hit[0]).dot(hit[1].normalized())


def surface_collision_audit(scene, body):
    result = {}
    for frame in FRAMES:
        scene.frame_set(frame)
        depsgraph = bpy.context.evaluated_depsgraph_get()
        depsgraph.update()
        tree = body_tree(body, depsgraph)
        frame_result = {}
        hair = bpy.data.objects[HAIR].evaluated_get(depsgraph)
        values = []
        for point in hair.data.points:
            value = signed_clearance(tree, hair.matrix_world @ point.position)
            if value is not None:
                values.append(value)
        frame_result[HAIR] = {
            "elementsTested": len(values),
            "minimumSignedClearanceM": min(values),
            "penetratingElements": sum(value < -0.00005 for value in values),
            "belowOneMmElements": sum(value < 0.001 for value in values),
        }
        for name in BROWS:
            obj = bpy.data.objects[name].evaluated_get(depsgraph)
            values = []
            for vertex in obj.data.vertices:
                value = signed_clearance(tree, obj.matrix_world @ vertex.co)
                if value is not None:
                    values.append(value)
            frame_result[name] = {
                "elementsTested": len(values),
                "minimumSignedClearanceM": min(values),
                "penetratingElements": sum(value < -0.00005 for value in values),
            }
        result[str(frame)] = frame_result
    scene.frame_set(1)
    return result


def model_statistics():
    stats = {
        "objects": len(bpy.data.objects),
        "meshes": 0,
        "vertices": 0,
        "polygons": 0,
        "triangles": 0,
        "curvesObjects": 0,
        "hairCurves": 0,
        "hairPoints": 0,
        "armatures": 0,
        "bones": 0,
        "shapeKeys": 0,
        "materials": len(bpy.data.materials),
        "images": len(bpy.data.images),
    }
    for obj in bpy.data.objects:
        if obj.type == "MESH":
            stats["meshes"] += 1
            stats["vertices"] += len(obj.data.vertices)
            stats["polygons"] += len(obj.data.polygons)
            stats["triangles"] += sum(max(1, len(poly.vertices) - 2) for poly in obj.data.polygons)
            if obj.data.shape_keys:
                stats["shapeKeys"] += max(0, len(obj.data.shape_keys.key_blocks) - 1)
        elif obj.type == "CURVES":
            stats["curvesObjects"] += 1
            stats["hairCurves"] += len(obj.data.curves)
            stats["hairPoints"] += len(obj.data.points)
        elif obj.type == "ARMATURE":
            stats["armatures"] += 1
            stats["bones"] += len(obj.data.bones)
    return stats


def dependency_inventory():
    images = []
    missing = []
    for image in bpy.data.images:
        if image.source not in {"FILE", "TILED"}:
            continue
        resolved = Path(bpy.path.abspath(image.filepath)) if image.filepath else None
        item = {
            "name": image.name,
            "packed": image.packed_file is not None,
            "source": image.source,
            "path": str(resolved) if resolved else "",
            "exists": bool(resolved and resolved.exists()),
        }
        images.append(item)
        if not item["packed"] and not item["exists"]:
            missing.append(image.name)
    return {"images": images, "missingExternalImages": missing}


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, label, location, target, lens, size, frame=1):
    scene.frame_set(frame)
    camera = scene.camera
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    path = EVIDENCE / f"female-next-r0001-{label}-f{frame:02d}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return str(path)


def render_set(scene):
    views = {
        "face-front": ((0.0, -0.64, 1.47), (0.0, -0.035, 1.445), 100, (1200, 1000)),
        "face-oblique": ((0.26, -0.62, 1.48), (0.0, -0.035, 1.445), 100, (1200, 1000)),
        "face-profile": ((0.64, -0.12, 1.47), (0.0, -0.02, 1.43), 95, (1000, 1000)),
        "full-front": ((0.0, -3.55, 0.92), (0.0, 0.0, 0.92), 58, (900, 1200)),
        "full-side": ((3.55, -0.15, 0.92), (0.0, 0.0, 0.92), 58, (900, 1200)),
        "full-back": ((0.0, 3.55, 0.92), (0.0, 0.0, 0.92), 58, (900, 1200)),
    }
    outputs = [render(scene, name, *settings, frame=1) for name, settings in views.items()]
    outputs.append(render(scene, "face-front", *views["face-front"], frame=33))
    outputs.append(render(scene, "full-front", *views["full-front"], frame=33))
    return outputs


for directory in (SOURCE_DIR, RUNTIME_DIR, EVIDENCE):
    directory.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
body = bpy.data.objects[BODY]
bpy.data.objects[HAIR].hide_render = bpy.data.objects[HAIR].hide_viewport = False
layer_counts = organize_layers(scene)
stats = model_statistics()
dependencies = dependency_inventory()
collisions = surface_collision_audit(scene, body)
penetrations = sum(
    item["penetratingElements"]
    for frame in collisions.values()
    for item in frame.values()
)

scene["aevrynd_character_id"] = "female-next"
scene["aevrynd_revision"] = "female-next-r0001"
scene["aevrynd_source_revision"] = "v249r1128-brow-density"
scene["aevrynd_release_state"] = "BASELINE_NOT_PROMOTABLE"
scene["aevrynd_website_promotion"] = "forbidden"
scene["aevrynd_runtime_export"] = "not-generated"
scene["aevrynd_external_platform_dependencies"] = "none"
scene.frame_set(1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
renders = render_set(scene)

report = {
    "revision": "female-next-r0001",
    "purpose": "authoritative baseline for a new controlled Aevrynd female character mainline",
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "runtimeOutput": None,
    "sourceOwnership": "Aevrynd-owned tracked v249/r1128 study; no MetaHuman, Unreal Engine, subscription or platform runtime dependency",
    "geometryChanged": False,
    "materialChanged": False,
    "layerCollectionsAdded": True,
    "layerObjectCounts": layer_counts,
    "statistics": stats,
    "dependencies": dependencies,
    "collisionAudit": collisions,
    "totalPenetratingElements": penetrations,
    "technicalStatus": "TECHNICAL_PASS" if penetrations == 0 and not dependencies["missingExternalImages"] else "TECHNICAL_FAIL",
    "visualStatus": "VISUAL_REVIEW_PENDING",
    "strictOverallScore": 42,
    "websitePromotionApproved": False,
    "enginePromotionApproved": False,
    "renders": renders,
}
REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print("AEVRYND_FEMALE_NEXT_R0001=" + json.dumps({
    "output": str(OUTPUT),
    "statistics": stats,
    "layerObjectCounts": layer_counts,
    "missingExternalImages": dependencies["missingExternalImages"],
    "totalPenetratingElements": penetrations,
    "technicalStatus": report["technicalStatus"],
}, sort_keys=True))
