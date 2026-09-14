import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-sorted-tear-film-r499.blend"
REPORT = ASSETS / "female-v249-mainline-hair-macro-volume-r502.study.json"
RENDER_DIR = ASSETS / "reviews" / "v249r502-hair-macro-volume-sweep"
BODY = "AevryndFemaleBodyBaseV118"
REGIONS = ("front", "crown", "rear")
ALL_REGIONS = ("front", "crown", "rear", "hairline")
SOLIDS = (BODY, "Clothing_Bandeau_v160", "Clothing_BandeauBinding_v162", "Clothing_BodyFitShorts_v135")
POINTS = 24
STRIDE = POINTS * 2
PENETRATION_LIMIT = -0.0005
VARIANTS = (
    ("a-r499-current", 0.0),
    ("b-volume-2mm", 0.002),
    ("c-volume-5mm", 0.005),
    ("d-volume-8mm", 0.008),
)


def smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def card_center(obj, card, row):
    base = card * STRIDE + row * 2
    return (obj.data.vertices[base].co + obj.data.vertices[base + 1].co) * 0.5


def group_phase(root, region):
    x_group = round(root.x / 0.018)
    y_group = round((root.y + 0.01) / 0.018)
    region_offset = {"front": 0.7, "crown": 2.3, "rear": 4.9}[region]
    return x_group * 1.731 + y_group * 2.417 + region_offset


def add_macro_volume(obj, region, amplitude):
    cards = int(obj.get("aevrynd_card_count", 0))
    if len(obj.data.vertices) != cards * STRIDE:
        raise RuntimeError(f"Unexpected runtime-card layout on {obj.name}")
    maximum = 0.0
    root_maximum = 0.0
    region_scale = {"front": 1.0, "crown": 0.72, "rear": 1.0}[region]
    for card in range(cards):
        root = card_center(obj, card, 0)
        phase = group_phase(root, region)
        for row in range(POINTS):
            t = row / (POINTS - 1)
            center = card_center(obj, card, row)
            radial = Vector((center.x, center.y + 0.012, 0.0))
            if radial.length < 1e-8:
                radial = Vector((0.0, -1.0, 0.0))
            radial.normalize()
            tangent = Vector((-radial.y, radial.x, 0.0))
            middle = math.sin(math.pi * t) ** 2
            tail = smoothstep((t - 0.38) / 0.62)
            root_guard = smoothstep(t / 0.16)
            outward_amount = amplitude * region_scale * (0.42 + 0.24 * (0.5 + 0.5 * math.sin(phase))) * (0.72 * middle + 0.34 * tail)
            lateral_amount = amplitude * region_scale * 0.58 * math.sin(phase * 1.13 + 0.4) * (middle + 0.42 * tail)
            vertical_amount = amplitude * region_scale * 0.30 * math.sin(phase * 0.79 + 1.1) * middle
            offset = (radial * outward_amount + tangent * lateral_amount + Vector((0.0, 0.0, vertical_amount))) * root_guard
            maximum = max(maximum, offset.length)
            if row == 0:
                root_maximum = max(root_maximum, offset.length)
            base = card * STRIDE + row * 2
            obj.data.vertices[base].co += offset
            obj.data.vertices[base + 1].co += offset
    obj.data.update()
    obj["aevrynd_revision"] = "v249r502-hair-macro-volume-study"
    obj["aevrynd_macro_volume_amplitude_m"] = amplitude
    obj["aevrynd_macro_volume_max_displacement_m"] = maximum
    return {"cards": cards, "maximumDisplacementM": maximum, "maximumRootDisplacementM": root_maximum}


def geometry(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    evaluated.to_mesh_clear()
    return points, faces


def tree(obj, depsgraph):
    points, faces = geometry(obj, depsgraph)
    return BVHTree.FromPolygons(points, faces, all_triangles=False)


def collision_snapshot(scene):
    result = {}
    for frame in (1, 20, 33, 61):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        solid_trees = {name: tree(bpy.data.objects[name], depsgraph) for name in SOLIDS}
        frame_report = {}
        for region in ALL_REGIONS:
            name = f"AevryndFemaleRuntimeCards_{region}_R467"
            evaluated = bpy.data.objects[name].evaluated_get(depsgraph)
            points = [evaluated.matrix_world @ vertex.co for vertex in evaluated.data.vertices]
            frame_report[region] = {}
            for solid, solid_tree in solid_trees.items():
                signed = []
                for point in points:
                    hit = solid_tree.find_nearest(point, 0.025)
                    if hit is not None and hit[1] is not None:
                        signed.append((point - hit[0]).dot(hit[1].normalized()))
                frame_report[region][solid] = {
                    "nearSamples": len(signed),
                    "minimumSignedM": min(signed) if signed else None,
                    "penetratingVertices": sum(value < PENETRATION_LIMIT for value in signed),
                }
        result[str(frame)] = frame_report
    return result


def collision_pass(snapshot):
    return all(
        value["penetratingVertices"] == 0
        for frame in snapshot.values()
        for region in frame.values()
        for value in region.values()
    )


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, camera, frame, name, location, target, lens):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x = scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)


RENDER_DIR.mkdir(parents=True, exist_ok=True)
report = {"source": str(SOURCE), "variants": {}, "renderDirectory": str(RENDER_DIR)}
for label, amplitude in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0.0
    scene.render.image_settings.file_format = "PNG"
    changes = {}
    if amplitude:
        for region in REGIONS:
            changes[region] = add_macro_volume(bpy.data.objects[f"AevryndFemaleRuntimeCards_{region}_R467"], region, amplitude)
    snapshot = collision_snapshot(scene)
    camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
    scene.camera = camera
    for values in (
        (1, label + "-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
        (1, label + "-three-quarter", (0.45, -0.66, 1.60), (0.0, -0.005, 1.56), 84),
        (1, label + "-back", (0.0, 0.90, 1.59), (0.0, 0.0, 1.56), 82),
        (1, label + "-top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
        (33, label + "-motion-front", (0.0, -0.76, 1.58), (0.0, -0.015, 1.56), 84),
    ):
        render(scene, camera, *values)
    report["variants"][label] = {
        "amplitudeM": amplitude,
        "changes": changes,
        "collision": snapshot,
        "collisionStatus": "PASS" if collision_pass(snapshot) else "FAIL",
    }
report["visualAssessment"] = {"status": "REJECTED", "reason": "The collision-safe 2 mm bound is visually negligible; visible 5/8 mm bounds penetrate the body during motion.", "promotion": None}
report["status"] = "REJECTED_VISUAL_AND_COLLISION_GATE"
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R502_HAIR_MACRO_VOLUME=" + json.dumps({label: value["collisionStatus"] for label, value in report["variants"].items()}, sort_keys=True))
