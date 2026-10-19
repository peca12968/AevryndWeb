"""Actual body first/last projected depth for an authored visual-hull proxy."""
from pathlib import Path
import bpy,importlib.util,numpy as np,time,json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sp=importlib.util.spec_from_file_location('depth54',Path(__file__).with_name('build-female-next-r0054-clump-volume.py'))
k=importlib.util.module_from_spec(sp);sp.loader.exec_module(k)
b=k.b;E=k.E

def main():
    tick=time.time();bpy.ops.wm.open_mainfile(filepath=str(k.SRC));before=k.f.state()
    V,T=b.evaluated(bpy.data.objects[b.BODY],True);tree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True)
    a=np.load(E/'concept-hull-masks.npz');x,y,z=a['x'],a['y'],a['z']
    front=np.full((len(x),len(z)),np.inf,dtype='f4');back=np.full_like(front,-np.inf)
    left=np.full((len(y),len(z)),np.inf,dtype='f4');right=np.full_like(left,-np.inf)
    for i,xx in enumerate(x):
        for j,zz in enumerate(z):
            p=tree.ray_cast(Vector((xx,-.3,zz)),Vector((0,1,0)),.6)[0]
            q=tree.ray_cast(Vector((xx,.3,zz)),Vector((0,-1,0)),.6)[0]
            if p is not None:front[i,j]=p.y
            if q is not None:back[i,j]=q.y
    for i,yy in enumerate(y):
        for j,zz in enumerate(z):
            p=tree.ray_cast(Vector((-.3,yy,zz)),Vector((1,0,0)),.6)[0]
            q=tree.ray_cast(Vector((.3,yy,zz)),Vector((-1,0,0)),.6)[0]
            if p is not None:left[i,j]=p.x
            if q is not None:right[i,j]=q.x
    assert k.f.state()==before
    np.savez_compressed(E/'concept-hull-body-depths.npz',frontY=front,backY=back,leftX=left,rightX=right)
    k.save('concept-hull-depth-source.json',{'source':str(k.SRC),'sourceSha256':b.sha(k.SRC),'bodyUnchanged':True,
        'bodyVertices':len(V),'bodyTriangles':len(T),'rays':2*(len(x)+len(y))*len(z),
        'scope':'First/last projected body depth only; not a closed-solid or continuous collision qualification.',
        'seconds':time.time()-tick})
    print('R54_BODY_DEPTHS',time.time()-tick,flush=True)

if __name__=='__main__':main()
