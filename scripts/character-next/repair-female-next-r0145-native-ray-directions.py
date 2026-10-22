"""Repair actual native ray direction units before saving a second full state.
Preserve A and all original clocks/failures. No anatomy/clearance/angle changes.
"""
from pathlib import Path
import bpy,numpy as np,json,time,datetime,importlib.util
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0145-aspherical-lid-wall';S=R/'engine/assets/characters/female-next/source';OUT=S/'r0145-source/aevrynd-female-next-r0145-b-normalized-aspherical-wall.blend'
sp=importlib.util.spec_from_file_location('r145repair',Path(__file__).with_name('build-female-next-r0145-aspherical-lid-wall.py'));h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h);a=h.a
def main():
    tick=time.time();assert not OUT.exists();b=json.loads((E/'a-build-summary.json').read_text('utf-8'));src=Path(b['output']);assert a.a.sha(src)==b['sha256'];bpy.ops.wm.open_mainfile(filepath=str(src));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update();rig=bpy.data.objects[b['actualRig']];names=a.FIXED+a.MOVING;before={n:a.geometry(bpy.data.objects[n]) for n in names};protected=a.a.protected();raw={n:a.rawsig(bpy.data.objects[n]) for n in names};affected=[h.h.h.SKIN]+h.h.h.ATTACH;oldPoses={}
    for f in [2,9]:scene.frame_set(f);bpy.context.view_layer.update();oldPoses[f]={n:a.geometry(bpy.data.objects[n])[0] for n in affected}
    h.save('native-ray-direction-repair-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originalStartedUTC':'2026-10-22T01:14:55+00:00','originalFailedReadbackHandle':55866,'originalRayCapabilityHandle':1134,'observedCapability':'Target output geometry/world bounds and optical centre are consistent; explicit unit forward ray hits. Production raw direction fields failed.','changedPremise':'Explicitly normalize every native radial ray direction before its independent ray length. No angle/radius/support/clearance/tolerance/material/topology change from A. Actual selected-point ray flags must clear before any B save.','sourceAImmutablePreserved':True})
    counts={}
    for name in affected:
        ng=bpy.data.objects[name].modifiers[0].node_group;N=ng.nodes;L=ng.links;rays=[n for n in N if n.bl_idname=='GeometryNodeRaycast'];assert len(rays)==4
        for node in rays:
            prior=node.inputs['Ray Direction'].links[0].from_socket;normalize=N.new('ShaderNodeVectorMath');normalize.operation='NORMALIZE';normalize.name='AFN145_ACTUAL_UNIT_RAY_DIRECTION';L.new(prior,normalize.inputs[0]);L.new(normalize.outputs['Vector'],node.inputs['Ray Direction'])
        counts[name]=len(rays)
    operation=[]
    for f in [2,9]:
        scene.frame_set(f);rig.update_tag();bpy.context.view_layer.update();bad={};deltas={}
        for name in affected:
            ev=bpy.data.objects[name].evaluated_get(bpy.context.evaluated_depsgraph_get()).data
            for side in ['L','R']:
                attr=ev.attributes['AFN145_SlideRayFailure_'+side];values=np.empty(len(attr.data),dtype='bool');attr.data.foreach_get('value',values);bad[name+'/'+side]=int(values.sum())
            deltas[name]=float(np.linalg.norm(a.geometry(bpy.data.objects[name])[0]-oldPoses[f][name],axis=1).max())
        operation.append({'frame':f,'actualControls':{s:float(rig[p]) for s,p in h.PROPS.items()},'actualSelectedPointRayFailures':bad,'actualGeometryDifferenceFromFailedA_M':deltas})
        h.save('native-ray-direction-repair-actual-readback.json',{'originalFullA':b,'normalizedRayNodeCounts':counts,'actualOperationsBeforeSave':operation,'allObservedRayFailuresZero':all(not any(x['actualSelectedPointRayFailures'].values()) for x in operation),'appearanceFunctionContactNotAccepted':True})
        assert not any(bad.values()),('Normalized ray capability still failed',f,bad)
    assert max(operation[-1]['actualGeometryDifferenceFromFailedA_M'].values())>.0001,'No actual displayed geometry change'
    scene.frame_set(1);rig.update_tag();bpy.context.view_layer.update();assert all(a.rawsig(bpy.data.objects[n])==raw[n] for n in names);neutral={n:float(np.linalg.norm(a.geometry(bpy.data.objects[n])[0]-before[n][0],axis=1).max()) for n in names};assert max(neutral.values())<2e-6 and a.a.protected()==protected
    bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=False)
    h.save('b-build-summary.json',dict(b,source=str(src),comparisonBaseline=b['comparisonBaseline'],output=str(OUT),sha256=a.a.sha(OUT),bytes=OUT.stat().st_size,oneCompleteCandidate=False,twoFullSavedCandidateStatesInOneOriginalRound=True,originalAAndItsKnownRayFailurePreserved=True,neutralActualGeometryDifferenceFromA_M=neutral,normalizedNativeRayDirections=True,secondsBeforePreview=time.time()-tick));views=[]
    for v in ['face','body-face','profile','oblique','back']:views.append(a.b.u.v.image('b-normalized-aspherical-wall',v));h.save('b-view-controls.json',views)
    motion=[]
    for f in [5,9,13,17]:
        scene.frame_set(f);bpy.context.view_layer.update()
        for v in ['face','body-face']:
            row=a.b.u.v.image('b-blink-%03d'%f,v);row['actualBlink']={s:float(rig[p]) for s,p in h.PROPS.items()};motion.append(row);h.save('b-actual-blink-motion-controls.json',motion)
    scene.frame_set(9);bpy.context.view_layer.update();h.save('b-actual-closed-profile-control.json',a.b.u.v.image('b-closed-blink','profile'));scene.frame_set(1);bpy.context.view_layer.update();assert a.a.protected()==protected and a.a.sha(src)==b['sha256'];print('R145_B_ACTUAL_NORMALIZED_ASPHERICAL_WALL_COMPLETE_HEAD_BODY_BLINK_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
