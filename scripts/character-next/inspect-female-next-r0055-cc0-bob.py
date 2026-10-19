"""Inspect only the pinned CC0 character geometry and authored guide data.

No addon installation, external tool code, auto-execution or runtime import.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib
R=Path(r'D:\Download\Aevrynd');D=R/'Reference/character/charmorph-vitruvian-cc0'
E=R/'Evidence/character-female-next/r0055-authored-cc0-bob';E.mkdir(parents=True,exist_ok=True)
assert hashlib.sha256((D/'char.blend').read_bytes()).hexdigest()=='7e9581c30b48f1409dfeec4a5ec0736014318fc8825ca6d4728f2b543bb02126'
bpy.ops.wm.open_mainfile(filepath=str(D/'char.blend'))
rows=[]
for o in bpy.data.objects:
    row={'object':o.name,'type':o.type}
    if o.type=='MESH':
        p=np.array([o.matrix_world@v.co for v in o.data.vertices]);head=p[p[:,2]>1.48]
        row.update(vertices=len(p),bounds=[p.min(0).tolist(),p.max(0).tolist()],matrix=[list(r) for r in o.matrix_world],modifiers=[m.type for m in o.modifiers])
        if len(head):row['headBounds']=[head.min(0).tolist(),head.max(0).tolist()]
        row['materialRegions']=[]
        for mi,mat in enumerate(o.data.materials):
            ids=sorted({vi for f in o.data.polygons if f.material_index==mi for vi in f.vertices})
            if ids:
                q=p[ids];row['materialRegions'].append({'material':mat.name if mat else 'EMPTY_SLOT_'+str(mi),'vertices':len(ids),'bounds':[q.min(0).tolist(),q.max(0).tolist()]})
        o.data.calc_loop_triangles()
        skinTriangles=np.array([list(t.vertices) for t in o.data.loop_triangles if o.data.polygons[t.polygon_index].material_index==4 and p[list(t.vertices),2].min()>1.48],dtype='i4')
        np.savez_compressed(E/'donor-native-body.npz',vertices=p,triangles=np.array([list(t.vertices) for t in o.data.loop_triangles],dtype='i4'),headSkinTriangles=skinTriangles)
        eye_ids=sorted({vi for face in o.data.polygons if face.material_index==3 for vi in face.vertices})
        eyes=p[eye_ids];left=eyes[eyes[:,0]<0].mean(0);right=eyes[eyes[:,0]>0].mean(0)
        row['registrationLandmarks']={'eyeCenterNegativeX':left.tolist(),'eyeCenterPositiveX':right.tolist(),'top':float(p[:,2].max()),'scope':'Mean of each source ocular material region; design registration landmarks, not scan measurements.'}
    rows.append(row)
a=np.load(D/'Bob.npz',allow_pickle=False);P=a['data'].reshape(-1,16,3)
report={'objects':rows,'guides':len(P),'points':16,'rootBounds':[P[:,0].min(0).tolist(),P[:,0].max(0).tolist()],
        'tipBounds':[P[:,-1].min(0).tolist(),P[:,-1].max(0).tolist()],'guideSHA256':hashlib.sha256((D/'Bob.npz').read_bytes()).hexdigest()}
(E/'donor-inspection.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print('CC0_SOURCE_INSPECTED',json.dumps(report),flush=True)
