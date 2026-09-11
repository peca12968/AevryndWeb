import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-scalp-boundary-cleanup-r283.blend"
REFERENCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-balanced-back-chain-motion-r279.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-safe-tip-transition-r284.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-safe-tip-transition-r284.build-report.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r284-safe-tip-transition"
CARDS = "AevryndFemaleRuntimeHairCards_R276"
POINTS = 24
STRIDE = POINTS * 2


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


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
cards = bpy.data.objects[CARDS]
reference_mesh_name = cards.data.name
with bpy.data.libraries.load(str(REFERENCE), link=False) as (data_from, data_to):
    if reference_mesh_name not in data_from.meshes:
        raise RuntimeError(f"reference mesh missing: {reference_mesh_name}")
    data_to.meshes = [reference_mesh_name]
reference_mesh = data_to.meshes[0]
if len(reference_mesh.vertices) != len(cards.data.vertices):
    raise RuntimeError("reference/current vertex count mismatch")
restored = []
maximum_delta = 0.0
for card_index in range(len(cards.data.vertices) // STRIDE):
    base = card_index * STRIDE
    for point in (15, 16, 17):
        for side in (0, 1):
            index = base + point * 2 + side
            delta = (cards.data.vertices[index].co - reference_mesh.vertices[index].co).length
            maximum_delta = max(maximum_delta, delta)
            cards.data.vertices[index].co = reference_mesh.vertices[index].co.copy()
            restored.append(index)
cards.data.update()
bpy.data.meshes.remove(reference_mesh)
cards["aevrynd_revision"] = "v249r284"
cards["aevrynd_tip_shortening_start_point"] = 18
scene["aevrynd_mainline_revision"] = "v249r284-safe-tip-transition"
scene["aevrynd_release_state"] = "SAFE_TIP_TRANSITION_PENDING_DYNAMIC_AUDIT"
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
    "source": str(SOURCE), "reference": str(REFERENCE), "output": str(OUTPUT),
    "cardObject": CARDS, "restoredPointsPerCard": [15, 16, 17],
    "restoredVertices": len(restored), "maximumRestoredDeltaM": maximum_delta,
    "tipShorteningNowStartsAtPoint": 18, "scalpLayerPreserved": "AevryndFemaleScalpUnderlayer_R280",
    "geometryVertexCountChanged": False, "ownedAssetOnly": True,
    "renderDirectory": str(RENDER_DIR), "status": "DYNAMIC_AND_VISUAL_REAUDIT_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R284_SAFE_TIP_TRANSITION=" + json.dumps(report, sort_keys=True))
