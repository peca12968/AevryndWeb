"""Measure actual retained native lid rim against the evaluated skin/eye.

No assumed ellipse or old-head lash coordinates. Geometry is not mutated.
"""
import bpy,importlib.util,json,time
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
spec=importlib.util.spec_from_file_location('c36',Path(__file__).with_name('build-female-next-r0036-brows.py'));c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c);b=c.b;v=c.v
R=b.R;S=b.S;E=R/'Evidence/character-female-next/r0037-eye-margin';E.mkdir(exist_ok=True)
SRC=S/'aevrynd-female-next-r0036-b-contact-refined-brows.blend'
def save(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def outer(side):return v.i.outer(side)
def spline(points,count=401):
    # Periodic centripetal-free Catmull-Rom used only to sample rim reference.
    out=[]
    for t in np.linspace(0,len(points),count,endpoint=False):
        k=int(t);u=t-k;p0=points[(k-1)%len(points)];p1=points[k%len(points)];p2=points[(k+1)%len(points)];p3=points[(k+2)%len(points)]
        out.append(.5*((2*p1)+(-p0+p2)*u+(2*p0-5*p1+4*p2-p3)*u*u+(-p0+3*p1-3*p2+p3)*u*u*u))
    return np.array(out)
def main():
    start=time.time();assert b.sha(SRC)=='d563918d780e6d86f52e8bd50562bc5beec427ccfc5ebb60ac88e3aa53185210';bpy.ops.wm.open_mainfile(filepath=str(SRC));body=bpy.data.objects[b.BODY];V,T=b.evaluated(body,True);bt=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True,epsilon=0.)
    native=np.array([list(body.matrix_world@p.co) for p in body.data.vertices]);inspection=json.loads((R/'Evidence/character-female-next/r0035-neutral-lid-rest/aperture-topology-inspection.json').read_text(encoding='utf8'));out={};arrays={}
    for side in ('L','R'):
        sign=1 if side=='L' else -1;center=np.array(v.i.FITS[side]['centerM']);ids=np.array([r['id'] for r in inspection['native'][side]['wallBoundaryVertices'] if native[r['id'],1]<-.108]);p=native[ids];angles=np.arctan2(p[:,2]-center[2],(p[:,0]-center[0])*sign);order=np.argsort(angles);p=p[order];ids=ids[order];reference=spline(p);eyeV,eyeT=outer(side);et=BVHTree.FromPolygons(eyeV.tolist(),eyeT.tolist(),all_triangles=True,epsilon=0.)
        closest=[bt.find_nearest(Vector(q)) for q in reference];skin=np.array([list(h[0]) for h in closest]);normals=np.array([list(h[1]) for h in closest]);tids=np.array([h[2] for h in closest]);gap=np.array([et.find_nearest(Vector(q))[3] for q in skin]);projection=np.linalg.norm(skin-reference,axis=1)
        # Split actual loop at its medial and lateral extrema; preserve all
        # actual y coordinates, not a clamped frontal ellipse or hidden sphere.
        xx=skin[:,0]*sign;medial=int(np.argmin(xx));lateral=int(np.argmax(xx));chain1=np.arange(medial,lateral+1) if medial<lateral else np.r_[np.arange(medial,len(skin)),np.arange(0,lateral+1)];chain2=np.arange(lateral,medial+1) if lateral<medial else np.r_[np.arange(lateral,len(skin)),np.arange(0,medial+1)]
        chain2=chain2[::-1];upper,lower=(chain1,chain2) if skin[chain1,2].mean()>skin[chain2,2].mean() else (chain2,chain1)
        for part,chain in [('upper',upper),('lower',lower)]:
            arrays[f'{side}_{part}_skin']=skin[chain];arrays[f'{side}_{part}_normals']=normals[chain];arrays[f'{side}_{part}_triangles']=tids[chain]
        out[side]={'nativeFrontRimVertices':ids.tolist(),'nativePositionsM':p.tolist(),'samples':len(skin),'actualEyeGapRangeM':[float(gap.min()),float(np.median(gap)),float(gap.max())],'sampleReferenceToActualBodyProjectionM':[float(projection.min()),float(projection.max())],'medialPointM':skin[medial].tolist(),'lateralPointM':skin[lateral].tolist(),'parts':{'upperSamples':len(upper),'lowerSamples':len(lower)},'sampledRows':[{'point':skin[k].tolist(),'normal':normals[k].tolist(),'bodyTriangle':int(tids[k]),'nearestEyeSurfaceGapM':float(gap[k])} for k in np.linspace(0,len(skin)-1,33,dtype='i4')]}
    np.savez_compressed(E/'actual-lid-margin.npz',**arrays);save('rim-inspection.json',{'source':str(SRC),'sourceSha256':b.sha(SRC),'sides':out,'bodyTriangles':len(T),'seconds':time.time()-start,'scope':'Reference curve projected to actual saved evaluated skin. This is attachment anatomy inspection, not a meniscus, deforming rig or complete collision proof.'});print('R37_MARGIN_INSPECT',json.dumps({s:{k:x[k] for k in ('nativeFrontRimVertices','actualEyeGapRangeM','medialPointM','lateralPointM','parts')} for s,x in out.items()}),flush=True)
if __name__=='__main__':main()
