"""Actual source guide identity/UV ownership and anatomical cap/volume map.
No final-curve firstpoint-as-birth proxy, world-box fit or frozen free lengths.
"""
from pathlib import Path
import bpy,numpy as np,json,datetime,time,hashlib,importlib.util,shutil
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
p=json.loads(Path('F:/AevryndStorage/character-development-paths.json').read_text('utf-8'));A=Path(p['directCharacterArchiveAccess']);E=A/'evidence/character-female-next/r0206-operative-guide-anatomical-map';F=Path('F:/AevryndEvidence/r0206-operative-guide-anatomical-map');t=json.loads((E/'before.json').read_text('utf-8'));tick=time.time()
def save(n,d):(E/n).write_bytes((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
def sha(f):return hashlib.file_digest(Path(f).open('rb'),'sha256').hexdigest()
sp=importlib.util.spec_from_file_location('r206base',A/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;h=m.h;sp=importlib.util.spec_from_file_location('r206cap',A/'scripts/character-next/build-female-next-r0198-native-birth-owned-scalp.py');f=importlib.util.module_from_spec(sp);sp.loader.exec_module(f)
ART=Path('C:/Users/USER/AppData/Local/Temp/Aevrynd-hair-editor-reference/hair.blend');assert sha(ART)=='93aedaef061dc14618a0fcfad33c3df816fa755e8093381cbdfd0fd4c34527f5';bpy.ops.wm.open_mainfile(filepath=str(ART));bpy.context.scene.frame_set(1);src=bpy.data.objects['basic_short_hair'];src.hide_set(False);at=src.data.attributes.new('AFN206_ORIGINAL_GUIDE_ID','INT','CURVE');at.data.foreach_set('value',np.arange(418,dtype='i4'));sourceUV=h.arr(src.data.attributes['surface_uv_coordinate'].data,'vector',418,2);uvName=src.data.surface_uv_map;surface=src.data.surface;found=False
for mod in src.modifiers:
 if mod.type=='NODES' and mod.node_group and any(x.bl_idname=='GeometryNodeDeformCurvesOnSurface' for x in mod.node_group.nodes) and not found:mod.show_viewport=True;found=True
 else:mod.show_viewport=False
assert found;bpy.context.view_layer.update();P,off=m.curveworld(src);de=src.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;ids=h.arr(de.attributes['AFN206_ORIGINAL_GUIDE_ID'].data,'value',418,dtype='i4');assert np.array_equal(ids,np.arange(418)) and len(P)==3506;V,T=a.geometry(surface);mesh=surface.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;mesh.calc_loop_triangles();loops=np.array([x.loops[:] for x in mesh.loop_triangles]);uv=h.arr(mesh.uv_layers[uvName].data,'uv',len(mesh.uv_layers[uvName].data),2)[loops];uvTree=BVHTree.FromPolygons(np.column_stack([uv.reshape(-1,2),np.zeros(3*len(T))]).tolist(),np.arange(3*len(T)).reshape(-1,3).tolist(),all_triangles=True)
def uvhit(tree,q,uvfaces):
 # Exact float64 triangle membership, without float32 BVH boundary projection.
 a=uvfaces[:,0];v0=uvfaces[:,1]-a;v1=uvfaces[:,2]-a;r=np.asarray(q)-a;det=v0[:,0]*v1[:,1]-v0[:,1]*v1[:,0];valid=np.abs(det)>1e-15;b=np.full(len(det),-np.inf);c=b.copy();b[valid]=(r[valid,0]*v1[valid,1]-r[valid,1]*v1[valid,0])/det[valid];c[valid]=(v0[valid,0]*r[valid,1]-v0[valid,1]*r[valid,0])/det[valid];bc=np.column_stack([1-b-c,b,c]);score=np.min(bc,axis=1);score[~valid]=-np.inf;fi=int(np.argmax(score))
 if score[fi]<-1e-10:
  save('unmatched-parametric-point.json',{'q':np.asarray(q).tolist(),'bestFace':fi,'bestBarycentric':bc[fi].tolist(),'bestMinimumWeight':float(score[fi]),'noGuardRelaxed':True});raise AssertionError(('Point not in target cap triangles',q,score[fi]))
 result=np.clip(bc[fi],0,1);result/=result.sum();return fi,result
sourceFaces=[];sourceBC=[]
for q in sourceUV:
 fi,bc=uvhit(uvTree,q,uv);sourceFaces.append(fi);sourceBC.append(bc)
sourceFaces=np.array(sourceFaces,'i4');sourceBC=np.array(sourceBC);sourceLogical=np.einsum('ni,nij->nj',sourceBC,V[T[sourceFaces]]);ownershipError=float(np.linalg.norm(P[off]-sourceLogical,axis=1).max());save('reopened-actual-guide-identity-and-uv-ownership.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sourceStyle':src.name,'sourceSurface':surface.name,'sourceUVMap':uvName,'persistentGuideIDsComplete':bool(np.array_equal(ids,np.arange(418))),'nativeGuideCurves':418,'nativeGuidePoints':3506,'nativeSurfaceDeformOnlyBeforeChildGeneration':True,'actualNativeSurfaceUVBarycentricGuideStartMaximumErrorM':ownershipError,'ownershipGuardM':3e-6,'noFinal25324FirstPointsUsedAsBirths':True});assert ownershipError<3e-6
mask=np.load(E.parent/'r0198-native-birth-owned-scalp/source-guide-and-cap-construction.npz')['sourceCapMask'].copy();oldMask=mask.copy();mask[sourceFaces]=True;mask=f.fill_holes(T,mask,V);repairs=[]
for attempt in range(4):
 try:sb,*_=f.boundary(V,T,mask);break
 except AssertionError:
  assert attempt<3;_,pid=np.unique(np.round(V,6),axis=0,return_inverse=True);tt=pid[T[mask]];edges=np.sort(np.vstack([tt[:,[0,1]],tt[:,[1,2]],tt[:,[2,0]]]),axis=1);edges,num=np.unique(edges,axis=0,return_counts=True);bv,degree=np.unique(edges[num==1],return_counts=True);bad=bv[degree>2];extra=np.any(np.isin(pid[T],bad),axis=1)&~mask;assert len(bad)>0 and int(extra.sum())<=24 and V[np.flatnonzero(np.isin(pid,bad)),2].min()>1.42;repairs.append(np.flatnonzero(extra).tolist());mask=f.fill_holes(T,mask|extra,V)
assert mask[sourceFaces].all();assert sha(t['source'])==t['sourceSha256'];bpy.ops.wm.open_mainfile(filepath=t['source']);s=bpy.context.scene;s.frame_set(1);skin=bpy.data.objects[a.FIXED[0]];W,TT=a.geometry(skin);sf=np.load(E.parent/'r0198-native-birth-owned-scalp/native-surface-birth-lineage.npz')['actualCurrentScalpFaces'];tm=np.zeros(len(TT),bool);tm[sf]=True;tb,*_=f.boundary(W,TT,tm)
def parameterize(V,T,mask,boundary):
 used=np.unique(T[mask]);_,index,local=np.unique(np.round(V[used],6),axis=0,return_index=True,return_inverse=True);actualIDs=used[index];xyz=V[actualIDs];lookup=np.full(len(V),-1,'i4');lookup[used]=local;faces=lookup[T[mask]];B=lookup[boundary];assert len(np.unique(B))==len(B);bp=xyz[B];mid=np.flatnonzero(np.abs(bp[:,0])<.02);assert len(mid)>1;front=int(mid[np.argmax(bp[mid,2])]);backCandidates=mid[bp[mid,1]>bp[front,1]+.035];assert len(backCandidates)>0;nape=int(backCandidates[np.argmin(bp[backCandidates,2])]);right=int(np.argmax(bp[:,0]));left=int(np.argmin(bp[:,0]));B=np.roll(B,-front)
 def locations(B):return [int(np.flatnonzero(B==lookup[boundary[q]])[0]) for q in [front,right,nape,left]]
 loc=locations(B)
 if not (0==loc[0]<loc[1]<loc[2]<loc[3]):B=np.r_[B[0],B[:0:-1]];loc=locations(B)
 assert 0==loc[0]<loc[1]<loc[2]<loc[3],('Anatomical boundary anchors out of order',loc)
 closed=np.r_[B,B[0]];angles=np.empty(len(B));anchors=np.r_[loc,len(B)];targetTheta=np.array([-np.pi/2,0,np.pi/2,np.pi,3*np.pi/2])
 for i in range(4):
  lo,hi=anchors[i:i+2];arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(xyz[closed[lo:hi+1]],axis=0),axis=1))];assert arc[-1]>0;angles[lo:hi]=targetTheta[i]+(targetTheta[i+1]-targetTheta[i])*arc[:-1]/arc[-1]
 UV=np.zeros((len(xyz),2));UV[B]=np.column_stack([np.cos(angles),np.sin(angles)]);edges=np.unique(np.sort(np.vstack([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),axis=1),axis=0);adj=np.zeros((len(xyz),len(xyz)));adj[edges[:,0],edges[:,1]]=1;adj[edges[:,1],edges[:,0]]=1;interior=np.setdiff1d(np.arange(len(xyz)),B);lap=np.diag(adj.sum(1))-adj;UV[interior]=np.linalg.solve(lap[np.ix_(interior,interior)],adj[np.ix_(interior,B)]@UV[B]);area=np.cross(UV[faces[:,1]]-UV[faces[:,0]],UV[faces[:,2]]-UV[faces[:,0]]);sign=1 if np.median(area)>0 else -1;assert np.min(area*sign)>1e-12,('Folded cap parameterization',float(np.min(area*sign)));return xyz,faces,UV,B,angles,lookup,actualIDs,[int(B[i]) for i in loc],float(np.min(area*sign))
sv,st,suv,sb,sa,slookup,sactual,sanchors,sarea=parameterize(V,T,mask,sb);tv,tt,tuv,tb,ta,tlookup,tactual,tanchors,tarea=parameterize(W,TT,tm,tb)
def radial(q,angles,Buv):
 theta=np.arctan2(q[:,1],q[:,0]);theta=np.where(theta<-np.pi/2,theta+2*np.pi,theta);i=np.searchsorted(angles,theta,side='right')-1;i=np.clip(i,0,len(angles)-1);p0=Buv[i];p1=Buv[(i+1)%len(Buv)];d=np.column_stack([np.cos(theta),np.sin(theta)]);cross=lambda x,y:x[:,0]*y[:,1]-x[:,1]*y[:,0];return cross(p0,p1)/cross(d,p1-p0)
def mapDisk(q):
 q=np.atleast_2d(q);r0=radial(q,sa,suv[sb]);r1=radial(q,ta,tuv[tb]);return q*(r1/r0)[:,None]
tree=BVHTree.FromPolygons(np.column_stack([tuv,np.zeros(len(tuv))]).tolist(),tt.tolist(),all_triangles=True)
def targetAt(q):
 faces=[];bary=[]
 for uvp in mapDisk(q):
  fi,bc=uvhit(tree,uvp,tuv[tt]);faces.append(fi);bary.append(bc)
 faces=np.array(faces,'i4');bary=np.array(bary);return np.einsum('ni,nij->nj',bary,W[TT[sf[faces]]]),sf[faces],bary
mappedVertices,_,_=targetAt(suv);sourceParamRoots=np.einsum('ni,nij->nj',sourceBC,suv[slookup[T[sourceFaces]]]);targetLogical,targetFaces,targetBC=targetAt(sourceParamRoots);centre=sv.mean(0);scale=.1;X=(sv-centre)/scale;pair=np.linalg.norm(X[:,None]-X[None,:],axis=2);kernel=pair*pair*np.log(np.maximum(pair,1e-12));polynomial=np.column_stack([np.ones(len(X)),X]);system=np.block([[kernel,polynomial],[polynomial.T,np.zeros((4,4))]]);coeff=np.linalg.solve(system,np.vstack([mappedVertices,np.zeros((4,3))]))
def warp(q):
 out=[]
 for lo in range(0,len(q),512):
  x=(np.asarray(q[lo:lo+512])-centre)/scale;r=np.linalg.norm(x[:,None]-X[None,:],axis=2);out.append((r*r*np.log(np.maximum(r,1e-12)))@coeff[:len(X)]+np.column_stack([np.ones(len(x)),x])@coeff[len(X):])
 return np.vstack(out)
sourceSamples=[];sampleSourceLeft=[];sampleSourceWeights=[];lengths=np.diff(np.r_[off,len(P)])
for i,L in enumerate(lengths):
 Q=P[off[i]:off[i]+L];arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(Q,axis=0),axis=1))];steps=np.linspace(0,arc[-1],16);ix=np.clip(np.searchsorted(arc,steps,side='right')-1,0,len(Q)-2);w=(steps-arc[ix])/np.maximum(arc[ix+1]-arc[ix],1e-12);sourceSamples.append(Q[ix]*(1-w[:,None])+Q[ix+1]*w[:,None]);sampleSourceLeft.append(ix);sampleSourceWeights.append(w)
