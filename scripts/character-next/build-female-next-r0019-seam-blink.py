"""A lower-lid height constraint and coherent lash hinge, with explicit half keys."""
import bpy,json,math,importlib.util,time
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
spec=importlib.util.spec_from_file_location('a',Path(__file__).with_name('build-female-next-r0019-native-blink.py'));a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
R,S,E,SRC,solid=a.R,a.S,a.E,a.SRC,a.solid
DST=S/'aevrynd-female-next-r0019-b-seam-blink-study.blend'
def driver(key,rig,side,half):
    c=key.driver_add('value');d=c.driver;d.type='SCRIPTED';v=d.variables.new();v.name='w';v.type='SINGLE_PROP';v.targets[0].id=rig;v.targets[0].data_path='["AFN19_Blink_'+side+'"]';d.expression='max(0,1-abs(2*min(1,max(0,w))-1))' if half else 'max(0,2*min(1,max(0,w))-1)'
def main():
    started=time.time();bpy.ops.wm.open_mainfile(filepath=str(SRC));rig=bpy.data.objects['AFN_R0005_Rig'];solid.stage.set_pose(rig,'neutral');before=a.prior.controls();body=bpy.data.objects['AFN_R0008_Body'];assert np.max(np.abs(np.array(body.matrix_world)-np.eye(4)))<1.e-8
    P=a.positions(body).astype(np.float64);data=np.load(S/'aevrynd-female-next-r0019-native-blink-data.npz');D={s:data['delta'+s].astype(np.float64) for s in ('L','R')};V,T,_=solid.data(body);V=np.array(V,dtype=np.float64);T=np.array(T,np.int32);fits=solid.stage.eyes.helper_centres();total=D['L']+D['R'];stationary=np.max(np.linalg.norm(total[T],axis=2),axis=1)<1.e-10;centres=V[T].mean(axis=1);full={};half={};corrections=[]
    for side in ('L','R'):
        centre=np.array(fits[side]['centre']);mask=stationary&(centres[:,2]<centre[2]+.0005)&(centres[:,2]>centre[2]-.016)&(centres[:,1]<-.115)&(np.abs(centres[:,0]-centre[0])<.026)
        lower=BVHTree.FromPolygons([Vector(p) for p in V],T[mask].tolist(),all_triangles=True);q=P+D[side];count=0;largest=0.;samples=[]
        for i in np.flatnonzero(D[side][:,2]<-.00001):
            p=q[i];hit,n,face,dist=lower.ray_cast(Vector((p[0],p[1],centre[2]+.002)),Vector((0,0,-1)),.035)
            if hit is None or P[i,2]<hit.z+.0008:continue
            gap=.000010;softness=.00012;h=p[2]-hit.z-gap
            if h>.0007:continue
            newZ=hit.z+gap+softness*np.logaddexp(0.,h/softness);correction=float(newZ-p[2])
            if correction>1.e-8:
                q[i,2]=newZ;count+=1;largest=max(largest,correction)
                if len(samples)<10:samples.append({'vertex':int(i),'liftM':correction,'lowerSurfaceZ':hit.z})
        full[side]=q;half[side]=P+.5*D[side];corrections.append({'side':side,'modifiedVertices':count,'maximumLiftM':largest,'stationaryLowerTriangles':int(mask.sum()),'minimumAuthoredVerticalGapM':.000010,'softTransitionM':.00012,'samples':samples})
    for side in ('L','R'):
        rig['AFN19_Blink_'+side]=0.;rig.id_properties_ui('AFN19_Blink_'+side).update(min=0.,max=1.,soft_min=0.,soft_max=1.)
        for name,target,isHalf in (('AFN19_Half_',half[side],True),('AFN19_Full_',full[side],False)):driver(a.add_key(body,name+side,target),rig,side,isHalf)
    lashPath=R/'Evidence/character-female-next/r0010-eye-rim/c-spaced-lashes-lash-bindings.json';browPath=S/'aevrynd-female-next-r0018-c-brow-bindings.json';bindings=json.loads(lashPath.read_text())+json.loads(browPath.read_text());groups={name:[r for r in bindings if r['object']==name] for name in sorted({r['object'] for r in bindings})};transports=[]
    for name,records in groups.items():
        o=bpy.data.objects[name];rest=a.positions(o);M=np.array(o.matrix_world);inv=np.linalg.inv(M);W=rest.astype(np.float64)@M[:3,:3].T+M[:3,3];radial=6 if name.startswith('AFN10_') else 5
        for side in ('L','R'):
            phaseTargets=[]
            for phase,Q in (('Half',half[side]),('Full',full[side])):
                roots=[];rotations=[];angles=[];centre=np.array(fits[side]['centre']);moved=0
                for rec in records:
                    ids=np.array(rec['bodyVertices']);bc=np.array(rec['barycentric']);F0,F1=a.frame(P[ids]),a.frame(Q[ids]);rot=F1@F0.T;anchor0=bc@P[ids];anchor1=bc@Q[ids];root0=W[rec['firstVertex']:rec['firstVertex']+radial].mean(axis=0);root1=anchor1+rot@(root0-anchor0)
                    roots.append((root0,root1));rotations.append(rot)
                    b0=math.atan2(root0[2]-centre[2],-(root0[1]-centre[1]));b1=math.atan2(root1[2]-centre[2],-(root1[1]-centre[1]));angles.append(b0-b1);moved+=np.linalg.norm(root1-root0)>1.e-9
                theta=float(np.median(angles));co,si=math.cos(theta),math.sin(theta);hinge=np.array(((1.,0.,0.),(0.,co,-si),(0.,si,co)));target=W.copy()
                for rec,(root0,root1),rot in zip(records,roots,rotations):
                    start=rec['firstVertex'];end=start+rec['vertices'];orientation=hinge if name.startswith('AFN10_') else rot;target[start:end]=(W[start:end]-root0)@orientation.T+root1
                local=target@inv[:3,:3].T+inv[:3,3];phaseTargets.append((phase,local))
                transports.append({'object':name,'side':side,'phase':phase,'movedRootFibres':int(moved),'hingeDegrees':math.degrees(theta) if name.startswith('AFN10_') else None,'orientation':'Coherent median eye-X hinge, actual triangle-frame root' if name.startswith('AFN10_') else 'Actual skin triangle frame'})
            if any(np.max(np.abs(target-rest))>1.e-9 for _,target in phaseTargets):
                for phase,target in phaseTargets:driver(a.add_key(o,'AFN19_'+phase+'_'+side,target),rig,side,phase=='Half')
    a.set_blink(0.,0.);assert a.prior.controls()==before
    cache=S/'aevrynd-female-next-r0019-b-corrected-blink-data.npz';np.savez_compressed(cache,neutral=P.astype(np.float32),halfL=half['L'].astype(np.float32),halfR=half['R'].astype(np.float32),fullL=full['L'].astype(np.float32),fullR=full['R'].astype(np.float32))
    # Validate the built-in safe-expression drivers against actual evaluated mesh arrays.
    driverTests=[]
    for w in (0.,.5,1.):
        a.set_blink(w,w);actual=np.array(solid.data(body)[0]);expected=P+(half['L']+half['R']-2*P)*(2*w if w<=.5 else 2*(1-w))+(full['L']+full['R']-2*P)*(max(0.,2*w-1));err=float(np.linalg.norm(actual-expected,axis=1).max());assert err<5.e-7;driverTests.append({'weight':w,'maximumBodyEvaluatorErrorM':err})
    a.set_blink(0.,0.);assert a.prior.controls()==before;bpy.context.scene['aevrynd_revision']='female-next-r0019-b';bpy.context.scene['aevrynd_release_state']='SEAM_CONSTRAINT_BLINK_RESEARCH_PENDING_GATES';bpy.context.scene['aevrynd_blink_controls']='Rig custom AFN19_Blink_L/R -> Half/Full piecewise morphs. No platform runtime needed for exported arrays.';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(DST));bpy.ops.wm.open_mainfile(filepath=str(DST));a.set_blink(0.,0.);assert a.prior.controls()==before
    a.save('b-build-verification.json',{'source':str(SRC),'sourceSha256':a.sha(SRC),'output':str(DST),'outputSha256':a.sha(DST),'cache':str(cache),'cacheSha256':a.sha(cache),'neutralHeadSkinEyesLashesHairBrowsRigLightMaterialStateExact':True,'corrections':corrections,'transport':transports,'driverChecks':driverTests,'controls':['AFN19_Blink_L','AFN19_Blink_R'],'fileBytes':DST.stat().st_size,'wallSeconds':time.time()-started,'status':'REOPEN_AND_DRIVER_CONTROL_PASS_CONTACT_PENDING','limits':['Lower surface height-field correction and key interpolation require complete actual contact checks.','Median lash hinge is an authoring approximation, not measured eyelash biomechanics.']})
    a.save('b-iteration-contract.json',{'reasonForSecondCandidate':'A has no optical crossings but has lower-lid/upper-lid overlap and many upper-lash self crossings. The same 462 body-self pairs exist without the r0008 socket correction, so removing that correction is not the solution and reintroduces 1776 optical crossings.','hypothesis':'Constrain the closed upper patch to the actual stationary lower surface with a smooth height floor, preserve a native half pose, and transport lashes with a coherent eye hinge instead of unstable independent strand orientations.','held':['Original neutral surface, eyes, skin, scalp hair, brow fibre count, lighting and exposure.'],'rejectIf':['Any actual sampled body self/attachment crossings remain.','Visible unclosed eye slit, flattened lid or unnatural lash fan.','Neutral or eye geometry changes.'],'candidatesSoFar':2})
    print('R0019_B_BUILD_REOPEN_PASS '+json.dumps(corrections),flush=True)
if __name__=='__main__':main()
