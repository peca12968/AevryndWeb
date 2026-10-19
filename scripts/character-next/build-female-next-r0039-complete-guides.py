"""r39: own complete guide paths with separate inner/outer spatial controls.
No artist geometry/nodes copied. No old per-lock exit or random cross-section:
each actual scalp guide keeps its own rooted path and full free control cage.
"""
import bpy,importlib.util,json,math,time,sys
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sp=importlib.util.spec_from_file_location('live39',Path(__file__).with_name('build-female-next-r0038-live-groom.py'));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
f=m.f;b=m.b;v=m.v;S=m.S;R=f.R
E=R/'Evidence/character-female-next/r0039-complete-guides';E.mkdir(parents=True,exist_ok=True)
SRC=m.OUT;OUT=S/'aevrynd-female-next-r0039-a-complete-guide-paths.blend'
A=np.array((.004,.25,.55,.85,1.1,1.4,1.7,2.05,2.4,2.75,3.138))
# Each row is newly authored x/y/z (metres) for the RIGHT half. Separate
# inner/outer controls are spatial points, not a radius around one master.
UP_IN=np.array([(.067,-.102,1.497),(.075,-.093,1.491),(.084,-.076,1.488),(.088,-.050,1.482),(.091,-.025,1.479),(.091,.003,1.477),(.086,.029,1.479),(.074,.050,1.482),(.055,.065,1.482),(.029,.073,1.479),(.002,.075,1.476)])
UP_OUT=np.array([(.078,-.112,1.513),(.084,-.103,1.511),(.096,-.079,1.508),(.104,-.051,1.504),(.108,-.022,1.499),(.106,.008,1.498),(.100,.038,1.502),(.087,.062,1.503),(.064,.078,1.505),(.035,.086,1.502),(.003,.090,1.499)])
MID_IN=np.array([(.071,-.104,1.438),(.079,-.092,1.435),(.086,-.072,1.430),(.087,-.046,1.425),(.089,-.020,1.422),(.090,.008,1.419),(.083,.034,1.421),(.073,.056,1.424),(.052,.071,1.423),(.027,.079,1.420),(.001,.082,1.418)])
MID_OUT=np.array([(.086,-.107,1.443),(.094,-.092,1.440),(.101,-.066,1.432),(.100,-.038,1.428),(.103,-.010,1.426),(.108,.019,1.428),(.099,.044,1.430),(.083,.067,1.433),(.062,.082,1.431),(.030,.091,1.427),(.002,.094,1.424)])
TIP_IN=np.array([(.066,-.109,1.373),(.075,-.094,1.368),(.078,-.075,1.359),(.076,-.044,1.355),(.078,-.015,1.352),(.079,.013,1.349),(.075,.038,1.353),(.064,.059,1.356),(.044,.072,1.351),(.024,.078,1.348),(.001,.080,1.345)])
TIP_OUT=np.array([(.077,-.103,1.365),(.083,-.089,1.356),(.085,-.064,1.345),(.087,-.038,1.343),(.090,-.009,1.350),(.092,.019,1.355),(.086,.044,1.350),(.069,.066,1.345),(.049,.079,1.344),(.027,.083,1.350),(.002,.085,1.354)])
# Explicit opposite-side differences at the six independently authored rows.
LEFT_DY=np.array([-.002,-.004,-.002,.003,.005,.002,-.001,-.004,-.003,.002,.001])
LEFT_DX=np.array([.000,.002,.003,-.001,-.002,.000,.002,.002,.001,.000,.000])
LEFT_DZ=np.array([.005,.008,.004,-.002,-.004,-.003,.002,.005,.001,-.003,-.002])
def save(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def norm(p):return p/max(np.linalg.norm(p),1e-20)
def row_at(inner,outer,a,u,side,station):
    L=np.array([np.interp(a,A,inner[:,j]) for j in range(3)])
    H=np.array([np.interp(a,A,outer[:,j]) for j in range(3)])
    q=L*(1-u)+H*u
    if side<0:
        q[0]+=float(np.interp(a,A,LEFT_DX))*(.3+.7*u)
        q[1]+=float(np.interp(a,A,LEFT_DY))
        q[2]+=float(np.interp(a,A,LEFT_DZ))*(.35 if station==0 else 1.)
    q[0]*=side;return q
def bspline(K,n=129):
    degree=3;last=len(K)-1;knots=np.r_[np.zeros(4),np.linspace(0,1,last-degree+2)[1:-1],np.ones(4)]
    out=[]
    for t in np.linspace(0,1,n):
        k=last if t>=1 else int(np.searchsorted(knots,t,side='right')-1)
        d=[K[j].copy() for j in range(k-degree,k+1)]
        for r in range(1,degree+1):
            for j in range(degree,r-1,-1):
                lo=knots[j+k-degree];hi=knots[j+1+k-r];w=(t-lo)/(hi-lo) if hi>lo else 0
                d[j]=(1-w)*d[j-1]+w*d[j]
        out.append(d[degree])
    return np.array(out)
def path(tree,tri,a,u,side,root):
    g=f.flowcheck;theta0=g.theta_min(a)+(1.54-g.theta_min(a))*u
    # Each root latitude retains a different crown end; no group funnel.
    angle_end=a+(1.02-a)*max(0.,1-a/1.25)*.78
    theta_end=min(theta0,.16+.48*u)
    proximal=[]
    for t in np.linspace(0,1,89):
        s=t*t*(3-2*t)
        hit,normal,tid,bary=g.scalp(tree,tri,side*(a+(angle_end-a)*s),theta0+(theta_end-theta0)*s)
        loft=(.0028+.0045*u)*math.sin(.5*math.pi*t)**1.4
        proximal.append(hit+normal*(.00018+loft))
    proximal=np.array(proximal);proximal[0]=root
    upper=row_at(UP_IN,UP_OUT,a,u,side,0);middle=row_at(MID_IN,MID_OUT,a,u,side,1);tip=row_at(TIP_IN,TIP_OUT,a,u,side,2)
    upper[2]=min(upper[2],proximal[-1,2]-.016)
    middle[2]=min(middle[2],upper[2]-.022)
    tip[2]=min(tip[2],middle[2]-.030)
    tangent=norm(proximal[-1]-proximal[-2])
    K=np.array([proximal[-1],proximal[-1]+tangent*.008,upper,middle,.30*middle+.70*tip,tip])
    free=bspline(K)
    P=np.vstack((proximal,free[1:]));arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(P,axis=0),axis=1))]
    t=np.linspace(0,arc[-1],128);out=np.column_stack([np.interp(t,arc,P[:,j]) for j in range(3)]);out[0]=root
    return out,K
