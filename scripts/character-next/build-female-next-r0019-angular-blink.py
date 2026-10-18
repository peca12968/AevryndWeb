"""Monotone eye-X angular warp, preserving cylindrical radius and native mesh."""
import bpy,json,math,importlib.util,time
import numpy as np
from pathlib import Path
from mathutils import Vector
spec=importlib.util.spec_from_file_location('a',Path(__file__).with_name('build-female-next-r0019-native-blink.py'));a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
R,S,E,SRC,solid=a.R,a.S,a.E,a.SRC,a.solid;DST=S/'aevrynd-female-next-r0019-c-angular-blink-study.blend'
def smooth(x):x=np.clip(x,0,1);return x*x*(3-2*x)
def trace(tree,centre,sign):
    points=[]
    def ray(x,z):return tree.ray_cast(Vector((x,-.3,z)),Vector((0,1,0)),.45)
    for absoluteX in np.linspace(.009,.050,206):
        x=sign*absoluteX;openZ=[]
        for z in np.linspace(centre[2]-.014,centre[2]+.014,161):
            hit,n,face,d=ray(x,z)
            if hit is not None and hit.y>-.115:openZ.append(float(z))
        if len(openZ)<3:continue
        one={'x':x,'absX':absoluteX}
        for label,gap,skin in (('lower',min(openZ),min(openZ)-.00035),('upper',max(openZ),max(openZ)+.00035)):
            for _ in range(16):
                z=(gap+skin)/2;hit,n,face,d=ray(x,z)
                if hit is not None and hit.y<-.115:skin=z
                else:gap=z
            z=skin+(.00012 if label=='upper' else -.00012);hit,n,face,d=ray(x,z)
            if hit is None:break
            one[label]=list(hit);one[label+'Angle']=math.atan2(hit.z-centre[2],-(hit.y-centre[1]))
        if 'upper' in one and 'lower' in one and one['upperAngle']>one['lowerAngle']+.002:points.append(one)
    assert len(points)>80,len(points)
    return points
def warp(P,centre,rim,w):
    # x/r-dependent blending of strictly increasing angular maps is increasing
    # in angle. This concerns the continuous field, not discrete mesh validity.
    dx=P[:,0]-centre[0];dy=P[:,1]-centre[1];dz=P[:,2]-centre[2];radius=np.hypot(dy,dz);phi=np.arctan2(dz,-dy);r3=np.sqrt(dx*dx+radius*radius);xs=np.array([r['x'] for r in rim]);order=np.argsort(xs);xs=xs[order];lo=np.array([r['lowerAngle'] for r in rim])[order];hi=np.array([r['upperAngle'] for r in rim])[order]
    lower=np.interp(P[:,0],xs,lo);upper=np.interp(P[:,0],xs,hi);top=1.15;epsilon=.004
    compressed=lower+(phi-lower)*epsilon/np.maximum(upper-lower,1.e-8)
    expanded=lower+epsilon+(phi-upper)*(top-lower-epsilon)/np.maximum(top-upper,1.e-8)
    mapped=np.where(phi<=lower,phi,np.where(phi<=upper,compressed,np.where(phi<top,expanded,phi)))
    taper=smooth((P[:,0]-xs[0]+.001)/.001)*smooth((xs[-1]+.001-P[:,0])/.001);radial=smooth((.026-r3)/(.026-.0165));blend=taper*radial*w
    angle=phi+blend*(mapped-phi);Q=P.copy();mask=(blend>0)&(mapped!=phi);Q[mask,1]=centre[1]-radius[mask]*np.cos(angle[mask]);Q[mask,2]=centre[2]+radius[mask]*np.sin(angle[mask]);return Q
def add_driver(key,rig,side,index):
    f=key.driver_add('value');d=f.driver;d.type='SCRIPTED';v=d.variables.new();v.name='w';v.type='SINGLE_PROP';v.targets[0].id=rig;v.targets[0].data_path='["AFN19_Blink_'+side+'"]';d.expression=f'max(0,1-abs(4*min(1,max(0,w))-{index}))'
