"""Improve r1060 lip form and replace ineffective mouth expression deltas."""

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-smooth-mouth-transfer-r1060-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-structured-lips-r1061-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1061-lip-form-expression.study.json"
OUT = ROOT.parent / "Temp/female-realism/v249r1061-lip-form-expression"
BODY = "AevryndFemaleCC0SmoothMouth_R1060"
OPEN_KEY = "Aevrynd_MouthOpenTest_R1030"
SMILE_KEY = "Aevrynd_SmileTest_R1030"
NEUTRAL_VARIANTS = (("a-control", 0.0), ("b-restrained", 0.70), ("c-anatomical", 1.0), ("d-strong", 1.30))
SELECTED = "c-anatomical"
EXPRESSION_VALUES = (0.65, 1.0, 1.25)


def gaussian(value, center, sigma):
    return math.exp(-0.5 * ((value - center) / sigma) ** 2)


def smoothstep(edge0, edge1, value):
    if edge0 == edge1:
        return 0.0
    t = max(0.0, min(1.0, (value - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def neutral_mixed_coordinates(body):
    blocks = body.data.shape_keys.key_blocks
    basis = blocks[0]
    coordinates = [item.co.copy() for item in basis.data]
    for block in blocks[1:]:
        if block.name in (OPEN_KEY, SMILE_KEY) or block.mute or abs(block.value) < 1e-8:
            continue
        relative = block.relative_key
        for index, coordinate in enumerate(coordinates):
            coordinate += block.value * (block.data[index].co - relative.data[index].co)
    return coordinates


def neutral_delta(point):
    ax = abs(point.x)
    side = -1.0 if point.x < 0.0 else 1.0
    if ax > 0.050 or point.y > -0.096 or not (1.355 < point.z < 1.414):
        return Vector()
    front = smoothstep(-0.096, -0.123, point.y)
    width = 1.0 - smoothstep(0.032, 0.049, ax)
    if front <= 0.0 or width <= 0.0:
        return Vector()

    # Recess and round the lower wetline to suppress the razor-bright shelf.
    lower_inner = gaussian(point.z, 1.3843, 0.0024) * width * front
    lower_pad = gaussian(point.z, 1.3783, 0.0052) * width * front
    lower_center = gaussian(ax, 0.0, 0.014)
    lower_outer = smoothstep(0.014, 0.035, ax)
    dy = 0.00046 * lower_inner
    dy += -0.00031 * lower_pad * (0.72 + 0.28 * lower_center)
    dy += 0.00022 * lower_pad * lower_outer
    dz = -0.00018 * lower_inner + 0.00008 * lower_pad * lower_center

    # Paired upper-lip volumes and a central notch make the Cupid bow readable.
    upper = gaussian(point.z, 1.3940, 0.0052) * width * front
    cupid = gaussian(ax, 0.0105, 0.0046)
    notch = gaussian(ax, 0.0, 0.0038)
    dy += -0.00038 * upper * (0.70 + 0.36 * cupid - 0.13 * notch)
    dz += 0.00036 * upper * cupid - 0.00025 * upper * notch

    # Close the lip mass into a short recessed commissure instead of a point.
    corner = gaussian(ax, 0.0355, 0.0058) * gaussian(point.z, 1.3885, 0.0060) * front
    dx = -side * 0.00034 * corner
    dy += 0.00062 * corner
    dz += 0.00007 * corner

    # Continue the paired bow into a restrained philtrum transition.
    philtrum = gaussian(point.z, 1.4040, 0.0056) * front
    dy += 0.00020 * philtrum * notch - 0.00013 * philtrum * gaussian(ax, 0.0065, 0.0028)
    return Vector((dx, dy, dz))


def expression_delta(point, expression):
    ax = abs(point.x)
    side = -1.0 if point.x < 0.0 else 1.0
    if ax > 0.050 or point.y > -0.094 or not (1.360 < point.z < 1.407):
        return Vector()
    front = smoothstep(-0.094, -0.121, point.y)
    width = 1.0 - smoothstep(0.030, 0.048, ax)
    center = 1.0 - smoothstep(0.018, 0.043, ax)
    upper = gaussian(point.z, 1.3935, 0.0060) * width * front
    lower = gaussian(point.z, 1.3792, 0.0062) * width * front
    seam = gaussian(point.z, 1.3865, 0.0040) * width * front
    corner = gaussian(ax, 0.0355, 0.0062) * gaussian(point.z, 1.3880, 0.0090) * front
    if expression == "open":
        # Separate both lips vertically and recess the wetline into the cavity.
        dz = 0.00072 * upper - 0.00235 * lower
        dy = 0.00034 * seam + 0.00012 * lower
        dx = -side * 0.00018 * corner
        return Vector((dx, dy, dz)) * (0.58 + 0.42 * center)

    # Raise and widen the commissures, with a restrained central lip response.
    dx = side * 0.00165 * corner
    dy = 0.00020 * seam - 0.00018 * corner
    dz = 0.00145 * corner - 0.00022 * upper + 0.00028 * lower
    return Vector((dx, dy, dz))


def apply_neutral(body, strength):
    coordinates = neutral_mixed_coordinates(body)
    inverse3 = body.matrix_world.inverted().to_3x3()
    movements = {}
    for index, coordinate in enumerate(coordinates):
        movement = neutral_delta(body.matrix_world @ coordinate) * strength
        if movement.length > 1e-7:
            movements[index] = inverse3 @ movement
    for block in body.data.shape_keys.key_blocks:
        for index, movement in movements.items():
            block.data[index].co += movement
    body.data.update()
    return movements


def replace_expression(body, name, expression):
    neutral = neutral_mixed_coordinates(body)
    block = body.data.shape_keys.key_blocks[name]
    relative = block.relative_key
    inverse3 = body.matrix_world.inverted().to_3x3()
    moved = 0
    maximum = 0.0
    maximum_vertical = 0.0
    for index, coordinate in enumerate(neutral):
        movement = expression_delta(body.matrix_world @ coordinate, expression)
        block.data[index].co = relative.data[index].co + inverse3 @ movement
        if movement.length > 1e-7:
            moved += 1
            maximum = max(maximum, movement.length)
            maximum_vertical = max(maximum_vertical, abs(movement.z))
    block.value = 0.0
    block.slider_min = 0.0
    block.slider_max = 1.5
    return {"movedVertices": moved, "maximumDeltaMm": maximum * 1000.0, "maximumVerticalMm": maximum_vertical * 1000.0}


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def hide_hair(scene):
    for obj in scene.objects:
        name = obj.name.lower()
        if obj.type == "CURVES" or any(token in name for token in ("groom", "scalp", "haircard", "hairfiber")):
            if not any(token in name for token in ("brow", "lash")):
                obj.hide_render = True


def render(scene, body, label, oblique=False):
    camera = scene.camera
    camera.data.lens = 135
    camera.location = ((-0.105 if oblique else 0.0), -0.43, 1.391)
    look_at(camera, (0.0, -0.115, 1.386))
    scene.render.resolution_x = 1100
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    path = OUT / f"{label}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return str(path)


OUT.mkdir(parents=True, exist_ok=True)
variants = []
for label, strength in NEUTRAL_VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    body = bpy.data.objects[BODY]
    body.name = "AevryndFemaleCC0StructuredLips_R1061"
    hide_hair(scene)
    movements = apply_neutral(body, strength)
    expression_metrics = {
        OPEN_KEY: replace_expression(body, OPEN_KEY, "open"),
        SMILE_KEY: replace_expression(body, SMILE_KEY, "smile"),
    }
    rendered = [render(scene, body, f"{label}-neutral-front"), render(scene, body, f"{label}-neutral-oblique", oblique=True)]
    variant = {
        "label": label,
        "strength": strength,
        "neutralMovedVertices": len(movements),
        "neutralMaximumMoveMm": max((movement.length for movement in movements.values()), default=0.0) * 1000.0,
        "expressions": expression_metrics,
        "renders": rendered,
    }
    if label == SELECTED:
        keys = body.data.shape_keys.key_blocks
        expression_renders = []
        for expression_label, key_name in (("open", OPEN_KEY), ("smile", SMILE_KEY)):
            for value in EXPRESSION_VALUES:
                keys[OPEN_KEY].value = 0.0
                keys[SMILE_KEY].value = 0.0
                keys[key_name].value = value
                expression_renders.append(render(scene, body, f"selected-{expression_label}-{value:.2f}"))
        keys[OPEN_KEY].value = 0.0
        keys[SMILE_KEY].value = 0.0
        variant["expressionRenders"] = expression_renders
        body["aevrynd_revision"] = "v249r1061-structured-lips-expression"
        body["aevrynd_source"] = SOURCE.name
        body["aevrynd_lip_form_strength"] = strength
        scene["aevrynd_release_state"] = "VISUAL_AND_COLLISION_REVIEW_PENDING"
        scene["aevrynd_website_promotion"] = "forbidden"
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    variants.append(variant)

report = {
    "revision": "v249r1061-lip-form-expression",
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "method": "all-shape neutral lip sculpt plus replacement of ineffective mouth-open and smile deltas",
    "variants": variants,
    "selectedVariant": SELECTED,
    "candidateStatus": "VISUAL_AND_COLLISION_REVIEW_PENDING",
    "websitePromotionApproved": False,
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1061_LIPS=" + json.dumps({
    "output": str(OUTPUT),
    "selected": SELECTED,
    "variants": [{"label": item["label"], "moved": item["neutralMovedVertices"], "maxMm": item["neutralMaximumMoveMm"]} for item in variants],
}, sort_keys=True))
