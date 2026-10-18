"""Build a continuous actual-skin scalp emitter and a new authored flow groom.

No affine-retargeted guide is used. The fibre counts/materials/radii are held
at r0013 B; valid loaded native datablocks are edited in place, never recreated.
"""
import bpy,json,math,hashlib,importlib.util,sys,time
import numpy as np
from pathlib import Path
from mathutils import Vector
spec=importlib.util.spec_from_file_location('route',Path(__file__).with_name('build-female-next-r0013-envelope-hair.py'));route=importlib.util.module_from_spec(spec);spec.loader.exec_module(route)
solid=route.solid;S=route.S;R=route.R;E=R/'Evidence/character-female-next/r0014-scalp-flow';E.mkdir(parents=True,exist_ok=True);solid.stage.eyes.E=E
SRC=S/'aevrynd-female-next-r0013-b-safe-io-native-envelope-hair-study.blend';rng=np.random.default_rng(1414);C=route.C;N=64

def support(V):
    i=np.arange(256);z=1-2*(i+.5)/256;angle=i*math.pi*(3-math.sqrt(5));q=np.sqrt(1-z*z);A=np.vstack((np.column_stack((q*np.cos(angle),q*np.sin(angle),z)),np.eye(3),-np.eye(3)));P=V[V[:,2]>1.30]-C;b=np.max(P@A.T,axis=0)
    return A,b

def theta_max(phi):return math.radians(82-24*max(-math.sin(phi),0)+38*max(math.sin(phi),0))

def root_allowed(root):
    p=root-C;length=np.linalg.norm(p);theta=math.acos(float(np.clip(p[2]/length,-1,1)));phi=math.atan2(p[1],p[0])
    if theta>theta_max(phi)+.012:return False
    if root[2]<1.485 and root[1]<-.012:return False
    if root[2]>1.50 and root[1]<.028 and abs(root[0])<.0008:return False
    return True

def skin_ray(tree,direction):
    d=Vector(direction).normalized();hit,n,ti,dist=tree.ray_cast(Vector(C)+d*.45,-d,.6)
    assert hit is not None
    return np.array(hit+n*.00020),np.array(n)

def scalp(tree,rig):
    points=[];normals=[];faces=[];rings=12;azimuths=64
    p,n=skin_ray(tree,(0,0,1));points.append(p);normals.append(n)
    for j in range(1,rings+1):
        for k in range(azimuths):
            phi=math.tau*k/azimuths;theta=theta_max(phi)*j/rings;d=(math.sin(theta)*math.cos(phi),math.sin(theta)*math.sin(phi),math.cos(theta));p,n=skin_ray(tree,d);points.append(p);normals.append(n)
    for k in range(azimuths):faces.append((0,1+k,1+(k+1)%azimuths))
    for j in range(rings-1):
        for k in range(azimuths):
            a=1+j*azimuths+k;b=1+j*azimuths+(k+1)%azimuths;c=a+azimuths;d=b+azimuths;faces.extend(((a,c,b),(b,c,d)))
    P=np.array(points);F=np.array(faces,dtype=np.int32);area=np.linalg.norm(np.cross(P[F[:,1]]-P[F[:,0]],P[F[:,2]]-P[F[:,0]]),axis=1)*.5
    m=bpy.data.meshes.new('AFN14_SCALP_EMITTER');m.from_pydata(P.tolist(),[],F.tolist());m.update();o=bpy.data.objects.new(m.name,m);bpy.context.scene.collection.objects.link(o);route.parent_head(o,rig);o.hide_render=True;o['aevrynd_layer']='HIDDEN_SCALP_EMITTER_NOT_RENDERED_CAP';o['partHalfWidthM']=.0008
    return P,F,area/area.sum(),np.array(normals)

def resample(P,n=64):
    lengths=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(P,axis=0),axis=1))];t=np.linspace(0,lengths[-1],n)
    return np.column_stack([np.interp(t,lengths,P[:,axis]) for axis in range(3)])

