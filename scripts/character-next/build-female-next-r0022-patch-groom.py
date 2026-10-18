"""Own two-domain scalp, authored crown/temple/back guide controls, actual-body guard."""
import bpy,bmesh,json,math,time,sys,importlib.util
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
spec=importlib.util.spec_from_file_location('prev',Path(__file__).with_name('build-female-next-r0021-root-transition.py'));prev=importlib.util.module_from_spec(spec);spec.loader.exec_module(prev)
R,S,base,solid,route=prev.R,prev.S,prev.base,prev.solid,prev.route
PREFIX='c' if '--ear-hulls' in sys.argv else 'b' if '--adaptive' in sys.argv else 'a'
E=R/'Evidence/character-female-next/r0022-patch-groom'
if PREFIX=='b':E=E/'b-adaptive-segments'
if PREFIX=='c':E=E/'c-local-ear-hulls'
E.mkdir(parents=True,exist_ok=True)
SRC=prev.SRC;DST=S/f'aevrynd-female-next-r0022-{PREFIX}-patch-groom-study.blend';GSRC=S/f'aevrynd-female-next-r0022-{PREFIX}-guides.blend';GUIDES=S/f'aevrynd-female-next-r0022-{PREFIX}-guides.npz';CACHE=S/f'aevrynd-female-next-r0022-{PREFIX}-hair-data.npz'
C=route.C;N=64;sha=prev.sha;rng=np.random.default_rng(2222)
EAR_TREES=[]
def save(name,obj):(E/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def smooth(x):return prev.smooth(x)
def head_state():
    state=base.snapshot();state['meshes']={n:v for n,v in state['meshes'].items() if not n.startswith('AFN22_')};return state
def theta_max(phi):
    # Own shaped hairline; the feather is represented separately as density.
    return math.radians(82-24*max(-math.sin(phi),0)+38*max(math.sin(phi),0))+.009*math.sin(7*phi+.3)
def polar(tree,theta,phi,offset=.0002):
    direction=Vector((math.sin(theta)*math.cos(phi),math.sin(theta)*math.sin(phi),math.cos(theta)));hit,normal,face,d=tree.ray_cast(Vector(C)+direction*.45,-direction,.7);assert hit is not None
    return np.array(hit+normal*offset,np.float64),np.array(normal,np.float64)
def domain_point(tree,side,u,v):
    phi=(-math.pi/2+v*math.pi) if side==1 else (math.pi/2+v*math.pi);theta=theta_max(phi)*u
    p,n=polar(tree,theta,phi);p[0]+=side*.00040
    # Rebind the seam shift onto actual skin, rather than floating its roots.
    d=Vector(p-C).normalized();hit,normal,face,dist=tree.ray_cast(Vector(C)+d*.45,-d,.7);assert hit is not None
    return np.array(hit+normal*.00020,np.float64),np.array(normal,np.float64)
def scalp(tree,rig):
    results=[]
    for side,name in ((1,'RIGHT'),(-1,'LEFT')):
        rings=12;cols=33;P=[];UV=[];F=[]
        p,n=domain_point(tree,side,0.,.5);P.append(p);UV.append((0.,.5))
        for j in range(1,rings+1):
            for k in range(cols):p,n=domain_point(tree,side,j/rings,k/(cols-1));P.append(p);UV.append((j/rings,k/(cols-1)))
        for k in range(cols-1):F.append((0,1+k,2+k))
        for j in range(rings-1):
            for k in range(cols-1):
                i=1+j*cols+k;F.extend(((i,i+cols,i+1),(i+1,i+cols,i+cols+1)))
        P=np.array(P,np.float32);F=np.array(F,np.int32);UV=np.array(UV,np.float32);m=bpy.data.meshes.new('AFN22_SCALP_'+name);m.from_pydata(P.tolist(),[],F.tolist());m.update();o=bpy.data.objects.new(m.name,m);bpy.context.scene.collection.objects.link(o);route.parent_head(o,rig);o.hide_render=True;o['aevrynd_layer']='EDITABLE_SCALP_DOMAIN';o['side']=side
        uv=m.uv_layers.new(name='ScalpUV')
        for polygon in m.polygons:
            for loop in polygon.loop_indices:uv.data[loop].uv=UV[m.loops[loop].vertex_index]
        density=m.attributes.new('density','FLOAT','POINT');parting=m.attributes.new('parting','FLOAT','POINT')
        density.data.foreach_set('value',np.array([float(smooth((1-float(u))/.07)) for u,v in UV],np.float32));parting.data.foreach_set('value',np.exp(-abs(P[:,0])/.004).astype(np.float32))
        area=np.linalg.norm(np.cross(P[F[:,1]]-P[F[:,0]],P[F[:,2]]-P[F[:,0]]),axis=1)/2;results.append((side,P,F,UV,area/area.sum()))
    return results
def ear_hulls(V,rig):
    rows=[]
    for side in (1,-1):
        selected=V[(V[:,0]*side>.070)&(V[:,1]>-.055)&(V[:,1]<.020)&(V[:,2]>1.405)&(V[:,2]<1.500)];assert len(selected)>30
        bm=bmesh.new()
        for p in selected:bm.verts.new(p)
        result=bmesh.ops.convex_hull(bm,input=list(bm.verts),use_existing_faces=False);faces=[f for f in result['geom'] if isinstance(f,bmesh.types.BMFace)];used=list({v for f in faces for v in f.verts});index={v:i for i,v in enumerate(used)};points=[tuple(v.co) for v in used];polygons=[[index[v] for v in f.verts] for f in faces];bm.free();name='AFN22_EAR_PROXY_'+('R' if side==1 else 'L');mesh=bpy.data.meshes.new(name);mesh.from_pydata(points,[],polygons);mesh.update();o=bpy.data.objects.new(name,mesh);bpy.context.scene.collection.objects.link(o);route.parent_head(o,rig);o.hide_render=True;o.hide_viewport=True;o['aevrynd_layer']='LOCAL_AUTHORING_EAR_HULL_NOT_FULL_BODY_COLLIDER';EAR_TREES.append(BVHTree.FromPolygons(points,polygons));rows.append({'object':name,'selectedBodyVertices':len(selected),'hullVertices':len(points),'hullFaces':len(polygons),'selection':{'signedXMinM':.070,'yRangeM':[-.055,.020],'zRangeM':[1.405,1.500]},'scope':'Local convex bridge across ear concavities only. Selected vertices/fully selected triangles covered; actual full-body capsules remain the acceptance authority.'})
    save('ear-proxy-description.json',{'proxies':rows,'policy':'No whole-head convex hull reused, no moved roots. Free-length guard blends in only after 10-20mm arc length.'})
def section(tree,z,phi,radiusFloor=0.,clearance=.007):
    direction=Vector((math.cos(phi),math.sin(phi),0.));centre=Vector((C[0],C[1],z));hit,n,face,d=tree.ray_cast(centre+direction*.45,-direction,.7)
    radius=float(np.linalg.norm(np.array(hit)[:2]-C[:2]))+clearance if hit is not None else radiusFloor
    radius=max(radius,radiusFloor);return np.array((C[0]+radius*direction.x,C[1]+radius*direction.y,z),np.float64),radius
def guard(P,tree,root,rootClearance=.0002):
    Q=P.copy();arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(P,axis=0),axis=1))];margin=rootClearance+.0013*smooth(arc/.014)
    for j,p in enumerate(P[1:],1):
        delta=p-C
        if p[2]>=C[2]:
            direction=Vector(delta).normalized();centre=Vector(C);length=float(np.linalg.norm(delta))
        else:
            direction=Vector((delta[0],delta[1],0.)).normalized();centre=Vector((C[0],C[1],p[2]));length=float(np.linalg.norm(delta[:2]))
        hit,n,face,d=tree.ray_cast(centre+direction*.45,-direction,.7)
        if EAR_TREES and arc[j]>.010:
            for proxy in EAR_TREES:
                h=proxy.ray_cast(centre+direction*.45,-direction,.7)[0]
                if h is not None:
                    outer=centre+direction*((h-centre).length)
                    if hit is None:hit=outer
                    else:
                        blend=float(smooth((arc[j]-.010)/.010));outerRadius=float((hit-centre).length)+blend*max(0.,float((outer-centre).length-(hit-centre).length));hit=centre+direction*outerRadius
        if hit is not None:
            required=float((hit-centre).length)+margin[j]
            if length<required:Q[j]=np.array(centre+direction*required)
    Q[0]=root;return Q
