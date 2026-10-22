"""Root-first current-scalp flow with actual triangle-neighbour interpolation.
The scalp chart addresses the current surface; it is not a hair UV contour.
"""
from pathlib import Path
import bpy,numpy as np,math,json,time,datetime,importlib.util
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0142-scalp-adjacent-flow';S=R/'engine/assets/characters/female-next/source'
SRC=S/'r0139-source/aevrynd-female-next-r0139-a-native-lid-follow.blend';OUT=S/'r0142-source/aevrynd-female-next-r0142-a-scalp-adjacent.blend';N=33
sp=importlib.util.spec_from_file_location('r142native',Path(__file__).with_name('build-female-next-r0141-authored-parting.py'));h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h);a=h.a;a.b.u.v.E=E
def save(n,x):
 (E/n).write_bytes((json.dumps(x,indent=2,default=lambda q:q.tolist() if isinstance(q,np.ndarray) else q.item() if isinstance(q,np.generic) else str(q))+'\n').encode())
def direction(uv,side):
 q=float(np.clip((.10-uv[1])/.45,0,1));q=q*q*(3-2*q);v=np.array([side*q,.25+.75*(1-q)]);return v/np.linalg.norm(v)
def resample(Q,n):
 arc=np.r_[0,np.linalg.norm(np.diff(Q,axis=0),axis=1).cumsum()];assert arc[-1]>1e-6
 return np.column_stack([np.interp(np.linspace(0,arc[-1],n),arc,Q[:,j]) for j in range(3)])
def three_guide_modifier(hair,skin,guides):
 h.b.gn(hair,skin,guides);ng=hair.modifiers[-1].node_group;ng.name='AFN142_CURRENT_SKIN_AND_SCALP_TRIANGLE_GUIDES';hair.modifiers[-1].name='AFN142_ACTUAL_SCALP_TRIANGLE_NEIGHBOURS';nodes=ng.nodes;L=ng.links
 rest=next(x for x in nodes if x.bl_idname=='GeometryNodeInputNamedAttribute' and x.inputs['Name'].default_value=='AFN140_GuideRest')
 subtract=next(link.to_node for link in rest.outputs['Attribute'].links if link.to_node.operation=='SUBTRACT');old=subtract.inputs[0].links[0].from_socket
 obj=next(x for x in nodes if x.bl_idname=='GeometryNodeObjectInfo' and x.inputs['Object'].default_value==guides);pos=next(x for x in nodes if x.bl_idname=='GeometryNodeInputPosition')
 index=nodes.new('GeometryNodeInputNamedAttribute');index.data_type='INT';index.inputs['Name'].default_value='AFN142_GuideIndex2'
 weight=nodes.new('GeometryNodeInputNamedAttribute');weight.data_type='FLOAT';weight.inputs['Name'].default_value='AFN142_GuideWeight2'
 sample=nodes.new('GeometryNodeSampleIndex');sample.data_type='FLOAT_VECTOR';sample.domain='POINT';L.new(obj.outputs['Geometry'],sample.inputs['Geometry']);L.new(pos.outputs['Position'],sample.inputs['Value']);L.new(index.outputs['Attribute'],sample.inputs['Index'])
 delta=nodes.new('ShaderNodeVectorMath');delta.operation='SUBTRACT';L.new(sample.outputs['Value'],delta.inputs[0]);L.new(old,delta.inputs[1]);scale=nodes.new('ShaderNodeVectorMath');scale.operation='SCALE';L.new(delta.outputs['Vector'],scale.inputs[0]);L.new(weight.outputs['Attribute'],scale.inputs['Scale']);add=nodes.new('ShaderNodeVectorMath');add.operation='ADD';L.new(old,add.inputs[0]);L.new(scale.outputs['Vector'],add.inputs[1]);L.new(add.outputs['Vector'],subtract.inputs[0])
