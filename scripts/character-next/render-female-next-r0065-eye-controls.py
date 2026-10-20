"""Equal-condition source controls or actual saved-native blink preview."""
import bpy,numpy as np,json,time,importlib.util,sys
from pathlib import Path
s=importlib.util.spec_from_file_location('eye65rendercontrols',Path(__file__).with_name('build-female-next-r0065-inner-eye.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);d=m.m;E=m.E
def main():
    tick=time.time();d.g.E=E;d.shade.g.E=E
    if '--baseline' in sys.argv:
        assert d.g.sha(m.SRC)==d.g.SOURCE_SHA;bpy.ops.wm.open_mainfile(filepath=str(m.SRC));d.shade.settings();d.save('baseline-extra-controls.json',d.shade.render('baseline-eye',('oblique','profile','alternate-oblique')));return
    ref=json.loads((E/'a-build-summary.json').read_text());assert d.g.sha(m.OUT)==ref['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(m.OUT));scene=bpy.context.scene;assert scene.frame_start==1 and scene.frame_end==48;d.shade.settings();d.k.b.camera('face');scene.render.resolution_x=scene.render.resolution_y=480;scene.cycles.samples=8;folder=E/'a-blink-frames';folder.mkdir(exist_ok=True);ctrl=bpy.data.objects['AFN59_FACE_CONTROLS'];old=json.loads((E.parent/'r0060-ocular-assembly/b-blink-clip-renders.json').read_text());rows=[]
    for frame in range(1,49):
        scene.frame_set(frame);bpy.context.view_layer.update();expected=old['frames'][frame-1];assert abs(ctrl['blink_left']-expected['left'])<1e-6 and abs(ctrl['blink_right']-expected['right'])<1e-6;scene.render.filepath=str(folder/f'{frame:04d}.png');bpy.ops.render.render(write_still=True);rows.append({'frame':frame,'left':ctrl['blink_left'],'right':ctrl['blink_right'],'file':scene.render.filepath})
        if frame%8==0:print('R65_NATIVE_BLINK_FRAME',frame,time.time()-tick,flush=True)
    d.save('a-blink-render-controls.json',{'source':str(m.OUT),'sha256':d.g.sha(m.OUT),'actualRenderedFrames':48,'fps':24,'resolution':[480,480],'cyclesSamples':8,'frames':rows,'originalNativeBlinkControlSequencePreserved':True,'readbackAllowance':1e-6,'newAnimationAuthored':False,'scope':'Actual saved A model/materials rendered through the existing native r59/r60 blink action. Offline visual preview only, not continuous contact or Aevrynd performance proof.','seconds':time.time()-tick})
if __name__=='__main__':main()
