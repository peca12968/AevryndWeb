import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"

strengths = {
    "0.05": {"frame1": 2, "frame20": 2, "frame33": 2, "frame61": 2},
    "0.10": {"frame1": 7, "frame20": 5, "frame33": 5, "frame61": 5},
    "0.20": {"frame1": 13, "frame20": 13, "frame33": 13, "frame61": 13},
    "0.40": {"frame1": 35, "frame20": 40, "frame33": 40, "frame61": 40},
    "0.80": {"frame1": 99, "frame20": 108, "frame33": 108, "frame61": 108},
    "1.20": {"frame1": 183, "frame20": 182, "frame33": 182, "frame61": 182},
}
report = {
    "revision": "v249r523-r524",
    "source": "aevrynd-female-authoring-v249-mainline-natural-commissures-r522.blend",
    "rejectedModel": "aevrynd-female-authoring-v249-mainline-orbital-volume-r524-rejected.blend",
    "method": "aperture-preserving orbital sweep followed by outward-only eyelid-roll collision clamp",
    "affectedVertices": 2060,
    "shapeKeysMovedTogether": [
        "Basis",
        "Aevrynd_Philtrum_Topology_R80",
        "Aevrynd_EyeAperture_Topology_R83",
        "Aevrynd_EvaluatedAnatomicalLids_R183",
        "Aevrynd_MouthPlacement_R198_5mm",
        "Aevrynd_ConvergedUpperLid_R210",
    ],
    "testedStrengths": strengths,
    "minimumTestedMaximumMoveMm": 0.7809777186417949 * (0.05 / 2.3),
    "visibleStudyStrengths": [1.8, 2.3, 2.8],
    "visibleStudy": "reviews/v249r523-orbital-volume-sweep/contact-sheet-orbital-volume-strong.jpg",
    "findings": [
        "The signed crease/tear-trough version intersected both cornea and sclera at every tested dynamic frame.",
        "Removing all inward crease and tear-trough motion increased overlap because the baseline eye envelope is already tightly tangent to the lid surface.",
        "Translating the complete optical stack in either world Y direction increased overlap and introduced iris, tear-meniscus or lash collisions.",
        "Even strength 0.05 produced two overlap pairs in every frame, so no nonzero collision-safe interval was found.",
    ],
    "status": "REJECTED_ZERO_COLLISION_NO_SAFE_VISIBLE_STRENGTH",
    "retainedMainline": "aevrynd-female-authoring-v249-mainline-natural-commissures-r522.blend",
    "websiteAsset": "v83 unchanged",
}
(ASSETS / "female-v249-mainline-orbital-volume-r524.rejection-audit.json").write_text(
    json.dumps(report, indent=2), encoding="utf-8"
)

build_path = ASSETS / "female-v249-mainline-orbital-volume-r524.build.json"
build = json.loads(build_path.read_text(encoding="utf-8"))
build["target"] = str(ASSETS / report["rejectedModel"])
build["status"] = report["status"]
build["rejectionAudit"] = "female-v249-mainline-orbital-volume-r524.rejection-audit.json"
build_path.write_text(json.dumps(build, indent=2), encoding="utf-8")

manifest_path = ASSETS / "female-v249-mainline-current.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
experiment = "r523-r524 orbital-volume sweep and outward-only eyelid-roll clamp"
if experiment not in manifest["latestRejectedExperiment"]:
    manifest["latestRejectedExperiment"] += "; " + experiment
manifest["latestRejectedReason"] = (
    "r523 makes orbital relief visible at strengths 1.8-2.8, but r524 finds no nonzero safe interval: "
    "even strength 0.05 creates two cornea/sclera overlap pairs at frames 1/20/33/61, while moving the "
    "optical stack in either direction worsens other eye-layer contacts. r522 remains the mainline."
)
if "r523-r524" not in manifest["latestFaceResearch"]:
    manifest["latestFaceResearch"] += "; r523-r524 rejected orbital-volume and eye-envelope study"
manifest["latestFaceResearchStatus"] = (
    "r522 remains the current offline technical face candidate at 58/100. r523-r524 proves the current "
    "tightly tangent eye envelope cannot accept visible orbital displacement: every nonzero bound fails "
    "the zero-overlap gate. The next orbital pass requires local eye-socket topology/clearance reconstruction."
)
if "r523-r524" not in manifest["latestFaceRejectedExperiment"]:
    manifest["latestFaceRejectedExperiment"] += "; r523-r524 orbital displacement with no nonzero collision-safe interval"
manifest["latestFaceRejectedReason"] = (
    "Even the minimum r524 strength 0.05 produces two eye-layer overlap pairs at every tested frame; visible "
    "bounds are much worse, and translating the optical stack introduces further iris, tear-film or lash contacts."
)
manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
print("AEVRYND_R524_REJECTION=" + json.dumps(report, sort_keys=True))
