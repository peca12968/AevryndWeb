import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cc0-scalp-foundation-r101.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r101-periocular-topology-r106-sweep"
BODY = "AevryndFemaleBodyBaseV118"
EYES = {"L": (0.034528, -0.10087, 1.607765), "R": (-0.034443, -0.10077, 1.607765)}
VARIANTS = (
    ("a-control", 0.0),
    ("b-restrained", 0.72),
    ("c-balanced", 1.00),
    ("d-strong", 1.38),
)


def gaussian(value, center, sigma):
    return math.exp(-0.5 * ((value - center) / sigma) ** 2)


def smoothstep(edge0, edge1, value):
    value = max(0.0, min(1.0, (value - edge0) / (edge1 - edge0)))
    return value * value * (3.0 - 2.0 * value)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def is_hair(obj):
    layer = str(obj.get("aevrynd_layer", ""))
    lower = obj.name.lower()
    return layer.startswith("hair.") or any(token in lower for token in ("hair", "groom", "scalp"))


def mixed_coordinate(keys, index):
    basis = keys[0].data[index].co.copy()
    result = basis.copy()
    for key in keys[1:]:
        if key.value:
            relative = key.relative_key.data[index].co
            result += (key.data[index].co - relative) * key.value
    return result


def sculpt(body, strength):
    keys = body.data.shape_keys.key_blocks
    current = [mixed_coordinate(keys, index) for index in range(len(body.data.vertices))]
    key = body.shape_key_add(name=f"Aevrynd_Periocular_R106_{strength:.2f}", from_mix=False)
    moved = 0
    maximum = 0.0
    signed = {"recessed": 0, "projected": 0}
    feature_hits = {"upper_crease": 0, "tarsal_plate": 0, "lower_rim": 0, "tear_trough": 0}

    for index, point in enumerate(current):
        best_delta = 0.0
        best_features = None
        for side, (cx, _cy, cz) in EYES.items():
            lateral = 1.0 if side == "L" else -1.0
            u = (point.x - cx) / 0.01045
            if abs(u) >= 1.30 or not (-0.136 < point.y < -0.098):
                continue

            clipped_u = max(-1.0, min(1.0, u))
            arc = math.sqrt(max(0.0, 1.0 - clipped_u * clipped_u))
            tilt = lateral * 0.023 * (point.x - cx)
            upper_edge = cz + 0.00382 * arc + tilt
            lower_edge = cz - 0.00282 * arc + tilt
            end_guard = smoothstep(1.24, 0.86, abs(u))
            front = gaussian(point.y, -0.118, 0.0100)

            # Four separate anatomical bands follow the actual almond aperture.
            # Positive Y is a recess; negative Y projects skin toward camera.
            upper_crease_z = upper_edge + 0.0040 * (0.50 + 0.50 * arc)
            tarsal_z = upper_edge + 0.00165 * (0.55 + 0.45 * arc)
            lower_rim_z = lower_edge - 0.00145 * (0.65 + 0.35 * arc)
            trough_z = lower_edge - 0.0061 * (0.82 + 0.18 * arc)

            upper_crease = gaussian(point.z, upper_crease_z, 0.00072)
            tarsal_plate = gaussian(point.z, tarsal_z, 0.00092)
            lower_rim = gaussian(point.z, lower_rim_z, 0.00088)
            tear_trough = gaussian(point.z, trough_z, 0.00135)

            # The tear trough is strongest medially and centrally; the lid rolls
            # taper earlier so neither corner is pinched into a dark notch.
            medial = gaussian(u, -0.34, 0.58)
            plate_guard = smoothstep(1.08, 0.80, abs(u))
            trough_guard = smoothstep(1.22, 0.92, abs(u)) * (0.70 + 0.30 * medial)
            delta = strength * front * end_guard * (
                0.00128 * upper_crease
                - 0.00082 * tarsal_plate * plate_guard
                - 0.00058 * lower_rim * plate_guard
                + 0.00088 * tear_trough * trough_guard
            )
            if abs(delta) > abs(best_delta):
                best_delta = delta
                best_features = (upper_crease, tarsal_plate, lower_rim, tear_trough)

        if abs(best_delta) <= 0.000001:
            continue
        key.data[index].co.y += best_delta
        moved += 1
        maximum = max(maximum, abs(best_delta))
        signed["recessed" if best_delta > 0.0 else "projected"] += 1
        for name, value in zip(feature_hits, best_features):
            if value >= 0.35:
                feature_hits[name] += 1

    key.value = 1.0
    key.slider_min = 0.0
    key.slider_max = 1.0
    body.data.update()
    return {
        "shape_key": key.name,
        "strength": strength,
        "vertices_moved": moved,
        "maximum_displacement_mm": maximum * 1000.0,
        "signed_vertices": signed,
        "feature_hits": feature_hits,
    }


def render(camera, name, location, target, lens, resolution):
    scene = bpy.context.scene
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x = resolution[0]
    scene.render.resolution_y = resolution[1]
    scene.render.filepath = str(OUT / f"{name}.png")
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

        geometry = sculpt(bpy.data.objects[BODY], strength) if strength else {
            "strength": 0.0,
            "vertices_moved": 0,
            "maximum_displacement_mm": 0.0,
        }
        camera = bpy.data.objects["Aevrynd Review Camera"]
        render(camera, f"{label}-01-eyes-front", (0.0, -0.445, 1.611), (0.0, -0.076, 1.608), 132, (1280, 760))
        render(camera, f"{label}-02-left-eye-three-quarter", (0.225, -0.390, 1.628), (0.018, -0.080, 1.607), 138, (1100, 900))
        render(camera, f"{label}-03-face-front", (0.0, -0.555, 1.605), (0.0, -0.058, 1.604), 116, (1050, 1050))
        report[label] = geometry

    (OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("AEVRYND_V249_R101_PERIOCULAR_R106_SWEEP=" + json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
