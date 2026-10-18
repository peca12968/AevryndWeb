"""Actual matched full-head renders and clearly scoped oral diagnostic motion."""
import bpy, importlib.util, json, sys, math
from pathlib import Path
from mathutils import Vector
spec=importlib.util.spec_from_file_location('verify24',Path(__file__).with_name('verify-female-next-r0024-oral-layers.py'))
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);b=v.b

def main():
    report=json.loads((b.E/'b-build-verification.json').read_text(encoding='utf8'))
    bpy.ops.wm.open_mainfile(filepath=report['output']);s=bpy.context.scene;c=s.camera
    b.solid.stage.set_pose(bpy.data.objects['AFN_R0005_Rig'],'neutral')
    s.render.threads_mode='FIXED';s.render.threads=4;s.render.resolution_percentage=100
    if s.render.engine=='CYCLES': s.cycles.samples=32;s.cycles.use_denoising=True
    oral=[o for o in bpy.data.objects if o.name.startswith('AFN24_') and o.type=='MESH']
    head=1.5624730926266572*.91;target=(0.,-.02,head);rows=[]
    def render(label,view='face'):
        if view=='mouth': location=(0.,-.38,1.399);aim=(0.,-.13,1.400);size=(1000,500)
        elif view=='layers':location=(.11,-.32,1.405);aim=(0.,-.10,1.399);size=(900,700)
        elif view=='oblique':location=(.46,-.82,head+.04);aim=target;size=(800,800)
        else:location=(0.,-.90,head+.015);aim=target;size=(800,800)
        c.location=location;c.rotation_euler=(Vector(aim)-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=100
        s.render.resolution_x,s.render.resolution_y=size
        path=b.E/(label+'-'+view+'.png');s.render.filepath=str(path);bpy.ops.render.render(write_still=True)
        rows.append({'label':label,'view':view,'path':str(path),'cameraMatrix':[x for row in c.matrix_world for x in row],'size':list(size),'lens':100,'engine':s.render.engine,'viewTransform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma,'lights':[(o.name,list(o.location),list(o.rotation_euler),o.data.energy) for o in bpy.data.objects if o.type=='LIGHT']})
        b.save('b-renders.json',{'source':report['output'],'sourceSha256':report['outputSha256'],'renders':rows,'baselineDefinition':'Same current r23 rest plus identical small open field, with only new oral meshes hidden. Not a previous accepted mouth animation.','limits':'B has contact failures; visual review only, no motion or complete head acceptance.'})
    for w,state in ((0.,'neutral'),(.2,'open')):
        v.weight(w)
        for visible,label in ((False,'before'),(True,'after')):
            for o in oral:o.hide_render=not visible
            for view in ('face','oblique','mouth'):render(label+'-'+state,view)
    # Isolated layer view is diagnostic, not a replacement for whole-head views.
    hidden=[]
    for o in bpy.data.objects:
        if o.type in ('MESH','CURVE','CURVES') and o not in oral and not o.hide_render:
            hidden.append(o);o.hide_render=True
    render('oral-components-open','layers')
    for o in hidden:o.hide_render=False
    master=bpy.data.objects['AFN24_MouthControl'];master.animation_data_clear()
    for frame,w in ((1,0.),(13,.2),(25,0.)):
        master['open']=w;master.keyframe_insert(data_path='["open"]',frame=frame)
    s.frame_start=1;s.frame_end=25;s.render.fps=12
    # Playback remains a failed-contact diagnostic. Never promote it as motion
    # qualification merely because the controller can animate.
    animation=b.S/'aevrynd-female-next-r0024-b-oral-motion-review.blend'
    c.location=(0.,-.90,head+.015);c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=100
    s.render.resolution_x=s.render.resolution_y=800
    s.frame_set(1);bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(animation),compress=True)
    for frame in (1,4,7,10,13,16,19,22,25):
        s.frame_set(frame);bpy.context.view_layer.update();render('motion-%02d'%frame)
    b.save('b-motion-render.json',{'source':str(animation),'sha256':b.sha(animation),'frames':[1,4,7,10,13,16,19,22,25],'fps':12,'status':'DIAGNOSTIC_CONTACT_FAILURES_PRESENT','scope':'Actual rig/body/dental/soft-tissue motion. No continuous contact or anatomical-motion acceptance.'})
    print('R0024_RENDER_DONE',flush=True)
if __name__=='__main__':main()
