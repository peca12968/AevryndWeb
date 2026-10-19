"""Independent authored 3D master locks on verified actual scalp follicles.

The coordinates below are newly authored for this head, not sampled from the
artist reference or from r33's free-length field. Each master has its own
scalp exit, free control points, width, depth and terminal placement.
"""
import bpy,importlib.util,json,time,math,sys,hashlib,shutil
from pathlib import Path
import numpy as np
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
spec=importlib.util.spec_from_file_location('g33',Path(__file__).with_name('build-female-next-r0033-parted-bob.py'));g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
E=g.b.R/'Evidence/character-female-next/r0034-master-locks';E.mkdir(parents=True,exist_ok=True)
S=g.b.S;SRC=g.SRC;OUT=S/'aevrynd-female-next-r0034-a-independent-master-locks.blend'
ROOTS=S/'aevrynd-female-next-r0033-c-bob-fibres.npz';N=160

# name, side, root azimuth/u, independent scalp exit azimuth/elevation,
# free 3D artist control points, half-width, half-depth (all world metres).
MASTERS=[
('L_front_inner',-1,.15,.15,.80,.38,[(-.090,-.128,1.515),(-.108,-.128,1.470),(-.102,-.115,1.428),(-.115,-.098,1.405),(-.096,-.105,1.387)],.008,.0035),
('L_front_outer',-1,.08,.75,.65,.64,[(-.084,-.133,1.540),(-.108,-.135,1.490),(-.116,-.117,1.445),(-.106,-.108,1.395),(-.089,-.120,1.358)],.009,.004),
('L_crown_sweep',-1,.50,.86,1.05,.52,[(-.102,-.105,1.535),(-.114,-.090,1.482),(-.100,-.085,1.430),(-.113,-.070,1.380),(-.099,-.065,1.350)],.010,.004),
('L_temple_inner',-1,.90,.16,1.25,.10,[(-.101,-.060,1.490),(-.114,-.055,1.450),(-.104,-.065,1.415),(-.116,-.050,1.380)],.008,.0035),
('L_temple_outer',-1,1.10,.65,1.30,.50,[(-.110,-.050,1.530),(-.123,-.040,1.480),(-.110,-.035,1.430),(-.120,-.010,1.380),(-.100,-.015,1.335)],.011,.0045),
('L_side_inner',-1,1.55,.18,1.58,.04,[(-.108,.001,1.490),(-.118,.010,1.450),(-.108,.005,1.405),(-.119,.018,1.365)],.009,.004),
('L_side_outer',-1,1.55,.85,1.68,.55,[(-.115,.017,1.530),(-.125,.022,1.470),(-.113,.030,1.423),(-.126,.025,1.370),(-.105,.030,1.340)],.011,.005),
('L_backside_inner',-1,2.05,.15,2.08,-.03,[(-.101,.054,1.480),(-.110,.070,1.440),(-.097,.075,1.400),(-.104,.080,1.350)],.009,.004),
('L_backside_outer',-1,2.00,.70,2.03,.50,[(-.105,.065,1.530),(-.116,.080,1.480),(-.106,.090,1.430),(-.112,.085,1.380),(-.090,.090,1.325)],.011,.005),
('L_rear_inner',-1,2.65,.16,2.65,-.14,[(-.066,.082,1.470),(-.075,.095,1.430),(-.065,.103,1.390),(-.070,.100,1.340)],.010,.0045),
('L_rear_outer',-1,2.65,.80,2.56,.50,[(-.069,.090,1.530),(-.082,.110,1.475),(-.075,.118,1.425),(-.083,.111,1.380),(-.064,.118,1.330)],.011,.005),
('L_back_part',-1,3.06,.45,2.95,.05,[(-.026,.090,1.500),(-.042,.105,1.455),(-.032,.115,1.415),(-.043,.109,1.370),(-.030,.120,1.335)],.012,.005),
('R_front_outer',1,.15,.85,.72,.70,[(.085,-.137,1.550),(.102,-.150,1.505),(.095,-.130,1.460),(.110,-.120,1.415),(.096,-.110,1.370)],.009,.004),
('R_front_inner',1,.18,.20,.88,.40,[(.085,-.125,1.515),(.098,-.135,1.480),(.090,-.120,1.440),(.100,-.100,1.412),(.090,-.105,1.390)],.008,.0035),
('R_temple_outer',1,.80,.70,1.20,.57,[(.100,-.085,1.535),(.118,-.085,1.490),(.110,-.075,1.445),(.122,-.060,1.400),(.107,-.060,1.350)],.010,.0045),
('R_temple_inner',1,.95,.18,1.30,.10,[(.100,-.060,1.490),(.110,-.070,1.450),(.100,-.060,1.415),(.110,-.040,1.380)],.008,.0035),
('R_side_outer',1,1.40,.90,1.50,.55,[(.115,-.023,1.535),(.125,-.020,1.485),(.117,-.010,1.435),(.127,-.015,1.385),(.112,.001,1.340)],.011,.005),
('R_side_inner',1,1.50,.20,1.65,.04,[(.107,.001,1.490),(.120,.015,1.455),(.110,.020,1.415),(.120,.025,1.375)],.009,.004),
('R_backside_outer',1,1.95,.72,2.02,.50,[(.110,.060,1.535),(.120,.075,1.490),(.110,.090,1.440),(.118,.080,1.390),(.105,.100,1.345)],.011,.005),
('R_backside_inner',1,2.05,.16,2.12,-.05,[(.099,.050,1.480),(.114,.070,1.440),(.100,.080,1.400),(.110,.085,1.365)],.009,.004),
('R_rear_outer',1,2.60,.85,2.55,.45,[(.075,.085,1.535),(.090,.105,1.480),(.080,.115,1.430),(.090,.109,1.380),(.070,.120,1.325)],.011,.005),
('R_rear_inner',1,2.65,.16,2.70,-.12,[(.065,.080,1.470),(.080,.096,1.435),(.070,.108,1.395),(.080,.100,1.355)],.010,.0045),
('R_back_part',1,3.04,.45,3.00,.04,[(.022,.090,1.500),(.040,.110,1.455),(.030,.120,1.410),(.040,.110,1.370),(.025,.120,1.330)],.012,.005),
('R_crown_sweep',1,.50,.97,.99,.70,[(.095,-.105,1.550),(.115,-.110,1.505),(.108,-.100,1.465),(.120,-.090,1.420),(.107,-.080,1.375)],.010,.0045),
]

