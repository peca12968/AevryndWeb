"""Bake the checked 48-guide world-space samples into an editable Blender diagnostic.

Every physics sample is retained as a linear shape-key interval. Full render
hair is hidden; this file must never be presented as the completed groom.
"""
import bpy,json,importlib.util,sys,time
import numpy as np
from pathlib import Path
spec=importlib.util.spec_from_file_location('flow',Path(__file__).with_name('build-female-next-r0014-scalp-flow.py'));flow=importlib.util.module_from_spec(spec);spec.loader.exec_module(flow)
E=flow.R/'Evidence/character-female-next/r0015-guide-dynamics';S=flow.S

def linear(action):
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for point in curve.keyframe_points:point.interpolation='LINEAR'

def main():
    started=time.time();case=sys.argv[sys.argv.index('--case')+1];result=json.loads((E/f'c-{case}-simulation.json').read_text());body_proof=json.loads((E/f'c-{case}-actual-body-verification.json').read_text());continuous=json.loads((E/f'c-{case}-continuous-body-verification.json').read_text());assert result['preliminaryNumericalGate']=='PASS' and body_proof['status']=='PASS_RECORDED_BODY_SAMPLES_ONLY' and continuous['status']=='PASS_CONTINUOUS_STATIC_BODY_GUIDE_SCOPE';cache=Path(result['output']);assert flow.route.sha(cache)==result['outputSha256']==continuous['cacheSha256'];d=np.load(cache);P=d['positions'];driver=json.loads((E/'driver-verification.json').read_text());bpy.ops.wm.open_mainfile(filepath=driver['source']);rig=bpy.data.objects['AFN_R0005_Rig'];flow.solid.stage.set_pose(rig,'neutral');original_geometry=flow.solid.geom(bpy.data.objects['AFN_R0008_Body'])
    for o in bpy.data.objects:
        if o.type=='CURVES' and o.name.startswith('AFN14_'):o.hide_render=True;o.hide_set(True)
    vertices=P[0].reshape(-1,3);count,points=P.shape[1:3];edges=[(g*points+j,g*points+j+1) for g in range(count) for j in range(points-1)];mesh=bpy.data.meshes.new('AFN15_CheckedGuideBank');mesh.from_pydata(vertices.tolist(),edges,[]);mesh.update();obj=bpy.data.objects.new('AFN15_CheckedGuideBank',mesh);bpy.context.scene.collection.objects.link(obj);obj['aevrynd_diagnostic_only']=True;obj['guides_simulated']=count;obj['full_groom_guides']=424;obj['child_fibres_animated']=0;obj['physical_and_display_radius_m']=.00006
    basis=obj.shape_key_add(name='Basis')
    for fi in range(1,len(P)):
        key=obj.shape_key_add(name=f'Physics_{fi:04d}',from_mix=False);key.data.foreach_set('co',P[fi].reshape(-1));key.value=0.;key.keyframe_insert(data_path='value',frame=fi);key.value=1.;key.keyframe_insert(data_path='value',frame=fi+1);key.value=0.;key.keyframe_insert(data_path='value',frame=fi+2)
    linear(mesh.shape_keys.animation_data.action)
    for fi,angle in enumerate(d['headYawRadians']):rig.pose.bones['head'].rotation_euler[1]=float(angle);rig.pose.bones['head'].keyframe_insert(data_path='rotation_euler',index=1,frame=fi+1)
    linear(rig.animation_data.action)
    material=bpy.data.materials.new('AFN15_DiagnosticGuideAmber');material.use_nodes=True;bs=next(n for n in material.node_tree.nodes if n.bl_idname=='ShaderNodeBsdfPrincipled');bs.inputs['Base Color'].default_value=(.48,.12,.015,1);bs.inputs['Roughness'].default_value=.5;bs.inputs['Emission Color'].default_value=(.3,.055,.004,1);bs.inputs['Emission Strength'].default_value=.35
    group=bpy.data.node_groups.new('AFN15_DiagnosticGuideTubes','GeometryNodeTree');group.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');group.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry');nodes=group.nodes;inp=nodes.new('NodeGroupInput');out=nodes.new('NodeGroupOutput');curve=nodes.new('GeometryNodeMeshToCurve');circle=nodes.new('GeometryNodeCurvePrimitiveCircle');circle.inputs['Resolution'].default_value=6;circle.inputs['Radius'].default_value=.00006;tube=nodes.new('GeometryNodeCurveToMesh');tube.inputs['Fill Caps'].default_value=True;mat=nodes.new('GeometryNodeSetMaterial');mat.inputs['Material'].default_value=material;group.links.new(inp.outputs['Geometry'],curve.inputs['Mesh']);group.links.new(curve.outputs['Curve'],tube.inputs['Curve']);group.links.new(circle.outputs['Curve'],tube.inputs['Profile Curve']);group.links.new(tube.outputs['Mesh'],mat.inputs['Geometry']);group.links.new(mat.outputs['Geometry'],out.inputs['Geometry']);modifier=obj.modifiers.new('Diagnostic radius - same as physics','NODES');modifier.node_group=group
    scene=bpy.context.scene;scene.frame_start=1;scene.frame_end=len(P);scene.render.fps=240;scene.render.fps_base=1.;scene.frame_set(1);scene['aevrynd_revision']='female-next-r0015-c-'+case;scene['aevrynd_release_state']='48_GUIDE_DIAGNOSTIC_NOT_FULL_GROOM_OR_RUNTIME';scene['aevrynd_continuous_collision_status']='BODY_ONLY_STATIC_HEAD_WIND_GUIDE_SCOPE_PASS';bpy.context.preferences.filepaths.save_version=0;dest=S/f'aevrynd-female-next-r0015-c-{case}-guide-motion-study.blend';bpy.ops.wm.save_as_mainfile(filepath=str(dest),compress=True)
    bpy.ops.wm.open_mainfile(filepath=str(dest));obj=bpy.data.objects['AFN15_CheckedGuideBank'];rig=bpy.data.objects['AFN_R0005_Rig'];obj.modifiers[0].show_viewport=False;errors=[]
    for fi in sorted(set((0,min(60,len(P)-1),min(150,len(P)-1),len(P)//2,len(P)-1))):
        scene=bpy.context.scene;scene.frame_set(fi+1);bpy.context.view_layer.update();me=obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;v=np.empty(len(me.vertices)*3,dtype=np.float32);me.vertices.foreach_get('co',v);error=float(np.max(np.linalg.norm(v.reshape(count,points,3)-P[fi],axis=-1)));assert error<.000001;assert abs(rig.pose.bones['head'].rotation_euler[1]-d['headYawRadians'][fi])<1e-6;errors.append({'physicsSample':fi,'maximumSavedCentrelineErrorM':error})
    all_key_error=0.
    for fi in range(1,len(P)):
        key=bpy.data.objects['AFN15_CheckedGuideBank'].data.shape_keys.key_blocks[f'Physics_{fi:04d}'];v=np.empty(P.shape[1]*P.shape[2]*3,dtype=np.float32);key.data.foreach_get('co',v);all_key_error=max(all_key_error,float(np.max(np.abs(v.reshape(P.shape[1:])-P[fi]))));assert key.relative_key.name=='Basis'
    assert all_key_error<.000001
    key_action=obj.data.shape_keys.animation_data.action;curves=[c for l in key_action.layers for s in l.strips for b in s.channelbags for c in b.fcurves];assert len(curves)==len(P)-1
    for curve in curves:
        assert len(curve.keyframe_points)==3 and [p.co[1] for p in curve.keyframe_points]==[0.,1.,0.] and all(p.interpolation=='LINEAR' for p in curve.keyframe_points)
    assert flow.solid.geom(bpy.data.objects['AFN_R0008_Body'])==original_geometry and not bpy.data.libraries;obj.modifiers[0].show_viewport=True
    (E/f'c-{case}-blender-review.json').write_text(json.dumps({'case':case,'sourceCacheSha256':result['outputSha256'],'output':str(dest),'outputSha256':flow.route.sha(dest),'fileBytes':dest.stat().st_size,'guides':count,'physicsSamplesBaked':len(P),'fps':240,'interpolation':'Linear world-space centreline shape-key intervals; head local-Y keys linear between matching samples.','savedReopenChecks':errors,'allSavedShapeKeyCoordinateMaximumErrorM':all_key_error,'allShapeKeysAndLinearWeightsChecked':True,'bodySourceGeometryUnchanged':True,'nativeFullHairHidden':True,'childFibresAnimated':0,'displayRadiusMatchesCheckedRadiusM':.00006,'continuousBodyProof':f'c-{case}-continuous-body-verification.json','motionAcceptance':'BODY_ONLY_WIND_GUIDE_SCOPE_PASS_NOT_FULL_HAIR_OR_CHARACTER','wallSeconds':time.time()-started},indent=2)+'\n');print('AFN15_MOTION_REVIEW_DONE='+case,flush=True)

if __name__=='__main__':main()