def catmull(points,steps=12):
    # Uniform Catmull-Rom with extrapolated endpoints, then arc sampling.
    p=np.array(points);extended=np.vstack((2*p[0]-p[1],p,2*p[-1]-p[-2]));out=[]
    for i in range(1,len(extended)-2):
        p0,p1,p2,p3=extended[i-1:i+3]
        for t in np.linspace(0,1,steps,endpoint=False):out.append(.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t))
    return np.vstack((out,p[-1]))
def resample(P,n):return prev.flow.resample(P,n)
TRI=None
REPAIR_STATS=[]
def adaptive_segments(P,tree,root,budget=64):
    # Bounded geometry refinement at actual failed segments. Extra CVs come
    # from the fixed allocation, not a tolerance/iteration increase. Straight
    # subdivision of already qualified segments preserves their exact route.
    q=P.copy();inserted=0
    while True:
        distances=[tree.find_nearest(Vector(p))[3] for p in q];bad=[]
        for j in range(len(q)-1):
            gap,method=route.capsule.segment_test(q[j],q[j+1],distances[j],distances[j+1],.00006,tree,TRI)
            if gap<=0:bad.append(j)
        if not bad:break
        if len(q)+len(bad)>budget:
            save('bounded-refinement-failure.json',{'source':str(SRC),'sourceSha256':sha(SRC),'root':root.tolist(),'polyline':q.tolist(),'badSegmentIndices':bad,'allocatedCVs':len(q),'maximumCVs':budget,'conservativeRadiusM':.00006,'numericalAllowanceM':.000001,'insertions':inserted,'scope':'Exact terminal failure snapshot of one bounded guide construction. Not a complete guide-set or self-contact report.'})
            raise RuntimeError(f'Adaptive geometry budget exceeded: {len(q)} CVs, {len(bad)} unresolved segments')
        for j in reversed(bad):
            # Use the actual segment/surface event. A geometric midpoint can
            # remain outside a thin ear while a different part crosses it;
            # subdividing that midpoint repeatedly cannot repair the event.
            delta=q[j+1]-q[j];length=float(np.linalg.norm(delta));hit,n,face,dist=tree.ray_cast(Vector(q[j]),Vector(delta/length),length)
            if hit is None:
                candidates=[q[j]+t*delta for t in np.linspace(0,1,9)];point=min(candidates,key=lambda p:tree.find_nearest(Vector(p))[3]);hit,n,face,dist=tree.find_nearest(Vector(point))
            fixed=np.array(hit+n*.0015,np.float64)
            if solid.classify(tree,TRI,Vector(fixed))!='outside':fixed=np.array(hit-n*.0015,np.float64)
            q=np.insert(q,j+1,fixed,axis=0);inserted+=1
    while len(q)<budget:
        j=int(np.argmax(np.linalg.norm(np.diff(q,axis=0),axis=1)));q=np.insert(q,j+1,(q[j]+q[j+1])/2,axis=0)
    assert np.array_equal(q[0],root);REPAIR_STATS.append(inserted);return q
