import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
TEMP = ROOT.parent / "Temp/female-realism"
REVIEW = ASSETS / "reviews/v249r337-natural-sclera"


def read(name):
    return json.loads((ASSETS / name).read_text(encoding="utf-8"))


def write(name, value):
    (ASSETS / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


r335_name = "female-v249-mainline-sclera-response-r335.study.json"
r335 = read(r335_name)
r335["status"] = "REJECT_INSUFFICIENT_RESPONSE_RANGE"
r335["finding"] = "A 20-30% ramp reduction changes the render too little and leaves 36.11-38.45% near-clipped bright-band samples."
write(r335_name, r335)

r336_name = "female-v249-mainline-deep-sclera-response-r336.study.json"
r336 = read(r336_name)
r336["status"] = "SELECT_B_DEEP_WARM"
r336["selection"] = {
    "variant": "b-deep-warm",
    "reason": "It reduces near-clipped bright-band samples from 40.69% to 10.80% while retaining a wet corneal highlight and avoiding the gray cast of c-deep-muted.",
}
write(r336_name, r336)

r337_name = "female-v249-mainline-natural-sclera-r337.build-report.json"
r337 = read(r337_name)
r337.update({
    "status": "TECHNICAL_PASS_VISUAL_FAIL",
    "strictBenchmark": "current-generation hero character, normal gameplay and face-close views",
    "strictScores": {"face": 43, "hair": 34, "overallCharacter": 39},
    "technicalGains": [
        "Only the owned procedural eye material changes; body, eye and hair geometry remain identical to collision-safe r334.",
        "Near-clipped samples in the fixed bright eye band fall from 40.69% to 10.80% at 0 EV.",
        "Body-eye overlap remains zero at frames 1 and 20; face binding, body rig and hair motion audits pass.",
    ],
    "visualGains": [
        "The sclera reads as warm living tissue instead of a flat white cutout.",
        "Lower eye-to-skin contrast reduces the false impression that the skin was progressively darkened.",
    ],
    "visualFailures": [
        "The eye aperture remains too wide and the neutral gaze remains mannequin-like.",
        "Caruncles still read as small red dots instead of integrated tissue wedges.",
        "Tear trough, canthal transitions, orbital planes and natural asymmetry remain underdeveloped.",
        "Skin and hair remain below the hero-character gate.",
    ],
    "faceLayerAudit": str(ASSETS / "female-v249-mainline-natural-sclera-r337.face-layer-audit.json"),
    "bodyRigAudit": str(ASSETS / "female-v249-mainline-natural-sclera-r337.body-rig-audit.json"),
    "hairLayerAudit": str(ASSETS / "female-v249-mainline-natural-sclera-r337.hair-layer-audit.json"),
    "hairMotionAudit": str(ASSETS / "female-v249-mainline-natural-sclera-r337.hair-motion-audit.json"),
    "reviewDirectory": str(REVIEW),
    "websitePromotionApproved": False,
})
write(r337_name, r337)

study = {
    "range": "r335-r337",
    "sourceCandidate": "aevrynd-female-authoring-v249-mainline-continuous-upper-lower-eyelids-r334.blend",
    "resultCandidate": "aevrynd-female-authoring-v249-mainline-natural-sclera-r337.blend",
    "status": "TECHNICAL_PASS_VISUAL_FAIL",
    "findings": [
        "r335 proves modest sclera color changes do not sufficiently control highlight clipping.",
        "r336 expands the search and selects the deep-warm response over the overly gray muted alternative.",
        "r337 freezes the selected response at 0 EV and passes collision, binding, rig and hair-motion audits.",
    ],
    "strictScores": {"face": 43, "hair": 34, "overallCharacter": 39},
    "websitePromotionApproved": False,
}
write("female-v249-mainline-r335-r337.study.json", study)

current_name = "female-v249-mainline-current.json"
current = read(current_name)
candidate = "aevrynd-female-authoring-v249-mainline-natural-sclera-r337.blend"
current.update({
    "latestEyeTechnicalCandidate": candidate,
    "latestEyeCandidateStatus": "r337 retains r334 collision-safe continuous lids and replaces the clipped white sclera response with the selected warm tissue response. Fixed bright-band near clipping falls from 40.69% to 10.80%; body-eye overlap stays zero at frames 1/20.",
    "latestFaceTechnicalCandidate": candidate,
    "latestFaceCandidateStatus": "TECHNICAL_PASS_VISUAL_FAIL_SCORE_43; eye-to-skin contrast is more natural, while aperture, canthi, caruncles, orbital anatomy, skin response and asymmetry remain below target.",
    "latestFaceResearch": "r248 legacy displacement rejection; r249-r258 CC0 foundation; r300-r334 eye geometry and collision studies; r335-r337 fixed-exposure sclera response calibration",
    "latestFaceResearchStatus": "r337 is the current technical node with naturalized sclera response, 16 head-bound face layers, zero body-eye overlap at frames 1/20 and a fully weighted 169,362-vertex body. Strict visual gate remains failed.",
    "latestHairAuthoringCandidate": candidate,
    "latestHairAuthoringAudit": "female-v249-mainline-natural-sclera-r337.hair-motion-audit.json",
    "latestHairAuthoringLayerAudit": "female-v249-mainline-natural-sclera-r337.hair-layer-audit.json",
})
work = current.get("nextRequiredWork", [])
if work:
    work[0] = "以 r337 為基底，把目前點狀淚阜重建為與內眼角銜接的楔形組織，補足內外眼角、淚溝與眶周平面並加入自然左右差異；重跑 frame 1/20 眼球與附屬層穿模。"
write(current_name, current)

REVIEW.mkdir(parents=True, exist_ok=True)
copies = {
    TEMP / "v249r335-sclera-response-sweep/a-r334-baseline-eyes.png": "r335-baseline-overbright.png",
    TEMP / "v249r335-sclera-response-sweep/c-muted-natural-eyes.png": "r335-rejected-insufficient-range.png",
    TEMP / "v249r336-deep-sclera-response-sweep/b-deep-warm-eyes.png": "r336-selected-deep-warm.png",
    TEMP / "v249r336-deep-sclera-response-sweep/c-deep-muted-eyes.png": "r336-rejected-gray.png",
}
for name in ("front-f01", "front-f20", "face-close-f01", "eyes-close-f01", "three-quarter-f01", "left-f01", "right-f01", "back-f01"):
    copies[TEMP / "v249r337-natural-sclera" / f"{name}.png"] = f"r337-{name}.png"
for source, target in copies.items():
    if not source.exists():
        raise FileNotFoundError(source)
    shutil.copy2(source, REVIEW / target)

print(json.dumps({"status": "PACKAGED", "review": str(REVIEW), "files": len(copies)}, ensure_ascii=False))
