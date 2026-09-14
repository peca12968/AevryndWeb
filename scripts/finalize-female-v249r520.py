import json
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
MODEL = ASSETS / "aevrynd-female-authoring-v249-mainline-natural-eye-ratio-r520.blend"
BUILD = ASSETS / "female-v249-mainline-natural-eye-ratio-r520.build-report.json"
VISUAL = ASSETS / "female-v249-mainline-natural-eye-ratio-r520.visual-review.json"

bpy.ops.wm.open_mainfile(filepath=str(MODEL))
scene = bpy.context.scene
scene["aevrynd_release_state"] = "OFFLINE_TECHNICAL_MAINLINE_ALL_GATES_PASS_VISUAL_HERO_FAIL"
scene["aevrynd_strict_hair_score"] = 47
scene["aevrynd_strict_eye_score"] = 69
scene["aevrynd_strict_face_score"] = 57
scene["aevrynd_strict_overall_score"] = 56
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(MODEL))

build = json.loads(BUILD.read_text(encoding="utf-8"))
build["status"] = "PASS_OFFLINE_TECHNICAL_MAINLINE_VISUAL_HERO_FAIL"
build["audits"] = {
    "faceAndStatic": "female-v249-mainline-natural-eye-ratio-r520.audit.json",
    "runtimeHair": "female-v249-mainline-natural-eye-ratio-r520.runtime-card-audit.json",
    "tone": "female-v249-mainline-natural-eye-ratio-r520.tone-contract-audit.json",
    "performance": "female-v249-mainline-natural-eye-ratio-r520.performance-audit.json",
    "views": "reviews/v249r520-natural-eye-ratio-11shot/contact-sheet-11shot.jpg",
}
BUILD.write_text(json.dumps(build, indent=2), encoding="utf-8")

review = {
    "revision": "v249r520",
    "status": "OFFLINE_TECHNICAL_MAINLINE_VISUAL_HERO_FAIL",
    "selected": "eye aperture strength 0.50; measured aspect 2.23; intact iris local-axis fit 0.85/0.65/0.60",
    "strictScores": {"hair": 47, "eyes": 69, "face": 57, "skin": 57, "mouth": 53, "bodyAndClothing": 49, "overall": 56},
    "improvements": [
        "reduces the round doll-like stare with a shallower almond aperture",
        "keeps intact textured irises while clearing body overlap",
        "moves upper lashes and the conforming eye shell with the continuous lids",
    ],
    "remainingFailures": [
        "orbital fat and lid thickness remain simplified",
        "tear duct and eye wetness response remain graphic",
        "mouth commissures, perioral volume and skin microdetail remain below hero quality",
        "hair macro hierarchy remains too straight and planar",
    ],
    "websitePromotionApproved": False,
    "websiteAsset": "v83 unchanged",
}
VISUAL.write_text(json.dumps(review, indent=2), encoding="utf-8")
print("AEVRYND_R520_FINAL=" + json.dumps(review, sort_keys=True))
