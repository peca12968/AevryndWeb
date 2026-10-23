"""One complete native rest groom from actual scalp adjacency/metric streamlines.
No decorative UV, foreign free-tail transport, sparse cage or cover mesh.
"""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,time,datetime,heapq
from mathutils import Vector
from mathutils.bvhtree import BVHTree
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');R=Path('D:/Download/Aevrynd');E=C/'evidence/character-female-next/r0185-topological-scalp-flow';OUT=C/'assets-source/aevrynd-character/female-next/r0185-source/aevrynd-female-next-r0185-a-topological-scalp-flow.blend'
sp=importlib.util.spec_from_file_location('r169',C/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;h=m.h
def save(n,q):(E/n).write_bytes((json.dumps(q,indent=2)+'\n').encode())
def unit(v):return v/max(float(np.linalg.norm(v)),1e-15)
def main():
 tick=time.time();t=json.loads((E/'before.json').read_text());assert not OUT.exists() and a.a.sha(Path(t['source']))==t['sourceSha256'];bpy.ops.wm.open_mainfile(filepath=t['source']);s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();skin=bpy.data.objects[a.FIXED[0]];old=bpy.data.objects[a.FIXED[1]];old.material_slots[0].link='DATA';originalLash=bpy.data.objects[a.FIXED[2]];originalLash.hide_render=False;originalLash.hide_set(False);rollback=bpy.data.objects['AFN184_ACTUAL_NATIVE_DEFORMED_LASHES'];rollback.hide_render=True;rollback.hide_set(True)
 raw={n:a.rawsig(bpy.data.objects[n]) for n in a.FIXED+a.MOVING};W,T=a.geometry(skin);sourceSkin=np.load(R/'Evidence/character-female-next/r0139-native-lid-follow/native-current-lid-skinning.npz');assert np.array_equal(T,sourceSkin['skinTriangles']) and np.max(abs(W-sourceSkin['skinWorld']))<1e-6
 sf=np.load(E.parent/'r0171-actual-scalp-chart/actual-scalp-groom-lineage.npz')['actualScalpFaces'];tri=T[sf];ids=np.unique(tri);B=W[tri];edge1=B[:,1]-B[:,0];edge2=B[:,2]-B[:,0];cross=np.cross(edge1,edge2);area=np.linalg.norm(cross,axis=1)*.5;faceNormals=cross/(2*area[:,None]);vn=np.zeros_like(W)
 for j in range(3):np.add.at(vn,tri[:,j],cross)
 vn/=np.maximum(np.linalg.norm(vn,axis=1,keepdims=True),1e-15)
 graph={int(i):{} for i in ids};edgeOwners={};adj=np.full((len(tri),3),-1,'i4')
 for f,row in enumerate(tri):
  for j in range(3):
   vi,vj=int(row[(j+1)%3]),int(row[(j+2)%3]);weight=float(np.linalg.norm(W[vi]-W[vj]));graph[vi][vj]=weight;graph[vj][vi]=weight;key=tuple(sorted((vi,vj)))
   if key in edgeOwners:ff,jj=edgeOwners[key];adj[f,j]=ff;adj[ff,jj]=f
   else:edgeOwners[key]=(f,j)
 seeds=ids[(abs(W[ids,0])<.0015)&(W[ids,2]>1.53)];assert len(seeds)>5;dist=np.full(len(W),np.inf);queue=[]
 for vi in seeds:dist[vi]=0;heapq.heappush(queue,(0.,int(vi)))
 while queue:
  value,vi=heapq.heappop(queue)
  if value!=dist[vi]:continue
  for vj,cost in graph[vi].items():
   candidate=value+cost
   if candidate<dist[vj]:dist[vj]=candidate;heapq.heappush(queue,(candidate,vj))
 assert np.isfinite(dist[ids]).all();edges=np.stack((edge1,edge2),2);pinv=np.linalg.pinv(edges);delta=dist[tri[:,1:]]-dist[tri[:,0,None]];gradient=np.einsum('fji,fj->fi',pinv,delta);norm=np.linalg.norm(gradient,axis=1);assert (norm>1e-8).all();gradient/=norm[:,None];uvder=np.einsum('fij,fj->fi',pinv,gradient);der=np.column_stack((-uvder.sum(1),uvder));body=BVHTree.FromPolygons(W.tolist(),T.tolist(),all_triangles=True)
 save('actual-scalp-metric-capability.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':t['source'],'actualSkin':skin.name,'actualScalpFaces':len(sf),'actualScalpVertices':len(ids),'actualScalpAreaM2':float(area.sum()),'actualScalpBBox':[W[ids].min(0).tolist(),W[ids].max(0).tolist()],'actualMidpartSkinVertexIDs':seeds.tolist(),'allVerticesConnectedToActualMidpart':True,'surfaceMetricGeodesicRangeM':[float(dist[ids].min()),float(dist[ids].max())],'sourceSkinActualTopologyEqual':True,'changedFailedPremise':'Actual three-dimensional Skin triangle adjacency/edge metric and in-face tangent gradient; no UV tangent, foreign free-path transfer or detached generic volume. Whole surface-to-free-tip geometry rebuilt.','officialDocumentation':'Blender official search excerpts on Curves surface anchoring and guide interpolation read; full docs fetch402, not claimed read. No code/asset import.','officialURL':'https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/hair/generation/interpolate_hair_curves.html','secondsBeforeGeometry':time.time()-tick})
 rng=np.random.default_rng(185);N=64000;K=33;faces=rng.choice(len(sf),N,p=area/area.sum());r=rng.random((N,2));r[:,0]=np.sqrt(r[:,0]);bcs=np.column_stack((1-r[:,0],r[:,0]*(1-r[:,1]),r[:,0]*r[:,1]));P=np.empty((N,K,3),'f4');rootWorld=np.einsum('bi,bij->bj',bcs,B[faces]);rootNo=np.einsum('bi,bij->bj',bcs,vn[tri[faces]]);rootNo/=np.linalg.norm(rootNo,axis=1,keepdims=True);rootCentre=rootWorld+rootNo*.000035;exits=np.full(N,-1,'i4');surfaceArc=np.zeros(N);stuck=[];slidingContacts=0;guideExamples=[];constructionRecords=[]
 # Every fibre is traced through actual adjacent Skin triangles. Offset is an
 # authored rest lift along a smooth anatomical surface normal, not a rescue
 # after an intersection, and no opaque cap or hidden coverage layer is used.
 for cid in range(N):
  f=int(faces[cid]);bc=bcs[cid].copy();q=bc@B[f];points=[rootCentre[cid].copy()];arc=0.;previous=-1;visited=set();lastDir=gradient[f].copy();lastNormal=rootNo[cid];liftMax=.0025+.0015*rng.random();reason='step_limit'
  for step in range(100):
   direction=gradient[f];db=der[f];times=np.where(db < -1e-9,-bc/np.minimum(db,-1e-9),np.inf);j=int(np.argmin(times));length=float(times[j])
   if not np.isfinite(length) or length < -1e-7:reason='invalid_edge';break
   length=max(length,1e-9);bc=np.clip(bc+db*length,0,1);bc/=bc.sum();q=bc@B[f];arc+=length;normal=unit(bc@vn[tri[f]]);lift=.000035+liftMax*(1-np.exp(-arc/.020));points.append(q+normal*lift);lastDir=direction;lastNormal=normal;nf=int(adj[f,j])
   if nf<0:reason='boundary';exits[cid]=f;break
   if nf==previous or nf in visited:reason='metric_ridge';break
   visited.add(f);previous=f;f=nf;uv=pinv[f]@(q-B[f,0]);bc=np.array([1-uv.sum(),*uv]);bc=np.maximum(bc,0);bc/=bc.sum()
  if reason!='boundary' and len(stuck)<30:stuck.append({'id':cid,'face':int(sf[f]),'reason':reason,'surfaceArcM':arc,'world':q.tolist()})
  surfaceArc[cid]=arc;p=points[-1].copy();direction=unit(lastDir+.08*lastNormal);targetZ=1.342+.030*rng.random();tailArc=0.;wavePhase=rng.uniform(0,2*np.pi);side=1. if p[0]>=0 else -1.
  for step in range(90):
   # An intrinsic soft bend toward gravity gives a new complete free section.
   # Small independent endpoint variations break a cut hem; no old tip survives.
   direction=unit(direction+.0035*42*np.array([0.,0.,-1.]));direction=unit(direction+np.array([side*.0025*np.sin(tailArc*42+wavePhase),.0015*np.cos(tailArc*35+wavePhase),0]));length=.0035;desired=p+direction*length;hit,no,fi,along=body.ray_cast(Vector(p),Vector(direction),length+.000035)
   if hit is not None and along>1e-7:
    normal=unit(np.array(no));direction=unit(direction-normal*min(float(direction@normal),0));desired=np.array(hit)+normal*.000040+direction*max(0,length-float(along));slidingContacts+=1
   points.append(desired);p=desired;tailArc+=length
   if p[2]<targetZ or tailArc>.245:break
  Q=np.array(points);lengths=np.r_[0,np.linalg.norm(np.diff(Q,axis=0),axis=1).cumsum()];assert lengths[-1]>.005;P[cid]=np.stack([np.interp(np.linspace(0,lengths[-1],K),lengths,Q[:,j]) for j in range(3)],1);P[cid,0]=rootCentre[cid]
  if cid%1000==0:
   guideExamples.append(P[cid].copy());constructionRecords.append({'id':cid,'actualRootSkinFace':int(sf[faces[cid]]),'surfaceExitReason':reason,'surfaceArcM':arc,'freeArcM':tailArc,'tip':p.tolist()})
  if cid%8000==0:print('R185_ACTUAL_TOPOLOGY_FIBRES_AUTHORED',cid,round(time.time()-tick,2),flush=True)
 assert np.isfinite(P).all();hd=bpy.data.hair_curves.new('AFN185_ACTUAL_SCALP_METRIC_COMPLETE_REST_GROOM_DATA');hd.add_curves([K]*N);hd.position_data.foreach_set('vector',P.ravel());rad=np.tile(.000035*(1-.98*np.linspace(0,1,K)**5),N).astype('f4');hd.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',rad);hd.attributes.new('AFN185_FOLLICLE_ID','INT','CURVE').data.foreach_set('value',np.arange(N,dtype='i4'))
 for j in range(3):hd.attributes.new('AFN185_SkinVertex'+str(j),'INT','CURVE').data.foreach_set('value',tri[faces,j].astype('i4'))
 hd.attributes.new('AFN185_RootBarycentric','FLOAT_VECTOR','CURVE').data.foreach_set('vector',bcs.astype('f4').ravel());hd.surface=skin;hd.surface_uv_map=skin.data.uv_layers.active.name;hair=bpy.data.objects.new('AFN185_ACTUAL_TOPOLOGICAL_SCALP_REST_HAIR',hd);s.collection.objects.link(hair);mat=bpy.data.materials.new('AFN185_NATIVE_BROWN_FIBRE_MATERIAL');mat.use_nodes=True;ns=mat.node_tree.nodes;ns.clear();bs=ns.new('ShaderNodeBsdfHairPrincipled');bs.parametrization='MELANIN';bs.inputs['Melanin'].default_value=.75;bs.inputs['Melanin Redness'].default_value=.15;bs.inputs['Roughness'].default_value=.35;bs.inputs['Radial Roughness'].default_value=.45;output=ns.new('ShaderNodeOutputMaterial');mat.node_tree.links.new(bs.outputs[0],output.inputs[0]);hd.materials.append(mat);old.hide_render=True;old.hide_set(True);s.render.hair_type='STRIP';s.camera.data.type='PERSP';bpy.context.view_layer.update();actual,offset=m.curveworld(hair);err=float(np.linalg.norm(actual-P.reshape(-1,3),axis=1).max());assert err<3e-6;assert raw=={n:a.rawsig(bpy.data.objects[n]) for n in raw}
 np.savez_compressed(E/'topological-scalp-flow-lineage.npz',rootTriangles=tri[faces],rootBC=bcs,rootWorld=rootWorld,rootCentre=rootCentre,scalpFaces=sf,metricDistance=dist[ids],scalpVertexIDs=ids,partVertexIDs=seeds,exitFaces=exits,surfaceArc=surfaceArc,representativeGuides=np.array(guideExamples))
 save('direct-topological-rest-authoring.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'nativeStrands':N,'controlsPerStrand':K,'actualScalpTriangleExits':int((exits>=0).sum()),'metricRidgeOrOtherInteriorTerminations':int((exits<0).sum()),'firstInteriorTerminationRecords':stuck,'surfaceArcQuantilesM':np.quantile(surfaceArc,[0,.1,.5,.9,1]).tolist(),'actualLocalSkinRaySlidingEvents':slidingContacts,'representativeWholePathRecords':constructionRecords,'nativeDisplayMaximumErrorM':err,'noForeignGuideUVCardOrOldTailShape':True,'noOpaqueCoverageLayer':True,'originalLashMeshVisibleAnd184CandidateHidden':True,'newHairIsNeutralRestOnlyNotHeadFollowOrPhysics':True,'allOriginalSevenRawMeshUVSignaturesRetained':True,'noFiniteSelfContinuousContactAcceptance':True,'secondsBeforePreview':time.time()-tick})
 hair['scope']='Unaccepted complete rest hairstyle, actual current scalp adjacency/metric pathways and newly authored free sections. Native editable64k full curves, persistent root IDs/triangles. No old UV/card/foreign tail, cover shell, head-follow/physics/runtime/contact acceptance.';a.b.u.v.E=E;views=[a.b.u.v.image('a-topological-scalp-flow','face')];bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=True);save('a-build-summary.json',{'source':t['source'],'output':str(OUT),'sha256':a.a.sha(OUT),'bytes':OUT.stat().st_size,'engineAlias':str(R/'engine/assets/characters/female-next/source/r0185-source'/OUT.name),'actualSkin':skin.name,'actualRig':'AFN138_ACTUAL_CURRENT_GAZE_RIG','actualHair':hair.name,'retainedSourceHair':old.name,'originalLashMeshVisible':originalLash.name,'hidden184LashRollback':rollback.name,'nativeStrands':N,'points':len(actual),'completeWomanCandidates':1,'fullNativeGroomCandidate':True,'unaccepted':True,'secondsBeforeOtherViews':time.time()-tick});assert OUT.stat().st_size<t['sourceBudgetBytes']
 for v in ['body-face','profile','back','oblique']:views.append(a.b.u.v.image('a-topological-scalp-flow',v));save('topological-scalp-preview-controls.json',views)
 print('R185_COMPLETE_TOPOLOGICAL_SCALP_REST_GROOM_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
