"""Actual full-head and dental assembly comparisons plus scoped playback."""
import bpy,importlib.util,json,shutil
from pathlib import Path
from mathutils import Vector
spec=importlib.util.spec_from_file_location('verify25',Path(__file__).with_name('verify-female-next-r0025-dental-contact.py'));v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);b=v.b
def main():
    report=json.loads((b.E/'a-build-verification.json').read_text(encoding='utf8'));baseline=json.loads((b.prior.E/'b-renders.json').read_text(encoding='utf8'));assert report['sourceSha256']==baseline['sourceSha256'];rows=[]
    for state in ('neutral','open'):
        for view in ('face','oblique','mouth'):
            row=next(r for r in baseline['renders'] if r['label']=='after-'+state and r['view']==view);dest=b.E/f'before-{state}-{view}.png';shutil.copyfile(row['path'],dest);copy=dict(row);copy.update({'label':'before-'+state,'path':str(dest),'inheritedExactSource':True});rows.append(copy)
    bpy.ops.wm.open_mainfile(filepath=report['output']);s=bpy.context.scene;c=s.camera;s.render.threads_mode='FIXED';s.render.threads=4;s.render.resolution_percentage=100
    if s.render.engine=='CYCLES':s.cycles.samples=32;s.cycles.use_denoising=True
    head=1.5624730926266572*.91;target=(0.,-.02,head)
    def render(label,view='face'):
        if view=='mouth':location=(0.,-.38,1.399);aim=(0.,-.13,1.400);size=(1000,500)
        elif view=='layers':location=(.11,-.32,1.405);aim=(0.,-.10,1.399);size=(900,700)
        elif view=='oblique':location=(.46,-.82,head+.04);aim=target;size=(800,800)
        else:location=(0.,-.90,head+.015);aim=target;size=(800,800)
        c.location=location;c.rotation_euler=(Vector(aim)-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=100;s.render.resolution_x,s.render.resolution_y=size
        path=b.E/(label+'-'+view+'.png');s.render.filepath=str(path);bpy.ops.render.render(write_still=True)
        rows.append({'label':label,'view':view,'path':str(path),'cameraMatrix':[x for row in c.matrix_world for x in row],'size':list(size),'lens':100,'engine':s.render.engine,'viewTransform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma,'lights':[(o.name,list(o.location),list(o.rotation_euler),o.data.energy) for o in bpy.data.objects if o.type=='LIGHT']})
        b.save('a-renders.json',{'source':report['output'],'sourceSha256':report['outputSha256'],'baselineSource':report['source'],'baselineSourceSha256':report['sourceSha256'],'renders':rows,'scope':'Only crown/contact geometry differs. Unresolved gingival/tongue contacts remain.'})
    for w,state in ((0.,'neutral'),(.2,'open')):
        v.weight(w)
        for view in ('face','oblique','mouth'):render('after-'+state,view)
    hidden=[]
    for o in bpy.data.objects:
        if o.type in ('MESH','CURVE','CURVES') and not o.name.startswith(('AFN24_','AFN25_')) and not o.hide_render:hidden.append(o);o.hide_render=True
    render('after-oral-open','layers')
    for o in hidden:o.hide_render=False
    master=bpy.data.objects['AFN24_MouthControl'];master.animation_data_clear()
    for frame,w in ((1,0.),(13,.2),(25,0.)):master['open']=w;master.keyframe_insert(data_path='["open"]',frame=frame)
    s.frame_start=1;s.frame_end=25;s.render.fps=12;c.location=(0.,-.90,head+.015);c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=100;s.render.resolution_x=s.render.resolution_y=800;s.frame_set(1)
    animation=b.S/'aevrynd-female-next-r0025-a-dental-motion-review.blend';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(animation),compress=True)
    for frame in (1,4,7,10,13,16,19,22,25):s.frame_set(frame);bpy.context.view_layer.update();render('motion-%02d'%frame)
    b.save('a-motion-render.json',{'source':str(animation),'sha256':b.sha(animation),'frames':[1,4,7,10,13,16,19,22,25],'fps':12,'status':'DENTAL_REPAIR_REVIEW_OTHER_ORAL_CONTACTS_UNRESOLVED','scope':'Actual model playback; dental pair sweep is separately qualified only for the stated range. Full mouth/body/tissue continuous contact remains unqualified.'})
    print('R0025_RENDER_DONE',flush=True)
if __name__=='__main__':main()
