"""Bounded anatomical-region inspection before a coherent soft-tissue repair."""
import bpy,json,importlib.util
from pathlib import Path
import numpy as np
spec=importlib.util.spec_from_file_location('b25',Path(__file__).with_name('build-female-next-r0025-dental-contact.py'));b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
E=b.R/'Evidence/character-female-next/r0026-oral-interface';E.mkdir(exist_ok=True)
def save(name,value):(E/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf8')
def main():
    manifest=json.loads((b.S.parent/'female-next.asset.json').read_text(encoding='utf8'));src=b.S.parent/manifest['oralResearchSource'];assert b.sha(src)==manifest['oralResearchSha256'];bpy.ops.wm.open_mainfile(filepath=str(src))
    rig=bpy.data.objects['AFN_R0005_Rig'];b.prior.solid.stage.set_pose(rig,'neutral');master=bpy.data.objects['AFN24_MouthControl'];teeth=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('AFN25_')];rows=[]
    for w in (0.,.2):
        master['open']=w;master.update_tag(refresh={'OBJECT'});bpy.context.scene.frame_set(bpy.context.scene.frame_current+1);bpy.context.view_layer.update()
        tongue=bpy.data.objects['AFN24_Tongue'];gum=bpy.data.objects['AFN24_ContinuousGingivalLining'];P,T,tree=b.prior.solid.data(tongue);G,GT,gtree=b.prior.solid.data(gum);p=np.array(P,np.float64);g=np.array(G,np.float64);contact=[]
        for tooth in teeth:
            Q,F,own=b.prior.solid.data(tooth);hits=tree.overlap(own)
            if hits:
                centres=np.array([p[list(T[i])].mean(0) for i,j in hits]);ids=sorted({v for i,j in hits for v in T[i]})
                contact.append({'tooth':tooth.name,'pairs':len(hits),'tongueTriangleCentreBoundsM':[centres.min(0).tolist(),centres.max(0).tolist()],'tongueVertices':ids})
        overlap=tree.overlap(gtree);ts=sorted({i for i,j in overlap});gs=sorted({j for i,j in overlap});tv=sorted({v for i in ts for v in T[i]});gv=sorted({v for i in gs for v in GT[i]})
        body=b.prior.solid.data(bpy.data.objects['AFN_R0008_Body']);bodygum=body[2].overlap(gtree)
        rows.append({'weight':w,'tongueTooth':contact,'tongueGingiva':{'pairs':len(overlap),'tongueVertices':tv,'gingivaVertices':gv,'tongueBoundsM':[p[tv].min(0).tolist(),p[tv].max(0).tolist()] if tv else None},'gingivaBody':{'pairs':len(bodygum),'gingivaTriangleCentres':[g[list(GT[j])].mean(0).tolist() for i,j in bodygum[:20]]}})
    topology=[]
    for o in (tongue,gum):
        edge_use={}
        for f in o.data.polygons:
            ids=list(f.vertices)
            for a,c in zip(ids,ids[1:]+ids[:1]):key=tuple(sorted((a,c)));edge_use[key]=edge_use.get(key,0)+1
        P=b.prior.positions(o);bounds=[edge for edge,n in edge_use.items() if n==1]
        topology.append({'name':o.name,'vertices':len(P),'polygons':len(o.data.polygons),'euler':len(P)-len(edge_use)+len(o.data.polygons),'boundaryEdges':len(bounds),'boundaryVertexIds':sorted({v for e in bounds for v in e}),'boundsM':[P.min(0).tolist(),P.max(0).tolist()]})
    folder=b.S/'oral/makehuman-system-cc0/teeth/teeth_base';V,uv,F,FUV=b.prior.proxy.obj(folder/'teeth_base.obj');groups=b.prior.proxy.components(len(V),F);mapping=b.prior.proxy.proxy(folder/'teeth_base.mhclo');indices=groups[0];refs=np.unique(mapping['ids'][indices]);weights={str(int(i)):int((mapping['ids'][indices]==i).any(1).sum()) for i in refs}
    save('interface-inspection.json',{'source':str(src),'sourceSha256':b.sha(src),'topology':topology,'contacts':rows,'gingivalNativeReferenceCounts':weights,'scope':'Actual regions, topology and raw contacts; no anatomical exclusion or acceptance.'})
    print(json.dumps({'topology':[{k:v for k,v in r.items() if k!='boundaryVertexIds'} for r in topology],'neutralTongueTooth':[{'tooth':r['tooth'],'pairs':r['pairs'],'bounds':r['tongueTriangleCentreBoundsM']} for r in rows[0]['tongueTooth']],'tongueGumPairs':[r['tongueGingiva']['pairs'] for r in rows],'gingivalNativeReferenceCounts':weights},indent=2),flush=True)
if __name__=='__main__':main()
