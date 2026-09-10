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
        'OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-face-r49.blend"',
    ),
    (
        'OUT = ROOT.parent / "Temp/female-realism/v249-mainline-eyelid-r23"',
        'OUT = ROOT.parent / "Temp/female-realism/v249-mainline-face-r49"',
    ),
    ('v249-mainline-eyelid-r23', 'v249-mainline-face-r49'),
    ('"eyelid-r23"', '"face-r49"'),
    ('AEVRYND_V249_MAINLINE_EYELID_R23=', 'AEVRYND_V249_MAINLINE_FACE_R49='),
)
for old, new in replacements:
    if old not in template:
        raise RuntimeError(f"face-r49 template token missing: {old}")
    template = template.replace(old, new)
exec(compile(template, str(ROOT / "scripts/build-female-v249-mainline-eyelid-wrap-r23.py"), "exec"))
