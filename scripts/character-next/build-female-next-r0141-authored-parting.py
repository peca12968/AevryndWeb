"""Original art-directed parted flow, not a reconstruction of old hair-card pieces."""
from pathlib import Path
import bpy,numpy as np,math,json,time,datetime,importlib.util
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0141-authored-parting-flow';S=R/'engine/assets/characters/female-next/source'
SRC=S/'r0139-source/aevrynd-female-next-r0139-a-native-lid-follow.blend';OUT=S/'r0141-source/aevrynd-female-next-r0141-a-authored-parting.blend'
sp=importlib.util.spec_from_file_location('r141native',Path(__file__).with_name('build-female-next-r0140-native-rooted-groom.py'));b=importlib.util.module_from_spec(sp);sp.loader.exec_module(b);a=b.a;a.b.u.v.E=E
N=33
def save(n,x):
 (E/n).write_bytes((json.dumps(x,indent=2,default=lambda q:q.tolist() if isinstance(q,np.ndarray) else q.item() if isinstance(q,np.generic) else str(q))+'\n').encode())
def smooth(knots,u):
 K=np.asarray(knots,dtype=float);t=np.clip(np.asarray(u),0,1)*(len(K)-1);i=np.minimum(t.astype(int),len(K)-2);f=(t-i)[:,None]
 A=K[np.maximum(i-1,0)];B=K[i];C=K[i+1];D=K[np.minimum(i+2,len(K)-1)]
 return .5*((2*B)+(-A+C)*f+(2*A-5*B+4*C-D)*f*f+(-A+3*B-3*C+D)*f*f*f)
