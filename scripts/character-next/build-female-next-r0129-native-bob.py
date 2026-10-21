"""Complete native strand bob from explicitly authored current-scalp guides.
No foreign root fit, UV strip conversion, radial growth or source-card shader
sweep. Intrinsic current-scalp interpolation fills the directly authored style.
"""
from pathlib import Path
import bpy,numpy as np,json,datetime,time,heapq,importlib.util
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0129-native-authored-bob';PRE=E.parent/'r0127-native-lid-closure';S=R/'engine/assets/characters/female-next/source';SRC=S/'r0129-source/aevrynd-female-next-r0129-a-native-bob-guide-authoring.blend';OUT=S/'r0129-source/aevrynd-female-next-r0129-b-native-strand-bob.blend';COUNT=24000;N=41
sp=importlib.util.spec_from_file_location('r129base',Path(__file__).with_name('author-female-next-r0129-bob-guides.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);b=a.b;q=a.a.q;b.u.v.E=E;m=b.u.m
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.tolist() if isinstance(a,np.ndarray) else a.item())+'\n',encoding='utf-8')
def attr(data,name,kind,domain,values):
 at=data.attributes.get(name) or data.attributes.new(name,kind,domain);at.data.foreach_set('vector' if kind=='FLOAT_VECTOR' else 'value',np.asarray(values,dtype='i4' if kind=='INT' else 'f4').ravel())
def live_guides(hair,guide):
 ng,n,L=m.interface('AFN129_EXPLICIT_NATIVE_GUIDES_TO_VISIBLE_STRANDS');inp=n.new('NodeGroupInput');out=n.new('NodeGroupOutput');info=n.new('GeometryNodeObjectInfo');info.transform_space='RELATIVE';info.inputs['Object'].default_value=guide;position=n.new('GeometryNodeInputPosition')
 def named(name,kind):
  at=n.new('GeometryNodeInputNamedAttribute');at.data_type=kind;at.inputs['Name'].default_value=name;return at.outputs['Attribute']
 def vec(op,A,B=None,scale=None):
  nd=n.new('ShaderNodeVectorMath');nd.operation=op;L.new(A,nd.inputs[0])
  if B is not None:L.new(B,nd.inputs[1])
  if scale is not None:L.new(scale,nd.inputs['Scale'])
  return nd.outputs['Vector']
 total=None
 for j in range(4):
  node=n.new('GeometryNodeSampleIndex');node.data_type='FLOAT_VECTOR';node.domain='POINT';node.clamp=False;L.new(info.outputs['Geometry'],node.inputs['Geometry']);L.new(position.outputs['Position'],node.inputs['Value']);L.new(named('AFN129_GuidePoint'+str(j),'INT'),node.inputs['Index']);term=vec('SCALE',node.outputs['Value'],scale=named('AFN129_GuideWeight'+str(j),'FLOAT'));total=term if total is None else vec('ADD',total,term)
 offset=vec('SUBTRACT',total,named('AFN129_RestGuideAtPoint','FLOAT_VECTOR'));offset=vec('SCALE',offset,scale=named('AFN129_FreeGuideEditWeight','FLOAT'));setpos=n.new('GeometryNodeSetPosition');L.new(inp.outputs['Geometry'],setpos.inputs['Geometry']);L.new(vec('ADD',position.outputs['Position'],offset),setpos.inputs['Position']);L.new(setpos.outputs['Geometry'],out.inputs['Geometry']);md=hair.modifiers.new('AFN129_LIVE_EXPLICIT_GUIDE_EDITS','NODES');md.node_group=ng
