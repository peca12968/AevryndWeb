"""Persist real packed-shaft motion as native editable point shape keys + GN.

All 481 solver states are sampled at 240Hz, with LINEAR weight interpolation.
The animation is an offline cache, not a live Aevrynd physics implementation.
The original facial action is preserved but unbound for this fixed-head test.
"""
from pathlib import Path
import bpy,numpy as np,json,time,importlib.util
sp=importlib.util.spec_from_file_location('packed62bake',Path(__file__).with_name('build-female-next-r0062-packed-bundle.py'));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
E=m.E;OUT=m.S/'aevrynd-female-next-r0062-b-cached-packed-wind-study.blend';CARRIER='AFN62_ACTUAL_SHAFT_MOTION_POINTS'

def poses():
    raw=np.load(E/'a-packed-bundle-authoring.npz')
    if (E/'c-independent-shaft-motion.npz').exists():
        cache=np.load(E/'c-independent-shaft-motion.npz');assert np.array_equal(cache['radii'],raw['radii']);return raw,None,cache['positions']
    states=np.load(E/'b-global-guide-motion.npz')['guide'];Q=np.array([m.display(C,raw['hexXY'],raw['rootOffsets'],raw['firstNormal'],raw['rootPoints']) for C in states]);return raw,states,Q

def main():
    tick=time.time();assert not OUT.exists();raw,states,Q=poses();rr=raw['radii'];preflight=[]
    # Independent complete broad-phase equivalence on the full initial bundle.
    old=E/'b-motion-static-self-falsification.json'
    if old.exists():assert json.loads(old.read_text())['sweepAndGridExactPairSetsAgreeOnWholeRestBundle']
    else:
        a,_=m.pair.grid_candidates(raw['positions'],rr);b,_=m.pair.candidates(raw['positions'],rr);assert np.array_equal(a,b)
    for key in (0,162,264,480):
        row=m.pair.static(Q[key],rr);row['state']=key;preflight.append(row)
    prefix='c' if states is None else 'b';m.save(prefix+'-motion-static-self-falsification.json',{'sweepAndGridExactPairSetsAgreeOnWholeRestBundle':True,'poses':preflight,'fullContinuousAcceptance':False,'independentActualRods':states is None})
    assert all(x['unqualifiedFinitePairs']==0 for x in preflight),'Dynamic packed shafts fail; stop before native cache expansion.'
    if states is not None:np.savez_compressed(E/'b-actual-shaft-motion.npz',positions=Q,radii=rr)
    ref=json.loads((E/'a-build-summary.json').read_text());assert m.sha(Path(ref['output']))==ref['outputSha256'];bpy.ops.wm.open_mainfile(filepath=ref['output']);ob=bpy.data.objects[m.NAME];ob.data.position_data.foreach_set('vector',Q[0].ravel());mesh=bpy.data.meshes.new(CARRIER);mesh.from_pydata(Q[0].reshape(-1,3).tolist(),[],[]);mesh.update();carrier=bpy.data.objects.new(CARRIER,mesh);bpy.context.scene.collection.objects.link(carrier);carrier.hide_render=True;carrier.hide_set(True);carrier.shape_key_add(name='Basis')
    for k in range(1,len(Q)):
        key=carrier.shape_key_add(name=f'AFN62_STATE_{k:04d}');key.data.foreach_set('co',Q[k].ravel());peak=1+k/10
        for frame,value in ((peak-.1,0.),(peak,1.),(peak+.1,0.)):key.value=value;key.keyframe_insert(data_path='value',frame=frame)
        if k%120==0:print('R62_NATIVE_KEYS',k,len(Q)-1,flush=True)
    action=carrier.data.shape_keys.animation_data.action
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    fc.extrapolation='CONSTANT'
                    for point in fc.keyframe_points:point.interpolation='LINEAR'
    ng=bpy.data.node_groups.new('AFN62_ACTUAL_SHAFT_LINEAR_CACHE','GeometryNodeTree');ng.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');ng.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry');inp=ng.nodes.new('NodeGroupInput');out=ng.nodes.new('NodeGroupOutput');info=ng.nodes.new('GeometryNodeObjectInfo');info.transform_space='RELATIVE';info.inputs['Object'].default_value=carrier;info.inputs['As Instance'].default_value=False;sample=ng.nodes.new('GeometryNodeSampleIndex');sample.data_type='FLOAT_VECTOR';sample.domain='POINT';sample.clamp=False;position=ng.nodes.new('GeometryNodeInputPosition');index=ng.nodes.new('GeometryNodeInputIndex');setpos=ng.nodes.new('GeometryNodeSetPosition');ng.links.new(inp.outputs['Geometry'],setpos.inputs['Geometry']);ng.links.new(info.outputs['Geometry'],sample.inputs['Geometry']);ng.links.new(position.outputs['Position'],sample.inputs['Value']);ng.links.new(index.outputs['Index'],sample.inputs['Index']);ng.links.new(sample.outputs['Value'],setpos.inputs['Position']);ng.links.new(setpos.outputs['Geometry'],out.inputs['Geometry']);mod=ob.modifiers.new('AFN62_NATIVE_MOTION_CACHE','NODES');mod.node_group=ng
    ctrl=bpy.data.objects['AFN59_FACE_CONTROLS'];original=ctrl.animation_data.action
    if original:original.use_fake_user=True;ctrl['AFN62_PreservedFaceAction']=original.name;ctrl.animation_data.action=None
    ctrl['blink_left']=ctrl['blink_right']=0.;scene=bpy.context.scene;scene.frame_start=1;scene.frame_end=49;scene.render.fps=24;scene['AFN62_scope']='Fixed-head61actualshafts. Play1..49. Baked240HzXPBD; scalar-angle model, not full calibrated hair/full hairstyle or realtimeengine. Original face action retained unbound for fixed neutral-body collision proof.';bpy.context.scene.frame_set(1);bpy.context.view_layer.update();g=m.g;g.k.b.camera('face');bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    m.save('b-build-summary.json',{'source':ref['output'],'sourceSha256':ref['outputSha256'],'output':str(OUT),'outputSha256':m.sha(OUT),'motionModel':'independent actual scalar-angle rods' if states is None else 'guide/follow approximation','motionData':'c-independent-shaft-motion.npz' if states is None else 'b-actual-shaft-motion.npz','actualFibres':len(rr),'actualPoints':int(Q[0].size//3),'carrier':CARRIER,'nativeShapeKeys':len(Q),'frameRange':[1,49],'fps':24,'solverStateDT':1/240,'keySpacingFrames':.1,'keyValueInterpolation':'LINEAR triangle weights, constant extrapolation','originalFaceActionPreservedUnbound':original.name if original else None,'actualDisplay':'All61nativePOLYshafts keep actual35umradii/taper/root metadata; GN uses stable point indices.','bodyOrSkinGeometryChanged':False,'fullAppearanceHairPhysicsEngineAcceptance':False,'seconds':time.time()-tick})
    print('R62_NATIVE_WIND_SOURCE_READY',time.time()-tick,flush=True)
if __name__=='__main__':main()
