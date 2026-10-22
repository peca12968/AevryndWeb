"""One demonstrated source-optics premise correction, not a roughness sweep.
Source actual hair Principled IOR=1000. Change ONLY effective IOR to1.55,
preserve complete source geometry/UV/alpha/pigment/roughness/exposure/49gaze.
Does not fix sheet topology, roots, collisions or natural movement.
"""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,time,datetime
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');R=Path('D:/Download/Aevrynd');E=C/'evidence/character-female-next/r0165-native-hair-construction';OUT=C/'assets-source/aevrynd-character/female-next/r0165-source/aevrynd-female-next-r0165-a-native-hair-optics.blend'
sp=importlib.util.spec_from_file_location('r165optics',C/'scripts/character-next/build-female-next-r0158-shared-native-skin.py');h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h);a=h.a;h.E=E
def val(x):
 if isinstance(x,(int,float,str,bool)) or x is None:return x
 try:return list(x)
 except TypeError:return str(x)
def signature(mat,omit=False):
 return {'method':mat.surface_render_method,'nodes':[{'name':n.name,'type':n.bl_idname,'inputs':[{'identifier':i.identifier,'name':i.name,'value':'IOR_OMITTED' if omit and n.bl_idname=='ShaderNodeBsdfPrincipled' and i.name=='IOR' else val(getattr(i,'default_value',None)),'linked':i.is_linked} for i in n.inputs],'image':n.image.name_full if n.bl_idname=='ShaderNodeTexImage' and n.image else None} for n in mat.node_tree.nodes],'links':[(l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in mat.node_tree.links]}
def main():
 tick=time.time();before=json.loads((E/'before.json').read_text());assert not OUT.exists() and a.a.sha(Path(before['source']))==before['sourceSha256'];alias=R/'engine/assets/characters/female-next/source/r0152-source'/Path(before['source']).name;assert a.a.sha(alias)==before['sourceSha256'];bpy.ops.wm.open_mainfile(filepath=str(alias));s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();hair=bpy.data.objects[a.FIXED[1]];skin=bpy.data.objects[a.FIXED[0]];rig=bpy.data.objects['AFN138_ACTUAL_CURRENT_GAZE_RIG'];raw={n:a.rawsig(bpy.data.objects[n]) for n in a.FIXED+a.MOVING};baseline={n:[a.a.hasharray(x) for x in a.geometry(bpy.data.objects[n])] for n in a.FIXED+a.MOVING};disabled=[]
 for ob in bpy.data.objects:
  if ob.type=='CURVES' or ob.name.startswith('AFN152_'):
   if not ob.hide_render:disabled.append(ob.name)
   ob.hide_render=True;ob.hide_set(True)
 hair.hide_render=False;hair.hide_set(False)
 # Verified immutable source library, same exact current meshes. New material
 # is an object override; library Mesh/material/old history are never modified.
 meshes=[d for d in bpy.data.meshes if d.library is None];names=[d.name for d in meshes]
 with bpy.data.libraries.load(before['source'],link=True) as (src,dst):dst.meshes=list(names)
 linked=dict(zip(names,dst.meshes));replaced=[]
 for ob in bpy.data.objects:
  if ob.type=='MESH' and ob.data in meshes:
   previous=ob.data;ob.data=linked[previous.name];replaced.append({'object':ob.name,'immutableMesh':ob.data.name})
 for d in meshes:
  if d.users==0:bpy.data.meshes.remove(d)
 source=hair.material_slots[0].material;originalSig=signature(source);bs=next(n for n in source.node_tree.nodes if n.bl_idname=='ShaderNodeBsdfPrincipled');originalIOR=float(bs.inputs['IOR'].default_value);assert originalIOR==1000.;mat=source.copy();mat.name='AFN165_HAIR_SOURCE_DIELECTRIC_IOR_CORRECTED';newBS=next(n for n in mat.node_tree.nodes if n.bl_idname=='ShaderNodeBsdfPrincipled');newBS.inputs['IOR'].default_value=1.55;hair.material_slots[0].link='OBJECT';hair.material_slots[0].material=mat;assert signature(source,True)==signature(mat,True);assert float(bs.inputs['IOR'].default_value)==1000.;actualIOR=float(newBS.inputs['IOR'].default_value);assert abs(actualIOR-1.55)<1e-6;bpy.context.view_layer.update();assert raw=={n:a.rawsig(bpy.data.objects[n]) for n in raw} and baseline=={n:[a.a.hasharray(x) for x in a.geometry(bpy.data.objects[n])] for n in baseline}
 h.save('direct-hair-optical-source-authoring-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originalStartedUTC':before['startedUTC'],'originalMajorDefect':'Coarse glossy original sheet/bundle hair','actualChangedPremise':'Installed actual original Hair material has unlinked Principled IOR1000, distinct from retired guide/cage/material-roughness rescue. One controlled source optical-model input correction to1.55, no parameter sweep. Geometry rest construction remains unresolved and is not claimed repaired.','originalActualIOR':originalIOR,'newEffectiveIOR':actualIOR,'shaderModelRemainsPrincipledSurfaceForExistingAlphaMesh':True,'allOtherShaderInputsLinksImagesAlphaColourRoughnessUnchanged':signature(source,True)==signature(mat,True),'sourceShaderSignature':originalSig,'candidateShaderSignature':signature(mat),'reference':'https://docs.blender.org/manual/en/5.0/render/shader_nodes/shader/hair_principled.html ;1.55 documented hair IOR default, not proof existing card model is a physiological fibre.','sameAllSevenRawMeshesUVAndEvaluatedNeutralGeometry':True,'onlyExplicitFailed152GroomDisabled':disabled,'immutableMeshReuse':replaced,'noNewHairGuidesRestShapeOrMotionClaimed':True})
 bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=True);h.save('a-build-summary.json',{'source':before['source'],'output':str(OUT),'engineAlias':str(R/'engine/assets/characters/female-next/source/r0165-source'/OUT.name),'sha256':a.a.sha(OUT),'bytes':OUT.stat().st_size,'actualSkin':skin.name,'actualRig':rig.name,'actualHair':hair.name,'actualHairMaterial':mat.name,'originalActualIOR':originalIOR,'newEffectiveIOR':actualIOR,'allCurrentGeometryUnchanged':True,'originalGazeAction':rig.animation_data.action.name,'source152FailedGroomNotAdopted':True,'onlyOpticalCorrectionCandidateNotGroomRebuild':True,'unaccepted':True,'secondsBeforePreview':time.time()-tick});assert OUT.stat().st_size<before['sourceBudgetBytes'];a.b.u.v.E=E;views=[]
 for view in ['face','body-face','profile','back','oblique']:
  ctl=a.b.u.v.image('a-hair-optical-source',view);ctl.update(frame=1,actualHairMaterial=mat.name,effectiveIOR=actualIOR,allCurrentEvaluatedGeometryUnchanged=True);views.append(ctl);h.save('actual-optical-source-preview-controls.json',views)
 print('R165_COMPLETE_NATIVE_HAIR_OPTICAL_SOURCE_HEAD_BODY_PROFILE_BACK_OBLIQUE_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
