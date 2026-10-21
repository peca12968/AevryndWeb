"""One source-derived hair-axis field test; all original card/color/PBR inputs fixed.
New atlas evidence changes the prior unsupported uniformV tangent premise.
No rotation/roughness/color/alpha/thickness sweep.
"""
from pathlib import Path
import bpy,numpy as np,json,time,importlib.util
sp=importlib.util.spec_from_file_location('r123flow',Path(__file__).with_name('build-female-next-r0123-current-scalp-growspace.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);b=a.b;q=a.q;E=a.E;S=a.S;SRC=S/'r0122-source/aevrynd-female-next-r0122-c-native-alpha-cards.blend';OUT=S/'r0123-source/aevrynd-female-next-r0123-b-source-atlas-strand-flow.blend'
def scalar(v):
 try:return list(v)
 except:return v
def main():
 tick=time.time();assert not OUT.exists();bpy.ops.wm.open_mainfile(filepath=str(SRC));b.deliver(0.);sourceHash=a.sha(SRC);hair=bpy.data.objects['AFN122_ORIGINAL_NATIVE_BOB_ALPHA_CARDS'];old=bpy.data.objects['AFN97_TUCKED_ARTIST_BOB_CHILDREN'];old.hide_set(False);bpy.context.view_layer.update();protected=a.a.protected();old.hide_set(True);beforeMesh=d,W,T=b.u.b.geom(hair);W=W.copy();T=T.copy();oldMat=hair.data.materials[0];mat=oldMat.copy();mat.name='AFN123_SOURCE_ATLAS_STRAND_ORIENTATION_ONLY';hair.data.materials[0]=mat;N=mat.node_tree.nodes;L=mat.node_tree.links;bs=next(n for n in N if n.bl_idname=='ShaderNodeBsdfPrincipled');parameters={s.name:scalar(s.default_value) for s in bs.inputs if hasattr(s,'default_value')};oldDiffuse=next(n.image for n in N if n.bl_idname=='ShaderNodeTexImage');originalTexture=a.sha(Path(bpy.path.abspath(oldDiffuse.filepath)));oldDiffuse.filepath='//../r0122-source/native-bob-texture-input/bob01_diffuse.png';assert a.sha(Path(bpy.path.abspath(oldDiffuse.filepath)))==originalTexture;uv=next(n for n in N if n.bl_idname=='ShaderNodeUVMap');u=next(n for n in N if n.bl_idname=='ShaderNodeTangent');geom=next(n for n in N if n.bl_idname=='ShaderNodeNewGeometry');v=next(n for n in N if n.bl_idname=='ShaderNodeVectorMath' and n.operation=='CROSS_PRODUCT');oldTangent=bs.inputs['Tangent'].links[0].from_node.name
 path=S/'r0123-source/native-strand-flow/bob01-undirected-strand-flow.png';image=bpy.data.images.load(str(path),check_existing=True);image.filepath='//native-strand-flow/bob01-undirected-strand-flow.png';image.colorspace_settings.name='Non-Color';tex=N.new('ShaderNodeTexImage');tex.name='AFN123_ORIGINAL_ATLAS_STRUCTURE_FLOW';tex.image=image;L.new(uv.outputs['UV'],tex.inputs['Vector']);sep=N.new('ShaderNodeSeparateXYZ');L.new(tex.outputs['Color'],sep.inputs[0])
 def math(op,x,y=None):
  n=N.new('ShaderNodeMath');n.operation=op
  if isinstance(x,(float,int)):n.inputs[0].default_value=x
  else:L.new(x,n.inputs[0])
  if y is not None:
   if isinstance(y,(float,int)):n.inputs[1].default_value=y
   else:L.new(y,n.inputs[1])
  return n.outputs[0]
 cx=math('SUBTRACT',math('MULTIPLY',sep.outputs['X'],2.),1.);sy=math('SUBTRACT',math('MULTIPLY',sep.outputs['Y'],2.),1.);phi=math('MULTIPLY',math('ARCTAN2',sy,cx),.5);cos=math('COSINE',phi);sin=math('SINE',phi)
 def scale(vec,value):
  n=N.new('ShaderNodeVectorMath');n.operation='SCALE';L.new(vec,n.inputs[0]);L.new(value,n.inputs['Scale']);return n.outputs['Vector']
 add=N.new('ShaderNodeVectorMath');add.name='AFN123_ACTUAL_ATLAS_STRAND_TANGENT';add.operation='ADD';L.new(scale(u.outputs['Tangent'],cos),add.inputs[0]);L.new(scale(v.outputs['Vector'],sin),add.inputs[1]);L.new(add.outputs['Vector'],bs.inputs['Tangent']);assert {s.name:scalar(s.default_value) for s in bs.inputs if hasattr(s,'default_value')}==parameters
 d,WW,TT=b.u.b.geom(hair);assert np.array_equal(WW,W) and np.array_equal(TT,T);old.hide_set(False);bpy.context.view_layer.update();assert a.a.protected()==protected;old.hide_set(True)
 hair['AFN123_flow_scope']='Only per-pixel hair axis from original atlas structure changes. Full original RGB/alpha, native mesh/UV, nominal thickness and all BSDF scalar inputs exact. Atlas-pattern orientation is not measured anatomy, finite alpha occupancy, current-root attachment or natural dynamics proof.'
 bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=False);assert a.sha(SRC)==sourceHash;a.save('b-build-summary.json',{'source':str(SRC),'sourceSha256':sourceHash,'output':str(OUT),'sha256':a.sha(OUT),'bytes':OUT.stat().st_size,'hairObject':hair.name,'changedFailedPremise':'R122 C assumed all atlas fibres follow uniformV. Actual original opaque coherent atlas has784496 of2279617 supported pixels differing by>20deg. Use one structure-derived undirected strand-axis field, no scalar/rotation/alpha sweep.','originalCardWorldHash':a.a.hasharray(W),'originalCardTriangleHash':a.a.hasharray(T),'allOriginalGeometryThicknessAndUVUnchanged':True,'allOriginalRGBABytesUnchanged':True,'originalDiffuseSha256':originalTexture,'allOriginalBSDFDefaultValuesUnchanged':parameters,'oldUniformVTangentNode':oldTangent,'newTangentNode':add.name,'flowDataTexture':{'relative':image.filepath,'absolute':str(path),'sha256':a.sha(path),'bytes':path.stat().st_size},'allProtectedR117BodyKeysOldFibresAndRadii':protected,'stillNoFiniteRootAlphaSelfContinuousMotionRuntimeQualification':True,'secondsBeforePreview':time.time()-tick})
 rows=[]
 for view in ['face','body-face','profile','oblique','back']:
  rows.append(b.u.v.image('b-source-atlas-flow',view));a.save('b-view-controls.json',rows)
 print('R123_SINGLE_SOURCE_ATLAS_FLOW_COMPLETE_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
