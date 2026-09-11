import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
TEMP = ROOT.parent / "Temp/female-realism"
REVIEW = ASSETS / "reviews/v249r328-unified-lid-integrated-eye"


def read(name):
    return json.loads((ASSETS / name).read_text(encoding="utf-8"))


def write(name, value):
    (ASSETS / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


status_updates = {
    "female-v249-mainline-native-lid-baseline-r319.study.json": "DIAGNOSTIC_NATIVE_APERTURE_TOO_OPEN",
    "female-v249-mainline-unified-dense-eyelid-r320.study.json": "VISUAL_GAIN_COLLISION_FAIL",
    "female-v249-mainline-dense-eyelid-eye-recess-r321.study.json": "REJECT_RECESS_INCREASES_FRONT_OPTICAL_COLLISIONS",
    "female-v249-mainline-dense-eyelid-split-depth-r322.study.json": "TECHNICAL_PASS_PROFILE_VISUAL_FAIL",
    "female-v249-mainline-dense-eyelid-ray-wrap-r324.study.json": "REJECT_FOLDING_AND_COLLISION",
    "female-v249-mainline-integrated-eye-shader-r327.study.json": "SELECTED_INTEGRATED_SHADER_DIRECTION",
}
for name, status in status_updates.items():
    data = read(name)
    data["status"] = status
    write(name, data)

r323_name = "female-v249-mainline-unified-dense-upper-eyelids-r323.build-report.json"
r323 = read(r323_name)
r323.update({
    "status": "TECHNICAL_PASS_VISUAL_FAIL_EYE_PROTRUSION",
    "strictScores": {"face": 62, "hair": 63, "overallCharacter": 60},
    "visualFailure": "The 0.9mm anterior front-optical offset required for zero overlap is visibly proud of the eyelid in profile; r328 removes these flat optical layers.",
    "websitePromotionApproved": False,
})
write(r323_name, r323)

r328_name = "female-v249-mainline-integrated-eye-shader-r328.build-report.json"
r328 = read(r328_name)
r328.update({
    "status": "TECHNICAL_PASS_VISUAL_FAIL",
    "strictScores": {"face": 63, "hair": 63, "overallCharacter": 61},
    "technicalGains": [
        "The separate r308 upper-lid overlays are absent; the 169,362-vertex body now forms the upper lids continuously.",
        "Eight planar cornea, limbal, iris and pupil objects are removed, eliminating their body and internal intersection classes.",
        "Each eye uses one owned 546-vertex spherical mesh with procedural sclera, limbal ring, iris, pupil and corneal-coat material layers.",
        "Body-versus-integrated-eye overlap is zero at frames 1 and 20.",
        "All 16 remaining face layers stay head-bound; all 169,362 body vertices retain weights in 21 groups and deform at frame 20.",
        "The 262,368-point authored groom retains zero body penetration at frames 1, 33 and 61."
    ],
    "visualGains": [
        "The upper eyelid no longer shows the separate r308 overlay seam.",
        "The eye profile no longer exposes protruding planar optical discs.",
        "The 2.2mm upper aperture reduces the round staring expression while keeping the iris readable."
    ],
    "visualFailures": [
        "The procedural iris is still too graphic and lacks the layered crypt, collarette and vascular detail expected of hero eyes.",
        "The lower lid, tear trough and caruncle remain shallow and generic.",
        "The neutral expression remains symmetrical and mannequin-like.",
        "Skin response remains waxy and lacks regional oil, dry, vascular and pigmentation variation.",
        "Hairline gaps, uniform curtain flow and needle-like ends remain the largest silhouette defects."
    ],
    "faceLayerAudit": str(ASSETS / "female-v249-mainline-integrated-eye-shader-r328.face-layer-audit.json"),
    "bodyRigAudit": str(ASSETS / "female-v249-mainline-integrated-eye-shader-r328.body-rig-audit.json"),
    "hairLayerAudit": str(ASSETS / "female-v249-mainline-integrated-eye-shader-r328.hair-layer-audit.json"),
    "hairMotionAudit": str(ASSETS / "female-v249-mainline-integrated-eye-shader-r328.hair-motion-audit.json"),
    "skinToneAudit": str(ASSETS / "female-v249-mainline-lighting-skin-tone-r329.study.json"),
    "exposureCalibration": str(ASSETS / "female-v249-mainline-exposure-calibration-r330.study.json"),
    "reviewDirectory": str(REVIEW),
    "websitePromotionApproved": False,
})
write(r328_name, r328)

study = {
    "range": "r319-r328",
    "sourceCandidate": "aevrynd-female-authoring-v249-mainline-collision-safe-optical-stack-r318.blend",
    "resultCandidate": "aevrynd-female-authoring-v249-mainline-integrated-eye-shader-r328.blend",
    "status": "TECHNICAL_PASS_VISUAL_FAIL",
    "findings": [
        "r319 proves the native opening is too large when the r308 overlay is hidden.",
        "r320 applies the dense evaluated body and establishes 2.2mm as the strongest stable aperture, but the lowered lid intersects planar optical layers.",
        "r321 proves posterior eye movement worsens planar-layer intersections.",
        "r322-r323 reach zero overlap by splitting sclera and front-layer depth, but profile review exposes the planar optical stack as protruding.",
        "r324 camera-axis wrapping folds the connected lid transition and creates hundreds of sclera overlaps; it is rejected.",
        "r325-r326 measure the 546-vertex sclera and the optical layer bounds needed to replace the planar stack.",
        "r327 integrates sclera, iris, limbal ring, pupil and corneal coat in an owned procedural shader on one spherical mesh.",
        "r328 removes eight planar optical objects and passes collision, head-binding, body-rig and hair-motion audits."
    ],
    "strictScores": {"face": 63, "hair": 63, "overallCharacter": 61},
    "websitePromotionApproved": False,
}
write("female-v249-mainline-r319-r328.study.json", study)

skin_study = {
    "range": "r329-r330",
    "sourceCandidate": "aevrynd-female-authoring-v249-mainline-integrated-eye-shader-r328.blend",
    "status": "PASS_NO_PROGRESSIVE_SKIN_DARKENING",
    "measurements": {
        "r318FixedPatchLuminance": 117.765,
        "r328FixedPatchLuminance": 117.779,
        "r328Plus0p25EVLuminance": 127.634,
        "r328Plus0p50EVLuminance": 138.198,
        "plus0p50EVNearClipPixelPercent": 0.812,
    },
    "decision": "Retain the authored 0 EV exposure and skin material. Preserve +0.25 EV as a brighter review-lighting option, and use 117.779 as the fixed-patch regression baseline for this camera.",
}
write("female-v249-mainline-r329-r330-skin-tone.study.json", skin_study)

current_name = "female-v249-mainline-current.json"
current = read(current_name)
candidate = "aevrynd-female-authoring-v249-mainline-integrated-eye-shader-r328.blend"
current.update({
    "latestEyeTechnicalCandidate": candidate,
    "latestEyeCandidateStatus": "r328 removes the r308 lid overlays and eight planar optical objects. One spherical eye per side now carries owned procedural sclera, limbal, iris, pupil and corneal-coat layers. Body-eye overlap is zero at frames 1/20, but strict eye detail remains below hero quality.",
    "latestFaceTechnicalCandidate": candidate,
    "latestFaceCandidateStatus": "TECHNICAL_PASS_VISUAL_FAIL_SCORE_63; continuous dense upper lids remove the overlay seam and the integrated eye fixes profile protrusion, while lower-lid anatomy, iris microstructure, facial asymmetry and skin response remain underdeveloped.",
    "latestRejectedExperiment": "r299 spike-like baby hairs; r302 sparse lid deformation; r303-r308 transitional lid overlays; r311 ineffective base displacement; r313 socket extrusion; r314 iris-hiding conformal stack; r321 posterior eye recess; r323 protruding planar optics; r324 folded ray-wrap lid",
    "latestRejectedReason": "The rejected branches either fail normal-distance visibility, increase collision counts, expose planar eye layers in profile, hide the iris, or fold the connected skin surface. r328 retains the continuous body lid and replaces the planar eye stack.",
    "latestFaceResearch": "r248 legacy displacement rejection; r249-r258 CC0 foundation; r300-r318 eye and collision studies; r319-r328 continuous dense lids and integrated eye shader",
    "latestFaceResearchStatus": "r328 is the current combined CC0 technical node. It has one integrated eye mesh per side, 16 head-bound face layers, zero body-eye overlap at frames 1/20, a fully weighted 169,362-vertex body and preserved collision-safe hair. Strict visual gate remains failed.",
    "latestHairAuthoringCandidate": candidate,
    "latestHairAuthoringAudit": "female-v249-mainline-integrated-eye-shader-r328.hair-motion-audit.json",
    "latestHairAuthoringLayerAudit": "female-v249-mainline-integrated-eye-shader-r328.hair-layer-audit.json",
    "latestHairAuthoringStatus": "TECHNICAL_PASS_VISUAL_FAIL_SCORE_63; r328 preserves 262,368 visible authored hair points with zero penetration at frames 1/33/61, zero root drift and zero settle error; runtime promotion remains forbidden"
})
current["latestSkinToneAudit"] = "female-v249-mainline-r329-r330-skin-tone.study.json"
current["latestSkinToneStatus"] = "PASS_NO_PROGRESSIVE_DARKENING; fixed-patch face luminance is 117.765 at r318 and 117.779 at r328. The darker impression is caused by stronger local eye contrast. Keep 0 EV as the authored baseline; +0.25 EV is retained only as a brighter review-lighting option."
work = current.get("nextRequiredWork", [])
if work:
    work[0] = "以 r328 的連續高密度眼瞼與單球眼睛為基礎，增加下眼瞼厚度、淚阜、淚溝與眶周平面；將程序虹膜擴充為角膜緣、虹膜隱窩、瞳孔緣與微血管分層，再重跑全眼球與表情碰撞。"
write(current_name, current)

REVIEW.mkdir(parents=True, exist_ok=True)
copies = {
    TEMP / "v249r319-native-lid-baseline/face-close.png": "r319-native-opening-too-large.png",
    TEMP / "v249r320-unified-dense-eyelid-sweep/c-2p2mm-front.png": "r320-selected-aperture-collision-fail.png",
    TEMP / "v249r323-unified-dense-upper-eyelids/left-f01.png": "r323-rejected-protruding-optics-profile.png",
    TEMP / "v249r324-dense-eyelid-ray-wrap-sweep/a-clearance-0p15mm-front.png": "r324-rejected-folded-ray-wrap.png",
    TEMP / "v249r327-integrated-eye-shader/face-close.png": "r327-selected-integrated-shader.png",
    TEMP / "v249r328-integrated-eye-shader/face-close-f01.png": "r328-face-close-f01.png",
    TEMP / "v249r328-integrated-eye-shader/three-quarter-f01.png": "r328-three-quarter-f01.png",
    TEMP / "v249r328-integrated-eye-shader/left-f01.png": "r328-left-f01.png",
    TEMP / "v249r328-integrated-eye-shader/right-f01.png": "r328-right-f01.png",
    TEMP / "v249r328-integrated-eye-shader/front-f20.png": "r328-front-f20.png",
    TEMP / "v249r328-integrated-eye-shader/back-f01.png": "r328-back-f01.png",
    TEMP / "v249r330-exposure-calibration/a-current-0ev.png": "r330-current-0ev.png",
    TEMP / "v249r330-exposure-calibration/b-plus-0p25ev.png": "r330-review-plus-0p25ev.png",
    TEMP / "v249r330-exposure-calibration/c-plus-0p50ev.png": "r330-rejected-plus-0p50ev-clipping.png",
}
for source, target in copies.items():
    if not source.exists():
        raise FileNotFoundError(source)
    shutil.copy2(source, REVIEW / target)

print(json.dumps({"status": "PACKAGED", "review": str(REVIEW), "files": len(copies)}, ensure_ascii=False))
