import json
from pathlib import Path

import bpy
import math
from mathutils import Matrix, Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-pruned-dynamic-outliers-r298.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-eye-depth-sclera-r300.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r300-eye-depth-sclera-sweep"
SCLERA_MATERIAL = "Aevrynd_EyeSclera_Physical_R252"
EYE_OBJECTS = [
    f"AevryndEye_{side}_{part}"
    for side in ("L", "R")
    for part in ("Sclera_R249", "Cornea_R252", "Limbal_R253", "Iris_R253", "Pupil_R253")
]
IRIS_OBJECTS = [
    f"AevryndEye_{side}_{part}"
    for side in ("L", "R")
    for part in ("Limbal_R253", "Iris_R253", "Pupil_R253")
]
FRONT_OBJECTS = [
    f"AevryndEye_{side}_{part}"
    for side in ("L", "R")
    for part in ("Cornea_R252", "Limbal_R253", "Iris_R253", "Pupil_R253")
]
ORIGINALS = {}


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def set_variant(depth_m, iris_scale, iris_z_m, gaze_deg, toned):
    for name in EYE_OBJECTS:
        obj = bpy.data.objects[name]
        originals = ORIGINALS[name]
        for vertex, coordinate in zip(obj.data.vertices, originals):
            vertex.co = coordinate
        if depth_m:
            for vertex in obj.data.vertices:
                vertex.co.y += depth_m
        obj.data.update()
    if iris_scale != 1.0:
        for name in IRIS_OBJECTS:
            obj = bpy.data.objects[name]
            center_x = sum(vertex.co.x for vertex in obj.data.vertices) / len(obj.data.vertices)
            center_z = sum(vertex.co.z for vertex in obj.data.vertices) / len(obj.data.vertices)
            for vertex in obj.data.vertices:
                vertex.co.x = center_x + (vertex.co.x - center_x) * iris_scale
                vertex.co.z = center_z + (vertex.co.z - center_z) * iris_scale
            obj.data.update()
    if iris_z_m:
        for name in IRIS_OBJECTS:
            obj = bpy.data.objects[name]
            for vertex in obj.data.vertices:
                vertex.co.z += iris_z_m
            obj.data.update()
    if gaze_deg:
        for side in ("L", "R"):
            sclera = bpy.data.objects[f"AevryndEye_{side}_Sclera_R249"]
            center = sum((vertex.co for vertex in sclera.data.vertices), Vector()) / len(sclera.data.vertices)
            rotation = Matrix.Rotation(math.radians(gaze_deg), 4, "X")
            for part in ("Cornea_R252", "Limbal_R253", "Iris_R253", "Pupil_R253"):
                obj = bpy.data.objects[f"AevryndEye_{side}_{part}"]
                for vertex in obj.data.vertices:
                    vertex.co = center + rotation @ (vertex.co - center)
                obj.data.update()
    ramp = next(node for node in bpy.data.materials[SCLERA_MATERIAL].node_tree.nodes if node.type == "VALTORGB")
    if toned:
        ramp.color_ramp.elements[0].color = (0.29, 0.235, 0.195, 1.0)
        ramp.color_ramp.elements[1].color = (0.60, 0.535, 0.465, 1.0)
    else:
        ramp.color_ramp.elements[0].color = (0.46, 0.39, 0.32, 1.0)
        ramp.color_ramp.elements[1].color = (0.78, 0.70, 0.61, 1.0)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
for name in EYE_OBJECTS:
    obj = bpy.data.objects[name]
    ORIGINALS[name] = [vertex.co.copy() for vertex in obj.data.vertices]
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
camera.location = (0.0, -0.68, 1.605)
camera.data.lens = 92
look_at(camera, (0.0, -0.035, 1.606))
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
variants = [
    {"name": "a-current", "depthM": 0.0, "irisScale": 1.0, "irisZM": 0.0, "gazeDeg": 0.0, "tonedSclera": False},
    {"name": "b-toned", "depthM": 0.0, "irisScale": 1.0, "irisZM": 0.0, "gazeDeg": 0.0, "tonedSclera": True},
    {"name": "c-toned-depth12", "depthM": 0.0012, "irisScale": 1.0, "irisZM": 0.0, "gazeDeg": 0.0, "tonedSclera": True},
    {"name": "d-toned-depth22", "depthM": 0.0022, "irisScale": 1.0, "irisZM": 0.0, "gazeDeg": 0.0, "tonedSclera": True},
    {"name": "e-toned-depth12-iris108", "depthM": 0.0012, "irisScale": 1.08, "irisZM": 0.0, "gazeDeg": 0.0, "tonedSclera": True},
    {"name": "f-toned-depth12-iris115", "depthM": 0.0012, "irisScale": 1.15, "irisZM": 0.0, "gazeDeg": 0.0, "tonedSclera": True},
    {"name": "g-toned-depth12-iris122", "depthM": 0.0012, "irisScale": 1.22, "irisZM": 0.0, "gazeDeg": 0.0, "tonedSclera": True},
    {"name": "h-toned-depth12-iris108-up08", "depthM": 0.0012, "irisScale": 1.08, "irisZM": 0.0008, "gazeDeg": 0.0, "tonedSclera": True},
    {"name": "i-toned-depth12-iris110-up08", "depthM": 0.0012, "irisScale": 1.10, "irisZM": 0.0008, "gazeDeg": 0.0, "tonedSclera": True},
    {"name": "j-toned-depth12-iris108-gaze35", "depthM": 0.0012, "irisScale": 1.08, "irisZM": 0.0, "gazeDeg": -3.5, "tonedSclera": True},
    {"name": "k-toned-depth12-iris108-gaze50", "depthM": 0.0012, "irisScale": 1.08, "irisZM": 0.0, "gazeDeg": -5.0, "tonedSclera": True},
]
for variant in variants:
    set_variant(variant["depthM"], variant["irisScale"], variant["irisZM"], variant["gazeDeg"], variant["tonedSclera"])
    scene.render.filepath = str(RENDER_DIR / f"{variant['name']}.png")
    bpy.ops.render.render(write_still=True)
set_variant(0.0, 1.0, 0.0, 0.0, False)
REPORT.write_text(json.dumps({
    "source": str(SOURCE), "variants": variants, "renderDirectory": str(RENDER_DIR),
    "status": "VISUAL_SELECTION_PENDING", "modelChanged": False,
}, indent=2), encoding="utf-8")
print("AEVRYND_V249R300_EYE_SWEEP=" + json.dumps({"variants": variants, "renderDirectory": str(RENDER_DIR)}, sort_keys=True))
