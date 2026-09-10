import math
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249.blend"
OUT = ROOT.parent / "Temp/female-realism/supraorbital-sweep-v249"


def gaussian(value, center, sigma):
    return math.exp(-0.5 * ((value - center) / sigma) ** 2)


def apply(body, base, strength):
    for vertex, coordinate in zip(body.data.vertices, base):
        vertex.co = coordinate
    body.data.update()
    normals = [vertex.normal.copy() for vertex in body.data.vertices]
    moved = 0
    maximum = 0.0
    for vertex, p, normal in zip(body.data.vertices, base, normals):
        if p.y > -0.093 or not (1.6145 < p.z < 1.641):
            continue
        delta = Vector()
        for cx in (-0.035, 0.035):
            dx = (p.x - cx) / 0.031
            if abs(dx) >= 1.12:
                continue
            horizontal = max(0.0, 1.0 - (dx / 1.12) ** 2) ** 1.8
            front = gaussian(p.y, -0.121, 0.026)
            arch = 1.6205 + 0.0030 * max(0.0, 1.0 - dx * dx)
            crease = horizontal * front * gaussian(p.z, arch, 0.00175)
            ridge = horizontal * front * gaussian(p.z, arch + 0.0054, 0.00235)
            outer_pad = max(0.0, abs(dx) - 0.55) / 0.57
            ridge *= 0.88 + 0.20 * outer_pad
            delta += normal * strength * (-0.00105 * crease + 0.00052 * ridge)
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
for label, strength in (("075", 0.75), ("100", 1.00), ("135", 1.35)):
    report = apply(body, base, strength)
    render(camera, f"eye-close-{label}", (0.0, -0.47, 1.610), (0.0, -0.065, 1.608), 112)
    render(camera, f"face-three-quarter-{label}", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88)
    print("SUPRAORBITAL", label, report)
