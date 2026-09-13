import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "assets-source/aevrynd-character"
TEMP = ROOT.parent / "Temp/female-realism"
REVIEW = ASSET_DIR / "reviews/v249r421-r436-lid-retopology-research"
SUMMARY = ASSET_DIR / "female-v249-mainline-r421-r436-lid-retopology-research.json"
MANIFEST = ASSET_DIR / "female-v249-mainline-current.json"


def update_report(filename, status, finding):
    path = ASSET_DIR / filename
    data = json.loads(path.read_text(encoding="utf-8"))
    data["status"] = status
    data["strictVisualFinding"] = finding
    data["websitePromotionApproved"] = False
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


decisions = {
    "female-v249-mainline-anatomical-lid-relief-r421.study.json": (
        "REJECTED_NO_MEANINGFUL_VISUAL_GAIN",
        "All three additive relief strengths remain visually indistinguishable at normal review distance; none resolves the flat applied-body eyelid flow.",
    ),
    "female-v249-mainline-extended-lid-relief-r422.study.json": (
        "REJECTED_DOUBLE_WHITE_BANDS",
        "The stronger displacement moves interleaved exterior and inner eyelid surfaces, producing stacked pale bands above the aperture.",
    ),
    "female-v249-mainline-external-lid-relief-r423.study.json": (
        "REJECTED_EXTERNAL_GATE_STILL_BANDED",
        "Normal and depth gating reduces affected vertices but does not isolate a coherent anatomical eyelid loop; the extra band remains.",
    ),
    "female-v249-mainline-single-profile-lid-r424.study.json": (
        "REJECTED_SAGGING_RECTANGULAR_PATCHES",
        "Direct profile fitting produces a hard upper ledge and rectangular lower-eye sag instead of a continuous tarsal surface.",
    ),
    "female-v249-mainline-external-lid-smoothing-r425.study.json": (
        "REJECTED_NO_MEANINGFUL_VISUAL_GAIN",
        "Four to fourteen smoothing iterations preserve the inherited edge-flow defect and do not create anatomical eyelid volume.",
    ),
    "female-v249-mainline-multiscale-skin-r426.study.json": (
        "REJECTED_NO_NORMAL_DISTANCE_GAIN",
        "Balanced chromatic mottling and chained pore normals slightly reduce waxiness only in close crops; the normal-distance hero-skin gate does not improve.",
    ),
    "female-v249-head-retopo-cage-r427.study.json": (
        "REJECTED_QUADRIFLOW_NO_TOPOLOGY_CHANGE",
        "QuadriFlow rejected the neck-cut evaluated mesh and left all 62,269 polygons unchanged.",
    ),
    "female-v249-exterior-head-cage-r428.study.json": (
        "REJECTED_QUADRIFLOW_TOPOLOGY_GATE_FAIL",
        "Largest-component cleanup proves the cut head is one connected shell with 314 boundary edges, but QuadriFlow still leaves topology unchanged.",
    ),
    "female-v249-exterior-head-cage-r429.study.json": (
        "REJECTED_QUADRIFLOW_TOPOLOGY_GATE_FAIL",
        "Triangulating the only 314-edge neck boundary produces a closed shell, yet short edges still trip Blender's manifold-consistency check.",
    ),
    "female-v249-exterior-head-cage-r430.study.json": (
        "REJECTED_QUADRIFLOW_TOPOLOGY_GATE_FAIL",
        "A 1.5 mm voxel remesh creates a watertight exterior but also many tiny neck-cut islands; QuadriFlow does not run.",
    ),
    "female-v249-exterior-head-cage-r431.study.json": (
        "REJECTED_QUADRIFLOW_TOPOLOGY_GATE_FAIL",
        "Removing all post-voxel islands yields one closed shell, but sub-0.1 mm edges still fail Blender's hidden QuadriFlow check.",
    ),
    "female-v249-exterior-head-cage-r432.study.json": (
        "REJECTED_QUADRIFLOW_TOPOLOGY_GATE_FAIL",
        "Removing the BMesh deform layer does not change the result; QuadriFlow still rejects the surface.",
    ),
    "female-v249-exterior-head-cage-r433.study.json": (
        "REJECTED_QUADRIFLOW_TOPOLOGY_GATE_FAIL",
        "Rebuilding a new geometry-only Mesh datablock removes inherited attributes but confirms custom data is not the remaining blocker.",
    ),
    "female-v249-exterior-head-cage-r434.study.json": (
        "REJECTED_SHORT_EDGE_DISSOLVE_BREAKS_MANIFOLD",
        "Dissolving 87 sub-0.1 mm edges creates boundary, wire and over-connected edges; this repair is unsafe.",
    ),
    "female-v249-exterior-head-cage-r435.study.json": (
        "TOPOLOGY_GATE_PASS_VISUAL_FAIL_SCAFFOLD_ONLY",
        "Temporary 100x geometry scaling clears Blender's absolute 0.1 mm edge check and produces 13,088 all-quad faces. Eye corners, nostrils, mouth corners and ear rims remain torn or collapsed, so this is a topology scaffold only.",
    ),
    "female-v249-shrinkwrapped-head-cage-r436.study.json": (
        "REJECTED_SURFACE_REPROJECTION_WRONG_TARGETS",
        "Nearest-surface reprojection moves vertices by up to 62.15 mm and retains broken eye, nose, mouth and ear boundaries.",
    ),
}
for filename, (status, finding) in decisions.items():
    update_report(filename, status, finding)

