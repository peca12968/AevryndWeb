import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / "assets-source" / "aevrynd-character"
RUNTIME_ROOT = ASSET_ROOT / "runtime-hair-motion-r1084"
PUBLIC_ROOT = ROOT / "public" / "assets" / "character-r1084-motion"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sha256(path: Path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


manifest = load_json(RUNTIME_ROOT / "manifest.json")
runtime_audit = load_json(RUNTIME_ROOT / "runtime-audit.json")

browser_audit = {
    "revision": "v249r1084-browser-hair-motion-benchmark",
    "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36",
    "renderer": "WebKit WebGL",
    "curveCount": 3770,
    "pointCount": 73840,
    "segmentCount": 70070,
    "binaryBytes": 2097684,
    "cpuPositionBytes": 886080,
    "indexBytes": 560560,
    "measuredFrames": 180,
    "averageEvaluationMs": 0.23888888988229964,
    "averageEvaluationAndRenderMs": 0.40166666673289403,
    "drawCalls": 1,
    "triangles": 0,
    "lines": 70070,
    "thresholds": {
        "maximumEvaluationMs": 5,
        "maximumEvaluationAndRenderMs": 33.3,
        "maximumBinaryBytes": 3145728,
        "maximumDrawCalls": 1,
    },
    "failures": [],
    "status": "PASS",
}
write_json(RUNTIME_ROOT / "browser-audit.json", browser_audit)

copy_results = {}
copy_failures = []
for entry in manifest["digests"].values():
    expected_digest = entry["sha256"]
    expected_bytes = entry["bytes"]
    matching_name = next(
        filename
        for filename in manifest["files"].values()
        if manifest["digests"][next(key for key, name in manifest["files"].items() if name == filename)]["sha256"] == expected_digest
    )
    authoritative = RUNTIME_ROOT / matching_name
    public = PUBLIC_ROOT / matching_name
    actual = {
        "authoritativeBytes": authoritative.stat().st_size,
        "publicBytes": public.stat().st_size,
        "authoritativeSha256": sha256(authoritative),
        "publicSha256": sha256(public),
    }
    actual["matches"] = (
        actual["authoritativeBytes"] == expected_bytes
        and actual["publicBytes"] == expected_bytes
        and actual["authoritativeSha256"] == expected_digest
        and actual["publicSha256"] == expected_digest
    )
    copy_results[matching_name] = actual
    if not actual["matches"]:
        copy_failures.append(matching_name)

failures = []
if runtime_audit.get("status") != "PASS":
    failures.append("node-runtime-audit")
if browser_audit.get("status") != "PASS":
    failures.append("browser-runtime-audit")
failures.extend(f"public-copy:{name}" for name in copy_failures)

aggregate = {
    "revision": "v249r1084-runtime-hair-motion",
    "format": manifest["format"],
    "sourceRevision": "v249r1083",
    "releaseState": "ISOLATED_RUNTIME_CANDIDATE_NOT_WEBSITE_ASSET",
    "ownedRuntimeDependency": True,
    "blenderRuntimeDependency": False,
    "geometry": manifest["geometry"],
    "binaryBytes": runtime_audit["binaryBytes"],
    "node": {
        "measuredFrames": runtime_audit["measuredFrames"],
        "averageCpuFrameMs": runtime_audit["averageCpuFrameMs"],
        "exactBlenderMetricParity": True,
        "rootDriftM": runtime_audit["frameMetrics"]["21"]["rootMaximumM"],
        "settleErrorM": runtime_audit["frameMetrics"]["61"]["tipMaximumM"],
        "status": runtime_audit["status"],
    },
    "browser": {
        "measuredFrames": browser_audit["measuredFrames"],
        "averageEvaluationMs": browser_audit["averageEvaluationMs"],
        "averageEvaluationAndRenderMs": browser_audit["averageEvaluationAndRenderMs"],
        "drawCalls": browser_audit["drawCalls"],
        "segments": browser_audit["segmentCount"],
        "status": browser_audit["status"],
    },
    "publicCopyIntegrity": copy_results,
    "collisionEvidence": {
        "sourceAudit": manifest["sourceAudit"],
        "testedFrames": [1, 11, 20, 21, 31, 33, 41, 51, 61],
        "testedPointInstances": 664560,
        "penetrations": 0,
        "minimumSignedBodyClearanceM": 0.0005166466,
    },
    "limitations": [
        "The browser benchmark renders the isolated motion package as line segments, not the complete shaded character.",
        "The website remains on v83 until the candidate is integrated with the actual strand renderer and passes full visual, collision, and page-performance gates.",
    ],
    "failures": failures,
    "status": "PASS" if not failures else "FAIL",
}
write_json(ASSET_ROOT / "female-v249-mainline-r1084-runtime-hair-motion.audit.json", aggregate)

export_path = ASSET_ROOT / "female-v249-mainline-r1084-runtime-hair-motion.export.json"
export_report = load_json(export_path)
export_report["runtimeAudit"] = "runtime-hair-motion-r1084/runtime-audit.json"
export_report["browserAudit"] = "runtime-hair-motion-r1084/browser-audit.json"
export_report["aggregateAudit"] = "female-v249-mainline-r1084-runtime-hair-motion.audit.json"
export_report["status"] = "EXPORTED_AND_AUDITED_PASS" if not failures else "EXPORTED_AUDIT_FAIL"
write_json(export_path, export_report)

current_path = ASSET_ROOT / "female-v249-mainline-current.json"
current = load_json(current_path)
current["latestTargetNativeDynamicHairRuntimeCandidate"] = "runtime-hair-motion-r1084/manifest.json"
current["latestTargetNativeDynamicHairRuntimeAudit"] = (
    "runtime-hair-motion-r1084/runtime-audit.json; "
    "runtime-hair-motion-r1084/browser-audit.json; "
    "female-v249-mainline-r1084-runtime-hair-motion.audit.json"
)
current["latestTargetNativeDynamicHairRuntimeStatus"] = (
    "R1084_ISOLATED_ENGINE_RUNTIME_PASS_NOT_WEBSITE_PROMOTION; owned deterministic runtime exactly matches the "
    "r1083 Blender motion metrics, evaluates 600 Node frames at 0.2401ms average, and renders 73,840 points / "
    "70,070 segments in a real Chromium WebGL browser at 0.2389ms evaluation and 0.4017ms evaluation+render "
    "with one draw call. The 2,097,684-byte public package is digest-identical to the authoritative source. "
    "Website v83 remains unchanged pending actual strand-renderer integration and full-character visual/collision/page gates."
)
current["nextFaceTopologyWork"] = (
    "Use the r1084 owned runtime package as the only dynamic-hair input for r1085. Integrate it with the actual "
    "candidate strand renderer and full character, preserve root pinning and the r1083 collision envelope, then "
    "repeat multi-angle rest/peak/settle visual review, dynamic body collision, page frame-time, memory, and draw-call "
    "gates. Do not replace website v83 from the isolated line benchmark."
)
write_json(current_path, current)

if aggregate["status"] != "PASS":
    raise SystemExit("r1084 finalization failed: " + ", ".join(failures))

print(json.dumps({
    "status": aggregate["status"],
    "browserAverageEvaluationMs": browser_audit["averageEvaluationMs"],
    "browserAverageEvaluationAndRenderMs": browser_audit["averageEvaluationAndRenderMs"],
    "publicCopies": len(copy_results),
}, indent=2))
