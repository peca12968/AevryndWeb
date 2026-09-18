"""Package the exact-edge support topology and collision review."""
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
CURRENT = ASSETS / "female-v249-mainline-current.json"
STUDY = ASSETS / "female-v249-mainline-r1068-exact-edge-support.study.json"
AUDIT = ASSETS / "female-v249-mainline-r1068-exact-edge-support.collision-audit.json"
R1061 = ROOT.parent / "Temp/female-realism/v249r1061-lip-form-expression"
R1068 = ROOT.parent / "Temp/female-realism/v249r1068-exact-edge-support"
REVIEW_DIR = ASSETS / "reviews/v249r1068-exact-edge-support"
REVIEW_DIR.mkdir(parents=True, exist_ok=True)
panels = (
    (R1061 / "c-anatomical-neutral-front.png", "r1061 neutral"),
    (R1061 / "c-anatomical-neutral-oblique.png", "r1061 oblique"),
    (R1061 / "selected-open-1.00.png", "r1061 open"),
    (R1061 / "selected-smile-1.00.png", "r1061 smile"),
    (R1068 / "neutral-front.png", "r1068 neutral"),
    (R1068 / "neutral-oblique.png", "r1068 oblique"),
    (R1068 / "mouth-open.png", "r1068 open"),
    (R1068 / "smile.png", "r1068 smile"),
)
sheet = Image.new("RGB", (1840, 960), (18, 18, 18))
draw = ImageDraw.Draw(sheet)
draw.text((20, 14), "Aevrynd v249r1068 | exact 76-edge support | COLLISION PASS / VISUAL PARTIAL", fill=(242, 242, 242))
for index, (path, label) in enumerate(panels):
    image = Image.open(path).convert("RGB")
    image.thumbnail((445, 420), Image.Resampling.LANCZOS)
    x, y = 20 + (index % 4) * 455, 48 + (index // 4) * 450
    sheet.paste(image, (x, y))
    draw.rectangle((x + 5, y + 5, x + 155, y + 30), fill=(18, 18, 18))
    draw.text((x + 10, y + 10), label, fill=(245, 245, 245))
review = REVIEW_DIR / "contact-sheet-r1068.jpg"
sheet.save(review, quality=94, subsampling=0)

study = json.loads(STUDY.read_text(encoding="utf-8"))
audit = json.loads(AUDIT.read_text(encoding="utf-8"))
study.update({
    "strictMouthScore100": 39,
    "collisionAudit": str(AUDIT),
    "collisionStatus": audit["status"],
    "review": str(review),
    "topologyDeltaVersusR1061": {"vertices": 234, "faces": 234, "vertexPercent": 1.7227416623711993},
    "finding": "Exact-edge baked support avoids the broad group-bevel humps and thins the neutral bright rim. All 35 shape keys and normalized weights transfer with 0.0218 mm maximum mapping distance; four rig frames, mouth-open, smile and 14 face attachments pass zero-overlap gates. Oblique and open views still expose a grey-white inner strip.",
    "candidateStatus": "TECHNICAL_TOPOLOGY_AND_COLLISION_PASS_VISUAL_PARTIAL",
    "websitePromotionApproved": False,
})
STUDY.write_text(json.dumps(study, indent=2), encoding="utf-8")
current = json.loads(CURRENT.read_text(encoding="utf-8"))
current["latestMouthTopologyResearch"] += "; female-v249-mainline-r1068-exact-edge-support.study.json; female-v249-mainline-r1068-exact-edge-support.collision-audit.json; reviews/v249r1068-exact-edge-support/contact-sheet-r1068.jpg"
current["latestMouthTopologyStatus"] = "R1068_TECHNICAL_TOPOLOGY_AND_COLLISION_PASS_VISUAL_PARTIAL; exact 76-edge 0.05mm two-segment support adds 234 vertices/faces (1.723%), preserves 35 keys and normalized weights, and passes four rig frames plus open/smile with zero body or face-attachment overlap. Strict score 39/100: neutral rim is thinner, but oblique/open views retain a grey-white strip."
current["latestMouthTopologyTransferStudy"] = "aevrynd-female-cc0-exact-edge-support-r1068-study.blend"
current["latestMouthTopologyCollisionAudit"] = "female-v249-mainline-r1068-exact-edge-support.collision-audit.json"
current["latestMouthReview"] = "reviews/v249r1068-exact-edge-support/contact-sheet-r1068.jpg"
current["nextFaceTopologyWork"] = "Use r1068 as the support-topology source for r1069. Rebuild only the visible lower inner strip between the new support rows as an inward-facing vestibule transition, preserve the exact 76-edge selection and transfer contract, then rerun oblique/open collision and normal continuity gates."
CURRENT.write_text(json.dumps(current, indent=2), encoding="utf-8")
print(json.dumps({"review": str(review), "collision": audit["status"], "score": study["strictMouthScore100"], "status": study["candidateStatus"]}, indent=2))
