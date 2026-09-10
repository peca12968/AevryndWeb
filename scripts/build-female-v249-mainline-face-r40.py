from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
template = (ROOT / "scripts/build-female-v249-mainline-face-r37.py").read_text(encoding="utf-8")
replacements = (
    ("face-r37.blend", "face-r40.blend"),
    ("v249-mainline-face-r37", "v249-mainline-face-r40"),
    ("FACE_R37_PENDING", "FACE_R40_PENDING"),
    (
        "if front < 0.002:\n            continue",
        "side_lower = gaussian(y, -0.015, 0.070) * gaussian(z, 1.490, 0.070)\n        if max(front, side_lower) < 0.002:\n            continue",
    ),
    (
        "jaw = gaussian(ax, 0.073, 0.026) * gaussian(z, 1.485, 0.034) * front",
        "jaw = gaussian(ax, 0.073, 0.027) * gaussian(z, 1.485, 0.038) * gaussian(y, -0.015, 0.060)",
    ),
    (
        "jaw_angle = gaussian(ax, 0.091, 0.017) * gaussian(z, 1.515, 0.028) * front",
        "jaw_angle = gaussian(ax, 0.091, 0.018) * gaussian(z, 1.515, 0.031) * gaussian(y, -0.010, 0.065)",
    ),
    (
        "chin_side = gaussian(ax, 0.043, 0.015) * gaussian(z, 1.476, 0.023) * front",
        "chin_side = gaussian(ax, 0.043, 0.016) * gaussian(z, 1.476, 0.026) * gaussian(y, -0.060, 0.055)",
    ),
    ("0.0032 * jaw + 0.0015 * jaw_angle", "0.0048 * jaw + 0.0030 * jaw_angle"),
    ("0.00105 * alar + 0.00045 * chin_side", "0.0028 * alar + 0.0015 * chin_side"),
    ("0.00165 * chin + 0.00075 * nose_tip + 0.00045 * bridge", "0.0032 * chin + 0.0022 * nose_tip + 0.0012 * bridge"),
    ("0.00085 * chin", "0.0018 * chin"),
    ("0.00020 * jaw", "0.00035 * jaw"),
    ("AEVRYND_V249_MAINLINE_FACE_R37=", "AEVRYND_V249_MAINLINE_FACE_R40="),
)
for old, new in replacements:
    if old not in template:
        raise RuntimeError(f"face-r40 template token missing: {old}")
    template = template.replace(old, new)
exec(compile(template, str(ROOT / "scripts/build-female-v249-mainline-face-r37.py"), "exec"))
