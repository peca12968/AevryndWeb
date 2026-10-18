"""A guide-first volumetric lock layout, retaining skin anchors and shading."""
import bpy,importlib.util,json,math,sys,time,hashlib
from pathlib import Path
import numpy as np
spec=importlib.util.spec_from_file_location('base',Path(__file__).with_name('build-female-next-r0016-feathered-tips.py'))
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
v14=base.v14;flow=v14.flow;route=flow.route;solid=flow.solid
VARIANT='c' if '--exact-crown' in sys.argv else 'b' if '--crown-preserve' in sys.argv else 'a'
R,S=base.R,base.S;E=R/'Evidence/character-female-next/r0017-volume-locks'
if VARIANT=='b':E=E/'b-crown-transition'
if VARIANT=='c':E=E/'c-exact-crown-transition'
E.mkdir(parents=True,exist_ok=True)
SRC=S/'aevrynd-female-next-r0014-c-review.blend';DST=S/f'aevrynd-female-next-r0017-{VARIANT}-volume-locks-study.blend'
GUIDES=S/f'aevrynd-female-next-r0017-{VARIANT}-volume-guides.npz';CACHE=S/f'aevrynd-female-next-r0017-{VARIANT}-hair-data.npz'
def save(name,data): (E/name).write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
def smooth(x): x=np.clip(x,0,1);return x*x*(3-2*x)

def select_masters(roots):
    ids=[]
    for side in (-1,1):
        pool=np.flatnonzero(roots[:,0]*side>0);selected=[int(pool[np.argmax(roots[pool,2])])]
        for _ in range(11):
            d=np.min(np.linalg.norm(roots[pool,None,:]-roots[selected][None,:,:],axis=2),axis=1)
            selected.append(int(pool[np.argmax(d)]))
        ids.extend(selected)
    ids=np.array(ids,np.int32);distance=np.linalg.norm(roots[:,None,:]-roots[ids][None,:,:],axis=2)
    distance[np.sign(roots[:,0,None])!=np.sign(roots[ids][None,:,0])]=np.inf
    return ids,np.argmin(distance,axis=1).astype(np.int32)

def guide_candidate(G,A,b):
    masters,assignment=select_masters(G[:,0]);M=G[masters].copy();u=np.linspace(0,1,G.shape[1])
    for j,p in enumerate(M):
        radial=p-route.C;horizontal=radial.copy();horizontal[:,2]=0
        horizontal/=np.maximum(np.linalg.norm(horizontal,axis=1,keepdims=True),1e-10)
        radial/=np.maximum(np.linalg.norm(radial,axis=1,keepdims=True),1e-10)
        crown=smooth((p[:,2]-1.48)/.04)
        n=horizontal*(1-crown[:,None])+radial*crown[:,None];n/=np.maximum(np.linalg.norm(n,axis=1,keepdims=True),1e-10)
        tangent=np.column_stack((-horizontal[:,1],horizontal[:,0],np.zeros(len(p))))
        phase=j*2.39996323
        loft=(.006+.005*(.5+.5*math.sin(phase)))*np.sin(math.pi*u)**.8
        wave=.007*np.sin(2*math.pi*u+phase)*np.sin(math.pi*u)**.8
        M[j]=p+n*loft[:,None]+tangent*wave[:,None]
    result=[]
    for gi,p in enumerate(G):
        arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
        blend=.80*smooth((arc-.015)/.055)
        if VARIANT in ('b','c'):blend*=smooth((1.515-p[:,2])/.045)
        q=p+blend[:,None]*(M[assignment[gi]]-p)
        changed=arc>.015
        if VARIANT=='c':changed &= p[:,2]<1.515
        ramp=smooth(arc/.020)
        q[changed]=route.shell_batch(q[changed],A,b,.00015+.00185*ramp[changed],.00005+.00095*ramp[changed])
        q[~changed]=p[~changed]
        result.append(q)
    return np.array(result,dtype=np.float32),masters,assignment

