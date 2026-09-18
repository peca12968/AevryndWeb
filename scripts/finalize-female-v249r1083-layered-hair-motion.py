"""Finalize the collision-qualified r1083 offline hair-motion study."""
import json
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
TEMP = ROOT.parent / "Temp/female-realism/v249r1083-layered-hair-motion-review"
STUDY = ASSETS / "female-v249-mainline-r1083-layered-hair-motion-sweep.study.json"
AUDIT = ASSETS / "female-v249-mainline-r1083-layered-hair-motion.audit.json"
RENDER = ASSETS / "female-v249-mainline-r1083-layered-hair-motion.render.json"
VISUAL = ASSETS / "female-v249-mainline-r1083-layered-hair-motion.visual-audit.json"
CURRENT = ASSETS / "female-v249-mainline-current.json"
REVIEW_DIR = ASSETS / "reviews/v249r1083-layered-hair-motion"
REVIEW = REVIEW_DIR / "contact-sheet-r1083.jpg"
LEDGER = ROOT / "scripts/CHARACTER-REFINEMENT.md"


audit = json.loads(AUDIT.read_text(encoding="utf-8"))
if audit.get("status") != "PASS":
    raise SystemExit("r1083 motion audit must pass before finalization")

frames = (1, 21, 31, 61)
views = ("front", "three-quarter", "back")
tile = (520, 430)
label_height = 40
canvas = Image.new("RGB", (tile[0] * len(views), (tile[1] + label_height) * len(frames)), (22, 22, 22))
draw = ImageDraw.Draw(canvas)
for row, frame in enumerate(frames):
    for column, view in enumerate(views):
        image = Image.open(TEMP / f"selected-f{frame:02d}-{view}.png").convert("RGB")
        image.thumbnail(tile)
        x = column * tile[0] + (tile[0] - image.width) // 2
        y = row * (tile[1] + label_height) + label_height + (tile[1] - image.height) // 2
        canvas.paste(image, (x, y))
        draw.text((column * tile[0] + 8, row * (tile[1] + label_height) + 11), f"frame {frame} | {view}", fill=(240, 240, 240))
REVIEW_DIR.mkdir(parents=True, exist_ok=True)
canvas.save(REVIEW, quality=93, subsampling=0)

peak_frame = str(audit["peakFrame"])
peak = audit["motion"][peak_frame]
minimum_clearance = min(item["minimumSignedClearanceM"] for item in audit["frames"].values())
total_point_tests = sum(item["pointsTested"] for item in audit["frames"].values())
visual = {
    "revision": "v249r1083-layered-hair-motion-visual-audit",
    "review": str(REVIEW),
    "framesReviewed": list(frames),
    "viewsReviewed": list(views),
    "peakFrame": audit["peakFrame"],
    "peakTipP95MotionM": peak["tipP95M"],
    "peakTipMaximumMotionM": peak["tipMaximumM"],
    "rootMaximumDriftM": max(item["rootMaximumM"] for item in audit["motion"].values()),
    "settleMaximumErrorM": audit["motion"]["61"]["allMaximumM"],
    "minimumSignedClearanceM": minimum_clearance,
    "visualFinding": "The side and lower clumps expand and lag by a few millimetres while roots remain fixed and the cycle settles exactly. The response is restrained and coherent, but the inherited long groom still reads as a straight curtain with weak macro-clump separation.",
    "hairMassScoreBefore100": 42,
    "hairMassScoreAfter100": 43,
    "strictFullHeadScoreBefore100": 42,
    "strictFullHeadScoreAfter100": 42,
    "status": "OFFLINE_SECONDARY_MOTION_PASS_VISUAL_PARTIAL_RUNTIME_UNVERIFIED",
}
VISUAL.write_text(json.dumps(visual, indent=2), encoding="utf-8")

study = json.loads(STUDY.read_text(encoding="utf-8"))
study.update({
    "audit": str(AUDIT),
    "renderReview": str(RENDER),
    "visualAudit": str(VISUAL),
    "review": str(REVIEW),
    "hairMassScore100": 43,
    "strictFullHeadScore100": 42,
    "candidateStatus": "OFFLINE_SECONDARY_MOTION_PASS_VISUAL_PARTIAL_RUNTIME_UNVERIFIED",
})
STUDY.write_text(json.dumps(study, indent=2), encoding="utf-8")

