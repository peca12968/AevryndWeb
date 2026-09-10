from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
template = (ROOT / "scripts/build-female-v249-mainline-eyelid-wrap-r23.py").read_text(encoding="utf-8")
replacements = (
    (
        'SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-r17.blend"',
        'SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-face-r38.blend"',
    ),
    (
        'OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-eyelid-r23.blend"',
        'OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-face-r51.blend"',
    ),
    (
        'OUT = ROOT.parent / "Temp/female-realism/v249-mainline-eyelid-r23"',
        'OUT = ROOT.parent / "Temp/female-realism/v249-mainline-face-r51"',
    ),
    ('STRENGTH_M = 0.0025', 'STRENGTH_M = 0.0024'),
    ('STRENGTH_M * (-0.58 * upper + 0.30 * lower)', 'STRENGTH_M * (0.0 * upper + 0.0 * lower)'),
    ('delta.z += STRENGTH_M * 0.13 * outer * horizontal * front', 'delta.z += STRENGTH_M * 0.03 * outer * horizontal * front'),
    ('delta.y -= 0.00022', 'delta.y -= 0.00018'),
    ('recess = 0.0006', 'recess = 0.0004'),
    ('0.6mm optical recess', '0.4mm optical recess'),
    ('v249-mainline-eyelid-r23', 'v249-mainline-face-r51'),
    ('"eyelid-r23"', '"face-r51"'),
    ('AEVRYND_V249_MAINLINE_EYELID_R23=', 'AEVRYND_V249_MAINLINE_FACE_R51='),
)
for old, new in replacements:
    if old not in template:
        raise RuntimeError(f"face-r51 template token missing: {old}")
    template = template.replace(old, new)
exec(compile(template, str(ROOT / "scripts/build-female-v249-mainline-eyelid-wrap-r23.py"), "exec"))
