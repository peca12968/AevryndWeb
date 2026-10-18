"""An actual-skin rooted, feathered hairline and part; preserve free lock lengths."""
import bpy,json,math,time,importlib.util,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
spec=importlib.util.spec_from_file_location('locks',Path(__file__).with_name('build-female-next-r0017-volume-locks.py'));old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
base,v14,flow,route,solid=old.base,old.v14,old.flow,old.route,old.solid
R,S=old.R,old.S;E=R/'Evidence/character-female-next/r0021-root-transition';E.mkdir(exist_ok=True)
SRC=S/'aevrynd-female-next-r0018-c-triangulated-brows-study.blend';DST=S/'aevrynd-female-next-r0021-a-root-transition-study.blend'
GUIDES=S/'aevrynd-female-next-r0021-a-root-guides.npz';CACHE=S/'aevrynd-female-next-r0021-a-hair-data.npz'
sha=base.sha
def save(name,obj):(E/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def smooth(x):return old.smooth(x)

def root_candidate(root,index,tree,layer):
    delta=root-route.C;length=float(np.linalg.norm(delta));theta=math.acos(float(np.clip(delta[2]/length,-1,1)));phi=math.atan2(delta[1],delta[0]);edgeDistance=(flow.theta_max(phi)-theta)*length
    front=float(smooth((-root[1]-.025)/.045));edge=float(1-smooth(max(edgeDistance,0)/.008))*front
    part=float(1-smooth(abs(root[0])/.008))*float(smooth((root[2]-1.505)/.015))*float(1-smooth((root[1]-.015)/.02))
    if max(edge,part)<1.e-7:return root.copy(),0.,None
    # Coherent boundary shape plus sub-millimetre follicle staggering; no
    # density increase, no random displacement of unconstrained free lengths.
    noise=math.sin(index*2.39996323+layer*1.7)
    coherent=.65*math.sin(17*phi+.7)+.35*math.sin(31*phi-1.2)
    theta+=edge*(.014*coherent+.009*noise)
    direction=np.array((math.sin(theta)*math.cos(phi),math.sin(theta)*math.sin(phi),math.cos(theta)))
    seed=route.C+direction*length
    if part>0:
        sign=1 if root[0]>0 else -1;desired=max(.00025,abs(seed[0])-.00055+.00025*math.sin(87*root[1]+.8)+.00018*noise);seed[0]=(1-part)*seed[0]+part*sign*desired
    direction=Vector(seed-route.C).normalized();hit,n,face,d=tree.ray_cast(Vector(route.C)+direction*.45,-direction,.6);assert hit is not None
    root1=np.array(hit+n*.00020,dtype=np.float64)
    return root1,max(edge,part),(np.array(hit,dtype=np.float64),np.array(n,dtype=np.float64),int(face))

def path_candidate(path,root1,strength,index,A,B):
    arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(path,axis=0),axis=1))];affected=arc<.028
    if strength==0:return path.astype(np.float32),affected&False
    fade=1-smooth(arc/.028);q=path+(root1-path[0])[None,:]*fade[:,None]
    radial=q-route.C;radial/=np.maximum(np.linalg.norm(radial,axis=1,keepdims=True),1.e-12)
    lift=(.00035+.00045*(.5+.5*math.sin(index*1.618)))*strength*np.sin(math.pi*np.clip(arc/.028,0,1))**2
    q+=radial*lift[:,None]
    active=affected&(arc>0);ramp=smooth(arc/.020)
    q[active]=route.shell_batch(q[active],A,B,.00015+.00185*ramp[active],.00005+.00095*ramp[active]);q[0]=root1;q[~affected]=path[~affected]
    return q.astype(np.float32),affected

def binding(root,tree,V,T,metadata):
    hit,n,face,d=tree.find_nearest(Vector(root));triangle=V[T[face]];p=np.array(hit);bary=np.linalg.lstsq(np.column_stack((triangle[1]-triangle[0],triangle[2]-triangle[0])),p-triangle[0],rcond=None)[0]
    return dict(metadata,bodyTriangle=int(face),bodyVertices=T[face].tolist(),barycentric=[float(1-bary.sum()),float(bary[0]),float(bary[1])],rootNormal=list(n),rootOffsetM=float(d))

