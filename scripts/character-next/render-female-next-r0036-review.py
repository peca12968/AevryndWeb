"""Supplementary matched opposite-side, alternate-light and full-body renders."""
import bpy,importlib.util,json
from pathlib import Path
from mathutils import Vector
spec=importlib.util.spec_from_file_location('c36',Path(__file__).with_name('build-female-next-r0036-brows.py'));c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c);b=c.b;v=c.v;E=c.E
def main():
    proof=c.read('b-saved-verification.json');assert proof['status']=='PASS_REOPENED_NEUTRAL_BROW_SCOPE';path=Path(proof['source']);assert b.sha(path)==proof['sourceSha256'];rows=[]
    for label,source in [('before',c.SRC),('b-after',path)]:
        bpy.ops.wm.open_mainfile(filepath=str(source));s=bpy.context.scene;s.render.resolution_x=s.render.resolution_y=800
        lights=[(o,list(o.location),list(o.rotation_euler),list(o.scale)) for o in s.objects if o.type=='LIGHT']
        for view in ('opposite-oblique','alternate-oblique','body-face'):
            if view=='body-face':c.camera(view)
            else:c.camera('oblique')
            if view=='opposite-oblique':cam=s.camera;cam.location.x=-cam.location.x;cam.rotation_euler=(Vector(b.TARGET)-cam.location).to_track_quat('-Z','Y').to_euler()
            if view=='alternate-oblique':
                for o,loc,rot,scale in lights:o.location.x=-o.location.x;o.rotation_euler=(Vector(b.TARGET)-o.location).to_track_quat('-Z','Y').to_euler()
            bpy.context.view_layer.update();s.render.filepath=str(E/f'{label}-{view}.png');bpy.ops.render.render(write_still=True);rows.append({'label':label,'view':view,'camera':b.matrix(s.camera.matrix_world),'lens':s.camera.data.lens,'resolution':[800,800],'stage':v.stage()})
            for o,loc,rot,scale in lights:o.location=loc;o.rotation_euler=rot;o.scale=scale
            bpy.context.view_layer.update()
    assert len(rows)==6
    for aa,bb in zip(rows[:3],rows[3:]):assert {k:w for k,w in aa.items() if k!='label'}=={k:w for k,w in bb.items() if k!='label'}
    c.save('b-supplementary-render-controls.json',{'matchedConditions':True,'rows':rows,'scope':'Actual complete source models; full-body rendering is context only, not body/rig/clothing acceptance.'});print('R36_SUPPLEMENTARY_DONE',flush=True)
if __name__=='__main__':main()
