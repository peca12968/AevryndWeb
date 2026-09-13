import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
TEMP = ROOT.parent / "Temp/female-realism"
REVIEW = ASSETS / "reviews/v249r420-layered-optical-stack"


def read(name):
    return json.loads((ASSETS / name).read_text(encoding="utf-8"))


def write(name, value):
    (ASSETS / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


r419_name = "female-v249-mainline-curved-optical-stack-r419.study.json"
r419 = read(r419_name)
r419.update({
    "status": "SELECT_B_BALANCED_FOR_R420",
    "visualReview": {
        "selectedVariant": "b-balanced",
        "finding": "All three convex-cornea samples remove the flat integrated-eye response. The 0.55 mm local bulge preserves a readable corneal volume without the stronger profile projection of variant c.",
        "decision": "BUILD_R420_WITH_SEPARATE_SCLERA_LIMBUS_IRIS_PUPIL_CORNEA",
    },
})
write(r419_name, r419)

r420_name = "female-v249-mainline-layered-optical-stack-r420.build-report.json"
r420 = read(r420_name)
r420.update({
    "status": "TECHNICAL_PASS_VISUAL_FAIL",
    "strictBenchmark": "current-generation hero character at normal gameplay distance and face-close framing",
    "strictScores": {"face": 51, "hair": 34, "overallCharacter": 44},
    "technicalGains": [
        "Each eye now has five explicit head-bound mesh layers: open sclera, limbal annulus, concave iris, recessed pupil and convex cornea.",
        "The owned 512 px Aevrynd iris texture replaces the single-surface procedural radial graphic.",
        "The selected optical group uses a 0.55 mm local corneal bulge and 1.00 mm local recess behind the eyelid envelope.",
        "Frames 1 and 20 have zero body/optical, caruncle/cornea and optical-layer triangle overlaps.",
        "All ten new eye layers follow the head bone by about 48 mm between review frames and remain enabled for rendering.",
    ],
    "visualGains": [
        "The iris has visible stromal depth and a separate pupil instead of reading as a flat colored circle.",
        "The sclera returns to a readable warm white and no longer darkens the full eye socket.",
        "Front and three-quarter views preserve the r418 medial-aperture proportion while improving eye depth.",
    ],
    "visualFailures": [
        "Upper and lower eyelids still lack a thick anatomical rim, and the upper crease remains an inflated smooth arc.",
        "The existing cinematic rig creates strong repeated area-light reflections; corneal roughness and light shapes need a dedicated response study.",
        "The iris texture is still too regular at extreme close range and needs higher-resolution asymmetric crypts and collarette breakup.",
        "Nasal alar planes, philtrum, vermilion volume, cheek asymmetry and regional skin maps remain below the hero gate.",
        "The inherited offline groom remains far below the hair target and is not the r409 runtime hair prototype.",
    ],
    "faceLayerAudit": str(ASSETS / "female-v249-mainline-layered-optical-stack-r420.face-layer-audit.json"),
    "collisionAudit": str(ASSETS / "female-v249-mainline-layered-optical-stack-r420.collision-audit.json"),
    "perceptualContrastAudit": str(ASSETS / "female-v249-mainline-r420.perceptual-contrast-audit.json"),
    "reviewDirectory": str(REVIEW),
    "websitePromotionApproved": False,
})
write(r420_name, r420)

write("female-v249-mainline-r419-r420-optical-study.json", {
    "range": "r419-r420",
    "sourceCandidate": "aevrynd-female-authoring-v249-mainline-broad-medial-aperture-r418.blend",
    "resultCandidate": "aevrynd-female-authoring-v249-mainline-layered-optical-stack-r420.blend",
    "status": "TECHNICAL_PASS_VISUAL_FAIL_SCORE_51",
    "findings": [
        "r419 proves that separate curved optical surfaces improve depth more than another integrated shader change.",
        "The first r420 build collided at the cornea and reconstructed sclera and was rejected.",
        "The corrected build preserves the collision-safe r418 sclera envelope, opens only its visible limbus, and recesses the four anterior optical layers by 1.00 mm local.",
        "All audited triangle-overlap counts are zero at frames 1 and 20.",
        "Neutral review confirms that perceived progressive darkening comes from scene contrast and the old dark sclera range rather than a cumulative skin-material change.",
    ],
    "strictScores": {"face": 51, "hair": 34, "overallCharacter": 44},
    "websitePromotionApproved": False,
})

current_name = "female-v249-mainline-current.json"
current = read(current_name)
candidate = "aevrynd-female-authoring-v249-mainline-layered-optical-stack-r420.blend"
current.update({
    "latestEyeTechnicalCandidate": candidate,
    "latestEyeCandidateStatus": "r420 replaces the integrated eye shader with ten explicit head-bound optical meshes. Frames 1/20 have zero body, caruncle and inter-layer overlaps; strict face score rises to 51/100.",
    "latestFaceTechnicalCandidate": candidate,
    "latestFaceCandidateStatus": "TECHNICAL_PASS_VISUAL_FAIL_SCORE_51; eye depth and sclera readability improve, while eyelid volume, corneal highlight control, high-resolution iris breakup and the remaining facial landmarks stay below target.",
    "latestFaceResearch": "r248 legacy displacement rejection; r249-r258 CC0 foundation; r300-r345 eye geometry and caruncle integration; r410-r420 orbital, lighting, aperture and layered-optics studies",
    "latestFaceResearchStatus": "r420 is the current technical face node. Its ten new eye meshes have explicit layers, valid head binding and zero audited overlap. Strict visual score is 51/100 and the website gate remains closed.",
    "latestFaceLightingStatus": "NO_PROGRESSIVE_SKIN_DARKENING_CONFIRMED; neutral white-light review isolates the perceived darkening to black-background, dark-hair and old sclera contrast. r420 raises sclera readability without changing the inherited skin material.",
    "latestFaceRejectedExperiment": "r410 wrong socket surface; r411-r413 insufficient visual gain; r414 graphic integrated iris; r416 narrow-transition canthus seam; initial r420 unrecessed cornea/sclera collision",
    "latestFaceRejectedReason": "The initial layered-optics build improved depth but failed collision. The corrected r420 retains the r418 sclera envelope and recesses the anterior optical group until all frame 1/20 checks reach zero.",
})
work = current.get("nextRequiredWork", [])
if work:
    work[0] = "以 r420 為基底重建有厚度的上下眼瞼邊緣、上眼瞼覆蓋與不對稱眶周平面；針對角膜粗糙度與燈形重跑中性／電影燈光審查，再提高虹膜非對稱細節，並保持第 1／20 幀零穿模。"
write(current_name, current)

REVIEW.mkdir(parents=True, exist_ok=True)
copies = {
    ASSETS / "reviews/v249r418-broad-medial-aperture/r418-eyes-close-f01.png": "r418-integrated-eye-baseline.png",
    TEMP / "v249r419-curved-optical-stack-sweep/a-low-eyes.png": "r419-a-low-eyes.png",
    TEMP / "v249r419-curved-optical-stack-sweep/b-balanced-eyes.png": "r419-b-selected-eyes.png",
    TEMP / "v249r419-curved-optical-stack-sweep/c-deep-eyes.png": "r419-c-deep-eyes.png",
    TEMP / "v249r419-curved-optical-stack-sweep/r420-selected-face.png": "r420-neutral-face.png",
    TEMP / "v249r419-curved-optical-stack-sweep/r420-selected-eyes.png": "r420-neutral-eyes.png",
    TEMP / "v249r419-curved-optical-stack-sweep/r420-selected-three-quarter.png": "r420-neutral-three-quarter.png",
}
for name in ("front-f01", "front-f20", "face-close-f01", "eyes-close-f01", "three-quarter-f01"):
    copies[TEMP / "v249r420-layered-optical-stack" / f"{name}.png"] = f"r420-cinematic-{name}.png"
for source, target in copies.items():
    if not source.exists():
        raise FileNotFoundError(source)
    shutil.copy2(source, REVIEW / target)

print(json.dumps({"status": "PACKAGED", "review": str(REVIEW), "files": len(copies)}, ensure_ascii=False))
