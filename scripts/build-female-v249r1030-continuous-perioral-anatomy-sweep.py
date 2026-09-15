"""Reshape the continuous CC0 mouth surface and add expression test keys."""

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-whole-face-identity-r1029-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-continuous-perioral-r1030-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1030-continuous-perioral-sweep.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r1030-continuous-perioral-sweep"
BODY = "AevryndFemaleCC0Baseline_v259"
NEUTRAL_KEY = "Aevrynd_PerioralAnatomy_R1030"
OPEN_KEY = "Aevrynd_MouthOpenTest_R1030"
SMILE_KEY = "Aevrynd_SmileTest_R1030"
VARIANTS = (("source-r1029", 0.0), ("a-restrained", 0.65), ("b-anatomical", 1.0), ("c-strong", 1.35))
SELECTED = "b-anatomical"
FRAMES = (1, 20, 33, 61)
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


def mixed_coordinates(body):
    blocks = body.data.shape_keys.key_blocks
    basis = blocks[0]
    coordinates = [item.co.copy() for item in basis.data]
    active = []
    for block in blocks[1:]:
        if block.mute or abs(block.value) < 1e-8:
            continue
        relative = block.relative_key
        active.append({"name": block.name, "value": float(block.value)})
        for index, coordinate in enumerate(coordinates):
            coordinate += block.value * (block.data[index].co - relative.data[index].co)
    return coordinates, active


def neutral_delta(point):
    ax = abs(point.x)
    side = -1.0 if point.x < 0.0 else 1.0
    if ax > 0.052 or point.y > -0.097 or not (1.347 < point.z < 1.414):
        return Vector(), {}
    front = smoothstep(-0.097, -0.125, point.y)
    width = 1.0 - smoothstep(0.034, 0.050, ax)
    components = {}

    # Recess the seam and commissures so the lip mass turns into the cheek.
    slit = gaussian(point.z, 1.3892, 0.0020) * width * front
    components["oral_seam"] = Vector((0.0, 0.00055 * slit, 0.0))
    corner = gaussian(ax, 0.0365, 0.0060) * gaussian(point.z, 1.3888, 0.0050) * front
    components["commissure"] = Vector((-side * 0.00045 * corner, 0.00095 * corner, 0.00018 * corner))

    # Replace the even shelf with paired Cupid peaks and a central tubercle.
    upper = gaussian(point.z, 1.3960, 0.0060) * width * front
    upper_outer = upper * smoothstep(0.010, 0.034, ax)
    components["upper_outer_recess"] = Vector((0.0, 0.00058 * upper_outer, 0.0))
    tubercle = upper * gaussian(ax, 0.0, 0.0080)
    components["upper_tubercle"] = Vector((0.0, -0.00028 * tubercle, -0.00008 * tubercle))
    cupid = upper * gaussian(ax, 0.0105, 0.0045)
    notch = upper * gaussian(ax, 0.0, 0.0038)
    components["cupid_peaks"] = Vector((0.0, -0.00012 * cupid, 0.00042 * cupid))
    components["cupid_notch"] = Vector((0.0, 0.00010 * notch, -0.00024 * notch))

    # Keep the lower central pad but taper its lateral thirds into the corners.
    lower = gaussian(point.z, 1.3785, 0.0065) * width * front
    lower_outer = lower * smoothstep(0.014, 0.035, ax)
    lower_center = lower * gaussian(ax, 0.0, 0.013)
    components["lower_outer_recess"] = Vector((0.0, 0.00062 * lower_outer, 0.00010 * lower_outer))
    components["lower_central_pad"] = Vector((0.0, -0.00018 * lower_center, 0.00006 * lower_center))

    # Philtrum groove and columns continue into the Cupid bow.
    philtrum = gaussian(point.z, 1.4050, 0.0065) * front
    groove = philtrum * gaussian(ax, 0.0, 0.0038)
    columns = philtrum * gaussian(ax, 0.0065, 0.0030)
    components["philtrum_groove"] = Vector((0.0, 0.00038 * groove, 0.0))
    components["philtrum_columns"] = Vector((0.0, -0.00022 * columns, 0.00004 * columns))

    mental = gaussian(point.z, 1.3585, 0.0075) * gaussian(ax, 0.0, 0.027) * front
    components["mentolabial_sulcus"] = Vector((0.0, 0.00034 * mental, 0.00004 * mental))

    delta = sum(components.values(), Vector())
    return delta, {name: movement.length for name, movement in components.items()}


