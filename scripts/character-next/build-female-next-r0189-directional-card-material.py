"""One complete-woman directional card material; preserve actual source F0.

Source IOR1000 is faithful specular-glossiness encoding, not an import bug.
This changes the material representation, never follicles, geometry or UVs.
"""
from pathlib import Path
import bpy,numpy as np,datetime,time,json,hashlib,importlib.util
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158')
R=Path('D:/Download/Aevrynd')
E=C/'evidence/character-female-next/r0189-source-alpha-pipeline'
OUT=C/'assets-source/aevrynd-character/female-next/r0189-source/aevrynd-female-next-r0189-a-directional-card-material.blend'
sp=importlib.util.spec_from_file_location('r189base',C/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;h=m.h
def save(n,v):(E/n).write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
def sha(p):return hashlib.file_digest(open(p,'rb'),'sha256').hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def main():
 tick=time.time();t=json.loads((E/'before.json').read_text());assert not OUT.exists();assert sha(t['source'])==t['sourceSha256']
 bpy.ops.wm.open_mainfile(filepath=t['source']);s=bpy.context.scene;s.frame_set(1);s.camera.data.type='PERSP'
 ob=bpy.data.objects['AFN126_ORIGINAL_Hair_Hair_0'];ob.hide_render=False;ob.hide_set(False);ob.material_slots[0].link='DATA'
 bpy.data.objects['AFN184_ACTUAL_NATIVE_DEFORMED_LASHES'].hide_render=True;bpy.data.objects['AFN184_ACTUAL_NATIVE_DEFORMED_LASHES'].hide_set(True)
 bpy.data.objects['AFN126_ORIGINAL_Eyelashes_Eyelashes_0'].hide_render=False;bpy.data.objects['AFN126_ORIGINAL_Eyelashes_Eyelashes_0'].hide_set(False)
 bpy.context.view_layer.update();protected={n:a.rawsig(bpy.data.objects[n]) for n in a.FIXED+a.MOVING};W,T=a.geometry(ob)
 a.b.u.v.E=E
 for v in ['face','body-face','back']:s.camera.data.type='PERSP';a.b.u.v.image('baseline-source-original-lashes',v)
 old=ob.material_slots[0].material;oldbs=next(n for n in old.node_tree.nodes if n.bl_idname=='ShaderNodeBsdfPrincipled')
 alphaMath=oldbs.inputs['Alpha'].links[0].from_node
 imageNode=next(x.from_node for x in alphaMath.inputs[0].links if x.from_node.bl_idname=='ShaderNodeTexImage');im=imageNode.image
 pixels=np.empty(len(im.pixels),'f4');im.pixels.foreach_get(pixels);alpha=pixels.reshape(im.size[1],im.size[0],im.channels)[:,:,3]
 gv,gu=np.gradient(alpha);weight=((alpha>.05)&(alpha<.95)).astype('f4');den=max(float(weight.sum()),1.)
 tensor=np.array([[np.sum(weight*gu*gu),np.sum(weight*gu*gv)],[np.sum(weight*gu*gv),np.sum(weight*gv*gv)]])/den
 val,vec=np.linalg.eigh(tensor);direction=vec[:,0];direction*=1 if direction[np.argmax(np.abs(direction))]>=0 else -1
 # This is an unoriented shading axis, not root-to-tip follicle inference.
 ob.data=ob.data.copy();mesh=ob.data;mesh.name='AFN189_SAME_HAIR_GEOMETRY_WITH_MEASURED_UV_SHADING_TANGENTS';mesh.calc_tangents(uvmap=mesh.uv_layers.active.name)
 U=h.arr(mesh.loops,'tangent',len(mesh.loops),3);N=h.arr(mesh.loops,'normal',len(mesh.loops),3);sg=h.arr(mesh.loops,'bitangent_sign',len(mesh.loops));V=np.cross(N,U)*sg[:,None]
 tangent=U*direction[0]+V*direction[1];tangent/=np.maximum(np.linalg.norm(tangent,axis=1)[:,None],1e-20)
 attr=mesh.attributes.new('AFN189_ACTUAL_FIBRE_SHADING_TANGENT','FLOAT_VECTOR','CORNER');attr.data.foreach_set('vector',tangent.astype('f4').ravel());mesh.update()
 new=old.copy();new.name='AFN189_DIRECTIONAL_CARD_PBR_PRESERVED_SOURCE_NORMAL_F0';bs=next(n for n in new.node_tree.nodes if n.bl_idname=='ShaderNodeBsdfPrincipled')
 oldior=float(oldbs.inputs['IOR'].default_value);oldlevel=float(oldbs.inputs['Specular IOR Level'].default_value);oldTint=np.array(oldbs.inputs['Specular Tint'].default_value[:3]);F0=((oldior-1)/(oldior+1))**2*2*oldlevel*oldTint
 newior=1.55;f=((newior-1)/(newior+1))**2;level=float(F0.max()/(2*f));tint=F0/F0.max()
 bs.inputs['IOR'].default_value=newior;bs.inputs['Specular IOR Level'].default_value=level;bs.inputs['Specular Tint'].default_value=(*tint,1);bs.inputs['Anisotropic'].default_value=.8
 # Physical shading choice: no emitted light; authored source emission is not a bug.
 bs.inputs['Emission Strength'].default_value=0
 an=new.node_tree.nodes.new('ShaderNodeAttribute');an.attribute_name=attr.name;an.name='AFN189_MEASURED_TEXTURE_AXIS_CORNER_ATTRIBUTE'
 tr=new.node_tree.nodes.new('ShaderNodeVectorTransform');tr.vector_type='VECTOR';tr.convert_from='OBJECT';tr.convert_to='WORLD';new.node_tree.links.new(an.outputs['Vector'],tr.inputs['Vector']);new.node_tree.links.new(tr.outputs['Vector'],bs.inputs['Tangent'])
 ob.material_slots[0].link='OBJECT';ob.material_slots[0].material=new;bpy.context.view_layer.update()
 assert protected=={n:a.rawsig(bpy.data.objects[n]) for n in protected}
 CW,CT=a.geometry(ob);assert np.array_equal(T,CT) and np.array_equal(W,CW)
 np.savez_compressed(E/'actual-shading-tangent-lineage.npz',textureAlphaGradientTensor=tensor,textureUnorientedUVAxis=direction,actualCornerTangents=tangent.astype('f4'),sourceF0=F0)
 proof={'UTC':now(),'originalStartedUTC':t['startedUTC'],'materialAuthoringStartedAfterSupportDeadline':now()>t['supportDeadlineUTC'],'sourceIOR1000IsFaithfulImporterF0EncodingNotBug':True,'importerEvidence':'D:/SteamLibrary/steamapps/common/Blender/5.2/scripts/addons_core/io_scene_gltf2/blender/imp/KHR_materials_pbrSpecularGlossiness.py','actualSourceMaterial':old.name,'newEffectiveMaterial':new.name,'changedPremise':'Replace isotropic emitted legacy card response with one directionally shaded non-emitting PBR representation. Keep actual normal-incidence RGB F0, diffuse texture/factor, alpha texture/factor, roughness, all hair/world geometry/UV and stage. No IOR-only repair or colour/roughness/density sweep.','anisotropy':.8,'newIOR':newior,'newSpecularIORLevel':level,'newSpecularTint':tint.tolist(),'sourceNormalF0':F0.tolist(),'normalF0ReconstructionMaximumError':float(np.max(np.abs(2*level*f*tint-F0))),'sourceEmissionStrength':float(oldbs.inputs['Emission Strength'].default_value),'newEmissionStrength':0,'emissionRemovalIsAuthoredModelChoiceNotImportCorrection':True,'alphaAtlasSize':list(im.size),'sourceAlphaImage':im.name,'alphaGradientTensor':tensor.tolist(),'gradientEigenvalues':val.tolist(),'axisStrengthRatio':float(val[-1]/max(val[0],1e-20)),'actualUnorientedUVShadingAxis':direction.tolist(),'notHairFlowOrFollicleMap':True,'tangentDomain':attr.domain,'tangentCount':len(tangent),'invalidTangentCount':int((~np.isfinite(tangent)).sum()),'zeroTangentCount':int((np.linalg.norm(tangent,axis=1)<.99).sum()),'protectedSevenRawMeshUVSignatures':protected,'actualHairWorldGeometryUnchanged':True,'actualHairVertices':len(mesh.vertices),'actualHairTriangles':len(T),'originalLashesRestoredForBaselineAndCandidate':True,'onlyOneCandidateNoVariants':True}
 save('directional-material-authoring.json',proof)
 for v in ['face','body-face','oblique','profile','back']:s.camera.data.type='PERSP';a.b.u.v.image('a-directional-card-material',v)
 s.camera.data.type='PERSP';a.b.u.v.image('a-directional-card-material-saved-head','face')
 OUT.parent.mkdir(parents=True,exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
 save('a-build-summary.json',{'UTC':now(),'output':str(OUT),'sha256':sha(OUT),'bytes':OUT.stat().st_size,'source':t['source'],'sourceSha256':t['sourceSha256'],'oneCandidate':True,'methodCount':1,'actualDisplayHair':ob.name,'effectiveMaterial':new.name,'elapsedJobSeconds':time.time()-tick,'sourceCapExceeded':OUT.stat().st_size>t['sourceBudgetBytes'],'appearanceFunctionContactRuntimeNotAcceptedByBuilder':True})
 print('R189_ONE_DIRECTIONAL_MATERIAL_COMPLETE_WOMAN_SAVED',str(OUT),flush=True)
if __name__=='__main__':main()
