"""Private C: actual-body local surface graph routes at failed hair segments.
Static authoring only. Each visibility edge passes full finite capsule test;
roots/endpoints retained, no contact exception and no density/tolerance trick.
"""
import bpy,importlib.util,json,time,heapq
from pathlib import Path
import numpy as np
import sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
sp=importlib.util.spec_from_file_location('adapt40',Path(__file__).with_name('build-female-next-r0040-adaptive-paths.py'));ad=importlib.util.module_from_spec(sp);sp.loader.exec_module(ad)
rod=ad.rod;a=ad.a;m=ad.m;f=ad.f;b=ad.b;v=ad.v;E=ad.E;PVT=ad.PVT

def unpack(file):
    d=np.load(file);o=d['offsets'];return [d['positionsWorld'][o[k]:o[k+1]].astype('f8') for k in range(len(o)-1)],[d['parameters'][o[k]:o[k+1]].copy() for k in range(len(o)-1)]

def normals(V,T):
    n=np.zeros_like(V);F=V[T];q=np.cross(F[:,1]-F[:,0],F[:,2]-F[:,0])
    for j in range(3):np.add.at(n,T[:,j],q)
    n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-20);return n

def route(A,B,V,T,N,tree,tri,radius,ball=.012,offsets=None):
    centre=(A+B)*.5;selected=np.flatnonzero(np.linalg.norm(V-centre,axis=1)<ball)
    lookup=np.full(len(V),-1,dtype='i4');lookup[selected]=np.arange(len(selected));localT=lookup[T];localT=localT[np.all(localT>=0,axis=1)]
    if len(localT)==0:return None,{'reason':'empty local surface graph'}
    offsets=offsets or (radius+.00035,);count=len(selected)
    G=np.vstack((A,B,*[V[selected]+N[selected]*offset for offset in offsets]));adj=[set() for x in G]
    for layer in range(len(offsets)):
        for t in localT+2+layer*count:
            for j,k in ((0,1),(1,2),(2,0)):adj[t[j]].add(int(t[k]));adj[t[k]].add(int(t[j]))
        kd=KDTree(count)
        for j,x in enumerate(G[2+layer*count:2+(layer+1)*count]):kd.insert(Vector(x),j+2+layer*count)
        kd.balance()
        for k in (0,1):
            for _,j,dist in kd.find_n(Vector(G[k]),min(24,count)):adj[k].add(j);adj[j].add(k)
        if layer:
            for j in range(count):
                lo=2+(layer-1)*count+j;hi=lo+count;adj[lo].add(hi);adj[hi].add(lo)
    ds={};outside={};edges={};queue=[(float(np.linalg.norm(B-A)),0.,0)];cost={0:0.};parent={};expanded=0
    def point(j):
        if j not in ds:ds[j]=tree.find_nearest(Vector(G[j]))[3];outside[j]=ds[j]>radius+1e-6 and f.flowcheck.cap.solid.classify(tree,tri,Vector(G[j]))=='outside'
        return outside[j]
    def edge(j,k):
        key=tuple(sorted((j,k)))
        if key not in edges:
            if not point(j) or not point(k):edges[key]=False
            else:edges[key]=f.flowcheck.cap.segment_test(G[j],G[k],ds[j],ds[k],radius,tree,tri)[0]>0
        return edges[key]
    while queue:
        _,c,j=heapq.heappop(queue)
        if c>cost[j]+1e-12:continue
        expanded+=1
        if j==1:
            path=[1]
            while path[-1]!=0:path.append(parent[path[-1]])
            path=path[::-1];return G[path],{'nodes':len(G),'expanded':expanded,'checkedEdges':len(edges),'pathPoints':len(path),'routeLengthM':c,'ballM':ball}
        if expanded>30000:break
        for k in sorted(adj[j]):
            new=c+float(np.linalg.norm(G[j]-G[k]))
            if new>=cost.get(k,float('inf')):continue
            if not edge(j,k):continue
            cost[k]=new;parent[k]=j;heapq.heappush(queue,(new+float(np.linalg.norm(G[k]-B)),new,k))
    return None,{'nodes':len(G),'expanded':expanded,'checkedEdges':len(edges),'reason':'No capsule-safe local graph route'}

def main():
    start=time.time();refine='--refine' in sys.argv;tag='c-refined' if refine else 'c'
    paths,params=unpack(PVT/('c-surface-guide-paths.npz' if refine else 'b-adaptive-guide-paths.npz'));bpy.ops.wm.open_mainfile(filepath=str(rod.SRC));s=bpy.context.scene;b.setup(s,b.config(s))
    V,T=b.evaluated(bpy.data.objects[b.BODY],True);tree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True);tri=V[T];N=normals(V,T);f.flowcheck.cap.math_controls();rows=[]
    for it in range(3):
        proof=f.flowcheck.check(paths,[np.full(len(x),.000046) for x in paths],tree,tri)
        if proof['status']=='PASS_TESTED_STATIC_CAPSULES':break
        groups={}
        for q in proof['failureSamples']:groups.setdefault(q['curve'],[]).append(q['segment'])
        for ci,segments in groups.items():
            for j in sorted(segments,reverse=True):
                Q,info=route(paths[ci][j],paths[ci][j+1],V,T,N,tree,tri,.000046,ball=.025 if refine else .012,offsets=(.00010,.000396,.0015) if refine else None)
                row={'iteration':it,'curve':ci,'segment':j,'success':Q is not None,**info};rows.append(row);print('R40_ROUTE',row,flush=True)
                if Q is None:continue
                arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(Q,axis=0),axis=1))];t=params[ci][j]+(params[ci][j+1]-params[ci][j])*arc/arc[-1]
                paths[ci]=np.vstack((paths[ci][:j+1],Q[1:-1],paths[ci][j+1:]));params[ci]=np.r_[params[ci][:j+1],t[1:-1],params[ci][j+1:]]
    ad.pack(paths,params,PVT/f'{tag}-surface-guide-paths.npz');proof=f.flowcheck.check([x.astype('f4').astype('f8') for x in paths],[np.full(len(x),.000046) for x in paths],tree,tri)
    ad.save(f'{tag}-guide-surface-routes.json',{'status':proof['status'],'body':proof,'routes':rows,'seconds':time.time()-start,'method':'Actual body topology local A-star graph; every used point outside closed body, every used edge passes full finite capsule test. No resampling.','radiusM':.000046,'designStandOffM':[.00010,.000396,.0015] if refine else .000396,'notInextensibleDynamicsOrSelfProof':True})
    print('R40_C_DONE',proof['status'],proof['unqualifiedSegments'],time.time()-start,flush=True)

if __name__=='__main__':main()
