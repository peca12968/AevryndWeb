"""Expand the binary lips vertex group into a soft topological boundary."""

import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-soft-warm-lip-response-r1031-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-soft-lip-boundary-r1032-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1032-lip-mask-boundary-sweep.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r1032-lip-mask-boundary-sweep"
BODY = "AevryndFemaleCC0Baseline_v259"
GROUP = "lips"
VARIANTS = (
    ("source-r1031", ()),
    ("a-one-ring-soft", (0.35,)),
    ("b-one-ring-medium", (0.60,)),
    ("c-two-ring-falloff", (0.45, 0.18)),
)
SELECTED = "b-one-ring-medium"


def group_weights(obj, group):
    values = {}
    for vertex in obj.data.vertices:
        try:
            values[vertex.index] = group.weight(vertex.index)
        except RuntimeError:
            pass
    return values


def expand_group(obj, ring_weights):
    group = obj.vertex_groups[GROUP]
    adjacency = {vertex.index: set() for vertex in obj.data.vertices}
    for edge in obj.data.edges:
        first, second = edge.vertices
        adjacency[first].add(second)
        adjacency[second].add(first)
    original = set(group_weights(obj, group))
    reached = set(original)
    frontier = set(original)
    rings = []
    for ring_index, weight in enumerate(ring_weights, 1):
        candidates = set().union(*(adjacency[index] for index in frontier)) - reached
        # A topological ring from the authored lip set is more reliable than
        # Basis-space coordinates because the active MPFB mix relocates the face.
        retained = sorted(candidates)
        if retained:
            group.add(retained, weight, "REPLACE")
        frontier = set(retained)
        reached.update(frontier)
        rings.append({"ring": ring_index, "weight": weight, "vertices": len(retained)})
    final = group_weights(obj, group)
    return {"originalVertices": len(original), "rings": rings, "finalVertices": len(final), "minimumWeight": min(final.values()), "maximumWeight": max(final.values())}


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def hide_hair(scene):
    hidden = []
    for obj in scene.objects:
        is_hair = obj.name.startswith(("Groom_", "AevryndFemaleTargetScalp")) or obj.type == "CURVES"
        is_face_fibre = "Brow" in obj.name or obj.name.endswith(("UpperLashes", "LowerLashes"))
        if is_hair and not is_face_fibre and not obj.hide_render:
            obj.hide_render = True
            hidden.append(obj.name)
    return hidden


def render(scene, label, location, target, lens, size=(1000, 1000)):
    camera = scene.camera
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    path = RENDER_DIR / f"{label}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return str(path)


RENDER_DIR.mkdir(parents=True, exist_ok=True)
variants = []
for label, ring_weights in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    bpy.context.view_layer.update()
    body = bpy.data.objects[BODY]
    before_slots = len(body.data.materials)
    edit = expand_group(body, ring_weights) if ring_weights else {"originalVertices": len(group_weights(body, body.vertex_groups[GROUP])), "rings": [], "finalVertices": len(group_weights(body, body.vertex_groups[GROUP])), "minimumWeight": 1.0, "maximumWeight": 1.0}
    hidden = hide_hair(scene)
    rendered = [
        render(scene, f"{label}-face-front", (0.0, -0.72, 1.430), (0.0, -0.060, 1.420), 88),
        render(scene, f"{label}-mouth-front", (0.0, -0.43, 1.388), (0.0, -0.120, 1.386), 135, (1200, 700)),
        render(scene, f"{label}-mouth-oblique", (0.21, -0.39, 1.392), (0.0, -0.115, 1.386), 128, (1200, 700)),
    ]
    for name in hidden:
        bpy.data.objects[name].hide_render = False
    variants.append({"label": label, "ringWeights": list(ring_weights), "edit": edit, "materialSlotsBefore": before_slots, "materialSlotsAfter": len(body.data.materials), "rendered": rendered, "status": "VISUAL_REVIEW_REQUIRED"})
    if label == SELECTED:
        scene["aevrynd_mainline_revision"] = "v249r1032-soft-lip-mask-boundary"
        scene["aevrynd_mainline_parent"] = SOURCE.name
        scene["aevrynd_release_state"] = "TECHNICAL_PASS_VISUAL_PARTIAL"
        scene["aevrynd_website_promotion"] = "forbidden"
        body["aevrynd_lip_mask_revision"] = "v249r1032"
        body["aevrynd_lip_mask_method"] = "one-ring topological expansion of named lips mask"
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "method": "topological rings around the existing named lips vertex group with bounded perioral filtering",
    "variants": variants,
    "provisionalSelection": SELECTED,
    "selectedVariant": SELECTED,
    "geometryChanged": False,
    "materialGraphChanged": False,
    "materialSlotDelta": 0,
    "websitePromotionApproved": False,
    "visualAssessment": "One neighbour ring softens the binary lip boundary. The two-ring falloff dyes surrounding skin and is rejected; the bright lower-rim line remains geometric.",
    "strictMouthScore": 38,
    "status": "TECHNICAL_PASS_VISUAL_PARTIAL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1032_LIP_MASK_BOUNDARY=" + json.dumps({"output": str(OUTPUT), "variants": [{"label": item["label"], "edit": item["edit"]} for item in variants]}, sort_keys=True))
