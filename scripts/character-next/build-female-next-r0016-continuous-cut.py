"""Second justified candidate: continuous arc cuts remove A's CV-grid steps."""
import bpy, importlib.util, json, sys, time
from pathlib import Path
import numpy as np
spec=importlib.util.spec_from_file_location('base',Path(__file__).with_name('build-female-next-r0016-feathered-tips.py'))
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
S,E,SRC=base.S,base.E,base.SRC
DST=S/'aevrynd-female-next-r0016-b-continuous-tip-study.blend'

def build():
    start=time.time();bpy.ops.wm.open_mainfile(filepath=str(SRC));before=base.snapshot();kept=[];rows=[]
    assert base.sha(SRC)==json.loads((E/'saved-prefix-verification.json').read_text())['sourceSha256']
    base.save('b-iteration-contract.json',{'source':str(SRC),'sourceSha256':base.sha(SRC),'candidateA':'REJECTED: CV-quantized trimming creates a stepped silhouette in the same-camera 700px pilot. No final render expansion.','hypothesis':'Continuous arc-length cuts with a smooth scalp-space graduation and strand-scale variation remove CV-grid stair steps while longer tip feathering reduces the hard cutoff.','changesFromA':['No clump-ID phase discontinuities.','Cut inside an existing segment; retain that segment prefix instead of snapping to a CV.','Resize only existing native curve point arrays; no new Curves constructor.','Avoid repeated endpoint suffixes.'],'rejectIf':['No visible improvement versus the original complete-head view.','Any failed capsule-subset bound.','Any head/material/root/parent control change.'],'resources':{'threads':4,'candidatesTotal':2,'pilotPixels':700,'finalViewsIfPilotPasses':3}})
    for li,name in enumerate(base.NAMES):
        o=bpy.data.objects['AFN14_'+name];P,rad,off=base.arrays(o);oldSig=base.signature(o);paths=[];radii=[];cuts=[];ts=[];removed=[];margins=[]
        for ci,(a,b) in enumerate(zip(off[:-1],off[1:])):
            p=P[a:b];r=rad[a:b];arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(p.astype(np.float64),axis=0),axis=1))]
            if li==2:
                paths.append(p.copy());radii.append(r.copy());cuts.append(len(p)-1);ts.append(0.);removed.append(0.);continue
            root=p[0].astype(np.float64)
            coherent=.5+.5*np.sin(64*root[1]+27*abs(root[0]))
            individual=.5+.5*np.sin(ci*2.399963229728653+li*1.3)
            trim=(.004+.010*coherent+.008*individual)*(0.65 if li==3 else 1.)
            trim=min(trim,arc[-1]*.10);target=arc[-1]-trim
            k=max(2,min(len(p)-2,int(np.searchsorted(arc,target,side='right')-1)))
            t=float((target-arc[k])/(arc[k+1]-arc[k]));assert 0<t<1
            exact=(1-t)*p[k].astype(np.float64)+t*p[k+1].astype(np.float64)
            q=np.vstack((p[:k+1],exact.astype(np.float32)))
            sr=np.r_[r[:k+1],min(r[k],r[k+1])].astype(np.float64)
            rem=target-np.r_[arc[:k+1],target]
            f=np.clip(rem/(.026+.012*coherent),0,1);f=f*f*(3-2*f)
            rr=np.maximum(1.e-8,sr*(.025+.975*f)).astype(np.float32)
            err=float(np.linalg.norm(q[-1].astype(np.float64)-exact))
            margin=float(max(r[k],r[k+1])-max(rr[-2],rr[-1]))
            assert margin>err*2+1.e-7
            paths.append(q);radii.append(rr);cuts.append(k);ts.append(t);removed.append(float(trim));margins.append(margin)
        sizes=[int(len(p)) for p in paths]
        o.data.resize_curves(sizes=sizes)
        Q=np.concatenate(paths);rr=np.concatenate(radii);o.data.position_data.foreach_set('vector',Q.ravel());o.data.attributes['radius'].data.foreach_set('value',rr)
        newSig=base.signature(o)
        assert all(newSig[k]==oldSig[k] for k in oldSig if k!='sizes')
        kept.append((o.name,P,rad,off,Q,rr,np.array(cuts,np.int32),np.array(ts,np.float64),newSig))
        rows.append({'object':o.name,'curves':len(sizes),'oldPoints':len(P),'points':len(Q),'meanRemovedArcM':float(np.mean(removed)),'maxRemovedArcM':float(max(removed)),'minimumLocalTerminalRadiusSlackM':float(min(margins)) if margins else None})
    assert base.snapshot()==before
    bpy.context.scene['aevrynd_revision']='female-next-r0016-b'
    bpy.context.scene['aevrynd_release_state']='CONTINUOUS_CUT_VISUAL_RESEARCH_NOT_RUNTIME'
    bpy.context.scene['aevrynd_groom_descriptor']='r0016-b-hair-data.npz for child paths/radii; r0014 root/guide bindings only'
    bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(DST));bpy.ops.wm.open_mainfile(filepath=str(DST))
    assert base.snapshot()==before
    saved=[];cache={}
    # Read saved arrays, independently verify each retained old edge and terminal edge.
    poseScales=[];rig=bpy.data.objects['AFN_R0005_Rig']
    for pose in ('neutral','gaze-left','gaze-right','turn-left','turn-right'):
        base.v14.solid.stage.set_pose(rig,pose)
        scales=[float(np.linalg.norm(np.array(bpy.data.objects[name].matrix_world)[:3,:3],ord=2)) for name,*_ in kept]
        poseScales.append({'pose':pose,'maxTransformOperatorNorm':max(scales)})
    maxScale=max(x['maxTransformOperatorNorm'] for x in poseScales)
    base.v14.solid.stage.set_pose(rig,'neutral')
    for name,P,rad,off,Q,rr,cuts,ts,sig in kept:
        o=bpy.data.objects[name];actual,ar,ao=base.arrays(o)
        assert np.array_equal(actual,Q) and np.array_equal(ar,rr) and base.signature(o)==sig
        assert np.isfinite(actual).all() and (ar>0).all() and all(v.value==1 for v in o.data.attributes['curve_type'].data) and not o.modifiers
        errors=[];slacks=[]
        for ci,((a,b),(x,y)) in enumerate(zip(zip(off[:-1],off[1:]),zip(ao[:-1],ao[1:]))):
            k=cuts[ci];t=ts[ci]
            if t==0:
                assert np.array_equal(actual[x:y],P[a:b]) and np.array_equal(ar[x:y],rad[a:b]);continue
            assert y-x==k+2 and np.array_equal(actual[x:y-1],P[a:a+k+1])
            assert (ar[x:y-1]<=rad[a:a+k+1]).all()
            exact=(1-t)*P[a+k].astype(np.float64)+t*P[a+k+1].astype(np.float64)
            error=float(np.linalg.norm(actual[y-1].astype(np.float64)-exact))*maxScale
            slack=float(max(rad[a+k],rad[a+k+1])-max(ar[y-2],ar[y-1]))
            assert slack>error+1.e-7
            errors.append(error);slacks.append(slack-error)
        assert np.array_equal(actual[ao[:-1]],P[off[:-1]])
        key=name.removeprefix('AFN14_');cache[key+'_positions']=actual;cache[key+'_radii']=ar;cache[key+'_offsets']=ao;cache[key+'_sourceSegment']=cuts;cache[key+'_sourceSegmentT']=ts
        saved.append({'object':name,'allRootsExact':True,'retainedSegmentsExactRadiusNonIncreasing':True,'terminalCapsulesInsideOldConservativeCapsule':True,'maximumWorldRoundoffM':max(errors) if errors else 0.,'minimumTerminalContainmentSlackAfterRoundoffM':min(slacks) if slacks else None})
    assert not bpy.data.libraries and all(i.packed_file for i in bpy.data.images if i.source=='FILE')
    cachePath=S/'aevrynd-female-next-r0016-b-hair-data.npz';np.savez_compressed(cachePath,**cache)
    base.save('b-saved-containment-verification.json',{'status':'PASS_POLY_PREFIX_AND_TERMINAL_CAPSULE_CONTAINMENT','source':str(SRC),'sourceSha256':base.sha(SRC),'output':str(DST),'outputSha256':base.sha(DST),'cache':str(cachePath),'cacheSha256':base.sha(cachePath),'checks':saved,'poses':poseScales,'headMaterialsLightsUVWeightsRigUnchanged':True,'layers':rows,'inheritedEvidence':{'chain':str(E/'saved-prefix-verification.json'),'sha256':base.sha(E/'saved-prefix-verification.json')},'proof':'Saved prefix segments coincide with source segments and have no larger radii. The new terminal endpoint lies within the old edge up to measured float32 roundoff. Candidate terminal capsule maximum radius plus world roundoff is strictly below the old conservative capsule maximum radius. Convexity of a capsule therefore contains the complete new terminal capsule. The unchanged rigid transforms preserve this argument in the five original static poses. Original full body/optical/brow/lash conservative capsule proof applies to the contained candidate.','limits':['Five static pose surface cases only, not motion or self contact.','No calibration, expression or runtime acceptance.','Guide and root bindings retained; child array lengths changed. Use this new cache.'],'wallSeconds':time.time()-start,'fileBytes':DST.stat().st_size})
    print('R0016_B_REOPEN_CONTAINMENT_PASS',flush=True)

if __name__=='__main__':
    if '--render' in sys.argv:
        base.DST=DST;base.RENDER_LABEL='candidate-b';base.render()
    else:build()
