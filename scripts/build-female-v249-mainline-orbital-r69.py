from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
template_path = ROOT / "scripts/build-female-v249-mainline-orbital-r68.py"
template = template_path.read_text(encoding="utf-8")
replacements = (
    (
        'OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-orbital-r68.blend"',
        'OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-orbital-r69.blend"',
    ),
    (
        'OUT = ROOT.parent / "Temp/female-realism/v249-mainline-orbital-r68"',
        'OUT = ROOT.parent / "Temp/female-realism/v249-mainline-orbital-r69"',
    ),
    (
        'report = {"body": apply_sculpt(body), "strength_mm": STRENGTH_M * 1000.0}',
        '''sculpt_report = apply_sculpt(body)
optical_report = {}
for side in ("L", "R"):
    for part in ("Sclera", "Cornea", "Iris", "Pupil", "Catchlight"):
        optical = bpy.data.objects.get(f"Eye_{side}_{part}")
        if optical is None or optical.type != "MESH":
            continue
        optical.data = optical.data.copy()
        for vertex in optical.data.vertices:
            vertex.co.y += 0.00050
        optical.data.update()
        optical_report[optical.name] = {"additional_recess_mm": 0.50, "vertices": len(optical.data.vertices)}
report = {"body": sculpt_report, "strength_mm": STRENGTH_M * 1000.0, "optical_recess": optical_report}''',
    ),
    ('v249-mainline-orbital-r68', 'v249-mainline-orbital-r69'),
    ('"orbital-r68"', '"orbital-r69"'),
    ('R68_STRICT_VISUAL_AND_COLLISION_REVIEW_REQUIRED', 'R69_STRICT_VISUAL_AND_COLLISION_REVIEW_REQUIRED'),
    ('AEVRYND_V249_ORBITAL_R68=', 'AEVRYND_V249_ORBITAL_R69='),
)
for old, new in replacements:
    if old not in template:
        raise RuntimeError(f"orbital-r69 template token missing: {old}")
    template = template.replace(old, new)
exec(compile(template, str(template_path), "exec"))
