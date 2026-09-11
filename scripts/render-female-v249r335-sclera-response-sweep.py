import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-continuous-upper-lower-eyelids-r334.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-sclera-response-r335.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r335-sclera-response-sweep"
VARIANTS = (
    ("a-r334-baseline", (0.58, 0.46, 0.42, 1.0), (0.94, 0.86, 0.76, 1.0), 0.18, 0.12),
    ("b-warm-natural", (0.46, 0.37, 0.34, 1.0), (0.76, 0.68, 0.62, 1.0), 0.14, 0.16),
    ("c-muted-natural", (0.39, 0.33, 0.31, 1.0), (0.66, 0.60, 0.56, 1.0), 0.12, 0.18),
    ("d-neutral-soft", (0.47, 0.42, 0.40, 1.0), (0.78, 0.74, 0.70, 1.0), 0.12, 0.17),
)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def eye_nodes(side):
    material = bpy.data.materials[f"Aevrynd_IntegratedEye_{side}_R328"]
    ramps = [node for node in material.node_tree.nodes if node.bl_idname == "ShaderNodeValToRGB"]
    sclera = next(node for node in ramps if node.color_ramp.elements[1].color[0] > 0.5)
    shader = next(node for node in material.node_tree.nodes if node.bl_idname == "ShaderNodeBsdfPrincipled")
    return material, sclera, shader


def image_metrics(path):
    image = bpy.data.images.load(str(path), check_existing=False)
    pixels = image.pixels[:]
    width, height = image.size
    # Central band contains both eyes in the dedicated close render. Values are scene-linear.
    values = []
    clipped = 0
    count = 0
    for y in range(int(height * 0.36), int(height * 0.64)):
        for x in range(int(width * 0.06), int(width * 0.94)):
            i = (y * width + x) * 4
            rgb = pixels[i:i + 3]
            luminance = 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]
            if luminance > 0.55:
                values.append(luminance)
                clipped += int(max(rgb) >= 0.99)
            count += 1
    bpy.data.images.remove(image)
    return {
        "brightEyeBandMeanLinear": sum(values) / len(values) if values else 0.0,
        "brightEyeBandSamples": len(values),
        "nearClipPercentOfBrightSamples": 100.0 * clipped / len(values) if values else 0.0,
        "cropSamples": count,
    }


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.view_settings.look = "Medium High Contrast"
scene.view_settings.exposure = 0.0
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
views = (
    ("eyes", (0.0, -0.46, 1.615), (0.0, -0.035, 1.610), 105),
    ("face", (0.0, -0.68, 1.605), (0.0, -0.035, 1.606), 92),
    ("three-quarter", (0.45, -0.62, 1.62), (0.0, -0.02, 1.605), 90),
)
metrics = {}
for label, low, high, coat, coat_roughness in VARIANTS:
    for side in ("L", "R"):
        material, ramp, shader = eye_nodes(side)
        ramp.color_ramp.elements[0].color = low
        ramp.color_ramp.elements[1].color = high
        shader.inputs["Coat Weight"].default_value = coat
        shader.inputs["Coat Roughness"].default_value = coat_roughness
        material["aevrynd_r335_variant"] = label
    bpy.context.view_layer.update()
    files = {}
    for view_name, location, target, lens in views:
        camera.location = location
        camera.data.lens = lens
        look_at(camera, target)
        scene.render.resolution_x = scene.render.resolution_y = 1000
        path = RENDER_DIR / f"{label}-{view_name}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        files[view_name] = str(path)
    metrics[label] = {
        "scleraRamp": {"low": list(low), "high": list(high)},
        "coatWeight": coat,
        "coatRoughness": coat_roughness,
        "fixedExposureEV": 0.0,
        "eyeBandMetrics": image_metrics(Path(files["eyes"])),
        "renders": files,
    }

report = {
    "source": str(SOURCE),
    "renderDirectory": str(RENDER_DIR),
    "variants": metrics,
    "method": "Fixed-camera, fixed-0EV sweep of only the integrated sclera ramp and corneal coat response; body, lights, skin and geometry remain unchanged.",
    "status": "VISUAL_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R335_SCLERA_RESPONSE=" + json.dumps(report, sort_keys=True))