def section_metrics(G):
    rows=[]
    for z in (1.51,1.46,1.40):
        hits=[]
        for p in G:
            indices=np.flatnonzero((p[:-1,2]>=z)&(p[1:,2]<z))
            if len(indices):
                j=indices[-1];t=(z-p[j,2])/(p[j+1,2]-p[j,2]);hits.append(p[j]*(1-t)+p[j+1]*t)
        if hits:
            h=np.array(hits);d=h[:,:2]-route.C[:2];r=np.linalg.norm(d,axis=1);angle=np.arctan2(d[:,1],d[:,0]);sectors=np.clip(((angle+math.pi)/(2*math.pi)*12).astype(int),0,11);widths=[]
            for sector in range(12):
                one=r[sectors==sector]
                if len(one)>=4:widths.append(float(np.percentile(one,90)-np.percentile(one,10)))
            rows.append({'zM':z,'guideCrossings':len(h),'radialMedianM':float(np.median(r)),'medianSectorRadialP90MinusP10M':float(np.median(widths)) if widths else None,'sectorCount':len(widths)})
    return rows

def guides():
    start=time.time();prior=R/'Evidence/character-female-next/r0014-scalp-flow'
    proof=json.loads((prior/'review-delivery-verification.json').read_text());assert base.sha(SRC)==proof['outputSha256']
    save('iteration-contract.json',{'previousGoalTurnClassification':'progress: two real tip candidates rendered and rejected; tip-only method stopped.','source':str(SRC),'sourceSha256':base.sha(SRC),'stage':'B_COMPLETE_HEAD_IN_PROGRESS','primaryDefect':'The complete bob is a near-continuous sheet with weak depth separation between locks.','hypothesis':'A 24-master three-dimensional clump layout, with coherent radial loft and curved flow, gives primary locks distinct cross-sectional volume while preserving skin-bound roots. Child transport must retain this volume without adding density.','reference':'https://www.sidefx.com/tutorials/grooming-and-rendering-realistic-hair/','referenceUse':'Conceptual primary clumping followed by individual strand structure; local code and geometry, no third-party assets/code imported.','expectedVisibleChange':'Readable curved locks and gaps/depth in the whole-head oblique/profile views, avoiding a single flat curtain.','rejectIf':['Any unresolved guide capsule before child generation.','Any root/head/material/light control change.','No discernible full-head volume/flow improvement under identical renders.','Hair becomes inflated tubes, rigid ropes, or conspicuous comb-like blocks.'],'resourceBudget':{'threads':4,'candidates':1,'guides':424,'masterLocks':24,'fibres':21086,'pilotPixels':700,'acceptedCandidateFinalViews':3,'staticPoses':5},'limits':'No new dynamics/self-contact/runtime acceptance; r0015 root-transition infeasibility remains unresolved.'})
    if VARIANT in ('b','c'):
        contract=json.loads((E/'iteration-contract.json').read_text());contract.update({'candidateA':'Visually withheld: free-length flow improves, but master attraction makes oversized scalloped crown lobes in profile.','reasonForSecondCandidate':'Separate preserved crown from free locks, rather than adjusting all master parameters.','hypothesis':'Keep original crown guides above z=1.515 m exactly unchanged, then smoothly activate volumetric lock attraction down to z=1.470 m. This should retain the original head-top silhouette and the improved lower side flow.','resourceBudget':dict(contract['resourceBudget'],candidates=2),'rejectIf':contract['rejectIf']+['Crown develops new lobes or the free-length benefit disappears.']});save('iteration-contract.json',contract)
    if VARIANT=='c':
        contract=json.loads((E/'iteration-contract.json').read_text());contract.update({'candidateB':'Crown no longer visibly lobed, but independent array checks falsify its exact preservation claim: 5 guide CVs move up to 52.7 um and 13,900 child CVs move up to 384.6 um above the declared crown boundary. No visual acceptance on a failed invariant.','reasonForThirdCandidate':'Apply exact crown-region protection to both final guide arrays and transported child arrays, including the shell pass. This corrects a specific verified invariant failure rather than sweeping style parameters.','hypothesis':'Use the same free-length volume field as B, with an exact unchanged source crown above z=1.515 m in guide and final child arrays. Smoothly activate transport below it.','resourceBudget':dict(contract['resourceBudget'],candidates=3)});save('iteration-contract.json',contract)
    bpy.ops.wm.open_mainfile(filepath=str(SRC));solid.stage.set_pose(bpy.data.objects['AFN_R0005_Rig'],'neutral')
    data=np.load(S/'aevrynd-female-next-r0014-c-clump-guides.npz');old=data['guides'].astype(np.float64);A=data['planeNormals'];b=data['planeOffsets']
    G,masters,assignment=guide_candidate(old,A,b)
    assert np.array_equal(G[:,0],old[:,0].astype(np.float32))
    V,T,tree=solid.data(bpy.data.objects['AFN_R0008_Body']);tri=np.array(V,dtype=np.float64)[np.array(T,dtype=np.int32)]
    audit=route.check_paths(list(G.astype(np.float64)),[np.full(64,.00006) for _ in G],tree,tri)
    np.savez_compressed(GUIDES,guides=G,oldGuides=old.astype(np.float32),planeNormals=A,planeOffsets=b,masterGuideIds=masters,guideMasterAssignments=assignment)
    save('guide-verification.json',{'status':audit['status'],'sourceSha256':base.sha(SRC),'guideData':str(GUIDES),'guideDataSha256':base.sha(GUIDES),'masterGuideIds':masters.tolist(),'guideCount':len(G),'bodyCapsules':audit,'childrenAllowed':audit['status']=='PASS_TESTED_BODY_CAPSULES','crossSectionBefore':section_metrics(old),'crossSectionAfter':section_metrics(G.astype(np.float64)),'metricScope':'Guide-line crossings of three horizontal planes, radial p90-p10 within fixed angular sectors; geometric spread only, not a realism or self-collision metric.','wallSeconds':time.time()-start})
    print('R0017_GUIDE_GATE='+audit['status'],flush=True)

