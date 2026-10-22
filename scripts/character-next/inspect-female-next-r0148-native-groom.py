"""Read one existing original demo's exact native roles/rights; no transplant."""
from pathlib import Path
import bpy,json,hashlib,re,time
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0148-native-groom-foundation';SRC=R/'Reference/character/blender-bystedt-hair-cc-by-sa/hair_nodes-female_hair_styles.blend'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 tick=time.time();digest=sha(SRC);assert digest=='1ad6202095c1793678fee7d69a7e9f8b5fdb6e5c293d300eb1062d2d437e8d48';bpy.ops.wm.open_mainfile(filepath=str(SRC),load_ui=False)
 texts=[{'name':t.name,'bytes':len(t.as_string().encode()),'sha256':hashlib.sha256(t.as_string().encode()).hexdigest(),'rightsLines':[s for s in t.as_string().splitlines() if re.search('licen|creative|by-sa|copyright|bystedt',s,re.I)]} for t in bpy.data.texts]
 assets=[]
 for ids in [bpy.data.objects,bpy.data.node_groups,bpy.data.materials,bpy.data.meshes,bpy.data.hair_curves]:
  for x in ids:
   if x.asset_data:assets.append({'name':x.name,'author':x.asset_data.author,'license':x.asset_data.license,'copyright':x.asset_data.copyright,'description':x.asset_data.description})
 objects=[]
 for o in bpy.data.objects:
  row={'name':o.name,'type':o.type,'hideRender':o.hide_render,'collections':[c.name for c in o.users_collection],'matrix':[list(r) for r in o.matrix_world],'modifiers':[{'name':m.name,'type':m.type,'nodeGroup':m.node_group.name if m.type=='NODES' and m.node_group else None,'showRender':m.show_render} for m in o.modifiers]}
  if o.type=='CURVES':row.update(curves=len(o.data.curves),points=len(o.data.points),surface=o.data.surface.name if o.data.surface else None,surfaceUV=o.data.surface_uv_map,attributes=[(a.name,a.domain,a.data_type) for a in o.data.attributes])
  if o.type=='MESH':row.update(vertices=len(o.data.vertices),polygons=len(o.data.polygons),uvs=[u.name for u in o.data.uv_layers])
  objects.append(row)
 out={'source':str(SRC),'sha256':digest,'bytes':SRC.stat().st_size,'texts':texts,'assetMetadata':assets,'objects':objects,'sourceOnlyNoFullWomanCandidateOrTransplant':True,'seconds':time.time()-tick}
 (E/'original-native-groom-roles-and-rights.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');assert sha(SRC)==digest;print('R148_ORIGINAL_NATIVE_GROOM_RIGHTS_AND_RAW_ROLES_OBSERVED',len(objects),texts,assets[:3],flush=True)
if __name__=='__main__':main()
