from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
template = (ROOT / "scripts/build-female-v249-mainline-skin-r24.py").read_text(encoding="utf-8")
replacements = (
    (
        'SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-eyelid-r23.blend"',
        'SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-r27.blend"',
    ),
    (
        'OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-skin-r24.blend"',
        'OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-skin-r29.blend"',
    ),
    (
        'OUT = ROOT.parent / "Temp/female-realism/v249-mainline-skin-r24"',
        'OUT = ROOT.parent / "Temp/female-realism/v249-mainline-skin-r29"',
    ),
    ('v249R24', 'v249R29'),
    ('V249R24', 'V249R29'),
    ('v249-mainline-skin-r24', 'v249-mainline-skin-r29'),
    ('"skin-r24"', '"skin-r29"'),
    ('pore.inputs["Scale"].default_value = 760.0', 'pore.inputs["Scale"].default_value = 520.0'),
    ('bump.inputs["Strength"].default_value = 0.105', 'bump.inputs["Strength"].default_value = 0.18'),
    ('bump.inputs["Distance"].default_value = 0.000028', 'bump.inputs["Distance"].default_value = 0.000085'),
    ('red = 1.0 + 0.085 * cheek', 'red = 1.0 + 0.115 * cheek'),
    ('green = 1.0 - 0.040 * cheek', 'green = 1.0 - 0.052 * cheek'),
    ('blue = 1.0 - 0.070 * cheek', 'blue = 1.0 - 0.090 * cheek'),
    ('"owned regional complexion and roughness fields plus restrained 760-scale pores"',
     '"owned regional complexion and roughness fields plus visible 520-scale pore relief"'),
    ('AEVRYND_V249_MAINLINE_SKIN_R24=', 'AEVRYND_V249_MAINLINE_SKIN_R29='),
)
for old, new in replacements:
    if old not in template:
        raise RuntimeError(f"skin-r29 template token missing: {old}")
    template = template.replace(old, new)
exec(compile(template, str(ROOT / "scripts/build-female-v249-mainline-skin-r24.py"), "exec"))
