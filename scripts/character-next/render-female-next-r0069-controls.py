"""Actual complete-character neutral controls, moved poses and animation frames."""
from pathlib import Path
import bpy,json,time,sys,numpy as np,importlib.util
s=importlib.util.spec_from_file_location('render69build',Path(__file__).with_name('build-female-next-r0069-complete-controls.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def main():
    tick=time.time();ref=m.read(m.E/'a-build-summary.json');assert m.sha(m.OUT)==ref['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(m.OUT));scene=bpy.context.scene;m.shade.g.E=m.E;m.shade.settings()
    if '--clip' not in sys.argv:
        scene.frame_set(1);m.save('a-neutral-full-view-controls.json',m.shade.render('a-control',('face','body-face','oblique','profile','back','alternate-oblique')));rows=[]
        for frame,views in ((13,('face',)),(25,('oblique',)),(49,('body-face',))):
            scene.frame_set(frame);rows+=m.shade.render('a-pose'+str(frame),views)
        scene.frame_set(1);m.save('a-posed-view-controls.json',rows);print('R69_FULL_VIEWS',time.time()-tick,flush=True);return
    folder=m.E/'a-motion-frames';folder.mkdir(exist_ok=True);scene.render.resolution_x=scene.render.resolution_y=480;scene.cycles.samples=8;rows=[]
    for frame in range(1,62,4):
        scene.frame_set(frame);bpy.context.view_layer.update();pose=[]
        for view in ('face','body-face'):
            m.k.b.camera(view);scene.camera.data.lens=85;scene.render.filepath=str(folder/f'{frame:04d}-{view}.png');bpy.ops.render.render(write_still=True);pose.append({'view':view,'file':scene.render.filepath,'camera':np.array(scene.camera.matrix_world).tolist()})
        rows.append({'frame':frame,'views':pose,'headQuaternion':list(bpy.data.objects['AFN69_BODY_CONTROLS'].pose.bones['Head'].rotation_quaternion),'leftArmQuaternion':list(bpy.data.objects['AFN69_BODY_CONTROLS'].pose.bones['LeftArm'].rotation_quaternion),'rightArmQuaternion':list(bpy.data.objects['AFN69_BODY_CONTROLS'].pose.bones['RightArm'].rotation_quaternion)})
        print('R69_MOTION_FRAME',frame,time.time()-tick,flush=True)
    scene.frame_set(1);m.save('a-motion-render-controls.json',{'source':str(m.OUT),'sha256':ref['outputSha256'],'resolution':[480,480],'samples':8,'threads':4,'sampleStepSourceFrames':4,'sourceFps':24,'displayFps':6,'rows':rows,'actual3DRenders':True,'noImageGeneratedMotion':True,'naturalHairDynamicsOrContinuousCollisionAccepted':False,'seconds':time.time()-tick})
if __name__=='__main__':main()