def children():
    start=time.time();gate=json.loads((E/'guide-verification.json').read_text());assert gate['childrenAllowed'] and gate['guideDataSha256']==base.sha(GUIDES) and gate['sourceSha256']==base.sha(SRC)
    bpy.ops.wm.open_mainfile(filepath=str(SRC));before=base.snapshot();data=np.load(GUIDES);G=data['guides'].astype(np.float64);old=data['oldGuides'].astype(np.float64);delta=G-old;A=data['planeNormals'];b=data['planeOffsets']
    bindings=json.loads((S/'aevrynd-female-next-r0014-root-bindings.json').read_text());binding_index={(x['layer'],x['curve']):x for x in bindings}
    allP=[];allR=[];layers=[];rows=[];signatures={}
    for li,name in enumerate(base.NAMES):
        o=bpy.data.objects['AFN14_'+name];P,rr,off=base.arrays(o);signatures[o.name]=v14.strand_signature(o);paths=[];maxChange=0.
        for ci,(a,z) in enumerate(zip(off[:-1],off[1:])):
            p=P[a:z].astype(np.float64);binding=binding_index[(li,ci)];ids=np.array(binding['guides']);w=np.array(binding['weights']);u=np.linspace(0,1,len(p))
            if li==2:q=p.copy()
            else:
                assert len(p)==64
                clump=(.20 if li==0 else .65)*u**1.8;one=np.eye(3)[np.argmax(w)];weights=(1-clump[:,None])*w+clump[:,None]*one
                transport=np.einsum('ji,ijk->jk',weights,delta[ids])*(.5 if li==3 else 1.)
                if VARIANT=='c':transport*=smooth((1.515-p[:,2])/.045)[:,None]
                q=p+transport
                arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))];changed=arc>.015;ramp=smooth(arc/.020)
                if VARIANT=='c':changed &= p[:,2]<1.515
                q[changed]=route.shell_batch(q[changed],A,b,.00015+.00185*ramp[changed],.00005+.00095*ramp[changed]);q[~changed]=p[~changed]
            q=q.astype(np.float32);maxChange=max(maxChange,float(np.linalg.norm(q-p,axis=1).max()));assert np.array_equal(q[0],P[a]);paths.append(q)
        Q=np.concatenate(paths);o.data.position_data.foreach_set('vector',Q.ravel());assert v14.strand_signature(o)==signatures[o.name]
        allP.extend(paths);allR.append(rr);layers.extend([li]*len(paths));rows.append({'object':o.name,'curves':len(paths),'points':len(Q),'maximumPointDisplacementM':maxChange})
    go=bpy.data.objects['AFN14_GUIDES']
    for spline,p in zip(go.data.splines,G):spline.points.foreach_set('co',np.column_stack((p,np.ones(len(p)))).astype(np.float32).ravel())
    assert base.snapshot()==before
    scene=bpy.context.scene;scene['aevrynd_revision']='female-next-r0017-'+VARIANT;scene['aevrynd_release_state']='VOLUME_LOCKS_STUDY_PENDING_SAVED_SURFACE_AND_VISUAL_GATES';scene['aevrynd_groom_descriptor']=f'aevrynd-female-next-r0017-{VARIANT}-groom.authoring.json'
    bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(DST));bpy.ops.wm.open_mainfile(filepath=str(DST));assert base.snapshot()==before
    positions=[];radii=[]
    for li,name in enumerate(base.NAMES):
        o=bpy.data.objects['AFN14_'+name];p,r,off=base.arrays(o);assert v14.strand_signature(o)==signatures[o.name];assert np.array_equal(p,np.concatenate([x for x,l in zip(allP,layers) if l==li]));positions.append(p);radii.append(r)
    assert not bpy.data.libraries and all(i.packed_file for i in bpy.data.images if i.source=='FILE')
    np.savez_compressed(CACHE,positions=np.concatenate(positions),radii=np.concatenate(radii),offsets=np.r_[0,np.cumsum([len(p) for p in allP])],layers=np.array(layers,np.int8))
    save('saved-build-verification.json',{'source':str(SRC),'sourceSha256':base.sha(SRC),'output':str(DST),'outputSha256':base.sha(DST),'cache':str(CACHE),'cacheSha256':base.sha(CACHE),'guideDataSha256':base.sha(GUIDES),'headMeshesUVWeightsRigMaterialsLightsUnchanged':True,'countsRadiiMaterialIndicesParentingUnchanged':True,'rootsExactAndHairlineLayerUnchanged':True,'noLinkedLibrariesAndImagesPacked':True,'layers':rows,'fibres':len(allP),'points':sum(len(p) for p in allP),'fileBytes':DST.stat().st_size,'wallSeconds':time.time()-start,'status':'REOPEN_ARRAY_CONTROL_PASS_COLLISION_PENDING'})
    print('R0017_CHILD_BUILD_REOPEN_PASS',flush=True)

