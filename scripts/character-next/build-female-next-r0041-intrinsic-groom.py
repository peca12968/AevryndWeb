"""Private B: complete-guide intrinsic skin transport for child paths.
Walks actual oriented body triangles, unfolding tangential displacements over
shared edges. No nearest-surface jumps or old child residuals. Not dynamics.
"""
import bpy,importlib.util,json,time
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sp=importlib.util.spec_from_file_location('frame41b',Path(__file__).with_name('build-female-next-r0041-root-frame-groom.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a)
ch=a.ch;ad=ch.ad;rt=ch.rt;rod=ch.rod;f=ch.f;b=ch.b;v=ch.v;E=a.E;PVT=a.PVT
OUT=PVT/'aevrynd-female-next-r0041-b-intrinsic-groom.blend'

class Surface:
    def __init__(self,V,T):
        self.V=V;self.T=T;self.tri=V[T];AB=self.tri[:,1]-self.tri[:,0];AC=self.tri[:,2]-self.tri[:,0]
        n=np.cross(AB,AC);self.normal=n/np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-30)
        aa=np.einsum('ij,ij->i',AB,AB);cc=np.einsum('ij,ij->i',AC,AC);ac=np.einsum('ij,ij->i',AB,AC);den=aa*cc-ac*ac;assert np.min(den)>0
        gb=(cc[:,None]*AB-ac[:,None]*AC)/den[:,None];gc=(aa[:,None]*AC-ac[:,None]*AB)/den[:,None];self.grad=np.stack((-gb-gc,gb,gc),axis=1)
        edges=np.stack((T[:,[1,2]],T[:,[2,0]],T[:,[0,1]]),axis=1).reshape(-1,2);edges.sort(axis=1);keys=edges[:,0].astype('i8')*len(V)+edges[:,1];order=np.argsort(keys);pairs=np.flatnonzero(keys[order[:-1]]==keys[order[1:]])
        assert not np.any(np.diff(pairs)==1),'Nonmanifold shared edge'
        flat=np.full(len(keys),-1,dtype='i4');lo=order[pairs];hi=order[pairs+1];flat[lo]=hi//3;flat[hi]=lo//3;self.adj=flat.reshape(-1,3)
        self.tree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True)
    def bary(self,tid,P):
        bc=self.grad[tid]@(P-self.tri[tid,0]);bc[0]+=1.;return bc
    def walk(self,tid,bc,delta):
        tid=int(tid);bc=bc.copy();delta=delta.copy();initialLength=float(np.linalg.norm(delta));travel=0.;tiny=0;visited={};transport=np.eye(3)
        for step in range(200):
            delta-=self.normal[tid]*(delta@self.normal[tid]);dw=self.grad[tid]@delta;end=bc+dw
            if np.min(end)>=-1e-9:
                end=np.maximum(end,0);end/=end.sum();return int(tid),end@self.tri[tid],self.normal[tid],step,transport
            active=np.where(dw<-1e-13,np.maximum(bc,0)/np.maximum(-dw,1e-30),np.inf);edge=int(np.argmin(active));t=float(np.clip(active[edge],0,1));cross=(bc+t*dw)@self.tri[tid];nt=int(self.adj[tid,edge])
            if nt<0:raise RuntimeError('Intrinsic walk reached body boundary')
            travel+=float(np.linalg.norm(delta))*t;tiny+=t<1e-8;visited[tid]=visited.get(tid,0)+1
            turn=a.rotation(self.normal[tid],self.normal[nt]);transport=turn@transport;delta=turn@(delta*(1-t));tid=nt;bc=self.bary(tid,cross);bc=np.maximum(bc,0);bc/=bc.sum()
        raise RuntimeError(('Intrinsic walk exceeded200edge crossings',{'initialLengthM':initialLength,'travelM':travel,'remainingM':float(np.linalg.norm(delta)),'tinyExits':tiny,'uniqueFaces':len(visited),'maxFaceVisits':max(visited.values())}))