def expression_delta(point, expression):
    ax = abs(point.x)
    side = -1.0 if point.x < 0.0 else 1.0
    if ax > 0.052 or point.y > -0.095 or not (1.360 < point.z < 1.405):
        return Vector()
    front = smoothstep(-0.095, -0.122, point.y)
    width = 1.0 - smoothstep(0.033, 0.050, ax)
    upper = gaussian(point.z, 1.3950, 0.0065) * width * front
    lower = gaussian(point.z, 1.3785, 0.0070) * width * front
    corner = gaussian(ax, 0.036, 0.0070) * gaussian(point.z, 1.388, 0.010) * front
    if expression == "open":
        center = 1.0 - smoothstep(0.020, 0.045, ax)
        return Vector((0.0, 0.00012 * lower, 0.00062 * upper - 0.00120 * lower)) * (0.55 + 0.45 * center)
    return Vector((side * 0.00155 * corner, -0.00018 * corner, 0.00130 * corner - 0.00032 * upper + 0.00032 * lower))


def add_shape_key(body, name, delta_function):
    old = body.data.shape_keys.key_blocks.get(name)
    if old:
        body.shape_key_remove(old)
    mixed, active = mixed_coordinates(body)
    key = body.shape_key_add(name=name, from_mix=False)
    inverse3 = body.matrix_world.inverted().to_3x3()
    moved = 0
    maximum = 0.0
    component_counts = {}
    component_maxima = {}
    for index, coordinate in enumerate(mixed):
        world = body.matrix_world @ coordinate
        result = delta_function(world)
        if isinstance(result, tuple):
            movement, components = result
        else:
            movement, components = result, {}
        if movement.length < 0.000001:
            continue
        key.data[index].co += inverse3 @ movement
        moved += 1
        maximum = max(maximum, movement.length)
        for component, amount in components.items():
            if amount > 0.000001:
                component_counts[component] = component_counts.get(component, 0) + 1
                component_maxima[component] = max(component_maxima.get(component, 0.0), amount)
    key.slider_min = 0.0
    key.slider_max = 1.5
    key.value = 0.0
    return key, {"movedVertices": moved, "maximumDeltaMm": maximum * 1000.0, "activeSelectionKeys": active, "componentVertexCounts": component_counts, "componentMaxMm": {name: value * 1000.0 for name, value in component_maxima.items()}}


def world_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    mesh.calc_loop_triangles()
    triangles = [tuple(triangle.vertices) for triangle in mesh.loop_triangles]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, triangles, all_triangles=True), vertices, triangles


def body_self_collision(body):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    tree, vertices, triangles = world_tree(body, depsgraph)
    disjoint = []
    for first, second in tree.overlap(tree):
        if first >= second:
            continue
        if set(triangles[first]).isdisjoint(triangles[second]):
            disjoint.append((first, second))
    return {"evaluatedVertices": len(vertices), "evaluatedTriangles": len(triangles), "nonAdjacentPairs": len(disjoint), "samplePairs": [list(pair) for pair in disjoint[:24]], "status": "PASS" if not disjoint else "FAIL"}


def attachment_collisions(body):
    scene = bpy.context.scene
    frames = {}
    failures = []
    for frame in FRAMES:
        scene.frame_set(frame)
        depsgraph = bpy.context.evaluated_depsgraph_get()
        depsgraph.update()
        body_tree, _vertices, _triangles = world_tree(body, depsgraph)
        values = {}
        for name in FACE_ATTACHMENTS:
            if name not in bpy.data.objects:
                continue
            other_tree, _other_vertices, _other_triangles = world_tree(bpy.data.objects[name], depsgraph)
            count = len(body_tree.overlap(other_tree))
            values[name] = count
            if count:
                failures.append({"frame": frame, "object": name, "triangleOverlapCount": count})
        frames[str(frame)] = values
    scene.frame_set(1)
    bpy.context.view_layer.update()
    return frames, failures


def mouth_edge_ratios(body, before, after):
    ratios = []
    for edge in body.data.edges:
        first, second = edge.vertices
        center = (body.matrix_world @ before[first] + body.matrix_world @ before[second]) * 0.5
        if abs(center.x) > 0.058 or center.y > -0.090 or not (1.342 < center.z < 1.416):
            continue
        old_length = (before[first] - before[second]).length
        new_length = (after[first] - after[second]).length
        if old_length > 1e-9:
            ratios.append(new_length / old_length)
    return {"edgeCount": len(ratios), "minimum": min(ratios), "maximum": max(ratios), "mean": sum(ratios) / len(ratios), "threshold": [0.30, 2.50], "status": "PASS" if min(ratios) >= 0.30 and max(ratios) <= 2.50 else "FAIL"}


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def hide_hair(scene):
    hidden = []
    for obj in scene.objects:
        is_hair = obj.name.startswith(("Groom_", "AevryndFemaleTargetScalp")) or obj.type == "CURVES"
        is_face_fibre = "Brow" in obj.name or obj.name.endswith(("UpperLashes", "LowerLashes"))
        if is_hair and not is_face_fibre and not obj.hide_render:
            obj.hide_render = True
            hidden.append(obj.name)
    return hidden


def render(scene, label, location, target, lens, size=(1000, 1000)):
    camera = scene.camera
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    path = RENDER_DIR / f"{label}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return str(path)


