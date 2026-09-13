import hashlib
import json
import os
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
BASELINE = Path(os.environ.get(
    "AEVRYND_PARITY_BASELINE",
    ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-runtime-balanced-brunette-r468-study.blend",
))
CANDIDATE = Path(os.environ.get(
    "AEVRYND_PARITY_CANDIDATE",
    ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-clean-cornea-r470.blend",
))
OUTPUT = Path(os.environ.get(
    "AEVRYND_PARITY_OUTPUT",
    ROOT / "assets-source/aevrynd-character/female-v249-mainline-clean-cornea-r470.collision-audit.json",
))
OBJECTS = (
    "AevryndFemaleBodyBaseV118",
    "Lip_Lower", "Lip_Upper", "Mouth_OralCavity", "Mouth_Tongue", "Mouth_UpperTeeth", "Mouth_WetLine",
) + tuple(
    f"Eye_{side}_{part}"
    for side in ("L", "R")
    for part in ("Caruncle", "Cornea", "Iris", "Pupil", "Sclera", "TearMeniscus", "UpperLashes")
)


def evaluated_hash(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    digest = hashlib.sha256()
    digest.update(str(len(mesh.vertices)).encode())
    digest.update(str(len(mesh.polygons)).encode())
    matrix = evaluated.matrix_world
    for vertex in mesh.vertices:
        point = matrix @ vertex.co
        digest.update(("%.8f,%.8f,%.8f;" % tuple(point)).encode())
    for polygon in mesh.polygons:
        digest.update((",".join(map(str, polygon.vertices)) + ";").encode())
    evaluated.to_mesh_clear()
    return digest.hexdigest()


def snapshot(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    scene = bpy.context.scene
    result = {}
    for frame in (1, 20):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        result[str(frame)] = {name: evaluated_hash(bpy.data.objects[name], depsgraph) for name in OBJECTS}
    return result


baseline = snapshot(BASELINE)
candidate = snapshot(CANDIDATE)
changes = []
for frame in ("1", "20"):
    for name in OBJECTS:
        if baseline[frame][name] != candidate[frame][name]:
            changes.append({
                "frame": int(frame),
                "object": name,
                "baseline": baseline[frame][name],
                "candidate": candidate[frame][name],
            })

cornea = bpy.data.materials["Aevrynd_Eye_Cornea_ClearBlend_R470"]
shader = next(node for node in cornea.node_tree.nodes if node.bl_idname == "ShaderNodeBsdfPrincipled")
report = {
    "baseline": str(BASELINE),
    "candidate": str(CANDIDATE),
    "frames": [1, 20],
    "objects": list(OBJECTS),
    "comparison": "SHA-256 over evaluated world-space vertices and face topology",
    "baselineHashes": baseline,
    "candidateHashes": candidate,
    "geometryChanges": changes,
    "corneaMaterial": {
        "name": cornea.name,
        "surfaceRenderMethod": cornea.surface_render_method,
        "roughness": shader.inputs["Roughness"].default_value,
        "transmissionWeight": shader.inputs["Transmission Weight"].default_value,
        "alpha": shader.inputs["Alpha"].default_value,
    },
    "collisionInference": "Exact evaluated geometry parity means body/eye/mouth collision state is unchanged from the audited r446/r468 geometry.",
    "status": "PASS_GEOMETRY_PARITY_COLLISION_STATE_INHERITED" if not changes else "FAIL_GEOMETRY_CHANGED",
}
OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R470_PARITY=" + json.dumps({"status": report["status"], "changes": changes}, sort_keys=True))
if changes:
    raise SystemExit(2)
