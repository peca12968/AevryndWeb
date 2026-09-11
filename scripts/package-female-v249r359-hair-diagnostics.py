import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
TEMP = ROOT.parent / "Temp/female-realism"
REVIEW = ASSETS / "reviews/v249r346-r359-hair-diagnostics"


def read(name):
    return json.loads((ASSETS / name).read_text(encoding="utf-8"))


def write(name, value):
    (ASSETS / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


updates = {
    "female-v249-mainline-outer-canthus-width-r346.study.json": (
        "REJECT_COLLISION_AND_OUTER_CANTHUS_NOTCHING",
        "All narrowed outer-canthus samples create triangular lid notches; tested variants also introduce body-eye triangle overlaps.",
    ),
    "female-v249-mainline-hairline-layer-isolation-r347.study.json": (
        "DIAGNOSTIC_TRANSITION_CARDS_NEEDED_FLYAWAYS_NOT_CAUSE",
        "Flyaway removal barely changes the defect. Removing transition cards exposes larger gaps, so the remaining fault is in the groom families and their support coverage.",
    ),
    "female-v249-mainline-groom-family-isolation-r348.study.json": (
        "DIAGNOSTIC_REDUNDANT_FRONT_FLOW_SECONDARY_REQUIRED",
        "Primary and secondary families contain redundant forehead-crossing flow. SecondaryFill is still required for the main curtain and cannot be disabled wholesale.",
    ),
    "female-v249-mainline-secondary-forehead-filter-r349.study.json": (
        "REJECT_INSUFFICIENT_FILTER_VOLUME",
        "The world-space filter reaches too few offending curves and leaves the visible forehead lines unchanged.",
    ),
    "female-v249-mainline-secondary-forehead-depth-r350.study.json": (
        "REJECT_DENSITY_LOSS_WITHOUT_FOREHEAD_LINE_REMOVAL",
        "Expanded depth filtering darkens and thins local fill while redundant PrimaryClumps preserve the long forehead lines.",
    ),
    "female-v249-mainline-screen-space-forehead-filter-r352.study.json": (
        "REJECT_RADIUS_SUPPRESSION_OVERRIDDEN_BY_MOTION_GRAPH",
        "Zeroing input radius does not remove the evaluated rendered strands after the existing Geometry Nodes motion graph.",
    ),
    "female-v249-mainline-dual-family-forehead-filter-r353.study.json": (
        "REJECT_RADIUS_SUPPRESSION_INEFFECTIVE_IN_BOTH_FAMILIES",
        "Applying radius suppression to both curve families still leaves the evaluated forehead strands visible.",
    ),
    "female-v249-mainline-dual-family-geometry-prune-r354.study.json": (
        "REJECT_OCCLUDED_REAR_CURVES_REMOVED",
        "True geometry pruning clears the front view but also selects curves hidden behind the head, producing unacceptable rear coverage loss.",
    ),
    "female-v249-mainline-depth-guarded-forehead-prune-r356.study.json": (
        "REJECT_INSUFFICIENT_DEPTH_RANGE",
        "The conservative front-depth guard preserves the back but removes only 23 curves and leaves the forehead artifact.",
    ),
    "female-v249-mainline-extended-depth-forehead-prune-r357.study.json": (
        "REJECT_INCORRECT_VERTICAL_ROI_AND_MINIMAL_GAIN",
        "Extending world depth remains ineffective because the camera-space vertical band is below the actual upper-forehead artifact.",
    ),
    "female-v249-mainline-corrected-forehead-roi-prune-r358.study.json": (
        "REJECT_HAIRLINE_MASS_LOSS_AND_EXPOSED_SCALP_RING",
        "Corrected camera coordinates remove the intended strands, but deletion opens a bright scalp ring and destroys the front hair mass.",
    ),
    "female-v249-mainline-forehead-flow-redirect-r359.study.json": (
        "REJECT_TEMPLE_KINKS_AND_FAN_OUT",
        "Ten millimetres leaves the artifact; twenty to thirty millimetres bends the dense family into visible hooks and lateral fan-out at the temple.",
    ),
}

for name, (status, finding) in updates.items():
    data = read(name)
    data["status"] = status
    data["finding"] = finding
    write(name, data)

r355_name = "female-v249-mainline-forehead-pruned-dual-groom-r355.build-report.json"
r355 = read(r355_name)
r355.update(
    {
        "status": "TECHNICAL_PASS_VISUAL_REJECT_BACK_COVERAGE_LOSS",
        "strictScores": {"face": 45, "hair": 28, "overallCharacter": 38},
        "technicalResults": [
            "Body rig and all 16 head-bound face layers pass.",
            "Hair motion passes at frames 1, 33 and 61 with zero penetrating samples.",
            "Visible authored hair points fall from 262,368 to 170,424.",
        ],
        "visualFailures": [
            "Front camera-space pruning incorrectly removes occluded rear curves and exposes a large bald cap from the back.",
            "Side flow remains uniformly parallel and the cut ends remain needle-like.",
        ],
        "bodyRigAudit": str(ASSETS / "female-v249-mainline-forehead-pruned-dual-groom-r355.body-rig-audit.json"),
        "faceLayerAudit": str(ASSETS / "female-v249-mainline-forehead-pruned-dual-groom-r355.face-layer-audit.json"),
        "hairLayerAudit": str(ASSETS / "female-v249-mainline-forehead-pruned-dual-groom-r355.hair-layer-audit.json"),
        "hairMotionAudit": str(ASSETS / "female-v249-mainline-forehead-pruned-dual-groom-r355.hair-motion-audit.json"),
        "websitePromotionApproved": False,
    }
)
write(r355_name, r355)

write(
    "female-v249-mainline-r346-r359-hair-diagnostics.study.json",
    {
        "range": "r346-r359",
        "sourceCandidate": "aevrynd-female-authoring-v249-mainline-canthus-fitted-wedge-r345.blend",
        "resultCandidate": "aevrynd-female-authoring-v249-mainline-canthus-fitted-wedge-r345.blend",
        "status": "NO_PROMOTION_ALL_LOCAL_GROOM_PATCHES_REJECTED",
        "strictScores": {"face": 45, "hair": 34, "overallCharacter": 41},
        "findings": [
            "r346 rejects narrower outer-eye geometry because of notching and collision.",
            "r347-r350 isolate the forehead fault to redundant primary/secondary guide flow rather than flyaways alone.",
            "r352-r353 prove point-radius suppression is not a reliable deletion mechanism after the motion graph.",
            "r354-r355 prove unoccluded screen selection is unsafe because it removes rear coverage even when collision and motion audits pass.",
            "r356-r358 add depth and corrected camera coordinates; accurate deletion exposes that the existing front hair mass depends on the offending curves.",
            "r359 retains density by lateral redirection, but creates temple hooks and fan-out.",
            "The current dense groom requires replacement with semantically authored part, crown, temple, side and rear guides rather than further local pruning.",
        ],
        "ownedAssetOnly": True,
        "websitePromotionApproved": False,
        "reviewDirectory": str(REVIEW),
    },
)

current_name = "female-v249-mainline-current.json"
current = read(current_name)
current.update(
    {
        "latestHairResearch": "r346-r359 layer isolation, evaluated-geometry pruning, occlusion/depth guards and flow redirection",
        "latestHairResearchStatus": "All local patch variants were rejected. r345 remains the hair technical node; r355 passes motion/collision but fails rear coverage, while r358-r359 expose scalp or create temple hooks.",
    }
)
work = current.get("nextRequiredWork", [])
if len(work) > 1:
    work[1] = "以 r345 為角色基底，重建具語意的分線、頭頂、太陽穴、側面與後腦導引束；各區獨立控制覆蓋、髮束粗細與不齊髮尾，禁止再以相機投影批量刪除或平移密集髮絲。"
write(current_name, current)

copies = {
    TEMP / "v249r346-outer-canthus-width-sweep/b-9p6mm-eyes.png": "r346-rejected-eye-notch.png",
    TEMP / "v249r347-hairline-layer-isolation/c-no-transition-cards-hairline-high.png": "r347-no-transition-cards-gap.png",
    TEMP / "v249r348-groom-family-isolation/c-no-secondary-hairline-high.png": "r348-no-secondary-support-loss.png",
    TEMP / "v249r350-secondary-forehead-depth-sweep/c-front-y-minus-0p12-hairline-high.png": "r350-density-loss-lines-remain.png",
    TEMP / "v249r354-dual-family-geometry-prune-sweep/c-mid-forehead-face.png": "r354-front-prune.png",
    TEMP / "v249r355-forehead-pruned-dual-groom/back-f01.png": "r355-rejected-bald-back.png",
    TEMP / "v249r356-depth-guarded-forehead-prune-sweep/b-front-y-minus-0p10-face.png": "r356-depth-safe-insufficient-front.png",
    TEMP / "v249r356-depth-guarded-forehead-prune-sweep/b-front-y-minus-0p10-back.png": "r356-depth-safe-back-preserved.png",
    TEMP / "v249r358-corrected-forehead-roi-prune-sweep/a-current-face.png": "r358-baseline-front.png",
    TEMP / "v249r358-corrected-forehead-roi-prune-sweep/b-right-lower-face.png": "r358-rejected-exposed-scalp-ring.png",
    TEMP / "v249r358-corrected-forehead-roi-prune-sweep/b-right-lower-back.png": "r358-back-impact.png",
    TEMP / "v249r359-forehead-flow-redirect-sweep/b-redirect-10mm-face.png": "r359-10mm-lines-remain.png",
    TEMP / "v249r359-forehead-flow-redirect-sweep/c-redirect-20mm-face.png": "r359-20mm-temple-hook.png",
    TEMP / "v249r359-forehead-flow-redirect-sweep/c-redirect-20mm-three-quarter.png": "r359-20mm-three-quarter-fan.png",
}
REVIEW.mkdir(parents=True, exist_ok=True)
for source, target in copies.items():
    if not source.exists():
        raise FileNotFoundError(source)
    shutil.copy2(source, REVIEW / target)

print(json.dumps({"status": "PACKAGED_NO_PROMOTION", "review": str(REVIEW), "files": len(copies)}, ensure_ascii=False))
