"""Measure the outer and socket surfaces around the r995 eye apertures."""

import json
from pathlib import Path

import bpy
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-target-native-lashes-r995.blend"
OUTPUT = ASSETS / "female-v249-mainline-cc0-target-native-lashes-r995.visible-eyelid-surface.json"
BODY = "AevryndFemaleCC0Baseline_v259"
CENTERS = {"L": 0.02815, "R": -0.02815}


def percentile(values, points=(0, 5, 25, 50, 75, 95, 100)):
    if not values:
        return {}
    array = np.asarray(values, dtype=np.float64)
    return {str(point): float(np.percentile(array, point)) for point in points}


def mixed_coordinates(body):
    blocks = body.data.shape_keys.key_blocks
    coordinates = [item.co.copy() for item in blocks[0].data]
    active = []
    for block in blocks[1:]:
        if block.mute or abs(block.value) < 1e-8:
            continue
        active.append({"name": block.name, "value": float(block.value)})
        for index, coordinate in enumerate(coordinates):
            coordinate += block.value * (
                block.data[index].co - block.relative_key.data[index].co
            )
    return coordinates, active


def summarize(body, coordinates, center_x):
    rows = []
    for index, coordinate in enumerate(coordinates):
        world = body.matrix_world @ coordinate
        dx = world.x - center_x
        if abs(dx) <= 0.018 and 1.431 < world.z < 1.474:
            rows.append({"index": index, "y": float(world.y), "z": float(world.z)})
    outer = [row for row in rows if row["y"] < -0.070]
    socket = [row for row in rows if row["y"] >= -0.070]
    return {
        "roiVertexCount": len(rows),
        "worldYPercentiles": percentile([row["y"] for row in rows]),
        "outerBand": {
            "criterion": "worldY < -0.070",
            "vertexCount": len(outer),
            "worldYPercentiles": percentile([row["y"] for row in outer]),
            "worldZPercentiles": percentile([row["z"] for row in outer]),
        },
        "socketBand": {
            "criterion": "worldY >= -0.070",
            "vertexCount": len(socket),
            "worldYPercentiles": percentile([row["y"] for row in socket]),
        },
    }


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
body = bpy.data.objects[BODY]
mixed, active = mixed_coordinates(body)
basis = [item.co.copy() for item in body.data.shape_keys.key_blocks[0].data]

report = {
    "source": str(SOURCE),
    "body": BODY,
    "coordinateNote": (
        "The review camera is on negative world Y. The Basis mesh is not the rendered face; "
        "selection must use the active relative-shape mix before modifiers."
    ),
    "activeShapeKeys": active,
    "sides": {},
}

for side, center_x in CENTERS.items():
    report["sides"][side] = {
        "basisCoordinateAnalysis": summarize(body, basis, center_x),
        "mixedCoordinateAnalysis": summarize(body, mixed, center_x),
    }

OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_VISIBLE_EYELID_SURFACE=" + json.dumps(report, sort_keys=True))
