"""Same-character native blink with editable controls and curve following.

Original CURVES/radii/topology remain intact. Hidden point meshes carry native
sampled shape keys; Geometry Nodes samples their positions by stable point ID.
No frame handler, auto-run script, addon or fitted lid construction is needed.
"""
from pathlib import Path
import bpy,numpy as np,json,time,importlib.util
sp=importlib.util.spec_from_file_location('base59',Path(__file__).with_name('build-female-next-r0057-coherent-preview.py'))
k=importlib.util.module_from_spec(sp);sp.loader.exec_module(k)
b=k.b;f=k.f;E=b.R/'Evidence/character-female-next/r0059-authored-blink';PREV=E.parent/'r0057-coherent-foundation';OUT=b.S/'aevrynd-female-next-r0059-a-authored-blink-study.blend'
BODY='AFN57_CC0_COHERENT_FEMALE_BODY';CTRL='AFN59_FACE_CONTROLS'
def save(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def driver(key,ctrl,side,expression):
    fc=key.driver_add('value');d=fc.driver;d.type='SCRIPTED';var=d.variables.new();var.name='v';var.type='SINGLE_PROP';var.targets[0].id=ctrl;var.targets[0].data_path='["blink_'+side.lower()+'"]';d.expression=expression;assert d.is_simple_expression
def flat(o):
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());q=np.empty(len(ev.data.position_data)*3,dtype='f4');ev.data.position_data.foreach_get('vector',q);return q.reshape(-1,3)
def set_frame(frame):bpy.context.scene.frame_set(frame);bpy.context.view_layer.update()
def make_facial_control(o,label,raw,ctrl):
    base=raw[label+'_neutral'];counts=raw[label+'Counts'];mesh=bpy.data.meshes.new('AFN59_'+label.upper()+'_NATIVE_POINT_POSES');mesh.from_pydata(base.tolist(),[],[]);mesh.update();ob=bpy.data.objects.new(mesh.name,mesh);bpy.context.scene.collection.objects.link(ob);ob.matrix_world=o.matrix_world.copy();ob.hide_render=True;ob.hide_set(True);ob['scope']='Native sampled facial-hair point coordinates; no display/collision proxy. Geometry Nodes drives actual original curves by stable point IDs.'
    ob.shape_key_add(name='Basis')
    for side in ('Left','Right'):
        for value in (25,50,75,100):
            key=ob.shape_key_add(name=f'{side}_{value:03d}');key.data.foreach_set('co',raw[f'{label}_{side.lower()}_{value:03d}'].ravel());driver(key,ctrl,side,f'max(0,1-abs(v*4-{value/25:g}))')
    ng=bpy.data.node_groups.new('AFN59_'+label.upper()+'_FOLLOW_NATIVE_POINTS','GeometryNodeTree');ng.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');ng.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
    inp=ng.nodes.new('NodeGroupInput');out=ng.nodes.new('NodeGroupOutput');info=ng.nodes.new('GeometryNodeObjectInfo');info.transform_space='RELATIVE';info.inputs['Object'].default_value=ob;info.inputs['As Instance'].default_value=False
    sample=ng.nodes.new('GeometryNodeSampleIndex');sample.data_type='FLOAT_VECTOR';sample.domain='POINT';sample.clamp=False;position=ng.nodes.new('GeometryNodeInputPosition');index=ng.nodes.new('GeometryNodeInputIndex');setpos=ng.nodes.new('GeometryNodeSetPosition')
    ng.links.new(inp.outputs['Geometry'],setpos.inputs['Geometry']);ng.links.new(info.outputs['Geometry'],sample.inputs['Geometry']);ng.links.new(position.outputs['Position'],sample.inputs['Value']);ng.links.new(index.outputs['Index'],sample.inputs['Index']);ng.links.new(sample.outputs['Value'],setpos.inputs['Position']);ng.links.new(setpos.outputs['Geometry'],out.inputs['Geometry'])
    mod=o.modifiers.new('AFN59_NATIVE_BLINK_FOLLOW','NODES');mod.node_group=ng;o['AFN59_animation']='Same-source native sampled point poses, piecewise linear between quarter steps; original curve counts/radii/material retained. Continuous collision not accepted.'
    return ob
