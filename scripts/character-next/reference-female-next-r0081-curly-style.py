"""Isolate and render the actual publisher curly style before any fitting.
This is an attributed reference, never a new Aevrynd character result.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
from mathutils import Matrix,Vector
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0081-editable-curly-groom';S=R/'engine/assets/characters/female-next/source';SRC=R/'Reference/character/blender-bystedt-hair-cc-by-sa/hair_nodes-female_hair_styles.blend';SHA='1ad6202095c1793678fee7d69a7e9f8b5fdb6e5c293d300eb1062d2d437e8d48'
def module(n,f):
 sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(f));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
m=module('ref81render','build-female-next-r0074-oral-controls.py');q=module('ref81data','qualify-female-next-r0075-dental-motion.py');m.E=E;m.m.shade.g.E=E
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):(E/n).write_text(json.dumps(v,indent=2,default=str)+'\n',encoding='utf-8')
def main():
 tick=time.time();assert sha(SRC)==SHA;bpy.ops.wm.open_mainfile(filepath=str(S/'aevrynd-female-next-r0076-a-proximal-crown-sculpt-study.blend'))
 for o in bpy.context.scene.objects:
  if o.type in ('MESH','CURVES'):o.hide_render=True
 with bpy.data.libraries.load(str(SRC),link=False) as (src,dst):dst.objects=['head','eyes','curly hair','curly growth mesh'];dst.texts=['Hair demo file info']
 objects={o.name:o for o in dst.objects};T=Matrix.Diagonal((.095,.095,.095,1.));T.translation=(0.,.015,1.562-16.410877227783203*.095)
 for name,o in objects.items():
  basis=o.matrix_basis.copy();o.parent=None;bpy.context.scene.collection.objects.link(o);o.matrix_world=T@basis if name=='eyes' else T;o.hide_render=name=='curly growth mesh';o.hide_set(False)
 bpy.context.scene.frame_set(1);bpy.context.view_layer.update();hair=objects['curly hair'];d=hair.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;P=q.arr(d.position_data,'vector',len(d.position_data),3);rr=q.arr(d.attributes['radius'].data,'value',len(P));assert len(d.curves)<250000 and len(P)<15000000 and np.isfinite(P).all() and np.isfinite(rr).all();assert rr.min()>=0
 graph=[]
 for md in hair.modifiers:
  if md.type=='NODES' and md.node_group:
   graph.append({'modifier':md.name,'group':md.node_group.name,'nodes':[{'name':n.name,'type':n.bl_idname,'group':n.node_tree.name if hasattr(n,'node_tree') and n.node_tree else None,'inputs':[{'name':i.name,'linked':i.is_linked,'value':list(i.default_value) if i.type in ('VECTOR','RGBA') else (i.default_value.name if hasattr(i.default_value,'name') else i.default_value)} for i in n.inputs if hasattr(i,'default_value')]} for n in md.node_group.nodes]})
 ref={'source':str(SRC),'sha256':SHA,'referenceOnly':True,'artist':'Daniel Bystedt','license':'CC BY-SA, version not specified by author/publisher','embeddedNotice':dst.texts[0].as_string(),'originalNativeGuides':len(hair.data.curves),'originalNativeGuidePoints':len(hair.data.position_data),'evaluatedCurves':len(d.curves),'evaluatedPoints':len(P),'localRadiusRange':[float(rr.min()),float(rr.max())],'localBounds':[P.min(0).tolist(),P.max(0).tolist()],'referenceObjectMatrix':np.array(T).tolist(),'sourceGraph':graph,'noNodeSettingsChanged':True,'embeddedCodeExecuted':False,'secondsBeforeRender':time.time()-tick};save('original-curly-evaluation.json',ref)
 # Author's embedded note asks for3 subdivisions for curl/braid render curves.
 # Production A/B will use the same setting for baseline and candidate.
 rows=[];s=bpy.context.scene;m.m.shade.settings();s.render.hair_subdiv=3;s.render.resolution_x=s.render.resolution_y=640;s.cycles.samples=16
 for view in ('face','oblique','profile','back'):
  m.m.k.b.camera('oblique' if view=='back' else view);s.camera.data.lens=85
  if view=='back':s.camera.location=(0,.91,1.43);s.camera.rotation_euler=(Vector((0,.02,1.405))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.lens=65
  s.render.filepath=str(E/('reference-original-curly-'+view+'.png'));bpy.ops.render.render(write_still=True);rows.append({'view':view,'file':s.render.filepath,'camera':np.array(s.camera.matrix_world).tolist(),'lights':m.q.lights(),'samples':16,'resolution':640,'hairSubdiv':3,'seed':s.cycles.seed,'exposure':s.view_settings.exposure,'look':s.view_settings.look,'referenceOnly':True});save('original-curly-views.json',rows)
 print('R81_ORIGINAL_CURLY_REFERENCE',ref['evaluatedCurves'],ref['evaluatedPoints'],time.time()-tick,flush=True)
if __name__=='__main__':main()