def guide(root,A,b,side):
    p=root.copy();path=[p.copy()];distance=0.;phase=63*root[0]+41*root[1];tipz=1.359+.006*math.sin(phase*2)+.004*math.cos(phase*3+.7)
    for step in range(190):
        n=(p-C)/np.array((.078,.095,.085))**2;n/=np.linalg.norm(n)
        front=float(np.clip((-p[1]-.015)/.09,0,1));drive=np.array((side*(1.2+1.8*front),.22,-1.));tangent=drive-n*(drive@n);tangent/=max(np.linalg.norm(tangent),1e-12)
        free=float(np.clip((1.493-p[2])/.031,0,1));free=free*free*(3-2*free);tangent=(1-free)*tangent+free*np.array((0.,.015,-1.));tangent/=np.linalg.norm(tangent)
        ds=.00035 if step==0 else (.0007 if step==1 else .0027);distance+=ds;q=p+ds*tangent
        ramp=min(1.,distance/.020);ramp=ramp*ramp*(3-2*ramp);q=route.shell(q,A,b,.00015+.00185*ramp,.00005+.00095*ramp)
        path.append(q);p=q
        if p[2]<=tipz and step>8:break
    else:raise RuntimeError('Guide did not fall to bob tip')
    path=np.array(path);tail=resample(path[2:],62);P=np.vstack((path[:2],tail))
    # Clump-scale gentle curl and varied inward tips, applied before the same
    # conservative global route; no nearest-body pushing of free lengths.
    u=np.linspace(0,1,64);rad=P-C;rad[:,2]=0;rad/=np.maximum(np.linalg.norm(rad,axis=1,keepdims=True),1e-9)
    P+=rad*(.0012*np.sin(math.pi*u)*np.sin(3*math.pi*u+phase))[:,None]
    curl=np.clip((u-.80)/.20,0,1);P-=rad*(.0035*curl*curl)[:,None]
    s=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(P,axis=0),axis=1))];ramp=np.clip(s/.020,0,1);ramp=ramp*ramp*(3-2*ramp)
    P[1:]=route.shell_batch(P[1:],A,b,.00015+.00185*ramp[1:],.00005+.00095*ramp[1:]);P[0]=root
    return P

def make_guides():
    started=time.time();bpy.ops.wm.open_mainfile(filepath=str(SRC));rig=bpy.data.objects['AFN_R0005_Rig'];solid.stage.set_pose(rig,'neutral');body=bpy.data.objects['AFN_R0008_Body'];body.data.calc_loop_triangles();V,T,tree=solid.data(body);V=np.array(V,dtype=np.float64);tri=V[np.array(T,dtype=np.int32)];A,b=support(V);P,F,prob,normals=scalp(tree,rig)
    seeds=[]
    for p in P[::2]:
        if root_allowed(p):seeds.append(p)
    # Explicit near-part rows prevent the old disconnected guide domain from
    # leaving a broad crown strip without root/flow coverage.
    for y in np.linspace(-.105,.028,24):
        for sign in (-1,1):
            hit,n,ti,d=tree.ray_cast(Vector((sign*.00095,float(y),1.72)),Vector((0,0,-1)),.3)
            if hit is not None:
                root=np.array(hit+n*.00020)
                if root_allowed(root):seeds.append(root)
    G=np.array([guide(p,A,b,1 if p[0]>=0 else -1) for p in seeds]);audit=route.check_paths(list(G),[np.full(64,.00006) for g in G],tree,tri)
    o=route.legacy_guides(list(G),rig);o.name='AFN14_GUIDES';o.data.name=o.name;o['aevrynd_revision']='female-next-r0014';o['aevrynd_layer']='AUTHORED_SCALP_FLOW_GUIDES'
    for o in bpy.data.objects:
        if o.type=='CURVES' and o.name.startswith('AFN13_'):o.hide_render=True
    np.savez_compressed(S/'aevrynd-female-next-r0014-a-scalp-guides.npz',guides=G.astype(np.float32),scalpVertices=P.astype(np.float32),scalpFaces=F,scalpProbabilities=prob,planeNormals=A,planeOffsets=b)
    scene=bpy.context.scene;scene['aevrynd_revision']='female-next-r0014-a-scalp-guides';scene['aevrynd_release_state']='GUIDE_AND_EMITTER_STUDY_NOT_RUNTIME';dest=S/'aevrynd-female-next-r0014-a-scalp-guides.blend';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(dest))
    result={'source':str(SRC),'sourceSha256':route.sha(SRC),'output':str(dest),'outputSha256':route.sha(dest),'scalpVertices':len(P),'scalpTriangles':len(F),'scalpAreaM2':float(np.sum(np.linalg.norm(np.cross(P[F[:,1]]-P[F[:,0]],P[F[:,2]]-P[F[:,0]]),axis=1)*.5)),'guides':len(G),'partHalfWidthM':.0008,'field':'Authored tangent vector field away from a narrow centre part, gravity-aligned drop and small inward tip curl. No transferred affine guides.','proxyPlanes':len(A),'guideBodyCheck':audit,'childGenerationAllowed':audit['status']=='PASS_TESTED_BODY_CAPSULES','wallSeconds':time.time()-started}
    (E/'scalp-guide-verification.json').write_text(json.dumps(result,indent=2)+'\n');print('AFN14_GUIDES='+json.dumps({k:v for k,v in result.items() if k!='guideBodyCheck'}),flush=True);print('AFN14_GUIDE_AUDIT='+json.dumps({k:v for k,v in audit.items() if 'Samples' not in k}),flush=True)

