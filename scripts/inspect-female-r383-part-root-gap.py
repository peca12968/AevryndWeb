from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-continuous-crown-field-r383.blend"
POINTS = 24
OBJECTS = (
    "AevryndFemaleFrontSurfaceFlow_R383",
    "AevryndFemaleCrownSurfaceFlow_R383",
    "AevryndFemaleRearSurfaceFlow_R383",
)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
for name in OBJECTS:
    obj = bpy.data.objects[name]
    roots = [obj.matrix_world @ obj.data.points[index].position for index in range(0, len(obj.data.points), POINTS)]
    abs_x = sorted(abs(point.x) for point in roots)
    quantiles = [abs_x[round((len(abs_x) - 1) * q)] for q in (0.0, 0.01, 0.05, 0.1, 0.25, 0.5)]
    print(f"{name}: curves={len(roots)} absRootX=" + ",".join(f"{value:.6f}" for value in quantiles))
    for y0, y1 in ((-0.14, -0.08), (-0.08, -0.02), (-0.02, 0.04), (0.04, 0.10), (0.10, 0.16)):
        band = [abs(point.x) for point in roots if y0 <= point.y < y1]
        if band:
            print(f"  y[{y0:.2f},{y1:.2f}): count={len(band)} minAbsX={min(band):.6f} p10={sorted(band)[round((len(band)-1)*0.1)]:.6f}")
