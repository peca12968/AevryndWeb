"""Actual native mouth control on the complete woman; no physical acceptance claim."""
from pathlib import Path
import bpy,numpy as np,json,hashlib,time,importlib.util,sys
def module(n,p):
    sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(p));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
m=module('oral74rig','build-female-next-r0069-complete-controls.py')
q=module('oral74render','build-female-next-r0071-hair-scattering.py')
R=m.R;S=m.S;E=R/'Evidence/character-female-next/r0074-oral-controls';D=R/'Reference/character/charmorph-vitruvian-cc0/r0074-oral-controls'
SRC=S/'aevrynd-female-next-r0069-a-complete-controls-study.blend';OUT=S/'aevrynd-female-next-r0074-a-native-mouth-controls-study.blend'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x):(E/n).write_text(json.dumps(x,indent=2)+'\n',encoding='utf8',newline='\n')
def render(tag,view,size=640,samples=16):
    s=bpy.context.scene;m.shade.settings();m.k.b.camera(view);s.camera.data.lens=85;s.render.resolution_x=s.render.resolution_y=size;s.cycles.samples=samples
    s.render.filepath=str(E/(tag+'-'+view+'.png'));ctl={'camera':np.array(s.camera.matrix_world).tolist(),'lights':q.lights(),'resolution':size,'samples':samples,'seed':s.cycles.seed,'exposure':s.view_settings.exposure,'look':s.view_settings.look,'frame':s.frame_current,'jawOpen':bpy.data.objects['AFN74_ORAL_CONTROLS']['jaw_open']}
    bpy.ops.render.render(write_still=True);return ctl
def main():
    tick=time.time();assert not OUT.exists() and sha(SRC)=='f358d3c5a4d00ee6ad94d324612b33bdcf5aa4dde0bb19382d72bc7afabbb667'
    bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;s.frame_set(1);m.shade.settings();m.shade.g.E=E
    rig=bpy.data.objects['AFN69_BODY_CONTROLS'];old=rig.animation_data.action;old.use_fake_user=True;rig.animation_data.action=None
    for bone in rig.pose.bones:assert np.max(np.abs(np.array(bone.matrix_basis)-np.eye(4)))<1e-6
    ctrl=bpy.data.objects.new('AFN74_ORAL_CONTROLS',None);s.collection.objects.link(ctrl);ctrl.empty_display_type='PLAIN_AXES';ctrl.empty_display_size=.04;ctrl.location=(0,-.3,1.42);ctrl['jaw_open']=0.;ctrl.id_properties_ui('jaw_open').update(min=0.,max=1.,description='Native CC0 Mouth_Large_Opened expression; 0 neutral, 1 source opening. Contact/complete anatomy not yet accepted.')
    ctrl['instructions']='Animate jaw_open 0..1. Frames1/13/25/37 demonstrate neutral/open/hold/return. Original head/arm action retained, detached to isolate this mouth operation.'
    z=np.load(D/'Mouth_Large_Opened.npz',allow_pickle=False);delta=np.zeros((37436,3));delta[z['idx']]=z['delta'];assert np.isfinite(delta).all();changes=[]
    for name in m.native_names():
        o=bpy.data.objects[name];ids=np.empty(len(o.data.vertices),'i4');o.data.attributes['AFN60_NativeVertexID'].data.foreach_get('value',ids);dd=delta[ids]
        if not np.any(dd):continue
        base=np.array([p.co[:] for p in o.data.shape_keys.key_blocks[0].data]);key=o.shape_key_add(name='AFN74_CC0_MOUTH_LARGE_OPENED',from_mix=False);key.relative_key=o.data.shape_keys.key_blocks[0];key.data.foreach_set('co',(base+dd).astype('f4').ravel())
        driver=key.driver_add('value').driver;driver.type='AVERAGE';v=driver.variables.new();v.name='jaw';v.type='SINGLE_PROP';v.targets[0].id=ctrl;v.targets[0].data_path='["jaw_open"]'
        changes.append({'object':name,'affectedVertices':int((np.linalg.norm(dd,axis=1)>1e-10).sum()),'maximumNativeDeltaM':float(np.linalg.norm(dd,axis=1).max())})
    for f,value in ((1,0.),(13,1.),(25,1.),(37,0.)):
        ctrl['jaw_open']=value;ctrl.keyframe_insert(data_path='["jaw_open"]',frame=f)
    ctrl.animation_data.action.name='AFN74_NEUTRAL_OPEN_HOLD_RETURN'
    for layer in ctrl.animation_data.action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    for p in fc.keyframe_points:p.interpolation='LINEAR'
    s.frame_start=1;s.frame_end=37;s.render.fps=24;s.frame_set(1);bpy.context.view_layer.update()
    s['AFN74_scope']='Complete native source mouth-opening pilot. No claim that all oral layers, contacts, natural dynamics or engine are accepted.'
    for o in bpy.context.selected_objects:o.select_set(False)
    ctrl.select_set(True);bpy.context.view_layer.objects.active=ctrl;m.k.b.camera('face');s.camera.data.lens=85;bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    save('a-build-summary.json',{'source':str(SRC),'sourceSha256':sha(SRC),'output':str(OUT),'outputSha256':sha(OUT),'outputBytes':OUT.stat().st_size,'nativeSource':str(D/'Mouth_Large_Opened.npz'),'nativeSourceSha256':sha(D/'Mouth_Large_Opened.npz'),'changes':changes,'control':ctrl.name,'property':'jaw_open','range':[0,1],'timeline':[[1,0],[13,1],[25,1],[37,0]],'fps':24,'originalHeadArmActionRetainedDetached':old.name,'topologyMaterialsRadiiWeightsLightingUnchanged':True,'fullOralLayersAndContactAndRuntimeAccepted':False,'secondsBeforePilot':time.time()-tick})
    s.frame_set(13);bpy.context.view_layer.update();save('a-open-pilot-controls.json',[render('a-open','face'),render('a-open','body-face')])
    print('R74_NATIVE_MOUTH_COMPLETE_PILOTS_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
