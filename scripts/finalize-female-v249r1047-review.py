"""Finalize the strict r1047 boundary isolation and turn rejection."""

import json
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "v249r1047-inner-boundary-turn-sweep"
ISOLATION_RENDER = ROOT.parent / "Temp" / "female-realism" / "v249r1047-boundary-face-isolation" / "boundary-groups.png"
REVIEW_DIR = ASSETS / "reviews" / "v249r1047-inner-boundary"
STUDY = ASSETS / "female-v249-mainline-r1047-inner-boundary-turn-sweep.study.json"
CURRENT = ASSETS / "female-v249-mainline-current.json"

REVIEW_DIR.mkdir(parents=True, exist_ok=True)
items = (
    ("face groups: red front / green mid / blue rear", ISOLATION_RENDER),
    ("r1046 source", RENDER_DIR / "source-r1046-neutral.png"),
    ("2.5 mm inward turn", RENDER_DIR / "a-2p5mm-neutral.png"),
    ("6 mm inward turn", RENDER_DIR / "c-6mm-neutral.png"),
)
sheet = Image.new("RGB", (1600, 980), (22, 22, 22))
draw = ImageDraw.Draw(sheet)
draw.text((20, 14), "Aevrynd v249r1047 inner-boundary turn | STRICT VISUAL REJECT 29/100", fill=(238, 238, 238))
for index, (label, path) in enumerate(items):
    image = Image.open(path).convert("RGB")
    image.thumbnail((800, 430), Image.Resampling.LANCZOS)
    x = (index % 2) * 800
    y = 60 + (index // 2) * 460
    sheet.paste(image, (x, y + 28))
    draw.text((x + 12, y + 5), label, fill=(238, 238, 238))
review = REVIEW_DIR / "contact-sheet-r1047.jpg"
sheet.save(review, quality=94, subsampling=0)

study = json.loads(STUDY.read_text(encoding="utf-8"))
study.update({
    "strictMouthScore100": 29,
    "retainedR1033Score100": 39,
    "visualFinding": "The 2.5mm bound shortens the pale strips but reveals deeper pink fragments. The 4-6mm bounds create a central bump and new creases because the eight faces share vertices with incompatible folded surfaces.",
    "collisionGate": "NOT_RUN_AFTER_DECISIVE_VISUAL_REJECT",
    "candidateBlendSaved": False,
    "websitePromotionApproved": False,
    "review": str(review),
    "status": "VISUAL_REJECT_DELETE_AND_REBUILD_REQUIRED",
})
STUDY.write_text(json.dumps(study, indent=2), encoding="utf-8")

current = json.loads(CURRENT.read_text(encoding="utf-8"))
current["latestMouthRejectedExperiment"] += "; r1047 15-face color isolation and eight-face topology-weighted inward-turn sweep"
current["latestMouthRejectedReason"] = "r1047 proves the bilateral pale strips come from eight first-visible mid-depth skin faces, distinct from four lower-lip front faces and two large side-shell faces. A 2.5mm weighted inward turn reveals deeper pink fragments; 4-6mm creates a central bump and creases. Visual score 29/100 triggers rejection before full collision promotion."
current["latestMouthTopologyResearch"] += "; female-v249-mainline-r1047-boundary-face-isolation.inspect.json; female-v249-mainline-r1047-inner-boundary-turn-sweep.study.json; reviews/v249r1047-inner-boundary/contact-sheet-r1047.jpg"
current["latestMouthTopologyStatus"] = "R1047_BOUNDARY_FACE_ISOLATION_COMPLETE_VISUAL_REJECT_SCORE_29; eight pale-strip faces are identified exactly, but deformation exposes deeper fragments and creates central folds. r1046 remains a rear-cavity technical study; r1033 stays retained."
current["nextFaceTopologyWork"] = "Delete the eight proven pale-strip faces together with only their incompatible folded interior neighbors, extract the resulting boundary loops, and bridge them with a newly sampled welded upper/lower inner-lip patch. Preserve the four red lower-lip front faces, explicit commissures, all 35 shape keys and deform weights; add jaw-coupled separation before collision review."
CURRENT.write_text(json.dumps(current, indent=2), encoding="utf-8")
print(json.dumps({"review": str(review), "status": study["status"], "strictScore": study["strictMouthScore100"]}, indent=2))
