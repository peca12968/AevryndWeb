"""Reopen without auto-run, render actual 48-frame blink evidence."""
from pathlib import Path
import bpy,json,time,hashlib,numpy as np
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0059-authored-blink'
def main():
    tick=time.time();a=json.loads((E/'a-build-summary.json').read_text());source=Path(a['output']);assert hashlib.sha256(source.read_bytes()).hexdigest()==a['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene
    assert scene.frame_start==1 and scene.frame_end==48 and scene.render.fps==24
    folder=E/'a-blink-frames';folder.mkdir(exist_ok=True);scene.render.resolution_x=scene.render.resolution_y=480;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';rows=[]
    ctrl=bpy.data.objects[a['controlObject']]
    for frame in range(1,49):
        scene.frame_set(frame);bpy.context.view_layer.update();scene.render.filepath=str(folder/f'{frame:04d}.png');bpy.ops.render.render(write_still=True);rows.append({'frame':frame,'left':ctrl['blink_left'],'right':ctrl['blink_right'],'path':scene.render.filepath})
    (E/'a-blink-clip-renders.json').write_text(json.dumps({'source':str(source),'sourceSha256':a['outputSha256'],'reopenedWithoutAutoRun':True,'frames':rows,'fps':24,'resolution':[480,480],'seconds':time.time()-tick,'noContinuousCollisionClaim':True},indent=2)+'\n',encoding='utf8');print('R59_ACTUAL_BLINK_FRAMES',len(rows),time.time()-tick,flush=True)
if __name__=='__main__':main()