def main():
    started=time.time();bpy.ops.wm.open_mainfile(filepath=str(SRC));rig=bpy.data.objects['AFN_R0005_Rig'];solid.stage.set_pose(rig,'neutral');before=a.prior.controls();body=bpy.data.objects['AFN_R0008_Body'];P=a.positions(body).astype(np.float64);assert np.max(np.abs(np.array(body.matrix_world)-np.eye(4)))<1.e-8;V,T,tree=solid.data(body);fits=solid.stage.eyes.helper_centres();rims={};fields={};stats=[]
    for side,sign in (('L',1),('R',-1)):
        centre=np.array(fits[side]['centre']);rim=trace(tree,centre,sign);rims[side]=rim;fields[side]=[warp(P,centre,rim,j/4).astype(np.float32) for j in range(1,5)];rig['AFN19_Blink_'+side]=0.;rig.id_properties_ui('AFN19_Blink_'+side).update(min=0.,max=1.,soft_min=0.,soft_max=1.)
        for j,Q in enumerate(fields[side],1):add_driver(a.add_key(body,f'AFN19_Phase{j}_{side}',Q),rig,side,j)
        stats.append({'side':side,'rimSamples':len(rim),'closedChangedVertices':int(np.any(fields[side][-1]!=P.astype(np.float32),axis=1).sum()),'maximumMoveM':float(np.linalg.norm(fields[side][-1]-P,axis=1).max()),'minimumUpperLowerAngleGapRad':float(min(r['upperAngle']-r['lowerAngle'] for r in rim))})
    sources=[R/'Evidence/character-female-next/r0010-eye-rim/c-spaced-lashes-lash-bindings.json',S/'aevrynd-female-next-r0018-c-brow-bindings.json'];records=sum([json.loads(p.read_text()) for p in sources],[]);groups={n:[r for r in records if r['object']==n] for n in sorted({r['object'] for r in records})};transport=[]
    for name,bindings in groups.items():
        o=bpy.data.objects[name];rest=a.positions(o);M=np.array(o.matrix_world);inv=np.linalg.inv(M);W=rest.astype(np.float64)@M[:3,:3].T+M[:3,3];radial=6 if name.startswith('AFN10_') else 5
        for side in ('L','R'):
            centre=np.array(fits[side]['centre']);targets=[]
            for j,Q in enumerate(fields[side],1):
                Q=Q.astype(np.float64);roots=[];rotations=[];angles=[]
                for rec in bindings:
                    ids=np.array(rec['bodyVertices']);bc=np.array(rec['barycentric']);rot=a.frame(Q[ids])@a.frame(P[ids]).T;anchor0=bc@P[ids];anchor1=bc@Q[ids];root0=W[rec['firstVertex']:rec['firstVertex']+radial].mean(axis=0);root1=anchor1+rot@(root0-anchor0);roots.append((root0,root1));rotations.append(rot);angles.append(math.atan2(root0[2]-centre[2],-(root0[1]-centre[1]))-math.atan2(root1[2]-centre[2],-(root1[1]-centre[1])))
                theta=float(np.median(angles));co,si=math.cos(theta),math.sin(theta);hinge=np.array(((1.,0.,0.),(0.,co,-si),(0.,si,co)));target=W.copy()
                for rec,(r0,r1),rot in zip(bindings,roots,rotations):
                    start=rec['firstVertex'];end=start+rec['vertices'];target[start:end]=(W[start:end]-r0)@(hinge if name.startswith('AFN10_') else rot).T+r1
                local=(target@inv[:3,:3].T+inv[:3,3]).astype(np.float32);targets.append(local);transport.append({'object':name,'side':side,'phase':j,'maximumMoveM':float(np.linalg.norm(local-rest,axis=1).max()),'hingeDegrees':math.degrees(theta) if name.startswith('AFN10_') else None})
            if any(np.any(Q!=rest) for Q in targets):
                for j,Q in enumerate(targets,1):add_driver(a.add_key(o,f'AFN19_Phase{j}_{side}',Q),rig,side,j)
    a.set_blink(0.,0.);assert a.prior.controls()==before;cache=S/'aevrynd-female-next-r0019-c-angular-blink-data.npz';np.savez_compressed(cache,neutral=P.astype(np.float32),**{f'phase{j}{side}':Q for side,phases in fields.items() for j,Q in enumerate(phases,1)})
    tests=[]
    for w in (0.,.125,.25,.5,.75,1.):
        a.set_blink(w,w);actual=np.array(solid.data(body)[0]);expected=P.copy()
        for side in ('L','R'):
            for j,Q in enumerate(fields[side],1):expected+=max(0.,1-abs(4*w-j))*(Q-P)
        err=float(np.linalg.norm(actual-expected,axis=1).max());assert err<5.e-7;tests.append({'weight':w,'maximumBodyEvaluatorErrorM':err})
    a.set_blink(0.,0.);assert a.prior.controls()==before;bpy.context.scene['aevrynd_revision']='female-next-r0019-c';bpy.context.scene['aevrynd_release_state']='MONOTONE_ANGULAR_BLINK_PENDING_ACTUAL_SURFACE_GATES';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(DST));bpy.ops.wm.open_mainfile(filepath=str(DST));a.set_blink(0.,0.);assert a.prior.controls()==before
    a.save('c-build-verification.json',{'source':str(SRC),'sourceSha256':a.sha(SRC),'output':str(DST),'outputSha256':a.sha(DST),'cache':str(cache),'cacheSha256':a.sha(cache),'neutralHeadSkinEyesLashesHairBrowsRigLightMaterialStateExact':True,'fields':stats,'transport':transport,'driverChecks':tests,'fileBytes':DST.stat().st_size,'wallSeconds':time.time()-started,'status':'REOPEN_AND_DRIVER_CONTROL_PASS_CONTACT_PENDING','limits':['Continuous angular-field injectivity is a design property; it does not prove the piecewise-linear mesh, closure completeness or contacts.','Four authored phases are linearly blended between keys; all sampled and continuous collision claims require their own evidence.']});a.save('c-traced-rims.json',rims)
    a.save('c-iteration-contract.json',{'reasonForThirdCandidate':'A native displacement overcloses the lower margin. B pointwise lower-height correction creates additional folds; stop that approach.','hypothesis':'Use a strictly increasing angular map around each eye X axis, with radius/x dependent fade and preserved cylindrical radius. This changes the deformation architecture rather than strength parameters; four angular phases reduce straight-line interpolation distortion.','spatialSettings':{'innerFullWeightSphereRadiusM':.0165,'outerZeroWeightSphereRadiusM':.026,'upperAngularIdentityLimitRad':1.15,'compressedAngleGapRad':.004},'rejectIf':['Any actual body self/eye/attachment contact remains in sample checks.','Visible unclosed iris slit, collapsed lid or unnatural deformed face.','Neutral state or eye/light/material change.'],'maximumCandidates':3})
    print('R0019_C_BUILD_REOPEN_PASS '+json.dumps(stats),flush=True)
if __name__=='__main__':main()
