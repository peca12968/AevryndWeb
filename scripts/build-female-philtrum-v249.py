import json
import runpy
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249.blend"

# The strong sweep ends on the selected 3.0 strength state, reconstructed from
# v248 each run so no experimental deformation is accumulated.
namespace = runpy.run_path(str(ROOT / "scripts/render-female-philtrum-strong-sweep-v248.py"))
body = bpy.data.objects["AevryndFemaleBodyBaseV118"]
body["aevrynd_face_revision"] = 249
body["aevrynd_philtrum_method"] = "correct_height_central_groove_columns_and_cupid_transition"
body["aevrynd_philtrum_max_delta_mm"] = 2.096022051632366
scene = bpy.context.scene
scene["aevrynd_face_revision"] = 249
scene["aevrynd_release_state"] = "CANDIDATE_PENDING_FACE_COLLISION_RUNTIME_AND_VISUAL_GATES"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

camera = bpy.data.objects["Aevrynd Review Camera"]
render = namespace["render"]
render(camera, "v249-face-three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88)
render(camera, "v249-face-profile", (0.70, -0.03, 1.61), (0.0, -0.005, 1.595), 88)
print("AEVRYND_PHILTRUM_V249=" + json.dumps({
    "output": str(OUTPUT), "strength": 3.0,
    "maximum_delta_mm": body["aevrynd_philtrum_max_delta_mm"],
}, sort_keys=True))
