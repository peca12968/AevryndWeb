import bpy,json,hashlib,array,shutil
from pathlib import Path
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0008-evaluated-sockets';report=json.loads((E/'female-next-r0008-evaluated-sockets.report.json').read_text());archive=E/'run1-before-group-cleanup';archive.mkdir(exist_ok=True)
def geom(m):
 h=hashlib.sha256();a=array.array('f',[0.]*(len(m.vertices)*3));m.vertices.foreach_get('co',a);h.update(a.tobytes());a=array.array('i',[0]*len(m.loops));m.loops.foreach_get('vertex_index',a);h.update(a.tobytes());return h.hexdigest()
results=[]
for v in report['variants']:
 p=Path(v['output']);shutil.copy2(p,archive/p.name);bpy.ops.wm.open_mainfile(filepath=str(p));b=bpy.data.objects['AFN_R0008_Body'];rig=bpy.data.objects['AFN_R0005_Rig'];names={x.name for x in rig.data.bones};used={g.group for vert in b.data.vertices for g in vert.groups};before=geom(b.data);removed=[]
 for g in reversed(list(b.vertex_groups)):
  if g.name not in names:
   if g.index in used:raise RuntimeError('Unexpected weighted non-bone group')
   removed.append(g.name);b.vertex_groups.remove(g)
 assert geom(b.data)==before;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(p));old=v['sha256'];v['sha256']=hashlib.sha256(p.read_bytes()).hexdigest();v['bytes']=p.stat().st_size;results.append({'label':v['label'],'removedUnusedGroups':removed,'geometryHashUnchanged':True,'previousSha256':old,'sha256':v['sha256']})
(E/'group-cleanup.json').write_text(json.dumps(results,indent=2)+'\n');(E/'female-next-r0008-evaluated-sockets.report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps([{'label':x['label'],'removed':len(x['removedUnusedGroups']),'geometryUnchanged':x['geometryHashUnchanged']} for x in results]))
