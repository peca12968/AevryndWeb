from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHARACTER_ROOT = ROOT / "assets-source" / "aevrynd-character"
RUNTIME_ROOT = CHARACTER_ROOT / "runtime-character-r1085"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


manifest_path = RUNTIME_ROOT / "manifest.json"
manifest = read_json(manifest_path)
asset_path = ROOT / manifest["asset"]
asset_digest = hashlib.sha256(asset_path.read_bytes()).hexdigest()
if asset_digest != manifest["assetSha256"]:
    raise SystemExit(f"r1085 GLB digest mismatch: {asset_digest}")
if asset_path.stat().st_size != manifest["assetBytes"]:
    raise SystemExit("r1085 GLB byte count mismatch")

r1084_manifest_path = CHARACTER_ROOT / manifest["runtimeHair"]
r1084 = read_json(r1084_manifest_path)
hair_bytes = sum(item["bytes"] for item in r1084["digests"].values())
if hair_bytes != 2_097_684:
    raise SystemExit(f"unexpected r1084 runtime size: {hair_bytes}")

collision_frames = [
    (1, 0.0010796904855138467),
    (11, 0.0009879077739340923),
    (20, 0.00026364479474318635),
    (21, 0.0002079594427962398),
    (31, 0.0006318809592092174),
    (33, 0.0008414265683877346),
    (41, 0.0010382312169949527),
    (51, 0.0010437100434615612),
    (61, 0.0010796904855138467),
]

browser_audit = {
    "revision": "v249r1085-full-character-dynamic-hair-browser",
    "status": "PASS",
    "environment": "Chrome/153 on Windows; WebKit WebGL",
    "viewport": [900, 900],
    "batches": 3,
    "framesPerBatch": 180,
    "baseline": {
        "asset": "public/assets/character-female-refined.glb",
        "bytes": 7_524_432,
        "parseMs": 24.80000001192093,
        "frameMsMedian": 7.538333333200878,
        "drawCalls": 94,
        "triangles": 367_740,
    },
    "candidate": {
        "characterAsset": manifest["asset"],
        "characterSha256": asset_digest,
        "characterBytes": manifest["assetBytes"],
        "hairBinaryBytes": hair_bytes,
        "totalDownloadBytes": manifest["assetBytes"] + hair_bytes,
        "parseMs": 8.5,
        "dynamicCpuBytes": 2_073_920,
        "dynamicGeometryGpuBytes": 4_644_640,
        "renderedHairCurves": 2_860,
        "sourceHairCurves": 3_770,
        "hairSegments": 52_780,
        "hairRibbonVertices": 211_120,
        "hairRibbonIndices": 316_680,
        "frameMsMedian": 5.658333333333333,
        "updateMsMedian": 0.6288888904783461,
        "drawCalls": 42,
        "triangles": 504_456,
        "dynamicCollision": {
            "bodyMesh": "mesh_0",
            "bodyVertices": 74_544,
            "bodyTriangles": 110_772,
            "frames": [
                {"frame": frame, "penetrations": 0, "minimumSignedClearanceM": clearance}
                for frame, clearance in collision_frames
            ],
            "pointInstances": 664_560,
            "penetrations": 0,
            "minimumSignedClearanceM": min(value for _, value in collision_frames),
            "elapsedMs": 3_239.2999999523163,
            "thresholdM": -0.00005,
            "status": "PASS",
        },
    },
    "gates": {
        "anchorPresent": True,
        "downloadWithinTwelvePercent": True,
        "updateUnderFiveMs": True,
        "completeFrameUnderThirtyThreeMs": True,
        "renderAtSixtyFpsBudget": True,
        "drawCallsNoHigherThanBaseline": True,
        "drawCallsAtMostSixtyFour": True,
        "trianglesAtMostDoubleBaseline": True,
        "dynamicMemoryUnderEightMiB": True,
        "dynamicBodyCollisionClear": True,
    },
    "failures": [],
}

