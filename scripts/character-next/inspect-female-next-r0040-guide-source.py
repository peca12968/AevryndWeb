"""r40 initial cause check and private raw-guide cache; no promotion."""
import bpy,importlib.util,json,time
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sp=importlib.util.spec_from_file_location('source40',Path(__file__).with_name('inspect-female-next-r0039-source-contacts.py'));src=importlib.util.module_from_spec(sp);sp.loader.exec_module(src)
c=src.c;a=c.a;m=c.m;f=c.f;b=c.b;v=c.v
E=f.R/'Evidence/character-female-next/r0040-guide-contact';E.mkdir(exist_ok=True);PVT=E/'private';PVT.mkdir(exist_ok=True)
def save(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def main():
    start=time.time();P,names,VS,TS=src.raw();main_count=names.count('long hair main');assert main_count==346
    # Raw source UVs, not resampled evaluated anonymous fields.
    raw=bpy.data.objects['long hair main'].data;attrs=[(x.name,x.data_type,x.domain,len(x.data)) for x in raw.attributes]
    uv=None
    for name in ('surface_uv_coordinate','surface_uv_coordinates'):
        ar=raw.attributes.get(name)
        if ar:
            uv=np.array([list(x.vector) for x in ar.data],dtype='f8');break
    growth=bpy.data.objects['long hair growth mesh'];growth.data.calc_loop_triangles()
    gV=np.array([v.co[:] for v in growth.data.vertices]);gT=np.array([x.vertices[:] for x in growth.data.loop_triangles])
    guv=np.array([loop.uv[:] for loop in growth.data.uv_layers.active.data]) if growth.data.uv_layers.active else np.empty((0,2))
    np.savez_compressed(PVT/'raw-artist-guides-reference-only.npz',positionsReferenceUnits=P[:main_count],allRawPositions=P,guideUV=uv if uv is not None else np.empty((0,2)),growthVertices=gV,growthTriangles=gT,growthLoopUV=guv,sourceHeadVertices=VS,sourceHeadTriangles=TS)
    # Check the previously identified deep point before/after transfer on the
    # same CLOSED target body. This does not use open-head normal signs as proof.
    orig=np.load(c.PRIVATE/'artist-render-12k-reference-only.npz')['positions'][10934,114].astype('f8')*np.array((.094,.085,.081))+np.array((0,.005,.234))
    phases={'originalAffineBeforeRootBlend':orig}
    for tag,file,objname in [('C0','aevrynd-female-next-r0039-c-artist-transfer-study.blend','AFN39_C_PRIVATE_ARTIST_FIBRES'),('C1','aevrynd-female-next-r0039-c1-surface-transfer-study.blend','AFN39_C1_PRIVATE_SURFACE_TRANSFER')]:
        bpy.ops.wm.open_mainfile(filepath=str(c.PRIVATE/file));o=bpy.data.objects[objname];q,r=v.hair_arrays(o);mx=np.array(o.matrix_world)
        phases[tag]=q[10934,114].astype('f8')@mx[:3,:3].T+mx[:3,3]
    V,T=b.evaluated(bpy.data.objects[b.BODY],True);tree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True);rows={}
    for key,p in phases.items():
        h,n,ti,d=tree.find_nearest(Vector(p));rows[key]={'classification':f.flowcheck.cap.solid.classify(tree,V[T],Vector(p)),'unsignedBoundaryDistanceM':d,'pointWorld':p.tolist()}
    (PVT/'deep-point-phase-diagnosis.json').write_text(json.dumps(rows,indent=2)+'\n')
    save('source-structure-summary.json',{'sourceFileSha256':b.sha(c.REF),'author':'Daniel Bystedt','privateOnly':True,'rawMainGuides':main_count,'allRawGuides':len(P),'nativeAttributes':attrs,'guideUVAvailable':uv is not None,'guideUVBounds':[uv.min(0).tolist(),uv.max(0).tolist()] if uv is not None else None,'growthMeshVertices':len(gV),'growthMeshTriangles':len(gT),'deepPointClassifications':{k:{q:z for q,z in row.items() if q!='pointWorld'} for k,row in rows.items()},'scope':'Private guide data cached; only structure/causal statistics may enter public history. No accepted model or contact claim.','seconds':time.time()-start})
    print('R40_SOURCE_READY',main_count,'UV',None if uv is None else uv.shape,'DEEP_PHASES',rows,flush=True)
if __name__=='__main__':main()