REVIEW.mkdir(parents=True, exist_ok=True)
review_images = {
    ASSET_DIR / "reviews/v249r420-layered-optical-stack/r420-neutral-eyes.png": "r420-neutral-eyes-baseline.png",
    TEMP / "v249r421-anatomical-lid-relief-sweep/c-strong-eyes.png": "r421-strong-no-gain.png",
    TEMP / "v249r422-extended-lid-relief-sweep/c-maximum-eyes.png": "r422-maximum-double-bands.png",
    TEMP / "v249r423-external-lid-relief-sweep/b-external-eyes.png": "r423-gated-still-banded.png",
    TEMP / "v249r424-single-profile-lid-sweep/b-half-eyes.png": "r424-profile-sag.png",
    TEMP / "v249r425-external-lid-smoothing-sweep/c-fourteen-eyes.png": "r425-smoothing-no-gain.png",
    TEMP / "v249r426-multiscale-skin-sweep/b-balanced-face-close.png": "r426-balanced-skin-close.png",
    TEMP / "v249r427-head-retopo-cage-study/r427-front.png": "r427-quadriflow-failed-front.png",
    TEMP / "v249r435-scaled-quadriflow-head-cage-study/r435-front.png": "r435-scaffold-front.png",
    TEMP / "v249r435-scaled-quadriflow-head-cage-study/r435-three-quarter.png": "r435-scaffold-three-quarter.png",
    TEMP / "v249r435-scaled-quadriflow-head-cage-study/r435-profile.png": "r435-scaffold-profile.png",
    TEMP / "v249r436-shrinkwrapped-head-cage-study/r436-front.png": "r436-reprojection-rejected-front.png",
    TEMP / "v249r436-shrinkwrapped-head-cage-study/r436-three-quarter.png": "r436-reprojection-rejected-three-quarter.png",
}
for source, filename in review_images.items():
    if not source.exists():
        raise FileNotFoundError(source)
    shutil.copy2(source, REVIEW / filename)

summary = {
    "mainlineBase": "aevrynd-female-authoring-v249-mainline-layered-optical-stack-r420.blend",
    "range": "r421-r436",
    "reviewDirectory": str(REVIEW),
    "authoritativeFaceCandidateUnchanged": "r420",
    "skinDecision": "r426 rejected: no normal-distance gain",
    "eyelidDecision": "r421-r425 rejected: applied 169k body topology cannot be converted into anatomical eyelid loops by coordinate displacement or smoothing",
    "retopologyDecision": "r435 is retained as a 13,088-face all-quad topology scaffold; r427-r434 document the Blender input constraints and r436 proves unconstrained nearest-surface reprojection is unsafe",
    "blenderSourceFinding": "Blender 5.2.1 mesh_is_manifold_consistent rejects edges whose endpoints compare within 1e-4 m; temporary geometry scaling avoids altering the source shape.",
    "nextRequiredWork": "On the r435 scaffold, replace the eye, nostril, mouth and ear boundary regions with explicit anatomical loops, then shrinkwrap only stable surrounding zones and transfer weights after visual topology passes.",
    "websitePromotionApproved": False,
    "status": "RESEARCH_PACKAGED_MAINLINE_UNCHANGED",
}
SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
(REVIEW / "review.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
manifest["latestFaceResearch"] = "r248 legacy displacement rejection; r249-r258 CC0 foundation; r300-r345 eye geometry and caruncle integration; r410-r420 orbital, lighting, aperture and layered optics; r421-r436 eyelid displacement and head retopology research"
manifest["latestFaceResearchStatus"] = "r420 remains the current technical face node. r421-r425 prove the applied 169k body cannot gain anatomical eyelid loops through displacement or smoothing. r435 produces a 13,088-face all-quad owned head scaffold after clearing Blender's absolute short-edge check, but strict visual review fails at eye, nose, mouth and ear boundaries. r436 unconstrained reprojection is rejected. Website gate remains closed."
manifest["latestFaceRetopologyResearch"] = "female-v249-mainline-r421-r436-lid-retopology-research.json"
manifest["latestFaceRetopologyResearchStatus"] = "R435_TOPOLOGY_PASS_VISUAL_FAIL_SCAFFOLD_ONLY_R436_REJECTED"
manifest["latestSkinMaterialResearch"] = "female-v249-mainline-multiscale-skin-r426.study.json"
manifest["latestSkinMaterialResearchStatus"] = "REJECTED_NO_NORMAL_DISTANCE_GAIN"
manifest["latestFaceRejectedExperiment"] = "r410-r416 orbital and aperture rejects; r421-r425 applied-body eyelid displacement/smoothing rejects; r427-r434 failed QuadriFlow input repair; r436 unsafe unconstrained reprojection"
manifest["latestFaceRejectedReason"] = "Applied high-density topology interleaves external and internal eyelid surfaces, so local coordinate edits create bands, ledges or no visible gain. R435 clears Blender's 0.1 mm absolute edge check and proves an owned all-quad scaffold is feasible, but automatic topology destroys anatomical facial boundaries; r436 nearest projection moves vertices to wrong surfaces."
manifest["nextRequiredWork"][0] = "以 r435 的 13,088 面全四邊形頭部籠為拓撲腳手架，手動重建上下眼瞼、鼻孔、嘴角與耳輪的環狀拓撲；僅回貼穩定的額頭、臉頰、顱頂與頸部區域，保留 r420 十層眼球並重跑第 1／20 幀零穿模與中性亮度審查。"
MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
