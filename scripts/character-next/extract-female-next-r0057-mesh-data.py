"""Extract portable CC0 mesh/UV arrays without embedding legacy systems."""
from pathlib import Path
import bpy,numpy as np,json,hashlib
R=Path(r'D:\Download\Aevrynd');D=R/'Reference/character/charmorph-vitruvian-cc0';E=R/'Evidence/character-female-next/r0057-coherent-foundation'
bpy.ops.wm.open_mainfile(filepath=str(D/'canonical-female-data.blend'));o=bpy.data.objects['cm_vitruvian'];mesh=o.data
counts=np.array([len(p.vertices) for p in mesh.polygons],dtype='i4');corners=np.array([v for p in mesh.polygons for v in p.vertices],dtype='i4');materials=np.array([p.material_index for p in mesh.polygons],dtype='i4');uv=np.array([v.uv[:] for v in mesh.uv_layers['VitruvianUV.UDIM'].data],dtype='f4')
assert len(uv)==len(corners)==counts.sum();P=np.load(D/'Default.npy');a=np.load(D/'Gender_Female.npz');F=P.copy();F[a['idx']]+=a['delta']
np.savez_compressed(E/'canonical-mesh-data.npz',canonical=P,female=F,polygonCounts=counts,corners=corners,materials=materials,uv=uv)
row={'vertices':len(P),'polygons':len(counts),'corners':len(corners),'uvMap':'VitruvianUV.UDIM','scope':'Exact original topology/loop UV and declared canonical/female arrays. No particle data, embedded texts, addon or engine tool code.'}
(E/'canonical-mesh-data.json').write_text(json.dumps(row,indent=2)+'\n',encoding='utf8');print('R57_PURE_MESH_READY',json.dumps(row),flush=True)