def main():
 tick=time.time();assert not OUT.exists();bpy.ops.wm.open_mainfile(filepath=str(SRC));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update()
 save('direct-authored-parting-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originalStartedUTC':'2026-10-21T23:45:30+00:00','action':'Directly author original 3D centre-part/front/side/back root-to-tip control strokes, layer starts and parting domains on actual current scalp; dense native child curves blend neighbouring authored flows. Not old connected-component medials, UV contours, normal-outward comb, imported whole-style fit or closed loft.'})
 protected=a.a.protected();skin=bpy.data.objects[a.FIXED[0]];old=bpy.data.objects[a.FIXED[1]];W,T=a.geometry(skin)
 fixed={n:[a.a.hasharray(x) for x in a.geometry(bpy.data.objects[n])] for n in a.FIXED+a.MOVING}
 src=np.load(E.parent/'r0140-native-clump-roots/native-open-clump-guides.npz');scalpFaces=src['scalpFaces'];tris=T[scalpFaces];BVH=BVHTree.FromPolygons([Vector(p) for p in W],tris.tolist(),all_triangles=True)
 # Explicit independent three-dimensional artist control strokes for the positive side.
 # Coordinates are metres in the actual current woman's world frame, not foreign style fitting.
 rows=np.array([
 [[.001,-.124,1.532],[.012,-.130,1.548],[.043,-.128,1.550],[.074,-.112,1.520],[.092,-.099,1.468],[.098,-.092,1.409],[.097,-.087,1.355],[.091,-.080,1.323],[.089,-.072,1.321]],
 [[.001,-.096,1.555],[.017,-.101,1.575],[.049,-.100,1.570],[.078,-.092,1.541],[.096,-.082,1.485],[.103,-.072,1.423],[.103,-.061,1.361],[.098,-.054,1.322],[.094,-.049,1.318]],
 [[.001,-.060,1.568],[.020,-.061,1.588],[.054,-.061,1.579],[.083,-.055,1.548],[.104,-.046,1.490],[.113,-.035,1.423],[.111,-.026,1.362],[.102,-.020,1.326],[.096,-.016,1.323]],
 [[.001,-.020,1.570],[.019,-.018,1.588],[.053,-.013,1.577],[.082,-.006,1.545],[.103,.006,1.490],[.111,.016,1.425],[.108,.025,1.365],[.100,.031,1.329],[.093,.033,1.325]],
 [[.001,.015,1.557],[.018,.027,1.577],[.050,.041,1.562],[.079,.052,1.532],[.099,.061,1.482],[.106,.067,1.426],[.101,.073,1.370],[.092,.074,1.333],[.085,.073,1.328]],
 [[.001,.040,1.540],[.008,.063,1.546],[.015,.084,1.526],[.026,.101,1.491],[.033,.107,1.443],[.035,.108,1.391],[.032,.107,1.351],[.025,.100,1.323],[.020,.097,1.319]]],dtype=float)
 guides=[];groups=[];guideRootFaces=[];guideBary=[];strokeRecords=[]
 for sign in [-1,1]:
  for row,K0 in enumerate(rows):
   K=K0.copy();K[:,0]*=sign
   # Different scalp layer starts belong to the same continuous designed flow.
   for layer,start in enumerate([0.,.13,.27,.42,.56]):
    u=np.linspace(start,1,N);Q=smooth(K,u);pt,no,fi,dist=BVH.find_nearest(Vector(Q[0]));fi=int(scalpFaces[fi]);tri=T[fi];B=W[tri];co=np.linalg.lstsq(np.column_stack([B[1]-B[0],B[2]-B[0]]),np.array(pt)-B[0],rcond=None)[0];bc=np.maximum([1-co.sum(),*co],0);bc/=bc.sum();normal=np.cross(B[1]-B[0],B[2]-B[0]);normal/=np.linalg.norm(normal);root=bc@B
    Q+=(root+normal*.00004-Q[0])*(1-np.linspace(0,1,N))[:,None]**2
    # Rear layers share one domain after the part ends; left/right front never interpolate across the part.
    group=2 if row>=4 else (0 if sign<0 else 1)
    strokeRecords.append({'guide':len(guides),'side':sign,'flowRow':row,'layer':layer,'startOnAuthoredStroke':start,'domain':group,'rootTriangle':fi,'rootBarycentric':bc,'rootProjectionDistanceM':dist,'semanticRole':'new authored current-scalp root and continuous part-to-tip layer, not a source artist follicle'})
    guides.append(Q);groups.append(group);guideRootFaces.append(fi);guideBary.append(bc)
 P=np.array(guides);groups=np.array(groups);guideData=bpy.data.hair_curves.new('AFN141_ORIGINAL_PARTING_SIDE_BACK_GUIDES');guideData.add_curves([N]*len(P));guideData.position_data.foreach_set('vector',P.astype('f4').ravel());guideData.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',np.full(len(P)*N,.0001,dtype='f4'));guideOb=bpy.data.objects.new('AFN141_EDITABLE_PARTING_FLOW_GUIDES',guideData);scene.collection.objects.link(guideOb);guideOb.hide_render=True;guideOb.hide_set(True)
 rng=np.random.default_rng(14161061);area=np.linalg.norm(np.cross(W[tris[:,1]]-W[tris[:,0]],W[tris[:,2]]-W[tris[:,0]]),axis=1)*.5
 count=42000;fidx=rng.choice(len(tris),count,p=area/area.sum());fi=scalpFaces[fidx];tri=T[fi];r1=np.sqrt(rng.random(count));r2=rng.random(count);bc=np.column_stack([1-r1,r1*(1-r2),r1*r2]);roots=np.einsum('bi,bij->bj',bc,W[tri]);normals=np.cross(W[tri[:,1]]-W[tri[:,0]],W[tri[:,2]]-W[tri[:,0]]);normals/=np.linalg.norm(normals,axis=1)[:,None]
 # Original intentional centre part. This is a styled scalp region, not post-hoc culling of failed contacts.
 keep=~((np.abs(roots[:,0])<.0007)&(roots[:,1]<.014)&(roots[:,2]>1.53));fi=fi[keep];tri=tri[keep];bc=bc[keep];roots=roots[keep];normals=normals[keep];count=len(roots)
 childGroup=np.where(roots[:,1]>.014,2,np.where(roots[:,0]<0,0,1));ids=[];weights=[];maxdist=[]
 for root,group in zip(roots,childGroup):
  candidates=np.flatnonzero(groups==group);dd=np.linalg.norm(P[candidates,0]-root,axis=1);ii=np.argsort(dd)[:2];ii=candidates[ii];d=np.linalg.norm(P[ii,0]-root,axis=1);ww=1/np.maximum(d,.0002)**2;ww/=ww.sum();ids.append(ii);weights.append(ww[1]);maxdist.append(float(d.min()))
 ids=np.array(ids,dtype='i4');weights=np.array(weights);u=np.linspace(0,1,N);center=P[ids[:,0]]*(1-weights[:,None,None])+P[ids[:,1]]*weights[:,None,None];rootDelta=roots-center[:,0];V=center+rootDelta[:,None,:]*(1-.72*u)[None,:,None];V+=normals[:,None,:]*.00004*(1-u)[None,:,None]
 # Small coherent fibre variations retain original parting and large flow; no sinusoidal whole-style generator.
 v=rng.normal(0,1,(count,3));v[:,2]*=.35;V+=v[:,None,:]*.00045*(u*(1-u))[None,:,None];V[:,:,2]+=rng.uniform(-.008,.008,count)[:,None]*u[None,:]**3
 V[:,0]=roots+normals*.000035
 B=W[tri];ax=B[:,1]-B[:,0];ax/=np.linalg.norm(ax,axis=1)[:,None];az=np.cross(B[:,1]-B[:,0],B[:,2]-B[:,0]);az/=np.linalg.norm(az,axis=1)[:,None];ay=np.cross(az,ax);basis=np.stack([ax,ay,az],axis=2);local=np.einsum('bni,bij->bnj',V-roots[:,None,:],basis)
 data=bpy.data.hair_curves.new('AFN141_CURRENT_ORIGINAL_INTERPOLATED_HAIR');data.add_curves([N]*count);data.position_data.foreach_set('vector',V.astype('f4').ravel())
 def attr(n,t,x,w=1):
  p=data.attributes.new(n,t,'POINT');p.data.foreach_set('vector' if w==3 else 'value',np.asarray(x,dtype='i4' if t=='INT' else 'f4').ravel())
 for j in range(3):
  attr('AFN140_SkinVertex'+str(j),'INT',np.repeat(tri[:,j],N));attr('AFN140_RestAxis'+str(j),'FLOAT_VECTOR',np.repeat(basis[:,:,j],N,axis=0),3)
 for name,x in [('AFN140_RootBarycentric',np.repeat(bc,N,axis=0)),('AFN140_RootLocal',local),('AFN140_RestWorld',V),('AFN140_GuideRest',center)]:attr(name,'FLOAT_VECTOR',x,3)
 # The existing native two-index sampler now blends two parent guides at matching stations.
 for j in range(2):attr('AFN140_GuideIndex'+str(j),'INT',ids[:,j,None]*N+np.arange(N))
 attr('AFN140_GuideWeight','FLOAT',np.repeat(weights,N));attr('AFN140_FreeShaftWeight','FLOAT',np.tile(np.minimum(1,u/.18)**2,count));attr('radius','FLOAT',np.tile(.000035*(1-.96*u**5),count));attr('AFN140_Along','FLOAT',np.tile(u,count))
 hair=bpy.data.objects.new('AFN141_CURRENT_AUTHORED_PARTED_HAIR',data);scene.collection.objects.link(hair);b.gn(hair,skin,guideOb);hair.modifiers[-1].name='AFN141_CURRENT_SKIN_AND_TWO_FLOW_GUIDES';hair.modifiers[-1].node_group.name='AFN141_NATIVE_SKIN_FRAME_AND_NEIGHBOURING_GUIDE_BLEND'
 mat=bpy.data.materials.new('AFN141_ORIGINAL_DARK_BROWN_NATIVE_FIBRE');mat.use_nodes=True;nodes=mat.node_tree.nodes;nodes.clear();shader=nodes.new('ShaderNodeBsdfHairPrincipled');shader.parametrization='MELANIN';shader.inputs['Melanin'].default_value=.90;shader.inputs['Melanin Redness'].default_value=.15;shader.inputs['Roughness'].default_value=.35;shader.inputs['Radial Roughness'].default_value=.45;out=nodes.new('ShaderNodeOutputMaterial');mat.node_tree.links.new(shader.outputs[0],out.inputs['Surface']);data.materials.append(mat);old.hide_render=True;old.hide_set(True);bpy.context.view_layer.update()
 actual=a.q.hair(hair);error=float(np.linalg.norm(actual-V.reshape(-1,3),axis=1).max());assert error<4e-6,error
 for n,value in fixed.items():assert [a.a.hasharray(x) for x in a.geometry(bpy.data.objects[n])]==value,n
 assert a.a.protected()==protected
 hair['sourceCredit']='Aevrynd original explicit parting/side/back control strokes and interpolated hair. Same retained DarkNik/NikZava284 head and MakeHuman/body inherited source/rights unchanged. No external hair mesh, image, texture or likeness adopted. Legacy AFN140 named attributes are the reused native current-skin/guide deformation mechanism only.'
 hair['scope']='One complete unaccepted original parted-bob candidate. New authored roots on actual scalp, two-parent interpolation and direct native point/guide editing. Neither biological follicle semantics nor natural dynamics/finite/self/continuous contact/runtime is established.'
 np.savez_compressed(E/'authored-parting-flow-lineage.npz',guides=P,guideDomain=groups,guideRootFaces=np.array(guideRootFaces),guideRootBarycentric=np.array(guideBary),childRootFaces=fi,childRootBarycentric=bc,childGuideIndices=ids,childSecondGuideWeight=weights,scalpFaces=scalpFaces)
 save('authored-parting-flow-construction.json',{'actualHair':hair.name,'actualGuideObject':guideOb.name,'originalControlStrokesPositiveSide':rows,'guides':len(P),'stations':N,'fibres':count,'points':count*N,'partingWidthM':.0014,'intentionalPartRegionExcludedFromInitialFolliclePlacementNotFailedContactCulling':True,'initialGuideRootToScalpDistanceM':{'min':float(min(x['rootProjectionDistanceM'] for x in strokeRecords)),'max':float(max(x['rootProjectionDistanceM'] for x in strokeRecords))},'closestAuthoredGuideRootDistanceM':{'max':max(maxdist),'median':float(np.median(maxdist))},'guideRecords':strokeRecords,'neutralEvaluatedCurveMaxErrorM':error,'numericEvaluationBoundNotContactToleranceM':4e-6,'sourceOldHairHiddenNoOpaqueUnderlay':True,'rootBinding':'Per-fibre current actual scalp triangle/barycentric and signed winding frame. Native attributes reuse r140 mechanism, not failed r140 hairstyle.','appearanceFunctionContactRuntimeAccepted':False,'secondsBeforePreview':time.time()-tick})
 bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=False)
 save('a-build-summary.json',{'source':str(SRC),'output':str(OUT),'sha256':a.a.sha(OUT),'bytes':OUT.stat().st_size,'actualHair':hair.name,'actualGuideObject':guideOb.name,'sourceOriginalHair':old.name,'nativeGuideCount':len(P),'fibres':count,'points':count*N,'currentProtectedAllOtherGeometryAndHiddenRollbackExact':True,'originalGazeRigActionLidDriversAndOriginalMaterialsRetained':True,'appearanceFunctionContactRuntimeNotYetAccepted':True,'oneCompleteCandidate':True,'secondsBeforePreview':time.time()-tick})
 views=[]
 for view in ['face','body-face','profile','oblique','back']:
  views.append(a.b.u.v.image('a-authored-parting',view));save('a-view-controls.json',views)
 print('R141_COMPLETE_AUTHORED_PARTING_HEAD_BODY_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
