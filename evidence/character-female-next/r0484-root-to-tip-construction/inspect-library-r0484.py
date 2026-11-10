from pathlib import Path
import json
import bpy
ROOT=Path(__file__).resolve().parent
path=ROOT.parent/'r0480-lock-clearance-projection/female-next-r0480-lock-clearance-projection-UNACCEPTED.blend'
with bpy.data.libraries.load(str(path),link=False) as (source,target):
    inventory={key:list(getattr(source,key)) for key in ('objects','scenes','collections','materials','images','armatures')}
(ROOT/'r480-library-inventory.json').write_bytes(json.dumps(inventory,indent=2).encode('utf8'))
print(json.dumps(inventory,indent=2),flush=True)
