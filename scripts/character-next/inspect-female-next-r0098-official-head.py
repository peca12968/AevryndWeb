"""Inventory existing official CC0 artist source; no source scripts executed."""
from pathlib import Path
import bpy,json,hashlib
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0098-whole-head-foundation';P=R/'Reference/character/blender-human-base-meshes-v1.4.1/human-base-meshes-bundle-v1.4.1/human_base_meshes_bundle.blend'
with bpy.data.libraries.load(str(P),link=False) as (a,b):
 row={'source':str(P),'sourceSha256':hashlib.sha256(P.read_bytes()).hexdigest(),'objects':list(a.objects),'collections':list(a.collections),'texts':list(a.texts)};b.texts=a.texts
row['sourceTextContents']={t.name:t.as_string() for t in b.texts if t is not None};(E/'official-source-inventory.json').write_text(json.dumps(row,indent=2)+'\n',encoding='utf8');print(json.dumps(row,indent=2),flush=True)
