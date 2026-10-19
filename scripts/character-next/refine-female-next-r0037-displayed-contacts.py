"""Bounded same-candidate exact-display contact repair; roots/radii unchanged.

No nearest-skin tangent-plane pushes. Ill-conditioned root-envelope constraints
are deferred to exact displayed surface/containment verification, never waived.
"""
import bpy,importlib.util,json,time,copy
import numpy as np
from pathlib import Path
def module(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
c=module('c37','build-female-next-r0037-explicit-lashes.py');g=c.g;f=c.f;b=c.b;v=c.v;E=c.E;S=c.S
def main():
    start=time.time();build=g.read('c-final-build.json');source=Path(build['output']);assert b.sha(source)==build['outputSha256'];bind=g.read('c-exact-lash-bindings.json');cache=np.load(bind['cache']);P=cache['positionsWorld'].copy();R=cache['radiiWorld'].copy();rest=P.copy();fixed=P[:,0].copy();flat=P.reshape(-1,3);size=P.shape[1];n=size-1;history=[]
    for iteration in range(24):
        ids,gap,_,_=f.contacts(P,R,8e-6);different=ids[:,0]//n!=ids[:,1]//n;ids=ids[different];gap=gap[different];active=ids[gap<4e-6];previous=P.copy();deferred=0;applied=0
        for i,j in active:
            ia=i//n*size+i%n;ib=j//n*size+j%n;di,ss,tt=f.distances(flat[ia:ia+1],flat[ia+1:ia+2],flat[ib:ib+1],flat[ib+1:ib+2]);d=float(di[0]);s=float(ss[0]);t=float(tt[0]);radius=max(R.ravel()[ia],R.ravel()[ia+1])+max(R.ravel()[ib],R.ravel()[ib+1]);need=max(0.,radius+4.5e-6-d);ma=ia%size!=0;mb=ib%size!=0;den=ma*(1-s)**2+s*s+mb*(1-t)**2+t*t
            if den<.01:deferred+=1;continue
            if need<=0:continue
            delta=((1-s)*flat[ia]+s*flat[ia+1]-(1-t)*flat[ib]-t*flat[ib+1])/max(d,1e-12);step=need/den
            for k,w,sign,movable in [(ia,1-s,1,ma),(ia+1,s,1,True),(ib,1-t,-1,mb),(ib+1,t,-1,True)]:flat[k]+=delta*(step*w*sign*movable)
            applied+=1
        P[:,0]=fixed;maximum=float(np.linalg.norm(P-rest,axis=2).max());row={'iteration':iteration,'candidatePairsBelowDesign':len(active),'deferredIllConditionedRootEnvelopes':deferred,'appliedCoupledFreePointConstraints':applied,'maximumDisplacementM':maximum};history.append(row)
        if maximum>.00010:P[:]=previous;row['rejectedStepAndRolledBack']=True;break
        if applied==0:break
    assert np.array_equal(P[:,0],fixed) and np.linalg.norm(P-rest,axis=2).max()<=.00010;bpy.ops.wm.open_mainfile(filepath=str(source));before=g.state();body=bpy.data.objects[b.BODY];inv=np.linalg.inv(np.array(body.matrix_world));delta=[]
    for rec,control in zip(bind['meshRecords'],bind['controls']):
        a=rec['firstCurve'];z=a+rec['curves'];o=bpy.data.objects[rec['object']];oldmat=o.data.materials[0];vertices=[];faces=[]
        for p,r in zip(P[a:z],R[a:z]):vv,tt=c.tube(p,r);offset=len(vertices);vertices.extend(vv);faces.extend(tt+offset)
        local=((np.array(vertices)-np.array(body.matrix_world)[:3,3])@inv[:3,:3].T).astype('f4');me=bpy.data.meshes.new(o.name+'_ContactResolved');me.from_pydata(local,[],faces);me.update();me.materials.append(oldmat);o.data=me
        for polygon in me.polygons:polygon.use_smooth=True
        control_object=bpy.data.objects[control];mx=np.array(control_object.matrix_world);mi=np.linalg.inv(mx[:3,:3]);control_object.data.position_data.foreach_set('vector',((P[a:z]-mx[:3,3])@mi.T).astype('f4').ravel());delta.append({'object':o.name,'maximumControlDisplacementM':float(np.linalg.norm(P[a:z]-rest[a:z],axis=2).max())})
    bpy.context.view_layer.update();assert g.state()==before;path=S/'aevrynd-female-next-r0037-c-resolved-lashes.npz';np.savez_compressed(path,positionsWorld=P,radiiWorld=R);newbind=copy.deepcopy(bind);newbind.update({'cache':str(path),'cacheSha256':b.sha(path)});g.save('c-final-lash-bindings.json',newbind);out=S/'aevrynd-female-next-r0037-c-final-contact-review.blend';g.c.camera('face');bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out),compress=True);new=copy.deepcopy(build);g.save('c-exact-final-build.json',build);new.update({'parentReview':str(source),'parentReviewSha256':b.sha(source),'output':str(out),'outputSha256':b.sha(out),'contactRelaxation':{'maximumDisplacementM':float(np.linalg.norm(P-rest,axis=2).max()),'maximumAllowedDisplacementM':.00010,'allRootsExact':True,'allRadiiExact':True,'history':history,'scope':'No skin halfspace pushes; exact displayed closed-mesh verification must resolve every remaining conservative envelope overlap. No collision tolerance changed.'}});g.save('c-final-build.json',new);g.save('c-displayed-contact-correction.json',{'source':str(source),'sourceSha256':b.sha(source),'output':str(out),'outputSha256':b.sha(out),'groups':delta,'history':history});g.render('c-after');g.closeup('c-after');print('R37_DISPLAY_CORRECTION_DONE',time.time()-start,flush=True)
if __name__=='__main__':main()
