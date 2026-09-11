import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
TEMP = ROOT.parent / "Temp/female-realism"
REVIEW = ASSETS / "reviews/v249r340-integrated-caruncle"


def read(name):
    return json.loads((ASSETS / name).read_text(encoding="utf-8"))


def write(name, value):
    (ASSETS / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


r338_name = "female-v249-mainline-caruncle-shape-r338.study.json"
r338 = read(r338_name)
r338["status"] = "SELECT_B_MEDIAL_SMALL"
r338["selection"] = {"variant": "b-medial-small", "reason": "The 1.86mm width is the least enlarged option that reads beyond a single dot; all tested body and eye overlap counts are zero."}
write(r338_name, r338)

r339_name = "female-v249-mainline-caruncle-tissue-r339.study.json"
r339 = read(r339_name)
r339["status"] = "SELECT_B_MUTED_TISSUE"
r339["selection"] = {"variant": "b-muted-tissue", "reason": "Lower saturation removes the bright-red capsule response while retaining a distinct moist tissue layer."}
write(r339_name, r339)

r340_name = "female-v249-mainline-integrated-caruncle-r340.build-report.json"
r340 = read(r340_name)
r340.update({
    "status": "TECHNICAL_PASS_VISUAL_FAIL",
    "strictBenchmark": "current-generation hero character, normal gameplay and face-close views",
    "strictScores": {"face": 44, "hair": 34, "overallCharacter": 40},
    "technicalGains": [
        "Each owned caruncle is widened from 1.16mm to 1.86mm and shifted 0.35mm toward the nasal canthus.",
        "The material changes from saturated red without subsurface response to muted tissue with 0.025 subsurface weight.",
        "Body-eye, body-caruncle and eye-caruncle triangle overlaps are zero on both sides at frames 1 and 20.",
        "Face binding, full-body rig and 262,368-point hair-motion audits pass.",
    ],
    "visualGains": ["The caruncle reads as a restrained tissue feature rather than a bright isolated red dot."],
    "visualFailures": [
        "The caruncle is still an ellipsoid layer and lacks a true wedge-shaped junction with the eyelid skin.",
        "Inner and outer canthal folds, tear trough and orbital planes remain shallow.",
        "Eye aperture, skin response, facial asymmetry and hair silhouette remain below target.",
    ],
    "faceLayerAudit": str(ASSETS / "female-v249-mainline-integrated-caruncle-r340.face-layer-audit.json"),
    "bodyRigAudit": str(ASSETS / "female-v249-mainline-integrated-caruncle-r340.body-rig-audit.json"),
    "hairLayerAudit": str(ASSETS / "female-v249-mainline-integrated-caruncle-r340.hair-layer-audit.json"),
    "hairMotionAudit": str(ASSETS / "female-v249-mainline-integrated-caruncle-r340.hair-motion-audit.json"),
    "reviewDirectory": str(REVIEW),
    "websitePromotionApproved": False,
})
write(r340_name, r340)

study = {
    "range": "r338-r340",
    "sourceCandidate": "aevrynd-female-authoring-v249-mainline-natural-sclera-r337.blend",
    "resultCandidate": "aevrynd-female-authoring-v249-mainline-integrated-caruncle-r340.blend",
    "status": "TECHNICAL_PASS_VISUAL_FAIL",
    "findings": [
        "r338 corrects bone-parent matrix scaling and selects the smallest medial shape with visible anatomical presence.",
        "r339 proves the original high-saturation red material causes the capsule appearance and selects muted tissue response.",
        "r340 combines both selections and adds explicit caruncle collision pairs at static and animated frames.",
    ],
    "strictScores": {"face": 44, "hair": 34, "overallCharacter": 40},
    "websitePromotionApproved": False,
}
write("female-v249-mainline-r338-r340.study.json", study)

current_name = "female-v249-mainline-current.json"
current = read(current_name)
candidate = "aevrynd-female-authoring-v249-mainline-integrated-caruncle-r340.blend"
current.update({
    "latestEyeTechnicalCandidate": candidate,
    "latestEyeCandidateStatus": "r340 retains r337 natural sclera and turns the isolated red caruncle dot into a 1.86mm muted tissue layer shifted toward the nasal canthus. Body-eye, body-caruncle and eye-caruncle overlap are zero at frames 1/20.",
    "latestFaceTechnicalCandidate": candidate,
    "latestFaceCandidateStatus": "TECHNICAL_PASS_VISUAL_FAIL_SCORE_44; the inner-eye tissue reads more naturally, but the true canthal wedge, tear trough, orbital anatomy, aperture and skin remain below target.",
    "latestFaceResearch": "r248 legacy displacement rejection; r249-r258 CC0 foundation; r300-r337 eye geometry, collision and response studies; r338-r340 collision-safe caruncle integration",
    "latestFaceResearchStatus": "r340 is the current technical node with natural sclera, muted caruncle tissue, 16 head-bound face layers and zero audited eye-region overlap at frames 1/20. Strict visual gate remains failed.",
    "latestHairAuthoringCandidate": candidate,
    "latestHairAuthoringAudit": "female-v249-mainline-integrated-caruncle-r340.hair-motion-audit.json",
    "latestHairAuthoringLayerAudit": "female-v249-mainline-integrated-caruncle-r340.hair-layer-audit.json",
})
work = current.get("nextRequiredWork", [])
if work:
    work[0] = "以 r340 為基底，將橢球淚阜進一步改造成與上下眼瞼銜接的楔形拓撲，雕刻鼻側內眼角折線、外眼角收束、淚溝與眶周平面；重跑所有眼區碰撞對。"
write(current_name, current)

REVIEW.mkdir(parents=True, exist_ok=True)
copies = {
    TEMP / "v249r338-caruncle-shape-sweep/a-r337-baseline-eyes.png": "r338-baseline-red-dot.png",
    TEMP / "v249r338-caruncle-shape-sweep/b-medial-small-eyes.png": "r338-selected-medial-small.png",
    TEMP / "v249r338-caruncle-shape-sweep/d-medial-large-eyes.png": "r338-rejected-oversized.png",
    TEMP / "v249r339-caruncle-tissue-sweep/a-r337-red-eyes.png": "r339-rejected-saturated-red.png",
    TEMP / "v249r339-caruncle-tissue-sweep/b-muted-tissue-eyes.png": "r339-selected-muted-tissue.png",
}
for name in ("front-f01", "front-f20", "face-close-f01", "eyes-close-f01", "three-quarter-f01", "left-f01", "right-f01", "back-f01"):
    copies[TEMP / "v249r340-integrated-caruncle" / f"{name}.png"] = f"r340-{name}.png"
for source, target in copies.items():
    if not source.exists():
        raise FileNotFoundError(source)
    shutil.copy2(source, REVIEW / target)

print(json.dumps({"status": "PACKAGED", "review": str(REVIEW), "files": len(copies)}, ensure_ascii=False))
