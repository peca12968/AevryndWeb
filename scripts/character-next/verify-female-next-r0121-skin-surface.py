"""Minimum independent reopen and unchanged geometry/operation/material scope.
No broad contact or runtime audit for a candidate without appearance gain.
"""
from pathlib import Path
import bpy,numpy as np,json,time,importlib.util
sp=importlib.util.spec_from_file_location('r121readback',Path(__file__).with_name('build-female-next-r0121-native-skin-surface.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);b=a.b;q=a.q;E=a.E
def val(v):
 if isinstance(v,(str,int,float,bool)) or v is None:return v
 try:return list(v)
 except:return str(v)
def mat_signature(m):
 if not m.use_nodes:return {'nodes':False}
 rows=[]
 for n in m.node_tree.nodes:
  row={'name':n.name,'type':n.bl_idname,'inputs':[(s.name,val(s.default_value)) for s in n.inputs if hasattr(s,'default_value')],'properties':{k:val(getattr(n,k)) for k in ['operation','blend_type','uv_map','attribute_name','attribute_type','feature','distance','voronoi_dimensions','noise_dimensions'] if hasattr(n,k)}}
  if hasattr(n,'image') and n.image:row['image']=[n.image.name,n.image.filepath,n.image.colorspace_settings.name]
  rows.append(row)
 return {'nodes':rows,'links':sorted([l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name] for l in m.node_tree.links)}
def poses():
 rows=[];neutral=None
 for label,v in [('neutral',0.),('half',.5),('closed',1.),('restored',0.)]:
  b.deliver(v);d,W,T=b.u.b.geom(bpy.data.objects['AFN113_COMPLETE_WOMAN_COHERENT_HEAD']);W=W.copy();T=T.copy()
  if neutral is None:neutral=W.copy()
  fibres={n:a.a.hasharray(q.hair(bpy.data.objects[n])) for n in ['AFN97_TUCKED_ARTIST_BOB_CHILDREN','AFN57_NATIVE_BROWS','AFN57_NATIVE_LASHES']}
  assert np.isfinite(W).all();rows.append({'state':label,'input':v,'actualSkinWorldHash':a.a.hasharray(W),'actualTriangleHash':a.a.hasharray(T),'actualFibreWorldHashes':fibres,'actualSkinMaximumMovementM':float(np.linalg.norm(W-neutral,axis=1).max())})
 assert rows[1]['actualSkinMaximumMovementM']>0 and rows[2]['actualSkinMaximumMovementM']>rows[1]['actualSkinMaximumMovementM'] and rows[3]['actualSkinMaximumMovementM']==0
 return rows
def main():
 tick=time.time();digest=a.sha(a.OUT);build=json.loads((E/'a-build-summary.json').read_text('utf-8'));bpy.ops.wm.open_mainfile(filepath=str(a.SRC));b.deliver(0);original=a.a.protected();oldMaterials={m.name:mat_signature(m) for m in bpy.data.materials};oldPoses=poses()
 bpy.ops.wm.open_mainfile(filepath=str(a.OUT));b.deliver(0);skin=bpy.data.objects['AFN113_COMPLETE_WOMAN_COHERENT_HEAD'];assert a.a.protected()==original==build['allOriginalGeometryKeysFibresBefore'];assert a.UVs(skin)==build['allUVHashesUnchanged'];assert all(mat_signature(bpy.data.materials[name])==row for name,row in oldMaterials.items())
 states=poses();assert states==oldPoses;b.deliver(0);line=np.load(E/'skin-surface-authoring-lineage.npz');coord=q.arr(skin.data.attributes['AFN121_SkinRestMetres'].data,'vector',len(skin.data.vertices),3);rough=q.arr(skin.data.attributes['AFN121_RegionalRoughness'].data,'value',len(skin.data.vertices));assert np.array_equal(coord,line['restWorldMetres']) and np.array_equal(rough,line['regionalRoughness'])
 mat=skin.data.materials[8];nodes=mat.node_tree.nodes;bs=next(n for n in nodes if n.bl_idname=='ShaderNodeBsdfPrincipled');assert bs.inputs['Roughness'].links[0].from_node.name=='AFN121_LOCAL_ROUGHNESS';assert bs.inputs['Normal'].links[0].from_node.name=='AFN121_MICROMETRE_SURFACE_NORMAL';assert [(l.from_node.name,l.from_socket.name) for l in bs.inputs['Base Color'].links]==[tuple(x) for x in build['unchangedNativeDiffuseBranch']]
 output=next(n for n in nodes if n.bl_idname=='ShaderNodeOutputMaterial');assert not output.inputs['Displacement'].is_linked
 # Unsaved direct actual field edit on a visible face vertex and exact restore.
 point=int(np.argmin(np.linalg.norm(coord-np.array([.03,-.12,1.43]),axis=1)));attr=skin.data.attributes['AFN121_RegionalRoughness'];old=float(attr.data[point].value);attr.data[point].value=old+.02;skin.data.update();bpy.context.view_layer.update();d,W,T=b.u.b.geom(skin);observed=float(d.attributes['AFN121_RegionalRoughness'].data[point].value);assert abs(observed-(old+.02))<1e-6;attr.data[point].value=old;skin.data.update();bpy.context.view_layer.update();d,W,T=b.u.b.geom(skin);assert float(d.attributes['AFN121_RegionalRoughness'].data[point].value)==old
 textures=[]
 for im in bpy.data.images:
  if im.source=='FILE' and not im.packed_file and im.filepath and im.users>0:
   p=Path(bpy.path.abspath(im.filepath));assert p.is_file(),str(p);textures.append({'name':im.name,'relative':im.filepath,'absolute':str(p),'bytes':p.stat().st_size,'sha256':a.sha(p)})
 assert a.sha(a.OUT)==digest==build['sha256'];assert a.sha(a.SRC)==build['sourceSha256']
 a.save('minimum-saved-skin-surface-readback.json',{'status':'INDEPENDENT_REOPEN_UNCHANGED_FULL_GEOMETRY_KEYS_FIBRES_AND_POSES_NEW_SKIN_FIELDS_RECOVERED','candidate':{'source':str(a.OUT),'sha256':digest,'bytes':a.OUT.stat().st_size},'allOriginalActualGeometryKeysFibresAndUVByteExact':True,'allOriginalMaterialNodeInputImageAndLinkSignaturesExact':True,'oldMaterialCountCompared':len(oldMaterials),'actualPoseStates':states,'candidateAllActualPoseWorldArraysExactlyMatchOriginalR117':True,'twoNativeRestSurfaceFieldsRecoveredExactly':True,'roughnessFieldActualEvaluatedDataEditAndExactRestore':{'point':point,'before':old,'observedAfterUnsavedEdit':observed,'restoredExactly':True,'notRenderedAppearanceOrCompleteOperationProof':True},'sameOriginalDiffuseBranchExact':True,'newActiveNormalAndRoughnessBranchesRecovered':True,'noShaderDisplacementConnected':True,'allReferencedExternalTextures':textures,'fullContactNaturalHairBodyRigWholeAnatomyRuntimeAndFemaleAcceptanceUnaccepted':True,'completeNewOperationAccepted':False,'seconds':time.time()-tick})
 print('R121_MINIMUM_SAVED_SKIN_SURFACE_READBACK_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