def main():
 tick=time.time();assert not OUT.exists();bpy.ops.wm.open_mainfile(filepath=str(SRC));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update()
 if not (E/'direct-scalp-root-authoring-start.json').exists():save('direct-scalp-root-authoring-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originalStartedUTC':'2026-10-21T23:57:00+00:00','action':'Author root-first current-scalp curves from actual native vertices/tangential surface flow and open free shafts; children use their actual scalp triangles and barycentrics. No free-path root projection, nearest-root guide assignment, old hair UV contour, foreign fit, normal-outward Add/global Comb or closed loft.'})
 protected=a.a.protected();skin=bpy.data.objects[a.FIXED[0]];old=bpy.data.objects[a.FIXED[1]];W,T=a.geometry(skin);fixed={n:[a.a.hasharray(x) for x in a.geometry(bpy.data.objects[n])] for n in a.FIXED+a.MOVING}
 chart=np.load(E.parent/'r0133-anatomical-scalp-chart/target-scalp-chart.npz');K=KDTree(len(W))
 for i,p in enumerate(W):K.insert(Vector(p),i)
 K.balance();matches=[K.find(Vector(p)) for p in chart['world']];mapped=np.array([x[1] for x in matches],dtype='i4');mapError=max(x[2] for x in matches);assert mapError<1e-6
 rootW=W[mapped];UV=chart['uv'];lookup={tuple(sorted(f)):i for i,f in enumerate(T)};scalpFaces=np.array([lookup[tuple(sorted(mapped[f]))] for f in chart['triangles']],dtype='i4');tri=T[scalpFaces];localLookup={int(j):i for i,j in enumerate(mapped)};localTri=np.array([[localLookup[int(v)] for v in f] for f in tri],dtype='i4');A=UV[localTri];B=rootW[localTri];inv=np.linalg.inv(np.stack([A[:,1]-A[:,0],A[:,2]-A[:,0]],axis=2));fn=np.cross(B[:,1]-B[:,0],B[:,2]-B[:,0]);area=np.linalg.norm(fn,axis=1)*.5;fn/=np.linalg.norm(fn,axis=1)[:,None]
 vn=np.zeros_like(rootW)
 for j in range(3):np.add.at(vn,localTri[:,j],fn*area[:,None])
 vn/=np.linalg.norm(vn,axis=1)[:,None];uv3=np.column_stack([UV,np.zeros(len(UV))]);uvBVH=BVHTree.FromPolygons([Vector(p) for p in uv3],localTri.tolist(),all_triangles=True)
 def at(uv):
  pt,no,f,d=uvBVH.find_nearest(Vector((float(uv[0]),float(uv[1]),0.)));co=inv[f]@(np.asarray(pt)[:2]-A[f,0]);bc=np.array([1-co.sum(),*co]);n=bc@vn[localTri[f]];n/=np.linalg.norm(n);return bc@B[f],n,float(d)
 guides=[];nativeIds=[];sides=[];guideIndex={};records=[]
 def make_guide(i,side):
  split=abs(UV[i,0])<1e-7 and UV[i,1]<.10;key=(int(i),int(side) if split else 0)
  if key in guideIndex:return guideIndex[key]
  root=rootW[i].copy();uv=UV[i].copy();surface=[root.copy()];normals=[vn[i].copy()];uvs=[uv.copy()]
  for step in range(100):
   d=direction(uv,side);middle=uv+d*.0175;goal=uv+direction(middle,side)*.035;p,n,outside=at(goal)
   if outside>1e-6:
    lo=uv.copy();hi=goal.copy()
    for _ in range(14):
     mid=(lo+hi)*.5
     if at(mid)[2]>1e-7:hi=mid
     else:lo=mid
    if np.linalg.norm(lo-uv)>1e-5:
     p,n,_=at(lo);surface.append(p);normals.append(n);uvs.append(lo)
    break
   uv=goal;surface.append(p);normals.append(n);uvs.append(uv.copy())
  surface=np.array(surface);normals=np.array(normals);arc=np.r_[0,np.linalg.norm(np.diff(surface,axis=0),axis=1).cumsum()];rho=float(np.clip(np.linalg.norm(UV[i]),0,1));volume=.004+.003*(1-rho*rho);lift=.000035+volume*(1-np.exp(-arc/.025));Q=surface+normals*lift[:,None]
  if len(Q)>1:tangent=Q[-1]-Q[-2]
  else:
   inside=UV[i]-direction(UV[i],side)*.01;p,n,_=at(inside);tangent=root-p
  tangent/=max(np.linalg.norm(tangent),1e-20);tipZ=1.325+.008*float(UV[i,1])+.002*rho;radial=normals[-1].copy();radial[2]=0;radial/=max(np.linalg.norm(radial),1e-20);outer=.010+.018*(1-rho);p0=Q[-1];p1=p0+tangent*.024;p2=p0+radial*(outer+.009);p2[2]=tipZ+.035;p3=p0+radial*outer;p3[2]=tipZ;t=np.linspace(0,1,29)[:,None];free=(1-t)**3*p0+3*(1-t)**2*t*p1+3*(1-t)*t*t*p2+t**3*p3;full=resample(np.concatenate([Q,free[1:]],axis=0),N);full[0]=root+vn[i]*.000035
  g=len(guides);guideIndex[key]=g;guides.append(full);nativeIds.append(i);sides.append(side);records.append({'guide':g,'actualNativeVertex':int(mapped[i]),'chartVertex':int(i),'partSide':int(side),'rootWorld':root,'surfaceFlowStations':len(surface),'surfaceArcM':float(arc[-1]),'rootRelocationM':0.,'rootFirstTangentAndLocalVolume':True,'tipZ':tipZ});return g
 # Guide topology is the actual current scalp tessellation, with a declared part split only.
 faceSides=np.where(UV[localTri].mean(1)[:,0]<0,-1,1);faceGuides=np.array([[make_guide(int(i),int(side)) for i in f] for f,side in zip(localTri,faceSides)],dtype='i4');P=np.array(guides);gd=bpy.data.hair_curves.new('AFN142_ROOT_FIRST_SCALP_NEIGHBOUR_GUIDES');gd.add_curves([N]*len(P));gd.position_data.foreach_set('vector',P.astype('f4').ravel());gd.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',np.full(len(P)*N,.0001,dtype='f4'));guideOb=bpy.data.objects.new('AFN142_EDITABLE_CURRENT_SCALP_FLOW_GUIDES',gd);scene.collection.objects.link(guideOb);guideOb.hide_render=True;guideOb.hide_set(True)
 edgeMap={};bad=[];partEdges=[]
 for f,g in zip(localTri,faceGuides):
  for j,k in [(0,1),(1,2),(2,0)]:
   edge=tuple(sorted((int(f[j]),int(f[k]))));pair={int(f[j]):int(g[j]),int(f[k]):int(g[k])}
   if edge in edgeMap and edgeMap[edge]!=pair:
    if all(abs(UV[x,0])<1e-7 for x in edge) and any(UV[x,1]<.10 for x in edge):partEdges.append(edge)
    else:bad.append(edge)
   edgeMap[edge]=pair
 assert not bad,('undeclared scalp neighbour discontinuity',bad[:4])
 rng=np.random.default_rng(14261061);count=42000;ff=rng.choice(len(tri),count,p=area/area.sum());r=np.sqrt(rng.random(count));s=rng.random(count);bc=np.column_stack([1-r,r*(1-s),r*s]);roots=np.einsum('bi,bij->bj',bc,W[tri[ff]]);childUV=np.einsum('bi,bij->bj',bc,UV[localTri[ff]]);keep=~((abs(roots[:,0])<.0007)&(childUV[:,1]<.10));ff=ff[keep];bc=bc[keep];roots=roots[keep];childUV=childUV[keep];count=len(ff);ids=faceGuides[ff];center=np.einsum('bi,bijk->bjk',bc,P[ids]);V=center.copy();u=np.linspace(0,1,N);noise=rng.normal(size=(count,3));noise[:,2]*=.35;scale=np.full(count,.0007);scale[rng.random(count)<.015]=.003;V+=noise[:,None,:]*scale[:,None,None]*(u*(1-u))[None,:,None];V[:,:,2]+=rng.uniform(-.006,.006,count)[:,None]*u[None,:]**4;cn=fn[ff];V[:,0]=roots+cn*.000035
  # Native current-skin triangle frames remain separate from the new scalp adjacency construction.
 childTri=tri[ff];childB=W[childTri];ax=childB[:,1]-childB[:,0];ax/=np.linalg.norm(ax,axis=1)[:,None];az=np.cross(childB[:,1]-childB[:,0],childB[:,2]-childB[:,0]);az/=np.linalg.norm(az,axis=1)[:,None];ay=np.cross(az,ax);basis=np.stack([ax,ay,az],axis=2);local=np.einsum('bni,bij->bnj',V-roots[:,None,:],basis);data=bpy.data.hair_curves.new('AFN142_NATIVE_SCALP_TRIANGLE_INTERPOLATED_HAIR');data.add_curves([N]*count);data.position_data.foreach_set('vector',V.astype('f4').ravel())
 def attr(name,t,x,w=1):
  p=data.attributes.new(name,t,'POINT');p.data.foreach_set('vector' if w==3 else 'value',np.asarray(x,dtype='i4' if t=='INT' else 'f4').ravel())
 for j in range(3):
  attr('AFN140_SkinVertex'+str(j),'INT',np.repeat(childTri[:,j],N));attr('AFN140_RestAxis'+str(j),'FLOAT_VECTOR',np.repeat(basis[:,:,j],N,axis=0),3)
 for name,x in [('AFN140_RootBarycentric',np.repeat(bc,N,axis=0)),('AFN140_RootLocal',local),('AFN140_RestWorld',V),('AFN140_GuideRest',center)]:attr(name,'FLOAT_VECTOR',x,3)
 for j,name in enumerate(['AFN140_GuideIndex0','AFN140_GuideIndex1','AFN142_GuideIndex2']):attr(name,'INT',ids[:,j,None]*N+np.arange(N))
 weight01=bc[:,1]/np.maximum(bc[:,0]+bc[:,1],1e-20);attr('AFN140_GuideWeight','FLOAT',np.repeat(weight01,N));attr('AFN142_GuideWeight2','FLOAT',np.repeat(bc[:,2],N));attr('AFN140_FreeShaftWeight','FLOAT',np.tile(np.minimum(1,u/.18)**2,count));attr('radius','FLOAT',np.tile(.000035*(1-.96*u**5),count));attr('AFN140_Along','FLOAT',np.tile(u,count))
 hair=bpy.data.objects.new('AFN142_CURRENT_ROOT_FIRST_SCALP_FLOW_HAIR',data);scene.collection.objects.link(hair);three_guide_modifier(hair,skin,guideOb);mat=bpy.data.materials.new('AFN142_ORIGINAL_DARK_BROWN_NATIVE_FIBRE');mat.use_nodes=True;nodes=mat.node_tree.nodes;nodes.clear();shader=nodes.new('ShaderNodeBsdfHairPrincipled');shader.parametrization='MELANIN';shader.inputs['Melanin'].default_value=.90;shader.inputs['Melanin Redness'].default_value=.15;shader.inputs['Roughness'].default_value=.35;shader.inputs['Radial Roughness'].default_value=.45;out=nodes.new('ShaderNodeOutputMaterial');mat.node_tree.links.new(shader.outputs[0],out.inputs['Surface']);data.materials.append(mat);old.hide_render=True;old.hide_set(True);bpy.context.view_layer.update();error=float(np.linalg.norm(a.q.hair(hair)-V.reshape(-1,3),axis=1).max());assert error<4e-6,error
 for n,value in fixed.items():assert [a.a.hasharray(x) for x in a.geometry(bpy.data.objects[n])]==value,n
 assert a.a.protected()==protected
 hair['sourceCredit']='Original Aevrynd current-scalp-rooted tangential flow, native triangle-neighbour interpolation and new fibre geometry. Existing DarkNik/NikZava284 head/body/textures/hidden rollback and original license obligations retained. No reference photo, foreign hair mesh/texture or likeness adopted. AFN140 attributes reuse native edit/skin-frame infrastructure only.';hair['scope']='One complete unaccepted root-first scalp-flow candidate. No nearest free-path root projection, source-card medials or hair UV contour. UV addresses only the actual scalp surface; open hair follows local head tangents and free shafts. Natural dynamics, finite/self/continuous collision and actual engine operation unaccepted.'
 np.savez_compressed(E/'scalp-adjacent-flow-lineage.npz',guides=P,guideNativeChartVertex=np.array(nativeIds),guidePartSide=np.array(sides),actualNativeVertexIds=mapped,actualScalpFaces=scalpFaces,actualScalpLocalTriangles=localTri,actualScalpFaceGuideIndices=faceGuides,childRootFaces=scalpFaces[ff],childRootBarycentric=bc,childGuideIndices=ids,childGuideWeights=bc,childScalpUV=childUV)
 save('scalp-adjacent-flow-construction.json',{'actualHair':hair.name,'actualGuideObject':guideOb.name,'nativeGuideCount':len(P),'stations':N,'fibres':count,'points':count*N,'currentSkinScalpMappingMaxM':mapError,'actualRootRelocationMaxM':0.,'rootFirstNoNearestGuideOrFreePathRootAssignment':True,'undeclaredSharedEdgeGuideDiscontinuityCount':len(bad),'declaredPartSharedEdges':len(partEdges),'actualScalpTriangleCount':len(scalpFaces),'childInterpolation':'Barycentric three guide vertices belonging to the SAME actual current-skin triangle; per-point live native sampler, no nearest-root matching. Shared edge guide IDs agree except declared central part.','scalpChartUse':'Parameter address for open tangential flow on actual skin; not hair-card UV contours, foreign fit, normal-outward Add/global Comb or closed loft.','artistFlow':'Centre part front through crown, increasing backflow behind crown; actual-root tangent and smooth local4..7mm layer volume, open cubic free shaft to original inward-tip long bob.','guideRecords':records,'partWidthM':.0014,'partIsInitialAuthoredFollicleRegionNotFailedContactCulling':True,'actualNeutralEvaluationMaxErrorM':error,'numericEvaluationBoundNotContactToleranceM':4e-6,'sourceOldHairHiddenNoOpaqueUnderlay':True,'appearanceFunctionContactRuntimeAccepted':False,'secondsBeforePreview':time.time()-tick})
 bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=False);save('a-build-summary.json',{'source':str(SRC),'output':str(OUT),'sha256':a.a.sha(OUT),'bytes':OUT.stat().st_size,'actualHair':hair.name,'actualGuideObject':guideOb.name,'sourceOriginalHair':old.name,'nativeGuideCount':len(P),'fibres':count,'points':count*N,'currentProtectedAllOtherGeometryAndHiddenRollbackExact':True,'originalGazeRigActionLidDriversAndOriginalMaterialsRetained':True,'appearanceFunctionContactRuntimeNotYetAccepted':True,'oneCompleteCandidate':True,'secondsBeforePreview':time.time()-tick});views=[]
 for view in ['face','body-face','profile','oblique','back']:
  views.append(a.b.u.v.image('a-scalp-adjacent',view));save('a-view-controls.json',views)
 print('R142_COMPLETE_ROOT_FIRST_SCALP_ADJACENT_HEAD_BODY_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
