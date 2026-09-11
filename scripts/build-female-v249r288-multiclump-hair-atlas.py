import json
import math
import random
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-matte-root-underlayer-r287.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-multiclump-hair-atlas-r288.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-multiclump-hair-atlas-r288.build-report.json"
TEXTURE = ROOT / "assets-source/aevrynd-character/textures/aevrynd-owned-hair-multiclump-r288.png"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r288-multiclump-hair-atlas"
CARDS = "AevryndFemaleRuntimeHairCards_R276"
MATERIAL = "Aevrynd_RuntimeHairCards_Multiclump_R288"
IMAGE_NAME = "AevryndOwnedHairMulticlump_R288"
POINTS = 24
CARD_COUNT = 384
WIDTH = 1024
HEIGHT = 2048
SLOTS = 8
SLOT_WIDTH = WIDTH // SLOTS


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def smoothstep(value):
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def look_at(obj, target):
    from mathutils import Vector

    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def create_atlas():
    rng = random.Random(2880811)
    pixels = [0.0] * (WIDTH * HEIGHT * 4)
    reports = []
    for slot in range(SLOTS):
        strand_count = (23, 29, 34, 26, 31, 37, 25, 32)[slot]
        centers = []
        for strand in range(strand_count):
            family = strand % 3
            family_center = (0.26, 0.51, 0.75)[family]
            centers.append(clamp(rng.gauss(family_center, 0.075), 0.055, 0.945))
        strand_data = []
        for strand, center in enumerate(centers):
            strand_data.append({
                "center": center,
                "width": rng.uniform(0.0040, 0.0115),
                "phase": rng.uniform(-math.pi, math.pi),
                "frequency": rng.uniform(0.55, 1.45),
                "wave": rng.uniform(0.005, 0.024),
                "drift": rng.uniform(-0.075, 0.075),
                "tip": rng.uniform(0.76, 1.0),
                "tone": rng.uniform(0.72, 1.12),
            })
        alpha_sum = 0.0
        coverage = 0
        for y in range(HEIGHT):
            v = y / (HEIGHT - 1)
            root_fade = smoothstep(v / 0.018)
            for local_x in range(SLOT_WIDTH):
                u = local_x / (SLOT_WIDTH - 1)
                alpha = 0.0
                tone_weight = 0.0
                for strand in strand_data:
                    if v >= strand["tip"]:
                        continue
                    tip_fade = 1.0 - smoothstep((v - strand["tip"] + 0.13) / 0.13)
                    center = (
                        strand["center"]
                        + strand["wave"] * math.sin(math.tau * strand["frequency"] * v + strand["phase"]) * (0.18 + 0.82 * v)
                        + strand["drift"] * v * v
                    )
                    distance = abs(u - center)
                    fiber = clamp(1.0 - distance / strand["width"])
                    value = fiber * tip_fade * root_fade
                    # Accumulation makes small natural clusters where fibers cross,
                    # while preserving transparent channels between the three families.
                    alpha = 1.0 - (1.0 - alpha) * (1.0 - value * 0.88)
                    tone_weight = max(tone_weight, value * strand["tone"])
                # A short root veil fills only the first fifth of the card. It avoids
                # scalp pinholes without turning the full length into an opaque ribbon.
                edge = 1.0 - smoothstep((abs(u - 0.5) - 0.43) / 0.055)
                root_veil = edge * (1.0 - smoothstep((v - 0.035) / 0.19)) * 0.22 * root_fade
                alpha = clamp(alpha + root_veil)
                alpha_sum += alpha
                coverage += int(alpha > 0.08)
                slot_warmth = (-0.08, 0.03, 0.09, -0.02, 0.06, -0.05, 0.11, 0.0)[slot]
                fiber_light = clamp(0.72 + 0.23 * tone_weight + slot_warmth, 0.58, 1.08)
                base = (0.034 * fiber_light, 0.0108 * fiber_light, 0.0056 * fiber_light)
                x = slot * SLOT_WIDTH + local_x
                offset = (y * WIDTH + x) * 4
                pixels[offset:offset + 4] = (base[0], base[1], base[2], alpha)
        reports.append({
            "slot": slot,
            "strands": strand_count,
            "meanAlpha": alpha_sum / (HEIGHT * SLOT_WIDTH),
            "coverageAbove008": coverage / (HEIGHT * SLOT_WIDTH),
        })
    old = bpy.data.images.get(IMAGE_NAME)
    if old:
        bpy.data.images.remove(old)
    image = bpy.data.images.new(IMAGE_NAME, width=WIDTH, height=HEIGHT, alpha=True)
    image.pixels.foreach_set(pixels)
    image.filepath_raw = str(TEXTURE)
    image.file_format = "PNG"
    image.colorspace_settings.name = "sRGB"
    TEXTURE.parent.mkdir(parents=True, exist_ok=True)
    image.save()
    image.pack()
    image["aevrynd_ownership"] = "procedurally generated in-project"
    image["aevrynd_license"] = "Aevrynd-owned"
    image["aevrynd_revision"] = "v249r288"
    return image, reports


