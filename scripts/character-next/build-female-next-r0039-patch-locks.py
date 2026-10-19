"""B: same-root patch-local guide interpolation, independent full 3D locks.
A's smooth cross-domain interpolation erases negative spaces. Here each scalp
patch retains multiple complete guides and two free-volume dimensions; no
shared per-lock exit, random scatter or single-axis funnel is introduced.
"""
import bpy,importlib.util,json,math,time
from pathlib import Path
import numpy as np
from mathutils.bvhtree import BVHTree
sp=importlib.util.spec_from_file_location('a39patch',Path(__file__).with_name('build-female-next-r0039-complete-guides.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a)
m=a.m;f=a.f;b=a.b;v=a.v;S=a.S;E=a.E
OUT=S/'aevrynd-female-next-r0039-b-patch-local-locks.blend';GROUPS=12
# Explicit regional styling in radial/tangent/z millimetres at upper, middle,
# terminal control levels. Neighboring locks intentionally have different
# bows/curls; opposite sides have independent settings.
STYLE={
 -1:np.array([[(2,-2,1),(8,-5,1),(-3,4,10)],[(1,1,0),(-1,4,0),(-5,6,2)],[(3,-1,1),(6,-3,-1),(-4,4,8)],[(0,2,0),(4,6,1),(-6,8,-3)],[(-1,1,0),(-2,4,0),(-3,-5,6)],[(2,-1,1),(9,-3,0),(-2,-6,10)],[(1,2,1),(3,5,0),(-7,1,1)],[(3,1,0),(7,4,-1),(0,-4,7)],[(0,-1,0),(1,-5,0),(-4,-7,-3)],[(1,2,1),(8,3,0),(-6,3,6)],[(2,-1,0),(-2,4,1),(-3,7,10)],[(0,1,0),(4,-2,0),(-1,-5,2)]],dtype='f8')*.001,
 1:np.array([[(1,1,1),(5,4,0),(-5,-5,7)],[(3,-1,0),(8,-3,1),(-2,6,-1)],[(0,2,1),(2,5,0),(-7,2,10)],[(2,1,0),(7,-4,-1),(-3,-6,4)],[(1,-2,0),(-1,3,0),(-5,6,-3)],[(3,1,1),(6,4,0),(-2,1,8)],[(0,2,0),(9,-3,1),(-4,-5,3)],[(1,-1,0),(2,-5,0),(-6,4,10)],[(2,1,1),(7,3,-1),(0,7,4)],[(0,2,0),(4,-4,1),(-5,2,-2)],[(3,-1,1),(8,4,0),(-2,-6,8)],[(1,1,0),(1,-3,0),(-4,5,1)]],dtype='f8')*.001}
WIDTH={-1:np.array((.82,.89,.76,.84,.92,.80,.86,.78,.90,.83,.88,.79)),1:np.array((.88,.79,.85,.91,.80,.84,.77,.87,.82,.90,.78,.85))}
def owner(params,parts):return (parts>0).astype('i4')*GROUPS+np.minimum((params[:,0]/math.pi*GROUPS).astype('i4'),GROUPS-1)
def new_bindings(roots,params,parts,ids):
    groups=owner(params,parts);gg=groups[ids];indices=np.empty((len(roots),3),dtype='i4');weights=np.empty((len(roots),3),dtype='f4');counts={}
    for group in range(GROUPS*2):
        ci=np.flatnonzero(groups==group);gi=np.flatnonzero(gg==group);assert len(gi)>=3
        D=np.sum((roots[ci,None]-roots[ids[gi]][None,:])**2,axis=2);order=np.argsort(D,axis=1)[:,:3]
        ds=np.take_along_axis(D,order,axis=1);w=1/np.maximum(ds,1e-16);w/=w.sum(1)[:,None]
        indices[ci]=gi[order];weights[ci]=w;counts[str(group)]={'guides':len(gi),'fibres':len(ci)}
    return indices,weights,groups,counts
def free_control(a0,u,side,level):
    gi=min(int(a0/math.pi*GROUPS),GROUPS-1);center=(gi+.5)*math.pi/GROUPS
    aa=center+(a0-center)*WIDTH[side][gi]
    IN,OUTER=[(a.UP_IN,a.UP_OUT),(a.MID_IN,a.MID_OUT),(a.TIP_IN,a.TIP_OUT)][level]
    q=a.row_at(IN,OUTER,float(aa),u,side,level)
    axis=a.norm(np.array((q[0],q[1]+.015,0.)));tangent=np.array((-axis[1],axis[0],0.))
    radial,tan,dz=STYLE[side][gi,level]
    q+=axis*radial+tangent*tan+np.array((0,0,dz))
    return q
def path(tree,tri,az,u,side,root):
    g=f.flowcheck;theta0=g.theta_min(az)+(1.54-g.theta_min(az))*u
    # Strictly monotone azimuth map: derivative is1-.75/pi>0. A's
    # nonlinear front sweep can reverse order; no such root route is reused.
    phi_end=.75+(1-.75/math.pi)*az;theta_end=min(theta0,.16+.48*u);proximal=[]
    for t in np.linspace(0,1,89):
        s=t*t*(3-2*t);hit,normal,tid,bary=g.scalp(tree,tri,side*(az+(phi_end-az)*s),theta0+(theta_end-theta0)*s)
        proximal.append(hit+normal*(.00018+(.0028+.0045*u)*math.sin(.5*math.pi*t)**1.4))
    proximal=np.array(proximal);proximal[0]=root
    upper,middle,tip=[free_control(az,u,side,k) for k in range(3)]
    upper[2]=min(upper[2],proximal[-1,2]-.016);middle[2]=min(middle[2],upper[2]-.022);tip[2]=min(tip[2],middle[2]-.030)
    tangent=a.norm(proximal[-1]-proximal[-2])
    K=np.array((proximal[-1],proximal[-1]+tangent*.008,upper,middle,.30*middle+.70*tip,tip))
    P=np.vstack((proximal,a.bspline(K)[1:]));arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(P,axis=0),axis=1))]
    t=np.linspace(0,arc[-1],128);q=np.column_stack([np.interp(t,arc,P[:,k]) for k in range(3)]);q[0]=root
    return q,K
