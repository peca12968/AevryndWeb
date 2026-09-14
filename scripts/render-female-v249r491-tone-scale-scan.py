import json
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-lip-response-r490.blend"
BASE_IMAGE = ASSETS / "reviews/v249r491-skin-breakup-sweep/baseline-face-f01.png"
OUT = ASSETS / "reviews/v249r491-tone-scale-scan"
REPORT = ASSETS / "female-v249-mainline-skin-breakup-r491.scale-scan.json"
BODY = "AevryndFemaleBodyBaseV118"
SCALES = (72, 78, 84, 90, 96, 102, 108, 114, 120)
RECTANGLES = {
    "leftCheek": (0.13, 0.28, 0.31, 0.54),
    "rightCheek": (0.69, 0.28, 0.87, 0.54),
    "forehead": (0.42, 0.77, 0.58, 0.90),
    "wholeFace": (0.08, 0.02, 0.92, 0.92),
}


def look(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def luminance(path, rectangle):
    image = bpy.data.images.load(str(path), check_existing=False)
    width, height = image.size
    pixels = image.pixels[:]
    x0, y0, x1, y1 = [
        int(value * (width if index % 2 == 0 else height))
        for index, value in enumerate(rectangle)
    ]
    total = 0.0
    count = 0
    for y in range(y0, y1):
        for x in range(x0, x1):
            offset = (y * width + x) * 4
            total += 0.2126 * pixels[offset] + 0.7152 * pixels[offset + 1] + 0.0722 * pixels[offset + 2]
            count += 1
    bpy.data.images.remove(image)
    return total / count


OUT.mkdir(parents=True, exist_ok=True)
baseline = {name: luminance(BASE_IMAGE, rectangle) for name, rectangle in RECTANGLES.items()}
results = []
for scale in SCALES:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    body = bpy.data.objects[BODY]
    material = body.active_material.copy()
    body.data.materials.clear()
    body.data.materials.append(material)
    noise = material.node_tree.nodes["Aevrynd anatomical tone breakup"]
    ramp = material.node_tree.nodes["Aevrynd restrained melanin range"]
    noise.inputs["Scale"].default_value = scale
    ramp.color_ramp.elements[0].color = (0.115, 0.033, 0.019, 1.0)
    ramp.color_ramp.elements[-1].color = (0.155, 0.049, 0.028, 1.0)
    scene.render.engine = "BLENDER_EEVEE"
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0
    scene.view_settings.gamma = 1
    scene.render.resolution_x = 1100
    scene.render.resolution_y = 1100
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
    scene.camera = camera
    camera.location = (0, -0.560, 1.585)
    camera.data.lens = 108
    look(camera, (0, -0.060, 1.585))
    output = OUT / f"scale-{scale}-face-f01.png"
    scene.render.filepath = str(output)
    bpy.ops.render.render(write_still=True)
    regions = {}
    passed = True
    for name, rectangle in RECTANGLES.items():
        candidate = luminance(output, rectangle)
        delta = (candidate - baseline[name]) * 100.0 / baseline[name]
        regions[name] = delta
        if abs(delta) > 1.0:
            passed = False
    results.append({"scale": scale, "deltaPercent": regions, "toneGate": "PASS" if passed else "FAIL"})

report = {
    "source": str(SOURCE),
    "baselineImage": str(BASE_IMAGE),
    "fixedRamp": {
        "dark": [0.115, 0.033, 0.019, 1.0],
        "light": [0.155, 0.049, 0.028, 1.0]
    },
    "results": results,
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R491_SCALE_SCAN=" + json.dumps(report, sort_keys=True))
