from pathlib import Path
from runpy import run_path
import inspect
import json
import numpy as np
ROOT=Path(__file__).resolve().parent
a=run_path(str(ROOT.parent/'r0480-lock-clearance-projection/author-r0480.py'))
probe=a['probe']
text='\n'.join(inspect.getsource(f) for f in (probe['scene_parts'],probe['state'],probe['r466']['layers'],probe['r466']['a'].open_scene,probe['r468']['choose']))
text+='\nHAIR='+a['groom'].HAIR
text+='\n'+'\n'.join(inspect.getsource(f) for f in (probe['r466']['c']['p']['active_layers'],probe['r466']['c']['p']['data_parts'],probe['r466']['a'].orb.open_scene))
orb=probe['r466']['a'].orb
text+='\nCURRENT_NAMES='+json.dumps(orb.u.p.names)
text+='\nRIG='+orb.g.a.s.RIG
parts_function=probe['r466']['c']['p']['data_parts'].__globals__['q']['parts']
layers_function=probe['r466']['c']['p']['active_layers'].__globals__['q']['m']['layers']
text+='\n'+inspect.getsource(parts_function)+'\n'+inspect.getsource(layers_function)
q=probe['r466']['c']['p']['active_layers'].__globals__['q']
mapping=dict(names=orb.u.p.names,rig=orb.g.a.s.RIG,wet=layers_function.__globals__['receipt']['wet'],lashes=q['prior']['lashes'])
(ROOT/'actual-component-map.json').write_bytes(json.dumps(mapping,indent=2).encode('utf8'))
(ROOT/'actual-parts-functions.txt').write_bytes(text.encode('utf8'))
data=np.load(ROOT/'reference/AFN126_ORIGINAL_Hair_Hair_0-original-geometry.npz',allow_pickle=False)
rows={k:dict(shape=list(data[k].shape),dtype=str(data[k].dtype),min=float(np.min(data[k])),max=float(np.max(data[k]))) for k in data.files}
(ROOT/'original-hair-arrays.json').write_bytes(json.dumps(rows,indent=2).encode('utf8'))
print(text,flush=True)
print(json.dumps(rows,indent=2),flush=True)
