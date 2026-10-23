"""One bounded source semantics read; do not execute third-party code."""
from pathlib import Path
import bpy,json,datetime
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');R=Path('D:/Download/Aevrynd');E=C/'evidence/character-female-next/r0196-artist-primary-volumes';bpy.ops.wm.open_mainfile(filepath=str(R/'Reference/character/blender-studio-ellie-v1-cc-by4/ellie.blend'))
t=bpy.data.texts['rigged_particle_hair.py'].as_string();lines=t.splitlines();matches=[]
for i,s in enumerate(lines):
 if any(x in s for x in ['hair_map','hair_keys','groom_base','hair_guides','hair_key.co','hair_data','intercept','spline','bone.head','head_local']):matches.append({'line':i+1,'context':'\n'.join(lines[max(0,i-3):i+6])})
o=bpy.data.objects['GEO-ellie_hair.groom_base'];uvs=[]
for uv in o.data.uv_layers:
 values=[tuple(v.uv) for v in uv.data];uvs.append({'name':uv.name,'min':[min(p[j] for p in values) for j in [0,1]],'max':[max(p[j] for p in values) for j in [0,1]],'first20':values[:20]})
rig=bpy.data.objects['RIG-Ellie'];bones=[{'name':b.name,'parent':b.parent.name if b.parent else None,'head':list(b.head_local),'tail':list(b.tail_local)} for b in rig.data.bones if 'hair' in b.name.lower()]
q={'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scriptReadOnlyMatches':matches[:60],'groomMeshUVs':uvs,'hairBones':bones,'groomCustomProperties':list(o.keys()),'scalpCustomProperties':list(bpy.data.objects['GEO-ellie_hair.scalp'].keys()),'noScriptExecutedOrImported':True}
(E/'artist-guide-semantics.json').write_bytes((json.dumps(q,indent=2)+'\n').encode());print('R196_ACTUAL_ARTIST_GUIDE_SEMANTICS_READ',json.dumps({'matches':matches[:30],'groomUVs':uvs,'hairBones':len(bones),'firstBones':bones[:5]}),flush=True)
