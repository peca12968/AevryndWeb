"""Read pinned CC0 source coordinates/UVs before one coherent foundation preview."""
from pathlib import Path
import bpy,numpy as np,json
R=Path(r'D:\Download\Aevrynd');D=R/'Reference/character/charmorph-vitruvian-cc0';E=R/'Evidence/character-female-next/r0057-coherent-foundation';E.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(D/'char.blend'));o=bpy.data.objects['cm_vitruvian']
print('R57_SOURCE_MODE',o.mode,'UV',[(u.name,len(u.data),len(u.uv)) for u in o.data.uv_layers],flush=True)
if o.mode!='OBJECT':bpy.context.view_layer.objects.active=o;bpy.ops.object.mode_set(mode='OBJECT')
mesh=o.data
P=np.array([v.co[:] for v in mesh.vertices]);basis=np.load(D/'Default.npy',allow_pickle=False)
rows=[]
for uv in mesh.uv_layers:
    if not len(uv.data):
        rows.append({'name':uv.name,'emptyUVData':True});continue
    byMaterial={}
    for face in mesh.polygons:
        if P[list(face.vertices),2].mean()<1.48:continue
        tiles=[]
        for li in face.loop_indices:
            a=np.array(uv.data[li].uv);tiles.append(int(np.floor(a[0]))+10*int(np.floor(a[1]))+1001)
        byMaterial.setdefault(str(face.material_index),[]).extend(tiles)
    rows.append({'name':uv.name,'active':uv==mesh.uv_layers.active,'headTileCountsByMaterial':{k:{str(t):int(c) for t,c in zip(*np.unique(v,return_counts=True))} for k,v in byMaterial.items()}})
report={'sourceVertices':len(P),'sourceShapeKeys':[k.name for k in mesh.shape_keys.key_blocks] if mesh.shape_keys else [],'uvLayers':rows,'basisShape':list(basis.shape),'basisVsNativeMaximumDifferenceM':float(np.linalg.norm(P-basis,axis=1).max()) if P.shape==basis.shape else None}
(E/'source-inspection.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print('R57_SOURCE_INSPECTION',json.dumps(report),flush=True)