def section_diagnostic():
    rows={}
    for side in (-1,1):
        grid=np.array([[row_at(MID_IN,MID_OUT,float(a),float(u),side,1) for a in A] for u in np.linspace(0,1,7)])
        widths=np.linalg.norm(grid[-1]-grid[0],axis=1)
        areas=[]
        for j in range(6):
            for k in range(len(A)-1):
                a=grid[j,k];bb=grid[j,k+1];c=grid[j+1,k]
                areas.append(float(np.linalg.norm(np.cross(bb-a,c-a))*.5))
        rows[str(side)]={'innerOuterControlSeparationRangeM':[float(widths.min()),float(widths.max())],'minimumControlTriangleAreaM2':min(areas),
          'scope':'Free middle-control grid only; nonzero area is not proof of full swept volume, injectivity, self-contact or displayed child safety.'}
    return rows
def main():
    start=time.time();assert b.sha(SRC)=='0f8707b92196bc58e158b997a9170f22708d5ddeb2c2e0d95856cbfd00bb4c04'
    save('round-contract.json',{'revision':'female-next-r0039-a','source':str(SRC),'sourceSha256':b.sha(SRC),
      'previousGoalTurnClassification':'progress: r38B live authoring integrated with neutral exact rest; A/C real style failures stopped; pushed e342b35',
      'mainDefect':'Scalp cap and broad straight curtains dominate actual complete head. Face/eye synthetic rendering and missing dynamics remain secondary.',
      'hypothesis':'Complete independently rooted guide paths with explicitly distinct inner/outer3Dcontrol rows can preserve layer depth instead of merging free hair into a shared exit or single sheet.',
      'methodDifference':'Replace all guide CV paths, not Gaussian offsets of old curves or a shared whole-head velocity field. Rooted crown ends vary in both chart dimensions; every guide has its own complete free cage and endpoint. No per-lock random scatter/funnel.',
      'referenceBasis':'Current body geometry and local reference-only r34artist guide preview: observe layered paths and varied free silhouettes; no guide coordinates/node code copied.',
      'expectedVisibleChange':'Depth through crown/temple/back, coherent independently curved locks and differentiated ends on the same12000fibres/radii/materials/light.',
      'smallTest':'Actual displayed256representative follower fibres against actual body; free-control-grid areas and complete-head12kpreview before all-fibre contact expansion',
      'reject':['Guide/body or root failure','Cap/sheet/funnel/wing silhouette or no full-head benefit','Collapsed free control grid'],
      'candidateCount':1,'resources':{'startUTC':'2026-10-19 11:55:25 UTC','checkpointUTC':'2026-10-19 12:40:25 UTC','threads':4,'heavyJobsAtOnce':1},
      'scope':'Neutral static authoring candidate; not self, dynamics, clothing, runtime or acceptance.'})
    bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;b.setup(s,b.config(s));before=f.state();hair=bpy.data.objects[f.OLD]
    baseline,rad=m.eval_arrays(hair);mx=np.array(hair.matrix_world);inverse=np.linalg.inv(mx)
    guide=bpy.data.objects[m.GUIDE];gp,gr=v.hair_arrays(guide);bind=np.load(S/'aevrynd-female-next-r0038-b-live-guide-bindings.npz');ids=bind['guideRootIds']
    source=np.load(S/'aevrynd-female-next-r0033-c-bob-fibres.npz');params=source['scalpParams'][ids];parts=source['parts'][ids]
    V,T=b.evaluated(bpy.data.objects[b.BODY],True);tree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True);tri=V[T]
    f.E=E;f.render('before')
    controls=[];world_guides=[]
    for n,(a,u) in enumerate(params):
        root=gp[n,0].astype('f8')@mx[:3,:3].T+mx[:3,3]
        P,K=path(tree,tri,float(a),float(u),int(parts[n]),root);world_guides.append(P);controls.append(K)
    P=np.array(world_guides);local=((P-mx[:3,3])@inverse[:3,:3].T).astype('f4');local[:,0]=gp[:,0]
    guide.data.position_data.foreach_set('vector',local.ravel());guide.data.update_tag()
    out,r=m.eval_arrays(hair);assert np.array_equal(out[:,0],baseline[:,0]) and np.array_equal(r,rad);assert f.state()==before
    world=out.astype('f8')@mx[:3,:3].T+mx[:3,3];rr=r.astype('f8')*np.linalg.norm(mx[:3,:3],ord=2)
    audit=f.flowcheck.check(world[ids],rr[ids],tree,tri);save('a-representative-body-contact.json',audit)
    diagnostic=section_diagnostic();assert all(d['minimumControlTriangleAreaM2']>1e-8 for d in diagnostic.values());save('a-free-control-grid.json',diagnostic)
    f.render('a-after')
    np.savez_compressed(S/'aevrynd-female-next-r0039-a-complete-guide-controls.npz',guidePositions=local,guideRootIds=ids,freeControlsWorld=np.array(controls),params=params,parts=parts)
    b.camera('face');s.camera.data.lens=85;s['AFN39_status']='COMPLETE_GUIDE_PATH_VISUAL_CANDIDATE_NOT_CONTACT_MOTION_ACCEPTED'
    bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    save('a-build.json',{'output':str(OUT),'outputSha256':b.sha(OUT),'cache':str(S/'aevrynd-female-next-r0039-a-complete-guide-controls.npz'),
      'sourceExactExceptGuidePositions':True,'radiiRootsMaterialStageExact':True,'controlGuideCount':len(P),'displayFibres':len(out),'pointsPerFibre':128,
      'representativeBody':audit,'fullChildrenBody':'NOT_TESTED','self':'NOT_TESTED','dynamicsRuntime':'NOT_IMPLEMENTED',
      'decision':'AWAIT_COMPLETE_HEAD_REVIEW' if audit['status']=='PASS_TESTED_STATIC_CAPSULES' else 'FAIL_REPRESENTATIVE_BODY_CONTACT',
      'rootedDomain':'Actual source-body scalp rays only in proximal root routes; independent2parameter guide ends, no common per-lock exits',
      'freeRows':{'A':A.tolist(),'UP_IN':UP_IN.tolist(),'UP_OUT':UP_OUT.tolist(),'MID_IN':MID_IN.tolist(),'MID_OUT':MID_OUT.tolist(),'TIP_IN':TIP_IN.tolist(),'TIP_OUT':TIP_OUT.tolist(),'LEFT_DX':LEFT_DX.tolist(),'LEFT_DY':LEFT_DY.tolist(),'LEFT_DZ':LEFT_DZ.tolist()},
      'seconds':time.time()-start})
    print('R39_A_DONE',audit['status'],time.time()-start,flush=True)
if __name__=='__main__':main()
