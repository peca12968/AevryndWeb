import json
from collections import defaultdict, deque
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-philtrum-r80.blend"
TOPOLOGY = ROOT / "assets-source/aevrynd-character/female-v249-mainline-eye-corners-r82.json"
OUT = ROOT.parent / "Temp/female-realism/v249-mainline-eye-corners-r82-sweep"
BODY = "AevryndFemaleBodyBaseV118"
VARIANTS = (("a-control", 0.0), ("b-restrained", 0.65), ("c-balanced", 1.0), ("d-strong", 1.4))


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def is_hair(obj):
    layer = str(obj.get("aevrynd_layer", ""))
    lower = obj.name.lower()
    return layer.startswith("hair.") or any(token in lower for token in ("hair", "groom", "scalp"))


def mesh_adjacency(mesh):
    adjacency = defaultdict(set)
    for edge in mesh.edges:
        first, second = edge.vertices
        adjacency[first].add(second)
        adjacency[second].add(first)
    return adjacency


def rings(adjacency, seed, maximum_distance=5):
    distance = {seed: 0}
    queue = deque([seed])
    while queue:
        current = queue.popleft()
        if distance[current] >= maximum_distance:
            continue
        for neighbor in adjacency[current]:
            if neighbor not in distance:
                distance[neighbor] = distance[current] + 1
                queue.append(neighbor)
    return distance


def sculpt_corners(body, strength):
    topology = json.loads(TOPOLOGY.read_text(encoding="utf-8"))
    adjacency = mesh_adjacency(body.data)
    key = body.shape_key_add(name=f"Aevrynd_EyeCorners_R82_{strength:.2f}", from_mix=False)
    accumulated = defaultdict(Vector)
    seeds = {}
    for side, info in topology["eyes"].items():
        lateral = 1.0 if side == "L" else -1.0
        seeds[side] = {}
        translations = {
            "inner": Vector((-lateral * 0.00034, 0.00010, -0.00020)),
            "outer": Vector((lateral * 0.00024, 0.00000, 0.00046)),
        }
        for label, translation in translations.items():
            seed = info["visible_surface_corners"][label]["index"]
            seeds[side][label] = seed
            for index, distance in rings(adjacency, seed).items():
                weight = (1.0 - distance / 6.0) ** 2
                accumulated[index] += translation * (strength * weight)
    maximum = 0.0
    for index, delta in accumulated.items():
        key.data[index].co += delta
        maximum = max(maximum, delta.length)
    key.value = 1.0
    key.slider_min = 0.0
    key.slider_max = 1.0
    return {
        "shape_key": key.name,
        "strength": strength,
        "moved_vertices": len(accumulated),
        "maximum_delta_mm": maximum * 1000.0,
        "seeds": seeds,
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
    for name, strength in VARIANTS:
        bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
        scene = bpy.context.scene
        scene.frame_set(1)
        scene.render.engine = "BLENDER_EEVEE"
        scene.render.resolution_x = scene.render.resolution_y = 1200
        scene.render.resolution_percentage = 100
        scene.render.image_settings.file_format = "PNG"
        for obj in bpy.data.objects:
            if is_hair(obj):
                obj.hide_render = True
        geometry = sculpt_corners(bpy.data.objects[BODY], strength) if strength else {
            "strength": 0.0, "moved_vertices": 0, "maximum_delta_mm": 0.0,
        }
        camera = bpy.data.objects["Aevrynd Review Camera"]
        render(camera, f"{name}-01-front", (0.0, -0.48, 1.610), (0.0, -0.065, 1.608), 122)
        render(camera, f"{name}-02-three-quarter", (0.38, -0.52, 1.625), (0.0, -0.025, 1.608), 108)
        report[name] = geometry
    (OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("AEVRYND_V249_EYE_CORNERS_R82_SWEEP=" + json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