current = json.loads(CURRENT.read_text(encoding="utf-8"))
current.update({
    "latestTargetNativeDynamicHairStudy": "aevrynd-female-cc0-layered-hair-motion-r1083-study.blend",
    "latestTargetNativeDynamicHairAudit": "female-v249-mainline-r1083-layered-hair-motion.audit.json; female-v249-mainline-r1083-layered-hair-motion.visual-audit.json",
    "latestTargetNativeDynamicHairReview": "reviews/v249r1083-layered-hair-motion/contact-sheet-r1083.jpg",
    "latestTargetNativeDynamicHairStatus": f"R1083_OFFLINE_SECONDARY_MOTION_PASS_VISUAL_PARTIAL_RUNTIME_UNVERIFIED; root-pinned per-clump phase motion reaches {peak['tipP95M']*1000:.3f}mm tip P95 and {peak['tipMaximumM']*1000:.3f}mm maximum at frame {peak_frame}, with zero root drift and exact frame-61 settle. Nine frames test {total_point_tests:,} hair points with zero penetration; minimum signed body clearance is {minimum_clearance*1000:.3f}mm. Object, curve, point, material-slot and draw-call counts are unchanged; one Blender Geometry Nodes modifier and two point attributes are added. Browser/runtime performance is not yet verified, so website v83 is unchanged.",
    "nextFaceTopologyWork": "Use r1083 only as the offline motion source. Start r1084 by baking the owned motion formula into an engine-readable animation representation in an isolated candidate asset, then benchmark GPU/CPU/frame time and repeat dynamic collision in the browser before any website replacement. Reject the path if it requires Blender at runtime or increases draw calls materially.",
    "latestFullHeadReview": "reviews/v249r1083-layered-hair-motion/contact-sheet-r1083.jpg",
    "latestFullHeadStatus": "R1083_STRICT_FULL_HEAD_42_OF_100_HERO_FAIL; hair mass/response improves 42 to 43 through collision-qualified root-pinned motion, but the straight curtain silhouette and weak macro-clump hierarchy remain. Runtime/browser performance is unverified and website v83 is unchanged.",
})
CURRENT.write_text(json.dumps(current, indent=2), encoding="utf-8")

heading = "### v249r1083 collision-qualified layered hair motion"
entry = f"""

{heading}
- r1083 adds two owned point-domain attributes and one Blender Geometry Nodes modifier to the r1082 groom. Each strand uses a t^2.15 root falloff, per-clump phase and a nonnegative outward-biased 60-frame damping envelope; roots remain fixed and frames 1/61 are rest states.
- The selected 4.5 mm authored bound reaches {peak['tipP95M']*1000:.3f} mm tip P95 and {peak['tipMaximumM']*1000:.3f} mm maximum evaluated motion at frame {peak_frame}. Root drift is exactly 0 and frame-61 settle error is exactly 0.
- Frames 1/11/20/21/31/33/41/51/61 test {total_point_tests:,} point instances with zero penetration. Minimum signed body clearance is {minimum_clearance*1000:.3f} mm at frame 21; object, curve, point and material-slot counts remain unchanged.
- Front, three-quarter and back review at rest, measured peak, mid-cycle and settle shows restrained coherent side/lower movement. Hair mass/response rises 42 to 43/100, while full-head quality remains 42/100 because the inherited groom is still a straight curtain with weak clump hierarchy.
- This is an offline motion source only. Browser animation representation and performance are unverified, so website v83 remains unchanged. r1084 must bake an engine-readable owned motion path and pass runtime timing plus dynamic collision before promotion.
"""
ledger = LEDGER.read_text(encoding="utf-8")
if heading not in ledger:
    LEDGER.write_text(ledger.rstrip() + entry + "\n", encoding="utf-8")

print(json.dumps({"review": str(REVIEW), "peakTipP95M": peak["tipP95M"], "minimumClearanceM": minimum_clearance, "status": "PASS"}, sort_keys=True))
