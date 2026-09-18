from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHARACTER_ROOT = ROOT / "assets-source" / "aevrynd-character"
RUNTIME_ROOT = CHARACTER_ROOT / "runtime-character-r1086"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


manifest = {
    "format": "aevrynd-full-character-runtime-presentation-v1",
    "revision": "v249r1086-full-density-double-sided-hair",
    "characterAsset": "public/assets/character-r1085/character-r1085.glb",
    "hairMotionManifest": "runtime-hair-motion-r1084/manifest.json",
    "renderer": "src/hair-strand-renderer-r1086.js",
    "benchmark": "public/benchmarks/r1086-full-character-hair.html",
    "representation": {
        "sourceCurves": 3770,
        "renderedCurves": 3770,
        "segments": 70070,
        "ribbonVertices": 280280,
        "ribbonIndices": 420420,
        "sidedness": "DOUBLE",
        "faceAndNeckMask": "SOFT_DEPTH_AWARE",
        "shortHairlineWidthScale": 1.72,
    },
    "ownership": "Aevrynd-authored runtime code and Aevrynd-owned/CC0-traceable geometry; no MetaHuman or Unreal dependency",
    "releaseState": "TECHNICAL_PASS_VISUAL_FAIL_NOT_WEBSITE_ASSET",
}

browser_audit = {
    "revision": "v249r1086-full-density-double-sided-hair-browser",
    "status": "PASS",
    "environment": "Chrome/153 on Windows; WebKit WebGL",
    "viewport": [900, 900],
    "batches": 3,
    "framesPerBatch": 180,
    "frontFrame21": {
        "frameMsMedian": 7.71777777771155,
        "updateMsMedian": 0.5955555571450127,
        "drawCalls": 42,
        "triangles": 573616,
    },
    "backFrame21": {
        "frameMsMedian": 10.122222222222222,
        "updateMsMedian": 0.6983333342605167,
        "drawCalls": 42,
        "triangles": 573616,
    },
    "download": {
        "characterBytes": 1472984,
        "hairBinaryBytes": 2097684,
        "totalBytes": 3570668,
    },
    "dynamicMemory": {
        "cpuBytes": 2073920,
        "geometryGpuBytes": 6166160,
        "totalBytes": 8240080,
        "gateBytes": 8388608,
        "remainingMarginBytes": 148528,
    },
    "collision": {
        "frames": [1, 11, 20, 21, 31, 33, 41, 51, 61],
        "pointInstances": 664560,
        "penetrations": 0,
        "minimumSignedClearanceM": 0.0002079594427962398,
        "status": "PASS",
    },
    "gates": {
        "completeFrameUnderThirtyThreeMs": True,
        "renderAtSixtyFpsBudgetAllReviewedAngles": True,
        "updateUnderFiveMs": True,
        "drawCallsNoHigherThanBaseline": True,
        "drawCallsAtMostSixtyFour": True,
        "trianglesAtMostDoubleBaseline": True,
        "dynamicMemoryUnderEightMiB": True,
        "dynamicBodyCollisionClear": True,
    },
}

visual_audit = {
    "revision": "v249r1086-full-density-double-sided-hair-visual-audit",
    "status": "FAIL",
    "strictScore": 28,
    "maximumScore": 100,
    "reviewedViews": [
        {"angleDegrees": 0, "frame": 21},
        {"angleDegrees": 180, "frame": 21},
    ],
    "improvementsOverR1085": [
        "All 3770 authored curves render instead of 2860, restoring 910 previously dropped curves.",
        "Double-sided ribbons remove view-dependent triangle culling as a possible cause of rear dropout.",
        "The depth-aware soft mask removes the hard z=1.455 fragment cutoff used by r1085.",
    ],
    "blockingFindings": [
        "The frontal hairline remains excessively high, sparse and scalloped, leaving a bald upper forehead.",
        "The rear view still exposes a very large occipital and nape gap after full-density double-sided rendering.",
        "Temple, ear and neck strands remain visibly isolated instead of forming coherent locks.",
        "The long hair mass still reads as a uniform straight curtain without large and medium clump hierarchy.",
        "Skin and brow presentation remain too flat and noisy for a hero character.",
    ],
    "rejectedExperiments": [
        "Unmasked full-density ribbons: exposes too many face and neck crossings.",
        "r517 card-groom transplant: historical scalp shape does not conform to the current head after scale and landmark alignment.",
        "Body-derived density overlay: reads as a painted cap rather than hair.",
        "Body-projected short fibers: reads as a jagged fringe and cannot replace authored guide flow.",
    ],
    "rootCause": "SOURCE_GROOM_COVERAGE_TOPOLOGY_INSUFFICIENT",
    "websitePromotion": False,
}

