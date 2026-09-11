import json
import math
import random
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-matte-root-underlayer-r287.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-readable-clump-cards-r289.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-readable-clump-cards-r289.build-report.json"
TEXTURE = ROOT / "assets-source/aevrynd-character/textures/aevrynd-owned-hair-readable-clumps-r289.png"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r289-readable-clump-cards"
CARDS = "AevryndFemaleRuntimeHairCards_R276"
MATERIAL = "Aevrynd_RuntimeHairCards_ReadableClumps_R289"
IMAGE_NAME = "AevryndOwnedHairReadableClumps_R289"
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
    rng = random.Random(2890351)
    pixels = [0.0] * (WIDTH * HEIGHT * 4)
    reports = []
    for slot in range(SLOTS):
        lock_count = (3, 4, 4, 5, 3, 5, 4, 4)[slot]
        locks = []
        for lock in range(lock_count):
            center = (lock + 0.5) / lock_count + rng.uniform(-0.035, 0.035)
            locks.append({
                "center": center,
                "rootWidth": rng.uniform(0.115, 0.165) / max(1.0, lock_count / 3.5),
                "tipWidth": rng.uniform(0.024, 0.052),
                "phase": rng.uniform(-math.pi, math.pi),
                "wave": rng.uniform(0.014, 0.045),
                "drift": rng.uniform(-0.12, 0.12),
                "tip": rng.uniform(0.74, 1.0),
            })
        alpha_sum = 0.0
        coverage = 0
        for y in range(HEIGHT):
            v = y / (HEIGHT - 1)
            root_fade = smoothstep(v / 0.012)
            root_merge = 1.0 - smoothstep((v - 0.015) / 0.18)
            for local_x in range(SLOT_WIDTH):
                u = local_x / (SLOT_WIDTH - 1)
                alpha = 0.0
                for lock in locks:
                    if v > lock["tip"]:
                        continue
                    life = clamp(v / lock["tip"])
                    tip_fade = 1.0 - smoothstep((life - 0.80) / 0.20)
                    center = (
                        lock["center"]
                        + lock["wave"] * math.sin(math.tau * (0.65 + slot * 0.035) * v + lock["phase"]) * smoothstep(v)
                        + lock["drift"] * v * v
                    )
                    width = lock["rootWidth"] * (1.0 - smoothstep(v)) + lock["tipWidth"] * smoothstep(v)
                    distance = abs(u - center) / max(width, 1e-5)
                    body = 1.0 - smoothstep((distance - 0.63) / 0.37)
                    alpha = max(alpha, body * tip_fade * root_fade * 0.86)
                # Merge only the card roots, then open readable negative channels.
                edge = 1.0 - smoothstep((abs(u - 0.5) - 0.44) / 0.045)
                alpha = max(alpha, edge * root_merge * root_fade * 0.38)
                # A few thin flyaway-width traces live inside each macro lock.
                trace = 0.0
                for trace_index in range(5):
                    center = (trace_index + 0.7) / 5.4 + 0.028 * math.sin(v * math.tau * (0.8 + trace_index * 0.07) + slot)
                    trace = max(trace, (1.0 - smoothstep((abs(u - center) - 0.006) / 0.010)) * (1.0 - smoothstep((v - 0.78) / 0.22)))
                alpha = clamp(alpha + trace * 0.18)
                alpha_sum += alpha
                coverage += int(alpha > 0.08)
                x = slot * SLOT_WIDTH + local_x
                offset = (y * WIDTH + x) * 4
                # Constant hue removes per-card checkerboarding. Lighting and
                # smooth normals provide the strand-direction variation.
                pixels[offset:offset + 4] = (0.026, 0.0072, 0.0037, alpha)
        reports.append({
            "slot": slot, "macroLocks": lock_count,
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
    image["aevrynd_revision"] = "v249r289"
    return image, reports


def assign_uv_and_smooth(mesh):
    for old in list(mesh.uv_layers):
        mesh.uv_layers.remove(old)
    uv = mesh.uv_layers.new(name="AevryndRuntimeHairCardUV_R289")
    stride = POINTS * 2
    inset = 2.0 / WIDTH
    slot_counts = [0] * SLOTS
    for polygon in mesh.polygons:
        polygon.use_smooth = True
        for loop_index in polygon.loop_indices:
            vertex_index = mesh.loops[loop_index].vertex_index
            card_index = vertex_index // stride
            local = vertex_index % stride
            point_index = local // 2
            side = local % 2
            slot = (card_index * 5 + card_index // 7 + card_index // 29) % SLOTS
            u0 = slot / SLOTS + inset
            u1 = (slot + 1) / SLOTS - inset
            uv.data[loop_index].uv = (u0 if side == 0 else u1, point_index / (POINTS - 1))
            if local == 0:
                slot_counts[slot] += 1
    uv.active_render = True
    mesh.uv_layers.active = uv
    mesh.update()
    return len(uv.data), slot_counts


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
    shader.inputs["Base Color"].default_value = (0.019, 0.0042, 0.0021, 1.0)
    shader.inputs["Roughness"].default_value = 0.52
    shader.inputs["Specular IOR Level"].default_value = 0.12
    anisotropic = shader.inputs.get("Anisotropic IOR Level")
    if anisotropic:
        anisotropic.default_value = 0.66
    links.new(texture.outputs["Alpha"], shader.inputs["Alpha"])
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    material.surface_render_method = "DITHERED"
    material.use_transparency_overlap = False
    material["aevrynd_layer"] = "material.hair.runtime_cards.readable_clumps"
    material["aevrynd_ownership"] = "procedurally generated in-project"
    material["aevrynd_revision"] = "v249r289"
    material["aevrynd_alpha_gain"] = 1.0
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
uv_loops, slot_counts = assign_uv_and_smooth(cards.data)
cards.data.materials.clear()
cards.data.materials.append(make_material(image))
cards["aevrynd_revision"] = "v249r289"
cards["aevrynd_atlas_slots"] = SLOTS
cards["aevrynd_visual_change"] = "readable macro-clump alpha; smooth strip normals; constant hue"
scene["aevrynd_mainline_revision"] = "v249r289-readable-clump-cards"
scene["aevrynd_hair_layers"] = "scalp_underlayer|runtime_dynamic_cards.readable_clumps|hairline_transition.head_bound|flyaways"
scene["aevrynd_release_state"] = "READABLE_CLUMP_VISUAL_REVIEW_PENDING"
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
    "slotCardCounts": slot_counts, "material": MATERIAL, "alphaGain": 1.0,
    "smoothPolygons": sum(polygon.use_smooth for polygon in cards.data.polygons),
    "geometryCoordinatesChanged": False, "topologyChanged": False,
    "weightsChanged": False, "animationChanged": False, "collisionContractChanged": False,
    "ownedAssetOnly": True, "renderDirectory": str(RENDER_DIR), "status": "VISUAL_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R289_READABLE_CLUMP_CARDS=" + json.dumps(report, sort_keys=True))
