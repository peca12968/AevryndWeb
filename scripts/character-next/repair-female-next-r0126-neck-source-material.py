"""Retain promising complete shape; repair exact source material/UV transition.
No geometry, face shader, pigment, lights, alpha or scalar parameter variant.
"""
from pathlib import Path
import bpy,bmesh,numpy as np,json,time,importlib.util
R=Path('D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0126-individual-head-foundation';SRC=S/'r0126-source/aevrynd-female-next-r0126-a-individual-artist-head.blend';OUT=S/'r0126-source/aevrynd-female-next-r0126-a2-source-material-neck.blend'
sp=importlib.util.spec_from_file_location('r126repair',Path(__file__).with_name('build-female-next-r0126-individual-head.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);b=a.b;q=a.q;b.u.v.E=E
def clone_graph(source,dest,prefix,uvname):
 N=dest.node_tree.nodes;links=dest.node_tree.links;mapping={};output=None
 for old in source.node_tree.nodes:
  if old.bl_idname=='ShaderNodeOutputMaterial':continue
  new=N.new(old.bl_idname);new.name=prefix+old.name;mapping[old]=new
  for prop in old.bl_rna.properties:
   key=prop.identifier
   if prop.is_readonly or key in ['rna_type','name','type','parent','location','width','height','dimensions','select','inputs','outputs','internal_links']:continue
   try:setattr(new,key,getattr(old,key))
   except (TypeError,AttributeError,ValueError):pass
  for src,dst in zip(old.inputs,new.inputs):
   if hasattr(src,'default_value'):
    try:dst.default_value=src.default_value
    except (TypeError,AttributeError,ValueError):pass
 for link in source.node_tree.links:
  if link.to_node.bl_idname=='ShaderNodeOutputMaterial':
   if link.to_socket.name=='Surface':output=mapping[link.from_node].outputs[list(link.from_node.outputs).index(link.from_socket)]
   continue
  links.new(mapping[link.from_node].outputs[list(link.from_node.outputs).index(link.from_socket)],mapping[link.to_node].inputs[list(link.to_node.inputs).index(link.to_socket)])
 if uvname:
  uv=N.new('ShaderNodeUVMap');uv.uv_map=uvname
  for old,new in mapping.items():
   if old.bl_idname=='ShaderNodeUVMap':new.uv_map=uvname
   if old.bl_idname=='ShaderNodeTexImage' and not old.inputs['Vector'].is_linked:links.new(uv.outputs['UV'],new.inputs['Vector'])
   if old.bl_idname=='ShaderNodeTexCoord':
    for link in list(new.outputs['UV'].links):links.new(uv.outputs['UV'],link.to_socket)
 assert output;return output
def main():
 tick=time.time();assert not OUT.exists();build=json.loads((E/'a-build-summary.json').read_text('utf-8'));assert a.a.sha(SRC)==build['sha256'];bpy.ops.wm.open_mainfile(filepath=str(SRC));skin=bpy.data.objects[build['actualSkinObject']];_,W,T=b.u.b.geom(skin);W=W.copy();T=T.copy();oldMat=bpy.data.materials['AFN126_ACTUAL_NECK_SOURCE_COLOR_TRANSITION'];native=next(m for m in skin.data.materials if m and m.name.startswith('AFN113_COHERENT_NATIVE_HEAD_SKIN'));artist=next(m for m in skin.data.materials if m and m.name.startswith('AFN126_NATIVE_ARTIST_HEAD_MATERIAL'));artistNormalMaps=[(n.name,n.uv_map) for n in artist.node_tree.nodes if n.bl_idname=='ShaderNodeNormalMap'];[(setattr(n,'uv_map','AngelicaOriginalUV')) for n in artist.node_tree.nodes if n.bl_idname=='ShaderNodeNormalMap'];patch=bpy.data.materials.new('AFN126_EXACT_DUAL_SOURCE_NECK_MATERIAL');patch.use_nodes=True;patch.node_tree.nodes.clear();bodyShader=clone_graph(native,patch,'NativeBody/',None);headShader=clone_graph(artist,patch,'ArtistHead/','AngelicaOriginalUV');N=patch.node_tree.nodes;links=patch.node_tree.links;attr=N.new('ShaderNodeAttribute');attr.attribute_name='AFN126_NECK_BLEND';mix=N.new('ShaderNodeMixShader');links.new(attr.outputs['Fac'],mix.inputs[0]);links.new(bodyShader,mix.inputs[1]);links.new(headShader,mix.inputs[2]);out=N.new('ShaderNodeOutputMaterial');links.new(mix.outputs['Shader'],out.inputs['Surface'])
 index=next(i for i,m in enumerate(skin.data.materials) if m==oldMat);bm=bmesh.new();bm.from_mesh(skin.data);weight=bm.verts.layers.float.get('AFN113_NATIVE_COLOR_WEIGHT');assert weight;z0=build['bodyCutWorldZ'];z1=build['headCutWorldZ'];boundary=[v for v in bm.verts if abs(v.co.z-z0)<2e-7];layers=list(bm.loops.layers.uv.values());nativeLayers=[l for l in layers if l.name!='AngelicaOriginalUV'];snap=[]
 for v in boundary:
  sourceLoops=[loop for loop in v.link_loops if loop.face.material_index!=index and all(p.co.z<=z0+2e-7 for p in loop.face.verts)];assert sourceLoops;snap.append((v.co.copy(),float(v[weight]),{layer.name:sourceLoops[0][layer].uv.copy() for layer in nativeLayers}))
 # Same shared angular partition: each new junction vertex lies on the ruled
 # segment from one exact native boundary vertex to its source-head partner.
 lineage=np.load(E/'individual-head-neck-lineage.npz');rings=lineage['bridgePoints'].reshape(5,-1,3);nativeLookup={tuple(np.round(np.array(co,dtype="f8"),7)):(w,uv) for co,w,uv in snap};nativeUV=[]
 for co in rings[0]:
  key=tuple(np.round(co,7));assert key in nativeLookup;nativeUV.append(nativeLookup[key])
 count=0
 for face in bm.faces:
  if face.material_index!=index:continue
  for loop in face.loops:
   co=np.array(loop.vert.co[:]);distance=np.linalg.norm(rings-co,axis=2);j,i=np.unravel_index(np.argmin(distance),distance.shape);assert distance[j,i]<3e-7;w,uv=nativeUV[i];loop.vert[weight]=w
   for layer in nativeLayers:loop[layer].uv=uv[layer.name]
  count+=1
 bm.to_mesh(skin.data);bm.free();skin.data.materials[index]=patch;skin.data.update();bpy.context.view_layer.update();_,after,afterT=b.u.b.geom(skin);assert np.array_equal(W,after) and np.array_equal(T,afterT);bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=False);a.save('a2-build-summary.json',build|{'source':str(SRC),'sourceSha256':a.a.sha(SRC),'output':str(OUT),'sha256':a.a.sha(OUT),'bytes':OUT.stat().st_size,'repair':'Exact original native-body and artist-head shader graphs mixed only on1320 neck faces; preserve each source UV and original body color-weight at all junction loops. No geometry/source texture/scalar/render changes. Head normal-map tangent UV explicitly restored to its original artist chart after joining to the body.','actualGeometryAndTrianglesExactlyPreserved':True,'correctedNeckFaces':count,'headNormalMapUVBefore':artistNormalMaps,'headNormalMapUVAfter':'AngelicaOriginalUV','originalBodySourceUVLayersExtendedOnJunction':[x.name for x in skin.data.uv_layers if x.name!='AngelicaOriginalUV'],'secondsBeforePreview':time.time()-tick});rows=[]
 for view in ['face','body-face','profile','oblique','back']:
  rows.append(b.u.v.image('a2-source-material-neck',view));a.save('a2-view-controls.json',rows)
 print('R126_COMPLETE_EXACT_SOURCE_NECK_MATERIAL_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
