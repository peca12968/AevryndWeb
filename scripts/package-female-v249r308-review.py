import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "assets-source/aevrynd-character"
TEMP = ROOT.parent / "Temp/female-realism"
REVIEW = ASSET / "reviews/v249r308-hair-eye-technical-pass"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


REVIEW.mkdir(parents=True, exist_ok=True)
copies = {
    TEMP / "v249r301-recessed-natural-eyes/face-close-f01.png": "r301-before-face-close.png",
    TEMP / "v249r308-curved-projected-upper-eyelids/front-f01.png": "r308-front-f01.png",
    TEMP / "v249r308-curved-projected-upper-eyelids/front-f20.png": "r308-front-f20.png",
    TEMP / "v249r308-curved-projected-upper-eyelids/face-close-f01.png": "r308-face-close-f01.png",
    TEMP / "v249r308-curved-projected-upper-eyelids/three-quarter-f01.png": "r308-three-quarter-f01.png",
    TEMP / "v249r308-curved-projected-upper-eyelids/left-f01.png": "r308-left-f01.png",
    TEMP / "v249r308-curved-projected-upper-eyelids/right-f01.png": "r308-right-f01.png",
    TEMP / "v249r305-projected-upper-eyelids/three-quarter-f01.png": "r305-rejected-flat-lid-three-quarter.png",
    TEMP / "v249r299-surface-baby-hairs/front-f01.png": "r299-rejected-spike-hairline.png",
}
for source, target in copies.items():
    if not source.exists():
        raise FileNotFoundError(source)
    shutil.copy2(source, REVIEW / target)

r301_path = ASSET / "female-v249-mainline-recessed-natural-eyes-r301.build-report.json"
r301 = read(r301_path)
r301.update({
    "status": "TECHNICAL_PASS_VISUAL_FAIL",
    "strictFaceVisualScore": 57,
    "visualFinding": "Warm recessed sclera and larger iris are safe, but the inherited round aperture leaves the character staring and cannot meet the hero-face gate.",
})
write(r301_path, r301)

for filename, status, score, finding in (
    ("female-v249-mainline-macro-lock-hierarchy-r297.build-report.json", "TECHNICAL_FAIL_VISUAL_FAIL", 63, "Macro families and tapered ends improve grouping, but one secondary rest outlier and one moving flyaway penetrate."),
    ("female-v249-mainline-pruned-dynamic-outliers-r298.build-report.json", "TECHNICAL_PASS_VISUAL_FAIL", 63, "Outliers are removed and motion passes; the silhouette, hairline and needle-like ends remain below hero quality."),
    ("female-v249-mainline-surface-baby-hairs-r299.build-report.json", "TECHNICAL_PASS_VISUAL_REJECT", 59, "Projected short hairs read as sparse hard spikes across the forehead."),
):
    path = ASSET / filename
    data = read(path)
    data.update({"status": status, "strictHairVisualScore": score, "visualFinding": finding})
    write(path, data)

r305_path = ASSET / "female-v249-mainline-projected-upper-eyelids-r305.build-report.json"
r305 = read(r305_path)
r305.update({
    "status": "TECHNICAL_PASS_VISUAL_REJECT",
    "strictFaceVisualScore": 58,
    "visualFinding": "Front iris occlusion improves, but constant inner-edge depth projects as a visor in three-quarter view.",
})
write(r305_path, r305)

r308_path = ASSET / "female-v249-mainline-curved-projected-upper-eyelids-r308.build-report.json"
r308 = read(r308_path)
r308.update({
    "status": "TECHNICAL_PASS_VISUAL_FAIL",
    "strictScores": {"face": 60, "hair": 63, "overallCharacter": 59},
    "visualGains": [
        "Upper lids now occlude the upper iris and reduce the round staring expression.",
        "Corner depth follows the globe and no longer forms the severe flat visor seen in r305.",
        "Upper lid margins and lashes follow the new aperture and remain head-bound.",
    ],
    "visualFailures": [
        "The separate lid surface still reads as a transitional overlay at close range; final work requires unified local eyelid retopology.",
        "Orbital, lower-lid and tear-trough anatomy remain too smooth and generic.",
        "Skin lacks regional oil, dry, vascular and pigmentation response and still reads waxy.",
        "Hairline remains sparse with a bright scalp band; the bob silhouette and needle-like ends remain synthetic.",
    ],
    "reviewDirectory": str(REVIEW),
    "websitePromotionApproved": False,
})
write(r308_path, r308)

for name, status, selection in (
    ("female-v249-mainline-eyelid-aperture-r302.study.json", "REJECTED_LOW_IMPACT", "Sparse base vertices cannot materially reshape the aperture."),
    ("female-v249-mainline-upper-eyelid-layer-r303.study.json", "DIRECTION_PROVEN_VARIANTS_REJECTED", "Independent lid surface can occlude iris; floating outer seam must be projected."),
    ("female-v249-mainline-integrated-upper-lid-r304.study.json", "REJECTED_VISIBLE_SEAM", "Depth alone leaves a swollen semicircular seam."),
    ("female-v249-mainline-curved-upper-lid-r306.study.json", "DIRECTION_PROVEN_VARIANTS_REJECTED", "Corner recession removes the flat visor but middle rows remain too free of the face."),
    ("female-v249-mainline-lid-projection-r307.study.json", "SELECTED_B_FAST_FOR_R308", "b-fast projection power 0.65 selected for the r308 technical node."),
):
    path = ASSET / name
    data = read(path)
    data["status"] = status
    data["selection"] = selection
    write(path, data)