def main():
 tick=time.time();assert not OUT.exists();save('strand-groom-authoring-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'action':'Fill actual source-native scalp using31 explicitly authored3D bob guides and live rooted visible strands. One fixed construction and shader, no sweep.'});bpy.ops.wm.open_mainfile(filepath=str(SRC));oldProtected=a.a.protected();skin=bpy.data.objects['AFN126_COMPLETE_WOMAN_BODY_AND_ARTIST_HEAD'];_,W,BT=b.u.b.geom(skin);W=W.copy();BT=BT.copy();currentSkin={'world':a.a.hasharray(W),'triangles':a.a.hasharray(BT)};data=np.load(PRE/'native-head-topology.npz');P=data['world'];T=data['triangles'];cap=np.load(E/'authored-native-scalp-domain.npz')['nativeScalpFaceIds'];line=np.load(E/'authored-native-guide-lineage.npz');G=line['guideWorld'].astype('f4');records=json.loads((E/'authored-native-bob-guides.json').read_text('utf-8'));guide=bpy.data.objects['AFN129_EXPLICIT_41_POINT_BOB_GUIDES'];nativeToActual=dict(line['nativeSourceToActualTriangle']);pointIds=line['actualSkinNativePointIds'];adj=[{} for p in P]
 for face in T[cap]:
  for i,j in zip(face,np.roll(face,-1)):weight=float(np.linalg.norm(P[i]-P[j]));adj[i][int(j)]=weight;adj[j][int(i)]=weight
 D=np.full((len(G),len(P)),np.inf,dtype='f4')
 for gi,row in enumerate(records):
  start=row['pickedNativeScalpVertex'];D[gi,start]=0.;heap=[(0.,int(start))]
  while heap:
   ds,i=heapq.heappop(heap)
   if ds>float(D[gi,i])+1e-7:continue
   for j,w in adj[i].items():
    nd=ds+w
    if nd<float(D[gi,j]):D[gi,j]=nd;heapq.heappush(heap,(float(D[gi,j]),j))
 rng=np.random.default_rng(12924031);tri=P[T[cap]];areas=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)*.5;chosen=rng.choice(cap,COUNT,p=areas/areas.sum());uv=rng.random((COUNT,2));s=np.sqrt(uv[:,0]);nativeBary=np.c_[1-s,s*(1-uv[:,1]),s*uv[:,1]];nativeIds=T[chosen];actualTriangleIds=np.array([nativeToActual[int(fi)] for fi in chosen],dtype=np.int32);rootTri=BT[actualTriangleIds];actualNative=pointIds[rootTri];bary=np.empty((COUNT,3))
 for j in range(3):bary[:,j]=nativeBary[np.arange(COUNT),(nativeIds==actualNative[:,j,None]).argmax(1)]
 roots=np.einsum('ij,ijk->ik',bary,W[rootTri]);edgeT=W[rootTri[:,1]]-W[rootTri[:,0]];edgeT/=np.linalg.norm(edgeT,axis=1)[:,None];normal=np.cross(W[rootTri[:,1]]-W[rootTri[:,0]],W[rootTri[:,2]]-W[rootTri[:,0]]);normal/=np.linalg.norm(normal,axis=1)[:,None];bitangent=np.cross(normal,edgeT);radius=rng.uniform(.000028,.000042,COUNT);rootCenter=roots+normal*radius[:,None];dist=(D[:,nativeIds]*nativeBary[None,:,:]).sum(2).T;groups=np.array([r['region'] for r in records]);rootRegion=np.where(roots[:,1]>.026,'B',np.where(roots[:,0]<0,'L','R'));dist[groups[None,:]!=rootRegion[:,None]]=np.inf;parents=np.argpartition(dist,3,axis=1)[:,:4];pd=np.take_along_axis(dist,parents,axis=1);assert np.isfinite(pd).all();weights=1./(pd+.002)**2;weights/=weights.sum(1)[:,None];base=np.zeros((COUNT,N,3),dtype='f4')
 for j in range(4):base+=G[parents[:,j]]*weights[:,j,None,None].astype('f4')
 t=np.linspace(0,1,N);clump=.2*(t*t*(3-2*t));offset=(rootCenter-base[:,0])[:,None,:]*(1-clump)[None,:,None];C=base.astype(float)+offset;phase=rng.uniform(0,2*np.pi,COUNT);phase2=rng.uniform(0,2*np.pi,COUNT);fade=np.sin(.5*np.pi*t)**2;wiggle=.0003*(np.sin(9*np.pi*t[None,:]+phase[:,None])-np.sin(phase[:,None]))*fade;wiggle2=.0002*(np.sin(7*np.pi*t[None,:]+phase2[:,None])-np.sin(phase2[:,None]))*fade;C+=wiggle[:,:,None]*edgeT[:,None,:]+wiggle2[:,:,None]*bitangent[:,None,:];C[:,:,2]+=rng.uniform(-.008,.010,COUNT)[:,None]*(t**4)[None,:];C[:,0]=rootCenter
 assert np.isfinite(C).all() and abs(C[:,:,0]).max()<.18 and C[:,:,2].max()<1.65 and C[:,:,2].min()>1.30
 curves=bpy.data.hair_curves.new('AFN129_NATIVE_STRAND_BOB_DATA');curves.add_curves([N]*COUNT);curves.position_data.foreach_set('vector',C.astype('f4').ravel());tip=np.clip((t-.8)/.2,0,1);profile=1-.94*tip*tip*(3-2*tip);radii=radius[:,None]*profile[None,:];attr(curves,'radius','FLOAT','POINT',radii)
 for j in range(4):attr(curves,'AFN129_GuidePoint'+str(j),'INT','POINT',parents[:,j,None]*N+np.arange(N)[None,:]);attr(curves,'AFN129_GuideWeight'+str(j),'FLOAT','CURVE',weights[:,j])
 attr(curves,'AFN129_RestGuideAtPoint','FLOAT_VECTOR','POINT',base);free=np.ones((COUNT,N));free[:,0]=0;attr(curves,'AFN129_FreeGuideEditWeight','FLOAT','POINT',free)
 for j in range(3):attr(curves,'AFN97_ScalpVertex'+str(j),'INT','CURVE',rootTri[:,j])
 for name,value in [('RootBarycentric',bary),('RestRoot',rootCenter),('RestT',edgeT),('RestB',bitangent),('RestN',normal)]:attr(curves,'AFN97_'+name,'FLOAT_VECTOR','CURVE',value)
 attr(curves,'AFN97_RootRadiusNative','FLOAT','CURVE',radius);attr(curves,'AFN129_SourceScalpTriangle','INT','CURVE',actualTriangleIds);curves.surface=skin;curves.surface_uv_map='AngelicaOriginalUV';hair=bpy.data.objects.new('AFN129_NATIVE_AUTHORED_VISIBLE_BOB',curves);bpy.context.scene.collection.objects.link(hair);live_guides(hair,guide);b.u.root_modifier(hair,skin);hair.modifiers[-1].name='AFN129_ACTUAL_SKIN_BARYCENTRIC_ROOT_FRAMES';hair.modifiers[-1].node_group.name='AFN129_NATIVE_BODY_ROOT_FRAME_TRANSPORT'
 mat=bpy.data.materials.new('AFN129_NATIVE_PHYSICAL_BROWN_HAIR');mat.use_nodes=True;nodes=mat.node_tree.nodes;nodes.clear();output=nodes.new('ShaderNodeOutputMaterial');shader=nodes.new('ShaderNodeBsdfHairPrincipled');shader.parametrization='MELANIN'
 for name,value in [('Melanin',.55),('Melanin Redness',.12),('Roughness',.36),('Radial Roughness',.48),('Coat',.04),('Random Color',.18),('Random Roughness',.12),('IOR',1.55)]:
  if shader.inputs.get(name):shader.inputs[name].default_value=value
 mat.node_tree.links.new(shader.outputs[0],output.inputs['Surface']);curves.materials.append(mat);oldHair=bpy.data.objects['AFN126_ORIGINAL_Hair_Hair_0'];oldHair.hide_render=True;oldHair.hide_set(True);bpy.context.view_layer.update();actual=q.hair(hair).reshape(C.shape);error=float(np.linalg.norm(actual-C,axis=2).max());assert np.isfinite(actual).all() and error<5e-6,error;assert oldProtected==a.a.protected();_,after,AT=b.u.b.geom(skin);assert currentSkin=={'world':a.a.hasharray(after),'triangles':a.a.hasharray(AT)}
 hair['scope']='All24000 visible native fibres follow31 actual explicit guides and independently source-bound current skin roots. Initial artist radii/colour/cut distribution, not biological calibration. Static appearance pending; no natural dynamics/finite/continuous contact/runtime acceptance.';hair['sourceCredit']='Original Angelica / DarkNik, original NikZava284, CC-BY4.0 silhouette/skin reference retained; new Aevrynd guide/strand construction, no exclusive ownership claim.';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=False);np.savez_compressed(E/'native-bob-strand-lineage.npz',guideWorld=G,chosenNativeScalpTriangles=chosen,actualSkinTriangleIds=actualTriangleIds,actualSkinVertexIds=rootTri,rootBarycentric=bary,actualRootSurfaceWorld=roots,actualRootNormals=normal,rootCenterWorld=rootCenter,childGuideIds=parents,childGuideWeights=weights,rootRadii=radius,authoredStrandWorld=C.astype('f4'))
 save('b-build-summary.json',{'source':str(SRC),'sourceSha256':a.a.sha(SRC),'output':str(OUT),'sha256':a.a.sha(OUT),'bytes':OUT.stat().st_size,'hairObject':hair.name,'guideObject':guide.name,'actualSkinObject':skin.name,'curves':COUNT,'pointsEach':N,'actualPoints':COUNT*N,'actualGuides':len(G),'actualSkinCurrentHashes':currentSkin,'oldHiddenRollbackExact':oldProtected==a.a.protected(),'allRootBarycentricBounded':bool(np.all(bary>=0)),'actualRestAgainstAuthoredMaxErrorM':error,'exactSourceScalpFaces':len(cap),'sourceScalpAreaM2':float(areas.sum()),'initialRadiusRangeM':[float(radius.min()),float(radius.max())],'nativeCurveTypeAttribute':str(curves.attributes.get('curve_type')),'newShaderInputs':{n.name:list(n.default_value) if hasattr(n.default_value,'__len__') else n.default_value for n in shader.inputs if hasattr(n,'default_value')},'noOldSourceCardGeometryOrEmissionRendered':True,'oldSourceHairPreservedHidden':True,'rootTransportUsesCurrentVisibleSkinNotOldHiddenBody':True,'noHairRemovedClippedOrRadiusRetunedAfterContactCheck':True,'fullNaturalMotionFiniteSelfContinuousContactAndRuntimeUnaccepted':True,'secondsBeforePreview':time.time()-tick});rows=[]
 for view in ['face','body-face','profile','oblique','back']:rows.append(b.u.v.image('b-native-strand-bob',view));save('b-view-controls.json',rows)
 print('R129_COMPLETE_NATIVE_STRAND_BOB_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
