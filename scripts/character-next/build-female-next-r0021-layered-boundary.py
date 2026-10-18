"""B: terminal mass behind a real short-hair boundary, not root-jitter alone."""
import bpy,json,math,importlib.util,time,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
spec=importlib.util.spec_from_file_location('rootstudy',Path(__file__).with_name('build-female-next-r0021-root-transition.py'));a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
R,S,base,solid,route,flow=a.R,a.S,a.base,a.solid,a.route,a.flow
E=a.E/'b-layered-boundary';E.mkdir(exist_ok=True)
SRC=a.SRC;DST=S/'aevrynd-female-next-r0021-b-layered-boundary-study.blend';GUIDES=S/'aevrynd-female-next-r0021-b-boundary-guides.npz';CACHE=S/'aevrynd-female-next-r0021-b-hair-data.npz'
sha=a.sha
def save(name,obj):(E/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def weight(p):
    d=p-route.C;length=float(np.linalg.norm(d));theta=math.acos(float(np.clip(d[2]/length,-1,1)));phi=math.atan2(d[1],d[0]);distance=(flow.theta_max(phi)-theta)*length
    front=float(a.smooth((-p[1]-.025)/.045));above=float(a.smooth((p[2]-1.50)/.012))
    return (1-float(a.smooth(max(distance,0)/.010)))*front*above,theta,phi,length
def retreat(p,tree):
    w,theta,phi,length=weight(p)
    if w<1.e-7:return p.copy()
    oldDirection=Vector(p-route.C).normalized();hit,n,face,d=tree.ray_cast(Vector(route.C)+oldDirection*.45,-oldDirection,.6);assert hit is not None;offset=length-float(np.linalg.norm(np.array(hit)-route.C));assert offset>-.000001,offset
    # One spatial field acts on all overlying terminal strands, so long hairs
    # from further back no longer cover the entire short-hair transition band.
    theta-=w*(.035+.008*math.sin(13*phi+.5)+.004*math.sin(29*phi))
    direction=Vector((math.sin(theta)*math.cos(phi),math.sin(theta)*math.sin(phi),math.cos(theta)));hit,n,face,d=tree.ray_cast(Vector(route.C)+direction*.45,-direction,.6);assert hit is not None
    return route.C+np.array(direction)*(float(np.linalg.norm(np.array(hit)-route.C))+max(offset,0))
def short_choice(root,ci,layer):
    w=weight(root)[0];random=.5+.5*math.sin(ci*2.3999632297+layer*1.7)
    return w>.02 and (layer==2 or random<.60*w)
def path(path,tree,ci,layer):
    short=short_choice(path[0],ci,layer);q=path.copy();keep=len(path)-1
    if short:
        arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(path,axis=0),axis=1))];length=.004+.017*(.5+.5*math.sin(ci*1.618+layer));keep=max(2,int(np.searchsorted(arc,min(length,arc[-1]),side='right')-1));q[keep+1:]=q[keep]
    else:
        for j,p in enumerate(path):q[j]=retreat(p,tree)
    return q.astype(np.float32),short,keep
def guides():
    started=time.time();bpy.ops.wm.open_mainfile(filepath=str(SRC));solid.stage.set_pose(bpy.data.objects['AFN_R0005_Rig'],'neutral');V,T,tree=solid.data(bpy.data.objects['AFN_R0008_Body']);V=np.array(V,np.float64);T=np.array(T,np.int32);data=np.load(S/'aevrynd-female-next-r0017-c-volume-guides.npz');G=data['guides'].astype(np.float64);Q=np.array([[retreat(p,tree) for p in g] for g in G],np.float32);audit=route.check_paths(list(Q.astype(np.float64)),[np.full(len(p),.00006) for p in Q],tree,V[T]);np.savez_compressed(GUIDES,guides=Q,planeNormals=data['planeNormals'],planeOffsets=data['planeOffsets']);bindings=[a.binding(q[0],tree,V,T,{'guide':i}) for i,q in enumerate(Q)];(S/'aevrynd-female-next-r0021-b-guide-bindings.json').write_text(json.dumps(bindings,separators=(',',':'))+'\n')
    save('iteration-contract.json',{'source':str(SRC),'sourceSha256':sha(SRC),'Adecision':'Visually rejected: 2737 roots shifted but overlying terminal hair still defines essentially the same hard edge. Stop root-jitter-only repair.','hypothesis':'A spatial terminal-hair retreat field acts on all overlying scalp-region strand segments, while selected existing boundary follicles retain short thinner paths. This changes layer occupancy, not total density, pigment or lighting.','expectedVisibleChange':'A visible short/fine transition ahead of the terminal-hair mass, avoiding an unbroken cap edge.','held':['All head/body/eye/brow/lash meshes, rig, UVs, materials and lights.','Total fibre count and per-curve CV allocation; no added hair.','Hair outside the spatial front boundary field for unshortened curves.'],'rejectIf':['Guide capsule/body failure.','No visible full-head edge improvement or conspicuous bald/shaved/stair edge.','Child capsule/body/component failure.'],'resourceBudget':{'threads':4,'maximumCandidatesThisRound':3,'candidateB':2,'guides':424,'fibres':21086,'spatialBoundaryWidthM':.010,'nominalTerminalRetreatRad':.035,'shortHairLengthRangeM':[.004,.021]},'limits':'Guide check concerns primary terminal field, not all short child hairs. Final children need independent checks; no self/motion/runtime proof.'});save('guide-verification.json',{'status':audit['status'],'bodyCapsules':audit,'childrenAllowed':audit['status']=='PASS_TESTED_BODY_CAPSULES','sourceSha256':sha(SRC),'guideData':str(GUIDES),'guideDataSha256':sha(GUIDES),'wallSeconds':time.time()-started});print('R0021_B_GUIDE_GATE',audit['status'],flush=True)