def save(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def read(n):return json.loads((E/n).read_text(encoding='utf8'))
def normalized(x):return x/max(np.linalg.norm(x),1e-20)
def resample(P,n=N):
    arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(P,axis=0),axis=1))];at=np.linspace(0,arc[-1],n)
    return np.column_stack([np.interp(at,arc,P[:,axis]) for axis in range(3)])

def root_data():
    proof=json.loads((E.parent/'r0033-parted-bob/c-saved-fibre-verification.json').read_text());assert proof['status']=='PASS_REOPENED_STATIC_SCOPE' and g.b.sha(ROOTS)==proof['cacheSha256']
    data=np.load(ROOTS);mx=np.array(proof['worldMatrix']);roots=data['positions'][:,0].astype('f8')@mx[:3,:3].T+mx[:3,3]
    params=data['scalpParams'].astype('f8');parts=data['parts'];costs=[]
    for m in MASTERS:
        name,side,a,u,*_=m;costs.append(np.where(parts==side,((params[:,0]-a)*(.6+.4*(1-params[:,1])))**2+((params[:,1]-u)*2)**2,np.inf))
    costs=np.array(costs).T;owners=np.argmin(costs,axis=1);centers=[int(np.argmin(costs[:,i])) for i in range(len(MASTERS))]
    return data,roots,params,parts,owners,centers

def free_controls(P,tangent,m):
    K=np.vstack((P[-1],np.array(m[6],dtype='f8')));T=np.zeros_like(K);T[0]=tangent*np.linalg.norm(K[1]-K[0])*.8
    T[1:-1]=(K[2:]-K[:-2])*.5;T[-1]=(K[-1]-K[-2])*.7
    return K,T

def free_samples(K,T,count=161):
    # The same free Bezier points/handles are saved as independent editable
    # controls. No global angle, common ring or free-length surface projection.
    P=[]
    for i in range(len(K)-1):
        for t in np.linspace(0,1,33)[:-1]:
            P.append((2*t**3-3*t*t+1)*K[i]+(t**3-2*t*t+t)*T[i]+(-2*t**3+3*t*t)*K[i+1]+(t**3-t*t)*T[i+1])
    P.append(K[-1]);return resample(np.array(P),count)

def frames(P,normal):
    tangent=np.gradient(P,axis=0);tangent/=np.maximum(np.linalg.norm(tangent,axis=1)[:,None],1e-20);ns=[];bs=[];n=normal.copy()
    for t in tangent:
        n=normalized(n-(n@t)*t);ns.append(n.copy());bs.append(normalized(np.cross(t,n)))
    return np.array(ns),np.array(bs)

