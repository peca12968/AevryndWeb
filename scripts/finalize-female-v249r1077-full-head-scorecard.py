"""Finalize the strict r1077 full-head visual baseline and defect ranking."""
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
CURRENT = ASSETS / "female-v249-mainline-current.json"
RENDER_REPORT = ASSETS / "female-v249-mainline-r1077-full-head-scorecard.render.json"
SCORE_REPORT = ASSETS / "female-v249-mainline-r1077-full-head-scorecard.json"
OUT = ROOT.parent / "Temp/female-realism/v249r1077-full-head-scorecard"
REVIEW_DIR = ASSETS / "reviews/v249r1077-full-head-scorecard"
REVIEW_DIR.mkdir(parents=True, exist_ok=True)
REVIEW = REVIEW_DIR / "contact-sheet-r1077.jpg"

files = sorted(OUT.glob("*.png"))
sheet = Image.new("RGB", (2020, 1830), (15, 15, 15))
draw = ImageDraw.Draw(sheet)
draw.text((15, 5), "Aevrynd v249r1077 | strict full-head scorecard | overall 39/100", fill=(242, 242, 242))
for index, path in enumerate(files):
    image = Image.open(path).convert("RGB")
    image.thumbnail((390, 560), Image.Resampling.LANCZOS)
    x, y = 15 + (index % 5) * 400, 25 + (index // 5) * 600
    sheet.paste(image, (x, y))
    draw.rectangle((x, y, x + 385, y + 24), fill=(10, 10, 10))
    draw.text((x + 5, y + 5), path.stem, fill=(240, 240, 240))
sheet.save(REVIEW, quality=94, subsampling=0)

render_report = json.loads(RENDER_REPORT.read_text(encoding="utf-8"))
rubric = [
    {"category": "cranial silhouette and facial planes", "weightPercent": 10, "score100": 42, "evidence": "The cranial vault is long and uniformly smooth; temple, zygomatic and mandibular plane changes remain weak in front, three-quarter and profile views."},
    {"category": "eyes and eyelids", "weightPercent": 20, "score100": 34, "evidence": "The aperture exposes large triangular sclera wedges, lid margins lack physical thickness, lateral canthi read as holes and the gaze remains rigid under front and oblique inspection."},
    {"category": "brows and lashes", "weightPercent": 5, "score100": 46, "evidence": "Lash density is technically present but the fan reads uniformly combed; pale sparse brows provide little anatomical framing."},
    {"category": "nose and midface", "weightPercent": 15, "score100": 40, "evidence": "Bridge-to-tip transition is generic; alar cartilage, nostril sill, nasolabial transition and cheek support remain under-defined across low, high and three-quarter views."},
    {"category": "mouth and perioral anatomy", "weightPercent": 15, "score100": 45, "evidence": "r1076 fixes the commissure normal spike, but vermilion volume, inner cavity depth, philtral columns and expressive compression remain shallow."},
    {"category": "skin response and regional detail", "weightPercent": 15, "score100": 36, "evidence": "Broad highlights and near-uniform color make the face read as smooth synthetic material; pores, roughness zones and regional color variation do not survive full-head distance."},
    {"category": "hairline and scalp transition", "weightPercent": 8, "score100": 32, "evidence": "The center part exposes a wide bright scalp strip, the frontal boundary is hard and wig-like, and temple transitions lack short graded fibers."},
    {"category": "hair mass, clumps and ends", "weightPercent": 12, "score100": 42, "evidence": "The 72,800-point owned groom forms a straight uniform curtain with weak macro-clump hierarchy, limited silhouette breakup and repetitive lower ends."},
]
weighted = sum(item["weightPercent"] * item["score100"] for item in rubric) / 100.0
report = {
    "revision": "v249r1077-full-head-scorecard",
    "source": render_report["source"], "renderReport": str(RENDER_REPORT), "review": str(REVIEW),
    "standard": "strict modern real-time hero-character presentation, scored as a complete head rather than averaging prior local technical scores",
    "rubric": rubric, "weightedScore100": weighted, "reportedStrictScore100": round(weighted),
    "rankedBlockers": [
        "eyes and eyelids: aperture, sclera wedges, lid thickness and canthus closure",
        "hairline and scalp transition: wide bright part and hard frontal boundary",
        "skin response: uniform color/roughness and broad synthetic highlight",
        "nose/midface planes: weak alar, cheek and nasolabial structure",
        "hair mass: straight curtain, weak clump hierarchy and repetitive ends",
        "mouth/perioral: shallow vermilion, cavity and expression compression",
    ],
    "selectedNextSubsystem": "EYES_AND_EYELIDS",
    "nextWork": "Build r1078 from r1076. Measure the current visible aperture against the existing 7.834 mm balanced anatomical guide; reshape upper/lower margin depth and lid thickness within collision clearances, then refit lash roots only if required. Reject any variant that reintroduces sclera/cornea/lash overlap or dark canthus holes.",
    "modelModified": False,
    "collisionStatus": "INHERITED_R1076_PASS_NO_MODEL_CHANGE",
    "performanceStatus": "INHERITED_R1076_PASS_NO_MODEL_CHANGE",
    "websitePromotionApproved": False,
    "status": "STRICT_BASELINE_ESTABLISHED_VISUAL_HERO_FAIL",
}
SCORE_REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")

current = json.loads(CURRENT.read_text(encoding="utf-8"))
current["latestFullHeadScorecard"] = "female-v249-mainline-r1077-full-head-scorecard.json"
current["latestFullHeadReview"] = "reviews/v249r1077-full-head-scorecard/contact-sheet-r1077.jpg"
current["latestFullHeadStatus"] = "R1077_STRICT_FULL_HEAD_BASELINE_39_OF_100_HERO_FAIL; eyes/lids 34, hairline 32, skin 36, nose/midface 40, cranial/facial planes 42, hair mass 42, mouth 45, brows/lashes 46. The eye aperture and lid/eye integration are the largest visible blocker. No model or website promotion occurred."
current["nextFaceTopologyWork"] = report["nextWork"]
CURRENT.write_text(json.dumps(current, indent=2), encoding="utf-8")

refinement_path = ROOT / "scripts/CHARACTER-REFINEMENT.md"
entry = "### v249r1077 strict full-head scorecard\n- Reframed the current r1076 face and owned r981 static groom in 15 calibrated views: front, bilateral three-quarter/profile, high/low, eye close-ups, hair front/back/top. The complete head scores 39/100 under a modern real-time hero-character rubric; prior local subsystem scores are not treated as overall quality.\n- Eyes/lids are the largest blocker at 34/100: oversized exposed aperture, triangular sclera wedges, weak lid thickness and canthus holes. Hairline 32 and skin response 36 follow. r1078 will address eyelid/eye integration first. No geometry, collision state, performance state or website asset changed.\n"
refinement = refinement_path.read_text(encoding="utf-8")
if entry not in refinement:
    refinement_path.write_text(refinement.rstrip() + "\n\n" + entry, encoding="utf-8")

print(json.dumps({"review": str(REVIEW), "overallScore": report["reportedStrictScore100"], "largestBlocker": report["selectedNextSubsystem"], "status": report["status"]}, indent=2))