def guides():
    started=time.time();manifest=json.loads((S.parent/'female-next.asset.json').read_text());assert sha(SRC)==manifest['workingReviewSha256'];bpy.ops.wm.open_mainfile(filepath=str(SRC));solid.stage.set_pose(bpy.data.objects['AFN_R0005_Rig'],'neutral');V,T,tree=solid.data(bpy.data.objects['AFN_R0008_Body']);V=np.array(V,np.float64);T=np.array(T,np.int32)
    data=np.load(S/'aevrynd-female-next-r0017-c-volume-guides.npz');G=data['guides'].astype(np.float64);A,B=data['planeNormals'],data['planeOffsets'];targets=[];bindings=[];changes=[]
    save('iteration-contract.json',{'previousGoalTurnClassification':'progress: r20 actual brow-support repair, bounded failed rim candidate, root/surface evidence and playable full-head review archived. Complete blink remains unqualified.','stage':'B_COMPLETE_HEAD_IN_PROGRESS','source':str(SRC),'sourceSha256':sha(SRC),'primaryDefect':'Hard uniform hairline and sawtooth centre-part emission; source crown reads as a cap.','hypothesis':'Replace the hard front/part root boundary with actual-skin follicle staggering and a gently varied initial lift, while joining the exact existing free lock paths after 28mm. This isolates root transition architecture instead of changing lighting, density, pigment or tip lengths.','expectedVisibleChange':'Less stamped front edge and part, fine irregular root emergence in the full face and oblique view, unchanged lower locks.','references':[{'url':'https://www.sidefx.com/tutorials/grooming-and-rendering-realistic-hair/','use':'Conceptual scalp density mask, guide versus strand variation. Own implementation; no Houdini dependency.'},{'url':'https://docs.blender.org/manual/en/5.1/modeling/geometry_nodes/hair/generation/interpolate_hair_curves.html','use':'Guide/scalp authoring concept; existing native curves edited, not importing external code.'}],'rejectIf':['Any guide capsule/body failure before child generation.','Root rebind or head/skin/eyes/brows/lashes/material/light controls fail.','New lower free-path movement beyond source arc 28mm.','No discernible full-head hairline/part improvement or new comb/bumpy cap appearance.'],'resourceBudget':{'threads':4,'candidates':1,'guides':424,'fibres':21086,'rootTransitionM':.028,'pilotResolution':800,'staticPoses':5},'scope':'Static appearance study; no full hair self-contact, dynamics or engine claim.'})
    for i,g in enumerate(G):
        root1,weight,hit=root_candidate(g[0],i,tree,-1);q,affected=path_candidate(g,root1,weight,i,A,B);targets.append(q);bindings.append(binding(q[0],tree,V,T,{'guide':i}));changes.append({'guide':i,'strength':weight,'rootMoveM':float(np.linalg.norm(root1-g[0])),'changedCVs':int(np.any(q!=g.astype(np.float32),axis=1).sum())})
    Q=np.array(targets,np.float32);audit=route.check_paths(list(Q.astype(np.float64)),[np.full(len(p),.00006) for p in Q],tree,V[T]);np.savez_compressed(GUIDES,guides=Q,oldGuides=G.astype(np.float32),planeNormals=A,planeOffsets=B);(S/'aevrynd-female-next-r0021-a-guide-bindings.json').write_text(json.dumps(bindings,separators=(',',':'))+'\n')
    save('guide-verification.json',{'status':audit['status'],'sourceSha256':sha(SRC),'guideData':str(GUIDES),'guideDataSha256':sha(GUIDES),'guides':len(Q),'changedRoots':sum(x['strength']>0 for x in changes),'changes':changes,'bodyCapsules':audit,'childrenAllowed':audit['status']=='PASS_TESTED_BODY_CAPSULES','wallSeconds':time.time()-started});print('R0021_GUIDE_GATE',audit['status'],flush=True)

