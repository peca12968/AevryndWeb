import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
TEMP = ROOT.parent / "Temp/female-realism"
REVIEW = ASSETS / "reviews/v249r318-optical-collision-pass"


def read(name):
    return json.loads((ASSETS / name).read_text(encoding="utf-8"))


def write(name, value):
    (ASSETS / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


build_name = "female-v249-mainline-collision-safe-optical-stack-r318.build-report.json"
build = read(build_name)
build.update({
    "status": "TECHNICAL_PASS_VISUAL_FAIL",
    "strictScores": {"face": 61, "hair": 63, "overallCharacter": 60},
    "technicalGains": [
        "The complete body-versus-eye audit is zero-overlap at frames 1 and 20 for sclera, cornea, limbal ring, iris and pupil on both eyes.",
        "The upper-lid overlay is zero-overlap against the body and every optical layer at frames 1 and 20.",
        "The cornea is separated from the limbal ring, iris and pupil; the iris and pupil are also intersection-free.",
        "All 26 tracked face layers remain head-bound, and the 262,368-point authored groom retains zero body penetration at frames 1, 33 and 61."
    ],
    "visualGains": [
        "The 0.76 optical-stack scale fits within the aperture without the face intersections discovered in r312.",
        "The iris-to-sclera proportion is less dominant than r308 while retaining the intended green eye material.",
        "The 0.08mm cornea-to-iris clearance removes hidden internal intersections without a visible step in the review renders."
    ],
    "visualFailures": [
        "The eye aperture remains too round and open for a natural neutral expression.",
        "The separate upper-lid surface reads as an overlay seam and is not acceptable final facial topology.",
        "Lower-lid thickness, tear troughs, caruncles and orbital planes remain underdeveloped.",
        "Skin response remains waxy and lacks regional variation.",
        "The hairline has sparse bright gaps, uniform curtain flow and needle-like ends."
    ],
    "faceLayerAudit": str(ASSETS / "female-v249-mainline-collision-safe-optical-stack-r318.face-layer-audit.json"),
    "hairLayerAudit": str(ASSETS / "female-v249-mainline-collision-safe-optical-stack-r318.hair-layer-audit.json"),
    "hairMotionAudit": str(ASSETS / "female-v249-mainline-collision-safe-optical-stack-r318.hair-motion-audit.json"),
    "reviewDirectory": str(REVIEW),
    "websitePromotionApproved": False
})
write(build_name, build)

r308_name = "female-v249-mainline-curved-projected-upper-eyelids-r308.build-report.json"
r308 = read(r308_name)
r308["status"] = "PARTIAL_TECHNICAL_PASS_GLOBAL_EYE_COLLISION_FAIL"
r308["collisionStatus"] = "PASS_UPPER_LID_ONLY_GLOBAL_EYE_STACK_FAIL"
r308["supersededBy"] = "aevrynd-female-authoring-v249-mainline-collision-safe-optical-stack-r318.blend"
r308["correction"] = (
    "The original r308 audit covered the added upper-lid surfaces. The broader r312 audit found 786 body-versus-optical-layer "
    "triangle overlaps across frames 1 and 20 in the inherited cornea, limbal and iris geometry. r318 closes those overlaps."
)
write(r308_name, r308)

study = {
    "range": "r309-r318",
    "sourceCandidate": "aevrynd-female-authoring-v249-mainline-curved-projected-upper-eyelids-r308.blend",
    "resultCandidate": "aevrynd-female-authoring-v249-mainline-collision-safe-optical-stack-r318.blend",
    "status": "TECHNICAL_PASS_VISUAL_FAIL",
    "findings": [
        "r309-r310 confirm that the native 10,582-vertex body has a regular eyelid control ring and evaluates to 169,362 vertices; raw topology density is not the main blocker.",
        "r311 native upper-lid motion is visually suppressed by the intersecting front optical stack.",
        "r312 exposes 786 body-versus-cornea/limbal/iris triangle overlaps across frames 1 and 20 in r301 and therefore in inherited r308 geometry.",
        "r313 moving the socket forward increases intersections and is rejected.",
        "r314 fully conformal optical geometry removes collisions but hides the iris behind opaque sclera and is visually rejected.",
        "r315 finds 0.76 as the largest tested uniform XZ optical scale with zero body overlap.",
        "r316 shows that scaling alone leaves cornea-to-iris and cornea-to-limbal intersections.",
        "r317 finds that clamping the cornea 0.08mm in front of the iris removes all tested internal optical overlaps.",
        "r318 combines the 0.76 optical scale and 0.08mm cornea clearance; full body, upper-lid, optical, face-binding and hair-motion audits pass."
    ],
    "strictScores": {"face": 61, "hair": 63, "overallCharacter": 60},
    "websitePromotionApproved": False,
    "reports": [
        "female-v249-mainline-eye-topology-wire-r309.study.json",
        "female-v249-mainline-eyelid-control-ring-r310.study.json",
        "female-v249-mainline-native-eyelid-sculpt-r311.study.json",
        "female-v249-mainline-body-eye-intersection-r312.audit.json",
        "female-v249-mainline-native-socket-clearance-r313.study.json",
        "female-v249-mainline-conformal-eye-stack-r314.study.json",
        "female-v249-mainline-collision-safe-optical-scale-r315.study.json",
        "female-v249-mainline-separated-optical-stack-r316.study.json",
        "female-v249-mainline-cornea-clearance-r317.study.json",
        build_name,
        "female-v249-mainline-collision-safe-optical-stack-r318.collision-audit.json",
        "female-v249-mainline-collision-safe-optical-stack-r318.face-layer-audit.json",
        "female-v249-mainline-collision-safe-optical-stack-r318.hair-layer-audit.json",
        "female-v249-mainline-collision-safe-optical-stack-r318.hair-motion-audit.json"
    ]
}
write("female-v249-mainline-r309-r318.study.json", study)

current_name = "female-v249-mainline-current.json"
current = read(current_name)
candidate = "aevrynd-female-authoring-v249-mainline-collision-safe-optical-stack-r318.blend"
current.update({
    "latestEyeTechnicalCandidate": candidate,
    "latestEyeCandidateStatus": "r312 corrected the incomplete r308 audit by finding 786 inherited body/optical overlaps. r315-r318 reduce the optical XZ scale to 0.76 and hold the cornea 0.08mm in front of the iris. Body, eyelid and internal optical overlaps are zero at frames 1/20, while strict eye/face quality remains 61/100 and requires unified local retopology.",
    "latestFaceTechnicalCandidate": candidate,
    "latestFaceCandidateStatus": "TECHNICAL_PASS_VISUAL_FAIL_SCORE_61; global eye collisions are closed, but the round aperture, upper-lid overlay seam, flat lower lid, generic orbital planes and waxy skin remain below hero quality.",
    "latestRejectedExperiment": "r299 spike-like surface baby hairs; r302 low-impact sparse-vertex lid deformation; r303-r304 floating lid seams; r305 flat visor; r306-r307 nonselected lid variants; r311 ineffective native-lid displacement; r313 collision-worsening socket extrusion; r314 iris-hiding conformal stack",
    "latestRejectedReason": "The rejected branches either fail normal-distance visibility, increase intersection counts, hide the iris, or introduce a visible seam. r318 is retained as a collision-safe technical candidate only.",
    "latestFaceResearch": "r248 legacy displacement rejection; r249-r258 CC0 foundation; r300-r301 eye optical sweep; r302-r308 eyelid studies; r309-r318 topology diagnosis and complete optical collision repair",
    "latestFaceResearchStatus": "r318 is the current combined CC0 technical node. The corrected broad audit has zero body/eye, eyelid/eye and internal optical triangle overlaps at frames 1/20; 26 face layers remain head-bound. Strict visual gate remains failed.",
    "latestHairAuthoringCandidate": candidate,
    "latestHairAuthoringAudit": "female-v249-mainline-collision-safe-optical-stack-r318.hair-motion-audit.json",
    "latestHairAuthoringLayerAudit": "female-v249-mainline-collision-safe-optical-stack-r318.hair-layer-audit.json",
    "latestHairAuthoringStatus": "TECHNICAL_PASS_VISUAL_FAIL_SCORE_63; r318 preserves 262,368 visible authored hair points with zero penetration at frames 1/33/61, zero root drift and zero settle error; runtime promotion remains forbidden"
})
work = current.get("nextRequiredWork", [])
if work:
    work[0] = "以 r318 的完整碰撞修正為基準，對眼眶區做正式局部重拓撲，將上眼瞼接入臉部連續網格並雕刻下眼瞼、淚阜、淚溝與眶周平面；完成後重跑全眼球、臉部綁定與表情碰撞。"
write(current_name, current)

REVIEW.mkdir(parents=True, exist_ok=True)
copies = {
    TEMP / "v249r309-eye-topology-wire/front.png": "r309-topology-wire-front.png",
    TEMP / "v249r314-conformal-eye-stack-sweep/b-cornea-0p78-front.png": "r314-rejected-conformal-white-eye.png",
    TEMP / "v249r315-collision-safe-optical-scale-sweep/c-0p76-front.png": "r315-selected-zero-overlap-scale.png",
    TEMP / "v249r318-collision-safe-optical-stack/face-close-f01.png": "r318-face-close-f01.png",
    TEMP / "v249r318-collision-safe-optical-stack/three-quarter-f01.png": "r318-three-quarter-f01.png",
    TEMP / "v249r318-collision-safe-optical-stack/front-f20.png": "r318-front-f20.png",
    TEMP / "v249r318-collision-safe-optical-stack/left-f01.png": "r318-left-f01.png",
    TEMP / "v249r318-collision-safe-optical-stack/right-f01.png": "r318-right-f01.png",
    TEMP / "v249r318-collision-safe-optical-stack/back-f01.png": "r318-back-f01.png"
}
for source, target in copies.items():
    if not source.exists():
        raise FileNotFoundError(source)
    shutil.copy2(source, REVIEW / target)

print(json.dumps({"status": "PACKAGED", "review": str(REVIEW), "files": len(copies)}, ensure_ascii=False))
