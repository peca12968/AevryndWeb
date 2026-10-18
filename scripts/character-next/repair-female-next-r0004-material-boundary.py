"""Correct the oral material boundary without changing the rejected geometry."""
import bpy, json, hashlib, shutil, array
from pathlib import Path
from mathutils import Vector
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0004-surface-conforming';REPORT=E/'female-next-r0004-perioral.report.json'
def geom_hash(o):
 h=hashlib.sha256();m=o.data
 for k in m.shape_keys.key_blocks:
  a=array.array('f',[0.]*(len(k.data)*3));k.data.foreach_get('co',a);h.update(a.tobytes())
 a=array.array('i',[0]*len(m.loops));m.loops.foreach_get('vertex_index',a);h.update(a.tobytes())
 return h.hexdigest()
def render(o,label,view,pose='neutral'):
 s=bpy.context.scene;s.frame_set(1);k=o.data.shape_keys.key_blocks;k['Aevrynd_MouthOpenTest_R1030'].value=float(pose=='open');k['Aevrynd_SmileTest_R1030'].value=float(pose=='smile');c=s.camera
 V={'face':((0.,-.64,1.47),(0.,-.035,1.445),100,(1200,1000)),'oblique':((.26,-.62,1.48),(0.,-.035,1.445),100,(1200,1000)), 'mouth':((0.,-.43,1.391),(0.,-.115,1.386),135,(1100,720)), 'mouth-oblique':((.105,-.43,1.391),(0.,-.115,1.386),135,(1100,720))}
 c.location,t,c.data.lens,size=V[view];c.rotation_euler=(Vector(t)-c.location).to_track_quat('-Z','Y').to_euler();s.render.resolution_x,s.render.resolution_y=size;s.render.resolution_percentage=100;s.render.filepath=str(E/f'{label}-{view}-{pose}.png');bpy.ops.render.render(write_still=True)
d=json.loads(REPORT.read_text());archive=E/'run1-before-material-correction';archive.mkdir(exist_ok=True);shutil.copy2(REPORT,archive/REPORT.name);results=[]
for v in d['variants']:
 if v['label']=='baseline':continue
 p=Path(v['output']);shutil.copy2(p,archive/p.name);bpy.ops.wm.open_mainfile(filepath=str(p));o=bpy.data.objects['AevryndFemaleNextPerioral_R0004'];before=geom_hash(o)
 first=v['edit']['oldPolygonCount']-v['edit']['removedFaces']+7*v['edit']['boundaryVertices'];changed=[]
 for i in range(first,first+v['edit']['boundaryVertices']):
  if o.data.polygons[i].material_index!=len(o.data.materials)-1:raise RuntimeError('Unexpected material at lip/inner-mouth boundary')
  o.data.polygons[i].material_index=0;changed.append(i)
 assert before==geom_hash(o)
 for view in ('face','oblique','mouth','mouth-oblique'):render(o,v['label'],view)
 for pose in ('open','smile'):render(o,v['label'],'mouth',pose)
 k=o.data.shape_keys.key_blocks;k['Aevrynd_MouthOpenTest_R1030'].value=0.;k['Aevrynd_SmileTest_R1030'].value=0.;bpy.context.view_layer.update();bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(p))
 oldsha=v['sourceSha256'];v['sourceSha256']=hashlib.sha256(p.read_bytes()).hexdigest();results.append({'label':v['label'],'correctedFaceCount':len(changed),'geometryHashBefore':before,'geometryHashAfter':geom_hash(o),'previousFileSha256':oldsha,'correctedFileSha256':v['sourceSha256']})
d['materialBoundaryCorrection']='Oral material begins at the margin-to-inner-wall band; all control geometry, all 35 key coordinates, and polygon connectivity have unchanged hashes. Previous files and report are locally archived.'
REPORT.write_text(json.dumps(d,indent=2)+'\n');(E/'material-boundary-correction.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2))
