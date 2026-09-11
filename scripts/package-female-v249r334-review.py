import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
TEMP = ROOT.parent / "Temp/female-realism"
REVIEW = ASSETS / "reviews/v249r334-continuous-upper-lower-eyelids"


def read(name):
    return json.loads((ASSETS / name).read_text(encoding="utf-8"))


def write(name, value):
    (ASSETS / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


updates = {
    "female-v249-mainline-layered-iris-shader-r331.study.json": "REJECT_GRAPHIC_COLLARETTE_AND_NEGLIGIBLE_VASCULAR_GAIN",
    "female-v249-mainline-dense-lower-eyelid-r332.study.json": "VISUAL_GAIN_COLLISION_FAIL_SELECTED_4P1MM",
    "female-v249-mainline-lower-lid-sclera-clearance-r333.study.json": "SELECTED_0P2MM_MINIMUM_ZERO_OVERLAP_RECESS",
}
for name, status in updates.items():
    data = read(name)
    data["status"] = status
    write(name, data)

r334_name = "female-v249-mainline-continuous-upper-lower-eyelids-r334.build-report.json"
r334 = read(r334_name)
r334.update({
    "status": "TECHNICAL_PASS_VISUAL_FAIL",
    "strictBenchmark": "current-generation hero character, normal gameplay and face-close views",
    "strictScores": {"face": 42, "hair": 34, "overallCharacter": 38},
    "technicalGains": [
        "The continuous 169,362-vertex body now forms both upper and lower eyelids.",
        "The selected 4.1mm lower aperture moves 688 left and 687 right body vertices with a maximum 1.481mm displacement.",
        "A minimal 0.2mm posterior eye correction clears both integrated spherical eyes at frames 1 and 20.",
        "All 16 face layers remain head-bound, all body vertices remain weighted, and all 262,368 authored hair points remain penetration-free at frames 1, 33 and 61.",
    ],
    "visualGains": ["The lower lid has more visible thickness and slightly reduces the fully exposed, round eye opening."],
    "visualFailures": [
        "The eye opening remains too wide and the sclera too bright, preserving a staring mannequin expression.",
        "Caruncle, tear trough, canthal transitions and lower-orbit planes remain shallow.",
        "The retained r328 iris is cleaner than r331, but still lacks natural crypt and radial depth.",
        "Skin remains waxy with weak pore, vascular, oil and pigmentation breakup.",
        "Hairline gaps, uniform curtain flow, isolated guide-like strands and needle ends remain severe.",
    ],
    "faceLayerAudit": str(ASSETS / "female-v249-mainline-continuous-upper-lower-eyelids-r334.face-layer-audit.json"),
    "bodyRigAudit": str(ASSETS / "female-v249-mainline-continuous-upper-lower-eyelids-r334.body-rig-audit.json"),
    "hairLayerAudit": str(ASSETS / "female-v249-mainline-continuous-upper-lower-eyelids-r334.hair-layer-audit.json"),
    "hairMotionAudit": str(ASSETS / "female-v249-mainline-continuous-upper-lower-eyelids-r334.hair-motion-audit.json"),
    "reviewDirectory": str(REVIEW),
    "websitePromotionApproved": False,
})
write(r334_name, r334)

study = {
    "range": "r331-r334",
    "sourceCandidate": "aevrynd-female-authoring-v249-mainline-integrated-eye-shader-r328.blend",
    "resultCandidate": "aevrynd-female-authoring-v249-mainline-continuous-upper-lower-eyelids-r334.blend",
    "status": "TECHNICAL_PASS_VISUAL_FAIL",
    "findings": [
        "r331's stronger collarette and veins read as graphic at review distance; retain the calmer r328 iris.",
        "r332 selects the restrained 4.1mm lower aperture, but direct placement intersects the left sclera.",
        "r333 establishes 0.2mm as the minimum tested posterior correction with zero body-eye overlap.",
        "r334 integrates both changes and passes collision, face binding, body rig and hair motion audits.",
    ],
    "strictScores": {"face": 42, "hair": 34, "overallCharacter": 38},
    "websitePromotionApproved": False,
}
write("female-v249-mainline-r331-r334.study.json", study)

current_name = "female-v249-mainline-current.json"
current = read(current_name)
candidate = "aevrynd-female-authoring-v249-mainline-continuous-upper-lower-eyelids-r334.blend"
current.update({
    "latestEyeTechnicalCandidate": candidate,
    "latestEyeCandidateStatus": "r334 adds continuous lower lids and a minimal 0.2mm eye recess. Body-eye overlap is zero at frames 1/20; visual quality remains below the hero-character gate.",
    "latestFaceTechnicalCandidate": candidate,
    "latestFaceCandidateStatus": "TECHNICAL_PASS_VISUAL_FAIL_SCORE_42; lower-lid structure improves slightly, while the eye opening, orbital anatomy, skin response and symmetry remain mannequin-like.",
    "latestFaceResearch": "r248 legacy displacement rejection; r249-r258 CC0 foundation; r300-r330 eye, collision and exposure studies; r331-r334 iris rejection and continuous lower-lid integration",
    "latestFaceResearchStatus": "r334 is the current technical node: 16 head-bound face layers, zero body-eye overlap at frames 1/20 and a fully weighted 169,362-vertex body. Strict visual gate remains failed.",
    "latestHairAuthoringCandidate": candidate,
    "latestHairAuthoringAudit": "female-v249-mainline-continuous-upper-lower-eyelids-r334.hair-motion-audit.json",
    "latestHairAuthoringLayerAudit": "female-v249-mainline-continuous-upper-lower-eyelids-r334.hair-layer-audit.json",
    "latestHairAuthoringStatus": "TECHNICAL_PASS_VISUAL_FAIL_SCORE_34; 262,368 authored points remain collision-safe and animated, but silhouette, hairline, clustering and strand endings fail the hero-quality gate.",
})
work = current.get("nextRequiredWork", [])
if work:
    work[0] = "以 r334 為技術基底，重建內外眼角、淚阜、淚溝與眶周平面，降低眼白視覺亮度並加入自然左右差異；任何修改都需重跑 frame 1/20 眼球穿模與多角度審查。"
write(current_name, current)

REVIEW.mkdir(parents=True, exist_ok=True)
copies = {
    TEMP / "v249r331-layered-iris-shader-sweep/a-r328-eyes.png": "r331-retained-r328-iris.png",
    TEMP / "v249r331-layered-iris-shader-sweep/b-layered-eyes.png": "r331-rejected-graphic-collarette.png",
    TEMP / "v249r332-dense-lower-eyelid-sweep/a-4p1mm-eyes.png": "r332-selected-4p1mm-collision-fail.png",
    TEMP / "v249r333-lower-lid-sclera-clearance-sweep/b-recess-0p2mm-eyes.png": "r333-selected-0p2mm-clearance.png",
}
for name in ("front-f01", "front-f20", "face-close-f01", "eyes-close-f01", "three-quarter-f01", "left-f01", "right-f01", "back-f01"):
    copies[TEMP / "v249r334-continuous-upper-lower-eyelids" / f"{name}.png"] = f"r334-{name}.png"
for source, target in copies.items():
    if not source.exists():
        raise FileNotFoundError(source)
    shutil.copy2(source, REVIEW / target)

print(json.dumps({"status": "PACKAGED", "review": str(REVIEW), "files": len(copies)}, ensure_ascii=False))