def children():
    started=time.time();gate=json.loads((E/'guide-verification.json').read_text());assert gate['childrenAllowed'] and gate['guideDataSha256']==sha(GUIDES) and gate['sourceSha256']==sha(SRC);bpy.ops.wm.open_mainfile(filepath=str(SRC));solid.stage.set_pose(bpy.data.objects['AFN_R0005_Rig'],'neutral');before=base.snapshot();V,T,tree=solid.data(bpy.data.objects['AFN_R0008_Body']);V=np.array(V,np.float64);T=np.array(T,np.int32);data=np.load(GUIDES);A,B=data['planeNormals'],data['planeOffsets'];oldbindings=json.loads((S/'aevrynd-female-next-r0014-root-bindings.json').read_text());oldIndex={(r['layer'],r['curve']):r for r in oldbindings};allP=[];allR=[];offsets=[0];layers=[];bindings=[];changedRanges={};rows=[];signatures={}
    for li,name in enumerate(base.NAMES):
        o=bpy.data.objects['AFN14_'+name];P,rr,off=base.arrays(o);sig=v14.strand_signature(o);signatures[o.name]=sig;Q=P.copy();changedRoots=0;maximum=0.;curves=[]
        for ci,(first,last) in enumerate(zip(off[:-1],off[1:])):
            p=P[first:last].astype(np.float64);root1,weight,hit=root_candidate(p[0],ci,tree,li);q,affected=path_candidate(p,root1,weight,ci+li*1729,A,B);Q[first:last]=q;bindings.append(binding(q[0],tree,V,T,{'layer':li,'curve':ci,'guides':oldIndex[(li,ci)]['guides'],'weights':oldIndex[(li,ci)]['weights'],'rootTransition':'Own per-strand root field then unchanged source free lengths; original guide weights are provenance, not an assertion of exact new interpolation.'}));changedRoots+=weight>0;maximum=max(maximum,float(np.linalg.norm(q-p,axis=1).max()));assert np.array_equal(q[~affected],P[first:last][~affected]);allP.append(q);allR.extend(rr[first:last]);offsets.append(offsets[-1]+len(q));layers.append(li)
            if np.any(q!=P[first:last]):curves.append(ci)
        o.data.position_data.foreach_set('vector',Q.ravel());assert v14.strand_signature(o)==sig;changedRanges[o.name]=curves;rows.append({'object':o.name,'curves':len(off)-1,'changedRootCurves':changedRoots,'changedCurves':len(curves),'maximumPointMoveM':maximum});print('R0021_LAYER',o.name,changedRoots,flush=True)
    for spline,p in zip(bpy.data.objects['AFN14_GUIDES'].data.splines,data['guides']):spline.points.foreach_set('co',np.column_stack((p,np.ones(len(p)))).astype(np.float32).ravel())
    bpy.data.objects['AFN14_SCALP_EMITTER']['aevrynd_layer']='ORIGINAL_EMITTER_REFERENCE_NEW_ROOTS_BOUND_DIRECTLY_TO_BODY';assert base.snapshot()==before
    CACHE.parent.mkdir(exist_ok=True);np.savez_compressed(CACHE,positions=np.concatenate(allP),radii=np.array(allR,np.float32),offsets=np.array(offsets,np.int64),layers=np.array(layers,np.int8));(S/'aevrynd-female-next-r0021-a-root-bindings.json').write_text(json.dumps(bindings,separators=(',',':'))+'\n');scene=bpy.context.scene;scene['aevrynd_revision']='female-next-r0021-a';scene['aevrynd_release_state']='ROOT_TRANSITION_APPEARANCE_STUDY_PENDING_SURFACE_AND_VISUAL_GATES';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(DST));bpy.ops.wm.open_mainfile(filepath=str(DST));assert base.snapshot()==before
    for name,sig in signatures.items():assert v14.strand_signature(bpy.data.objects[name])==sig
    assert not bpy.data.libraries and all(i.packed_file for i in bpy.data.images if i.source=='FILE')
    save('saved-build-verification.json',{'source':str(SRC),'sourceSha256':sha(SRC),'output':str(DST),'outputSha256':sha(DST),'cache':str(CACHE),'cacheSha256':sha(CACHE),'layers':rows,'headMeshesUVWeightsRigMaterialsLightsExact':True,'countsRadiiMaterialsParentingExact':True,'freeCVsBeyondSourceArc28mmExact':True,'rootBindings':str(S/'aevrynd-female-next-r0021-a-root-bindings.json'),'changedCurveIds':changedRanges,'fileBytes':DST.stat().st_size,'wallSeconds':time.time()-started,'status':'REOPEN_AND_CONTROL_PASS_SURFACES_PENDING'});print('R0021_SAVED',flush=True)

def render():
    baseline='--baseline' in sys.argv;src=SRC if baseline else DST;bpy.ops.wm.open_mainfile(filepath=str(src));solid.stage.set_pose(bpy.data.objects['AFN_R0005_Rig'],'neutral');s=bpy.context.scene;s.render.threads_mode='FIXED';s.render.threads=4;head=1.5624730926266572*.91;target=(0.,-.02,head);label='baseline' if baseline else 'candidate-a';rows=[]
    for lightMode in ('saved','alternate'):
        if lightMode=='alternate':
            for light in (o for o in bpy.data.objects if o.type=='LIGHT'):
                light.location.x=-light.location.x;light.rotation_euler=(Vector(target)-light.location).to_track_quat('-Z','Y').to_euler()
        for view,location in [('face',(0.,-.90,head+.015)),('oblique',(.46,-.82,head+.04)),('profile',(.86,-.16,head+.02))]:
            if lightMode=='alternate' and view=='profile':continue
            c=s.camera;c.location=location;c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=100;s.render.resolution_x=s.render.resolution_y=800;s.render.resolution_percentage=100;dest=E/f'{label}-{lightMode}-{view}.png';s.render.filepath=str(dest);bpy.ops.render.render(write_still=True);rows.append({'path':str(dest),'view':view,'light':lightMode,'cameraMatrix':[v for row in c.matrix_world for v in row],'lens':100,'resolution':[800,800],'engine':s.render.engine,'viewTransform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma,'lights':[(o.name,list(o.location),list(o.rotation_euler),o.data.energy) for o in bpy.data.objects if o.type=='LIGHT']})
    save(label+'-renders.json',{'source':str(src),'sourceSha256':sha(src),'renders':rows})

if __name__=='__main__':
    if '--children' in sys.argv:children()
    elif '--render' in sys.argv:render()
    else:guides()
