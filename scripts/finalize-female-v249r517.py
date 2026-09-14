import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"


def read(name):
    return json.loads((ASSETS / name).read_text(encoding="utf-8"))


def write(name, value):
    (ASSETS / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


updates = {
    "female-v249-mainline-asymmetric-crown-flow-r511.study.json": (
        "REJECTED_KEEP_R510",
        "Only the 4mm bound passes collision and its visual change is negligible; the 7mm and 10mm bounds still look planar and fail dynamic body clearance."
    ),
    "female-v249-mainline-grouped-crown-lock-r512.study.json": (
        "REJECTED_KEEP_R510",
        "All reduced-card crown bounds pass collision but remain hidden beneath the dominant front layer, producing no meaningful full-groom change."
    ),
    "female-v249-mainline-front-layer-replacement-r514.study.json": (
        "REJECTED_REPAIRED_IN_R516",
        "Direct front replacement creates visible grouping, but all three initial bounds have 1.9-3.2mm shallow body penetration."
    ),
    "female-v249-mainline-front-density-reduction-r515.study.json": (
        "REJECTED_KEEP_R510",
        "Exact collision-safe subsets reveal stepped holes and horizontal cutouts around the temple and ear."
    ),
    "female-v249-mainline-front-clearance-repair-r516.study.json": (
        "SELECTED_C_FOR_R517",
        "The repaired 320-card bound passes all four frames and gives the best balance of coverage, side grouping and runtime reduction; 260 cards leave isolated long locks and 380 cards fail after repair."
    ),
}
for name, (status, reason) in updates.items():
    value = read(name)
    value["visualAssessment"] = {"status": status, "reason": reason}
    value["status"] = status
    write(name, value)

r513 = read("female-v249-mainline-runtime-hair-layer-isolation-r513.study.json")
r513["visualAttribution"] = {
    "dominantFrontAndSideLayer": "AevryndFemaleRuntimeCards_front_R467",
    "crownContribution": "narrow top strip largely occluded in the complete groom",
    "rearContribution": "back and lower rear coverage",
    "conclusion": "Visible curtain repair must replace the front layer; crown-only tuning cannot materially change the full groom."
}
r513["status"] = "DIAGNOSTIC_COMPLETE_FRONT_LAYER_IDENTIFIED"
write("female-v249-mainline-runtime-hair-layer-isolation-r513.study.json", r513)

review = {
    "candidate": "aevrynd-female-authoring-v249-mainline-layered-front-locks-r517.blend",
    "baseline": "aevrynd-female-authoring-v249-mainline-lighter-neutral-skin-r510.blend",
    "reviewSet": "reviews/v249r517-layered-front-locks-11shot/contact-sheet-11shot.jpg",
    "strictScores100": {
        "hair": 47,
        "eyes": 68,
        "faceGeometry": 56,
        "skinSurface": 57,
        "mouth": 53,
        "bodyAndClothing": 49,
        "overallCharacter": 55
    },
    "improvements": [
        "The dominant 420-card front curtain is replaced by 320 broader, length-staggered locks.",
        "Three-quarter and profile views gain more uneven side grouping and less uniform lower density.",
        "The selected repair converges to zero body and clothing penetration over frames 1/20/33/61.",
        "Left/right hair context becomes 3.59%/17.35% brighter while fixed skin regions stay within 0.35% of r510.",
        "Runtime export removes 9,200 rendered triangles and 505,988 bytes with unchanged draw calls."
    ],
    "remainingFailures": [
        "The front mass still reads too straight and sheet-like at macro distance.",
        "The central part remains broad and symmetric because the occluded crown and foundation topology are unchanged.",
        "Large/medium/fine lock hierarchy and controlled flyaways remain weak.",
        "Facial secondary anatomy, skin regional maps and garment construction remain below hero quality."
    ],
    "technicalGates": {
        "staticParityAndExpectedFrontReplacement": "PASS",
        "fourFrameBodyAndClothingCollision": "PASS",
        "dynamicMotionAndSettle": "PASS",
        "toneContract": "PASS",
        "elevenViewReview": "PASS_NO_NEW_ARTIFACT",
        "nodeRuntimeBenchmark": "PASS",
        "browserWebGLBenchmark": "PASS"
    },
    "status": "TECHNICAL_GATES_PASS_VISUAL_HERO_GATE_FAIL",
    "websitePromotionApproved": False
}
write("female-v249-mainline-layered-front-locks-r517.visual-review.json", review)

current = read("female-v249-mainline-current.json")
current["latestCharacterTechnicalCandidate"] = "aevrynd-female-authoring-v249-mainline-layered-front-locks-r517.blend"
current["latestCharacterCandidateStatus"] = "R517_OFFLINE_TECHNICAL_MAINLINE; the dominant front curtain is reduced from 420 to 320 broader staggered locks after r513 layer attribution. Static parity, four-frame body/clothing collision, tone, motion, 11-shot, Node.js and actual browser WebGL gates pass. Strict overall score is 55/100; website v83 remains unchanged."
current["latestHairTechnicalCandidate"] = "aevrynd-female-authoring-v249-mainline-layered-front-locks-r517.blend"
current["latestHairCandidateStatus"] = "r517 replaces only the visible front layer with 320 collision-repaired broader staggered locks. It removes 100 cards, 4,800 authoring vertices, 2,300 quads, 9,200 rendered triangles and 505,988 GLB bytes. Hair rises to 47/100 but still fails hero quality for straight planar mass, symmetric part and weak hierarchy."
current["latestHairDynamicTechnicalCandidate"] = "aevrynd-female-authoring-v249-mainline-layered-front-locks-r517.blend"
current["latestHairDynamicAudit"] = "female-v249-mainline-layered-front-locks-r517.runtime-card-audit.json"
current["latestHairDynamicStatus"] = "R517_PASS_ZERO_BODY_AND_CLOTHING_PENETRATION_FRAMES_1_20_33_61_MAX_LAYER_P95_2_666MM_MAX_4_631MM_ROOT_AND_SETTLE_STABLE"
current["latestHairResearch"] += "; r511-r512 rejected crown flow/grouping; r513 layer isolation; r514-r516 dominant-front replacement and clearance repair; r517 selected layered front locks"
current["latestHairResearchStatus"] = "r513 proves front_R467, not crown_R467, dominates the visible curtain. r514 establishes visible broad/staggered grouping but fails shallow collision; r516 repairs the selected 320-card bound across all dynamic frames. r517 passes every technical gate and reduces runtime cost, raising strict hair quality from 45 to 47/100. It remains a technical step below the hero gate."
current["latestSkinToneAudit"] = "female-v249-mainline-layered-front-locks-r517.tone-audit.json"
current["latestSkinToneStatus"] = "PASS_R510_LIGHTER_NEUTRAL_SKIN_RETAINED; r517 hair replacement changes forehead -0.029%, left/right cheeks -0.292%/-0.349%, chin -0.054%, all within 1%; left/right hair context becomes 3.592%/17.348% brighter."
current["latestRejectedExperiment"] += "; r511 invisible crown deformation/collision; r512 occluded crown card grouping; r514 shallow-collision front groups; r515 stepped-hole density subsets; r516 260-card isolated locks and unrepaired 380-card bound"
current["latestRejectedReason"] = "r513 layer isolation shows the front layer is the visible blocker. Crown-only r511-r512 changes are occluded; exact front reduction r515 creates temple holes. r516 c is retained because dynamic repair clears the useful 320-card grouped form without the 260-card isolated strips or 380-card residual collision."
write("female-v249-mainline-current.json", current)
print("AEVRYND_R517_FINALIZED")
