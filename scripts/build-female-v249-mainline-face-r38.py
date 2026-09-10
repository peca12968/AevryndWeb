from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
template = (ROOT / "scripts/build-female-v249-mainline-face-r37.py").read_text(encoding="utf-8")
replacements = (
    ("face-r37.blend", "face-r38.blend"),
    ("v249-mainline-face-r37", "v249-mainline-face-r38"),
    ("FACE_R37_PENDING", "FACE_R38_PENDING"),
    ("0.0032 * jaw + 0.0015 * jaw_angle", "0.0090 * jaw + 0.0050 * jaw_angle"),
    ("0.00105 * alar + 0.00045 * chin_side", "0.0028 * alar + 0.0018 * chin_side"),
    ("0.00165 * chin + 0.00075 * nose_tip + 0.00045 * bridge", "0.0045 * chin + 0.0022 * nose_tip + 0.0012 * bridge"),
    ("0.00085 * chin", "0.0024 * chin"),
    ("0.00020 * jaw", "0.00045 * jaw"),
    ("AEVRYND_V249_MAINLINE_FACE_R37=", "AEVRYND_V249_MAINLINE_FACE_R38="),
)
for old, new in replacements:
    if old not in template:
        raise RuntimeError(f"face-r38 template token missing: {old}")
    template = template.replace(old, new)
exec(compile(template, str(ROOT / "scripts/build-female-v249-mainline-face-r37.py"), "exec"))