def guide(root,side,uv,tree):
    u,v=uv;d=root-C;theta=math.acos(float(np.clip(d[2]/np.linalg.norm(d),-1,1)));phi=math.atan2(d[1],d[0]);front=float(np.clip((-root[1]-.005)/.10,0,1));back=float(np.clip((root[1]+.015)/.07,0,1))
    # Explicit patch control family: frontal sweep goes towards the temples,
    # occipital roots retain posterior flow. Crown controls are entirely new.
    goal=(.10-.55*front+1.25*back) if side==1 else math.pi-(.10-.55*front+1.25*back)
    difference=math.atan2(math.sin(goal-phi),math.cos(goal-phi));phase=11*phi+17*root[1];loft=.0027+.0012*math.sin(phase*.6);controls=[root.copy()]
    if root[2]>1.500:
        for dt,blend,lift in ((.20,.18,.0015),(.50,.48,loft),(.83,.83,loft+.0015)):
            angle=min(theta+dt,1.45)
            if angle<=theta+.03:continue
            p,n=polar(tree,angle,phi+difference*blend,0.);controls.append(p+n*lift)
    earZ=min(1.478,root[2]-.010);ear,earRadius=section(tree,earZ,goal,clearance=.007+.002*math.sin(phase));controls.append(ear)
    bottom=1.355+.006*math.sin(phase*.7)+.003*math.cos(3*phi+u*2)
    for z,t,angle in ((earZ-.022,.30,goal+.045*math.sin(phase)),((earZ+bottom)/2,.65,goal-.055*math.sin(phase)),(bottom,1.,goal+.025*math.cos(phase))):
        floor=earRadius*(1-.035*t)-.0025*t*t;p,r=section(tree,z,angle,floor,.005);controls.append(p)
    # Resolve the real bound-skin departure explicitly before arc sampling.
    hit,n,face,dist=tree.find_nearest(Vector(root));normal=np.array(n,np.float64);tangent=controls[1]-root;tangent-=normal*(tangent@normal);tangent/=max(np.linalg.norm(tangent),1.e-12);first=root+tangent*.00055+normal*.00012
    dense=catmull([first]+controls[1:]);tail=resample(dense,46 if PREFIX=='b' else 62);P=np.vstack((root,first,tail));P=guard(P,tree,root)
    if PREFIX=='b':P=adaptive_segments(P,tree,root)
    family='CROWN' if root[2]>1.535 else 'FRONTAL_SWEEP' if front>.5 else 'OCCIPITAL' if back>.4 else 'TEMPORAL'
    return P.astype(np.float32),{'side':side,'uv':[float(u),float(v)],'family':family,'controls':np.array(controls).tolist(),'departurePoint':first.tolist()}
