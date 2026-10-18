"""Geometry-first face structure sweep for Aevrynd female-next."""
from pathlib import Path
import json
import math

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(r"D:\Download\Aevrynd")
SOURCE = ROOT / "engine" / "assets" / "characters" / "female-next" / "source" / "aevrynd-female-next-r0001-baseline.blend"
OUTPUT = ROOT / "engine" / "assets" / "characters" / "female-next" / "source" / "aevrynd-female-next-r0002-face-structure-study.blend"
EVIDENCE = ROOT / "Evidence" / "character-female-next" / "r0002-face-structure"
REPORT = EVIDENCE / "female-next-r0002-face-structure.report.json"
BODY = "AevryndFemaleCC0PalpebralClosure_R1097"
HAIR = "AevryndFemaleGradedHairlineGroom_R1081"
BROWS = ("Brow_L", "Brow_R", "Brow_L_Density", "Brow_R_Density")
FRAMES = (1, 20, 33, 61)
VARIANTS = (("a-subtle", 0.70), ("b-balanced", 1.00), ("c-strong", 1.30))
SELECTED = "b-balanced"


def gaussian(value, centre, radius):
    return math.exp(-((value - centre) / radius) ** 2)


def delta_for(co, strength):
    x, y, z = co
    if y >= -0.015 or z < 1.275 or z > 1.575 or abs(x) > 0.135:
        return Vector((0.0, 0.0, 0.0))
    front = max(0.0, min(1.0, (-y - 0.015) / 0.085))
    side = -1.0 if x < 0.0 else 1.0
    ax = abs(x)
    malar = gaussian(ax, 0.061, 0.031) * gaussian(z, 1.485, 0.045) * front
    jaw = gaussian(ax, 0.068, 0.040) * gaussian(z, 1.365, 0.055) * front
    chin = gaussian(x, 0.0, 0.043) * gaussian(z, 1.325, 0.035) * front
    lower_cheek = gaussian(ax, 0.055, 0.042) * gaussian(z, 1.415, 0.050) * front
    return Vector((
        strength * side * (0.0045 * malar - 0.0050 * jaw - 0.0015 * lower_cheek),
        strength * (-0.0050 * malar - 0.0055 * chin + 0.0015 * lower_cheek),
        strength * (-0.0018 * chin + 0.0012 * malar),
    ))


def deform_all_shape_keys(obj, strength):
    keys = obj.data.shape_keys.key_blocks if obj.data.shape_keys else None
    basis = keys[0] if keys else None
    original = [point.co.copy() for point in (basis.data if basis else obj.data.vertices)]
    deltas = [delta_for(co, strength) for co in original]
    if keys:
        for key in keys:
            for index, delta in enumerate(deltas):
                key.data[index].co += delta
    else:
        for index, delta in enumerate(deltas):
            obj.data.vertices[index].co += delta
    changed = [d.length for d in deltas if d.length > 1e-8]
    obj.data.update()
    return {
        "verticesChangedPerShape": len(changed),
        "shapeKeysChanged": len(keys) if keys else 0,
        "maximumDeltaMm": max(changed) * 1000.0 if changed else 0.0,
        "meanChangedDeltaMm": sum(changed) / len(changed) * 1000.0 if changed else 0.0,
        "regions": ["malar projection and width", "lower-cheek plane", "jaw taper", "chin projection"],
    }


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


def clearance(tree, point):
    hit = tree.find_nearest(point)
    if not hit or hit[1] is None:
        return None
    return (point - hit[0]).dot(hit[1].normalized())


