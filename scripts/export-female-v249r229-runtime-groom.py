import json
import shutil
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SOURCE_BLEND = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-pruned-long-hair-r229.blend"
SOURCE_RUNTIME = ROOT / "assets-source/aevrynd-character/runtime-groom-v249r94"
SOURCE_DYNAMIC = ROOT.parent / "Temp/female-realism/v249-mainline-cc0-natural-long-hair-r94-dynamics"
OUTPUT_RUNTIME = ROOT / "assets-source/aevrynd-character/runtime-groom-v249r229"
OUTPUT_DYNAMIC = ROOT.parent / "Temp/female-realism/v249r229-pruned-long-hair-dynamics"
REPORT = OUTPUT_RUNTIME / "integration.json"
MAIN = "AevryndFemaleCC0LongHairStudyMain_v249r85"
POINTS_PER_CURVE = 20
SOURCE_MAIN_CURVES = 11193


def subset_file(source, target, indices, bytes_per_curve):
    payload = source.read_bytes()
    expected_minimum = SOURCE_MAIN_CURVES * bytes_per_curve
    if len(payload) < expected_minimum:
        raise RuntimeError(f"{source.name}: {len(payload)} bytes is smaller than {expected_minimum}")
    with target.open("wb") as handle:
        for index in indices:
            start = index * bytes_per_curve
            handle.write(payload[start:start + bytes_per_curve])


bpy.ops.wm.open_mainfile(filepath=str(SOURCE_BLEND))
main = bpy.data.objects[MAIN]
source_index = main.data.attributes["aevrynd_source_curve_index"]
indices = [item.value for item in source_index.data]
if len(indices) != len(main.data.curves) or len(set(indices)) != len(indices):
    raise RuntimeError("retained source curve indices are incomplete or duplicated")
if indices != sorted(indices) or indices[0] < 0 or indices[-1] >= SOURCE_MAIN_CURVES:
    raise RuntimeError("retained source curve indices are out of order or range")

OUTPUT_RUNTIME.mkdir(parents=True, exist_ok=True)
OUTPUT_DYNAMIC.mkdir(parents=True, exist_ok=True)
shutil.copyfile(SOURCE_RUNTIME / "simulation-guides.f32", OUTPUT_RUNTIME / "simulation-guides.f32")
subset_file(SOURCE_RUNTIME / "follow-guide.u16", OUTPUT_RUNTIME / "follow-guide.u16", indices, 2)
subset_file(SOURCE_RUNTIME / "follow-offsets.f32", OUTPUT_RUNTIME / "follow-offsets.f32", indices, POINTS_PER_CURVE * 3 * 4)
subset_file(SOURCE_RUNTIME / "follow-collision-normal.i8", OUTPUT_RUNTIME / "follow-collision-normal.i8", indices, POINTS_PER_CURVE * 3)
subset_file(SOURCE_RUNTIME / "follow-contact-head-weight.u8", OUTPUT_RUNTIME / "follow-contact-head-weight.u8", indices, POINTS_PER_CURVE)

manifest = json.loads((SOURCE_RUNTIME / "manifest.json").read_text(encoding="utf-8"))
manifest["source"] = str(SOURCE_BLEND)
manifest["render"]["curveCount"] = len(indices)
manifest["layers"] = [{
    "id": "hair.cc0-baked.main",
    "simulated": True,
    "curveCount": len(indices),
    "simulationGuides": 192,
}]
manifest["releaseState"] = "R229_TECHNICAL_CANDIDATE_NOT_WEBSITE_ASSET"
manifest["pruning"] = {
    "sourceRuntime": "runtime-groom-v249r94",
    "sourceCurveCount": SOURCE_MAIN_CURVES,
    "retainedCurveCount": len(indices),
    "sourceIndexAttribute": source_index.name,
    "exactDynamicTrajectorySubset": True,
}
(OUTPUT_RUNTIME / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

frames = json.loads((SOURCE_DYNAMIC / "frames.json").read_text(encoding="utf-8"))
for state in frames["saved"]:
    subset_file(SOURCE_DYNAMIC / state["filename"], OUTPUT_DYNAMIC / state["filename"], indices, POINTS_PER_CURVE * 3 * 4)
frames["source"] = str(OUTPUT_RUNTIME)
frames["curveCount"] = len(indices)
frames["mainCurveCount"] = len(indices)
frames["fillCurveCount"] = 0
frames["simulatedLayers"] = [{"id": "hair.cc0-baked.main", "curveCount": len(indices)}]
(OUTPUT_DYNAMIC / "frames.json").write_text(json.dumps(frames, indent=2), encoding="utf-8")

source_bytes = sum((SOURCE_RUNTIME / name).stat().st_size for name in (
    "follow-guide.u16", "follow-offsets.f32", "follow-collision-normal.i8", "follow-contact-head-weight.u8"
))
output_bytes = sum((OUTPUT_RUNTIME / name).stat().st_size for name in (
    "follow-guide.u16", "follow-offsets.f32", "follow-collision-normal.i8", "follow-contact-head-weight.u8"
))
report = {
    "sourceBlend": str(SOURCE_BLEND),
    "sourceRuntime": str(SOURCE_RUNTIME),
    "outputRuntime": str(OUTPUT_RUNTIME),
    "retainedCurveCount": len(indices),
    "retainedPointCount": len(indices) * POINTS_PER_CURVE,
    "sourceIndexMinimum": indices[0],
    "sourceIndexMaximum": indices[-1],
    "sourceIndexUnique": len(set(indices)) == len(indices),
    "dynamicStates": [state["frame"] for state in frames["saved"]],
    "sourceFollowBytes": source_bytes,
    "outputFollowBytes": output_bytes,
    "followByteReductionPercent": (1.0 - output_bytes / source_bytes) * 100.0,
    "trajectorySource": "exact subset of the r187 motion-audited r94 runtime states",
    "status": "DYNAMIC_COLLISION_AUDIT_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R229_RUNTIME_GROOM=" + json.dumps(report, sort_keys=True))
