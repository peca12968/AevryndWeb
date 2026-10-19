"""Fetch only pinned CC0 authored blink deltas, never addon code."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,urllib.request,numpy as np
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0059-authored-blink';D=R/'Reference/character/charmorph-vitruvian-cc0';E.mkdir(parents=True,exist_ok=True)
REV='c252d1fc7f00ba59d87b66b3d32fa3471fc6ee44';files=[]
contract={'revision':'female-next-r0059','startUTC':datetime.now(timezone.utc).isoformat(),'previousGoalTurnClassification':'progress: reconciled/archived portable r57D, corrected original follicle-key assumption and rejected r58 native Bob against actual render surface; no full-character appearance gain.','mainDefect':'Coherent foundation is static; eyelids and lashes cannot yet perform a real editable blink. Hair remains unresolved but repeated Bob fitting is stopped.','sourceAndReference':'Retained r57D complete-body candidate plus original same37436index CC0 Eyes_Closed_Left/Right authored morphs and original native eyelash emitter.','expectedVisibleChange':'Natural actual eyelid closure with lash following, editable left/right controls and a playable blink on the complete character, preserving neutral look.','minimumPilot':'Read same-topology deltas and native lash poses, build one source-native motion candidate, render neutral/half/closed plus head/body views.','reject':'Neutral regression, bad closure, detached lashes, actual ocular intersections or invalid controls; no procedural r44/r45 revival, tolerance or shader sweep.','resources':'One heavy job, max4threads; first diagnostic10minutes, actual preview or falsification before45minute resource checkpoint. No app/addon installation.','candidateCount':1,'runtimeWebsitePromotion':False}
(E/'round-contract.json').write_text(json.dumps(contract,indent=2)+'\n',encoding='utf8')
for name in ('Eyes_Closed_Left.npz','Eyes_Closed_Right.npz','morphs.json'):
    url=f'https://raw.githubusercontent.com/Upliner/CharMorph-Vitruvian/{REV}/morphs/L3/{name}';p=E/('source-'+name)
    if not p.exists():
        with urllib.request.urlopen(url,timeout=30) as src:p.write_bytes(src.read())
    row={'file':p.name,'url':url,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
    if name.endswith('.npz'):
        a=np.load(p,allow_pickle=False);assert set(a.files)=={'idx','delta'} and a['delta'].shape==(len(a['idx']),3) and np.isfinite(a['delta']).all() and a['idx'].max()<37436
        row.update(indices=len(a['idx']),maximumDeltaM=float(np.linalg.norm(a['delta'],axis=1).max()))
    files.append(row)
provenance={'repository':'https://github.com/Upliner/CharMorph-Vitruvian','commit':REV,'license':'CC0 per pinned config.yaml; Sean Buckley/Olaf Delgado-Friedrichs and additional contributors credited there. Data only; no addon/embedded program code imported.','files':files}
(E/'source-provenance.json').write_text(json.dumps(provenance,indent=2)+'\n',encoding='utf8')
print('R59_PINNED_BLINK_DATA',json.dumps(files),flush=True)
