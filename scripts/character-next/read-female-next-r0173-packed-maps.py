"""Read original packed bytes to identify actual source map semantics; no model save."""
from pathlib import Path
import bpy,json,hashlib,datetime
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');E=C/'evidence/character-female-next/r0173-artist-fibre-surface';d=json.loads((E/'before.json').read_text());bpy.ops.wm.open_mainfile(filepath=d['source']);rows=[]
for name in ['Image_0','Image_1']:
 im=bpy.data.images[name];raw=bytes(im.packed_file.data);ext='png' if raw.startswith(b'\x89PNG') else 'jpg';p=E/('actual-original-'+name+'.'+ext);assert not p.exists();p.write_bytes(raw);rows.append({'name':name,'file':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'originalColorspace':im.colorspace_settings.name,'packedBytesUnmodified':True})
(E/'actual-packed-map-bytes.json').write_bytes((json.dumps({'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'maps':rows},indent=2)+'\n').encode());print('R173_ORIGINAL_PACKED_MAP_BYTES_EXTRACTED',rows,flush=True)