def main():
    start=time.time();assert b.sha(a.SRC)=='0f8707b92196bc58e158b997a9170f22708d5ddeb2c2e0d95856cbfd00bb4c04'
    a.save('b-round-contract.json',{'source':str(a.SRC),'sourceSha256':b.sha(a.SRC),'candidateCountThisRound':2,
      'Adecision':'Reject: smooth global guide-grid silhouette is a rounded continuous shell in both EEVEE and matched Cycles/Huang. Do not tune that global field.',
      'differentBasis':'Same-part patch-local interpolation with24own scalp domains, >=3complete guides per patch, independent upper/mid/tip styling and retained2Dwidth/depth. Strictly monotone proximal azimuth map replacesAfront order reversal.',
      'primaryHypothesis':'Preserve intentional free-length negative spaces and distinct lock bends instead of globally smoothing every guide into curtains.',
      'reference':'https://research.dreamworks.com/wp-content/uploads/2018/07/a36-somasundaram-Edited.pdf',
      'referenceUse':'Primary published art-directed clump-ID interpolation principle only; own data/math/node graph, no external groom or code imported.',
      'expectedVisibleChange':'Readable complete-head independent locks and varied end silhouettes without detached roots, wings or funnels.',
      'pilot':'256actual displayed followers/body; all12000remain for matched complete-head preview before expensive full contact proof.',
      'reject':['No full-head appearance gain','Disconnected rope/funnel/wing or source scalp detachment','Guide/body/root failure'],
      'scope':'Static visual candidate only; no self/dynamics/runtime acceptance.'})
    bpy.ops.wm.open_mainfile(filepath=str(a.SRC));s=bpy.context.scene;b.setup(s,b.config(s));before=f.state()
    hair=bpy.data.objects[f.OLD];base,rad=m.eval_arrays(hair);mx=np.array(hair.matrix_world);inv=np.linalg.inv(mx)
    guide=bpy.data.objects[m.GUIDE];gp,gr=v.hair_arrays(guide);old=np.load(S/'aevrynd-female-next-r0038-b-live-guide-bindings.npz');ids=old['guideRootIds']
    source=np.load(S/'aevrynd-female-next-r0033-c-bob-fibres.npz');params=source['scalpParams'];parts=source['parts']
    index,weights,groups,counts=new_bindings(base[:,0].astype('f8'),params,parts,ids)
    assert np.all(groups[ids[index]]==groups[:,None]) and np.max(np.abs(weights.sum(1)-1))<2e-7
    for k in range(3):
        hair.data.attributes['AFN38_Guide'+str(k)].data.foreach_set('value',index[:,k])
        hair.data.attributes['AFN38_Weight'+str(k)].data.foreach_set('value',weights[:,k])
    hair.data.update_tag();neutral,nr=m.eval_arrays(hair);assert np.array_equal(neutral,base) and np.array_equal(nr,rad)
    V,T=b.evaluated(bpy.data.objects[b.BODY],True);tree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True);tri=V[T];paths=[];controls=[]
    for k,(az,u) in enumerate(params[ids]):
        root=gp[k,0].astype('f8')@mx[:3,:3].T+mx[:3,3]
        P,K=path(tree,tri,float(az),float(u),int(parts[ids[k]]),root);paths.append(P);controls.append(K)
    P=np.array(paths);local=((P-mx[:3,3])@inv[:3,:3].T).astype('f4');local[:,0]=gp[:,0]
    guide.data.position_data.foreach_set('vector',local.ravel());guide.data.update_tag()
    out,r=m.eval_arrays(hair);assert np.array_equal(out[:,0],base[:,0]) and np.array_equal(r,rad);assert f.state()==before
    world=out.astype('f8')@mx[:3,:3].T+mx[:3,3];rr=r.astype('f8')*np.linalg.norm(mx[:3,:3],ord=2)
    audit=f.flowcheck.check(world[ids],rr[ids],tree,tri);a.save('b-representative-body-contact.json',audit)
    f.E=E;f.render('b-after')
    cache=S/'aevrynd-female-next-r0039-b-patch-local-controls.npz'
    np.savez_compressed(cache,guidePositions=local,guideRootIds=ids,indices=index,weights=weights,groups=groups,freeControlsWorld=np.array(controls))
    b.camera('face');s.camera.data.lens=85;s['AFN39_status']='PATCH_LOCAL_GUIDE_LOCK_VISUAL_CANDIDATE_NOT_CONTACT_ACCEPTED'
    bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    a.save('b-build.json',{'output':str(OUT),'outputSha256':b.sha(OUT),'cache':str(cache),'sourceStateExactExceptIntentionalGuideAndCurveBindingAttrs':True,
      'radiiRootsCountMaterialsAndStageExact':True,'displayFibres':len(out),'pointsPerFibre':128,'guides':len(ids),'patches':counts,
      'AfrontSweepCanReverseOrder':True,'BproximalAzimuthDerivativeRange':[1-.75/math.pi,1.],
      'representativeBody':audit,'fullChildrenBody':'NOT_TESTED','self':'NOT_TESTED','dynamicsRuntime':'NOT_IMPLEMENTED',
      'stylesWorldRadialTangentZ':{str(k):val.tolist() for k,val in STYLE.items()},'withinPatchWidths':{str(k):val.tolist() for k,val in WIDTH.items()},
      'decision':'AWAIT_COMPLETE_HEAD_REVIEW' if audit['status']=='PASS_TESTED_STATIC_CAPSULES' else 'FAIL_REPRESENTATIVE_BODY_CONTACT','seconds':time.time()-start})
    print('R39_B_DONE',audit['status'],time.time()-start,flush=True)
if __name__=='__main__':main()
