"""Independent whole source recovery after two visible material failures."""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,time
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0131-native-hair-material';S=R/'engine/assets/characters/female-next/source';SRC=S/'r0126-source/aevrynd-female-next-r0126-b-source-section-neck.blend'
sp=importlib.util.spec_from_file_location('r131verify',Path(__file__).with_name('build-female-next-r0131-native-hair-material.py'));c=importlib.util.module_from_spec(sp);sp.loader.exec_module(c);a=c.a;b=c.b;q=c.q
def save(n,x):(E/n).write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def geom():
 out={}
 for key,name in [('skin','AFN126_COMPLETE_WOMAN_BODY_AND_ARTIST_HEAD'),('hair','AFN126_ORIGINAL_Hair_Hair_0')]:
  o=bpy.data.objects[name];_,W,T=b.u.b.geom(o);out[key+'World']=a.hasharray(W);out[key+'Triangles']=a.hasharray(T)
 out['hairUV']=a.hasharray(q.arr(bpy.data.objects['AFN126_ORIGINAL_Hair_Hair_0'].data.uv_layers.active.data,'uv',len(bpy.data.objects['AFN126_ORIGINAL_Hair_Hair_0'].data.loops),2));return out
def main():
 tick=time.time();bpy.ops.wm.open_mainfile(filepath=str(SRC));baseline=geom();protected=a.protected();oldHair=bpy.data.objects['AFN126_ORIGINAL_Hair_Hair_0'].data.materials[0];oldHairName=oldHair.name;oldGraphs={m.name:c.signature(m) for m in bpy.data.materials};baseShader=next(n for n in oldHair.node_tree.nodes if n.type=='BSDF_PRINCIPLED');baseLink=baseShader.inputs['Base Color'].links[0];alphaLink=baseShader.inputs['Alpha'].links[0];baseGraph={'node':baseLink.from_node.name,'signature':c.signature(oldHair)['nodes']};alphaNode=alphaLink.from_node.name;colourNode=baseLink.from_node.name;results={}
 for tag in ['a','b']:
  build=json.loads((E/(tag+'-build-summary.json')).read_text('utf-8'));src=Path(build['output']);assert a.sha(src)==build['sha256'];bpy.ops.wm.open_mainfile(filepath=str(src));assert geom()==baseline==build['actualGeometryHashes'];assert a.protected()==protected;hair=bpy.data.objects['AFN126_ORIGINAL_Hair_Hair_0'];mat=hair.data.materials[0];assert mat.name==build['newMaterial'];missing=[n for n in oldGraphs if n not in bpy.data.materials];assert all(n==oldHairName for n in missing);assert all(c.signature(bpy.data.materials[n])==v for n,v in oldGraphs.items() if n in bpy.data.materials);coverage=mat.node_tree.nodes['AFN131_EXACT_ORIGINAL_ALPHA_COVERAGE'];assert coverage.inputs[0].links[0].from_node.name==alphaNode
  # Original diffuse/alpha source subgraphs and every source image remain exact.
  originalNodes={n['name']:n for n in baseGraph['signature']};newNodes={n['name']:n for n in c.signature(mat)['nodes']}
  for n,row in originalNodes.items():
   if row['type']!='ShaderNodeBsdfPrincipled':assert newNodes[n]==row,n
  assert colourNode in mat.node_tree.nodes and alphaNode in mat.node_tree.nodes;images=[]
  for im in bpy.data.images:
   if im.source=='FILE' and not im.packed_file and im.filepath:
    p=Path(bpy.path.abspath(im.filepath));assert p.is_file();images.append({'relative':im.filepath,'absolute':str(p),'sha256':a.sha(p),'bytes':p.stat().st_size})
  skin=bpy.data.objects['AFN126_COMPLETE_WOMAN_BODY_AND_ARTIST_HEAD'];assert not skin.data.shape_keys and not any(md.type=='ARMATURE' for md in skin.modifiers);assert a.sha(src)==build['sha256'];results[tag]={'source':str(src),'sha256':build['sha256'],'bytes':src.stat().st_size,'independentlyReopened':True,'actualVisibleHeadBodyHairWorldTrianglesAndHairUVExactlyMatchOriginalR126':True,'allHiddenOldRollbackShapeKeysFibresAndRadiiExact':True,'allOtherOriginalMaterialGraphsExact':True,'unreferencedOriginalHairMaterialMissingInCandidate':missing,'originalDiffuseAndCoverageSubgraphNodesExact':True,'currentVisibleHeadHasOwnFaceRigOrMorphs':False,'allReferencedExternalTextures':images,'sourceMaterialOnlyNoNewCompleteOperationAccepted':True,'naturalHairMotionFiniteSelfContinuousContactRuntimeAccepted':False};save('minimum-saved-native-material-readback.json',{'sources':results,'scope':'Actual source recovery and exact protected geometry/colour/coverage data only. A chrome-card and B darkened-card appearances rejected; no complete operation or collision/runtime acceptance.','seconds':time.time()-tick})
 print('R131_COMPLETE_MATERIAL_SOURCES_INDEPENDENTLY_RECOVERED',time.time()-tick,flush=True)
if __name__=='__main__':main()