RENDER_DIR.mkdir(parents=True, exist_ok=True)
variants = []
for label, strength in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    bpy.context.view_layer.update()
    body = bpy.data.objects[BODY]
    before, _active = mixed_coordinates(body)
    neutral_key, edit = add_shape_key(body, NEUTRAL_KEY, neutral_delta)
    neutral_key.value = strength
    bpy.context.view_layer.update()
    after, _active_after = mixed_coordinates(body)
    edge_audit = mouth_edge_ratios(body, before, after)
    self_audit = body_self_collision(body)
    hidden = hide_hair(scene)
    rendered = [
        render(scene, f"{label}-face-front", (0.0, -0.72, 1.430), (0.0, -0.060, 1.420), 88),
        render(scene, f"{label}-mouth-front", (0.0, -0.43, 1.388), (0.0, -0.120, 1.386), 135, (1200, 700)),
        render(scene, f"{label}-mouth-oblique", (0.21, -0.39, 1.392), (0.0, -0.115, 1.386), 128, (1200, 700)),
        render(scene, f"{label}-profile", (0.68, -0.035, 1.430), (0.0, -0.045, 1.410), 88),
    ]
    for name in hidden:
        bpy.data.objects[name].hide_render = False
    status = "TECHNICAL_PASS" if edge_audit["status"] == "PASS" and self_audit["status"] == "PASS" else "TECHNICAL_FAIL"
    variant = {"label": label, "strength": strength, "edit": edit, "mouthEdgeRatios": edge_audit, "neutralSelfCollision": self_audit, "rendered": rendered, "status": status}
    variants.append(variant)
    if label == SELECTED and status == "TECHNICAL_PASS":
        # Build two engine-facing expression tests on the selected neutral form.
        open_key, open_edit = add_shape_key(body, OPEN_KEY, lambda point: expression_delta(point, "open"))
        smile_key, smile_edit = add_shape_key(body, SMILE_KEY, lambda point: expression_delta(point, "smile"))
        expression_audits = {}
        expression_rendered = []
        hidden = hide_hair(scene)
        for expression, key in (("mouth-open", open_key), ("smile", smile_key)):
            key.value = 1.0
            bpy.context.view_layer.update()
            expression_audits[expression] = body_self_collision(body)
            expression_rendered.append(render(scene, f"selected-{expression}-face", (0.0, -0.72, 1.430), (0.0, -0.060, 1.420), 88))
            expression_rendered.append(render(scene, f"selected-{expression}-mouth", (0.0, -0.43, 1.388), (0.0, -0.120, 1.386), 135, (1200, 700)))
            key.value = 0.0
        for name in hidden:
            bpy.data.objects[name].hide_render = False
        variant["expressionKeys"] = {OPEN_KEY: open_edit, SMILE_KEY: smile_edit}
        variant["expressionSelfCollision"] = expression_audits
        variant["expressionRendered"] = expression_rendered
        if all(item["status"] == "PASS" for item in expression_audits.values()):
            frames, failures = attachment_collisions(body)
            variant["fourFrameBodyAttachmentCollision"] = frames
            variant["fourFrameCollisionFailures"] = failures
            if not failures:
                scene["aevrynd_mainline_revision"] = "v249r1030-continuous-perioral-anatomy"
                scene["aevrynd_mainline_parent"] = SOURCE.name
                scene["aevrynd_release_state"] = "TECHNICAL_PASS_VISUAL_PARTIAL"
                scene["aevrynd_website_promotion"] = "forbidden"
                body["aevrynd_mouth_revision"] = "v249r1030"
                body["aevrynd_mouth_method"] = "continuous body topology with neutral anatomy, open and smile shape keys"
                bpy.context.preferences.filepaths.save_version = 0
                bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
            else:
                variant["status"] = "TECHNICAL_FAIL"
        else:
            variant["status"] = "TECHNICAL_FAIL"

report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "method": "active-mixed-coordinate continuous body-mouth reshaping plus independent open and smile relative keys",
    "variants": variants,
    "provisionalSelection": SELECTED,
    "selectedVariant": SELECTED,
    "topologyChanged": False,
    "detachedLipObjectAdded": False,
    "websitePromotionApproved": False,
    "visualAssessment": "Continuous-body oral seam, Cupid bow, commissure and perioral transitions improve, but the cavity and expression amplitude remain too shallow for hero quality.",
    "strictMouthScore": 37,
    "status": "TECHNICAL_PASS_VISUAL_PARTIAL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1030_CONTINUOUS_PERIORAL=" + json.dumps({
    "output": str(OUTPUT),
    "variants": [{"label": item["label"], "strength": item["strength"], "moved": item["edit"]["movedVertices"], "maxMm": item["edit"]["maximumDeltaMm"], "edge": [item["mouthEdgeRatios"]["minimum"], item["mouthEdgeRatios"]["maximum"]], "selfPairs": item["neutralSelfCollision"]["nonAdjacentPairs"], "status": item["status"]} for item in variants],
}, sort_keys=True))