def math_controls():
    V=np.array(((0.,0.,0.),(1.,0.,0.),(0.,1.,0.),(1.,1.,0.)))
    T=np.array(((0,1,2),(1,3,2)),dtype='i4');s=Surface(V,T);tid,p,n,steps,transport=s.walk(0,np.array((.6,.2,.2)),np.array((.6,.4,0.)));assert tid==1 and np.linalg.norm(p-(.8,.6,0))<1e-12
    #Folded surface: unfolding must preserve total travel over the shared edge.
    V=np.array(((0.,0.,0.),(1.,0.,0.),(0.,1.,0.),(1.,1.,1.)))
    s=Surface(V,T);p0=np.array((.25,.25,0.));d=np.array((.5,.5,0.));tid,p,n,steps,transport=s.walk(0,np.array((.5,.25,.25)),d);assert tid==1 and np.linalg.norm(transport@s.normal[0]-n)<1e-12
    hit=np.array((.5,.5,0.));assert abs(np.linalg.norm(p0-hit)+np.linalg.norm(p-hit)-np.linalg.norm(d))<1e-12
    print('R41_INTRINSIC_MATH_CONTROLS_PASS',flush=True)

def main():
    start=time.time();math_controls()
    a.save('b-method-contract.json',{'basis':'Intrinsic triangular surface transport with edge unfolding; preserve full guide path offset vector near the actual body and root-frame rigid path beyond25mm, with10..25mm smooth blend. No original-child residual, arbitrary projection or cross-island guide mixing.','mathControls':'Known flat and folded two-triangle travel and endpoint cases passed. Actual displayed pilot/body remains independent.','walkBoundChange':'Initial80face bound stopped after14mm of actual travel,80distinctfaces,max1visit and1mm left. No looping. Set200face guard, numerical and contact tolerances unchanged.','failurePolicy':'Any root logarithm failure, boundary,200face limit, nonfinite point or representative full capsule failure stops expansion.','resources':{'checkpointUTC':'2026-10-19 14:10:07 UTC','heavyJobsAtOnce':1,'blenderThreads':4,'maximumFullGenerationSeconds':720},'scope':'Static private geometric authoring; no natural dynamics,self or engine proof.'})
    guides,params=rt.unpack(rod.PVT/'c-refined-surface-guide-paths.npz');lineage=np.load(rod.PVT/'c-child-guide-lineage.npz');ii=lineage['indices'];ww=lineage['weights'];nearest=ii[np.arange(len(ii)),ww.argmax(1)]
    source=rod.c.PRIVATE/'aevrynd-female-next-r0039-c1-surface-transfer-study.blend';bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene;old=bpy.data.objects['AFN39_C1_PRIVATE_SURFACE_TRANSFER'];base,rad=ad.read_native(old);old.hide_render=True;retained=f.state();old.hide_render=False
    V,T=b.evaluated(bpy.data.objects[b.BODY],True);surface=Surface(V,T);bind=np.load(rod.c.PRIVATE/'c1-private-surface-transfer.npz');childTr=bind['rootTriangles'];childBC=bind['rootBarycentric'];childFoot=np.einsum('ij,ijk->ik',childBC,surface.tri[childTr]);childN=surface.normal[childTr]
    roots=[];cache=[]
    #All source control samples use exact body triangle/barycentric feet.
    for gi,(G,ts) in enumerate(zip(guides,params)):
        rows=[];frame=np.eye(3);previousNormal=None
        for Q in G:
            h,n,tid,dist=surface.tree.find_nearest(Vector(Q));foot,bc=rod.c1.exact_triangle_foot(Q,surface.tri[tid]);normal=surface.normal[tid]
            if previousNormal is not None:frame=a.rotation(previousNormal,normal)@frame
            rows.append((int(tid),bc,foot,Q-foot,float(np.linalg.norm(Q-foot)),frame.copy()));previousNormal=normal
        cache.append(rows);roots.append(rows[0])
    stats={'walks':0,'walkFailures':0,'maximumEdgeCrossings':0,'maximumRootLogResidualM':0.};pilotIds=np.linspace(0,len(base)-1,256,dtype='i4')
    def child(ci,requested=None):
        gi=int(nearest[ci]);G=guides[gi];rows=cache[gi];rootTid,rootBC,rootFoot,_,_,_=roots[gi];nRoot=surface.normal[rootTid];delta=childFoot[ci]-rootFoot;delta-=nRoot*(delta@nRoot)
        #Solve actual follicle endpoint in the original root tangent plane.
        for k in range(8):
            _,p,nn,steps,transport=surface.walk(rootTid,rootBC,delta);res=childFoot[ci]-p
            if np.linalg.norm(res)<1e-7:break
            delta+=transport.T@res;delta-=nRoot*(delta@nRoot)
        err=float(np.linalg.norm(res));stats['maximumRootLogResidualM']=max(stats['maximumRootLogResidualM'],err)
        if err>2e-6:raise RuntimeError(('Root logarithm did not converge',ci,err))
        ts=params[gi] if requested is None else requested
        selectedG=[];selectedRows=[]
        for t in ts:
            lo=int(np.clip(np.searchsorted(params[gi],t,side='right')-1,0,len(G)-1))
            if abs(t-params[gi][lo])<1e-14:Q=G[lo];row=rows[lo]
            else:
                Q=np.array([np.interp(t,params[gi],G[:,k]) for k in range(3)]);_,_,tid,_=surface.tree.find_nearest(Vector(Q));foot,bc=rod.c1.exact_triangle_foot(Q,surface.tri[tid]);frame=a.rotation(surface.normal[rows[lo][0]],surface.normal[tid])@rows[lo][5];row=(int(tid),bc,foot,Q-foot,float(np.linalg.norm(Q-foot)),frame)
            selectedG.append(Q);selectedRows.append(row)
        selectedG=np.array(selectedG);R=a.rotation(nRoot,childN[ci]);rigid=base[ci][0]+(selectedG-G[0])@R.T;result=rigid.copy()
        for j,(tid,bc,foot,offset,distance,frame) in enumerate(selectedRows):
            if j==0:result[0]=base[ci][0];continue
            if distance>=.025:continue
            tangent=frame@delta
            try:nt,newfoot,newnormal,steps,transport=surface.walk(tid,bc,tangent)
            except RuntimeError:
                stats['walkFailures']+=1;raise
            stats['walks']+=1;stats['maximumEdgeCrossings']=max(stats['maximumEdgeCrossings'],steps)
            intrinsic=newfoot+transport@offset
            q=np.clip((distance-.010)/.015,0,1);q=q*q*(3-2*q);result[j]=intrinsic*(1-q)+rigid[j]*q
        rr=np.interp(ts,np.linspace(0,1,len(rad[ci])),rad[ci]);return result,rr
    paths=[];radii=[];failure=None
    try:
        for ci in pilotIds:P,rr=child(int(ci));paths.append(P);radii.append(rr)
    except RuntimeError as ex:failure=str(ex)
    if failure:
        a.save('b-build-summary.json',{'status':'STOP_INTRINSIC_TRANSPORT_FAILURE','reason':failure,'completedPilotCurves':len(paths),'stats':stats,'fullGroomExpanded':False,'seconds':time.time()-start});print('R41_B_STOP',failure,flush=True);return
    old.hide_render=True;old.hide_set(True);pilotObj=ad.make_native(old,paths,radii,'AFN41_B_PRIVATE_ACTUAL_PILOT');actual,rr=ad.read_native(pilotObj);f.flowcheck.cap.math_controls();pilot=f.flowcheck.check(actual,rr,surface.tree,surface.tri)
    (PVT/'b-pilot-body-contact-before-refinement.json').write_text(json.dumps({'actualChildIds':pilotIds.tolist(),'proof':pilot},indent=2)+'\n')
    #Nonlinear intrinsic mapping bends a source edge. Refine that SAME map,
    #not a new collision push; any mapped point inside the body disproves it.
    curveTs=[params[int(nearest[ci])].copy() for ci in pilotIds];refinement=[];mappedInside=[]
    for depth in range(8):
        if pilot['status']=='PASS_TESTED_STATIC_CAPSULES':break
        groups={}
        for q in pilot['failureSamples']:groups.setdefault(q['curve'],set()).add(q['segment'])
        for k,edges in groups.items():
            mids=np.array([(curveTs[k][j]+curveTs[k][j+1])*.5 for j in edges]);curveTs[k]=np.unique(np.r_[curveTs[k],mids]);paths[k],radii[k]=child(int(pilotIds[k]),curveTs[k])
            for t in mids:
                j=int(np.searchsorted(curveTs[k],t));state=f.flowcheck.cap.solid.classify(surface.tree,surface.tri,Vector(paths[k][j]))
                if state!='outside':mappedInside.append({'actualChild':int(pilotIds[k]),'parameter':float(t),'state':state})
        if mappedInside:break
        pilot=f.flowcheck.check([x.astype('f4').astype('f8') for x in paths],radii,surface.tree,surface.tri);refinement.append({'depth':depth+1,'unqualifiedSegments':pilot['unqualifiedSegments'],'points':sum(map(len,paths))});print('R41_B_REFINEMENT',refinement[-1],flush=True)
    (PVT/'b-pilot-body-contact.json').write_text(json.dumps({'actualChildIds':pilotIds.tolist(),'proof':pilot,'refinement':refinement,'mappedInsideFailures':mappedInside},indent=2)+'\n');pilotObj.hide_render=True;pilotObj.hide_set(True);assert f.state()==retained
    if pilot['status']!='PASS_TESTED_STATIC_CAPSULES':
        pilotObj.hide_render=False;pilotObj.hide_set(False)
        for o in scene.objects:
            if o.type=='CURVES' and o!=pilotObj and o.name not in ('AFN36_L_BrowFibres','AFN36_R_BrowFibres'):o.hide_set(True)
        f.E=PVT;f.render('b-pilot',('face','profile'));ch.review.extras('b-pilot',PVT)
        b.camera('face');scene.camera.data.lens=85;scene['AFN41_scope']='REJECTED256CURVE_PILOT_ONLY_NOT_COMPLETE_HAIRSTYLE';bpy.context.preferences.filepaths.save_version=0
        pilotFile=PVT/'aevrynd-female-next-r0041-b-intrinsic-pilot-study.blend';bpy.ops.wm.save_as_mainfile(filepath=str(pilotFile),compress=True)
        a.save('b-build-summary.json',{'status':'STOP_INTRINSIC_MAP_POINT_OR_SEGMENT_FAILURE','pilot':{k:pilot[k] for k in ('status','curves','segments','unqualifiedSegments','minimumCertifiedClearanceLowerBoundM','minimumSampledCVSurfaceGapM')},'nativePilotOutput':str(pilotFile),'nativePilotSha256':b.sha(pilotFile),'savedNativePilotIsInitialUnrefined10FailureState':True,'mappedInsideFailures':len(mappedInside),'refinement':refinement,'fullGroomExpanded':False,'stats':stats,'seconds':time.time()-start});print('R41_B_STOP',pilot['unqualifiedSegments'],'mappedInside',len(mappedInside),stats,time.time()-start,flush=True);return
    refinedPilot=ad.make_native(old,paths,radii,'AFN41_B_PRIVATE_REFINED_PILOT');actual,rr=ad.read_native(refinedPilot);pilot=f.flowcheck.check(actual,rr,surface.tree,surface.tri);refinedPilot.hide_render=True;refinedPilot.hide_set(True)
    (PVT/'b-refined-native-pilot-body.json').write_text(json.dumps({'actualChildIds':pilotIds.tolist(),'proof':pilot},indent=2)+'\n')
    if pilot['status']!='PASS_TESTED_STATIC_CAPSULES':raise RuntimeError('Saved native refined pilot fails body gate')
    pilotCache={int(ci):(paths[k],radii[k]) for k,ci in enumerate(pilotIds)};paths=[];radii=[]
    for ci in range(len(base)):
        P,rr=pilotCache[ci] if ci in pilotCache else child(ci);paths.append(P);radii.append(rr)
        if ci%1000==0:print('R41_B_CHILDREN',ci,time.time()-start,flush=True)
        if time.time()-start>720:raise RuntimeError('12minute bounded child generation reached')
    obj=ad.make_native(old,paths,radii,'AFN41_B_PRIVATE_INTRINSIC_FIBRES');actual,rr=ad.read_native(obj);obj.hide_render=True;assert f.state()==retained;old.hide_render=False;old.hide_set(False);f.E=PVT;f.render('b-before');before=ch.review.extras('b-before',PVT);old.hide_render=True;old.hide_set(True);obj.hide_render=False;obj.hide_set(False);f.render('b-after');after=ch.review.extras('b-after',PVT);assert before==after
    b.camera('face');scene.camera.data.lens=85;scene['AFN41_status']='PRIVATE_INTRINSIC_GROOM_NOT_ADOPTED';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    a.save('b-build-summary.json',{'status':'COMPLETE_PRIVATE_GROOM_VISUAL_REVIEW_REQUIRED','output':str(OUT),'sha256':b.sha(OUT),'count':len(actual),'points':sum(map(len,actual)),'pilot':{k:pilot[k] for k in ('status','curves','segments','unqualifiedSegments','minimumCertifiedClearanceLowerBoundM','minimumSampledCVSurfaceGapM')},'fullGroomExpanded':True,'stats':stats,'seconds':time.time()-start,'allChildSelfContinuousRuntime':'NOT_QUALIFIED'})

if __name__=='__main__':main()
