import json
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249.blend"
BODY = "AevryndFemaleBodyBaseV118"
HAIR = ("HairCoverageTiles_v246", "HairSilhouetteCards_v246", "HairDetailFibers_v246")
SOLIDS = (
    BODY, "HairScalp", "Clothing_Bandeau_v160",
    "Clothing_BandeauBinding_v162", "Clothing_BodyFitShorts_v135",
)


def tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    result = BVHTree.FromPolygons(
        [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices],
        [tuple(poly.vertices) for poly in mesh.polygons],
        all_triangles=False,
    )
    evaluated.to_mesh_clear()
    return result


bpy.ops.wm.open_mainfile(filepath=str(MODEL))
scene = bpy.context.scene
report = {"frames": {}, "status": "PASS", "failures": []}
for frame in (1, 20):
    scene.frame_set(frame)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    cache = {}
    def get(name):
        if name not in cache:
            cache[name] = tree(bpy.data.objects[name], depsgraph)
        return cache[name]
    values = {}
    for hair in HAIR:
        for solid in SOLIDS:
            key = f"{hair}__{solid}"
            values[key] = len(get(hair).overlap(get(solid)))
            if values[key]:
                report["failures"].append({"frame": frame, "pair": key, "overlaps": values[key]})
    # These contacts are intentional alpha-card layering and are recorded rather
    # than treated as solid-surface penetration.
    values["coverage__silhouette_layer_contacts"] = len(get(HAIR[0]).overlap(get(HAIR[1])))
    values["coverage__hairline_layer_contacts"] = len(get(HAIR[0]).overlap(get("HairlineNaturalCards_v214")))
    values["silhouette__hairline_layer_contacts"] = len(get(HAIR[1]).overlap(get("HairlineNaturalCards_v214")))
    values["fibers__hairline_layer_contacts"] = len(get(HAIR[2]).overlap(get("HairlineNaturalCards_v214")))
    values["coverage__fibers_layer_contacts"] = len(get(HAIR[0]).overlap(get(HAIR[2])))
    values["silhouette__fibers_layer_contacts"] = len(get(HAIR[1]).overlap(get(HAIR[2])))
    report["frames"][str(frame)] = values

if scene.get("aevrynd_hair_revision") != 246:
    report["failures"].append({"contract": "scene hair revision mismatch"})
for name in HAIR:
    obj = bpy.data.objects.get(name)
    if obj is None or obj.get("aevrynd_revision") != 246 or not obj.get("aevrynd_runtime_owned"):
        report["failures"].append({"contract": f"invalid owned layer {name}"})
if report["failures"]:
    report["status"] = "FAIL"
(ROOT / "assets-source/aevrynd-character/female-authoring-v249.hair-audit.json").write_text(
    json.dumps(report, indent=2), encoding="utf-8"
)
print("AEVRYND_V249_HAIR_AUDIT=" + json.dumps(report, sort_keys=True))
if report["failures"]:
    raise SystemExit(2)


