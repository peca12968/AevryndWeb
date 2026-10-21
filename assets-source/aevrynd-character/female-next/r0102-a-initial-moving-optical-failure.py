"""One geometry-derived adaptive inner-lid surface on the retained B2 woman.
New source controls are created where source-surface interpolation bends away
from a planar face. Original endpoints, clearances, UV, rig and strands stay.
The construction criterion is sampled, not a continuous collision certificate.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0102-facet-aware-lid-surface';OLD=E.parent/'r0101-articulated-eyelid-topology';S=R/'engine/assets/characters/female-next/source';SRC=S/'aevrynd-female-next-r0101-b2-lid-uv-and-attachment.blend';OUT=S/'aevrynd-female-next-r0102-a-facet-aware-lining.blend'
sp=importlib.util.spec_from_file_location('r102facet',Path(__file__).with_name('build-female-next-r0098-native-head.py'));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);q=m.q;v=m.v;v.E=E
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.item() if isinstance(a,np.generic) else a.tolist())+'\n',encoding='utf8')
def geom(ob):
 d,P=q.geom(ob);d.calc_loop_triangles();return d,P,q.arr(d.loop_triangles,'vertices',len(d.loop_triangles),3,dtype='i4')
def deliver(blink):
 face=bpy.data.objects['AFN59_FACE_CONTROLS'];oral=bpy.data.objects['AFN74_ORAL_CONTROLS'];face['blink_left']=face['blink_right']=blink;oral['jaw_open']=0
 for ob in [face,oral]:ob.update_tag()
 for name in m.m.rig.native_names():ob=bpy.data.objects[name];ob.update_tag();ob.data.shape_keys.update_tag()
 bpy.data.objects['AFN101_EDITABLE_LID_AND_SOCKET_COMPONENT'].data.shape_keys.update_tag();bpy.context.view_layer.update()
def main():
 tick=time.time();assert not OUT.exists();bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();skin=bpy.data.objects['AFN101_CONTINUOUS_WOMAN_WITH_ARTICULATED_LIDS'];helper=bpy.data.objects['AFN101_EDITABLE_LID_AND_SOCKET_COMPONENT'];face=bpy.data.objects['AFN59_FACE_CONTROLS'];oral=bpy.data.objects['AFN74_ORAL_CONTROLS'];actions={ob.name:ob.animation_data.action if ob.animation_data else None for ob in [face,oral]};props={ob.name:{key:ob[key] for key in (['blink_left','blink_right'] if ob==face else ['jaw_open'])} for ob in [face,oral]}
 for ob in [face,oral]:
  if ob.animation_data:ob.animation_data.action=None
 deliver(0);d,V0,T0=geom(skin);V0=V0.copy();T0=T0.copy();hair=bpy.data.objects['AFN97_TUCKED_ARTIST_BOB_CHILDREN'];hair0=q.hair(hair).copy();lashHelper=bpy.data.objects['AFN59_LASHES_NATIVE_POINT_POSES'];lash0=q.geom(lashHelper)[1].copy();oldOrig=q.arr(d.attributes['AFN101_OriginalCIndex'].data,'value',len(V0),dtype='i4');oldPatch=q.arr(d.attributes['AFN101_PatchIndex'].data,'value',len(V0),dtype='i4');oldKeys=np.where(oldOrig>=0,oldOrig,677442+oldPatch);oldSort=np.argsort(oldKeys);raw=skin.data;rawP=q.arr(raw.vertices,'co',len(raw.vertices),3);T=q.arr(raw.loops,'vertex_index',len(raw.loops),dtype='i4').reshape(-1,3);UV={u.name:q.arr(u.data,'uv',len(u.data),2).reshape(-1,3,2).copy() for u in raw.uv_layers};material=q.arr(raw.polygons,'material_index',len(raw.polygons),dtype='i4');smooth=q.arr(raw.polygons,'use_smooth',len(raw.polygons),dtype=bool);attrs={}
 names={'OriginalCIndex':('INT','value',1),'PatchIndex':('INT','value',1),'BindIndex':('INT','value',1),'FollowWeight':('FLOAT','value',1),'Conform':('FLOAT','value',1),'Clearance':('FLOAT','value',1),'Side':('FLOAT','value',1),'EyeCentre':('FLOAT_VECTOR','vector',3),'BindRest':('FLOAT_VECTOR','vector',3),'UnusedCorrespondence':('BOOLEAN','value',1)}
 for name,(kind,prop,width) in names.items():attrs[name]=q.arr(raw.attributes['AFN101_'+name].data,prop,len(raw.vertices),width,dtype='i4' if kind=='INT' else bool if kind=='BOOLEAN' else 'f4').copy()
 rawKeys=np.where(attrs['OriginalCIndex']>=0,attrs['OriginalCIndex'],677442+attrs['PatchIndex']);loc=np.searchsorted(oldKeys[oldSort],rawKeys[T]);assert np.array_equal(oldSort[loc],T0),'Source raw/final face identity changed';A=np.array(skin.matrix_world);HA=np.array(helper.matrix_world);world=lambda p:p@HA[:3,:3].T+HA[:3,3];centre=attrs['EyeCentre']@A[:3,:3].T+A[:3,3];scale=np.linalg.norm(A[:3,0]);oldHelper=helper.data;keys={k.name:q.arr(k.data,'co',len(oldHelper.vertices),3).copy() for k in oldHelper.shape_keys.key_blocks};assert set(keys)=={'Basis','AFN101_Closed_L','AFN101_Closed_R'};helperMap=dict(np.load(OLD/'b-anatomical-lid-lineage.npz')['patchHelperOriginalBodyMapping'].tolist());parent=np.arange(len(T),'i4') if False else np.arange(len(T),dtype='i4');sourceFaceCount=len(T);sourcePointCount=len(rawP);passes=[];sampleValues=[0.,.25,.5,.75,1.];eyeTrees={};eyeReference={};eyeMoves={}
 for value in [0.,.5,1.]:
  deliver(value);eyeTrees[value]={};eyeMoves[value]={}
  for side in ['L','R']:
   ed,EV,ET=geom(bpy.data.objects['AFN60_'+side+'_EYE_OUTER_SHELL_APPROX']);eyeTrees[value][side]=BVHTree.FromPolygons(EV.tolist(),ET.tolist(),all_triangles=True)
   if value==0:eyeReference[side]=EV.copy()
   eyeMoves[value][side]=float(np.linalg.norm(EV-eyeReference[side],axis=1).max())
 assert max(v for row in eyeMoves.values() for v in row.values())<4e-7,'Optical mesh changes with blink: sampled reference must be rebuilt per pose'
 tree=eyeTrees[0.]
 def project(P,C,G,side):
  result=P.copy()
  for sign,name in [(1,'L'),(-1,'R')]:
   for i in np.flatnonzero(side*sign>0):
    direction=P[i]-C[i];length=np.linalg.norm(direction);direction/=length;hit,*_=tree[name].ray_cast(Vector(C[i]),Vector(direction),.2);assert hit is not None,'Source radial field has no optical hit';target=np.array(hit)+direction*G[i]
    if length<np.linalg.norm(target-C[i]):result[i]=target
  return result
 def source_pose(value):
  H=keys['Basis']+value*(keys['AFN101_Closed_L']+keys['AFN101_Closed_R']-2*keys['Basis']);return world(H)[attrs['PatchIndex']]
 eligiblePoints=(attrs['OriginalCIndex']<0)&(attrs['FollowWeight']==0)&(attrs['Conform']==1)&(abs(attrs['Clearance']-.00010/scale)<1e-7);selected=np.flatnonzero(np.all(eligiblePoints[T],axis=1));chosenVertices=np.unique(T[selected]);deliver(.5);_,actualHalf,_=geom(skin);ids=oldSort[np.searchsorted(oldKeys[oldSort],rawKeys[chosenVertices])];calculated=project(source_pose(.5)[chosenVertices],centre[chosenVertices],attrs['Clearance'][chosenVertices]*scale,attrs['Side'][chosenVertices]);fieldError=float(np.linalg.norm(calculated-actualHalf[ids],axis=1).max());assert fieldError<4e-6,fieldError;deliver(0)
 prior=json.loads((OLD/'evaluated-blink-and-contact.json').read_text('utf8'));witness=set(row['actualSkinTriangle'] for side in prior['states'][2]['scopedOpticalSurfaceContact'] for row in side['triangleSurfaceIntersectionOrTouchWitnesses']);assert witness<=set(selected),'A prior witness lies outside the anatomical lining repair region'
 # Adaptive control geometry, driven by original optical-surface curvature.
 # A fixed clearance-derived defect target replaces arbitrary ring density.
 for depth in range(4):
  eligiblePoints=(attrs['OriginalCIndex']<0)&(attrs['FollowWeight']==0)&(attrs['Conform']==1)&(abs(attrs['Clearance']-.00010/scale)<1e-7);selected=np.flatnonzero(np.all(eligiblePoints[T],axis=1));tri=T[selected];defect=np.zeros(len(tri));gap=(attrs['Clearance'][tri]*scale).min(1);C=centre[tri[:,0]];side=attrs['Side'][tri[:,0]]
  for value in sampleValues:
   rawWorld=source_pose(value);rawTri=rawWorld[tri];points=project(rawTri.reshape(-1,3),np.repeat(C,3,axis=0),(attrs['Clearance'][tri]*scale).ravel(),np.repeat(side,3)).reshape(-1,3,3)
   for weights in [(0.5,.5,0),(0,.5,.5),(.5,0,.5),(1/3,1/3,1/3)]:
    w=np.array(weights);P=np.einsum('v,bvi->bi',w,rawTri);G=np.einsum('v,bv->b',w,attrs['Clearance'][tri]*scale);surface=project(P,C,G,side);linear=np.einsum('v,bvi->bi',w,points);defect=np.maximum(defect,np.linalg.norm(surface-linear,axis=1))
  marked=selected[defect>gap/4]
  if depth==0:marked=np.unique(np.r_[marked,np.array(sorted(witness),'i4')])
  row={'depth':depth,'examinedLiningFaces':len(selected),'maximumSampledInterpolationDefectM':float(defect.max()),'fixedAuthoredInnerWallClearanceM':.0001,'defectTargetIsOneQuarterOfActualClearance':True,'markedFaces':len(marked),'poseSamples':sampleValues,'globalCurvatureOrContinuousContactBound':False};passes.append(row);save('a-adaptive-construction.json',{'sourceFieldReadbackMaximumErrorM':fieldError,'opticalMeshBlinkWorldChangesM':eyeMoves,'passes':passes,'scope':'Geometry-derived local source-surface reconstruction, not a parameter sweep or continuous/global collision certificate.'});print('R102_ADAPTIVE_SOURCE_FACETS',depth,len(marked),row['maximumSampledInterpolationDefectM'],flush=True)
  if not len(marked) or depth==3:break
  edgePairs=np.sort(np.concatenate([T[marked][:,[0,1]],T[marked][:,[1,2]],T[marked][:,[2,0]]]),axis=1);unique=np.unique(edgePairs,axis=0);assert len(rawP)+len(unique)<sourcePointCount+50000,'Local construction resource limit';oldCount=len(rawP);newIDs=np.arange(oldCount,oldCount+len(unique),dtype='i4');edgeLookup={tuple(map(int,p)):int(i) for p,i in zip(unique,newIDs)};edgeCode=unique[:,0].astype('u8')*(oldCount+len(unique))+unique[:,1];allEdges=np.stack([T[:,[0,1]],T[:,[1,2]],T[:,[2,0]]],axis=1);codes=np.minimum(allEdges[:,:,0],allEdges[:,:,1]).astype('u8')*(oldCount+len(unique))+np.maximum(allEdges[:,:,0],allEdges[:,:,1]);flags=np.isin(codes,edgeCode);changed=flags.any(1);unchanged=np.flatnonzero(~changed);children=[];uvChildren={name:[] for name in UV};childParents=[]
  for fi in np.flatnonzero(changed):
   a,b,c=map(int,T[fi]);mids=[edgeLookup.get(tuple(sorted(pair))) for pair in [(a,b),(b,c),(c,a)]];n=sum(x is not None for x in mids);mab,mbc,mca=mids
   if n==1:
    j=next(i for i,x in enumerate(mids) if x is not None);aa,bb,cc=[int(T[fi,(j+k)%3]) for k in range(3)];mm=mids[j];newFaces=[[aa,mm,cc],[mm,bb,cc]]
   elif n==2:
    j=next(i for i in range(3) if mids[i] is not None and mids[(i+1)%3] is not None);aa,bb,cc=[int(T[fi,(j+k)%3]) for k in range(3)];u,vv=mids[j],mids[(j+1)%3];newFaces=[[bb,vv,u],[aa,u,cc],[u,vv,cc]]
   else:newFaces=[[a,mab,mca],[mab,b,mbc],[mca,mbc,c],[mab,mbc,mca]]
   children.extend(newFaces);childParents.extend([fi]*len(newFaces))
   for name,values in UV.items():
    tab={a:values[fi,0],b:values[fi,1],c:values[fi,2]}
    for mm,pair in zip(mids,[(a,b),(b,c),(c,a)]):
     if mm is not None:tab[mm]=(tab[pair[0]]+tab[pair[1]])/2
    uvChildren[name].extend([[tab[i] for i in face] for face in newFaces])
  sourceHelperIDs=attrs['PatchIndex'][unique];newHelperIDs=np.arange(len(keys['Basis']),len(keys['Basis'])+len(unique),dtype='i4')
  for name in keys:keys[name]=np.vstack((keys[name],keys[name][sourceHelperIDs].mean(1))).astype('f4')
  for bodyID,helperID in zip(newIDs,newHelperIDs):helperMap[int(bodyID)]=int(helperID)
  rawP=np.vstack((rawP,rawP[unique].mean(1))).astype('f4');centre=np.vstack((centre,centre[unique].mean(1)))
  for name in attrs:
   if name=='PatchIndex':extra=newHelperIDs
   elif name=='OriginalCIndex':extra=np.full(len(unique),-1,'i4')
   elif name=='UnusedCorrespondence':extra=np.zeros(len(unique),bool)
   elif names[name][0]=='INT':extra=attrs[name][unique[:,0]]
   else:extra=attrs[name][unique].mean(1)
   attrs[name]=np.concatenate((attrs[name],extra.astype(attrs[name].dtype)))
  order=np.r_[unchanged,np.array(childParents,'i4')];T=np.vstack((T[unchanged],np.array(children,'i4')));material=material[order];smooth=smooth[order];parent=parent[order]
  for name in UV:UV[name]=np.concatenate((UV[name][unchanged],np.array(uvChildren[name],'f4')))
  assert len(T)<1600000,'Local finite-surface face budget exceeded'
 # Rebuild the editable source helper and the complete joined skin, retaining
 # all prior point identities. UV is interpolated per parent face/corner.
 oldMaterials=list(raw.materials);newMesh=bpy.data.meshes.new('AFN102_FACET_AWARE_COMPLETE_SKIN');newMesh.from_pydata(rawP.tolist(),[],T.tolist());newMesh.update()
 for mat in oldMaterials:newMesh.materials.append(mat)
 newMesh.polygons.foreach_set('material_index',material);newMesh.polygons.foreach_set('use_smooth',smooth)
 for name,values in UV.items():newMesh.uv_layers.new(name=name).data.foreach_set('uv',values.reshape(-1,2).ravel())
 newMesh.uv_layers.active=newMesh.uv_layers['VitruvianUV.UDIM'];newMesh.uv_layers['VitruvianUV.UDIM'].active_render=True
 for name,(kind,prop,width) in names.items():newMesh.attributes.new('AFN101_'+name,kind,'POINT').data.foreach_set(prop,attrs[name].ravel())
 newMesh.attributes.new('AFN102_R101ParentFaceID','INT','FACE').data.foreach_set('value',parent);patchFaces=T[np.any(attrs['OriginalCIndex'][T]<0,axis=1)];hm=bpy.data.meshes.new('AFN102_EDITABLE_ADAPTIVE_LID_COMPONENT');hm.from_pydata(keys['Basis'].tolist(),[],[[helperMap[int(i)] for i in face] for face in patchFaces]);hm.update();reference=helper.copy();reference.data=oldHelper;bpy.context.scene.collection.objects.link(reference);reference.name='AFN102_REFERENCE_R101_SOURCE_COMPONENT';reference.hide_render=True;reference.hide_set(True);helper.data=hm
 for name in ['Basis','AFN101_Closed_L','AFN101_Closed_R']:
  key=helper.shape_key_add(name=name);key.data.foreach_set('co',keys[name].ravel())
  if name!='Basis':
   driver=key.driver_add('value').driver;driver.type='SCRIPTED';var=driver.variables.new();var.name='blink';var.targets[0].id=face;var.targets[0].data_path='["blink_'+('left' if name.endswith('_L') else 'right')+'"]';driver.expression='min(1,max(0,blink))'
 skin.data=newMesh;helper.update_tag();skin.update_tag();bpy.context.view_layer.update();deliver(0);nd,W,NT=geom(skin);newOrig=q.arr(nd.attributes['AFN101_OriginalCIndex'].data,'value',len(W),dtype='i4');newPatch=q.arr(nd.attributes['AFN101_PatchIndex'].data,'value',len(W),dtype='i4');newKeys=np.where(newOrig>=0,newOrig,677442+newPatch);sort=np.argsort(newKeys);mapping=sort[np.searchsorted(newKeys[sort],oldKeys)];assert np.array_equal(newKeys[mapping],oldKeys);oldPointError=float(np.linalg.norm(W[mapping]-V0,axis=1).max());assert oldPointError<4e-6
 for k in range(3):
  attr=hair.data.attributes['AFN97_ScalpVertex'+str(k)];old=q.arr(attr.data,'value',24800,dtype='i4');attr.data.foreach_set('value',mapping[old]);attr=lashHelper.data.attributes['AFN101_LashVertex'+str(k)];old=q.arr(attr.data,'value',len(lashHelper.data.vertices),dtype='i4');attr.data.foreach_set('value',mapping[old])
 hair.data.update_tag();hair.update_tag();lashHelper.data.update_tag();lashHelper.update_tag();bpy.context.view_layer.update();hairError=float(np.linalg.norm(q.hair(hair)-hair0,axis=1).max());lashError=float(np.linalg.norm(q.geom(lashHelper)[1]-lash0,axis=1).max());assert hairError<6e-6 and lashError<6e-6
 binding=json.loads((OLD/'b2-lash-root-bindings.json').read_text('utf8'));triKeys={tuple(sorted(map(int,t))) for t in NT}
 for row in binding:row['actualSkinTriangle']=mapping[np.array(row['actualSkinTriangle'])].tolist();assert tuple(sorted(row['actualSkinTriangle'])) in triKeys,'An unchanged lash attachment no longer lies on an actual skin triangle'
 save('a-retained-lash-bindings.json',binding);save('a-build-summary.json',{'source':str(SRC),'sourceSha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'output':str(OUT),'renderSkin':skin.name,'editableComponent':helper.name,'sourceRawVertices':sourcePointCount,'newRawVertices':len(rawP),'newActualVertices':len(W),'sourceFaces':sourceFaceCount,'newActualFaces':len(NT),'addedSourceControls':len(rawP)-sourcePointCount,'adaptivePasses':passes,'sampledDefectTargetMet':passes[-1]['markedFaces']==0,'sourceFieldReadbackMaximumWorldErrorM':fieldError,'oldActualVertexMaximumWorldDifferenceM':oldPointError,'allGroomControlsMaximumWorldDifferenceM':hairError,'allLashControlsMaximumWorldDifferenceM':lashError,'clearanceThicknessMaterialsRadiiAndOriginalControlsUnchanged':True,'completeAppearanceOperationFiniteContactRuntimeAccepted':False,'secondsBeforePreview':time.time()-tick});np.savez_compressed(E/'a-facet-construction-lineage.npz',originalActualToNewActual=mapping,parentR101FaceIDs=parent,addedRawVertexIDs=np.arange(sourcePointCount,len(rawP)),actualOriginalSourceIDs=newOrig,actualPatchSourceIDs=newPatch)
 deliver(0)
 for ob in [face,oral]:
  for key,value in props[ob.name].items():ob[key]=value
  if ob.animation_data:ob.animation_data.action=actions[ob.name]
  ob.update_tag()
 s.frame_set(1);bpy.context.view_layer.update();m.m.rig.shade.settings();m.m.rig.k.b.camera('face');s.camera.data.lens=85;s.render.hair_subdiv=3;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True);views=[]
 for view in ['face','profile','body-face']:views.append(v.image('a-facet-lining',view));save('a-view-controls.json',views)
 print('R102_FIRST_COMPLETE_PREVIEW_DONE',time.time()-tick,flush=True)
 for ob in [face,oral]:
  if ob.animation_data:ob.animation_data.action=None
 for label,value in [('half',.5),('closed',1.)]:deliver(value);views.append(v.image('a-facet-lining-'+label,'face'));save('a-view-controls.json',views)
 print('R102_FACET_LINING_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
