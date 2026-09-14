import json
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
MODEL = ASSETS / "aevrynd-female-authoring-v249-mainline-orbital-brow-refit-r526.blend"
VISUAL = ASSETS / "female-v249-mainline-orbital-brow-refit-r526.visual-review.json"
RUNTIME = ASSETS / "runtime-character-r526"

browser = {
    "environment": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/152.0.0.0 Safari/537.36",
    "method": "one shared WebGL renderer; alternating five baseline/candidate batches; 300 frames per batch at 900x900; gl.finish synchronization",
    "viewport": [900, 900],
    "batches": 5,
    "framesPerBatch": 300,
    "baseline": {
        "revision": "r522",
        "bytes": 16222608,
        "parseMsMedian": 27.400000005960464,
        "renderMsMedian": 0.415,
        "parseSamplesMs": [43.400000005960464, 27.400000005960464, 18.69999998807907, 24.299999982118607, 31.599999994039536],
        "renderSamplesMs": [0.46100000003973646, 0.405, 0.425, 0.4073333332935969, 0.415],
        "drawCalls": 70,
        "triangles": 391126,
    },
    "candidate": {
        "revision": "r526",
        "bytes": 16214800,
        "parseMsMedian": 23.099999994039536,
        "renderMsMedian": 0.4096666666865349,
        "parseSamplesMs": [24.400000005960464, 36.599999994039536, 21.900000005960464, 23.099999994039536, 19.30000001192093],
        "renderSamplesMs": [0.4153333333134651, 0.417333333392938, 0.4039999999602636, 0.4096666666865349, 0.4040000000596046],
        "drawCalls": 70,
        "triangles": 390278,
    },
}
browser["delta"] = {
    "bytes": browser["candidate"]["bytes"] - browser["baseline"]["bytes"],
    "parseMsMedian": browser["candidate"]["parseMsMedian"] - browser["baseline"]["parseMsMedian"],
    "renderMsMedian": browser["candidate"]["renderMsMedian"] - browser["baseline"]["renderMsMedian"],
    "drawCalls": browser["candidate"]["drawCalls"] - browser["baseline"]["drawCalls"],
    "triangles": browser["candidate"]["triangles"] - browser["baseline"]["triangles"],
}
browser["gates"] = {
    "noDownloadRegression": True,
    "noDrawCallRegression": True,
    "noTriangleRegression": True,
    "renderWithinFifteenPercent": True,
    "parseWithinFifteenPercent": True,
}
browser["status"] = "PASS"
(RUNTIME / "browser-performance-audit.json").write_text(json.dumps(browser, indent=2), encoding="utf-8")

bpy.ops.wm.open_mainfile(filepath=str(MODEL))
scene = bpy.context.scene
scene["aevrynd_release_state"] = "OFFLINE_TECHNICAL_MAINLINE_ALL_GATES_PASS_VISUAL_HERO_FAIL"
scene["aevrynd_strict_hair_score"] = 47
scene["aevrynd_strict_eye_score"] = 70
scene["aevrynd_strict_face_score"] = 59
scene["aevrynd_strict_skin_score"] = 57
scene["aevrynd_strict_mouth_score"] = 55
scene["aevrynd_strict_body_clothing_score"] = 49
scene["aevrynd_strict_overall_score"] = 58
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(MODEL))

review = {
    "revision": "v249r526",
    "status": "OFFLINE_TECHNICAL_MAINLINE_VISUAL_HERO_FAIL",
    "strictScores": {"hair": 47, "eyes": 70, "face": 59, "skin": 57, "mouth": 55, "bodyAndClothing": 49, "overall": 58},
    "improvements": [
        "adds restrained upper/lower eyelid roll and orbital transition to the continuous body across all six shape keys",
        "removes only dynamically hidden cornea/sclera faces while retaining every iris face and visible optical surface",
        "refits 237 eyebrow control points to the new face with at least 0.127 mm measured root clearance",
        "keeps fixed skin regions 0.00005 to 0.106 percent brighter than r522 instead of continuing the darkening trend",
    ],
    "passedGates": [
        "body self-intersection and all eye/mouth layers at frames 1/20/33/61",
        "eyebrow/body collision at frames 1/20/33/61",
        "runtime hair/body/clothing collision and motion envelope",
        "11-shot visual review and fixed tone contract",
        "structural performance and actual Chrome WebGL benchmark",
    ],
    "remainingFailures": [
        "eyelid margin, canthus shape, tear-duct wetness and iris response remain visibly synthetic",
        "skin lacks regional pores, blood flow, oil and dryness breakup",
        "hair still reads as a symmetric planar curtain with weak macro/medium/fine hierarchy",
        "body, clothing and deformation remain below hero quality",
    ],
    "websitePromotionApproved": False,
    "websiteAsset": "v83 unchanged",
}
VISUAL.write_text(json.dumps(review, indent=2), encoding="utf-8")

manifest_path = ASSETS / "female-v249-mainline-current.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["latestCharacterTechnicalCandidate"] = MODEL.name
manifest["latestCharacterCandidateStatus"] = (
    "R526_OFFLINE_TECHNICAL_MAINLINE; orbital relief is made collision-safe by pruning 165 dynamically hidden cornea/sclera faces and refitting 237 brow controls. "
    "Four-frame face, brow, hair/clothing, tone, 11-shot, structural and actual browser WebGL gates pass. Strict overall score is 58/100; website v83 remains unchanged."
)
manifest["latestEyeTechnicalCandidate"] = MODEL.name
manifest["latestEyeCandidateStatus"] = "R526_PASS; complete irises retained, visible cornea/sclera intact, zero body/eye overlap frames 1/20/33/61, strict eye score 70/100."
manifest["latestFaceTechnicalCandidate"] = MODEL.name
manifest["latestFaceCandidateStatus"] = "R526_OFFLINE_TECHNICAL_PASS_VISUAL_HERO_FAIL_SCORE_59; orbital and eyelid volume improves modestly while all collision, tone and browser gates pass."
manifest["latestFaceResearchStatus"] = (
    "r526 is the current offline technical face candidate at 59/100. It resolves the r524 eye-envelope dead end by pruning only hidden optical faces and refitting brows, "
    "but eyelid margins, canthi, tear response, skin microdetail and hair hierarchy remain below hero quality."
)
manifest["latestEyelidCollisionAudit"] = "female-v249-mainline-orbital-brow-refit-r526.audit.json"
manifest["latestEyelidStatus"] = "R526_PASS_SIGNED_ORBITAL_RELIEF_HIDDEN_OPTICAL_FACE_PRUNE_COMPLETE_IRISES_ZERO_FACE_LAYER_OVERLAP_FRAMES_1_20_33_61"
manifest["latestSkinToneAudit"] = "female-v249-mainline-orbital-brow-refit-r526.tone-contract-audit.json"
manifest["latestSkinToneStatus"] = "PASS_R510_LIGHTER_NEUTRAL_SKIN_RETAINED; r526 fixed regions are 0.00005%-0.106% brighter than r522."
manifest["latestBrowTechnicalCandidate"] = MODEL.name
manifest["latestBrowCollisionAudit"] = "female-v249-mainline-orbital-brow-refit-r526.brow-collision-audit.json"
manifest["latestBrowStatus"] = "R526_PASS_237_CONTROLS_REFIT_MAX_0P252MM_ZERO_BODY_OVERLAP_FRAMES_1_20_33_61_MIN_ROOT_CLEARANCE_0P127MM"
manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
print("AEVRYND_R526_FINAL=" + json.dumps(review, sort_keys=True))
