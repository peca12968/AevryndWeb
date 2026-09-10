import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-eyelid-r78.blend"
OUT = ROOT.parent / "Temp/female-realism/v249-mainline-philtrum-r80-sweep"
BODY = "AevryndFemaleBodyBaseV118"
VARIANTS = (
    ("a-control", 0, 0.0),
    ("b-restrained", 3, 0.22),
    ("c-balanced", 5, 0.30),
    ("d-strong", 7, 0.38),
    ("e-deep", 12, 0.45),
    ("f-limit", 20, 0.50),
)


def smoothstep(edge0, edge1, value):
    value = max(0.0, min(1.0, (value - edge0) / (edge1 - edge0)))
    return value * value * (3.0 - 2.0 * value)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def is_hair(obj):
    layer = str(obj.get("aevrynd_layer", ""))
    lower = obj.name.lower()
    return layer.startswith("hair.") or any(token in lower for token in ("hair", "groom", "scalp"))


def region_weight(point):
    ax = abs(point.x)
    if ax >= 0.024 or not (1.532 < point.z < 1.555) or not (-0.160 < point.y < -0.105):
        return 0.0
    side = smoothstep(0.024, 0.014, ax)
    lower = smoothstep(1.532, 1.538, point.z)
    upper = smoothstep(1.555, 1.548, point.z)
    return side * lower * upper


def topology_smooth(body, iterations, factor):
    vertices = body.data.vertices
    adjacency = [[] for _ in vertices]
    for edge in body.data.edges:
        first, second = edge.vertices
        adjacency[first].append(second)
        adjacency[second].append(first)
    original_y = [vertex.co.y for vertex in vertices]
    weights = [region_weight(vertex.co) for vertex in vertices]
    active = [index for index, weight in enumerate(weights) if weight > 0.0]
    for _iteration in range(iterations):
        current_y = [vertex.co.y for vertex in vertices]
        updates = {}
        for index in active:
            neighbors = adjacency[index]
            if not neighbors:
                continue
            average = sum(current_y[other] for other in neighbors) / len(neighbors)
            updates[index] = current_y[index] + (average - current_y[index]) * factor * weights[index]
        for index, value in updates.items():
            vertices[index].co.y = value
    body.data.update()
    deltas = [abs(vertices[index].co.y - original_y[index]) for index in active]
    return {
        "active_vertices": len(active),
        "iterations": iterations,
        "factor": factor,
        "maximum_delta_mm": max(deltas, default=0.0) * 1000.0,
        "mean_delta_mm": (sum(deltas) / len(deltas) if deltas else 0.0) * 1000.0,
    }


def render(camera, name, location, target, lens):
    scene = bpy.context.scene
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {}
    for name, iterations, factor in VARIANTS:
        bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
        scene = bpy.context.scene
        scene.frame_set(1)
        scene.render.engine = "BLENDER_EEVEE"
        scene.render.resolution_x = scene.render.resolution_y = 1100
        scene.render.resolution_percentage = 100
        scene.render.image_settings.file_format = "PNG"
        for obj in bpy.data.objects:
            if is_hair(obj):
                obj.hide_render = True
        geometry = topology_smooth(bpy.data.objects[BODY], iterations, factor)
        camera = bpy.data.objects["Aevrynd Review Camera"]
        render(camera, f"{name}-01-front", (0.0, -0.50, 1.555), (0.0, -0.070, 1.545), 118)
        render(camera, f"{name}-02-three-quarter", (0.32, -0.50, 1.58), (0.0, -0.035, 1.550), 110)
        render(camera, f"{name}-03-profile", (0.62, -0.03, 1.57), (0.0, -0.010, 1.545), 100)
        report[name] = geometry
    (OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("AEVRYND_V249_PHILTRUM_R80_SWEEP=" + json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
