"""Locate the few exact self-contact failures before any bounded cleanup."""
import bpy,importlib.util,json
from pathlib import Path
import numpy as np
spec=importlib.util.spec_from_file_location('b26',Path(__file__).with_name('build-female-next-r0026-oral-interface.py'));b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
def main():
    report=json.loads((b.E/'c-build-verification.json').read_text(encoding='utf8'));bpy.ops.wm.open_mainfile(filepath=report['output']);o=bpy.data.objects['AFN26_Tongue'];P,T,tree=b.b.prior.solid.data(o);p=np.array(P,np.float64);pairs=[(i,j) for i,j in tree.overlap(tree) if i<j and set(T[i]).isdisjoint(T[j])];rows=[]
    for i,j in pairs:
        a,c=p[list(T[i])],p[list(T[j])];dist=np.linalg.norm(a[:,None,:]-c[None,:,:],axis=2);rows.append({'triangles':[i,j],'vertexIds':[list(T[i]),list(T[j])],'vertexPositionsM':[a.tolist(),c.tolist()],'minimumCrossVertexDistanceM':float(dist.min()),'smallestOwnEdgeM':float(min(np.linalg.norm(q-np.roll(q,1,axis=0),axis=1).min() for q in (a,c)))})
    b.save('c-self-contact-diagnosis.json',{'asset':report['output'],'assetSha256':report['outputSha256'],'pairs':rows,'scope':'Actual reopened full triangles, before cleanup. No acceptance.'});print(json.dumps(rows,indent=2),flush=True)
if __name__=='__main__':main()
