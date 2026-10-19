"""Read-only inventory of original artist data and in-file license notices."""
import bpy,json,hashlib
from pathlib import Path
import numpy as np
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0038-volume-flow'
P=R/'Reference/character/blender-hair-styles/hair_nodes-female_hair_styles.blend'
bpy.ops.wm.open_mainfile(filepath=str(P))
texts={t.name:t.as_string() for t in bpy.data.texts}
out={'source':str(P),'sha256':hashlib.sha256(P.read_bytes()).hexdigest(),'texts':texts,'objects':[]}
for o in bpy.data.objects:
 if o.type not in ('MESH','CURVES'):continue
 item={'name':o.name,'type':o.type,'matrix':[list(r) for r in o.matrix_world],'modifiers':[(m.name,m.type) for m in o.modifiers],'props':{k:str(o[k]) for k in o.keys()}}
 if o.type=='CURVES':
  points=np.empty(len(o.data.points)*3,dtype='f4');o.data.position_data.foreach_get('vector',points);points=points.reshape(-1,3)
  roots=np.array([points[c.first_point_index] for c in o.data.curves])
  item.update({'curves':len(o.data.curves),'bounds':[points.min(0).tolist(),points.max(0).tolist()],'rootsBounds':[roots.min(0).tolist(),roots.max(0).tolist()]})
 else:
  points=np.array([v.co[:] for v in o.data.vertices]);item['bounds']=[points.min(0).tolist(),points.max(0).tolist()]
 out['objects'].append(item)
(E/'original-artist-infile-inventory.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'texts':texts,'objects':[{k:v for k,v in r.items() if k not in ('props','modifiers','matrix')} for r in out['objects']]},ensure_ascii=False))