def collision_audit(scene, body):
    result = {}
    for frame in FRAMES:
        scene.frame_set(frame)
        depsgraph = bpy.context.evaluated_depsgraph_get()
        depsgraph.update()
        tree = body_tree(body, depsgraph)
        frame_result = {}
        hair = bpy.data.objects[HAIR].evaluated_get(depsgraph)
        values = [clearance(tree, hair.matrix_world @ point.position) for point in hair.data.points]
        values = [value for value in values if value is not None]
        frame_result[HAIR] = {
            "elementsTested": len(values),
            "minimumSignedClearanceM": min(values),
            "penetratingElements": sum(value < -0.00005 for value in values),
        }
        for name in BROWS:
            obj = bpy.data.objects[name].evaluated_get(depsgraph)
            values = [clearance(tree, obj.matrix_world @ vertex.co) for vertex in obj.data.vertices]
            values = [value for value in values if value is not None]
            frame_result[name] = {
                "elementsTested": len(values),
                "minimumSignedClearanceM": min(values),
                "penetratingElements": sum(value < -0.00005 for value in values),
            }
        result[str(frame)] = frame_result
    scene.frame_set(1)
    return result


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, label, view, frame=1, hide_hair=False):
    camera = scene.camera
    views = {
        "front": ((0.0, -0.64, 1.47), (0.0, -0.035, 1.445), 100, (1200, 1000)),
        "oblique": ((0.26, -0.62, 1.48), (0.0, -0.035, 1.445), 100, (1200, 1000)),
        "profile": ((0.64, -0.12, 1.47), (0.0, -0.02, 1.43), 95, (1000, 1000)),
    }
    scene.frame_set(frame)
    camera.location, target, camera.data.lens, size = views[view]
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    hair = bpy.data.objects[HAIR]
    scalp = bpy.data.objects["AevryndFemaleTargetScalp_R976"]
    old = (hair.hide_render, scalp.hide_render)
    if hide_hair:
        hair.hide_render = scalp.hide_render = True
    suffix = "-structure" if hide_hair else ""
    path = EVIDENCE / f"{label}-{view}{suffix}-f{frame:02d}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    hair.hide_render, scalp.hide_render = old
    return str(path)


EVIDENCE.mkdir(parents=True, exist_ok=True)
variants = []
for label, strength in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    body = bpy.data.objects[BODY]
    edit = deform_all_shape_keys(body, strength)
    collision = collision_audit(scene, body)
    penetrations = sum(item["penetratingElements"] for frame in collision.values() for item in frame.values())
    renders = [
        render(scene, label, "front"),
        render(scene, label, "oblique"),
        render(scene, label, "profile"),
        render(scene, label, "oblique", hide_hair=True),
        render(scene, label, "front", frame=33),
    ]
    status = "TECHNICAL_PASS" if penetrations == 0 else "TECHNICAL_FAIL"
    variants.append({
        "label": label,
        "strength": strength,
        "edit": edit,
        "collisionAudit": collision,
        "totalPenetratingElements": penetrations,
        "technicalStatus": status,
        "renders": renders,
    })
    if label == SELECTED and status == "TECHNICAL_PASS":
        scene["aevrynd_revision"] = "female-next-r0002-face-structure-study"
        scene["aevrynd_source_revision"] = "female-next-r0001"
        scene["aevrynd_release_state"] = "VISUAL_REVIEW_PENDING"
        scene["aevrynd_website_promotion"] = "forbidden"
        scene["aevrynd_runtime_export"] = "not-generated"
        body["aevrynd_face_structure_method"] = "smooth malar, lower-cheek, jaw and chin deformation propagated through all shape keys"
        scene.frame_set(1)
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "revision": "female-next-r0002-face-structure-sweep",
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "hypothesis": "A geometry-first increase in malar projection plus a narrower lower cheek and jaw with modest chin projection will make the face less flat without changing lighting, skin, eyes or hair.",
    "topologyChanged": False,
    "materialsChanged": False,
    "shapeKeyPropagation": "identical per-vertex basis delta applied to all 35 keys",
    "variants": variants,
    "provisionalSelection": SELECTED,
    "visualStatus": "VISUAL_REVIEW_PENDING",
    "enginePromotionApproved": False,
    "websitePromotionApproved": False,
}
REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print("AEVRYND_FEMALE_NEXT_R0002=" + json.dumps({
    "variants": [{
        "label": variant["label"],
        "maxDeltaMm": variant["edit"]["maximumDeltaMm"],
        "changedVertices": variant["edit"]["verticesChangedPerShape"],
        "penetrations": variant["totalPenetratingElements"],
        "status": variant["technicalStatus"],
    } for variant in variants]
}, sort_keys=True))