def assign_staggered_uv(mesh):
    old = mesh.uv_layers.get("AevryndRuntimeHairCardUV")
    if old:
        mesh.uv_layers.remove(old)
    uv = mesh.uv_layers.new(name="AevryndRuntimeHairCardUV_R288")
    stride = POINTS * 2
    inset = 2.0 / WIDTH
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            vertex_index = mesh.loops[loop_index].vertex_index
            card_index = vertex_index // stride
            local = vertex_index % stride
            point_index = local // 2
            side = local % 2
            # Prime-number hashing prevents neighboring cards from sampling the
            # same clump family and removes the visible tiled row cadence.
            slot = (card_index * 5 + card_index // 7 + card_index // 29) % SLOTS
            u0 = slot / SLOTS + inset
            u1 = (slot + 1) / SLOTS - inset
            uv.data[loop_index].uv = (u0 if side == 0 else u1, point_index / (POINTS - 1))
    uv.active_render = True
    mesh.uv_layers.active = uv
    return len(uv.data)


def make_material(image):
    material = bpy.data.materials.new(MATERIAL)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = image
    shader.inputs["Roughness"].default_value = 0.46
    shader.inputs["Specular IOR Level"].default_value = 0.16
    anisotropic = shader.inputs.get("Anisotropic IOR Level")
    if anisotropic:
        anisotropic.default_value = 0.72
    alpha_gain = nodes.new("ShaderNodeMath")
    alpha_gain.operation = "MULTIPLY"
    alpha_gain.use_clamp = True
    alpha_gain.inputs[1].default_value = 1.12
    alpha_gain.label = "Natural clump coverage 1.12x"
    links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    links.new(texture.outputs["Alpha"], alpha_gain.inputs[0])
    links.new(alpha_gain.outputs[0], shader.inputs["Alpha"])
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    material.surface_render_method = "DITHERED"
    material.use_transparency_overlap = False
    material["aevrynd_layer"] = "material.hair.runtime_cards.multiclump"
    material["aevrynd_ownership"] = "procedurally generated in-project"
    material["aevrynd_revision"] = "v249r288"
    material["aevrynd_alpha_gain"] = 1.12
    return material


def render(camera, frame, name, location):
    scene = bpy.context.scene
    scene.frame_set(frame)
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    camera.location = location
    camera.data.lens = 82
    look_at(camera, (0.0, 0.0, 1.56))
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
cards = bpy.data.objects[CARDS]
if len(cards.data.vertices) != CARD_COUNT * POINTS * 2:
    raise RuntimeError("unexpected r287 card topology")
image, slot_reports = create_atlas()
uv_loops = assign_staggered_uv(cards.data)
cards.data.materials.clear()
cards.data.materials.append(make_material(image))
cards["aevrynd_revision"] = "v249r288"
cards["aevrynd_atlas_slots"] = SLOTS
cards["aevrynd_visual_change"] = "eight staggered clump families; geometry and weights unchanged"
scene["aevrynd_mainline_revision"] = "v249r288-multiclump-hair-atlas"
scene["aevrynd_hair_layers"] = "scalp_underlayer|runtime_dynamic_cards.multiclump|hairline_transition.head_bound|flyaways"
scene["aevrynd_release_state"] = "MULTICLUMP_VISUAL_REVIEW_PENDING"
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 800
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
for frame, name, location in (
    (1, "front-f01", (0.0, -0.90, 1.59)), (33, "front-f33", (0.0, -0.90, 1.59)),
    (1, "left-f01", (-0.72, -0.55, 1.59)), (1, "right-f01", (0.72, -0.55, 1.59)),
    (1, "back-f01", (0.0, 0.90, 1.59)), (33, "back-f33", (0.0, 0.90, 1.59)),
):
    render(camera, frame, name, location)
scene.frame_set(1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE), "output": str(OUTPUT), "texture": str(TEXTURE),
    "textureSize": [WIDTH, HEIGHT], "atlasSlots": SLOTS, "slotReports": slot_reports,
    "cardObject": CARDS, "cardCount": CARD_COUNT, "uvLoops": uv_loops,
    "material": MATERIAL, "alphaGain": 1.12,
    "geometryChanged": False, "weightsChanged": False, "animationChanged": False,
    "collisionContractChanged": False, "ownedAssetOnly": True,
    "renderDirectory": str(RENDER_DIR), "status": "VISUAL_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R288_MULTICLUMP_ATLAS=" + json.dumps(report, sort_keys=True))
