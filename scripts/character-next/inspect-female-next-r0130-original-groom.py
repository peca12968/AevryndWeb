"""Read original artist groom metadata/texts without evaluating large modifiers."""
from pathlib import Path
import bpy,json,datetime,hashlib
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0130-artist-native-groom';SRC=R/'Reference/character/blender-bystedt-hair-cc-by-sa/hair_nodes-female_hair_styles.blend'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 h=sha(SRC);assert h=='1ad6202095c1793678fee7d69a7e9f8b5fdb6e5c293d300eb1062d2d437e8d48';bpy.ops.wm.open_mainfile(filepath=str(SRC));texts=[]
 for i,t in enumerate(bpy.data.texts):
  s=t.as_string();out=E/('original-text-'+str(i)+'.txt');out.write_text(s,encoding='utf-8');texts.append({'name':t.name,'file':str(out),'bytes':len(s.encode())})
 rows=[]
 for ob in bpy.data.objects:
  row={'name':ob.name,'type':ob.type,'hideRender':ob.hide_render,'collections':[c.name for c in ob.users_collection],'matrixWorld':[list(r) for r in ob.matrix_world],'modifiers':[{'name':m.name,'type':m.type,'nodeGroup':m.node_group.name if m.type=='NODES' and m.node_group else None,'showViewport':m.show_viewport,'showRender':m.show_render} for m in ob.modifiers]}
  if ob.type=='MESH':row.update(vertices=len(ob.data.vertices),polygons=len(ob.data.polygons),materials=[m.name if m else None for m in ob.data.materials],uvLayers=[u.name for u in ob.data.uv_layers])
  elif ob.type=='CURVES':row.update(curves=len(ob.data.curves),points=len(ob.data.points),surface=ob.data.surface.name if ob.data.surface else None,surfaceUVMap=ob.data.surface_uv_map,attributes=[(a.name,a.data_type,a.domain,len(a.data)) for a in ob.data.attributes],materials=[m.name if m else None for m in ob.data.materials])
  rows.append(row)
 source={'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':str(SRC),'sha256':h,'bytes':SRC.stat().st_size,'texts':texts,'objects':rows,'scenes':[{'name':s.name,'objects':len(s.objects),'camera':s.camera.name if s.camera else None,'engine':s.render.engine,'resolution':[s.render.resolution_x,s.render.resolution_y],'samples':s.cycles.samples} for s in bpy.data.scenes],'scriptsAutoExecutionEnabled':bpy.context.preferences.filepaths.use_scripts_auto_execute,'originalNotSavedOrImportedIntoCurrentWoman':True,'modifierOutputsNotEvaluatedByThisInspection':True};(E/'original-artist-groom-inspection.json').write_text(json.dumps(source,indent=2)+'\n',encoding='utf-8');assert sha(SRC)==h;print('R130_ORIGINAL_GROOM_METADATA_AND_TEXTS_READ',len(rows),len(texts),flush=True)
if __name__=='__main__':main()
