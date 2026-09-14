import json
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
MODEL = ASSETS / "aevrynd-female-authoring-v249-mainline-natural-commissures-r522.blend"
BUILD = ASSETS / "female-v249-mainline-natural-commissures-r522.build-report.json"
VISUAL = ASSETS / "female-v249-mainline-natural-commissures-r522.visual-review.json"

bpy.ops.wm.open_mainfile(filepath=str(MODEL))
scene = bpy.context.scene
scene["aevrynd_release_state"] = "OFFLINE_TECHNICAL_MAINLINE_ALL_GATES_PASS_VISUAL_HERO_FAIL"
scene["aevrynd_strict_hair_score"] = 47
scene["aevrynd_strict_eye_score"] = 69
scene["aevrynd_strict_face_score"] = 58
scene["aevrynd_strict_mouth_score"] = 55
scene["aevrynd_strict_overall_score"] = 57
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(MODEL))

build = json.loads(BUILD.read_text(encoding="utf-8"))
build["status"] = "PASS_OFFLINE_TECHNICAL_MAINLINE_VISUAL_HERO_FAIL"
build["selectionNote"] = "r521 visual bound 1.75 was reduced to 1.60 because its fixed chin crop exceeded the 1 percent tone gate; 1.60 passes at +0.973 percent"
build["audits"] = {
    "faceAndSelfIntersection": "female-v249-mainline-natural-commissures-r522.audit.json",
    "runtimeHair": "female-v249-mainline-natural-commissures-r522.runtime-card-audit.json",
    "tone": "female-v249-mainline-natural-commissures-r522.tone-contract-audit.json",
    "performance": "female-v249-mainline-natural-commissures-r522.performance-audit.json",
    "mouthAB": "reviews/v249r522-natural-commissures-mouth/contact-sheet-mouth-ab.jpg",
    "views": "reviews/v249r522-natural-commissures-11shot/contact-sheet-11shot.jpg",
}
BUILD.write_text(json.dumps(build, indent=2), encoding="utf-8")

review = {
    "revision": "v249r522",
    "status": "OFFLINE_TECHNICAL_MAINLINE_VISUAL_HERO_FAIL",
    "strictScores": {"hair": 47, "eyes": 69, "face": 58, "skin": 57, "mouth": 55, "bodyAndClothing": 49, "overall": 57},
    "improvements": [
        "replaces needle-like lip termination with a shallow commissure dimple",
        "adds restrained paired upper-lip and central lower-lip volume",
        "preserves neutral expression and all six shape-key states",
    ],
    "remainingFailures": [
        "upper-lip border and philtrum transition remain broad",
        "fine lip creases and localized moisture breakup remain weak",
        "orbital volume, skin microdetail and hair macro hierarchy remain below hero quality",
    ],
    "websitePromotionApproved": False,
    "websiteAsset": "v83 unchanged",
}
VISUAL.write_text(json.dumps(review, indent=2), encoding="utf-8")
print("AEVRYND_R522_FINAL=" + json.dumps(review, sort_keys=True))
