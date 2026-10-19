"""Pinned data-only hair library; never install or execute embedded code."""
from pathlib import Path
from datetime import datetime,timezone
import json,urllib.request,hashlib,time
R=Path(r'D:\Download\Aevrynd');D=R/'Reference/character/charmorph-vitruvian-cc0';E=R/'Evidence/character-female-next/r0058-source-emitter';E.mkdir(parents=True,exist_ok=True)
REV='c252d1fc7f00ba59d87b66b3d32fa3471fc6ee44';REL='hair.blend';tick=time.time()
contract={'revision':'female-next-r0058','startUTC':datetime.now(timezone.utc).isoformat(),'previousGoalTurnClassification':'progress: r56/r57 reconciled, actual full views audited, portable r57D retained with failed head-hair contacts, no model adoption.','source':'r57D coherent female foundation, unchanged r51 fallback','reference':'Pinned original CC0 Vitruvian hair.blend + config.yaml, actual source emitter rather than assumed NPZ/body compatibility.','expectedVisibleChange':'A natural complete head hairstyle whose paths/follicles originate on the actual compatible source emitter; otherwise explicit rejection before children.','minimumTest':'Inspect actual native library emitter and evaluated authored Bob data, compare source pose/topology and roots before a single complete-head/body preview.','reject':'Emitter compatibility cannot be established, paths are already invalid, or full hairstyle shape remains implausible. No nearest-root fitting or density/parameter sweeps.','resourceLimit':'One heavy job, max4threads; first diagnosis bounded10minutes, first full preview or method rejection before45minute checkpoint; no addon/other app installation.','candidateCount':1,'runtimeWebsitePromotion':False}
(E/'round-contract.json').write_text(json.dumps(contract,indent=2)+'\n',encoding='utf8')
raw=f'https://raw.githubusercontent.com/Upliner/CharMorph-Vitruvian/{REV}/{REL}'
with urllib.request.urlopen(raw,timeout=30) as s:pointer=s.read()
assert pointer.startswith(b'version https://git-lfs.github.com/spec/v1\n')
expected=dict(line.split(' ',1) for line in pointer.decode().splitlines());oid=expected['oid'].split(':',1)[1];size=int(expected['size'])
p=D/'hair.blend';url=f'https://media.githubusercontent.com/media/Upliner/CharMorph-Vitruvian/{REV}/{REL}'
if not p.exists():
    with urllib.request.urlopen(url,timeout=60) as src,p.open('wb') as dst:
        while chunk:=src.read(1024*1024):dst.write(chunk)
assert p.stat().st_size==size and hashlib.sha256(p.read_bytes()).hexdigest()==oid
(E/'source-provenance.json').write_text(json.dumps({'repository':'https://github.com/Upliner/CharMorph-Vitruvian','commit':REV,'file':str(p),'url':url,'sha256':oid,'bytes':size,'license':'CC0 per pinned config.yaml; author credits retained. Tool/addon code not imported.','autoExecute':'DISABLED','seconds':time.time()-tick},indent=2)+'\n',encoding='utf8')
print('R58_PINNED_NATIVE_LIBRARY',size,oid,time.time()-tick,flush=True)
