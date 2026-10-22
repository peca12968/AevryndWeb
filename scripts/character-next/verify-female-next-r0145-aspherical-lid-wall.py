"""Independent actual full-skin operation, original-point lineage and raw contacts."""
from pathlib import Path
import bpy,numpy as np,json,time,importlib.util
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0145-aspherical-lid-wall'
def module(n,name):
    sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(name));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
h=module('r145readback','build-female-next-r0145-aspherical-lid-wall.py');a=h.a;ct=module('r145contact','contact-female-next-r0138-ocular-surfaces.py');sig=module('r145materials','build-female-next-r0131-native-hair-material.py')
def snap(names):return {n:a.geometry(bpy.data.objects[n]) for n in names}
def weights(ob):
    x=np.zeros((len(ob.data.vertices),len(ob.vertex_groups)))
    for v in ob.data.vertices:
        for g in v.groups:x[v.index,g.group]=g.weight
    return x
def main():
    tick=time.time();b=json.loads((E/'a-build-summary.json').read_text('utf-8'));src=Path(b['output']);assert a.a.sha(src)==b['sha256'];names=a.FIXED+a.MOVING;skinName=h.h.h.SKIN
    bpy.ops.wm.open_mainfile(filepath=b['comparisonBaseline']);scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update();protected=a.a.protected();baseline=snap(names);raw={n:a.rawsig(bpy.data.objects[n]) for n in names if n!=skinName};mats={m.name:sig.signature(m) for m in bpy.data.materials};oldWeights=weights(bpy.data.objects[skinName]);oldGroupNames=[g.name for g in bpy.data.objects[skinName].vertex_groups];originalAction=bpy.data.objects[b['actualRig']].animation_data.action.name;originalGaze={};oldControls={}
    for f in range(1,50):
        scene.frame_set(f);bpy.context.view_layer.update();originalGaze[f]=snap([skinName]+h.h.h.ATTACH+a.MOVING);oldControls[f]={n:list(bpy.data.objects[b['actualRig']].pose.bones[n].rotation_euler) for n in a.bone_names().values()}
    bpy.ops.wm.open_mainfile(filepath=str(src));scene=bpy.context.scene;rig=bpy.data.objects[b['actualRig']];skin=bpy.data.objects[skinName];scene.frame_set(1);bpy.context.view_layer.update();mapping=h.attr_array(skin.data,'AFN145_ORIGINAL_VERTEX_ID');ids=np.flatnonzero(mapping>=0);assert len(ids)==len(baseline[skinName][0]) and len(np.unique(mapping[ids]))==len(ids)
    assert a.a.protected()==protected and {n:a.rawsig(bpy.data.objects[n]) for n in raw}==raw and {m.name:sig.signature(m) for m in bpy.data.materials if m.name in mats}==mats
    assert [g.name for g in skin.vertex_groups]==oldGroupNames and np.array_equal(weights(skin)[ids],oldWeights[mapping[ids]])
    base=snap(names);neutral={n:float(np.linalg.norm(base[n][0][ids]-baseline[n][0][mapping[ids]],axis=1).max()) if n==skinName else float(np.linalg.norm(base[n][0]-baseline[n][0],axis=1).max()) for n in names};assert max(neutral.values())<2e-6
    demo=rig.animation_data.action;slot=rig.animation_data.action_slot;display={n:{'hideRender':bpy.data.objects[n].hide_render,'materials':[m.name if m else None for m in bpy.data.objects[n].data.materials]} for n in names};a.b.u.v.image.__globals__['m'].rig.shade.settings();bpy.context.view_layer.update();assert display=={n:{'hideRender':bpy.data.objects[n].hide_render,'materials':[m.name if m else None for m in bpy.data.objects[n].data.materials]} for n in names}
    cases=[];pairs={};firstFailure=None;actual=[];gaze=[];rayFailures=[]
    def contact_pose(label,frame,now):
        nonlocal firstFailure
        W,T=now[skinName];Skin=W[T];lo=Skin.min(1);hi=Skin.max(1)
        for n in a.MOVING:
            V,F=now[n];r=ct.query(Skin,V[F],lo,hi);key=label+'-'+n;pairs[key+'-proper']=r['properCrossings'];pairs[key+'-all']=r['intersections'];row={'pose':label,'frame':frame,'actualBlink':{s:float(rig[p]) for s,p in h.PROPS.items()},'actualSkinFaces':len(T),'actualEyeFaces':len(F),'object':n,'actualSkinWorldHash':a.a.hasharray(W),'actualSkinTriangleHash':a.a.hasharray(T),'actualEyeWorldHash':a.a.hasharray(V),'aabbCandidatePairs':r['candidatePairs'],'properTriangleSurfaceCrossingPairs':len(r['properCrossings']),'allTriangleSurfaceContactPairs':len(r['intersections']),'coplanarContactPairs':len(r['coplanarContacts']),'degenerateCandidatePairs':r['degenerateCandidatePairs'],'firstProperSkinEyeFacePairs':r['properCrossings'][:20].tolist(),'actualAllFacesCoveredNotSourceOrVertexSamples':True};cases.append(row)
            if len(r['intersections']) or r['degenerateCandidatePairs']:
                firstFailure=row;return
    for f in range(1,18):
        scene.frame_set(f);bpy.context.view_layer.update();now=snap(names);assert all(np.isfinite(W).all() for W,T in now.values());props={s:float(rig[p]) for s,p in h.PROPS.items()};bad={}
        for name in [skinName]+h.h.h.ATTACH:
            mesh=bpy.data.objects[name].evaluated_get(bpy.context.evaluated_depsgraph_get()).data
            for side in ['L','R']:
                attr=mesh.attributes.get('AFN145_SlideRayFailure_'+side)
                if props['L'] or props['R']:assert attr is not None,(f,name,side)
                if attr:
                    values=np.empty(len(attr.data),dtype='bool');attr.data.foreach_get('value',values);bad[name+'/'+side]=int(values.sum())
        rayFailures.append({'frame':f,'activePointRayFailureCounts':bad});assert not any(bad.values()),(f,bad)
        actual.append({'frame':f,'actualBlink':props,'allCurrentDisplayedGeometryFinite':True,'skinWorldHash':a.a.hasharray(now[skinName][0]),'skinTriangleHash':a.a.hasharray(now[skinName][1]),'displayedSkinMaxMovementFromNeutralM':float(np.linalg.norm(now[skinName][0]-base[skinName][0],axis=1).max())})
        if firstFailure is None:contact_pose('blink-%03d'%f,f,now)
    # Independently compare all original points and native controls, regardless of blink rejection.
    rig.animation_data.action=bpy.data.actions[originalAction]
    for p in h.PROPS.values():rig[p]=0.
    rig.update_tag()
    for f in range(1,50):
        scene.frame_set(f);bpy.context.view_layer.update();now=snap([skinName]+h.h.h.ATTACH+a.MOVING);errors={}
        assert {n:list(rig.pose.bones[n].rotation_euler) for n in a.bone_names().values()}==oldControls[f]
        for n in now:
            errors[n]=float(np.linalg.norm(now[n][0][ids]-originalGaze[f][n][0][mapping[ids]],axis=1).max()) if n==skinName else float(np.linalg.norm(now[n][0]-originalGaze[f][n][0],axis=1).max());assert errors[n]<2e-6,(f,n,errors[n])
        gaze.append({'frame':f,'allOriginalPointMaxDeviationM':errors,'originalEyeControls':oldControls[f]})
        if firstFailure is None:contact_pose('original-gaze-%03d'%f,f,now)
    del originalGaze
    np.savez_compressed(E/'actual-aspherical-ocular-contact-pairs.npz',**pairs)
    h.save('actual-aspherical-ocular-surface-contact.json',{'source':str(src),'sha256':b['sha256'],'cases':cases,'firstRelatedFailure':firstFailure,'relatedRawSurfaceFailureObserved':firstFailure is not None,'allRequestedBlink17AndOriginalGaze49CasesCompleted':firstFailure is None and len(cases)==132,'earlyStopAfterFirstRelatedKnownFailure':firstFailure is not None,'actualSkinReevaluatedPerPose':True,'numericPredicateEpsilonM':ct.EPS,'epsilonIsNotPhysicalClearanceTolerance':True,'globalSignedMinimumM':None,'finiteThicknessContainmentSelfOtherLayersAlphaCombinedGazeBlinkAndContinuousAccepted':False,'noFailingFacesRemovedEyesScaledRangeShrunkOrToleranceRelaxed':True,'seconds':time.time()-tick})
    rig.animation_data.action=None
    for n in a.bone_names().values():rig.pose.bones[n].rotation_euler=(0,0,0)
    for p in h.PROPS.values():rig[p]=0.
    rig.update_tag();bpy.context.view_layer.update();rest=snap(names);manual=[]
    for l,r in [(1.,0.),(0.,1.),(.5,.5),(1.,1.),(0.,0.)]:
        rig[h.PROPS['L']]=l;rig[h.PROPS['R']]=r;rig.update_tag();bpy.context.view_layer.update();now=snap(names);move={n:float(np.linalg.norm(now[n][0]-rest[n][0],axis=1).max()) for n in names};opposite=None
        if (l,r) in [(1.,0.),(0.,1.)]:
            mask=rest[skinName][0][:,0]<-.002 if l else rest[skinName][0][:,0]>.002;opposite=float(np.linalg.norm(now[skinName][0][mask]-rest[skinName][0][mask],axis=1).max());assert opposite<2e-6
        if l or r:assert move[skinName]>.001
        else:assert max(move.values())<2e-6
        manual.append({'L':l,'R':r,'actualDisplayedMeshMovementM':move,'oppositeSideSkinMovementM':opposite})
    rig.animation_data.action=demo;rig.animation_data.action_slot=slot;scene.frame_set(1);rig.update_tag();bpy.context.view_layer.update();returned=snap(names);restore={n:float(np.linalg.norm(returned[n][0]-base[n][0],axis=1).max()) for n in names};assert max(restore.values())<2e-6 and a.a.protected()==protected
    textures=[]
    for im in bpy.data.images:
        if im.source=='FILE' and not im.packed_file and im.filepath:
            p=Path(bpy.path.abspath(im.filepath));assert p.is_file();textures.append({'relative':im.filepath,'absolute':str(p),'sha256':a.a.sha(p),'bytes':p.stat().st_size})
    assert a.a.sha(src)==b['sha256']
    h.save('minimum-saved-aspherical-lid-wall-readback.json',{'source':str(src),'sha256':b['sha256'],'bytes':src.stat().st_size,'independentlyReopened':True,'actualCurrentSkinSlideAndNativeControl':True,'actualControllers':h.PROPS,'allOriginalSkinPointsUniquelyAccountedFor':True,'originalSkinVertexWeightsExact':True,'otherOriginalRawMeshesAndAllOriginalMaterialGraphsExact':True,'hiddenRollbackExact':True,'actualDisplayBeforeAfterPresetIdentical':True,'neutralOriginalPointErrorsM':neutral,'numericEvaluationBoundNotContactToleranceM':2e-6,'newSkinTopologyExplicitlyChangedNotClaimedExactToR139':True,'all49OriginalGazePointAndControlPreservation':gaze,'all17ActualBlinkFrames':actual,'actualRayFailureCounts':rayFailures,'independentActualManualControls':manual,'actualNeutralAndControlStateRestored':True,'actualRestorationErrorsM':restore,'allReferencedExternalTextures':textures,'relatedRawSurfaceFailureObserved':firstFailure is not None,'newCompleteUsableBlinkAcceptedByThisReadback':False,'completeAppearanceAnatomyFiniteSelfContinuousOrRuntimeNotAutomaticallyAccepted':True,'seconds':time.time()-tick})
    print('R145_INDEPENDENT_ACTUAL_ASPHERICAL_BLINK_RESTORE_AND_GAZE49_CONTACT_DONE',firstFailure is not None,len(cases),time.time()-tick,flush=True)
if __name__=='__main__':main()
