"""One bounded source-stack control after three constructions, not a candidate.
Check the omitted original Surface Deform stage and actual generator outputs.
Render original artist head/groom with the controlled brown material.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0082-head-volume-cage';S=R/'engine/assets/characters/female-next/source';DEMO=R/'Reference/character/blender-bystedt-hair-cc-by-sa/hair_nodes-female_hair_styles.blend'
sp=importlib.util.spec_from_file_location('control82',Path(__file__).with_name('build-female-next-r0082-head-cage.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);q=a.q
def save(n,v):(E/n).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def main():
 tick=time.time();ref=q.read(E/'c-build-summary.json');assert hashlib.sha256(Path(ref['output']).read_bytes()).hexdigest()==ref['outputSha256'];bpy.ops.wm.open_mainfile(filepath=ref['output']);bpy.context.scene.frame_set(1);old=bpy.data.objects[ref['editableGuideObject']];A=old.matrix_world.copy();z=np.load(E/'c-wrap-and-render-lineage.npz') if (E/'c-wrap-and-render-lineage.npz').exists() else np.load(E/'b-wrap-and-render-lineage.npz');expected=z['sourceGeneratedLocal']
 for o in bpy.context.scene.objects:
  if o.type in ('MESH','CURVES'):o.hide_render=True
 with bpy.data.libraries.load(str(DEMO),link=False) as (src,dst):dst.objects=['curly hair','curly growth mesh','long hair growth mesh']
 hair,curly,long=dst.objects
 for o in (hair,curly,long):o.parent=None;bpy.context.scene.collection.objects.link(o);o.matrix_world=A.copy();o.hide_render=o is not hair;o.hide_set(False)
 hair.data.materials.clear();hair.data.materials.append(bpy.data.materials['Brown hair']);native=q.arr(hair.data.position_data,'vector',len(hair.data.position_data),3);mainMod=next(md for md in hair.modifiers if md.type=='NODES' and md.node_group and md.node_group.name.startswith('curly hair'));mainMod.show_viewport=mainMod.show_render=False;bpy.context.view_layer.update();d=hair.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;deformed=q.arr(d.position_data,'vector',len(d.position_data),3);assert deformed.shape==native.shape
 mainMod.show_viewport=mainMod.show_render=True;bpy.context.view_layer.update();d=hair.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;full=q.arr(d.position_data,'vector',len(d.position_data),3);counts=np.array([c.points_length for c in d.curves]);rawDelta=float(np.linalg.norm((deformed-native)@np.array(A)[:3,:3].T,axis=1).max());outputDelta=float(np.linalg.norm((full-expected)@np.array(A)[:3,:3].T,axis=1).max()) if full.shape==expected.shape else None
 branches=[];seen=set()
 def scan(group):
  if group.name in seen:return
  seen.add(group.name)
  for node in group.nodes:
   if 'Viewport' in node.bl_idname or 'viewport' in node.name.lower():branches.append({'group':group.name,'node':node.name,'type':node.bl_idname})
   for socket in node.inputs:
    if socket.name=='Viewport Amount':
     row={'group':group.name,'node':node.name,'socket':socket.name,'linked':socket.is_linked,'default':socket.default_value}
     if socket.is_linked:
      link=socket.links[0];row.update(sourceNode=link.from_node.name,sourceType=link.from_node.bl_idname,sourceSocket=link.from_socket.name,sourceDefault=link.from_socket.default_value if hasattr(link.from_socket,'default_value') and isinstance(link.from_socket.default_value,(int,float,bool)) else None)
     branches.append(row)
   if hasattr(node,'node_tree') and node.node_tree:scan(node.node_tree)
 for md in hair.modifiers:
  if md.type=='NODES' and md.node_group:scan(md.node_group)
 result={'source':str(DEMO),'sourceSHA256':hashlib.sha256(DEMO.read_bytes()).hexdigest(),'referenceOnlyNotNewCandidate':True,'sameReferenceObjectMatrix':np.array(A).tolist(),'originalNativeGuides':len(hair.data.curves),'afterSurfaceDeformGuides':len(hair.data.curves),'afterSurfaceDeformPoints':len(deformed),'maximumOriginalSurfaceDeformWorldShiftM':rawDelta,'completeOriginalStackCurves':len(counts),'completeOriginalStackPoints':len(full),'restoredR82SourceBeforeWrapPoints':len(expected),'completeOriginalVsRestoredSourceMaximumWorldDifferenceM':outputDelta,'sameGeneratedCountsNotClaimedAsSameShape':True,'viewportBranchInspection':branches,'currentSceneModeIsViewportEvaluationNotRenderDepsgraphCertificate':True,'materialControl':'Exact current Brown hair on original publisher head and unmodified original complete stack, same object fit. Not Aevrynd woman result.','newCandidateOrModelSaved':False,'secondsBeforeReferenceRenders':time.time()-tick};save('original-stack-control.json',result);np.savez_compressed(E/'original-stack-control-lineage.npz',rawNativeGuides=native,originalDeformedGuides=deformed,originalStackPositions=full,originalStackCounts=counts,matrix=np.array(A));head=bpy.data.objects['AFN68_ORIGINAL_REFERENCE_HEAD_HIDDEN'];head.hide_render=False;head.hide_set(False);head.matrix_world=A.copy();rows=[]
 for view in ('face','back'):rows.append(a.render('reference-original-brown',view));save('original-brown-reference-controls.json',rows)
 print('R82_ORIGINAL_STACK_CONTROL',rawDelta,outputDelta,len(full),time.time()-tick,flush=True)
if __name__=='__main__':main()
