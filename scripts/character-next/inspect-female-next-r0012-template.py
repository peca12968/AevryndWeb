"""Inspect raw CC0 guide data without evaluating dense geometry-node children."""
import bpy,json
from pathlib import Path
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0012-layered-hair'
REF=R/'sites-engine-journey/assets-source/reference/cc0/makehuman-haireditor/unpacked/hair/haireditor/hair.blend'
with bpy.data.libraries.load(str(REF),link=False) as (f,t):t.objects=['Human','straight_hair_to_shoulder']
rows=[]
for o in t.objects:
    d=o.data;row={'name':o.name,'type':o.type,'matrix':[list(r) for r in o.matrix_world],'dataProperties':[p.identifier for p in d.bl_rna.properties],'attributes':[{'name':a.name,'domain':a.domain,'type':a.data_type,'length':len(a.data)} for a in getattr(d,'attributes',[])],
      'modifiers':[{'name':m.name,'type':m.type,'nodeGroup':m.node_group.name if m.type=='NODES' and m.node_group else None} for m in o.modifiers]}
    if o.type=='MESH':row.update({'vertices':len(d.vertices),'bounds':[[min(v.co[a] for v in d.vertices),max(v.co[a] for v in d.vertices)] for a in range(3)]})
    if o.type=='CURVES':
        row.update({'curves':len(d.curves),'points':len(d.points),'curveProperties':dir(d.curves[0]),'pointProperties':dir(d.points[0]),'firstCurvePoints':[list(p.position) for p in list(d.curves[0].points)[:6]],'bounds':[[min(p.position[a] for p in d.points),max(p.position[a] for p in d.points)] for a in range(3)]})
    rows.append(row)
(E/'template-guide-inspection.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