def bind(root,tree,V,T,metadata):return prev.binding(root,tree,V,T,metadata)
def guides():
    global TRI
    started=time.time();manifest=json.loads((S.parent/'female-next.asset.json').read_text());assert sha(SRC)==manifest['workingReviewSha256'];bpy.ops.wm.open_mainfile(filepath=str(SRC));rig=bpy.data.objects['AFN_R0005_Rig'];solid.stage.set_pose(rig,'neutral');before=head_state();V,T,tree=solid.data(bpy.data.objects['AFN_R0008_Body']);V=np.array(V,np.float64);T=np.array(T,np.int32);patches=scalp(tree,rig);G=[];descs=[];bindings=[]
    save('iteration-contract.json',{'source':str(SRC),'sourceSha256':sha(SRC),'previousGoalTurnClassification':'progress: two real hairline candidates rejected under matched images, official native two-island scalp and independent-guide structure inspected; next architecture changes rather than parameter sweeps.','stage':'B_COMPLETE_HEAD_IN_PROGRESS','hypothesis':'Own separate scalp UV domains plus authored frontal/crown/temporal/occipital control paths and actual-body radial-section routing produce a new complete bob, replacing the common global tangent and convex-envelope crown.','expectedVisibleChange':'Whole crown flow, temple sweep and hanging locks read as separate curved regions rather than a flat cap and uniform sheet.','held':'Source head/eyes/skin/brows/lashes/rig/materials/light/exposure, total existing render fibre/CV allocation/radii.','referenceUse':'Only general authoring structure learned from the local Daniel Bystedt CC-BY-SA demo; no reference geometry, textures, nodes or code copied.','rejectIf':['Any actual guide/body capsule fails before child generation.','New render geometry fails complete child/body/component checks.','Whole-head matched views retain cap/sheet appearance or introduce lobes, bald gaps or noisy strands.','Unrelated source state changes.'],'budget':{'threads':4,'candidatesMaximum':3,'guideCount':424,'renderFibres':21086,'renderPoints':1347824,'pilotResolution':800,'newDynamics':False},'guardScope':'Exact actual-body rays at each CV are only an authoring guard. Final complete capsule checks, not CV/ray sampling, determine separation.'})
    TRI=V[T]
    if PREFIX=='c':
        ear_hulls(V,rig);contract=json.loads((E/'iteration-contract.json').read_text());contract.update({'reasonForCandidateC':'A actual-CV guard leaves ear crossings. B bounded segment refinement exhausted 64 CVs with unresolved spans; stop refinement-only correction.','geometricCorrection':'Bridge actual ear concavities with two compact local convex authoring hulls, preserving the new patch guide architecture and actual roots. Final full-body capsules retain the original radius/tolerance.','proxyLimits':'Ear hulls cover only the recorded local vertex selection. They are not a full-body or moving-contact certificate.'});save('iteration-contract.json',contract)
    if PREFIX=='b':
        contract=json.loads((E/'iteration-contract.json').read_text());contract.update({'reasonForCandidateB':'A point-guarded guide field has 56 complete-segment failures around the ear although CVs are outside. Child expansion was stopped.','geometricCorrection':'Start with 48 CVs, insert actual-contact bridge points within the fixed 64-CV allocation; final spare CVs only subdivide already safe straight segments. Same 1um allowance and 60um conservative radius. Stop if allocation is insufficient.','rootPolicy':'Actual-skin roots remain exact; no collision exclusions or tolerance relaxation.'});save('iteration-contract.json',contract)
        contract.update({'implementationCorrection':'The first implementation inserted midpoints which need not coincide with a thin-ear collision. Use the actual centreline/surface hit, or sampled nearest contact for a finite-radius near miss, and construct the bridge along its checked outside normal. Same authored hairstyle, root positions, allocation, radius and tolerance; retain the failed midpoint log.'});save('iteration-contract.json',contract)
    for side in (1,-1):
        uvSeeds=[(j/12,(k+.5)/16) for j in range(1,13) for k in range(16)]+[(float(u),v) for u in np.linspace(.08,.95,20) for v in (.0,)]
        for uv in uvSeeds:
            root,n=domain_point(tree,side,*uv);p,desc=guide(root,side,uv,tree);i=len(G);G.append(p);descs.append(desc);bindings.append(bind(p[0],tree,V,T,{'guide':i,'side':side,'uv':list(uv)}))
    G=np.array(G,np.float32);assert len(G)==424;audit=route.check_paths(list(G.astype(np.float64)),[np.full(64,.00006) for _ in G],tree,V[T]);np.savez_compressed(GUIDES,guides=G,guideUV=np.array([d['uv'] for d in descs],np.float32),guideSides=np.array([d['side'] for d in descs],np.int8),**{f'{name}{i}':value for i,patch in enumerate(patches) for name,value in zip(('side','vertices','faces','uv','probability'),patch)});save('guide-controls.json',{'guides':descs,'guard':'Actual radial/section skin support; no old global convex support reused.','sourceSha256':sha(SRC),'adaptiveInsertions':REPAIR_STATS});(S/f'aevrynd-female-next-r0022-{PREFIX}-guide-bindings.json').write_text(json.dumps(bindings,separators=(',',':'))+'\n')
    o=route.legacy_guides(list(G),rig);o.name='AFN22_GUIDES';o.data.name=o.name;o['aevrynd_layer']='OWN_EDITABLE_COMPLETE_PATCH_GUIDES';assert head_state()==before;bpy.context.preferences.filepaths.save_version=0;bpy.context.scene['aevrynd_revision']='female-next-r0022-a-guides';bpy.context.scene['aevrynd_release_state']='GUIDE_GATE_ONLY_NOT_FULL_HAIR';bpy.ops.wm.save_as_mainfile(filepath=str(GSRC));save('guide-verification.json',{'status':audit['status'],'childrenAllowed':audit['status']=='PASS_TESTED_BODY_CAPSULES','bodyCapsules':audit,'guides':424,'guideData':str(GUIDES),'guideDataSha256':sha(GUIDES),'guideBlender':str(GSRC),'guideBlenderSha256':sha(GSRC),'sourceSha256':sha(SRC),'headStateExact':True,'scalpObjects':['AFN22_SCALP_RIGHT','AFN22_SCALP_LEFT'],'wallSeconds':time.time()-started});print('R0022_GUIDE_GATE',audit['status'],flush=True)
