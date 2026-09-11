from pathlib import Path


# Reuse the established r370 point-to-body audit with only the candidate and
# object revision names changed.  This keeps its penetration threshold and the
# frame 1/frame 20 comparison identical.
ROOT = Path(__file__).resolve().parents[1]
source_path = ROOT / "scripts/audit-female-v249r370-hair-collision.py"
source = source_path.read_text(encoding="utf-8")
for old, new in (
    ("hierarchical-fiber-groom-r370", "perceptual-contrast-groom-r371"),
    ("female-v249-mainline-r370.hair-collision-audit.json", "female-v249-mainline-r371.hair-collision-audit.json"),
    ("R370", "R371"),
    ("r370", "r371"),
):
    source = source.replace(old, new)
exec(compile(source, str(source_path), "exec"), {"__name__": "__main__", "__file__": str(source_path)})
