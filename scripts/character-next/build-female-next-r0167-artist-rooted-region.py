"""One local artist-guide region, current-scalp sculpting and pre-removal coverage.
CC0 complete36 source curves are construction reference; original252 source and
all source modifiers stay external. No whole-groom affine/UV/rest transplant.
"""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,time,datetime
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');R=Path('D:/Download/Aevrynd');E=C/'evidence/character-female-next/r0167-artist-rooted-region';OUT=C/'assets-source/aevrynd-character/female-next/r0167-source/aevrynd-female-next-r0167-a-artist-rooted-region.blend'
sp=importlib.util.spec_from_file_location('r167base',R/'scripts/character-next/build-female-next-r0149-native-physical-groom.py');base=importlib.util.module_from_spec(sp);sp.loader.exec_module(base);a=base.a;h=base
def save(n,x):(E/n).write_bytes((json.dumps(x,indent=2)+'\n').encode())
def attr(d,name,typ,domain,prop,x):d.attributes.new(name,typ,domain).data.foreach_set(prop,np.asarray(x).ravel())
def unit(v):return v/np.maximum(np.linalg.norm(v,axis=-1,keepdims=True),1e-30)
def smooth(P,N=49):
 Q=np.vstack((P[0],P,P[-1]));out=[]
 for t in np.linspace(0,len(P)-1,N):
  i=min(int(t),len(P)-2);u=t-i;p0,p1,p2,p3=Q[i:i+4];out.append(.5*((2*p1)+(-p0+p2)*u+(2*p0-5*p1+4*p2-p3)*u*u+(-p0+3*p1-3*p2+p3)*u*u*u))
 return np.array(out)
