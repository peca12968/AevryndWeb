"""Sculpt broad adult facial identity while preserving the r1028 eye stack."""

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-interpolated-lash-density-r1028-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-whole-face-identity-r1029-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1029-whole-face-identity-sweep.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r1029-whole-face-identity-sweep"
BODY = "AevryndFemaleCC0Baseline_v259"
FRAMES = (1, 20, 33, 61)
VARIANTS = (("a-subtle", 0.55), ("b-balanced", 0.65), ("c-strong", 0.75))
SELECTED = "b-balanced"
FACE_ATTACHMENTS = (
    "Brow_L", "Brow_L_Density", "Brow_R", "Brow_R_Density",
    "Eye_L_Sclera", "Eye_L_Cornea", "Eye_L_UpperLashes", "Eye_L_LowerLashes",
    "Eye_R_Sclera", "Eye_R_Cornea", "Eye_R_UpperLashes", "Eye_R_LowerLashes",
    "Eye_L_MedialCaruncle_R1023", "Eye_R_MedialCaruncle_R1023",
)


def gaussian(value, center, sigma):
    return math.exp(-0.5 * ((value - center) / sigma) ** 2)


def smoothstep(edge0, edge1, value):
    t = max(0.0, min(1.0, (value - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def identity_delta(point, strength):
    """Return a smooth world-space delta from broad, non-eye facial landmarks."""
    ax = abs(point.x)
    side = -1.0 if point.x < 0.0 else 1.0
    front = smoothstep(-0.020, -0.085, point.y)
    eye_zone = gaussian(ax, 0.032, 0.026) * gaussian(point.z, 1.458, 0.020)
    eye_guard = 1.0 - 0.985 * eye_zone
    delta = Vector()
    components = {}

    # Break the oversized spherical forehead without touching the brow fibres.
    forehead = smoothstep(1.494, 1.532, point.z) * smoothstep(0.018, 0.062, ax)
    forehead *= gaussian(point.y, -0.060, 0.070)
    components["forehead_taper"] = Vector((-side * 0.0022 * forehead, 0.0, -0.00035 * forehead))

    temple = gaussian(ax, 0.061, 0.014) * gaussian(point.z, 1.500, 0.020) * front
    components["temple_plane"] = Vector((-side * 0.00105 * temple, 0.00030 * temple, 0.0))

    # Establish a zygomatic high point and a shallower lower-cheek plane.
    malar = gaussian(ax, 0.052, 0.018) * gaussian(point.z, 1.427, 0.018) * gaussian(point.y, -0.108, 0.034) * eye_guard
    components["malar_projection"] = Vector((side * 0.00130 * malar, -0.00135 * malar, 0.00045 * malar))

    buccal = gaussian(ax, 0.052, 0.022) * gaussian(point.z, 1.394, 0.022) * gaussian(point.y, -0.102, 0.038)
    components["buccal_plane"] = Vector((-side * 0.00020 * buccal, 0.00085 * buccal, -0.00015 * buccal))

    # Give the central face a readable bridge, tip and alar transition.
    bridge = gaussian(ax, 0.0, 0.011) * gaussian(point.z, 1.452, 0.025) * gaussian(point.y, -0.126, 0.032) * eye_guard
    components["nasal_bridge"] = Vector((0.0, -0.00090 * bridge, 0.00012 * bridge))

    tip = gaussian(ax, 0.0, 0.014) * gaussian(point.z, 1.417, 0.013) * gaussian(point.y, -0.143, 0.026)
    components["nasal_tip"] = Vector((0.0, -0.00105 * tip, 0.00018 * tip))

    ala = gaussian(ax, 0.019, 0.0085) * gaussian(point.z, 1.408, 0.011) * gaussian(point.y, -0.132, 0.027)
    components["alar_definition"] = Vector((side * 0.00045 * ala, -0.00035 * ala, -0.00010 * ala))

    # Shape the lower third as one continuous mass instead of a round mask.
    jaw = gaussian(ax, 0.065, 0.020) * gaussian(point.z, 1.354, 0.026) * gaussian(point.y, -0.070, 0.055)
    jaw *= 1.0 - gaussian(ax, 0.0, 0.030)
    components["jaw_taper"] = Vector((-side * 0.00225 * jaw, 0.00025 * jaw, 0.00010 * jaw))

    chin = gaussian(ax, 0.0, 0.029) * gaussian(point.z, 1.333, 0.018) * gaussian(point.y, -0.075, 0.040)
    components["chin_projection"] = Vector((0.0, -0.00090 * chin, -0.00035 * chin))

    mental = gaussian(ax, 0.0, 0.031) * gaussian(point.z, 1.360, 0.012) * gaussian(point.y, -0.100, 0.038)
    components["mental_sulcus"] = Vector((0.0, 0.00048 * mental, 0.00010 * mental))

    # A restrained asymmetry keeps mirrored highlights from reading as synthetic.
    asymmetry = gaussian(ax, 0.050, 0.024) * gaussian(point.z, 1.405, 0.040) * front
    components["asymmetry"] = Vector((0.0, (-0.00016 if point.x < 0.0 else 0.00010) * asymmetry, (0.00010 if point.x < 0.0 else -0.00007) * asymmetry))

    # Preserve the exact r1028 lid, lash and brow support surface.  A smooth
    # rectangular falloff reaches zero through the attachment-bearing band.
    protected_x = smoothstep(0.006, 0.016, ax) * (1.0 - smoothstep(0.060, 0.074, ax))
    protected_z = smoothstep(1.432, 1.442, point.z) * (1.0 - smoothstep(1.487, 1.498, point.z))
    attachment_guard = 1.0 - protected_x * protected_z
    guarded = {name: movement * attachment_guard for name, movement in components.items()}
    for movement in guarded.values():
        delta += movement
    return delta * strength, {name: movement.length * strength for name, movement in guarded.items()}


def sculpt_all_shape_keys(body, strength):
    keys = list(body.data.shape_keys.key_blocks)
    basis = keys[0]
    inverse3 = body.matrix_world.inverted().to_3x3()
    deltas = {}
    counts = {}
    maxima = {}
    for vertex in body.data.vertices:
        world = body.matrix_world @ basis.data[vertex.index].co
        if world.z < 1.295 or world.z > 1.550 or abs(world.x) > 0.130 or world.y > 0.005:
            continue
        movement, components = identity_delta(world, strength)
        if movement.length < 0.000002:
            continue
        deltas[vertex.index] = inverse3 @ movement
        for name, amount in components.items():
            if amount > 0.000002:
                counts[name] = counts.get(name, 0) + 1
                maxima[name] = max(maxima.get(name, 0.0), amount)
    for key in keys:
        for index, delta in deltas.items():
            key.data[index].co += delta
    body.data.update()
    return {
        "affectedVertices": len(deltas),
        "shapeKeysMovedTogether": [key.name for key in keys],
        "maximumMoveMm": max(delta.length for delta in deltas.values()) * 1000.0,
        "componentVertexCounts": counts,
        "componentMaxMm": {name: value * 1000.0 for name, value in maxima.items()},
    }


def world_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    polygons = [tuple(poly.vertices) for poly in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, polygons, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


def collision_frames():
    scene = bpy.context.scene
    results = {}
    failures = []
    for frame in FRAMES:
        scene.frame_set(frame)
        depsgraph = bpy.context.evaluated_depsgraph_get()
        depsgraph.update()
        body_tree = world_tree(bpy.data.objects[BODY], depsgraph)
        frame_result = {}
        for name in FACE_ATTACHMENTS:
            if name not in bpy.data.objects:
                continue
            count = len(body_tree.overlap(world_tree(bpy.data.objects[name], depsgraph)))
            frame_result[name] = count
            if count:
                failures.append({"frame": frame, "object": name, "triangleOverlapCount": count})
        for side in ("L", "R"):
            upper = world_tree(bpy.data.objects[f"Eye_{side}_UpperLashes"], depsgraph)
            lower = world_tree(bpy.data.objects[f"Eye_{side}_LowerLashes"], depsgraph)
            sclera = world_tree(bpy.data.objects[f"Eye_{side}_Sclera"], depsgraph)
            cornea = world_tree(bpy.data.objects[f"Eye_{side}_Cornea"], depsgraph)
            for pair, first, second in (
                ("upper-sclera", upper, sclera), ("upper-cornea", upper, cornea),
                ("lower-sclera", lower, sclera), ("lower-cornea", lower, cornea),
                ("upper-lower", upper, lower),
            ):
                count = len(first.overlap(second))
                frame_result[f"Eye_{side}_{pair}"] = count
                if count:
                    failures.append({"frame": frame, "object": f"Eye_{side}_{pair}", "triangleOverlapCount": count})
        results[str(frame)] = frame_result
    return results, failures


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def render_views(scene, label):
    hidden = []
    for obj in scene.objects:
        is_hair = obj.name.startswith(("Groom_", "AevryndFemaleTargetScalp")) or obj.type == "CURVES"
        is_face_fibre = "Brow" in obj.name or obj.name.endswith(("UpperLashes", "LowerLashes"))
        if is_hair and not is_face_fibre and not obj.hide_render:
            obj.hide_render = True
            hidden.append(obj.name)
    scene.render.resolution_x = scene.render.resolution_y = 1000
    camera = scene.camera
    camera.data.lens = 88
    rendered = []
    for view, location, target in (
        ("front", (0.0, -0.72, 1.430), (0.0, -0.060, 1.420)),
        ("three-quarter-left", (0.40, -0.63, 1.438), (0.0, -0.052, 1.415)),
        ("profile-left", (0.68, -0.035, 1.430), (0.0, -0.045, 1.410)),
    ):
        camera.location = location
        look_at(camera, target)
        path = RENDER_DIR / f"{label}-{view}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        rendered.append(str(path))
    for name in hidden:
        bpy.data.objects[name].hide_render = False
    return rendered


RENDER_DIR.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
baseline_scene = bpy.context.scene
baseline_scene.frame_set(1)
bpy.context.view_layer.update()
baseline_rendered = render_views(baseline_scene, "source-r1028")
variants = []
for label, strength in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    bpy.context.view_layer.update()
    body = bpy.data.objects[BODY]
    edit = sculpt_all_shape_keys(body, strength)
    bpy.context.view_layer.update()
    bpy.context.view_layer.update()
    collisions, failures = collision_frames()
    scene.frame_set(1)
    bpy.context.view_layer.update()
    rendered = render_views(scene, label)
    status = "TECHNICAL_PASS" if not failures else "TECHNICAL_FAIL"
    variants.append({
        "label": label,
        "strength": strength,
        "edit": edit,
        "fourFrameBodyAttachmentCollision": collisions,
        "collisionFailures": failures,
        "rendered": rendered,
        "status": status,
    })
    if label == SELECTED and status == "TECHNICAL_PASS":
        scene["aevrynd_mainline_revision"] = "v249r1029-whole-face-identity"
        scene["aevrynd_mainline_parent"] = SOURCE.name
        scene["aevrynd_release_state"] = "TECHNICAL_PASS_VISUAL_REVIEW_REQUIRED"
        scene["aevrynd_website_promotion"] = "forbidden"
        body["aevrynd_face_revision"] = "v249r1029"
        body["aevrynd_face_method"] = "broad adult female forehead, temple, malar, nasal, jaw, chin and asymmetric identity field"
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "method": "smooth broad-form identity field applied identically to every body shape key",
    "baselineRendered": baseline_rendered,
    "variants": variants,
    "provisionalSelection": SELECTED,
    "selectedVariant": None,
    "status": "VISUAL_REVIEW_REQUIRED",
    "topologyChanged": False,
    "websitePromotionApproved": False,
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1029_WHOLE_FACE_IDENTITY=" + json.dumps({
    "output": str(OUTPUT),
    "variants": [{"label": item["label"], "maxMm": item["edit"]["maximumMoveMm"], "affected": item["edit"]["affectedVertices"], "collisions": len(item["collisionFailures"]), "status": item["status"]} for item in variants],
}, sort_keys=True))
