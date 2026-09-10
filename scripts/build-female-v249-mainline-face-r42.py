from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
template = (ROOT / "scripts/build-female-v249-mainline-face-r37.py").read_text(encoding="utf-8")
replacements = (
    ("face-r37.blend", "face-r42.blend"),
    ("v249-mainline-face-r37", "v249-mainline-face-r42"),
    ("FACE_R37_PENDING", "FACE_R42_PENDING"),
    (
        "if front < 0.002:\n            continue",
        "side_lower = gaussian(y, -0.055, 0.040) * gaussian(z, 1.505, 0.055)\n        if y > -0.028 or max(front, side_lower) < 0.002:\n            continue",
    ),
    (
        "jaw = gaussian(ax, 0.073, 0.026) * gaussian(z, 1.485, 0.034) * front",
        "jaw = gaussian(ax, 0.073, 0.027) * gaussian(z, 1.500, 0.035) * gaussian(y, -0.055, 0.032)",
    ),
    (
        "jaw_angle = gaussian(ax, 0.091, 0.017) * gaussian(z, 1.515, 0.028) * front",
        "jaw_angle = gaussian(ax, 0.091, 0.018) * gaussian(z, 1.515, 0.030) * gaussian(y, -0.050, 0.032)",
    ),
    (
        "chin_side = gaussian(ax, 0.043, 0.015) * gaussian(z, 1.476, 0.023) * front",
        "chin_side = gaussian(ax, 0.043, 0.016) * gaussian(z, 1.476, 0.026) * gaussian(y, -0.075, 0.040)",
    ),
    ("0.0032 * jaw + 0.0015 * jaw_angle", "0.0060 * jaw + 0.0035 * jaw_angle"),
    ("0.00105 * alar + 0.00045 * chin_side", "0.0028 * alar + 0.0015 * chin_side"),
    ("0.00165 * chin + 0.00075 * nose_tip + 0.00045 * bridge", "0.0032 * chin + 0.0022 * nose_tip + 0.0012 * bridge"),
    ("0.00085 * chin", "0.0018 * chin"),
    ("0.00020 * jaw", "0.00035 * jaw"),
    ("AEVRYND_V249_MAINLINE_FACE_R37=", "AEVRYND_V249_MAINLINE_FACE_R42="),
)
for old, new in replacements:
    if old not in template:
        raise RuntimeError(f"face-r42 template token missing: {old}")
    template = template.replace(old, new)
exec(compile(template, str(ROOT / "scripts/build-female-v249-mainline-face-r37.py"), "exec"))
