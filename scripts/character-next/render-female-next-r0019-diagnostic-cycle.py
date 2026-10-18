"""Standalone animated review; retained as failed whole-blink diagnostics only."""
import bpy,json,hashlib,importlib.util
import numpy as np
from pathlib import Path
from mathutils import Vector
spec=importlib.util.spec_from_file_location('build',Path(__file__).with_name('build-female-next-r0019-native-blink.py'));build=importlib.util.module_from_spec(spec);spec.loader.exec_module(build)
E,S=build.E,build.S
def shape_digest():
    h=hashlib.sha256()
    for o in sorted((x for x in bpy.data.objects if x.type=='MESH' and x.data.shape_keys),key=lambda x:x.name):
        for key in o.data.shape_keys.key_blocks:
            p=np.empty((len(key.data),3),np.float32);key.data.foreach_get('co',p.ravel());h.update(o.name.encode());h.update(key.name.encode());h.update(p.tobytes())
    return h.hexdigest()
def main():
    source=S/'aevrynd-female-next-r0019-c-angular-blink-study.blend';report=json.loads((E/'c-build-verification.json').read_text());assert build.sha(source)==report['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(source));build.set_blink(0.,0.);before=build.prior.controls();shapes=shape_digest();rig=bpy.data.objects['AFN_R0005_Rig'];scene=bpy.context.scene;scene.render.fps=60;scene.frame_start=1;scene.frame_end=121
    for frame,value in ((1,0.),(31,0.),(39,1.),(41,1.),(55,0.),(121,0.)):
        for side in ('L','R'):rig['AFN19_Blink_'+side]=value;rig.keyframe_insert(data_path='["AFN19_Blink_'+side+'"]',frame=frame)
    action=rig.animation_data.action
    curves=[]
    if hasattr(action,'fcurves'):curves=list(action.fcurves)
    else:
        for layer in action.layers:
            for strip in layer.strips:
                bag=strip.channelbag(rig.animation_data.action_slot)
                if bag:curves.extend(bag.fcurves)
    assert len(curves)==2
    for f in curves:
        for k in f.keyframe_points:k.interpolation='LINEAR'
    scene.frame_set(1);assert build.prior.controls()==before and shape_digest()==shapes;scene['aevrynd_release_state']='FAILED_WHOLE_BLINK_DIAGNOSTIC_BROW_CONTACTS_PENDING';scene['aevrynd_motion_scope']='Two-second authored diagnostic, no natural timing or continuous collision acceptance.';bpy.context.preferences.filepaths.save_version=0;dest=S/'aevrynd-female-next-r0019-c-animated-diagnostic.blend';bpy.ops.wm.save_as_mainfile(filepath=str(dest));bpy.ops.wm.open_mainfile(filepath=str(dest));scene=bpy.context.scene;scene.frame_set(1);assert build.prior.controls()==before and shape_digest()==shapes
    rig=bpy.data.objects['AFN_R0005_Rig'];head=1.5624730926266572*.91;c=scene.camera;c.location=(0.,-.90,head+.015);c.rotation_euler=(Vector((0.,-.02,head))-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=100;scene.render.resolution_x=scene.render.resolution_y=700;scene.render.resolution_percentage=100;scene.render.threads_mode='FIXED';scene.render.threads=4;frames=[];folder=E/'diagnostic-frames';folder.mkdir(exist_ok=True)
    for i,frame in enumerate(range(1,122,4)):
        scene.frame_set(frame);path=folder/f'blink-{i:03d}.png';scene.render.filepath=str(path);bpy.ops.render.render(write_still=True);frames.append({'frame':frame,'timeS':(frame-1)/60,'leftWeight':float(rig['AFN19_Blink_L']),'rightWeight':float(rig['AFN19_Blink_R']),'path':str(path)})
    build.save('animated-review-verification.json',{'source':str(source),'sourceSha256':build.sha(source),'output':str(dest),'outputSha256':build.sha(dest),'neutralControlAndAllShapeArraysUnchanged':True,'shapeArrayDigest':shapes,'actionChannels':2,'fps':60,'frameRange':[1,121],'keyInterpolation':'LINEAR','renderedPreviewFps':15,'frames':frames,'fileBytes':dest.stat().st_size,'scope':'Editable two-second diagnostic only. C has known brow/body and brow/brow contact failures. Not accepted whole-blink motion; timing is authored, not measured.'})
    print('R0019_DIAGNOSTIC_CYCLE_RENDERED',flush=True)
if __name__=='__main__':main()
