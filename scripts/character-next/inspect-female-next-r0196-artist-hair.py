"""Read artist source hair structure without executing source rig scripts."""
from pathlib import Path
import bpy,json,datetime,hashlib,numpy as np
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');R=Path('D:/Download/Aevrynd');E=C/'evidence/character-female-next/r0196-artist-primary-volumes';source=R/'Reference/character/blender-studio-ellie-v1-cc-by4/ellie.blend'
assert hashlib.file_digest(source.open('rb'),'sha256').hexdigest()=='3dd235218725a9e68890073bbeacb4820f9b34db65d44f80c31bb88696a3c54c'
bpy.ops.wm.open_mainfile(filepath=str(source));rows=[]
for o in bpy.data.objects:
 if o.type not in ['MESH','CURVE','CURVES']:continue
 d=o.data;row={'name':o.name,'type':o.type,'hideRender':o.hide_render,'hideViewport':o.hide_viewport,'matrixWorld':[list(r) for r in o.matrix_world],'materials':[m.name if m else None for m in d.materials],'modifiers':[{'name':m.name,'type':m.type,'object':m.object.name if m.type=='ARMATURE' and m.object else None} for m in o.modifiers]}
 if o.type=='MESH':row.update(vertices=len(d.vertices),polygons=len(d.polygons),uvNames=[u.name for u in d.uv_layers],boundBox=[list(v) for v in o.bound_box],shapeKeys=[k.name for k in d.shape_keys.key_blocks] if d.shape_keys else [])
 elif o.type=='CURVES':row.update(curves=len(d.curves),points=len(d.points))
 else:row.update(splines=len(d.splines),splineSizes=[len(s.points)+len(s.bezier_points) for s in d.splines],bevelDepth=d.bevel_depth)
 rows.append(row)
q={'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':str(source),'objects':rows,'collections':[c.name for c in bpy.data.collections],'textNames':[t.name for t in bpy.data.texts],'sourceNotSavedOrImported':True,'embeddedScriptsNotExecuted':True}
(E/'artist-source-structure.json').write_bytes((json.dumps(q,indent=2)+'\n').encode());print('R196_ORIGINAL_ARTIST_HAIR_STRUCTURE_READ',json.dumps([r for r in rows if any(s in r['name'].lower() for s in ['hair','head','scalp'])]),flush=True)
