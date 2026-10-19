"""Bounded native/evaluated eye-socket localization, no geometry mutation saved."""
import bpy,json,importlib.util,hashlib
from pathlib import Path
import numpy as np
from mathutils.bvhtree import BVHTree
spec=importlib.util.spec_from_file_location('b28',Path(__file__).with_name('build-female-next-r0028-cc0-foundation.py'));b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
E=b.R/'Evidence/character-female-next/r0029-native-eye-interface';E.mkdir(parents=True,exist_ok=True)
def save(n,x):(E/n).write_text(json.dumps(x,indent=2)+'\n',encoding='utf8')
def sphere(p):
    q=p.mean(0);x=p-q;fit=np.linalg.lstsq(np.column_stack((2*x,np.ones(len(x)))),(x*x).sum(1),rcond=None)[0];c=q+fit[:3];rr=np.linalg.norm(p-c,axis=1);return c,float(np.median(rr)),float(rr.min()),float(rr.max())
def main():
    assert b.sha(b.OUT)=='68aa031b5ef4ad3353129eeb9ac881ef7237ed840928e05bd0c4a6b6e32cba6c';bpy.ops.wm.open_mainfile(filepath=str(b.OUT));body=bpy.data.objects[b.BODY];m=body.modifiers[0];eyes={o.name:b.evaluated(o,True) for o in bpy.data.objects if o.type=='MESH' and '.eye.' in o.name};rows={};base=np.array([list(body.matrix_world@v.co) for v in body.data.vertices]);polys=[list(p.vertices) for p in body.data.polygons];adj={i:set() for i in range(len(base))}
    for edge in body.data.edges:a,c=edge.vertices;adj[a].add(c);adj[c].add(a)
    native={}
    for name,(p,pt) in eyes.items():
        c,r,rmin,rmax=sphere(p);near=np.flatnonzero(np.linalg.norm(base-c,axis=1)<r*2.5);meshrows=[{'vertex':int(i),'position':base[i].tolist(),'radiusRatio':float(np.linalg.norm(base[i]-c)/r),'neighbors':sorted(adj[int(i)])} for i in near]
        native[name]={'fittedSphereCenterM':c.tolist(),'fittedMedianRadiusM':r,'fittedRadiusRangeM':[rmin,rmax],'nearVertices':meshrows,'nearPolygons':[{'polygon':i,'vertices':ids} for i,ids in enumerate(polys) if any(v in set(near) for v in ids)]}
    for level in (0,3):
        m.levels=level;bpy.context.view_layer.update();v,t=b.evaluated(body,True);tree=BVHTree.FromPolygons(v.tolist(),t.tolist(),all_triangles=True,epsilon=0.0);entries={}
        for name,(p,pt) in eyes.items():
            eye=BVHTree.FromPolygons(p.tolist(),pt.tolist(),all_triangles=True);pairs=tree.overlap(eye);ids=np.unique([a for a,c in pairs]);tri=v[t[ids]] if len(ids) else np.empty((0,3,3));centroid=tri.mean(1);normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-20)
            entries[name]={'trianglePairs':len(pairs),'uniqueBodyTriangles':len(ids),'bodyTriangleIndices':[int(i) for i in ids],'crossingTriangleCentersM':centroid.tolist(),'crossingTriangleNormals':normal.tolist(),'crossingBodyVertexBoundsM':{'min':tri.reshape(-1,3).min(0).tolist(),'max':tri.reshape(-1,3).max(0).tolist()} if len(ids) else None}
        rows[str(level)]=entries
    save('native-interface-inspection.json',{'source':str(b.OUT),'sourceSha256':b.sha(b.OUT),'native':native,'levels':rows,'scope':'Actual native vertex connectivity, coarse and full sculpt triangle overlaps; no exclusions. Fitted sphere is geometric diagnostic only, not a collider acceptance claim.'});print('R29_INSPECT_DONE',json.dumps({k:{n:{'pairs':v['trianglePairs'],'bounds':v['crossingBodyVertexBoundsM']} for n,v in a.items()} for k,a in rows.items()}),flush=True)
if __name__=='__main__':main()
