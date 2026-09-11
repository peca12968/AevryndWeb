import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-converged-upper-lid-r210.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r230-strand-smoothing-sweep"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-strand-smoothing-r230.sweep-report.json"
MAIN = "AevryndFemaleCC0LongHairStudyMain_v249r85"
VARIANTS = (("a-control", 0.0), ("b-subtle", 0.35), ("c-balanced", 0.60), ("d-strong", 0.85))
PASSES = 2


def smooth_curves(obj, strength):
    data = obj.data
    original = [point.position.copy() for point in data.points]
    positions = [point.copy() for point in original]
    for _ in range(PASSES):
        updated = [point.copy() for point in positions]
        for curve in data.curves:
            start = curve.first_point_index
            end = start + curve.points_length
            for index in range(start + 1, end - 1):
                laplacian = (positions[index - 1] + positions[index + 1]) * 0.5
                updated[index] = positions[index].lerp(laplacian, strength)
        positions = updated
    maximum = 0.0
    mean = 0.0
    changed = 0
    for index, point in enumerate(data.points):
        delta = (positions[index] - original[index]).length
        point.position = positions[index]
        if delta > 1e-8:
            changed += 1
            maximum = max(maximum, delta)
            mean += delta
    data.update_tag()
    return {
        "strength": strength,
        "passes": PASSES,
        "changedPoints": changed,
        "maximumDeltaMm": maximum * 1000.0,
        "meanChangedDeltaMm": (mean / changed * 1000.0) if changed else 0.0,
        "rootAndTipPositionsPreserved": True,
    }


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, filename, location, target, lens):
    scene = bpy.context.scene
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x = 1000
    scene.render.resolution_y = 1000
    scene.render.filepath = str(OUT / filename)
    bpy.ops.render.render(write_still=True)


OUT.mkdir(parents=True, exist_ok=True)
report = {"source": str(SOURCE), "variants": {}, "status": "VISUAL_SELECTION_PENDING"}
for label, strength in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    main = bpy.data.objects[MAIN]
    metrics = smooth_curves(main, strength) if strength else {
        "strength": 0.0,
        "passes": 0,
        "changedPoints": 0,
        "maximumDeltaMm": 0.0,
        "meanChangedDeltaMm": 0.0,
        "rootAndTipPositionsPreserved": True,
    }
    camera = bpy.data.objects["Aevrynd Review Camera"]
    render(camera, f"{label}-01-front-close.png", (0.0, -1.15, 1.57), (0.0, 0.0, 1.55), 92)
    render(camera, f"{label}-02-three-quarter.png", (1.75, -2.10, 1.52), (0.0, 0.0, 1.42), 88)
    render(camera, f"{label}-03-rear.png", (0.0, 2.42, 1.48), (0.0, 0.0, 1.42), 88)
    render(camera, f"{label}-04-top.png", (0.0, -0.22, 2.52), (0.0, 0.0, 1.58), 82)
    report["variants"][label] = metrics
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R230_STRAND_SMOOTHING=" + json.dumps(report, sort_keys=True))
