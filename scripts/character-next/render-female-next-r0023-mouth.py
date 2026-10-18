"""Matched actual full-head, alternate-light and lip closeup renders."""
import bpy,json,sys,importlib.util
from pathlib import Path
from mathutils import Vector
spec=importlib.util.spec_from_file_location('build',Path(__file__).with_name('build-female-next-r0023-neutral-mouth.py'));b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
spec=importlib.util.spec_from_file_location('views',Path(__file__).with_name('build-female-next-r0021-root-transition.py'));views=importlib.util.module_from_spec(spec);spec.loader.exec_module(views)
def main():
    baseline='--baseline' in sys.argv;prefix='b' if '--b' in sys.argv else 'a';source=b.SRC if baseline else (b.S/'aevrynd-female-next-r0023-b-rest-lip-field-study.blend' if prefix=='b' else b.DST);label='baseline' if baseline else 'candidate-'+prefix
    if '--review' in sys.argv:source=b.S/'aevrynd-female-next-r0023-b-neutral-review.blend';label='review-b';prefix='b'
    if prefix=='a':
        views.E=b.E;views.SRC=b.SRC;views.DST=b.DST;views.render()
    else:
        bpy.ops.wm.open_mainfile(filepath=str(source));b.solid.stage.set_pose(bpy.data.objects['AFN_R0005_Rig'],'neutral');s=bpy.context.scene;s.render.threads_mode='FIXED';s.render.threads=4;head=1.5624730926266572*.91;target=(0.,-.02,head);rows=[]
        for lightMode in ('saved','alternate'):
            if lightMode=='alternate':
                for light in (o for o in bpy.data.objects if o.type=='LIGHT'):light.location.x=-light.location.x;light.rotation_euler=(Vector(target)-light.location).to_track_quat('-Z','Y').to_euler()
            for view,location in [('face',(0.,-.90,head+.015)),('oblique',(.46,-.82,head+.04)),('profile',(.86,-.16,head+.02))]:
                if lightMode=='alternate' and view=='profile':continue
                c=s.camera;c.location=location;c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=100;s.render.resolution_x=s.render.resolution_y=800;s.render.resolution_percentage=100;path=b.E/f'{label}-{lightMode}-{view}.png';s.render.filepath=str(path);bpy.ops.render.render(write_still=True);rows.append({'path':str(path),'view':view,'light':lightMode,'cameraMatrix':[v for row in c.matrix_world for v in row],'lens':100,'resolution':[800,800],'engine':s.render.engine,'viewTransform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma,'lights':[(o.name,list(o.location),list(o.rotation_euler),o.data.energy) for o in bpy.data.objects if o.type=='LIGHT']})
        b.save(label+'-renders.json',{'source':str(source),'sourceSha256':b.sha(source),'renders':rows})
    bpy.ops.wm.open_mainfile(filepath=str(source));b.solid.stage.set_pose(bpy.data.objects['AFN_R0005_Rig'],'neutral');s=bpy.context.scene;c=s.camera;c.location=(0.,-.38,1.399);c.rotation_euler=(Vector((0.,-.13,1.400))-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=100;s.render.resolution_x=1400;s.render.resolution_y=700;s.render.resolution_percentage=100;s.render.threads_mode='FIXED';s.render.threads=4;path=b.E/f'{label}-mouth-closeup.png';s.render.filepath=str(path);bpy.ops.render.render(write_still=True);b.save(label+'-mouth-closeup-render.json',{'source':str(source),'sourceSha256':b.sha(source),'path':str(path),'cameraMatrix':[v for row in c.matrix_world for v in row],'lens':100,'resolution':[1400,700],'engine':s.render.engine,'viewTransform':s.view_settings.view_transform,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma,'lights':[(o.name,list(o.location),list(o.rotation_euler),o.data.energy) for o in bpy.data.objects if o.type=='LIGHT']});print('R0023_RENDER_DONE',label,flush=True)
if __name__=='__main__':main()
