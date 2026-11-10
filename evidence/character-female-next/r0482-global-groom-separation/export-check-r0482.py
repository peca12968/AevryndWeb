from pathlib import Path
from runpy import run_path
import sys
ROOT=Path(__file__).resolve().parent
sys.argv=['blender','--','--source',str(ROOT/'female-next-r0482-global-groom-UNACCEPTED.blend'),'--out',str(ROOT/'portable-export-check')]
run_path(str(ROOT/'export-r0482.py'),run_name='__main__')