def main():
    tick=time.time();ref=json.loads((PREV/'d-build-summary.json').read_text());source=Path(ref['output']);assert b.sha(source)==ref['outputSha256'];raw=np.load(E/'native-blink-pose-data.npz');bpy.ops.wm.open_mainfile(filepath=str(source));stage=f.v.stage();body=bpy.data.objects[BODY]
    ctrl=bpy.data.objects.new(CTRL,None);ctrl.empty_display_type='PLAIN_AXES';ctrl.empty_display_size=.025;ctrl.location=(.20,0,1.5);bpy.context.scene.collection.objects.link(ctrl)
    for side in ('Left','Right'):
        prop='blink_'+side.lower();ctrl[prop]=0.;ctrl.id_properties_ui(prop).update(min=0.,max=1.,soft_min=0.,soft_max=1.,description='Native authored '+side.lower()+' eyelid closure, 0=open 1=closed; facial-hair positions follow sampled source data.')
        key=body.shape_key_add(name='AFN59_Blink_'+side);key.data.foreach_set('co',raw['key'+side].ravel());driver(key,ctrl,side,'v')
    controls=[]
    for label in ('lashes','brows'):controls.append(make_facial_control(bpy.data.objects['AFN57_NATIVE_'+label.upper()],label,raw,ctrl))
    # Linear property animation avoids overshooting the accepted control range.
    timeline=[(1,0.,0.),(15,0.,0.),(18,.5,.5),(21,1.,1.),(24,.5,.5),(27,0.,0.),(34,0.,0.),(37,1.,0.),(40,0.,0.),(48,0.,0.)]
    for frame,left,right in timeline:
        ctrl['blink_left']=left;ctrl['blink_right']=right
        for prop in ('blink_left','blink_right'):ctrl.keyframe_insert(data_path='["'+prop+'"]',frame=frame)
    action=ctrl.animation_data.action
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    for point in fc.keyframe_points:point.interpolation='LINEAR'
    scene=bpy.context.scene;scene.frame_start=1;scene.frame_end=48;scene.render.fps=24
    readback=[]
    for frame,pose in ((1,'neutral'),(18,'both_050'),(21,'both_100'),(37,'left_100')):
        set_frame(frame);entry={'frame':frame,'pose':pose,'controls':[ctrl['blink_left'],ctrl['blink_right']]}
        for label in ('lashes','brows'):
            points=flat(bpy.data.objects['AFN57_NATIVE_'+label.upper()]);error=float(np.linalg.norm(points-raw[label+'_'+pose],axis=1).max());assert error<1e-6,(label,pose,error);entry[label+'MaximumNativePointErrorM']=error
        readback.append(entry)
    set_frame(1);assert f.v.stage()==stage
    for o in bpy.context.selected_objects:o.select_set(False)
    ctrl.select_set(True);bpy.context.view_layer.objects.active=ctrl;b.camera('face');scene.camera.data.lens=85
    scene['AFN59_status']='AUTHORED_BLINK_NATIVE_FOLLOW_STUDY_NOT_ACCEPTED';ctrl['instructions']='Play frames1-48 at24fps: bilateral blink then left wink. Select this object for blink_left/right. Original body/UV/neutral source retained; no full character/contacts/runtime acceptance.'
    bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    save('a-build-summary.json',{'revision':'female-next-r0059','source':str(source),'sourceSha256':b.sha(source),'output':str(OUT),'outputSha256':b.sha(OUT),'mainHypothesis':'Same-topology authored eyelid morphs with native-source lash/brow following can produce an actual editable blink without procedural lid reconstruction.','controlObject':CTRL,'properties':['blink_left','blink_right'],'frameRange':[1,48],'fps':24,'timeline':timeline,'nativeFacialHairSampleReadback':readback,'bodyOriginalUVAndMaterialsRetained':True,'nativeCurveTopologyRadiiMaterialsRetained':True,'handlersAutoRunAddonsRequired':False,'skinLightExposureUnchanged':True,'blinkDataApproximation':'Facial hair exact quarter-step native poses, measured small bilateral additivity error; piecewise linear point interpolation between them. Not exact native rotation or continuous collision proof.','acceptance':'PENDING_ACTUAL_APPEARANCE_AND_CONTACT_REVIEW','hairRigClothesRuntime':'STILL_UNACCEPTED','seconds':time.time()-tick})
    for frame,label in ((1,'a-neutral'),(18,'a-half'),(21,'a-closed')):
        set_frame(frame);f.E=E;f.render(label,('face','profile','oblique') if frame!=18 else ('face','profile'))
        if frame!=18:k.k.k.k.k.a.i.ch.review.extras(label,E)
    set_frame(37);f.E=E;f.render('a-left-wink',('face',));set_frame(1)
    print('R59_AUTHORED_BLINK_PREVIEW',str(OUT),time.time()-tick,flush=True)
if __name__=='__main__':main()
