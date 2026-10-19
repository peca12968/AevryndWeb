"""Bounded actual topology/interface diagnosis for a geometry repair."""
from pathlib import Path
from datetime import datetime,timezone
import bpy,numpy as np,json,time,hashlib
R=Path(r'D:\Download\Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0060-ocular-assembly';PREV=E.parent/'r0059-authored-blink';E.mkdir(parents=True,exist_ok=True)
def save(n,x):(E/n).write_text(json.dumps(x,indent=2)+'\n',encoding='utf8')
def main():
    tick=time.time();a=json.loads((PREV/'a-build-summary.json').read_text());path=Path(a['output']);assert hashlib.sha256(path.read_bytes()).hexdigest()==a['outputSha256']
    save('round-contract.json',{'revision':'female-next-r0060','startUTC':datetime.now(timezone.utc).isoformat(),'previousGoalTurnClassification':'progress: real native editable blink, lash/brow following and48rendered frames; contact failure found and archivedf653407, not adopted.','source':str(path),'sourceSha256':a['outputSha256'],'mainDefect':'Actual eye/skin/wetline interfaces cross in neutral and closed poses; data are mixed in one mesh.','expectedVisibleOrFunctionalChange':'Correctly separated editable ocular structure with actual finite surface separation, retaining whole-character neutral face and native blink/curves.','minimumPilot':'Exact connected-component/vertex lineage, actual sagittal eye section, then one topology/interface authoring candidate before broad pose testing.','reject':'Hidden/resized/translated entire globe to mask failure, changed subdivision seams, major visible eye/face regression, or remaining endpoint intersections.','resources':'One heavy job,4threads; diagnosis10minute limit and actual preview/rejection before45minute resource checkpoint. No new tools/addons or unrelated asset imports.'})
    bpy.ops.wm.open_mainfile(filepath=str(path));o=bpy.data.objects['AFN57_CC0_COHERENT_FEMALE_BODY'];mesh=o.data;N=len(mesh.vertices);parent=np.arange(N,dtype='i4')
    def root(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return int(i)
    for edge in mesh.edges:
        x,y=edge.vertices;rx,ry=root(x),root(y)
        if rx!=ry:parent[ry]=rx
    reps=np.array([root(i) for i in range(N)]);unique,components=np.unique(reps,return_inverse=True);P=np.array([v.co[:] for v in mesh.vertices],dtype='f4');F=np.array([v.co[:] for v in mesh.shape_keys.key_blocks['AFN57_Supplied_Female_Morph'].data],dtype='f4');mats=np.array([p.material_index for p in mesh.polygons],dtype='i4');polys=[p.vertices[:] for p in mesh.polygons];faceComponents=np.array([components[p[0]] for p in polys],dtype='i4');rows=[]
    for ci in range(len(unique)):
        vi=np.flatnonzero(components==ci);fi=np.flatnonzero(faceComponents==ci);ids,counts=np.unique(mats[fi],return_counts=True);bounds=[F[vi].min(0).tolist(),F[vi].max(0).tolist()];rows.append({'component':ci,'vertices':len(vi),'polygons':len(fi),'materials':dict(zip(ids.astype(str).tolist(),counts.tolist())),'femaleLocalBounds':bounds,'vertexIDRange':[int(vi.min()),int(vi.max())]})
    # Source shape keys and native UV are recorded once for exact split/rebuild.
    corners=np.array([v for p in polys for v in p],dtype='i4');counts=np.array([len(p) for p in polys],dtype='i4');uv=np.array([p.uv[:] for p in mesh.uv_layers['VitruvianUV.UDIM'].data],dtype='f4');keys={key.name:np.array([v.co[:] for v in key.data],dtype='f4') for key in mesh.shape_keys.key_blocks}
    np.savez_compressed(E/'native-component-lineage.npz',positions=P,components=components.astype('i4'),faceComponents=faceComponents,corners=corners,polygonCounts=counts,materials=mats,uv=uv,matrix=np.array(o.matrix_world),**keys)
    save('native-components.json',{'source':str(path),'sourceSha256':a['outputSha256'],'components':rows,'totalVertices':N,'totalPolygons':len(polys),'noGeometryModified':True,'seconds':time.time()-tick})
    for r in rows:print('R60_COMPONENT',json.dumps(r),flush=True)
    print('R60_TOPOLOGY_READY',len(rows),time.time()-tick,flush=True)
if __name__=='__main__':main()