def groom_path(tree,tri,root,param,m,scatter=(0.,0.),trim=1.):
    name,side,a,u,exit_a,exit_theta,free,width,depth=m;ra,ru=param;theta0=g.theta_min(ra)+(1.54-g.theta_min(ra))*ru
    target_theta=min(theta0,exit_theta);exit_phi=side*exit_a
    # Only the actual-skin attachment section follows a surface chart. Each
    # free length below is its own artist-edited 3D spline with finite volume.
    proximal=[];last_normal=None
    for t in np.linspace(0,1,81):
        f=t*t*(2-t);p,n,tid,bary=g.scalp(tree,tri,side*ra+(exit_phi-side*ra)*f,theta0+(target_theta-theta0)*f)
        # Thickness is spatial, not a rendered solid patch. Follicle is fixed.
        loft=.013+.003*ru
        proximal.append(p+n*(.00018+loft*math.sin(.5*math.pi*t)**1.2));last_normal=n
    proximal=np.array(proximal);proximal[0]=root
    tangent=normalized(proximal[-1]-proximal[-2]);K,T=free_controls(proximal,tangent,m);F=free_samples(K,T)
    ns,bs=frames(F,last_normal);s=np.linspace(0,1,len(F));profile=(.65+.35*np.sin(math.pi*s))*(1-s)**.45
    offset=ns*(scatter[1]*depth*profile)[:,None]+bs*(scatter[0]*width*profile)[:,None]
    # Offset is smoothly introduced across the last rooted quarter so no
    # artificial step occurs where the free volume begins.
    start_offset=offset[0];ramp=np.clip((np.linspace(0,1,len(proximal))-.65)/.35,0,1);ramp=ramp*ramp*(3-2*ramp);proximal+=ramp[:,None]*start_offset
    F+=offset
    if trim<1:
        target=max(4,int((len(F)-1)*trim));F=F[:target+1]
    return resample(np.vstack((proximal,F[1:]))),K,T,last_normal

def legacy_paths(name,paths,body,radius,mat,render=True):
    d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.bevel_depth=radius;d.bevel_resolution=0;d.use_fill_caps=True;d.materials.append(mat)
    for P in paths:
        spline=d.splines.new('POLY');spline.points.add(len(P)-1);spline.points.foreach_set('co',np.column_stack((P,np.ones(len(P)))).astype('f4').ravel())
    o=bpy.data.objects.new(name,d);bpy.context.scene.collection.objects.link(o);o.parent=body;o.matrix_world=Matrix.Identity(4);o.hide_render=not render;return o

def editable_controls(name,K,T,body):
    d=bpy.data.curves.new('CTRL34_'+name,'CURVE');d.dimensions='3D';sp=d.splines.new('BEZIER');sp.bezier_points.add(len(K)-1)
    for p,k,t in zip(sp.bezier_points,K,T):p.co=k;p.handle_left_type='FREE';p.handle_right_type='FREE';p.handle_left=k-t/3;p.handle_right=k+t/3
    o=bpy.data.objects.new(d.name,d);bpy.context.scene.collection.objects.link(o);o.parent=body;o.matrix_world=Matrix.Identity(4);o.hide_render=True;o.hide_set(True);o['aevrynd_layer']='EDITABLE_INDEPENDENT_FREE_LOCK_CONTROLS';o['regeneration']='Own Hermite/Bezier evaluation from these handles; explicit cache rebuild required, not live simulation.';return o

