import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cc0-rig-transfer-r250.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cc0-normalized-rig-r251.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-cc0-normalized-rig-r251.build-report.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r251-cc0-normalized-rig"
BODY = "AevryndFemaleBody_CC0_R249"


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, location, target, lens, size):
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene = bpy.context.scene
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)


def normalize_weights(body):
    changed = 0
    before_min = float("inf")
    before_max = 0.0
    maximum_change = 0.0
    for vertex in body.data.vertices:
        values = [(entry.group, entry.weight) for entry in vertex.groups if entry.weight > 0.0]
        total = sum(weight for _group, weight in values)
        before_min = min(before_min, total)
        before_max = max(before_max, total)
        if total <= 1e-12:
            continue
        for group_index, weight in values:
            normalized = weight / total
            maximum_change = max(maximum_change, abs(normalized - weight))
            body.vertex_groups[group_index].add([vertex.index], normalized, "REPLACE")
        if abs(total - 1.0) > 1e-7:
            changed += 1
    after = [sum(entry.weight for entry in vertex.groups) for vertex in body.data.vertices]
    return {
        "verticesChanged": changed,
        "beforeMinimumSum": before_min,
        "beforeMaximumSum": before_max,
        "afterMinimumSum": min(after),
        "afterMaximumSum": max(after),
        "maximumSingleWeightChange": maximum_change,
    }


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
body = bpy.data.objects[BODY]
metrics = normalize_weights(body)
body["aevrynd_revision"] = "v249r251-cc0-normalized-rig"
body["aevrynd_weight_method"] = "surface proximity transfer followed by per-vertex normalization"
scene["aevrynd_mainline_revision"] = "v249r251-cc0-normalized-rig"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "DEFORMATION_AUDIT_PENDING"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
views = (
    (1, "01-neutral-full", (0.0, -4.45, 1.10), (0.0, 0.0, 1.00), 76, (900, 1200)),
    (20, "02-pose-full", (0.0, -4.45, 1.10), (0.0, 0.0, 1.00), 76, (900, 1200)),
    (20, "03-pose-face", (0.62, -1.0, 1.64), (0.0, 0.0, 1.60), 88, (1000, 1000)),
)
for frame, name, location, target, lens, size in views:
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    render(camera, name, location, target, lens, size)
scene.frame_set(1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "normalization": metrics,
    "status": "DEFORMATION_AUDIT_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R251_NORMALIZED_RIG=" + json.dumps(report, sort_keys=True))
