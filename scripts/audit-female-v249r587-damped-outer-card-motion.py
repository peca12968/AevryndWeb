import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-damped-outer-card-motion-r587.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-damped-outer-card-motion-r587.motion-audit.json"
CARDS = "AevryndFemaleTangentOuterHairCards_R587"
RIG = "AevryndFemaleRig"
FRAMES = (1, 20, 33, 45, 61)
VERTICES_PER_CARD = 48
ROOT_VERTICES = 10


def evaluated_head_local_points(scene, obj, rig, frame):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    head_inverse = (rig.matrix_world @ rig.pose.bones["head"].matrix).inverted()
    points = [head_inverse @ (evaluated.matrix_world @ vertex.co) for vertex in mesh.vertices]
    evaluated.to_mesh_clear()
    return points


def percentile(values, fraction):
    ordered = sorted(values)
    if not ordered:
        return 0.0
    return ordered[min(len(ordered) - 1, round((len(ordered) - 1) * fraction))]


bpy.ops.wm.open_mainfile(filepath=str(MODEL))
scene = bpy.context.scene
obj = bpy.data.objects[CARDS]
rig = bpy.data.objects[RIG]
samples = {frame: evaluated_head_local_points(scene, obj, rig, frame) for frame in FRAMES}
rest = samples[1]

frames = {}
for frame in FRAMES:
    deltas = [(point - base).length for point, base in zip(samples[frame], rest)]
    root_deltas = []
    for start in range(0, len(deltas), VERTICES_PER_CARD):
        root_deltas.extend(deltas[start:start + ROOT_VERTICES])
    frames[str(frame)] = {
        "p95DeltaM": percentile(deltas, 0.95),
        "maxDeltaM": max(deltas, default=0.0),
        "rootMaxDeltaM": max(root_deltas, default=0.0),
    }

peak = samples[33]
pair_mismatch = []
card_count = len(rest) // VERTICES_PER_CARD
for card in range(0, card_count - 1, 2):
    first = card * VERTICES_PER_CARD
    second = (card + 1) * VERTICES_PER_CARD
    for offset in range(VERTICES_PER_CARD):
        delta_a = peak[first + offset] - rest[first + offset]
        delta_b = peak[second + offset] - rest[second + offset]
        pair_mismatch.append((delta_a - delta_b).length)

gates = {
    "peakP95AtLeast2mm": frames["33"]["p95DeltaM"] >= 0.002,
    "peakMaxAtLeast4mm": frames["33"]["maxDeltaM"] >= 0.004,
    "frame20ReboundAtLeast1mm": frames["20"]["maxDeltaM"] >= 0.001,
    "frame45ReboundAtLeast1mm": frames["45"]["maxDeltaM"] >= 0.001,
    "rootPinnedWithin0_02mm": max(item["rootMaxDeltaM"] for item in frames.values()) <= 0.00002,
    "settledByFrame61Within0_05mm": frames["61"]["maxDeltaM"] <= 0.00005,
    "companionCardsCoherentWithin0_02mm": max(pair_mismatch, default=0.0) <= 0.00002,
}
report = {
    "model": str(MODEL),
    "object": CARDS,
    "referenceSpace": "AevryndFemaleRig/head local",
    "frames": frames,
    "cardCount": card_count,
    "verticesPerCard": VERTICES_PER_CARD,
    "rootVerticesPerCard": ROOT_VERTICES,
    "peakCompanionCardMaxMismatchM": max(pair_mismatch, default=0.0),
    "gates": gates,
    "status": "PASS" if all(gates.values()) else "FAIL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R587_DAMPED_CARD_MOTION=" + json.dumps(report, sort_keys=True))
if report["status"] != "PASS":
    raise SystemExit(2)
