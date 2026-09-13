import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
TEMP = ROOT.parent / "Temp/female-realism"
REVIEW = ASSETS / "reviews/v249r418-broad-medial-aperture"


def read(name):
    return json.loads((ASSETS / name).read_text(encoding="utf-8"))


def write(name, value):
    (ASSETS / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


r415_name = "female-v249-mainline-neutral-diagnostic-r415.study.json"
r415 = read(r415_name)
r415.update({
    "status": "ACCEPTED_DIAGNOSTIC_RIG",
    "finding": "Neutral white area lights, AgX Base Contrast, and hidden large-hair layers expose facial form without the warm/cool split-light bias. The baseline confirms excessive intercanthal spacing, weak lid volume, flat orbital planes, and shallow mouth/nasal landmarks.",
    "modelPromotionApproved": False,
})
write(r415_name, r415)

r416_name = "female-v249-mainline-medial-aperture-r416.study.json"
r416 = read(r416_name)
r416.update({
    "status": "REJECT_ALL_NARROW_TRANSITION_SEAM",
    "visualReview": {
        "finding": "All three variants reduce the excessive intercanthal gap, but the narrow medial deformation boundary creates a vertical artificial crease beside each inner canthus.",
        "decision": "REJECT_ALL",
    },
})
write(r416_name, r416)

r417_name = "female-v249-mainline-broad-medial-transition-r417.study.json"
r417 = read(r417_name)
r417.update({
    "status": "SELECT_B_AS_R418_TECHNICAL_CANDIDATE",
    "visualReview": {
        "selectedVariant": "b-broad-2p7mm",
        "finding": "The broad nasal-bridge transition removes the r416 crease. Variant b improves eye-width-to-intercanthal-gap balance without the stronger inward pull of variant c; all audited eye/body and caruncle/body overlaps remain zero.",
        "decision": "BUILD_R418_FROM_B",
    },
})
write(r417_name, r417)

r418_name = "female-v249-mainline-broad-medial-aperture-r418.build-report.json"
r418 = read(r418_name)
r418.update({
    "status": "TECHNICAL_PASS_VISUAL_FAIL",
    "strictBenchmark": "current-generation hero character at normal gameplay distance and face-close framing",
    "strictScores": {"face": 47, "hair": 34, "overallCharacter": 42},
    "technicalGains": [
        "The outer canthus remains fixed while the visible aperture extends 2.665mm toward the nose.",
        "Each complete eye stack shifts 1.333mm toward the facial midline and 0.800mm deeper.",
        "The body deformation blends across the medial orbital wall and nasal bridge instead of leaving the r416 vertical seam.",
        "Body-eye, body-caruncle and eye-caruncle triangle overlaps are zero on both sides at frames 1 and 20.",
        "All 16 face layers retain valid head-bone binding; the 169,362-vertex body rig and inherited dynamic groom audits pass.",
    ],
    "visualGains": [
        "Eye width and intercanthal spacing read closer to adult facial proportions in front and three-quarter views.",
        "The widened medial aperture removes some of the small, widely separated doll-eye appearance without creating cross-eyed gaze.",
    ],
    "visualFailures": [
        "Upper and lower lids remain shallow and the upper crease still reads as a smooth inflated arc.",
        "The iris shader and catchlights remain graphic, and the eye lacks a separately modeled corneal bulge and iris depth.",
        "Nasal alar planes, philtrum, vermilion volume, cheek asymmetry and regional skin detail remain below the hero-character gate.",
        "The inherited offline groom remains far below the hair target and is not the r409 runtime hair prototype.",
    ],
    "faceLayerAudit": str(ASSETS / "female-v249-mainline-broad-medial-aperture-r418.face-layer-audit.json"),
    "bodyRigAudit": str(ASSETS / "female-v249-mainline-broad-medial-aperture-r418.body-rig-audit.json"),
    "hairLayerAudit": str(ASSETS / "female-v249-mainline-broad-medial-aperture-r418.hair-layer-audit.json"),
    "hairMotionAudit": str(ASSETS / "female-v249-mainline-broad-medial-aperture-r418.hair-motion-audit.json"),
    "reviewDirectory": str(REVIEW),
    "websitePromotionApproved": False,
})
write(r418_name, r418)

write("female-v249-mainline-r410-r418-face-study.json", {
    "range": "r410-r418",
    "sourceCandidate": "aevrynd-female-authoring-v249-mainline-canthus-fitted-wedge-r345.blend",
    "resultCandidate": "aevrynd-female-authoring-v249-mainline-broad-medial-aperture-r418.blend",
    "status": "TECHNICAL_PASS_VISUAL_FAIL_SCORE_47",
    "findings": [
        "r410 selected the wrong socket surface and is rejected.",
        "r411 reaches the visible orbital surface but is too subtle for standalone promotion.",
        "r412 identifies a collision-safe canthus recess limit; the strongest sample collides on the right eye.",
        "r413 combines safe orbital edits but remains nearly indistinguishable from r345.",
        "r414 softens the procedural iris but remains graphic and is rejected.",
        "r415 establishes a neutral diagnostic rig and confirms that face structure, rather than progressive darkening, is the dominant issue.",
        "r416 improves spacing but creates a narrow-transition seam and is rejected.",
        "r417 broadens the medial transition and selects its middle variant.",
        "r418 freezes the selected proportional edit and passes collision, binding, rig and inherited groom audits.",
    ],
    "strictScores": {"face": 47, "hair": 34, "overallCharacter": 42},
    "websitePromotionApproved": False,
})

current_name = "female-v249-mainline-current.json"
current = read(current_name)
candidate = "aevrynd-female-authoring-v249-mainline-broad-medial-aperture-r418.blend"
current.update({
    "latestEyeTechnicalCandidate": candidate,
    "latestEyeCandidateStatus": "r418 keeps the outer canthus fixed, extends the medial aperture 2.665mm, shifts each complete eye stack 1.333mm medially and 0.800mm deeper, and preserves zero body-eye, body-caruncle and eye-caruncle overlap at frames 1/20.",
    "latestFaceTechnicalCandidate": candidate,
    "latestFaceCandidateStatus": "TECHNICAL_PASS_VISUAL_FAIL_SCORE_47; adult eye-spacing balance improves without the r416 medial crease, while eyelid volume, eye optics, mouth/nasal landmarks, asymmetry and regional skin detail remain below target.",
    "latestFaceResearch": "r248 legacy displacement rejection; r249-r258 CC0 foundation; r300-r345 eye geometry and caruncle integration; r410-r418 orbital, lighting and medial-aperture studies",
    "latestFaceResearchStatus": "r418 is the current technical face node with a broad medial orbital transition, 16 head-bound face layers, complete eye-stack refit, valid body rig and zero audited eye-region overlap. Strict visual score is 47/100 and the website gate remains closed.",
    "latestFaceDiagnostic": "female-v249-mainline-neutral-diagnostic-r415.study.json",
    "latestFaceDiagnosticStatus": "ACCEPTED_NEUTRAL_WHITE_THREE_AREA_LIGHT_RIG_AGX_BASE_CONTRAST",
    "latestFaceRejectedExperiment": "r410 wrong socket surface; r411-r413 insufficient visual gain; r414 graphic iris response; r416 narrow-transition canthus seam",
    "latestFaceRejectedReason": "None of r410-r416 produced a collision-safe, seam-free and clearly improved facial result. r417 corrected the deformation field and supplied the r418 technical candidate.",
})
work = current.get("nextRequiredWork", [])
if work:
    work[0] = "以 r418 為基底重建有厚度的上下眼瞼、上眼瞼覆蓋與不對稱眶周平面；將鞏膜、虹膜／瞳孔與角膜凸面改成可獨立驗證的光學層，重跑第 1／20 幀碰撞與中性／電影燈光審查。"
write(current_name, current)

REVIEW.mkdir(parents=True, exist_ok=True)
copies = {
    TEMP / "v249r415-neutral-diagnostic/r345-material-face-front.png": "r345-neutral-baseline-face.png",
    TEMP / "v249r415-neutral-diagnostic/r345-material-face-three-quarter.png": "r345-neutral-baseline-three-quarter.png",
    TEMP / "v249r416-medial-aperture-sweep/b-medial-3p3mm-face.png": "r416-rejected-narrow-transition-seam.png",
    TEMP / "v249r417-broad-medial-transition-sweep/a-broad-2p1mm-face.png": "r417-a-broad-2p1mm.png",
    TEMP / "v249r417-broad-medial-transition-sweep/b-broad-2p7mm-face.png": "r417-b-selected-broad-2p7mm.png",
    TEMP / "v249r417-broad-medial-transition-sweep/c-broad-3p3mm-face.png": "r417-c-broad-3p3mm.png",
}
for name in ("front-f01", "front-f20", "face-close-f01", "eyes-close-f01", "three-quarter-f01", "left-f01", "right-f01", "back-f01"):
    copies[TEMP / "v249r418-broad-medial-aperture" / f"{name}.png"] = f"r418-{name}.png"
for source, target in copies.items():
    if not source.exists():
        raise FileNotFoundError(source)
    shutil.copy2(source, REVIEW / target)

print(json.dumps({"status": "PACKAGED", "review": str(REVIEW), "files": len(copies)}, ensure_ascii=False))