def render():
    from mathutils import Vector
    baseline='--baseline' in sys.argv;pilot='--pilot' in sys.argv;alternate='--alternate' in sys.argv
    src=SRC if baseline else DST;bpy.ops.wm.open_mainfile(filepath=str(src));solid.stage.set_pose(bpy.data.objects['AFN_R0005_Rig'],'neutral')
    s=bpy.context.scene;s.render.threads_mode='FIXED';s.render.threads=4;head=1.5624730926266572*.91;target=(0.,-.02,head)
    if alternate:
        # Separate lighting robustness comparison; exactly the same setup for A/B.
        for light in (o for o in bpy.data.objects if o.type=='LIGHT'):
            d=np.array(light.location,dtype=np.float64)-np.array(target);light.location=Vector(np.array(target)+np.array((-d[1],d[0],d[2])));light.rotation_euler=(Vector(target)-light.location).to_track_quat('-Z','Y').to_euler()
    views={'face':(0.,-.90,head+.015),'oblique':(.36,-.84,head+.02),'profile':(.9,-.03,head+.015)}
    rows=[];label=('baseline' if baseline else 'candidate-'+VARIANT)+('-side-light' if alternate else '-pilot' if pilot else '')
    for view in (('oblique',) if pilot or alternate else ('face','oblique','profile')):
        c=s.camera;c.location=views[view];c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=100
        s.render.resolution_x=s.render.resolution_y=700 if pilot else 1100;s.render.resolution_percentage=100
        dest=E/f'{label}-{view}.png';s.render.filepath=str(dest);bpy.ops.render.render(write_still=True)
        rows.append({'path':str(dest),'view':view,'cameraMatrix':[x for row in c.matrix_world for x in row],'lens':c.data.lens,'resolution':[s.render.resolution_x,s.render.resolution_y],'engine':s.render.engine,'viewTransform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma,'lights':[(o.name,list(o.location),list(o.rotation_euler),o.data.energy,o.data.size,list(o.data.color)) for o in bpy.data.objects if o.type=='LIGHT']})
    save(label+'-renders.json',{'source':str(src),'sourceSha256':base.sha(src),'variant':'All lights rotated 90 degrees around head, unchanged exposure/energy' if alternate else 'Unmodified original lighting','renders':rows})
    print('R0017_RENDER_DONE '+label,flush=True)

def verify():
    build=json.loads((E/'saved-build-verification.json').read_text());assert base.sha(DST)==build['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(DST));parts=[bpy.data.objects['AFN14_'+name] for name in base.NAMES]
    output=E/'saved-surface-verification.json';poses={}
    if '--resume' in sys.argv and output.exists():
        prev=json.loads(output.read_text());assert prev['candidateSha256']==base.sha(DST);poses=prev['poses']
    for pose in ('neutral','gaze-left','gaze-right','turn-left','turn-right'):
        if pose in poses:continue
        start=time.time();solid.stage.set_pose(bpy.data.objects['AFN_R0005_Rig'],pose);V,T,tree=solid.data(bpy.data.objects['AFN_R0008_Body']);tri=np.array(V,dtype=np.float64)[np.array(T,dtype=np.int32)];body={};allP=[];allR=[]
        for o in parts:
            P,rr=v14.prior.native_paths(o);allP.extend(P);allR.extend(rr);body[o.name]=route.check_paths(P,rr,tree,tri);print('R0017_STATIC '+pose+' '+o.name+' '+body[o.name]['status'],flush=True)
        extra=v14.prior.secondary_surfaces(allP,allR,[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(('AFN6_','AFN10_','AFN11_'))])
        poses[pose]={'body':body,'otherSurfaces':extra,'wallSeconds':time.time()-start}
        status='PASS_TESTED_STATIC_SURFACE_SCOPE' if all(x['status']=='PASS_TESTED_BODY_CAPSULES' for row in poses.values() for x in row['body'].values()) and all(x['status']=='PASS_SURFACE_SEPARATION' for row in poses.values() for x in row['otherSurfaces'].values()) else 'FAIL_OR_UNRESOLVED'
        save(output.name,{'candidate':str(DST),'candidateSha256':base.sha(DST),'status':status,'poses':poses,'scope':'Complete saved POLY capsules with radius vs actual body and optical/brow/lash surfaces in five static poses only. No self, continuous motion, expression or runtime acceptance.'})
        if status!='PASS_TESTED_STATIC_SURFACE_SCOPE':break
    print('R0017_SAVED_STATIC_DONE',flush=True)

if __name__=='__main__':
    if '--children' in sys.argv:children()
    elif '--render' in sys.argv:render()
    elif '--verify' in sys.argv:verify()
    else:guides()
