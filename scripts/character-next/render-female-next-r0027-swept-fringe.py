"""Matched actual complete-head style review; no lighting camouflage."""
import bpy,importlib.util,json,shutil
from pathlib import Path
from mathutils import Vector
spec=importlib.util.spec_from_file_location('b27',Path(__file__).with_name('build-female-next-r0027-swept-fringe.py'));b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
def main():
    report=json.loads((b.E/(b.LABEL+'-build-verification.json')).read_text(encoding='utf8'));baseline=json.loads((b.R/'Evidence/character-female-next/r0023-neutral-mouth/review-b-renders.json').read_text(encoding='utf8'));assert baseline['sourceSha256']==report['sourceSha256'];rows=[];OUT=b.E/b.LABEL;OUT.mkdir(exist_ok=True)
    for row in baseline['renders']:
        copy=dict(row);dest=OUT/f"before-{row['light']}-{row['view']}.png";shutil.copyfile(row['path'],dest);copy['path']=str(dest);copy['label']='before';rows.append(copy)
    bpy.ops.wm.open_mainfile(filepath=report['output']);b.old.solid.stage.set_pose(bpy.data.objects['AFN_R0005_Rig'],'neutral');s=bpy.context.scene;s.render.threads_mode='FIXED';s.render.threads=4;head=1.5624730926266572*.91;target=(0.,-.02,head)
    for light in ('saved','alternate'):
        if light=='alternate':
            for o in (o for o in bpy.data.objects if o.type=='LIGHT'):o.location.x=-o.location.x;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
        for view,location in [('face',(0.,-.90,head+.015)),('oblique',(.46,-.82,head+.04)),('profile',(.86,-.16,head+.02))]:
            if light=='alternate' and view=='profile':continue
            c=s.camera;c.location=location;c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=100;s.render.resolution_x=s.render.resolution_y=800;s.render.resolution_percentage=100;path=OUT/f'after-{light}-{view}.png';s.render.filepath=str(path);bpy.ops.render.render(write_still=True);rows.append({'label':'after','path':str(path),'view':view,'light':light,'cameraMatrix':[v for row in c.matrix_world for v in row],'lens':100,'resolution':[800,800],'engine':s.render.engine,'viewTransform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma,'lights':[(o.name,list(o.location),list(o.rotation_euler),o.data.energy) for o in bpy.data.objects if o.type=='LIGHT']})
            b.save(b.LABEL+'-renders.json',{'source':report['output'],'sourceSha256':report['outputSha256'],'baselineSource':report['source'],'baselineSourceSha256':report['sourceSha256'],'renders':rows,'scope':'Own static hairstyle geometry only; unchanged face/skin/material/exposure. Self, dynamics and runtime not qualified.'})
    print('R0027_RENDER_DONE',flush=True)
if __name__=='__main__':main()
