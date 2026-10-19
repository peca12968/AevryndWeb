"""Final bounded anatomical root-layout repair; no strand/radius removal.

Fixed roots were disproven at a true crossing. Simultaneous tangent repulsion
on the actual same lid skin rebinds any moved follicles with exact barycentrics.
This is not a root-off-skin lift or a changed contact tolerance.
"""
import bpy,importlib.util,time,copy
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
spec=importlib.util.spec_from_file_location('r37',Path(__file__).with_name('refine-female-next-r0037-displayed-contacts.py'));r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r);c=r.c;g=r.g;b=r.b;v=r.v;E=r.E;S=r.S
def main():
    start=time.time();build=g.read('c-final-build.json');source=Path(build['output']);assert b.sha(source)==build['outputSha256'];bindings=g.read('c-final-lash-bindings.json');cache=np.load(bindings['cache']);P=cache['positionsWorld'].copy();R=cache['radiiWorld'].copy();initial=P.copy();rows=bindings['roots'];bpy.ops.wm.open_mainfile(filepath=str(source));before=g.state();body=bpy.data.objects[b.BODY];V,T=b.evaluated(body,True);bt=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True);history=[]
    for iteration in range(6):
        root=P[:,0];dist=np.linalg.norm(root[:,None]-root[None,:],axis=2);required=R[:,0,None]+R[None,:,0]+8e-6;i,j=np.where(np.triu(dist<required,1));history.append({'iteration':iteration,'closeRootPairs':len(i)})
        if not len(i):break
        delta=np.zeros_like(root);count=np.zeros(len(root))
        for a,z in zip(i,j):
            n=np.array(rows[a]['normal'])+np.array(rows[z]['normal']);n/=np.linalg.norm(n);d=root[a]-root[z];tangent=d-n*(d@n);tangent/=max(np.linalg.norm(tangent),1e-12);step=(required[a,z]-dist[a,z])*.60;delta[a]+=tangent*step;delta[z]-=tangent*step;count[a]+=1;count[z]+=1
        delta/=np.maximum(count[:,None],1.)
        for k in np.flatnonzero(count):
            target=np.array(rows[k]['surfaceM'])+delta[k];hit,n,tid,d=bt.find_nearest(Vector(target));tri=V[T[tid]];co=np.linalg.lstsq(np.column_stack((tri[1]-tri[0],tri[2]-tri[0])),np.array(hit)-tri[0],rcond=None)[0];bc=np.maximum(0,np.array((1-co.sum(),co[0],co[1])));bc/=bc.sum();skin=bc@tri;nn=np.array(n);nn/=np.linalg.norm(nn);newroot=skin+nn*rows[k]['standOffM'];shift=newroot-P[k,0];P[k]+=shift;rows[k].update({'bodyTriangle':int(tid),'bodyVertices':T[tid].tolist(),'barycentric':bc.tolist(),'surfaceM':skin.tolist(),'normal':nn.tolist(),'rootLayoutCorrectionM':(P[k,0]-initial[k,0]).tolist()})
        assert np.linalg.norm(P[:,0]-initial[:,0],axis=1).max()<50e-6
    inv=np.linalg.inv(np.array(body.matrix_world));moved=[]
    for rec,control in zip(bindings['meshRecords'],bindings['controls']):
        a=rec['firstCurve'];z=a+rec['curves'];o=bpy.data.objects[rec['object']];mat=o.data.materials[0];vertices=[];faces=[]
        for p,rr in zip(P[a:z],R[a:z]):vv,tt=c.tube(p,rr);offset=len(vertices);vertices.extend(vv);faces.extend(tt+offset)
        local=((np.array(vertices)-np.array(body.matrix_world)[:3,3])@inv[:3,:3].T).astype('f4');me=bpy.data.meshes.new(o.name+'_RootLayout');me.from_pydata(local,[],faces);me.update();me.materials.append(mat);o.data=me
        for polygon in me.polygons:polygon.use_smooth=True
        co=bpy.data.objects[control];mx=np.array(co.matrix_world);co.data.position_data.foreach_set('vector',((P[a:z]-mx[:3,3])@np.linalg.inv(mx[:3,:3]).T).astype('f4').ravel())
    bpy.context.view_layer.update();assert g.state()==before;path=S/'aevrynd-female-next-r0037-c-follicle-layout-lashes.npz';np.savez_compressed(path,positionsWorld=P,radiiWorld=R);bindings.update({'cache':str(path),'cacheSha256':b.sha(path)});g.save('c-final-lash-bindings.json',bindings);out=S/'aevrynd-female-next-r0037-c-anatomical-eye-review.blend';g.c.camera('face');bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out),compress=True);new=copy.deepcopy(build);g.save('c-before-layout-build.json',build);layout={'history':history,'movedFollicles':int((np.linalg.norm(P[:,0]-initial[:,0],axis=1)>1e-10).sum()),'maximumRootDisplacementM':float(np.linalg.norm(P[:,0]-initial[:,0],axis=1).max()),'maximumAllowedRootDisplacementM':50e-6,'all220ShapesAndRadiiRetained':True,'newBindingsOnActualSameSkin':True,'source':str(source),'sourceSha256':b.sha(source),'seconds':time.time()-start};new.update({'output':str(out),'outputSha256':b.sha(out),'rootLayoutCorrection':layout});g.save('c-final-build.json',new);g.save('c-root-layout-correction.json',layout);g.render('c-after');g.closeup('c-after');print('R37_ROOT_LAYOUT_DONE',layout,flush=True)
if __name__=='__main__':main()
