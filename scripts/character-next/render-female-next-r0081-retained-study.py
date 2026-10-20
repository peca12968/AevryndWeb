"""Small visual record of retained unaccepted research, not expanded acceptance.
Same light/camera pairs plus low-resolution rigid-follow demonstration.
Known neutral body intersections and numeric target failure remain failures.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
from mathutils import Vector
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0081-editable-curly-groom'
sp=importlib.util.spec_from_file_location('visual81',Path(__file__).with_name('build-female-next-r0081-editable-curly.py'));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):(E/n).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def image(tag,view):
 s=bpy.context.scene;m.rig.shade.settings();m.rig.k.b.camera('oblique' if view in ('back','alternate-oblique') else view);s.camera.data.lens=85;s.render.hair_subdiv=3;s.render.resolution_x=s.render.resolution_y=640;s.cycles.samples=16;lights=[(o,o.matrix_world.copy()) for o in s.objects if o.type=='LIGHT']
 if view=='back':s.camera.location=(0,.91,1.43);s.camera.rotation_euler=(Vector((0,.02,1.405))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.lens=65
 if view=='alternate-oblique':
  for o,mat in lights:o.location.x=-o.location.x;o.rotation_euler=(Vector(m.rig.k.b.TARGET)-o.location).to_track_quat('-Z','Y').to_euler()
 s.render.filepath=str(E/(tag+'-'+view+'.png'));row={'file':s.render.filepath,'view':view,'camera':np.array(s.camera.matrix_world).tolist(),'lights':m.m.q.lights(),'resolution':640,'samples':16,'seed':s.cycles.seed,'exposure':s.view_settings.exposure,'look':s.view_settings.look,'hairSubdiv':3,'frame':s.frame_current,'jawOpen':bpy.data.objects['AFN74_ORAL_CONTROLS']['jaw_open']};bpy.ops.render.render(write_still=True)
 for o,mat in lights:o.matrix_world=mat
 bpy.context.view_layer.update();return row
def main():
 tick=time.time();ref=m.q.read(E/'b-build-summary.json');rows={};check=m.q.read(E/'b-independent-readback.json');assert not check['bodyFrameTargetPassed'] and check['contactStatus']=='FAIL_FREE_SHAFT_BODY_INTERIOR_SAMPLE_WITNESSES'
 for tag,path,digest in [('baseline-r76',ref['completeBaselineSource'],ref['completeBaselineSha256']),('b-curly',ref['output'],ref['outputSha256'])]:
  assert sha(Path(path))==digest;bpy.ops.wm.open_mainfile(filepath=path);bpy.context.scene.frame_set(1);rows[tag]=[image(tag,view) for view in ('oblique','back','alternate-oblique')];save('retained-study-view-controls.json',rows)
 s=bpy.context.scene;m.rig.shade.settings();m.rig.k.b.camera('face');s.camera.data.lens=85;s.render.hair_subdiv=3;s.render.resolution_x=s.render.resolution_y=320;s.cycles.samples=4;movie=[]
 for i,deg in enumerate([0,-8,-16,-20,-12,0,12,20,16,8,0]):
  m.rig.axis_pose(bpy.data.objects['AFN69_BODY_CONTROLS'],'Head',(0,0,1),deg);bpy.context.view_layer.update();s.render.filepath=str(E/('rigid-follow-'+str(i).zfill(2)+'.png'));bpy.ops.render.render(write_still=True);movie.append({'file':s.render.filepath,'headYawDegrees':deg})
 save('rigid-follow-clip-frames.json',{'source':ref['output'],'sha256':ref['outputSha256'],'frames':movie,'meaning':'Actual sequential pose evaluation and renders, not image warping. Rigid root-frame following only, no hair inertia/bending/collision response. Original independent2micrometre frame target failed; known neutral body intersections remain. Not continuous contact or natural-motion verification.','resolution':320,'samples':4,'seconds':time.time()-tick});print('R81_RETAINED_VISUAL_RECORD_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
