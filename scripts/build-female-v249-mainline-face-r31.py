from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
template = (ROOT / "scripts/build-female-v249-mainline-face-r30.py").read_text(encoding="utf-8")
replacements = (
    (
        'OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-face-r30.blend"',
        'OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-face-r31.blend"',
    ),
    (
        'OUT = ROOT.parent / "Temp/female-realism/v249-mainline-face-r30"',
        'OUT = ROOT.parent / "Temp/female-realism/v249-mainline-face-r31"',
    ),
    (
        '        if face < 0.002:\n            continue',
        '        if face < 0.002:\n            continue\n'
        '        eye_contact_guard = 0.012 < abs(x) < 0.088 and 1.582 < z < 1.648\n'
        '        lip_contact_guard = abs(x) < 0.066 and 1.500 < z < 1.548\n'
        '        if eye_contact_guard or lip_contact_guard:\n            continue',
    ),
    ('v249-mainline-face-r30', 'v249-mainline-face-r31'),
    ('"face-r30"', '"face-r31"'),
    ('AEVRYND_V249_MAINLINE_FACE_R30=', 'AEVRYND_V249_MAINLINE_FACE_R31='),
)
for old, new in replacements:
    if old not in template:
        raise RuntimeError(f"face-r31 template token missing: {old}")
    template = template.replace(old, new)
exec(compile(template, str(ROOT / "scripts/build-female-v249-mainline-face-r30.py"), "exec"))
