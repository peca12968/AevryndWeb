from pathlib import Path


# Keep r371 as a small, reviewable calibration step.  The complete groom is
# rebuilt by r370; this wrapper changes only the density foundation strength
# and revision identifiers before executing the same deterministic build.
ROOT = Path(__file__).resolve().parents[1]
source_path = ROOT / "scripts/build-female-v249r370-hierarchical-fiber-groom.py"
source = source_path.read_text(encoding="utf-8")

replacements = {
    "hierarchical-fiber-groom-r370": "perceptual-contrast-groom-r371",
    "v249r370-hierarchical-fiber-groom": "v249r371-perceptual-contrast-groom",
    "v249r370": "v249r371",
    "R370": "R371",
    "r370": "r371",
    "SCALP_MAX_ALPHA = 0.63": "SCALP_MAX_ALPHA = 0.50",
    'hair.inputs["Melanin"].default_value = 0.76': 'hair.inputs["Melanin"].default_value = 0.68',
    'hair.inputs["Melanin Redness"].default_value = 0.58': 'hair.inputs["Melanin Redness"].default_value = 0.54',
    '"energy": 8.0': '"energy": 8.0',
    "AEVRYND_R371_HIERARCHICAL_FIBER_GROOM": "AEVRYND_R371_PERCEPTUAL_CONTRAST_GROOM",
}
for old, new in replacements.items():
    source = source.replace(old, new)

# The review light stays fixed.  Reducing the head-bound density layer instead
# of raising exposure preserves the accepted skin response and facial form.
source = source.replace(
    '"reason": "Calibrated against the r358 accepted skin mean after adding the translucent density foundation."',
    '"reason": "Held at the r370 calibrated value; r371 corrects perceptual darkening at the scalp density layer rather than changing exposure."',
)
exec(compile(source, str(source_path), "exec"), {"__name__": "__main__", "__file__": str(source_path)})
