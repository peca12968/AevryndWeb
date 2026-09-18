"""Export the r1083 character without its Blender-only groom for r1085 runtime integration."""
import hashlib
import json
import subprocess
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-layered-hair-motion-r1083-study.blend"
OUTPUT_DIR = ROOT / "public" / "assets" / "character-r1085"
OUTPUT = OUTPUT_DIR / "character-r1085.glb"
RAW_OUTPUT = ROOT / ".character-build" / "character-r1085-authoring.glb"
MANIFEST = ASSETS / "runtime-character-r1085" / "manifest.json"
HAIR = "AevryndFemaleGradedHairlineGroom_R1081"
ANCHOR = "AevryndHairMotionAnchor_R1085"
BODY = "AevryndFemaleCC0BalancedEyeOptics_R1080"
RUNTIME_BODY = "AevryndFemaleEvaluatedSurface_R1085"


def sha256(path: Path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
hair = bpy.data.objects[HAIR]
body = bpy.data.objects[BODY]
for modifier in body.modifiers:
    if modifier.type == "SUBSURF":
        modifier.levels = 1
        modifier.render_levels = 1

old_runtime_body = bpy.data.objects.get(RUNTIME_BODY)
if old_runtime_body:
    bpy.data.objects.remove(old_runtime_body, do_unlink=True)
depsgraph = bpy.context.evaluated_depsgraph_get()
depsgraph.update()
evaluated_body = body.evaluated_get(depsgraph)
runtime_body_mesh = bpy.data.meshes.new_from_object(evaluated_body, depsgraph=depsgraph, preserve_all_data_layers=True)
runtime_body = bpy.data.objects.new(RUNTIME_BODY, runtime_body_mesh)
scene.collection.objects.link(runtime_body)
runtime_body.matrix_world = body.matrix_world.copy()
runtime_body["aevrynd_runtime_role"] = "evaluated-static-collision-and-visual-surface"
runtime_body["aevrynd_source_object"] = BODY

old_anchor = bpy.data.objects.get(ANCHOR)
if old_anchor:
    bpy.data.objects.remove(old_anchor, do_unlink=True)
anchor = bpy.data.objects.new(ANCHOR, None)
scene.collection.objects.link(anchor)
anchor.empty_display_type = "PLAIN_AXES"
anchor.empty_display_size = 0.08
anchor.parent = hair.parent
anchor.parent_type = hair.parent_type
anchor.parent_bone = hair.parent_bone
anchor.matrix_world = hair.matrix_world.copy()
anchor["aevrynd_runtime_role"] = "dynamic-hair-local-origin"
anchor["aevrynd_source_object"] = HAIR

bpy.ops.object.select_all(action="DESELECT")
selected = []
for item in scene.objects:
    if item in {hair, body} or item.type in {"CAMERA", "LIGHT"}:
        continue
    if item.type not in {"ARMATURE", "MESH", "CURVES", "EMPTY"}:
        continue
    if item.hide_viewport or item.hide_render or item.hide_get():
        continue
    item.select_set(True)
    selected.append(item)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
RAW_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
MANIFEST.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(
    filepath=str(RAW_OUTPUT),
    export_format="GLB",
    use_selection=True,
    export_apply=False,
    export_yup=True,
    export_extras=True,
    export_animations=False,
    export_attributes=True,
    export_vertex_color="ACTIVE",
)
packer = ROOT.parent / "ToolCache" / "meshoptimizer-1.2-build" / "Release" / "gltfpack.exe"
subprocess.run([
    str(packer), "-i", str(RAW_OUTPUT), "-o", str(OUTPUT),
    "-cc", "-kn", "-km", "-ke", "-kv", "-vp", "16", "-vt", "16", "-vn", "12",
], check=True)

report = {
    "format": "aevrynd-full-character-with-runtime-hair-v1",
    "revision": "v249r1085-full-character-export",
    "source": str(SOURCE),
    "asset": "public/assets/character-r1085/character-r1085.glb",
    "assetBytes": OUTPUT.stat().st_size,
    "assetSha256": sha256(OUTPUT),
    "excludedBlenderGroom": HAIR,
    "runtimeHair": "runtime-hair-motion-r1084/manifest.json",
    "anchor": ANCHOR,
    "selectedObjects": len(selected),
    "selectedMeshes": sum(item.type == "MESH" for item in selected),
    "selectedCurves": sum(item.type == "CURVES" for item in selected),
    "selectedArmatures": sum(item.type == "ARMATURE" for item in selected),
    "evaluatedStaticBody": RUNTIME_BODY,
    "evaluatedBodyVertices": len(runtime_body_mesh.vertices),
    "evaluatedBodyFaces": len(runtime_body_mesh.polygons),
    "evaluatedSubdivisionLevels": 1,
    "deformationQualification": "PENDING_WEIGHT_AND_SHAPE_KEY_TRANSFER",
    "ownership": "Aevrynd-owned/CC0-traceable authoring geometry; no MetaHuman or Unreal runtime dependency",
    "releaseState": "ISOLATED_FULL_CHARACTER_CANDIDATE_NOT_WEBSITE_ASSET",
}
MANIFEST.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print("AEVRYND_R1085_FULL_CHARACTER_EXPORT=" + json.dumps(report, sort_keys=True))
