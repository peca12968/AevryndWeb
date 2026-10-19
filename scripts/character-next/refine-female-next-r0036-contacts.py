"""Resolve the bounded simultaneous solver's measured residual contacts.

Constraint graph coloring eliminates Jacobi averaging at crowded contacts.
Same 900 follicles, radii, image paths, materials and scalp/body/eye state.
This is a static contact correction, not a second appearance claim.
"""
import bpy,importlib.util,json,time,copy
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
def module(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
c=module('c36','build-female-next-r0036-brows.py');f=module('f36','solve-female-next-r0036-brow-contacts.py');b=c.b;v=c.v;E=c.E;S=c.S
def main():
    start=time.time();old=c.read('a-build.json');assert b.sha(Path(old['output']))==old['outputSha256'];proof=c.read('a-saved-verification.json');assert proof['browSelf']['notCertifiedSeparated']==10 and proof['body']['status']=='PASS_TESTED_STATIC_CAPSULES'
    bpy.ops.wm.open_mainfile(filepath=old['output']);s=bpy.context.scene;original=c.state();source_cache=np.load(old['cache']);raw=[];P=[];r=[];matrices=[]
    for name in old['objects']:
        o=bpy.data.objects[name];p,rr=v.hair_arrays(o);mx=np.array(o.matrix_world);raw.append(p.copy());matrices.append(mx);P.append(p.astype('f8')@mx[:3,:3].T+mx[:3,3]);r.append(rr.astype('f8')*np.linalg.norm(mx[:3,:3],ord=2))
    P=np.concatenate(P);r=np.concatenate(r);rest=P.copy();fixed=P[:,0].copy();flat=P.reshape(-1,3);size=P.shape[1];n=size-1;body=bpy.data.objects[b.BODY];V,T=b.evaluated(body,True);bt=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True,epsilon=0.)
    hits=[bt.find_nearest(Vector(p)) for p in flat];floor=np.array([list(h[0]) for h in hits]);normal=np.array([list(h[1]) for h in hits]);normal/=np.linalg.norm(normal,axis=1)[:,None];history=[]
    for iteration in range(18):
        ids,gap,_,_=f.contacts(P,r,8e-6);active=ids[gap<4e-6];history.append({'iteration':iteration,'below4MicrometreDesignMargin':len(active),'below1MicrometreQualificationMargin':int((gap<=1e-6).sum()),'minimumTestedPairCapsuleGapM':float(gap.min())});print('R36_COLORED',history[-1],flush=True)
        if not len(active):break
        vi=active[:,0]//n*size+active[:,0]%n;vj=active[:,1]//n*size+active[:,1]%n;groups=[];used=[]
        for row,(i,j) in enumerate(zip(vi,vj)):
            vertices={int(i),int(i+1),int(j),int(j+1)}
            for k,taken in enumerate(used):
                if vertices.isdisjoint(taken):groups[k].append(row);taken.update(vertices);break
            else:groups.append([row]);used.append(set(vertices))
        for group in groups:
            group=np.array(group,dtype='i4');ia=vi[group];ib=vj[group];di,ss,tt=f.distances(flat[ia],flat[ia+1],flat[ib],flat[ib+1]);radi=np.maximum(r[:,:-1],r[:,1:]).ravel();rr=radi[active[group,0]]+radi[active[group,1]];needed=np.maximum(4.5e-6+rr-di,0)
            direction=(flat[ia]*(1-ss[:,None])+flat[ia+1]*ss[:,None]-flat[ib]*(1-tt[:,None])-flat[ib+1]*tt[:,None])/np.maximum(di[:,None],1e-12)
            ma=(ia%size)!=0;mb=(ib%size)!=0;den=ma*(1-ss)**2+ss*ss+mb*(1-tt)**2+tt*tt;correction=needed/np.maximum(den,1e-12)
            for indices,weight,sign,movable in [(ia,1-ss,1,ma),(ia+1,ss,1,np.ones(len(ia),bool)),(ib,1-tt,-1,mb),(ib+1,tt,-1,np.ones(len(ia),bool))]:flat[indices]+=direction*(sign*correction*weight*movable)[:,None]
        depth=np.einsum('ij,ij->i',flat-floor,normal);flat+=normal*np.maximum(r.ravel()+25e-6-depth,0)[:,None];P[:,0]=fixed
        assert np.linalg.norm(P-rest,axis=2).max()<.00010
    # Serialized precision is rechecked independently in the final verifier.
    local=[]
    for index,name in enumerate(old['objects']):
        o=bpy.data.objects[name];mx=matrices[index];inv=np.linalg.inv(mx);p=(P[index*450:(index+1)*450]-mx[:3,3])@inv[:3,:3].T;p=p.astype('f4');p[:,0]=raw[index][:,0];o.data.position_data.foreach_set('vector',p.ravel());local.append(p)
    local=np.concatenate(local);assert np.array_equal(local[:,0],source_cache['positions'][:,0]);bpy.context.view_layer.update();assert c.state()==original
    cache_path=S/'aevrynd-female-next-r0036-b-brow-fibres.npz';data={k:source_cache[k] for k in source_cache.files};data['positions']=local;np.savez_compressed(cache_path,**data)
    for name in old['objects']:bpy.data.objects[name]['AFN36_binding_cache']=cache_path.name
    out=S/'aevrynd-female-next-r0036-b-contact-refined-brows.blend';s['AFN36_status']='PENDING_REOPENED_NEUTRAL_BROW_CONTACT_AND_APPEARANCE';c.camera('face');bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out),compress=True)
    report=copy.deepcopy(old);report.update({'output':str(out),'outputSha256':b.sha(out),'cache':str(cache_path),'cacheSha256':b.sha(cache_path),'parentCandidate':old['output'],'parentCandidateSha256':old['outputSha256'],'decision':'PENDING_SAVED_CONTACT_AND_APPEARANCE','contactCorrection':{'method':'Globally coupled finite-capsule constraint graph coloring; each disjoint batch projected without averaged-away residual corrections. Same roots, radii and authored style; no density/material or source changes.','sweeps':history,'all900RootLocalCoordinatesExact':True,'maximumWorldDisplacementFromAM':float(np.linalg.norm(P-rest,axis=2).max()),'maximumAllowedDisplacementFromAM':.00010},'seconds':time.time()-start})
    c.save('b-build.json',report);c.render('b-after');print('R36_B_CONTACT_REFINEMENT_DONE',time.time()-start,flush=True)
if __name__=='__main__':main()
