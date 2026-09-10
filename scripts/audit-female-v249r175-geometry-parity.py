import hashlib
import json
import struct
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-deform-matched-scalp-r163.blend"
CANDIDATE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cornea-response-r175.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-cornea-response-r175.geometry-parity.json"


def update_point(digest, point):
    digest.update(struct.pack("<3d", float(point.x), float(point.y), float(point.z)))


def snapshot(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    scene = bpy.context.scene
    frames = {}
    for frame in (1, 20):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        digest = hashlib.sha256()
        objects = 0
        points = 0
        for obj in sorted(bpy.data.objects, key=lambda item: item.name):
            if obj.type not in {"MESH", "CURVES"}:
                continue
            evaluated = obj.evaluated_get(depsgraph)
            digest.update(obj.name.encode("utf-8"))
            digest.update(obj.type.encode("ascii"))
            if obj.type == "MESH":
                mesh = evaluated.to_mesh()
                digest.update(struct.pack("<II", len(mesh.vertices), len(mesh.polygons)))
                for vertex in mesh.vertices:
                    update_point(digest, evaluated.matrix_world @ vertex.co)
                for polygon in mesh.polygons:
                    digest.update(struct.pack("<I", len(polygon.vertices)))
                    for index in polygon.vertices:
                        digest.update(struct.pack("<I", index))
                points += len(mesh.vertices)
                evaluated.to_mesh_clear()
            else:
                digest.update(struct.pack("<II", len(evaluated.data.points), len(evaluated.data.curves)))
                for point in evaluated.data.points:
                    update_point(digest, evaluated.matrix_world @ point.position)
                points += len(evaluated.data.points)
            objects += 1
        frames[str(frame)] = {"sha256": digest.hexdigest(), "objects": objects, "points": points}
    return frames


baseline = snapshot(BASELINE)
candidate = snapshot(CANDIDATE)
status = "PASS" if baseline == candidate else "FAIL"
report = {"baseline": str(BASELINE), "candidate": str(CANDIDATE), "framesBaseline": baseline, "framesCandidate": candidate, "status": status}
OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R175_GEOMETRY_PARITY=" + json.dumps(report, sort_keys=True))
if status != "PASS":
    raise SystemExit(2)