study = {
    "range": "v249r297-r308",
    "currentTechnicalNode": "aevrynd-female-authoring-v249-mainline-curved-projected-upper-eyelids-r308.blend",
    "hair": {
        "source": "r298 pruned macro-lock hierarchy",
        "visiblePoints": 262368,
        "layers": ["scalp underlayer", "primary clumps", "secondary fill", "hairline transition", "flyaways", "hidden runtime proxy"],
        "collisionFrames": [1, 33, 61],
        "penetratingPoints": 0,
        "rootMaximumM": 0.0,
        "settleMaximumM": 0.0,
        "peakP95M": 0.0034924972303594357,
        "strictScore": 63,
    },
    "eyes": {
        "r301": "safe sclera tone, 1.2mm recess and 1.08 iris scale",
        "r302": "base-mesh sparse-vertex deformation rejected as visually negligible",
        "r303-r307": "upper-lid surface, seam-depth, corner-curvature and projection studies",
        "r308": "205 vertices and 160 faces per upper lid, projected to 0.1mm body clearance",
        "collisionFrames": [1, 20],
        "triangleOverlaps": 0,
        "headBindingViolations": 0,
        "strictScore": 60,
    },
    "status": "TECHNICAL_PASS_VISUAL_FAIL",
    "websiteAsset": "v83",
    "websitePromotionApproved": False,
    "next": "Replace the transitional upper-lid overlays with unified local eyelid retopology, then sculpt the lower lid, tear trough and orbital planes before further material polish.",
}
write(ASSET / "female-v249-mainline-r297-r308.study.json", study)

manifest_path = ASSET / "female-v249-mainline-current.json"
manifest = read(manifest_path)
manifest.update({
    "latestHairPerformanceResearch": "r227-r272 density and thin cards; r273-r287 runtime wide-card layers; r288-r298 authored curves, macro locks and collision-safe motion; r299 rejected baby-hair study",
    "latestHairPerformanceResearchStatus": "r298 retains 776 primary, 10,086 secondary and 70 flyaway curves at 262,368 visible points. Frames 1/33/61 have zero penetration, zero root drift and zero settle error with 3.492mm peak P95 motion. r299 surface baby hairs are rejected as sparse spikes.",
    "latestHairAuthoringCandidate": "aevrynd-female-authoring-v249-mainline-curved-projected-upper-eyelids-r308.blend",
    "latestHairAuthoringAudit": "female-v249-mainline-curved-projected-upper-eyelids-r308.hair-motion-audit.json",
    "latestHairAuthoringLayerAudit": "female-v249-mainline-curved-projected-upper-eyelids-r308.hair-layer-audit.json",
    "latestHairAuthoringStatus": "TECHNICAL_PASS_VISUAL_FAIL_SCORE_63; r308 preserves the r298 curve groom and its zero-penetration motion while adding the eye work; runtime promotion remains forbidden",
    "latestEyeTechnicalCandidate": "aevrynd-female-authoring-v249-mainline-curved-projected-upper-eyelids-r308.blend",
    "latestEyeCandidateStatus": "r301 safely tones/recesses the optical stack. r302 proves sparse base vertices are insufficient. r303-r307 establish and refine a separate projected upper-lid layer. r308 passes body and eye triangle-overlap gates at frames 1/20 and head-binding checks, but strict eye/face quality is 60/100 and still requires unified local retopology.",
    "latestFaceTechnicalCandidate": "aevrynd-female-authoring-v249-mainline-curved-projected-upper-eyelids-r308.blend",
    "latestFaceCandidateStatus": "TECHNICAL_PASS_VISUAL_FAIL_SCORE_60; upper-iris occlusion and corner curvature improve the expression, while overlay seams, flat lower lids, generic orbital planes and waxy regional skin keep it below hero quality.",
    "latestRejectedExperiment": "r299 spike-like surface baby hairs; r302 low-impact sparse-vertex lid deformation; r303-r304 floating lid seams; r305 flat visor; r306-r307 nonselected lid curvature/projection variants",
    "latestRejectedReason": "Each rejected branch either fails normal-distance visibility or introduces a seam/protrusion visible in close and three-quarter review. r308 is retained only as a collision-safe technical topology target.",
    "latestFaceResearch": "r248 legacy displacement rejection; r249-r258 CC0 foundation; r300-r301 eye optical sweep; r302-r308 eyelid aperture, curvature and surface-projection studies",
    "latestFaceResearchStatus": "r308 is the current combined CC0 technical node. All 26 tracked eye/face layers remain head-bound with negligible drift, and the new upper lids have zero triangle overlaps with body and optical layers at frames 1/20. Strict visual gate remains failed.",
})
next_work = manifest.get("nextRequiredWork", [])
priority = "以 r308 為技術參考，對眼眶區做正式局部重拓撲，將上眼瞼接入臉部連續網格並雕刻下眼瞼、淚溝與眶周平面；完成後重跑眼球、臉部綁定與表情碰撞"
manifest["nextRequiredWork"] = [priority] + [item for item in next_work if item != priority]
write(manifest_path, manifest)

print(json.dumps({"reviewDirectory": str(REVIEW), "copied": len(copies), "status": r308["status"]}, ensure_ascii=False))
