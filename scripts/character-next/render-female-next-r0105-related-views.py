"""Matched oblique and a separately declared second lighting for the UV repair."""
from pathlib import Path
import bpy,json,importlib.util,time
from mathutils import Vector,Matrix
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0105-native-head-skin-chart';S=R/'engine/assets/characters/female-next/source'
sp=importlib.util.spec_from_file_location('r105views',Path(__file__).with_name('build-female-next-r0104-native-head-union.py'));u=importlib.util.module_from_spec(sp);sp.loader.exec_module(u);u.v.E=E
def main():
 tick=time.time();rows={}
 for tag,name in [('baseline','aevrynd-female-next-r0104-b2-native-head-material-repair.blend'),('a','aevrynd-female-next-r0105-a-native-lip-chart.blend')]:
  bpy.ops.wm.open_mainfile(filepath=str(S/name));rows[tag]=[u.v.image(tag+'-related','oblique')];target=Vector(u.m.m.rig.k.b.TARGET);turn=Matrix.Rotation(.6981317008,4,'Z')
  for ob in bpy.context.scene.objects:
   if ob.type=='LIGHT':ob.location=target+turn.to_3x3()@(ob.location-target);ob.rotation_euler=(target-ob.location).to_track_quat('-Z','Y').to_euler()
  rows[tag].append(u.v.image(tag+'-second-lighting','face'));(E/'related-view-controls.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf8',newline='\n')
 for a,b in zip(rows['baseline'],rows['a']):assert {k:v for k,v in a.items() if k!='file'}=={k:v for k,v in b.items() if k!='file'}
 print('R105_RELATED_MATCHED_VIEWS_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
