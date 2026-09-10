import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249.blend"
OUT = ROOT.parent / "Temp/female-realism/eyelid-structure-strong-sweep-v249"


def gaussian(value, center, sigma):
    return math.exp(-0.5 * ((value - center) / sigma) ** 2)


def apply(body, base, strength):
    moved = 0
    maximum = 0.0
    for vertex, coordinate in zip(body.data.vertices, base):
        vertex.co = coordinate
    body.data.update()
    normals = [vertex.normal.copy() for vertex in body.data.vertices]
    for vertex, p, normal in zip(body.data.vertices, base, normals):
        if p.y > -0.096 or not (1.585 < p.z < 1.632):
            continue
        delta = Vector()
        for cx in (-0.035, 0.035):
            dx = (p.x - cx) / 0.031
            if abs(dx) >= 1.15:
                continue
            horizontal = max(0.0, 1.0 - (dx / 1.15) ** 2) ** 1.7
            front = gaussian(p.y, -0.126, 0.025)
            upper_margin = horizontal * front * gaussian(p.z, 1.6100, 0.0040)
            lower_margin = horizontal * front * gaussian(p.z, 1.5988, 0.0042)
            fold = horizontal * front * gaussian(p.z, 1.6190, 0.0031)
            fold_ridge = horizontal * front * gaussian(p.z, 1.6242, 0.0030)
            lower_roll = horizontal * front * gaussian(p.z, 1.5948, 0.0044)
            # Slightly close the aperture and give the upper lid a soft fold.
            delta.z += strength * (-0.00034 * upper_margin + 0.00016 * lower_margin)
            delta += normal * strength * (-0.00042 * fold + 0.00018 * fold_ridge + 0.00022 * lower_roll)
            # Raise the outer canthus by at most 0.18 mm without changing width.
            outer = dx * (1.0 if cx > 0.0 else -1.0)
            corner = horizontal * front * gaussian(abs(dx), 0.91, 0.18)
            delta.z += strength * 0.00018 * max(0.0, outer) * corner
        if delta.length > 0.000001:
            vertex.co += delta
            moved += 1
            maximum = max(maximum, delta.length)
    body.data.update()
    return moved, maximum * 1000.0


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, location, target, lens):
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = scene.render.resolution_y = 1100
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(OUT / f"{name}.png")
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
OUT.mkdir(parents=True, exist_ok=True)
body = bpy.data.objects["AevryndFemaleBodyBaseV118"]
base = [vertex.co.copy() for vertex in body.data.vertices]
camera = bpy.data.objects["Aevrynd Review Camera"]
for label, strength in (("250", 2.50), ("400", 4.00), ("550", 5.50)):
    report = apply(body, base, strength)
    render(camera, f"eye-close-{label}", (0.0, -0.47, 1.610), (0.0, -0.065, 1.608), 112)
    render(camera, f"face-three-quarter-{label}", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88)
    print("EYELID", label, report)

