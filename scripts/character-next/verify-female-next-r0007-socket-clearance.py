"""Independently check saved socket edits, exact eye preservation, and locked controls."""
import bpy,json,hashlib,array,math
from pathlib import Path
R=Path(r'D:\Download\Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0007-socket-clearance'
def hmesh(m):
 h=hashlib.sha256();a=array.array('f',[0.]*(len(m.vertices)*3));m.vertices.foreach_get('co',a);h.update(a.tobytes());a=array.array('i',[0]*len(m.loops));m.loops.foreach_get('vertex_index',a);h.update(a.tobytes());return h.hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(S/'aevrynd-female-next-r0006-b-balanced-study.blend'));original=[v.co.copy() for v in bpy.data.objects['AFN_R0005_Body'].data.vertices];eye_hashes={o.name:hmesh(o.data) for o in bpy.data.objects if o.name.startswith('AFN6_') and o.type=='MESH'}
d=json.loads((E/'female-next-r0007-socket-clearance.report.json').read_text());results=[]
for variant in d['variants']:
 p=Path(variant['output']);bpy.ops.wm.open_mainfile(filepath=str(p));m=bpy.data.objects['AFN_R0005_Body'].data;records={r['vertex'] for r in variant['edit']['movementRecords']};locked={i for x in variant['edit']['selections'].values() for i in x['lockedVisibleVertices']};conflict=records & locked
 changed={i for i,v in enumerate(m.vertices) if (v.co-original[i]).length>1e-9};eyes={o.name:hmesh(o.data)==eye_hashes[o.name] for o in bpy.data.objects if o.name in eye_hashes};weights=[sum(g.weight for g in v.groups) for v in m.vertices]
 assert changed==records and not conflict and all(eyes.values())
 assert hashlib.sha256(p.read_bytes()).hexdigest()==variant['sha256']
 results.append({'label':variant['label'],'reopen':True,'sha256':variant['sha256'],'fileBytes':p.stat().st_size,'controlVertices':len(m.vertices),'controlPolygons':len(m.polygons),'allQuads':all(len(f.vertices)==4 for f in m.polygons),'bodyChangeMatchesDeclaredRecords':True,'undeclaredBodyChanges':len(changed-records),'lockedControlsChanged':len(conflict),'eyeGeometryUnchanged':eyes,'nonFiniteControlVertices':sum(any(not math.isfinite(x) for x in v.co) for v in m.vertices),'maxWeightSumError':max(abs(w-1) for w in weights),'rigBones':len(bpy.data.objects['AFN_R0005_Rig'].data.bones),'independentMpFbImport':False})
(E/'saved-socket-verification.json').write_text(json.dumps({'revision':'female-next-r0007','results':results,'scope':'source controls and eye geometry; the measured subdivision-limit deviation remains a failed experimental constraint'},indent=2)+'\n');print(json.dumps(results,indent=2))
