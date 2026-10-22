"""One actual generator-input and complete-curve dataset equivalence check."""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,hashlib,datetime
from mathutils.kdtree import KDTree
from mathutils import Vector
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');E=C/'evidence/character-female-next/r0171-actual-scalp-chart';sp=importlib.util.spec_from_file_location('r171inputs',C/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);h=m.h;b=json.loads((E/'before.json').read_text());assert m.a.a.sha(Path(b['source']))==b['sourceSha256'];bpy.ops.wm.open_mainfile(filepath=b['source']);s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();hair=bpy.data.objects['AFN170_ACTUAL_ROOT_CONSTRAINED_NATIVE_GROOM'];carrier=bpy.data.objects['AFN170_ROOT_CONSTRAINED_ANATOMICAL_CARRIER']
def snapshot():
 P,offset=m.curveworld(hair);ev=hair.evaluated_get(bpy.context.evaluated_depsgraph_get());d=ev.data;r=h.arr(d.attributes['radius'].data,'value',len(P));end=np.r_[offset[1:],len(P)];hashes=[];shape=[]
 for x,y in zip(offset,end):hashes.append(hashlib.sha256(P[x:y].astype('<f4').tobytes()+r[x:y].astype('<f4').tobytes()).hexdigest());shape.append(y-x)
 attrs=[(a.name,a.domain,a.data_type) for a in d.attributes];uv=d.attributes.get('surface_uv_coordinate');U=h.arr(uv.data,'vector',len(uv.data),2) if uv and uv.domain=='CURVE' else None
 return P,offset,r,sorted(hashes),shape,attrs,U
A=snapshot();hair.update_tag();carrier.update_tag();bpy.context.view_layer.update();B=snapshot();sameShape=A[4]==B[4];indexError=float(np.linalg.norm(A[0]-B[0],axis=1).max()) if A[0].shape==B[0].shape else None;exactMultiset=A[3]==B[3];uvMatch=None
if A[6] is not None and B[6] is not None:
 kd=KDTree(len(B[6]))
 for i,p in enumerate(B[6]):kd.insert(Vector((p[0],p[1],0)),i)
 kd.balance();indices=[];gaps=[]
 for p in A[6]:q,i,g=kd.find(Vector((p[0],p[1],0)));indices.append(i);gaps.append(g)
 if len(set(indices))==len(indices) and max(gaps)<1e-6:
  diffs=[]
  for i,j in enumerate(indices):
   ai=A[1][i];bi=B[1][j];na=A[4][i];nb=B[4][j]
   if na==nb:diffs.append(float(np.linalg.norm(A[0][ai:ai+na]-B[0][bi:bi+nb],axis=1).max()))
  uvMatch={'uniqueOneToOne':True,'maximumRootUVDelta':max(gaps),'maximumFullCurvePointDeltaM':max(diffs),'matchedCurves':len(diffs)}
groups={};visited=set()
def inspect(g):
 if g.name in visited:return
 visited.add(g.name);rows=[]
 for n in g.nodes:
  values={}
  for inp in n.inputs:
   if hasattr(inp,'default_value'):
    v=inp.default_value
    if isinstance(v,bpy.types.ID):values[inp.name]={'ID':v.name,'type':v.bl_rna.identifier}
    elif isinstance(v,(float,int,str,bool)):values[inp.name]=v
    else:values[inp.name]=str(v)
  rows.append({'name':n.name,'type':n.bl_idname,'defaults':values,'linkedInputs':[x.name for x in n.inputs if x.is_linked]})
  if n.bl_idname=='GeometryNodeGroup' and n.node_tree:inspect(n.node_tree)
 groups[g.name]={'nodes':rows,'links':[{'from':x.from_node.name,'socket':x.from_socket.name,'to':x.to_node.name,'input':x.to_socket.name} for x in g.links]}
for mod in hair.modifiers:
 if mod.type=='NODES' and mod.node_group:inspect(mod.node_group)
result={'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'actualNativeCurves':len(A[1]),'actualNativePoints':len(A[0]),'allCurvePointCountsEqual':sameShape,'rawPointIndexMaximumDeltaM':indexError,'exactCompletePositionRadiusCurveMultisetEqual':exactMultiset,'UVMatchedFullCurves':uvMatch,'geometryRepresentationScope':'Complete evaluated native curve control paths+radius. Type/other attributes listed separately; not exact renderer spline/depsgraph or motion proof.','attributes':A[5],'sourceCarrierVertexGroups':list(carrier.vertex_groups.keys()),'nativeNodeGroups':groups,'sourceFileNotResaved':True};(E/'actual-native-generator-and-curve-equivalence.json').write_bytes((json.dumps(result,indent=2)+'\n').encode());print('R171_ORIGINAL_GENERATOR_AND_DATASET_CHECK',json.dumps({k:v for k,v in result.items() if k!='nativeNodeGroups'}),flush=True)
