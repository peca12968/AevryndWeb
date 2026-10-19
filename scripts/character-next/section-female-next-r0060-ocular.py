"""Exact rendered-surface sagittal sections, not a replacement character image."""
from pathlib import Path
import bpy,numpy as np,json,time
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0060-ocular-assembly';PREV=E.parent/'r0059-authored-blink'
def main():
    tick=time.time();a=json.loads((PREV/'a-build-summary.json').read_text());bpy.ops.wm.open_mainfile(filepath=a['output']);body=bpy.data.objects['AFN57_CC0_COHERENT_FEMALE_BODY'];raw=np.load(E/'native-component-lineage.npz');matrix=np.array(body.matrix_world);F=raw['AFN57_Supplied_Female_Morph'];sphere=F[raw['components']==0];centre=(sphere.min(0)+sphere.max(0))*.5;C=centre@matrix[:3,:3].T+matrix[:3,3];plane=float(C[0]);result={'centreWorldM':C.tolist(),'planeXWorldM':plane,'horizontalCoordinate':'Forward = -(Y-centreY), vertical = Z-centreZ; millimetres in plot.','source':a['output'],'sourceSha256':a['outputSha256'],'poses':{}}
    for md in body.modifiers:
        if md.type=='SUBSURF':md.levels=md.render_levels
    for frame,label in ((1,'neutral'),(21,'closed')):
        bpy.context.scene.frame_set(frame);bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles();P=np.empty(len(me.vertices)*3,dtype='f4');me.vertices.foreach_get('co',P);P=P.reshape(-1,3).astype('f8')@matrix[:3,:3].T+matrix[:3,3];T=np.empty(len(me.loop_triangles)*3,dtype='i4');me.loop_triangles.foreach_get('vertices',T);T=T.reshape(-1,3);mi=np.empty(len(T),dtype='i4');me.loop_triangles.foreach_get('material_index',mi);ev.to_mesh_clear();tri=P[T];ids=np.flatnonzero((tri[:,:,0].min(1)<=plane)&(tri[:,:,0].max(1)>=plane)&(tri[:,:,2].min(1)<C[2]+.027)&(tri[:,:,2].max(1)>C[2]-.027)&(tri[:,:,1].min(1)<C[1]+.025)&(tri[:,:,1].max(1)>C[1]-.04));sections={}
        for i in ids:
            p=tri[i];points=[]
            for j in range(3):
                aa=p[j];bb=p[(j+1)%3];den=bb[0]-aa[0]
                if abs(den)<1e-15:continue
                t=(plane-aa[0])/den
                if 0<=t<=1:
                    q=aa+t*(bb-aa)
                    if not any(np.linalg.norm(q-z)<1e-10 for z in points):points.append(q)
            if len(points)==2:sections.setdefault(str(mi[i]),[]).append([q.tolist() for q in points])
        result['poses'][label]=sections;print('R60_SECTION',label,{m:len(x) for m,x in sections.items()},flush=True)
    # Exact source material interfaces, useful for the replacement anatomical rim.
    mesh=body.data;edges={}
    for p in mesh.polygons:
        if p.material_index not in (4,7):continue
        for x,y in zip(p.vertices,list(p.vertices[1:])+[p.vertices[0]]):edges.setdefault(tuple(sorted((x,y))),[]).append(p.material_index)
    seams=[list(edge) for edge,roles in edges.items() if 4 in roles and 7 in roles]
    result['sourceSkinWetMaterialSharedEdges']=seams;result['seconds']=time.time()-tick;(E/'rendered-ocular-sections.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print('R60_SECTION_READY',len(seams),time.time()-tick,flush=True)
if __name__=='__main__':main()
