"""Matched alternate/opposite/full-body views and reopened eye closeup."""
import bpy,importlib.util,json
from pathlib import Path
from mathutils import Vector
spec=importlib.util.spec_from_file_location('g37',Path(__file__).with_name('build-female-next-r0037-eye-margin.py'));g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g);b=g.b;v=g.v;E=g.E
def main():
    proof=g.read('c-saved-verification.json');assert proof['status']=='PASS_REOPENED_ATTACHED_EYE_MARGIN_NEUTRAL_SCOPE';path=Path(proof['source']);assert b.sha(path)==proof['sourceSha256'];rows=[];close=[]
    for label,source in [('before',g.SRC),('c-after',path)]:
        bpy.ops.wm.open_mainfile(filepath=str(source));s=bpy.context.scene;s.render.resolution_x=s.render.resolution_y=800;lights=[(o,list(o.location),list(o.rotation_euler),list(o.scale)) for o in s.objects if o.type=='LIGHT']
        for view in ('opposite-oblique','alternate-oblique','body-face'):
            g.c.camera('body-face' if view=='body-face' else 'oblique')
            if view=='opposite-oblique':cam=s.camera;cam.location.x=-cam.location.x;cam.rotation_euler=(Vector(b.TARGET)-cam.location).to_track_quat('-Z','Y').to_euler()
            if view=='alternate-oblique':
                for o,loc,rot,scale in lights:o.location.x=-o.location.x;o.rotation_euler=(Vector(b.TARGET)-o.location).to_track_quat('-Z','Y').to_euler()
            bpy.context.view_layer.update();s.render.filepath=str(E/f'{label}-{view}.png');bpy.ops.render.render(write_still=True);rows.append({'label':label,'view':view,'camera':b.matrix(s.camera.matrix_world),'resolution':[800,800],'lens':s.camera.data.lens,'stage':v.stage()})
            for o,loc,rot,scale in lights:o.location=loc;o.rotation_euler=rot;o.scale=scale
            bpy.context.view_layer.update()
        close.append(g.closeup(label+'-reopened'))
    for aa,bb in zip(rows[:3],rows[3:]):assert {k:z for k,z in aa.items() if k!='label'}=={k:z for k,z in bb.items() if k!='label'}
    assert close[0]==close[1];g.save('c-supplementary-controls.json',{'matchedAdditionalViews':True,'matchedReopenedEyeCloseups':True,'rows':rows,'closeup':close,'scope':'Actual final complete source model, neutral only. Full-body context is not body/rig/clothing/dynamic acceptance.'});print('R37_REVIEW_RENDER_DONE',flush=True)
if __name__=='__main__':main()
