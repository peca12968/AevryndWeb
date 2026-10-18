"""Inspect topology and CC0 native closure deltas before any new shape candidate."""
import bpy,json,hashlib,gzip
import numpy as np
from pathlib import Path
R=Path(r'D:\Download\Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0019-blink';E.mkdir(parents=True,exist_ok=True)
SRC=S/'aevrynd-female-next-r0018-c-triangulated-brows-study.blend';ADDON=Path(r'C:\Users\USER\AppData\Roaming\Blender Foundation\Blender\5.2\extensions\user_default\mpfb')
def main():
    m=json.loads((S.parent/'female-next.asset.json').read_text());assert m['workingReviewSource']=='source/'+SRC.name and hashlib.sha256(SRC.read_bytes()).hexdigest()==m['workingReviewSha256'];bpy.ops.wm.open_mainfile(filepath=str(SRC))
    objects=[]
    for name in ('AFN_R0008_Body','AFN_R0005_EditableNativeCC0','AFN_R0005_Rig'):
        o=bpy.data.objects[name];row={'name':name,'type':o.type,'matrix':list(v for r in o.matrix_world for v in r)}
        if o.type=='MESH':
            row.update({'vertices':len(o.data.vertices),'polygons':len(o.data.polygons),'modifiers':[{'name':v.name,'type':v.type,'viewport':v.show_viewport,'render':v.show_render,'levels':getattr(v,'levels',None),'vertexGroup':getattr(v,'vertex_group',None)} for v in o.modifiers],'shapeKeys':[(k.name,k.value) for k in o.data.shape_keys.key_blocks] if o.data.shape_keys else [],'eyeRelatedGroups':[g.name for g in o.vertex_groups if any(k in g.name.lower() for k in ('eye','lid','face'))]})
        else:row['bones']=[b.name for b in o.data.bones]
        objects.append(row)
    targets=[]
    for race in ('african','asian','caucasian'):
        for side in ('left','right'):
            p=ADDON/f'data/targets/expression/units/{race}/eye-{side}-closure.target.gz';raw=gzip.decompress(p.read_bytes()).decode();rows=[line.split() for line in raw.splitlines() if line and not line.startswith('#')];values=np.array([[float(x) for x in line] for line in rows]);targets.append({'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'headers':[line for line in raw.splitlines() if line.startswith('#')],'vertices':len(values),'minimumVertexId':int(values[:,0].min()),'maximumVertexId':int(values[:,0].max()),'rawDeltaBounds':[values[:,1:].min(axis=0).tolist(),values[:,1:].max(axis=0).tolist()]})
    report={'source':str(SRC),'sourceSha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'objects':objects,'localClosureTargetData':targets,'engineProgramImported':False,'nextCheck':'Evaluate retained native macro source with/without sparse authored closure targets and subdivision 2; prove exact vertex/polygon correspondence to current baked body before transferring deltas. Do not modify the working source.'}
    (E/'source-inspection.json').write_text(json.dumps(report,indent=2)+'\n');print('R0019_SOURCE_INSPECTED',flush=True)
if __name__=='__main__':main()
