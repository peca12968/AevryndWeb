import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"


def read(name):
    return json.loads((ASSETS / name).read_text(encoding="utf-8"))


def write(name, value):
    (ASSETS / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


r507 = read("female-v249-mainline-crown-layer-replacement-r507.study.json")
r507["visualAssessment"] = {
    "selected": None,
    "status": "REJECTED_COLLISION_AND_VISUAL_GAIN",
    "reason": "All shortened/curved crown replacements remain visually close to the planar source and introduce 17.0-19.9 mm worst signed body penetration across the dynamic audit.",
}
r507["status"] = "REJECTED_KEEP_R506"
write("female-v249-mainline-crown-layer-replacement-r507.study.json", r507)

r508 = read("female-v249-mainline-crown-root-width-r508.study.json")
r508["visualAssessment"] = {
    "selected": None,
    "status": "REJECTED_VISUALLY_NEGLIGIBLE",
    "reason": "Identity, 1.15x and 1.30x center-root widths all pass frames 1/20/33/61, but matched front, three-quarter, profile, top and motion views show no meaningful reduction in the straight part or planar side flow.",
}
r508["status"] = "REJECTED_KEEP_R506"
write("female-v249-mainline-crown-root-width-r508.study.json", r508)

r509 = read("female-v249-mainline-skin-tone-r509.study.json")
r509["visualAssessment"] = {
    "selected": "b-lighter-neutral",
    "status": "SELECTED_FOR_R510",
    "reason": "It removes the brown/dim cast while retaining facial plane separation. c begins to flatten secondary forms and d is visibly washed out.",
}
r509["status"] = "SELECTED_B_FOR_R510_TECHNICAL_CANDIDATE"
write("female-v249-mainline-skin-tone-r509.study.json", r509)

parity = read("female-v249-mainline-lighter-neutral-skin-r510.material-parity-audit.json")
performance = {
    "candidate": "aevrynd-female-authoring-v249-mainline-lighter-neutral-skin-r510.blend",
    "baseline": "aevrynd-female-authoring-v249-mainline-layered-rear-locks-r506.blend",
    "basis": "material parameter invariance",
    "meshInventoryExact": not parity["changedMeshes"],
    "armatureExact": parity["armatureExact"],
    "shaderNodeCountExact": parity["shaderTopologyExact"],
    "shaderLinkCountExact": parity["shaderTopologyExact"],
    "textureCountDelta": 0,
    "drawCallDelta": 0,
    "triangleDelta": 0,
    "runtimeAllocationDeltaBytes": 0,
    "explanation": "r510 changes two constant RGBA ramp endpoints in the existing skin shader. It adds no geometry, texture, node, link, material slot, modifier or draw call, so the measured r506 runtime cost remains invariant.",
    "status": "PASS",
}
write("female-v249-mainline-lighter-neutral-skin-r510.performance-contract-audit.json", performance)

review = {
    "candidate": "aevrynd-female-authoring-v249-mainline-lighter-neutral-skin-r510.blend",
    "baseline": "aevrynd-female-authoring-v249-mainline-layered-rear-locks-r506.blend",
    "reviewSet": "reviews/v249r510-lighter-neutral-skin-11shot/contact-sheet-11shot.jpg",
    "strictScores100": {
        "hair": 45,
        "eyes": 68,
        "faceGeometry": 56,
        "skinSurface": 57,
        "mouth": 53,
        "bodyAndClothing": 49,
        "overallCharacter": 54,
    },
    "improvements": [
        "The fixed face regions are 24.79-26.72 percent brighter in scene-linear luminance without changing lights or exposure.",
        "The former brown/dim cast is reduced and the eye sockets, nasal planes, cheeks and lips remain readable.",
        "All 11 views preserve the accepted r506 geometry, rear hair silhouette and pose behavior.",
    ],
    "remainingFailures": [
        "Crown part and front/side hair cards remain broad, straight and planar.",
        "Facial secondary planes, lid thickness, orbital fat and expression anatomy remain below hero quality.",
        "Skin still lacks authored regional vascular, oil, dry and pigmentation maps.",
        "Garment silhouette, seams, thickness and material response remain basic.",
    ],
    "technicalGates": {
        "exactMeshParity": "PASS",
        "exactArmatureParity": "PASS",
        "fourFrameHairBodyAndClothingCollision": "PASS",
        "toneIntent": "PASS_INTENTIONAL_BRIGHTENING_24_79_TO_26_72_PERCENT",
        "performanceStructuralParity": "PASS_ZERO_COST_DELTA",
        "elevenViewReview": "PASS_NO_NEW_ARTIFACT",
    },
    "status": "TECHNICAL_GATES_PASS_VISUAL_HERO_GATE_FAIL",
    "websitePromotionApproved": False,
}
write("female-v249-mainline-lighter-neutral-skin-r510.visual-review.json", review)

current = read("female-v249-mainline-current.json")
current["latestCharacterTechnicalCandidate"] = "aevrynd-female-authoring-v249-mainline-lighter-neutral-skin-r510.blend"
current["latestCharacterCandidateStatus"] = "R510_OFFLINE_TECHNICAL_MAINLINE; selected r509 b-lighter-neutral removes the progressive dark appearance by increasing fixed face-region luminance 24.79%-26.72% with unchanged lights/exposure. Exact geometry, armature and shader topology parity pass; r506 four-frame hair/body/clothing collision and runtime cost are invariant. Strict overall score is 54/100 and hero quality still fails, so website v83 is unchanged."
current["latestSkinTechnicalCandidate"] = "aevrynd-female-authoring-v249-mainline-lighter-neutral-skin-r510.blend"
current["latestSkinCandidateStatus"] = "r510 changes only the two linear-RGBA endpoints of the existing melanin ramp. It adds no mesh, texture, node, link, slot or draw call. Fixed face regions brighten 24.79%-26.72%; c and d are rejected for flattening or washing out facial planes. Regional skin maps and stronger secondary anatomy are still required."
current["latestSkinToneAudit"] = "female-v249-mainline-lighter-neutral-skin-r510.tone-audit.json"
current["latestSkinToneStatus"] = "PASS_INTENTIONAL_LIGHTER_NEUTRAL_RESPONSE; forehead +26.717%, left cheek +24.792%, right cheek +25.525%, chin +24.846% with Standard/None, exposure 0 and the complete light rig unchanged."
current["latestRejectedExperiment"] += "; r507 shortened/curved crown collision failures; r508 collision-safe but visually negligible crown-root widening"
current["latestRejectedReason"] = "r507 crown replacements remain planar and create 17.0-19.9mm dynamic body penetration. r508 preserves the accepted guide envelope and passes collision, but 1.15x/1.30x root widening is visually negligible. Crown improvement requires new asymmetric guide families rather than parameter edits to r467 cards."
current["latestHairResearch"] += "; r507-r508 rejected crown replacement/root-width studies"
current["latestHairResearchStatus"] = "r506 remains the hair technical candidate at 45/100. r507 proves that shortening/curving the inherited crown cards creates dynamic body penetration without fixing the planar flow; r508 proves collision-safe root widening alone is visually negligible. The next hair pass must author new asymmetric crown guide families. r510 changes skin tone only."
write("female-v249-mainline-current.json", current)
print("AEVRYND_R510_FINALIZED")
