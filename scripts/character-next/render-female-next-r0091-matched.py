"""Repair stale pre-depsgraph camera records for the required matched art board.
No model edits, new angles, physics expansion or score change.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
from mathutils import Vector
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0091-clump-cross-sections';S=R/'engine/assets/characters/female-next/source'
sp=importlib.util.spec_from_file_location('r91matched',Path(__file__).with_name('render-female-next-r0081-retained-study.py'));v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v);m=v.m
def image(tag,view):
 s=bpy.context.scene;m.rig.shade.settings();m.rig.k.b.camera('oblique' if view=='back' else view);s.camera.data.lens=85;s.render.hair_subdiv=3;s.render.resolution_x=s.render.resolution_y=640;s.cycles.samples=16
 if view=='back':s.camera.location=(0,.91,1.43);s.camera.rotation_euler=(Vector((0,.02,1.405))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.lens=65
 bpy.context.view_layer.update();s.render.filepath=str(E/('matched-'+tag+'-'+view+'.png'));row={'file':s.render.filepath,'view':view,'camera':np.array(s.camera.matrix_world).tolist(),'lensMM':s.camera.data.lens,'lights':m.m.q.lights(),'resolution':640,'samples':16,'seed':s.cycles.seed,'exposure':s.view_settings.exposure,'look':s.view_settings.look,'hairSubdiv':3,'frame':s.frame_current,'jawOpen':bpy.data.objects['AFN74_ORAL_CONTROLS']['jaw_open'],'capture':'Explicit view_layer.update before metadata, then same actual render.'};bpy.ops.render.render(write_still=True);return row
def main():
 tick=time.time();refs=[('baseline',S/'aevrynd-female-next-r0088-b-supported-lid-aperture.blend','72435890a03cab26ff2f3e238060daf2b2cf797f85543d8fd6182583cc1101a7')]
 for tag in ['a','b']:
  d=json.loads((E/(tag+'-build-summary.json')).read_text(encoding='utf8'));refs.append((tag,Path(d['output']),d['outputSha256']))
 rows={}
 for tag,p,digest in refs:
  assert hashlib.sha256(p.read_bytes()).hexdigest()==digest;bpy.ops.wm.open_mainfile(filepath=str(p));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();rows[tag]=[image(tag,view) for view in ['face','back','body-face']];(E/'matched-view-controls.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf8')
  if tag!='baseline':
   for a,b in zip(rows['baseline'],rows[tag]):assert {k:v for k,v in a.items() if k!='file'}=={k:v for k,v in b.items() if k!='file'}
 print('R91_MATCHED_ART_METADATA_AND_RENDER_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
