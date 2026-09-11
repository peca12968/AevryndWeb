import bpy
from mathutils import Vector


bpy.ops.wm.open_mainfile(
    filepath=r"D:\Download\Aevrynd\sites-engine-journey\assets-source\aevrynd-character\aevrynd-female-authoring-v249-mainline-continuous-crown-field-r383.blend"
)
body = bpy.data.objects["AevryndFemaleBody_CC0_R249"]
world = [body.matrix_world @ vertex.co for vertex in body.data.vertices]
print("BODY_BOUNDS", tuple(min(point[i] for point in world) for i in range(3)), tuple(max(point[i] for point in world) for i in range(3)))
for name in (
    "AevryndFemaleHairlineTransition_R383",
    "AevryndFemaleFrontSurfaceFlow_R383",
    "AevryndFemaleCrownSurfaceFlow_R383",
    "AevryndFemaleRearSurfaceFlow_R383",
):
    obj = bpy.data.objects[name]
    roots = [obj.matrix_world @ obj.data.points[index].position for index in range(0, len(obj.data.points), 24)]
    print(
        "ROOT_BOUNDS", name, len(roots),
        tuple(round(min(point[i] for point in roots), 6) for i in range(3)),
        tuple(round(max(point[i] for point in roots), 6) for i in range(3)),
    )
    if "HairlineTransition" in name:
        rows = []
        for curve in range(len(obj.data.points) // 24):
            root = obj.matrix_world @ obj.data.points[curve * 24].position
            tip = obj.matrix_world @ obj.data.points[curve * 24 + 23].position
            rows.append((root.x, root, tip))
        for _x, root, tip in sorted(rows, key=lambda row: row[0])[::12]:
            print("HAIRLINE_SAMPLE", tuple(round(v, 5) for v in root), tuple(round(v, 5) for v in tip))
