import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"; TEMP = ROOT.parent / "Temp/female-realism"
REVIEW = ASSETS / "reviews/v249r345-canthus-fitted-wedge"

def read(name): return json.loads((ASSETS / name).read_text(encoding="utf-8"))
def write(name, value): (ASSETS / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

updates = {
    "female-v249-mainline-caruncle-wedge-r341.study.json": ("SELECT_B_SOFT_WEDGE", "b-soft-wedge makes a restrained nasal-base/globe-tip asymmetry with zero body and eye overlap."),
    "female-v249-mainline-caruncle-medial-fit-r342.study.json": ("INSUFFICIENT_POSITION_RANGE", "The first 0.75mm extension remains visibly lateral; all samples are collision-free."),
    "female-v249-mainline-caruncle-medial-limit-r343.study.json": ("INSUFFICIENT_POSITION_RANGE", "Even 1.75mm additional shift remains short of the canthal fold; all samples are collision-free."),
    "female-v249-mainline-caruncle-medial-contact-r344.study.json": ("SELECT_C_PLUS_2P50MM", "2.50mm additional shift reaches the visual canthal fold; 2.75mm overshoots onto the nasal skin."),
}
for name, (status, finding) in updates.items():
    data = read(name); data["status"] = status; data["finding"] = finding; write(name, data)

r345_name = "female-v249-mainline-canthus-fitted-wedge-r345.build-report.json"; r345 = read(r345_name)
r345.update({
    "status": "TECHNICAL_PASS_VISUAL_FAIL", "strictBenchmark": "current-generation hero character, normal gameplay and face-close views",
    "strictScores": {"face": 45, "hair": 34, "overallCharacter": 41},
    "technicalGains": [
        "Both 482-vertex owned caruncles now use a true asymmetric cross-section with a broad nasal base and a tapered globe-facing tip.",
        "The selected placement moves each layer 2.50mm farther toward the nasal canthus than r340, 2.85mm total from r337.",
        "Body-eye, body-caruncle and eye-caruncle overlap are zero on both sides at frames 1 and 20.",
        "Face binding, body rig and 262,368-point hair motion audits pass.",
    ],
    "visualGains": ["The muted tissue layer now sits at the inner-canthus fold and no longer reads as a lateral sclera dot."],
    "visualFailures": [
        "The surrounding skin still lacks a sculpted upper/lower canthal junction, so the separate layer remains detectable at extreme close range.",
        "The aperture remains too wide and orbital volume, tear trough, asymmetry, skin and hair remain below target.",
    ],
    "faceLayerAudit": str(ASSETS / "female-v249-mainline-canthus-fitted-wedge-r345.face-layer-audit.json"),
    "bodyRigAudit": str(ASSETS / "female-v249-mainline-canthus-fitted-wedge-r345.body-rig-audit.json"),
    "hairLayerAudit": str(ASSETS / "female-v249-mainline-canthus-fitted-wedge-r345.hair-layer-audit.json"),
    "hairMotionAudit": str(ASSETS / "female-v249-mainline-canthus-fitted-wedge-r345.hair-motion-audit.json"),
    "reviewDirectory": str(REVIEW), "websitePromotionApproved": False,
}); write(r345_name, r345)

write("female-v249-mainline-r341-r345.study.json", {
    "range": "r341-r345", "sourceCandidate": "aevrynd-female-authoring-v249-mainline-integrated-caruncle-r340.blend",
    "resultCandidate": "aevrynd-female-authoring-v249-mainline-canthus-fitted-wedge-r345.blend", "status": "TECHNICAL_PASS_VISUAL_FAIL",
    "findings": ["r341 selects a soft wedge topology.", "r342-r343 prove the original caruncle layer is substantially lateral to the true canthus.", "r344 selects 2.50mm additional medial shift before the 2.75mm visual overshoot.", "r345 freezes the wedge and placement and passes all collision, binding, rig and hair audits."],
    "strictScores": {"face": 45, "hair": 34, "overallCharacter": 41}, "websitePromotionApproved": False,
})

current_name = "female-v249-mainline-current.json"; current = read(current_name)
candidate = "aevrynd-female-authoring-v249-mainline-canthus-fitted-wedge-r345.blend"
current.update({
    "latestEyeTechnicalCandidate": candidate,
    "latestEyeCandidateStatus": "r345 deforms each owned caruncle into a nasal-base/globe-tip wedge and fits it to the inner canthus. All body-eye, body-caruncle and eye-caruncle overlap counts remain zero at frames 1/20.",
    "latestFaceTechnicalCandidate": candidate,
    "latestFaceCandidateStatus": "TECHNICAL_PASS_VISUAL_FAIL_SCORE_45; the caruncle is no longer a lateral red dot, while surrounding canthal skin, orbital anatomy, aperture and surface detail remain below target.",
    "latestFaceResearch": "r248 legacy displacement rejection; r249-r258 CC0 foundation; r300-r340 eye geometry, response and caruncle integration; r341-r345 wedge topology and canthal fitting",
    "latestFaceResearchStatus": "r345 is the current technical node with canthus-fitted wedge tissue, natural sclera, 16 head-bound face layers and zero audited eye-region overlap at frames 1/20. Strict visual gate remains failed.",
    "latestHairAuthoringCandidate": candidate, "latestHairAuthoringAudit": "female-v249-mainline-canthus-fitted-wedge-r345.hair-motion-audit.json",
    "latestHairAuthoringLayerAudit": "female-v249-mainline-canthus-fitted-wedge-r345.hair-layer-audit.json",
})
work = current.get("nextRequiredWork", [])
if work: work[0] = "以 r345 為基底雕刻上下眼瞼在內眼角的連續皮膚折線、外眼角收束、淚溝與眶周平面，並降低整體眼裂水平寬度；重跑眼球、淚阜、眼瞼附屬層與動作幀碰撞。"
write(current_name, current)

REVIEW.mkdir(parents=True, exist_ok=True)
copies = {
    TEMP / "v249r341-caruncle-wedge-sweep/a-r340-ellipsoid-eyes.png": "r341-baseline-ellipsoid.png",
    TEMP / "v249r341-caruncle-wedge-sweep/b-soft-wedge-eyes.png": "r341-selected-soft-wedge.png",
    TEMP / "v249r343-caruncle-medial-limit-sweep/d-plus-1p75mm-eyes.png": "r343-still-lateral.png",
    TEMP / "v249r344-caruncle-medial-contact-sweep/c-plus-2p50mm-eyes.png": "r344-selected-canthus-fit.png",
    TEMP / "v249r344-caruncle-medial-contact-sweep/d-plus-2p75mm-eyes.png": "r344-rejected-medial-overshoot.png",
}
for name in ("front-f01", "front-f20", "face-close-f01", "eyes-close-f01", "three-quarter-f01", "left-f01", "right-f01", "back-f01"):
    copies[TEMP / "v249r345-canthus-fitted-wedge" / f"{name}.png"] = f"r345-{name}.png"
for source, target in copies.items():
    if not source.exists(): raise FileNotFoundError(source)
    shutil.copy2(source, REVIEW / target)
print(json.dumps({"status": "PACKAGED", "review": str(REVIEW), "files": len(copies)}, ensure_ascii=False))