def main():
 tick=time.time();before=json.loads((E/'before.json').read_text());assert not OUT.exists() and a.a.sha(Path(before['source']))==before['sourceSha256'];bpy.ops.wm.open_mainfile(filepath=before['source']);s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();skin=bpy.data.objects[a.FIXED[0]];oldHair=bpy.data.objects[a.FIXED[1]];oldHair.material_slots[0].link='DATA';oldHair.hide_render=False;oldHair.hide_set(False);rig=bpy.data.objects['AFN138_ACTUAL_CURRENT_GAZE_RIG'];protected={n:a.rawsig(bpy.data.objects[n]) for n in a.FIXED+a.MOVING if n!=oldHair.name};baseline={n:[a.a.hasharray(v) for v in a.geometry(bpy.data.objects[n])] for n in protected};W,T=a.geometry(skin);cache=np.load(R/'Evidence/character-female-next/r0150-authored-rooted-locks/actual-current-scalp.npz');assert np.array_equal(T,cache['triangles']) and float(np.linalg.norm(W-cache['world'],axis=1).max())<2e-6;scalpFaces=cache['scalpFaces'];tree=BVHTree.FromPolygons(W.tolist(),T[scalpFaces].tolist(),all_triangles=True)
 def root(p):
  hit,normal,fi,distance=tree.find_nearest(Vector(p));fi=int(scalpFaces[fi]);tri=T[fi];B=W[tri];u=np.linalg.lstsq(np.column_stack((B[1]-B[0],B[2]-B[0])),np.array(hit)-B[0],rcond=None)[0];bc=np.array([1-u.sum(),*u]);return bc@B,tri,bc,np.array(normal),float(distance),fi
 skin.data.calc_loop_triangles();uvlayer=skin.data.uv_layers['AngelicaOriginalUV']
 def uv(fi,bc):return bc@np.array([uvlayer.data[li].uv[:] for li in skin.data.loop_triangles[int(fi)].loops])
 source=np.load(E/'actual-cc0-complete-guide-reference.npz');Q=source['guideWorld'];ids=np.where((Q[:,0,0]>.003)&(Q[:,0,1]<-.01)&(Q[:,0,2]>1.59))[0];assert len(ids)==36
 guides=[];gTri=[];gBC=[];gUp=[];gGroup=[];gUV=[];rootGaps=[]
 for sourceID in ids:
  q=Q[sourceID];seed=q[0]+np.array([0.,.012,-.095]);r,tri,bc,normal,gap,fi=root(seed);t=np.linspace(0,1,16);D=q-q[0]
  # Deliberate current-woman local sculpt: crown lift, temple clearance, bob
  # length and inward tail turn. Source nonuniform36 complete flows retained,
  # no three center paths, radial cross sections or entire foreign hairstyle.
  P=r+np.column_stack((.95*D[:,0]+.025*np.sin(np.pi*t*.85),.80*D[:,1]+.012*np.sin(np.pi*t),.78*D[:,2]+.008*np.sin(np.pi*t)))
  P[:,0]-=.008*np.clip((t-.8)/.2,0,1)**2;P=smooth(P);P[0]=r
  guides.append(P);gTri.append(tri);gBC.append(bc);gUp.append(normal);gGroup.append(0);gUV.append(uv(fi,bc));rootGaps.append(gap)
 guides=np.array(guides,'f4');gTri=np.array(gTri,'i4');gBC=np.array(gBC);gUp=np.array(gUp);gGroup=np.array(gGroup,'i4')
 # Current-surface emission footprint: actual triangles close to the complete
 # guide-root patch, not arbitrary disks around three numerical center paths.
 rootKD=KDTree(len(guides))
 for i,p in enumerate(guides[:,0]):rootKD.insert(Vector(p),i)
 rootKD.balance();centers=W[T[scalpFaces]].mean(1);domain=[]
 for fi,p in zip(scalpFaces,centers):
  _,i,distance=rootKD.find(Vector(p))
  if distance<.006 and p[0]>.002:domain.append(int(fi))
 domain=np.array(domain,'i4');assert len(domain)>20;B=W[T[domain]];areas=np.linalg.norm(np.cross(B[:,1]-B[:,0],B[:,2]-B[:,0]),axis=1)/2;rng=np.random.default_rng(1671128);chosen=rng.choice(domain,16000,p=areas/areas.sum());ab=rng.random((len(chosen),2));mask=ab.sum(1)>1;ab[mask]=1-ab[mask];rBC=np.column_stack((1-ab.sum(1),ab));rTri=T[chosen];renderRoots=(W[rTri]*rBC[:,:,None]).sum(1);rUp=unit(np.cross(W[rTri[:,1]]-W[rTri[:,0]],W[rTri[:,2]]-W[rTri[:,0]]));rGroup=np.zeros(len(chosen),'i4');rootUV=np.array([uv(fi,bc) for fi,bc in zip(chosen,rBC)])
 # Establish correspondence BEFORE removing or generating display fibres.
 # This is a guide-envelope distance criterion, not proof of optical fill,
 # rendered spline occupancy, or finite contact acceptance.
 src=np.load(E.parent/'r0165-native-hair-construction/actual-original-hair-geometry.npz');HP=src['positions'];component=src['components'];kd=KDTree(len(guides)*49)
 for i,p in enumerate(guides.reshape(-1,3)):kd.insert(Vector(p),i)
 kd.balance();dist=np.array([kd.find(Vector(p))[2] for p in HP]);selected=[];componentEvidence=[]
 for ci in range(int(component.max())+1):
  mask=component==ci;v=HP[mask];dd=dist[mask]
  if v[:,0].min()>.003 and float(dd.max())<.012:
   selected.append(ci);componentEvidence.append({'component':ci,'vertices':int(mask.sum()),'maximumVertexToGuideSampleM':float(dd.max()),'bounds':[v.min(0).tolist(),v.max(0).tolist()]})
 assert len(selected)>0,'No fully corresponding source component; do not create an old-hair-underlay candidate.'
 save('pre-replacement-current-region-correspondence.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sourceGuideIDs':ids.tolist(),'sourceRootUVRetainedAsReferenceOnlyNotTransferred':True,'sourceFullGuideRootOwnership':'Each selected original16-station curve remains complete; native Human/UVMap source retained externally, current roots independently on current Skin triangles.','localRootSeedToCurrentScalpM':{'min':min(rootGaps),'median':float(np.median(rootGaps)),'max':max(rootGaps)},'currentGuideBounds':[guides.min((0,1)).tolist(),guides.max((0,1)).tolist()],'actualCurrentEmissionTriangles':len(domain),'emissionAreaM2':float(areas.sum()),'selectedWholeSourceComponents':componentEvidence,'replacementDefinitionBeforePreview':'All component vertices must lie in12mm current sculpted guide-sample envelope and entirely positive-x regional domain. No centroid mask, post-preview mask shrink, strand failure filtering or hidden selected-source underlay.','geometricCorrespondenceNotProofOfOpticalCoverageOrFiniteContact':True})
 data=bpy.data.hair_curves.new('AFN167_EDITABLE_ARTIST_REGION_GUIDES_DATA');data.add_curves([49]*len(guides));data.position_data.foreach_set('vector',guides.ravel());data.surface=skin;data.surface_uv_map='AngelicaOriginalUV';attr(data,'surface_uv_coordinate','FLOAT2','CURVE','vector',np.array(gUV,'f4'));attr(data,'AFN167_GUIDE_UP','FLOAT_VECTOR','CURVE','vector',gUp.astype('f4'));attr(data,'AFN167_GROUP','INT','CURVE','value',gGroup);go=bpy.data.objects.new('AFN167_EDITABLE_ROOT_TO_TIP_LOCK_GUIDES',data);s.collection.objects.link(go);go.hide_render=True;go.hide_set(True);B=W[gTri];rootBase=(B*gBC[:,:,None]).sum(1);ax=unit(B[:,1]-B[:,0]);az=unit(np.cross(B[:,1]-B[:,0],B[:,2]-B[:,0]));ay=np.cross(az,ax);D=guides-rootBase[:,None,:];local=np.stack(((D*ax[:,None]).sum(2),(D*ay[:,None]).sum(2),(D*az[:,None]).sum(2)),axis=2);base.bind(go,skin,gTri,gBC,local,guides)
 mesh=bpy.data.meshes.new('AFN167_ACTUAL_LOCAL_SCALP_ROOTS_DATA');mesh.from_pydata(renderRoots.tolist(),[],[]);mesh.update();ro=bpy.data.objects.new('AFN167_ACTUAL_LOCAL_CURRENT_SCALP_ROOTS',mesh);s.collection.objects.link(ro);ro.hide_render=True;ro.hide_set(True);attr(mesh,'AFN167_ROOT_UP','FLOAT_VECTOR','POINT','vector',rUp.astype('f4'));attr(mesh,'AFN167_GROUP','INT','POINT','value',rGroup);attr(mesh,'AFN167_BC','FLOAT_VECTOR','POINT','vector',rBC.astype('f4'))
 for j in range(3):attr(mesh,'AFN167_V'+str(j),'INT','POINT','value',rTri[:,j])
 hd=bpy.data.hair_curves.new('AFN167_ACTUAL_LOCAL_NATIVE_GROOM_DATA');hair=bpy.data.objects.new('AFN167_ACTUAL_ROOTED_FRONT_LOCK_GROOM',hd);s.collection.objects.link(hair);graph=bpy.data.node_groups.new('AFN167_LOCAL_ARTIST_LOCKS_NATIVE_INTERPOLATION','GeometryNodeTree');graph.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');graph.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry');hair.modifiers.new('AFN167_NATIVE_LOCAL_LOCK_VOLUME','NODES').node_group=graph;n=graph.nodes;L=graph.links;out=n.new('NodeGroupOutput')
 def info(ob):
  x=n.new('GeometryNodeObjectInfo');x.transform_space='RELATIVE';x.inputs['Object'].default_value=ob;return x.outputs['Geometry']
 def named(name,typ='FLOAT_VECTOR'):
  x=n.new('GeometryNodeInputNamedAttribute');x.data_type=typ;x.inputs['Name'].default_value=name;return x.outputs['Attribute']
 def vec(op,*values):
  x=n.new('ShaderNodeVectorMath');x.operation=op
  for j,value in enumerate(values):L.new(value,x.inputs[j])
  return x.outputs[0]
 def scale(v,t):
  x=n.new('ShaderNodeVectorMath');x.operation='SCALE';L.new(v,x.inputs[0]);L.new(t,x.inputs['Scale']);return x.outputs[0]
 position=n.new('GeometryNodeInputPosition').outputs[0];sourceGeo=info(skin);corners=[]
 for j in range(3):
  nd=n.new('GeometryNodeSampleIndex');nd.data_type='FLOAT_VECTOR';nd.domain='POINT';nd.clamp=False;L.new(sourceGeo,nd.inputs['Geometry']);L.new(position,nd.inputs['Value']);L.new(named('AFN167_V'+str(j),'INT'),nd.inputs['Index']);corners.append(nd.outputs['Value'])
 split=n.new('ShaderNodeSeparateXYZ');L.new(named('AFN167_BC'),split.inputs[0]);root=vec('ADD',vec('ADD',scale(corners[0],split.outputs[0]),scale(corners[1],split.outputs[1])),scale(corners[2],split.outputs[2]));setp=n.new('GeometryNodeSetPosition');L.new(info(ro),setp.inputs['Geometry']);L.new(root,setp.inputs['Position']);mtp=n.new('GeometryNodeMeshToPoints');mtp.mode='VERTICES';L.new(setp.outputs[0],mtp.inputs['Mesh']);inter=n.new('GeometryNodeInterpolateCurves');L.new(info(go),inter.inputs['Guide Curves']);L.new(named('AFN167_GUIDE_UP'),inter.inputs['Guide Up']);L.new(named('AFN167_GROUP','INT'),inter.inputs['Guide Group ID']);L.new(mtp.outputs[0],inter.inputs['Points']);L.new(named('AFN167_ROOT_UP'),inter.inputs['Point Up']);L.new(named('AFN167_GROUP','INT'),inter.inputs['Point Group ID']);inter.inputs['Max Neighbors'].default_value=4;rad=n.new('GeometryNodeSetCurveRadius');parameter=n.new('GeometryNodeSplineParameter');taper=n.new('ShaderNodeMapRange');taper.inputs['From Min'].default_value=0.;taper.inputs['From Max'].default_value=1.;taper.inputs['To Min'].default_value=.00004;taper.inputs['To Max'].default_value=.000006;L.new(parameter.outputs['Factor'],taper.inputs['Value']);L.new(taper.outputs['Result'],rad.inputs['Radius']);L.new(inter.outputs[0],rad.inputs['Curve']);mat=bpy.data.materials.new('AFN167_NATIVE_FIBRE_REFERENCE_DEFAULT_COLOR');mat.use_nodes=True;ns=mat.node_tree.nodes;ns.clear();bs=ns.new('ShaderNodeBsdfHairPrincipled');defaultColor=list(bs.inputs['Color'].default_value);bs.parametrization='COLOR';bs.inputs['Roughness'].default_value=.35;bs.inputs['Radial Roughness'].default_value=.45;mo=ns.new('ShaderNodeOutputMaterial');mat.node_tree.links.new(bs.outputs[0],mo.inputs[0]);setmat=n.new('GeometryNodeSetMaterial');setmat.inputs['Material'].default_value=mat;L.new(rad.outputs[0],setmat.inputs['Geometry']);L.new(setmat.outputs[0],out.inputs['Geometry']);bpy.context.view_layer.update();actual=a.q.hair(hair);assert len(actual)==16000*49 and np.isfinite(actual).all();rootError=float(np.linalg.norm(actual.reshape(16000,49,3)[:,0]-renderRoots,axis=1).max());assert rootError<3e-6
 original=oldHair.data;mask=np.isin(component,selected);keep=[f for f in original.polygons if not mask[int(f.vertices[0])]];P=h.arr(original.vertices,'co',len(original.vertices),3);retained=bpy.data.meshes.new('AFN167_RETAINED_ARTIST_HAIR_OUTSIDE_CORRESPONDING_REGION');retained.from_pydata(P.tolist(),[],[list(f.vertices) for f in keep]);retained.update()
 for ma in original.materials:retained.materials.append(ma)
 loops=np.array([li for f in keep for li in range(f.loop_start,f.loop_start+f.loop_total)],'i4')
 for i,f in enumerate(retained.polygons):f.material_index=keep[i].material_index;f.use_smooth=keep[i].use_smooth
 for uv0 in original.uv_layers:
  dst=retained.uv_layers.new(name=uv0.name);dst.data.foreach_set('uv',h.arr(uv0.data,'uv',len(uv0.data),2)[loops].ravel());dst.active_render=uv0.active_render;dst.active_clone=uv0.active_clone
 retained.uv_layers.active_index=original.uv_layers.active_index;retained.normals_split_custom_set(h.arr(original.corner_normals,'vector',len(original.loops),3)[loops].tolist());oldHair.data=retained;oldHair.material_slots[0].link='DATA';bpy.context.view_layer.update();assert protected=={n:a.rawsig(bpy.data.objects[n]) for n in protected} and baseline=={n:[a.a.hasharray(v) for v in a.geometry(bpy.data.objects[n])] for n in baseline}
 save('direct-artist-rooted-region-authoring.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originalStartedUTC':before['startedUTC'],'changedPremise':'Complete36 source-artist guide flow group sculpted locally on current scalp and pre-removal all-vertex spatial correspondence replaces166 three arbitrary primary arcs and centroid mask. Current-triangle roots and native interpolation reused as tools only.','sourceGuideIDs':ids.tolist(),'actualGuideCurves':len(guides),'nativeRenderCurves':16000,'actualRenderPoints':len(actual),'actualRootArithmeticMaximumErrorM':rootError,'sourceFullComponentsSelectedBeforeContacts':selected,'sourcePolygonsRemovedForActualReplacement':len(original.polygons)-len(keep),'allUnselectedHairPolygonsUVCornerNormalsPreserved':True,'noSelectedSourceUnderlayRetained':True,'nativeMaterialColorMode':'COLOR actual default, identical166 for controlled construction change','actualDefaultColorRGBA':defaultColor,'originalHairDataMaterialIORRestored':1000.,'fullHairRestMotionContactRuntimeStillUnaccepted':True})
 np.savez_compressed(E/'actual-rooted-lock-construction-lineage.npz',sourceGuideIDs=ids,guideWorld=guides,guideRootTriangles=gTri,guideRootBarycentric=gBC,rootTriangles=rTri,rootBarycentric=rBC,rootWorld=renderRoots,rootGroup=rGroup,currentEmissionFaces=domain,retainedOriginalHairPolygons=np.array([f.index for f in keep],'i4'),replacedSourceComponents=np.array(selected,'i4'))
 bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=True);save('a-build-summary.json',{'source':before['source'],'output':str(OUT),'engineAlias':str(R/'engine/assets/characters/female-next/source/r0167-source'/OUT.name),'sha256':a.a.sha(OUT),'bytes':OUT.stat().st_size,'actualSkin':skin.name,'actualRig':rig.name,'actualHair':hair.name,'actualGuides':go.name,'actualRootPoints':ro.name,'retainedSourceHair':oldHair.name,'nativeStrands':16000,'points':len(actual),'originalGazeAction':rig.animation_data.action.name,'regionalReplacementOnlyNotCompleteNewHairstyle':True,'unaccepted':True,'secondsBeforePreview':time.time()-tick});assert OUT.stat().st_size<before['sourceBudgetBytes'];a.b.u.v.E=E;views=[]
 for view in ['face','body-face','profile','back','oblique']:
  ctl=a.b.u.v.image('a-artist-rooted-region',view);ctl.update(frame=1,actualHair=hair.name,localRegionReplacement=True,hairTypeAtActualCapture=s.render.hair_type,actualSamplesAtCapture=s.cycles.samples,actualResolutionAtCapture=[s.render.resolution_x,s.render.resolution_y]);views.append(ctl);save('actual-rooted-lock-preview-controls.json',views)
 print('R167_COMPLETE_ARTIST_ROOTED_REGION_HEAD_BODY_PROFILE_BACK_OBLIQUE_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
