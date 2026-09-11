import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-per-chain-collision-r278.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-balanced-back-chain-motion-r279.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-balanced-back-chain-motion-r279.build-report.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r279-balanced-back-chain-motion"
RIG = "AevryndFemaleRig"
AMPLIFIED = ("hair_dyn.L.back", "hair_dyn.R.back")


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def smoothstep(value):
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def envelope(frame):
    if frame <= 20 or frame >= 46:
        return 0.0
    if frame <= 33:
        return smoothstep((frame - 20) / 13.0)
    return 1.0 - smoothstep((frame - 33) / 13.0)


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
rig = bpy.data.objects[RIG]
gains = {}
for frame in range(scene.frame_start, scene.frame_end + 1):
    scene.frame_set(frame)
    gain = 1.0 + 0.78 * envelope(frame)
    gains[str(frame)] = gain
    for chain in AMPLIFIED:
        for segment in range(1, 4):
            bone = rig.pose.bones[f"{chain}.{segment:02d}"]
            bone.rotation_euler = tuple(value * gain for value in bone.rotation_euler)
            bone.keyframe_insert("rotation_euler", frame=frame)
rig["aevrynd_hair_back_chain_balance_gain"] = 1.78
rig["aevrynd_hair_back_chain_balance_window"] = "frames 20-46; smooth peak at 33"
scene["aevrynd_mainline_revision"] = "v249r279-balanced-back-chain-motion"
scene["aevrynd_release_state"] = "BALANCED_BACK_CHAIN_MOTION_PENDING_COLLISION_AUDIT"
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
    "source": str(SOURCE), "output": str(OUTPUT), "amplifiedChains": list(AMPLIFIED),
    "peakGain": 1.78, "gainWindow": [20, 46], "peakFrame": 33, "frameGains": gains,
    "geometryChanged": False, "materialChanged": False, "ownedAssetOnly": True,
    "renderDirectory": str(RENDER_DIR), "status": "DYNAMIC_AND_COLLISION_REAUDIT_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R279_BALANCED_BACK_CHAIN_MOTION=" + json.dumps(report, sort_keys=True))
