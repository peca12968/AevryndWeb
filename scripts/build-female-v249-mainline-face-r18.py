import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-r17.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-face-r18.blend"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249-mainline-face-r18"
BODY_NAME = "AevryndFemaleBodyBaseV118"


def gaussian(value, center, sigma):
    return math.exp(-0.5 * ((value - center) / sigma) ** 2)


def sculpt_upper_orbit(body):
    base = [vertex.co.copy() for vertex in body.data.vertices]
    body.data.update()
    normals = [vertex.normal.copy() for vertex in body.data.vertices]
    moved = 0
    maximum = 0.0

    # v254 proved this region collision-safe, but its 1.35 strength read as a
    # continuous dark stripe. r18 keeps the same v249 topology and uses a much
    # softer anatomical transition: a shallow lid fold plus brow-pad support.
    strength = 0.48
    for vertex, point, normal in zip(body.data.vertices, base, normals):
        if point.y > -0.093 or not (1.6145 < point.z < 1.641):
            continue
        displacement = Vector()
        for center_x in (-0.035, 0.035):
            dx = (point.x - center_x) / 0.031
            if abs(dx) >= 1.12:
                continue
            horizontal = max(0.0, 1.0 - (dx / 1.12) ** 2) ** 2.2
            front = gaussian(point.y, -0.121, 0.026)
            arch = 1.6205 + 0.0030 * max(0.0, 1.0 - dx * dx)
            fold = horizontal * front * gaussian(point.z, arch, 0.00215)
            brow_pad = horizontal * front * gaussian(point.z, arch + 0.0058, 0.0031)
            outer = max(0.0, abs(dx) - 0.58) / 0.54
            brow_pad *= 0.86 + 0.14 * outer
            displacement += normal * strength * (-0.00082 * fold + 0.00042 * brow_pad)
        if displacement.length > 0.000001:
            vertex.co += displacement
            moved += 1
            maximum = max(maximum, displacement.length)

    body.data.update()
    return {"moved_vertices": moved, "max_displacement_mm": maximum * 1000.0}


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, location, target, lens):
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1100
    scene.render.resolution_y = 1100
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
RENDER_DIR.mkdir(parents=True, exist_ok=True)
body = bpy.data.objects[BODY_NAME]
report = sculpt_upper_orbit(body)
body["aevrynd_mainline_baseline"] = "v249"
body["aevrynd_face_revision"] = "v249-mainline-face-r18"
body["aevrynd_face_change"] = "subtle_upper_orbit_transition"
bpy.context.scene["aevrynd_mainline_baseline"] = "v249"
bpy.context.scene["aevrynd_mainline_parent"] = SOURCE.name
bpy.context.scene["aevrynd_mainline_revision"] = "face-r18"
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

camera = bpy.data.objects["Aevrynd Review Camera"]
render(camera, "01-face-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88)
render(camera, "02-eye-close", (0.0, -0.47, 1.610), (0.0, -0.065, 1.608), 112)
render(camera, "03-face-three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88)
print("AEVRYND_V249_MAINLINE_FACE_R18=", report)