def children():
    started=time.time();gate=json.loads((E/'guide-verification.json').read_text());assert gate['childrenAllowed'] and sha(GUIDES)==gate['guideDataSha256'] and sha(SRC)==gate['sourceSha256'];bpy.ops.wm.open_mainfile(filepath=str(SRC));solid.stage.set_pose(bpy.data.objects['AFN_R0005_Rig'],'neutral');before=base.snapshot();V,T,tree=solid.data(bpy.data.objects['AFN_R0008_Body']);V=np.array(V,np.float64);T=np.array(T,np.int32);allP=[];allR=[];offsets=[0];layers=[];bindings=[];rows=[];changedIds={};signatures={}
    for li,name in enumerate(base.NAMES):
        o=bpy.data.objects['AFN14_'+name];P,rr,off=base.arrays(o);sig=base.signature(o);signatures[o.name]=sig;Q=P.copy();rad=rr.copy();shorts=0;changed=[]
        for ci,(first,last) in enumerate(zip(off[:-1],off[1:])):
            p=P[first:last].astype(np.float64);q,short,keep=path(p,tree,ci,li);Q[first:last]=q
            if short:
                shorts+=1;arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))];remaining=np.maximum(arc[keep]-arc,0);factor=(.42+.20*(.5+.5*math.sin(ci*1.23)))*a.smooth(remaining/max(.002,arc[keep]*.5));rad[first:last]=np.maximum(1.e-8,rr[first:last]*factor).astype(np.float32)
            if np.any(q!=P[first:last]) or short:changed.append(ci)
            bindings.append(a.binding(q[0],tree,V,T,{'layer':li,'curve':ci,'shortBoundaryHair':short,'keptSourcePrefixCV':keep if short else None}));allP.append(q);allR.extend(rad[first:last]);offsets.append(offsets[-1]+len(q));layers.append(li)
        o.data.position_data.foreach_set('vector',Q.ravel());o.data.attributes['radius'].data.foreach_set('value',rad);assert base.signature(o)==sig;assert np.all(rad<=rr);changedIds[o.name]=changed;rows.append({'object':o.name,'curves':len(off)-1,'shortBoundaryFibres':shorts,'changedCurves':len(changed),'radiiNeverIncreased':True});print('R0021_B_LAYER',o.name,shorts,flush=True)
    G=np.load(GUIDES)['guides']
    for spline,p in zip(bpy.data.objects['AFN14_GUIDES'].data.splines,G):spline.points.foreach_set('co',np.column_stack((p,np.ones(len(p)))).astype(np.float32).ravel())
    bpy.data.objects['AFN14_SCALP_EMITTER']['aevrynd_layer']='ORIGINAL_DOMAIN_REFERENCE_FINAL_ROOTS_BOUND_DIRECTLY_TO_BODY';assert base.snapshot()==before;np.savez_compressed(CACHE,positions=np.concatenate(allP),radii=np.array(allR,np.float32),offsets=np.array(offsets,np.int64),layers=np.array(layers,np.int8));bindingPath=S/'aevrynd-female-next-r0021-b-root-bindings.json';bindingPath.write_text(json.dumps(bindings,separators=(',',':'))+'\n');scene=bpy.context.scene;scene['aevrynd_revision']='female-next-r0021-b';scene['aevrynd_release_state']='LAYERED_HAIRLINE_BOUNDARY_APPEARANCE_STUDY_PENDING_GATES';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(DST));bpy.ops.wm.open_mainfile(filepath=str(DST));assert base.snapshot()==before
    for name,sig in signatures.items():assert base.signature(bpy.data.objects[name])==sig
    assert not bpy.data.libraries and all(i.packed_file for i in bpy.data.images if i.source=='FILE');save('saved-build-verification.json',{'source':str(SRC),'sourceSha256':sha(SRC),'output':str(DST),'outputSha256':sha(DST),'cache':str(CACHE),'cacheSha256':sha(CACHE),'rootBindings':str(bindingPath),'layers':rows,'changedCurveIds':changedIds,'headMeshesUVWeightsRigMaterialsLightsExact':True,'curveCountsCVAllocationMaterialsParentingExact':True,'radiusPolicy':'Unchanged except contracted/feathered short boundary fibres; never increased.','noLinkedLibrariesAndImagesPacked':True,'wallSeconds':time.time()-started,'status':'REOPEN_AND_CONTROL_PASS_SURFACES_PENDING'});print('R0021_B_SAVED',flush=True)
if __name__=='__main__':
    if '--children' in sys.argv:children()
    elif '--render' in sys.argv:
        a.SRC=SRC;a.DST=DST;a.E=E;a.render()
    else:guides()