aggregate = {
    "revision": "v249r1086-full-density-double-sided-hair",
    "manifest": "runtime-character-r1086/manifest.json",
    "browserAudit": "runtime-character-r1086/browser-audit.json",
    "visualAudit": "female-v249-mainline-r1086-full-density-double-sided-hair.visual-audit.json",
    "technicalStatus": "PASS",
    "visualStatus": "FAIL",
    "releaseState": "TECHNICAL_PASS_VISUAL_FAIL_NOT_WEBSITE_ASSET",
    "websitePromotion": False,
    "nextRequiredWork": (
        "r1087 must rebuild the Blender source groom with explicit frontal hairline, occipital coverage and nape guide rows, "
        "plus asymmetric large/medium clumps. Export a new owned runtime package and repeat front, bilateral oblique, profile, "
        "rear, top, motion, collision, memory, draw-call and frame-time gates."
    ),
}

write_json(RUNTIME_ROOT / "manifest.json", manifest)
write_json(RUNTIME_ROOT / "browser-audit.json", browser_audit)
write_json(CHARACTER_ROOT / "female-v249-mainline-r1086-full-density-double-sided-hair.visual-audit.json", visual_audit)
write_json(CHARACTER_ROOT / "female-v249-mainline-r1086-full-density-double-sided-hair.audit.json", aggregate)

current_path = CHARACTER_ROOT / "female-v249-mainline-current.json"
current = read_json(current_path)
current.update(
    {
        "latestFullCharacterRuntimeCandidate": "runtime-character-r1086/manifest.json",
        "latestFullCharacterRuntimeAudit": (
            "runtime-character-r1086/browser-audit.json; "
            "female-v249-mainline-r1086-full-density-double-sided-hair.visual-audit.json; "
            "female-v249-mainline-r1086-full-density-double-sided-hair.audit.json"
        ),
        "latestFullCharacterRuntimeStatus": (
            "R1086_TECHNICAL_PASS_VISUAL_FAIL_NOT_WEBSITE_ASSET; all 3770 curves render double-sided with a soft depth-aware mask. "
            "Front/back frame medians are 7.7178/10.1222ms, update medians 0.5956/0.6983ms, with 42 draw calls, 573616 triangles, "
            "8240080 dynamic bytes, zero penetrations over 664560 point instances and 0.208mm minimum clearance. Strict visual score "
            "is 28/100 because the frontal hairline remains bald/scalloped and the rear occipital/nape gap survives full-density rendering. "
            "Website v83 remains unchanged."
        ),
        "latestFullHeadStatus": (
            "R1086_BROWSER_RUNTIME_28_OF_100_VISUAL_FAIL; r1086 removes culling and hard-mask ambiguity but proves the source groom "
            "lacks frontal and rear coverage topology. The retained Blender source remains 42/100 and website v83 remains unchanged."
        ),
        "nextRequiredWork": [
            "In Blender, author explicit frontal hairline, occipital coverage and nape guide rows on the r1083/r1086 mainline source.",
            "Build asymmetric large and medium clumps before adding fine fibers; reject shader overlays and historical scalp transplants.",
            "Export a new owned runtime package and repeat front, oblique, profile, rear, top, motion, collision and browser performance gates before website promotion.",
        ],
        "nextFaceTopologyWork": aggregate["nextRequiredWork"],
    }
)
write_json(current_path, current)

print(json.dumps({"revision": manifest["revision"], "technical": "PASS", "visual": "FAIL", "score": 28}, indent=2))
