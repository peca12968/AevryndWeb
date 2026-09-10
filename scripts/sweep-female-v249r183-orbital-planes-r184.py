import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-guarded-anatomical-lids-r183.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r184-orbital-planes-sweep"
BODY = "AevryndFemaleBodyBaseV118"
EYES = {"L": (0.034528, 1.607765, 1.0), "R": (-0.034443, 1.607765, -1.0)}
VARIANTS = (
    ("a-control", 0.0),
    ("b-restrained", 0.68),
    ("c-balanced", 1.00),
    ("d-strong", 1.32),
)


def gaussian(value, center, sigma):
    return math.exp(-0.5 * ((value - center) / sigma) ** 2)


def smoothstep(edge0, edge1, value):
    value = max(0.0, min(1.0, (value - edge0) / (edge1 - edge0)))
    return value * value * (3.0 - 2.0 * value)


def is_hair(obj):
    layer = str(obj.get("aevrynd_layer", ""))
    lower = obj.name.lower()
    return layer.startswith("hair.") or any(token in lower for token in ("hair", "groom", "scalp"))


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def consolidate_final_surface(body, name):
    key = body.shape_key_add(name=name, from_mix=True)
    previous = [old.name for old in body.data.shape_keys.key_blocks[1:-1]]
    for old in body.data.shape_keys.key_blocks[1:-1]:
        old.value = 0.0
    key.value = 1.0
    return key, previous


def orbital_delta(p, strength):
    if p.y > -0.086 or not (1.558 < p.z < 1.654):
        return 0.0, None
    best = 0.0
    best_features = None
    for _side_name, (cx, cz, lateral_sign) in EYES.items():
        u = (p.x - cx) / 0.032
        if abs(u) >= 1.18:
            continue
        lateral_u = u * lateral_sign
        horizontal = smoothstep(1.18, 0.78, abs(u))
        horizontal = 0.20 * max(0.0, 1.0 - abs(u) / 1.18) + 0.80 * horizontal
        front = gaussian(p.y, -0.114, 0.018)

        # The eyebrow arch peaks lateral to the pupil.  Four broad bands form
        # a continuous orbital volume rather than engraved lid lines.
        arch = gaussian(lateral_u, 0.34, 0.52)
        brow_z = cz + 0.0250 + 0.0040 * arch - 0.0012 * gaussian(lateral_u, -0.78, 0.32)
        brow_ridge = gaussian(p.z, brow_z, 0.0042)
        upper_sulcus = gaussian(p.z, cz + 0.0120 + 0.0024 * arch, 0.0030)
        infraorbital_rim = gaussian(p.z, cz - 0.0140 - 0.0010 * arch, 0.0035)
        tear_trough = gaussian(p.z, cz - 0.0240, 0.0048) * (0.72 + 0.28 * gaussian(lateral_u, -0.35, 0.58))
        malar_support = gaussian(p.z, cz - 0.0370, 0.0100) * gaussian(lateral_u, 0.36, 0.72)

        # The camera faces negative Y: negative displacements project the
        # bony/fat pads, while positive displacements recess the sulci.
        delta_y = strength * horizontal * front * (
            -0.00130 * brow_ridge
            + 0.00115 * upper_sulcus
            - 0.00075 * infraorbital_rim
            + 0.00088 * tear_trough
            - 0.00115 * malar_support
        )
        if abs(delta_y) > abs(best):
            best = delta_y
            best_features = (brow_ridge, upper_sulcus, infraorbital_rim, tear_trough, malar_support)
    return best, best_features


def sculpt(key, strength):
    moved = 0
    maximum = 0.0
    feature_hits = {"brow_ridge": 0, "upper_sulcus": 0, "infraorbital_rim": 0, "tear_trough": 0, "malar_support": 0}
    for point in key.data:
        best, best_features = orbital_delta(point.co, strength)

        if abs(best) <= 0.000001:
            continue
        point.co.y += best
        moved += 1
        maximum = max(maximum, abs(best))
        for feature, value in zip(feature_hits, best_features):
            if value >= 0.35:
                feature_hits[feature] += 1
    return {
        "verticesMoved": moved,
        "maxMoveMm": maximum * 1000.0,
        "featureHits": feature_hits,
    }


def conform_brows(strength):
    report = {}
    for name in ("Brow_L", "Brow_L_Density", "Brow_R", "Brow_R_Density"):
        obj = bpy.data.objects[name]
        obj.data = obj.data.copy()
        world_to_local = obj.matrix_world.inverted().to_3x3()
        moved = 0
        maximum = 0.0
        for vertex in obj.data.vertices:
            world = obj.matrix_world @ vertex.co
            delta_y, _features = orbital_delta(world, strength)
            if delta_y >= -0.000001:
                continue
            # Follow the projected brow surface and retain a small air gap so
            # the independent fiber/density layers cannot be swallowed by it.
            displacement = Vector((0.0, delta_y - 0.00012 * strength, 0.0))
            vertex.co += world_to_local @ displacement
            moved += 1
            maximum = max(maximum, displacement.length)
        obj.data.update()
        report[name] = {"verticesMoved": moved, "maxMoveMm": maximum * 1000.0}
    return report


def render(camera, filename, location, target, lens, size):
    scene = bpy.context.scene
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.filepath = str(OUT / filename)
    bpy.ops.render.render(write_still=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {}
    for label, strength in VARIANTS:
        bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
        scene = bpy.context.scene
        scene.frame_set(1)
        scene.render.engine = "BLENDER_EEVEE"
        scene.render.resolution_percentage = 100
        scene.render.image_settings.file_format = "PNG"
        for obj in bpy.data.objects:
            if is_hair(obj):
                obj.hide_render = True
        body = bpy.data.objects[BODY]
        if strength:
            key, consolidated = consolidate_final_surface(body, f"Aevrynd_OrbitalPlanes_R184_{strength:.2f}")
            metrics = sculpt(key, strength)
            metrics["shapeKey"] = key.name
            metrics["consolidatedShapeKeys"] = consolidated
            metrics["browConformance"] = conform_brows(strength)
        else:
            metrics = {"verticesMoved": 0, "maxMoveMm": 0.0, "featureHits": {}}
        body.data.update()
        camera = bpy.data.objects["Aevrynd Review Camera"]
        render(camera, f"{label}-01-eyes-front.png", (0.0, -0.445, 1.611), (0.0, -0.076, 1.608), 132, (1280, 760))
        render(camera, f"{label}-02-left-eye-three-quarter.png", (0.225, -0.390, 1.628), (0.018, -0.080, 1.607), 138, (1100, 900))
        render(camera, f"{label}-03-face-front.png", (0.0, -0.555, 1.605), (0.0, -0.058, 1.604), 116, (1050, 1050))
        render(camera, f"{label}-04-face-profile.png", (0.56, -0.050, 1.612), (0.0, -0.030, 1.603), 108, (1050, 1050))
        report[label] = {"strength": strength, **metrics}
    report_path = ROOT / "assets-source/aevrynd-character/female-v249-mainline-orbital-planes-r184.sweep-report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("AEVRYND_V249_R184_ORBITAL_SWEEP=" + json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