S=np.array(sourceSamples);Q=warp(S.reshape(-1,3)).reshape(418,16,3);rootResidual=targetLogical-Q[:,0];rootError=np.linalg.norm(rootResidual,axis=1);eps=1e-5;sample=S.reshape(-1,3);J=np.stack([(warp(sample+np.eye(3)[i]*eps)-warp(sample-np.eye(3)[i]*eps))/(2*eps) for i in range(3)],axis=2);det=np.linalg.det(J);save('reopened-cap-volume-map-before-guard.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sourceGuideIdentityAndSurfaceOwnershipQualified':True,'sourceCapFaces':int(mask.sum()),'all418LogicalSourceOwnerFacesIncluded':True,'sourceCapRootOwnerFacesAdded':np.flatnonzero(mask&~oldMask).tolist(),'sourceCapLocalTopologyRepairs':repairs,'sourceCapMinimumOrientedParamArea':sarea,'targetCapMinimumOrientedParamArea':tarea,'rootResidualQuantilesM':np.quantile(rootError,[0,.5,.9,1]).tolist(),'completeGuideVolumeJacobianDeterminantRange':[float(det.min()),float(det.max())],'fixedMapResidualGuardM':.003,'fixedPositiveJacobianGuard':.05,'anatomicalLandmarkViewsStillPending':True,'noCurrentGroomEmittedYet':True});
originalGuard=json.loads((E/'cap-volume-map-before-guard.json').read_text('utf-8'));assert abs(float(rootError.max())-originalGuard['rootResidualQuantilesM'][-1])<1e-10 and abs(float(det.min())-originalGuard['completeGuideVolumeJacobianDeterminantRange'][0])<1e-10;assert rootError.max()>.003 and det.min()<.05
badRootIDs=np.flatnonzero(rootError>=.003);badDetPoints=np.flatnonzero(det<=.05);save('failed-cap-volume-domains.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originalFixedRootResidualGuardM':.003,'originalFixedVolumeJacobianGuard':.05,'rootResidualMaximumM':float(rootError.max()),'rootResidualFailedGuideIDs':badRootIDs.tolist(),'rootResidualFailedPositionsWorld':Q[badRootIDs,0].tolist(),'exactCurrentSkinParametricTargetsWorld':targetLogical[badRootIDs].tolist(),'volumeJacobianMinimum':float(det.min()),'lowJacobianSourceGuidePointPairs':np.column_stack([badDetPoints//16,badDetPoints%16]).tolist(),'allVolumeJacobianValuesPositive':bool(det.min()>0),'notCallingBelowMarginAFoldOrCollision':True,'all418GuidesAndAllCompletePathsRetained':True,'noMapGuardRelaxedNoNewGroomEmitted':True,'minimumReproductionOnlyNotNewAuthoringAttempt':True})
np.savez_compressed(E/'failed-operative-guide-cap-map-lineage.npz',sourceNativeIDs=ids,sourceNativePositions=P,sourceNativeOffsets=off,sourceNativeUV=sourceUV,sourceOwnerFaces=sourceFaces,sourceOwnerBC=sourceBC,sourceLogicalBirths=sourceLogical,sourceResampledPaths=S,sourceSampleLeftIndices=np.array(sampleSourceLeft),sourceSampleRightWeights=np.array(sampleSourceWeights),mappedUnqualifiedWholePaths=Q,currentSkinParametricTargetLogicalBirths=targetLogical,currentSkinTargetFaces=targetFaces,currentSkinTargetTriangles=TT[targetFaces],currentSkinTargetBC=targetBC,sourceCapWorld=sv,sourceCapTriangles=st,sourceCapUV=suv,sourceBoundary=sb,sourceBoundaryAngles=sa,sourceAnchorIDs=sanchors,targetCapWorld=tv,targetCapTriangles=tt,targetCapUV=tuv,targetBoundary=tb,targetBoundaryAngles=ta,targetAnchorIDs=tanchors,sourceVolumeAnchors=sv,volumeAnchorTargets=mappedVertices,warpCentre=centre,warpNormalization=scale,warpCoefficients=coeff,rootResiduals=rootResidual,fullGuideJacobianDeterminants=det,failedRootIDs=badRootIDs,failedJacobianPointIDs=badDetPoints)
protected={name:a.rawsig(bpy.data.objects[name]) for name in a.FIXED+a.MOVING};coll=bpy.data.collections.new('AFN206_REJECTED_CAP_VOLUME_MAP_DIAGNOSTIC');s.collection.children.link(coll)
def curveObject(name,points,lengths):
 cu=bpy.data.hair_curves.new(name);cu.add_curves(np.asarray(lengths).tolist());cu.position_data.foreach_set('vector',np.asarray(points,dtype='f4').ravel());at=cu.attributes.new('AFN206_PERSISTENT_ORIGINAL_GUIDE_ID','INT','CURVE');at.data.foreach_set('value',np.arange(418,dtype='i4'));ob=bpy.data.objects.new(name,cu);coll.objects.link(ob);ob.hide_render=True;ob.hide_set(True);return ob
sourceGuide=curveObject('AFN206_ACTUAL_NATIVE_SOURCE_GUIDE_SNAPSHOT',P,lengths);mappedGuide=curveObject('AFN206_REJECTED_WHOLE_VOLUME_MAPPED_GUIDES',Q.reshape(-1,3),np.full(418,16));me=bpy.data.meshes.new('AFN206_EXACT_CURRENT_SKIN_PARAMETRIC_GUIDE_TARGETS');me.from_pydata(targetLogical.tolist(),[],[]);me.update();targets=bpy.data.objects.new(me.name,me);coll.objects.link(targets)
def attribute(d,name,kind,value,prop='value'):
 at=d.attributes.new(name,kind,'POINT');at.data.foreach_set(prop,np.asarray(value).ravel())
attribute(me,'AFN206_PERSISTENT_ORIGINAL_GUIDE_ID','INT',np.arange(418,dtype='i4'))
for k in range(3):attribute(me,'AFN198_CAP_I'+str(k),'INT',TT[targetFaces,k]);attribute(me,'AFN198_CAP_W'+str(k),'FLOAT',targetBC[:,k].astype('f4'))
attribute(me,'AFN198_ROOT_BIND_WORLD','FLOAT_VECTOR',targetLogical.astype('f4'),'vector');previous=bpy.data.objects['AFN204_ACTUAL_CURRENT_SKIN_CONNECTED_CROP'];targets.modifiers.new('AFN206_CURRENT_SKIN_REFERENCE_TARGET_BINDING','NODES').node_group=previous.modifiers['AFN198_ACTUAL_GUIDE_CAP_BINDING'].node_group.copy();targets.hide_render=True;targets.hide_set(True)
# Render anatomical domain witnesses. These are explicitly source/current
# reference views only, with diagnostic display offsets, not appearance results.
originalStates={ob.name:(ob.hide_render,ob.hide_get()) for ob in s.objects};viewer=bpy.data.objects.new('AFN206_SOURCE_CAP_REFERENCE_VIEWER',bpy.data.objects['AFN205_ACTUAL_SOURCE_HUMAN_REFERENCE'].data.copy());s.collection.objects.link(viewer);viewer.matrix_world=Matrix.Translation((0,.03,-.1));mat=bpy.data.materials.new('AFN206_DIAGNOSTIC_SOURCE_GRAY');mat.use_nodes=True;bs=mat.node_tree.nodes.new('ShaderNodeBsdfPrincipled');out=mat.node_tree.nodes.new('ShaderNodeOutputMaterial');mat.node_tree.links.new(bs.outputs['BSDF'],out.inputs['Surface']);bs.inputs['Base Color'].default_value=(.25,.25,.25,1);viewer.data.materials.clear();viewer.data.materials.append(mat);markerGroups={}
colors=[(1,.03,.02,1),(.03,1,.08,1),(.04,.2,1,1),(1,.03,.8,1)]
for label,vertices,boundary,anchorIDs,shift in [('source',sv,sb,sanchors,np.array([0,.03,-.1])),('target',tv,tb,tanchors,np.zeros(3))]:
 objects=[];line=bpy.data.curves.new('AFN206_'+label+'_ACTUAL_CAP_BOUNDARY','CURVE');line.dimensions='3D';line.bevel_depth=.0005;sp=line.splines.new('POLY');sp.points.add(len(boundary));centreV=vertices.mean(0)
 for point,vid in zip(sp.points,np.r_[boundary,boundary[0]]):
  pos=vertices[vid];no=pos-centreV;no/=np.linalg.norm(no);point.co=(*(pos+shift+no*.001),1)
 ob=bpy.data.objects.new(line.name,line);s.collection.objects.link(ob);objects.append(ob)
 for i,vid in enumerate(anchorIDs):
  pos=vertices[vid];no=pos-centreV;no/=np.linalg.norm(no);bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=6,radius=.003,location=pos+shift+no*.002);ob=bpy.context.object;ob.name='AFN206_'+label+['_FRONT_HAIRLINE','_RIGHT_PERIAURICULAR','_POSTERIOR_NAPE','_LEFT_PERIAURICULAR'][i];mt=bpy.data.materials.new(ob.name);mt.diffuse_color=colors[i];mt.use_nodes=True;bs=mt.node_tree.nodes.new('ShaderNodeBsdfPrincipled');ou=mt.node_tree.nodes.new('ShaderNodeOutputMaterial');mt.node_tree.links.new(bs.outputs['BSDF'],ou.inputs['Surface']);bs.inputs['Base Color'].default_value=colors[i];ob.data.materials.append(mt);objects.append(ob)
 markerGroups[label]=objects
captures=[]
def capture(scene):
 captures.append({'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'output':scene.render.filepath,'frame':scene.frame_current,'cameraMatrixWorld':[list(x) for x in scene.camera.matrix_world],'lens':scene.camera.data.lens,'exposure':scene.view_settings.exposure,'scope':'Source/current anatomical cap reference only, not candidate appearance. Source viewer display translation[0,.03,-.1]; line1mm and marker2mm diagnostic offsets only.'});save('anatomical-domain-render-pre-states.json',captures)
bpy.app.handlers.render_pre.append(capture);a.b.u.v.E=F
for label in ['source','target']:
 for name,(render,hidden) in originalStates.items():bpy.data.objects[name].hide_render=render;bpy.data.objects[name].hide_set(hidden)
 for objects in markerGroups.values():
  for ob in objects:ob.hide_render=True
 viewer.hide_render=True
 if label=='source':
  for name in originalStates:
   if bpy.data.objects[name].type in ['MESH','CURVES','CURVE']:bpy.data.objects[name].hide_render=True
  viewer.hide_render=False;viewer.hide_set(False)
 else:bpy.data.objects[a.FIXED[1]].hide_render=True
 for ob in markerGroups[label]:ob.hide_render=False;ob.hide_set(False)
 for view in ['face','profile','back']:s.camera.data.type='PERSP';a.b.u.v.image('diagnostic-'+label+'-anatomical-cap',view)
bpy.app.handlers.render_pre.remove(capture)
for file in F.glob('matched-diagnostic-*.png'):shutil.copyfile(file,E/file.name)

for name,(render,hidden) in originalStates.items():bpy.data.objects[name].hide_render=render;bpy.data.objects[name].hide_set(hidden)
viewer.hide_render=True;viewer.hide_set(True)
for objects in markerGroups.values():
 for ob in objects:ob.hide_render=True;ob.hide_set(True)
bpy.data.objects[a.FIXED[1]].hide_render=False;bpy.data.objects['AFN204_ACTUAL_CURRENT_SKIN_CONNECTED_CROP'].hide_render=True;assert protected=={name:a.rawsig(bpy.data.objects[name]) for name in protected};output=F/'aevrynd-female-next-r0206-rejected-cap-volume-map-diagnostic.blend';out=A/'assets-source/aevrynd-character/female-next/r0206-source'/output.name;out.parent.mkdir();bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(output),compress=True);shutil.copyfile(output,out);assert sha(out)==sha(output)
save('diagnostic-build-summary.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'output':str(out),'userReviewSource':str(output),'sha256':sha(out),'bytes':out.stat().st_size,'actualCurrentSkin':skin.name,'actualSourceSnapshot':sourceGuide.name,'actualRejectedMappedGuideSnapshot':mappedGuide.name,'actualCurrentSkinReferenceTargets':targets.name,'nativeSourceGuideCount':418,'nativeSourcePoints':len(P),'completeMappedGuidePaths':418,'mappedGuidePoints':len(Q.reshape(-1,3)),'sourceGuideIDUVTriangleOwnershipMaximumErrorM':ownershipError,'rootResidualMaximumM':float(rootError.max()),'minimumVolumeJacobian':float(det.min()),'allSevenRawMeshUVSignaturesUnchanged':protected,'allFailedGuidesAndDomainsRetained':True,'diagnosticOnlyNoNewCompleteAppearanceCandidate':True,'newGroomCandidates':0,'originalHairRestored':True,'originalNumericalGuardsUnchanged':True,'originalClockNotReset':True,'elapsedMinimumReproductionSeconds':time.time()-tick});print('R206_FAILED_COMPLETE_CAP_VOLUME_MAP_REPRODUCTION_SAVED',json.dumps({'failedRoots':len(badRootIDs),'lowJacobianPoints':len(badDetPoints),'source':str(output)}),flush=True)