def sample_root(tree,patches,layer):
    for attempt in range(2000):
        side,P,F,UV,prob=patches[int(rng.integers(2))];face=F[int(rng.choice(len(F),p=prob))];s=math.sqrt(float(rng.random()));t=float(rng.random());weights=np.array((1-s,s*(1-t),s*t));uv=weights@UV[face];edge=float(smooth((1-uv[0])/.065))
        if rng.random()>edge:continue
        if layer==2 and not(uv[0]>.88 and uv[1]<.48):continue
        seed=weights@P[face];hit,n,fi,d=tree.find_nearest(Vector(seed));root=np.array(hit+n*.00020,np.float64);return root,side,uv
    raise RuntimeError('Bounded scalp sampler exhausted')
def children():
    started=time.time();proof=json.loads((E/'guide-verification.json').read_text());assert proof['childrenAllowed'] and sha(GUIDES)==proof['guideDataSha256'] and sha(SRC)==proof['sourceSha256'];bpy.ops.wm.open_mainfile(filepath=str(GSRC));rig=bpy.data.objects['AFN_R0005_Rig'];solid.stage.set_pose(rig,'neutral');before=head_state();V,T,tree=solid.data(bpy.data.objects['AFN_R0008_Body']);V=np.array(V,np.float64);T=np.array(T,np.int32);d=np.load(GUIDES);G=d['guides'].astype(np.float64);guv=d['guideUV'];gsides=d['guideSides'];patches=[(int(d[f'side{i}']),d[f'vertices{i}'],d[f'faces{i}'],d[f'uv{i}'],d[f'probability{i}']) for i in (0,1)];bindings=[];allP=[];allR=[];offsets=[0];layers=[];rows=[];signatures={}
    for li,name in enumerate(base.NAMES):
        o=bpy.data.objects['AFN14_'+name];P,rr,off=base.arrays(o);signature=base.v14.strand_signature(o);signatures[o.name]=signature;paths=[]
        for ci,(first,last) in enumerate(zip(off[:-1],off[1:])):
            root,side,uv=sample_root(tree,patches,li);pool=np.flatnonzero(gsides==side);distance=np.linalg.norm((guv[pool]-uv)*np.array((.10,.20)),axis=1);ids=pool[np.argsort(distance)[:3]];dist=np.linalg.norm((guv[ids]-uv)*np.array((.10,.20)),axis=1);weights=1/np.maximum(dist,.0008)**2;weights/=weights.sum();u=np.linspace(0,1,64);clump=(.35 if li==0 else .70)*smooth(u);nearest=np.eye(3)[np.argmax(weights)];w=(1-clump[:,None])*weights+clump[:,None]*nearest;raw=np.einsum('ji,ijk->jk',w,G[ids]);raw+=(root-weights@G[ids,0])[None,:]*(1-u[:,None])**2
            # Small individual strand detail follows the new guide layout, not
            # an independent random walk. Roots and first departure stay fixed.
            radial=raw-C;radial[:,2]=0;radial/=np.maximum(np.linalg.norm(radial,axis=1,keepdims=True),1.e-12);tangent=np.column_stack((-radial[:,1],radial[:,0],np.zeros(64)));variation=(.00022 if li<2 else .00060)*np.sin(math.pi*u)**1.4*np.sin(4*math.pi*u+ci*2.39996);raw+=tangent*variation[:,None];raw[:,2]+=float(rng.uniform(-.002,.002))*u**5
            if li==2:
                arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(raw,axis=0),axis=1))];length=float(rng.uniform(.008,.030));k=max(3,int(np.searchsorted(arc,min(length,arc[-1]),side='right')));raw=resample(raw[:k],last-first)
            elif last-first!=64:raw=resample(raw,last-first)
            raw=guard(raw,tree,root);raw=raw.astype(np.float32);paths.append(raw);bindings.append(bind(raw[0],tree,V,T,{'layer':li,'curve':ci,'side':int(side),'uv':uv.tolist(),'guides':ids.tolist(),'weights':weights.tolist()}));allP.append(raw);allR.extend(rr[first:last]);offsets.append(offsets[-1]+len(raw));layers.append(li)
        o.data.position_data.foreach_set('vector',np.concatenate(paths).ravel());assert base.v14.strand_signature(o)==signature;o['aevrynd_revision']='female-next-r0022-a';rows.append({'object':o.name,'curves':len(paths),'points':sum(len(p) for p in paths)});print('R0022_LAYER',o.name,len(paths),flush=True)
    bpy.data.objects['AFN14_GUIDES'].hide_viewport=True;bpy.data.objects['AFN14_GUIDES'].hide_render=True;bpy.data.objects['AFN14_SCALP_EMITTER']['aevrynd_layer']='OLD_DOMAIN_REFERENCE_NOT_CURRENT_EMITTER';assert head_state()==before;np.savez_compressed(CACHE,positions=np.concatenate(allP),radii=np.array(allR,np.float32),offsets=np.array(offsets,np.int64),layers=np.array(layers,np.int8));(S/'aevrynd-female-next-r0022-a-root-bindings.json').write_text(json.dumps(bindings,separators=(',',':'))+'\n');bpy.context.scene['aevrynd_revision']='female-next-r0022-a';bpy.context.scene['aevrynd_release_state']='NEW_COMPLETE_GROOM_STUDY_PENDING_FINAL_CONTACT_AND_VISUAL_GATES';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(DST));bpy.ops.wm.open_mainfile(filepath=str(DST));assert head_state()==before
    for name,sig in signatures.items():assert base.v14.strand_signature(bpy.data.objects[name])==sig
    assert not bpy.data.libraries and all(i.packed_file for i in bpy.data.images if i.source=='FILE');save('saved-build-verification.json',{'source':str(SRC),'sourceSha256':sha(SRC),'output':str(DST),'outputSha256':sha(DST),'cache':str(CACHE),'cacheSha256':sha(CACHE),'guideSource':str(GSRC),'guideDataSha256':sha(GUIDES),'headMeshesUVWeightsRigMaterialsLightsExact':True,'countsRadiiMaterialsParentingExact':True,'curveCounts':len(allP),'points':sum(len(p) for p in allP),'layers':rows,'newScalpDomains':2,'fileBytes':DST.stat().st_size,'wallSeconds':time.time()-started,'status':'REOPEN_CONTROL_PASS_FINAL_CONTACT_PENDING'});print('R0022_CHILDREN_SAVED',flush=True)
def render():
    prev.E=E;prev.SRC=SRC;prev.DST=DST;prev.render()
if __name__=='__main__':
    if '--children' in sys.argv:children()
    elif '--render' in sys.argv:render()
    else:guides()
