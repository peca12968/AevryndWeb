"""Bounded complete-character operation clip and defect views; no beautification."""
from pathlib import Path
import bpy,numpy as np,json,time,importlib.util
from mathutils import Vector
sp=importlib.util.spec_from_file_location('oral74render',Path(__file__).with_name('build-female-next-r0074-oral-controls.py'));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
E=m.E
def main():
    tick=time.time();ref=json.loads((E/'c-build-summary.json').read_text());check=json.loads((E/'c-independent-readback.json').read_text());assert check['sha256']==ref['outputSha256'] and m.sha(Path(ref['output']))==ref['outputSha256'];bpy.ops.wm.open_mainfile(filepath=ref['output']);s=bpy.context.scene;m.m.shade.g.E=E;s.frame_set(13);bpy.context.view_layer.update();rows=[]
    for view in ('profile','alternate-oblique'):
        saved=[(o,o.matrix_world.copy()) for o in s.objects if o.type=='LIGHT'];m.m.shade.settings();m.m.k.b.camera('oblique' if view=='alternate-oblique' else view);s.camera.data.lens=85
        if view=='alternate-oblique':
            for o,_ in saved:o.location.x=-o.location.x;o.rotation_euler=(Vector(m.m.k.b.TARGET)-o.location).to_track_quat('-Z','Y').to_euler()
        s.render.resolution_x=s.render.resolution_y=640;s.cycles.samples=16;s.render.filepath=str(E/('c-operation-'+view+'.png'));ctl={'view':view,'frame':13,'camera':np.array(s.camera.matrix_world).tolist(),'lights':m.q.lights(),'resolution':640,'samples':16,'exposure':s.view_settings.exposure,'look':s.view_settings.look};bpy.ops.render.render(write_still=True);rows.append(ctl)
        for o,matrix in saved:o.matrix_world=matrix
    m.save('c-angle-light-controls.json',rows)
    folder=E/'c-motion-frames';folder.mkdir(exist_ok=True);motion=[]
    for f in (1,4,7,10,13,17,21,25,28,31,34,37):
        s.frame_set(f);bpy.context.view_layer.update();ctl=m.render('c-motion-frames/'+str(f).zfill(4),'face',384,8);ctl['file']=str(folder/(str(f).zfill(4)+'-face.png'));motion.append(ctl);m.save('c-motion-controls.json',motion)
    s.frame_set(13);bpy.context.view_layer.update();keep={'AFN74_UPPER_TEETH_RIGID','AFN74_LOWER_TEETH_RIGID','AFN74_LOWER_GUM_REGION','AFN74_TONGUE_REGION'}
    for o in s.objects:
        if o.type in ('MESH','CURVES') and o.name not in keep:o.hide_render=True
    m.m.shade.settings();c=s.camera;c.location=(0,-.34,1.445);c.rotation_euler=(Vector((0,-.105,1.390))-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=85;s.render.resolution_x=s.render.resolution_y=640;s.cycles.samples=16;s.render.filepath=str(E/'c-isolated-dental-structure.png');bpy.ops.render.render(write_still=True)
    print('R74_OPERATION_EVIDENCE_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