def main():
    start=time.time();assert g.b.sha(SRC)=='7b8b110dd50db95a722797113d8abe2a1682d347e8e1874412999c70c21c1a20';g.cap.math_controls()
    save('round-contract.json',{'previousGoalTurnClassification':'progress: r33 complete native hairstyle rejected after exact source preservation and full static body/optic evidence; common analytic free-fall family stopped','source':str(SRC),'sourceSha256':g.b.sha(SRC),'primaryDefect':'Coherent sheet-like hair mass and row-like tips in a shared angular free-fall field','hypothesis':'Independent authored 3D free-lock controls with different curved paths, layered lengths and finite cross-sections create a volumetric natural silhouette instead of common ribbons','candidateCount':1,'masterLocks':24,'reference':'Already-local Daniel Bystedt raw guide structure studied privately; source geometry/node code not adopted','reuse':'Only verified actual scalp follicles/barycentrics and native-format workflow from r33; no old free paths or contact inheritance','smallPilot':'24 center paths plus up to4 actual-domain-root boundary fibre examples per lock, all complete160point finite capsules','reject':['Any unresolved representative guide/body capsule','Detached follicles, severe silhouette inflation, obvious repeated tubes or a new sheet mass','No full-head visible benefit versus r33 rejected C after actual child preview'],'resourceLimit':{'threads':4,'checkpointMinutes':45,'diagnosticInitialMinutes':10,'fibresMaximum':12000,'headRender':800},'integration':'Same r32 body/skin/8 optical meshes and saved stage; no male, website/runtime or appearance-score promotion implied'})
    bpy.ops.wm.open_mainfile(filepath=str(SRC));scene=bpy.context.scene;g.b.E=E;cfg=g.b.config(scene);g.b.setup(scene,cfg);body=bpy.data.objects[g.b.BODY]
    originals={o.name:g.signature(o) for o in scene.objects if o.type=='MESH' and not o.hide_render};save('baseline-state.json',{'visibleMeshes':originals,'config':cfg,'baselineHash':g.b.sha(SRC)})
    prior=E.parent/'r0033-parted-bob'
    for p in prior.glob('before-*.png'):shutil.copyfile(p,E/p.name)
    shutil.copyfile(prior/'before-renders.json',E/'before-renders.json');save('reused-baseline.json',{'sourceSha256':g.b.sha(SRC),'evidence':str(prior/'before-renders.json'),'reason':'Exact same retained r32 source and stage; six existing actual renders are valid unchanged baseline, not a model rerender claim'})
    V,T=g.b.evaluated(body,True);tri=V[T];tree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True)
    data,roots,params,parts,owners,centers=root_data();paths=[];records=[];controls=[]
    for mi,m in enumerate(MASTERS):
        ci=centers[mi];P,K,tangent,n=groom_path(tree,tri,roots[ci],params[ci],m);paths.append(P);records.append({'master':mi,'rootId':ci,'scatter':[0,0],'role':'center'});controls.append({'name':m[0],'sourceRootId':ci,'knots':K.tolist(),'tangents':tangent.tolist(),'halfWidthM':m[7],'halfDepthM':m[8],'ownFreeControls':m[6]});editable_controls(m[0],K,tangent,body)
        ids=np.flatnonzero(owners==mi);assert len(ids)>0,m[0]
        # Representative domain-boundary roots AND four nonzero bundle axes.
        boundary=[ids[np.argmin(params[ids,0])],ids[np.argmax(params[ids,0])],ids[np.argmin(params[ids,1])],ids[np.argmax(params[ids,1])]]
        for ri,scatter in zip(boundary,[(1,0),(-1,0),(0,1),(0,-1)]):
            P,*_=groom_path(tree,tri,roots[ri],params[ri],m,scatter);paths.append(P);records.append({'master':mi,'rootId':int(ri),'scatter':scatter,'role':'representative_boundary_only'})
    paths=np.array(paths);mat=g.material();o=legacy_paths('AFN34_A_REPRESENTATIVE_GUIDES',paths,body,.00008,mat);bpy.context.view_layer.update()
    actual=np.array([[list(o.matrix_world@Vector(p.co[:3])) for p in sp.points] for sp in o.data.splines]);radii=np.full(actual.shape[:2],.00008)
    audit=g.check(actual,radii,tree,tri);save('a-representative-contact.json',audit)
    assert {n:g.signature(bpy.data.objects[n]) for n in originals}==originals;assert g.b.config(scene)==cfg
    save('a-master-controls.json',{'masters':[{'name':m[0],'side':m[1],'rootParam':[m[2],m[3]],'exitParam':[m[4],m[5]],'freeWorldPoints':m[6],'halfWidthM':m[7],'halfDepthM':m[8]} for m in MASTERS],'centres':controls,'guideExamples':records,'rootCache':str(ROOTS),'rootCacheSha256':g.b.sha(ROOTS),'rootOwnerCounts':np.bincount(owners,minlength=len(MASTERS)).tolist(),'scope':'Independent own3D controls; representative guide/contact pilot only, not child or continuous tube proof'})
    np.savez_compressed(S/'aevrynd-female-next-r0034-a-master-guides.npz',positions=actual.astype('f4'),radii=radii.astype('f4'),owner=owners,centerRootIds=np.array(centers),sampleRootIds=np.array([r['rootId'] for r in records]),sampleMasterIds=np.array([r['master'] for r in records]))
    g.b.camera('face');scene['AFN34_status']='INDEPENDENT_MASTER_GUIDE_PILOT_NOT_QUALIFIED_GROOM';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    save('a-build-verification.json',{'source':str(SRC),'sourceSha256':g.b.sha(SRC),'output':str(OUT),'outputSha256':g.b.sha(OUT),'originalVisibleMeshesExact':originals,'stageExact':True,'masterLocks':24,'representativeGuides':len(actual),'guidePoints':N,'contact':audit,'expansionAllowed':audit['status']=='PASS_TESTED_STATIC_CAPSULES','seconds':time.time()-start,'limits':['Only120representative paths, not all12000children','Not a conservative swept-volume master-tube proof','No hair/hair, dynamics, rig, runtime, LOD or appearance qualification']})
    g.q.render('a-guides');print('R34_MASTER_PILOT_DONE',audit['status'],flush=True)

if __name__=='__main__':main()