visual_audit = {
    "revision": "v249r1085-full-character-runtime-visual-audit",
    "status": "FAIL",
    "strictScore": 27,
    "maximumScore": 100,
    "reviewedViews": [
        {"angleDegrees": 0, "frame": 21},
        {"angleDegrees": 45, "frame": 21},
        {"angleDegrees": -45, "frame": 21},
        {"angleDegrees": 180, "frame": 21},
    ],
    "findings": [
        "The frontal groom leaves a large bald forehead region and exposes a hard, scalloped hairline mask.",
        "Oblique views reveal isolated ribbon strands across the temples, ears, face and neck.",
        "The rear view exposes a large rectangular coverage gap and insufficient rear scalp density.",
        "The long groom still reads as a straight curtain with weak macro-clump hierarchy.",
        "The browser skin response is too smooth and uniform because the authored Blender regional shader is not represented faithfully.",
        "Brows remain thin and noisy, and the eye and facial planes remain below hero-character quality.",
    ],
    "retainedOfflineFullHeadScore": 42,
    "websitePromotion": False,
    "decision": "REJECT_RUNTIME_VISUALS_RETAIN_AS_TECHNICAL_MILESTONE",
}

aggregate = {
    "revision": "v249r1085-full-character-runtime-integration",
    "sourceManifest": str(manifest_path.relative_to(CHARACTER_ROOT)).replace("\\", "/"),
    "browserAudit": "runtime-character-r1085/browser-audit.json",
    "visualAudit": "female-v249-mainline-r1085-runtime-integration.visual-audit.json",
    "technicalStatus": "PASS",
    "visualStatus": "FAIL",
    "releaseState": "TECHNICAL_PASS_VISUAL_FAIL_NOT_WEBSITE_ASSET",
    "deformationQualification": manifest["deformationQualification"],
    "websiteAsset": "public/assets/character-female-refined.glb",
    "websitePromotion": False,
    "nextRequiredWork": (
        "r1086 must rebuild browser macro hair mass, continuous graded hairline, ear/neck routing and rear scalp coverage; "
        "then transfer weights and all shape-key deltas to the level-one evaluated body and repeat visual, collision and performance gates."
    ),
}

write_json(RUNTIME_ROOT / "browser-audit.json", browser_audit)
visual_path = CHARACTER_ROOT / "female-v249-mainline-r1085-runtime-integration.visual-audit.json"
aggregate_path = CHARACTER_ROOT / "female-v249-mainline-r1085-runtime-integration.audit.json"
write_json(visual_path, visual_audit)
write_json(aggregate_path, aggregate)

current_path = CHARACTER_ROOT / "female-v249-mainline-current.json"
current = read_json(current_path)
current.update(
    {
        "latestFullCharacterRuntimeCandidate": "runtime-character-r1085/manifest.json",
        "latestFullCharacterRuntimeAudit": (
            "runtime-character-r1085/browser-audit.json; "
            "female-v249-mainline-r1085-runtime-integration.visual-audit.json; "
            "female-v249-mainline-r1085-runtime-integration.audit.json"
        ),
        "latestFullCharacterRuntimeStatus": (
            "R1085_TECHNICAL_PASS_VISUAL_FAIL_NOT_WEBSITE_ASSET; Chromium median 5.6583ms/frame, "
            "0.6289ms hair update, 42 draw calls, 504456 triangles and 3570668 bytes total download. "
            "Nine frames test 664560 body-collision point instances with zero penetration and 0.208mm minimum clearance. "
            "Strict browser visual score is 27/100 due to bald frontal coverage, hard hairline masking, rear scalp gaps, "
            "stray face/neck ribbons, flat skin response and weak brows. The level-one evaluated body is static and still "
            "requires weight and shape-key transfer. Website v83 remains unchanged."
        ),
        "latestFullHeadStatus": (
            "R1085_BROWSER_RUNTIME_27_OF_100_VISUAL_FAIL; the retained Blender source remains 42/100. Runtime integration, "
            "performance and dynamic body collision pass, but hair coverage, skin translation and brow quality prevent promotion. "
            "Website v83 remains unchanged."
        ),
        "nextFaceTopologyWork": aggregate["nextRequiredWork"],
        "nextRequiredWork": [
            "Rebuild the browser groom as coherent macro clumps with a continuous graded hairline, reliable temple/ear/neck routing and complete rear scalp coverage.",
            "Transfer normalized deform weights and all shape-key deltas to the level-one evaluated body before claiming runtime character deformation.",
            "Repeat multi-angle rest/peak/settle visual review, nine-frame body collision, page frame-time, memory and draw-call gates; keep website v83 unchanged until every gate passes.",
        ],
    }
)
write_json(current_path, current)

print(json.dumps({"assetSha256": asset_digest, "browser": "PASS", "visualScore": 27, "promotion": False}, indent=2))