def sample_root(tree,P,F,prob,near_edge=False):
    for attempt in range(1000):
        ids=F[int(rng.choice(len(F),p=prob))];s=math.sqrt(float(rng.random()));v=float(rng.random());w=np.array((1-s,s*(1-v),s*v));seed=np.einsum('i,ij->j',w,P[ids]);hit,n,ti,d=tree.find_nearest(Vector(seed));root=np.array(hit+n*.00020)
        if not root_allowed(root):continue
        delta=root-C;theta=math.acos(float(delta[2]/np.linalg.norm(delta)));phi=math.atan2(delta[1],delta[0])
        if near_edge and not(theta/theta_max(phi)>.89 and root[1]<-.04):continue
        return root,np.array(n),int(ti),np.array(hit)
    raise RuntimeError('Scalp root sampler exhausted bounded attempts')

def make_children():
    start=time.time();proof=json.loads((E/'scalp-guide-verification.json').read_text());assert proof['childGenerationAllowed'];src=Path(proof['output']);assert route.sha(src)==proof['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(src));rig=bpy.data.objects['AFN_R0005_Rig'];solid.stage.set_pose(rig,'neutral');body=bpy.data.objects['AFN_R0008_Body'];body.data.calc_loop_triangles();V,T,tree=solid.data(body);V=np.array(V,dtype=np.float64);T=np.array(T,dtype=np.int32)
    d=np.load(S/'aevrynd-female-next-r0014-a-scalp-guides.npz');G=d['guides'].astype(np.float64);P=d['scalpVertices'];F=d['scalpFaces'];prob=d['scalpProbabilities'];A=d['planeNormals'];b=d['planeOffsets'];roots=G[:,0];allP=[];allR=[];layers=[];bindings=[];allLayer=[]
    for li,name in enumerate(('PRIMARY_MASS','SECONDARY_CLUMPS','HAIRLINE_FINE','FLYAWAYS')):
        obj=bpy.data.objects['AFN13_'+name];sizes=[c.points_length for c in obj.data.curves];rr=np.empty(len(obj.data.points),dtype=np.float32);obj.data.attributes['radius'].data.foreach_get('value',rr);offset=np.r_[0,np.cumsum(sizes)];paths=[]
        for ci,size in enumerate(sizes):
            root,n,ti,hit=sample_root(tree,P,F,prob,li==2);side=1 if root[0]>=0 else -1;eligible=np.flatnonzero(roots[:,0]*side>0);dist=np.linalg.norm(roots[eligible]-root,axis=1);ids=eligible[np.argsort(dist)[:3]];distance=np.linalg.norm(roots[ids]-root,axis=1);w=1/np.maximum(distance,.0006)**2;w/=w.sum()
            u=np.linspace(0,1,64);clump=(.20 if li==0 else .65)*u**1.8;one=np.eye(3)[np.argmax(w)];weights=(1-clump[:,None])*w+clump[:,None]*one;raw=np.einsum('ji,ijk->jk',weights,G[ids]);raw+=(root-np.einsum('i,ij->j',w,roots[ids]))[None,:]*(1-u[:,None])**2
            raw[:,2]+=float(rng.uniform(-.0015,.0015))*u**5
            if li==2:raw=resample(raw[:(18 if size==24 else 30)],size)
            elif size!=64:raw=resample(raw,size)
            if li==3:
                radial=raw-C;radial/=np.maximum(np.linalg.norm(radial,axis=1,keepdims=True),1e-9);raw+=radial*(.0015*np.sin(np.linspace(0,math.pi,len(raw))))[:,None]
            arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(raw,axis=0),axis=1))];ramp=np.clip(arc/.02,0,1);ramp=ramp*ramp*(3-2*ramp);raw[1:]=route.shell_batch(raw[1:],A,b,.00015+.00185*ramp[1:],.00005+.00095*ramp[1:]);raw[0]=root
            paths.append(raw);allLayer.append(li)
            triangle=V[T[ti]];bc=np.linalg.lstsq(np.column_stack((triangle[1]-triangle[0],triangle[2]-triangle[0])),hit-triangle[0],rcond=None)[0];bindings.append({'layer':li,'curve':ci,'bodyTriangle':ti,'bodyVertices':T[ti].tolist(),'barycentric':[float(1-bc.sum()),float(bc[0]),float(bc[1])],'rootNormal':n.tolist(),'guides':ids.tolist(),'weights':w.tolist()})
        obj.data.position_data.foreach_set('vector',np.concatenate(paths).astype(np.float32).ravel());obj.name='AFN14_'+name;obj.data.name=obj.name;obj.hide_render=False;obj['aevrynd_revision']='female-next-r0014';obj['aevrynd_layer']=name
        allP.extend(paths);allR.extend([rr[a:b] for a,b in zip(offset[:-1],offset[1:])]);layers.append({'object':obj.name,'curves':len(paths),'points':int(offset[-1])});print('AFN14_LAYER='+json.dumps(layers[-1]),flush=True)
    assert len(allP)==21086 and sum(len(p) for p in allP)==1347824
    np.savez_compressed(S/'aevrynd-female-next-r0014-a-hair-data.npz',positions=np.concatenate(allP).astype(np.float32),radii=np.concatenate(allR).astype(np.float32),offsets=np.r_[0,np.cumsum([len(p) for p in allP])],layers=np.array(allLayer,dtype=np.int8))
    (E/'root-bindings.json').write_text(json.dumps(bindings,separators=(',',':'))+'\n');scene=bpy.context.scene;scene['aevrynd_revision']='female-next-r0014-a-scalp-flow';scene['aevrynd_release_state']='STATIC_HAIR_STUDY_PENDING_REOPEN_AND_VISUAL_REVIEW';dest=S/'aevrynd-female-next-r0014-a-scalp-flow-study.blend';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(dest))
    (E/'scalp-flow-build.json').write_text(json.dumps({'source':str(src),'sourceSha256':route.sha(src),'output':str(dest),'outputSha256':route.sha(dest),'layers':layers,'hairCurves':len(allP),'hairPoints':sum(len(p) for p in allP),'materialAndRadiusPolicy':'Exact r0013 B parameters/radii and counts retained; only root distribution and paths changed.','nativeIO':'Edited existing valid loaded native curve arrays; no direct new Curves ID, stock operator or library deletion.','fileBytes':dest.stat().st_size,'wallSeconds':time.time()-start,'overallCharacterScore':None},indent=2)+'\n');print('AFN14_CHILDREN_DONE',flush=True)

if __name__=='__main__':
    if '--children' in sys.argv:make_children()
    else:
        (E/'iteration-contract.json').write_text(json.dumps({'source':str(SRC),'previousGoalTurnClassification':'progress: r0013 complete-capsule static separation and exact cache I/O established; visual groom rejected','primaryDefect':'Discontinuous root/guide domain produces a broad bald part and uniform curtain flow.','hypothesis':'A continuous actual-skin scalp emitter with a 1.6 mm nominal part and an authored tangent/gravity flow removes the root-domain gap and produces curved coherent fall, at unchanged fibre counts and materials.','rejectIf':['Any unresolved guide/body capsule before child generation.','No visible improvement in crown/part/flow under the same Eevee setup.','Any changed skin geometry/material, exposure or other head components.'],'resourceBudget':{'threads':8,'guidesMaximum':500,'nativeFibres':21086,'nativePoints':1347824,'renderViews':3,'dynamicAcceptance':False}},indent=2)+'\n');make_guides()
