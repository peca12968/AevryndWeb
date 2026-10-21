"""Reconstruct actual front-lid topology with independently authored bands.
Keep the r102 finite inner lining and the same complete woman. One candidate.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0103-anatomical-front-lid-bands';OLD=E.parent/'r0102-facet-aware-lid-surface';ORBIT=E.parent/'r0101-articulated-eyelid-topology';S=R/'engine/assets/characters/female-next/source';SRC=S/'aevrynd-female-next-r0102-a-facet-aware-lining.blend';OUT=S/'aevrynd-female-next-r0103-a-anatomical-front-bands.blend'
def mod(n,p):
 sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(p));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
b=mod('r103base','build-female-next-r0102-facet-lining.py');q=b.q;v=b.v;v.E=E;orb=mod('r103orbit','build-female-next-r0101-orbital-lids.py')
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.item() if isinstance(a,np.generic) else a.tolist())+'\n',encoding='utf8',newline='\n')
def stitch(a,pa,c,pc):
 fs=[];i=j=0
 while i<len(a) or j<len(c):
  aa=int(a[i%len(a)]);cc=int(c[j%len(c)]);na=pa[(i+1)%len(a)]+(1 if i+1>=len(a) else 0);nc=pc[(j+1)%len(c)]+(1 if j+1>=len(c) else 0)
  if j==len(c) or (i<len(a) and na<=nc):fs.append([aa,cc,int(a[(i+1)%len(a)])]);i+=1
  else:fs.append([aa,cc,int(c[(j+1)%len(c)])]);j+=1
 return fs
def main():
 tick=time.time();assert not OUT.exists();bpy.ops.wm.open_mainfile(filepath=str(SRC));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update();skin=bpy.data.objects['AFN101_CONTINUOUS_WOMAN_WITH_ARTICULATED_LIDS'];helper=bpy.data.objects['AFN101_EDITABLE_LID_AND_SOCKET_COMPONENT'];face=bpy.data.objects['AFN59_FACE_CONTROLS'];oral=bpy.data.objects['AFN74_ORAL_CONTROLS'];hair=bpy.data.objects['AFN97_TUCKED_ARTIST_BOB_CHILDREN'];lash=bpy.data.objects['AFN59_LASHES_NATIVE_POINT_POSES'];actions={o.name:o.animation_data.action if o.animation_data else None for o in [face,oral]};props={o.name:{k:o[k] for k in (['blink_left','blink_right'] if o==face else ['jaw_open'])} for o in [face,oral]}
 for ob in [face,oral]:
  if ob.animation_data:ob.animation_data.action=None
 b.deliver(0);d,V0,T0=b.geom(skin);V0=V0.copy();oldOrig=q.arr(d.attributes['AFN101_OriginalCIndex'].data,'value',len(V0),dtype='i4');oldPatch=q.arr(d.attributes['AFN101_PatchIndex'].data,'value',len(V0),dtype='i4');oldKeys=np.where(oldOrig>=0,oldOrig,677442+oldPatch);oldSort=np.argsort(oldKeys);hair0=q.hair(hair).copy();H0=q.geom(lash)[1].copy();b.deliver(1);V1=b.geom(skin)[1].copy();b.deliver(0);raw=skin.data;P=q.arr(raw.vertices,'co',len(raw.vertices),3);T=q.arr(raw.loops,'vertex_index',len(raw.loops),dtype='i4').reshape(-1,3);UV={u.name:q.arr(u.data,'uv',len(u.data),2).reshape(-1,3,2).copy() for u in raw.uv_layers};mat=q.arr(raw.polygons,'material_index',len(raw.polygons),dtype='i4');smooth=q.arr(raw.polygons,'use_smooth',len(raw.polygons),dtype=bool);names={'OriginalCIndex':('INT','value',1),'PatchIndex':('INT','value',1),'BindIndex':('INT','value',1),'FollowWeight':('FLOAT','value',1),'Conform':('FLOAT','value',1),'Clearance':('FLOAT','value',1),'Side':('FLOAT','value',1),'EyeCentre':('FLOAT_VECTOR','vector',3),'BindRest':('FLOAT_VECTOR','vector',3),'UnusedCorrespondence':('BOOLEAN','value',1)};attrs={n:q.arr(raw.attributes['AFN101_'+n].data,p,len(P),w,dtype='i4' if kind=='INT' else bool if kind=='BOOLEAN' else 'f4').copy() for n,(kind,p,w) in names.items()};oldPCount=len(P);rawKeys=np.where(attrs['OriginalCIndex']>=0,attrs['OriginalCIndex'],677442+attrs['PatchIndex']);rawToActual=lambda ids:oldSort[np.searchsorted(oldKeys[oldSort],rawKeys[ids])];A=np.array(skin.matrix_world);HA=np.array(helper.matrix_world);HI=np.linalg.inv(HA[:3,:3]);local=lambda W:(W-HA[:3,3])@HI.T;oldHelper=helper.data;keys={k.name:q.arr(k.data,'co',len(oldHelper.vertices),3).copy() for k in oldHelper.shape_keys.key_blocks};hmap=dict(np.load(ORBIT/'b-anatomical-lid-lineage.npz')['patchHelperOriginalBodyMapping'].tolist())
 # R102 added helper points are identified through its persisted point IDs.
 for i in np.flatnonzero(attrs['OriginalCIndex']<0):hmap[int(i)]=int(attrs['PatchIndex'][i])
 mid=(attrs['OriginalCIndex']<0)&(abs(attrs['FollowWeight']-.55)<1e-6);midIDs=np.flatnonzero(mid);assert len(midIDs)==320;remove=np.isin(T,midIDs).any(1);assert remove.sum()==1440;kept=np.flatnonzero(~remove);patchUV={}
 for name,values in UV.items():
  unique,inverse=np.unique(T[remove].ravel(),return_inverse=True);summed=np.zeros((len(unique),2));counts=np.zeros(len(unique));np.add.at(summed,inverse,values[remove].reshape(-1,2));np.add.at(counts,inverse,1);patchUV[name]={int(i):uv for i,uv in zip(unique,summed/counts[:,None])}
 edges=np.load(ORBIT/'b-anatomical-lid-lineage.npz')['originalBoundaryEdges'];adj={int(i):set() for i in np.unique(edges)}
 for aa,cc in edges:adj[int(aa)].add(int(cc));adj[int(cc)].add(int(aa))
 Wraw=P@A[:3,:3].T+A[:3,3];newFaces=[];profiles=[];newPointUV={name:[] for name in UV};newData={name:[] for name in attrs};newP=[];newKey={name:[] for name in keys};newHelperStart=len(keys['Basis']);newRawStart=len(P);sourceParent=q.arr(raw.attributes['AFN102_R101ParentFaceID'].data,'value',len(T),dtype='i4')
 # Artist-authored corresponding cross-section stations, not a parameter scan.
 stations=[('pretarsal',.14,.12,-.00010,-.00005),('tarsal_edge',.32,.30,-.00020,-.00004),('crease_attachment',.45,.48,.00065,0.),('fold_lip',.55,.62,-.00030,-.00004),('orbital_transition',.78,.82,-.00008,-.00002)]
 for sign,side in [(1,'L'),(-1,'R')]:
  boundary=np.array([i for i in adj if Wraw[i,0]*sign>0],'i4');loop,k=orb.order_cycle(boundary,adj,Wraw);assert len(loop)==240;par1=np.r_[0,np.cumsum(np.linalg.norm(np.diff(Wraw[loop[:k+1]],axis=0),axis=1))];par1=.5*par1/par1[-1];tail=np.r_[loop[k:],loop[:1]];par2=np.r_[0,np.cumsum(np.linalg.norm(np.diff(Wraw[tail],axis=0),axis=1))];par2=.5+.5*par2/par2[-1];param=np.r_[par1,par2[1:-1]];t=np.arange(160)/160;extended=np.r_[param,1];boundary0=V0[rawToActual(loop)];boundary1=V1[rawToActual(loop)];interpolate=lambda x:np.column_stack([np.interp(t,extended,np.r_[x[:,j],x[:1,j]]) for j in range(x.shape[1])]);outer0=interpolate(boundary0);outer1=interpolate(boundary1);margin=np.flatnonzero((attrs['OriginalCIndex']<0)&(attrs['Side']*sign>0)&(attrs['FollowWeight']==0)&(attrs['Clearance']>0.0003/A[0,0]));assert len(margin)==160;M0=V0[rawToActual(margin)];M1=V1[rawToActual(margin)];fade=np.sin(np.pi*np.linspace(0,1,81));fade=np.r_[fade,np.zeros(79)]**.6;bands=[];upperCount=81
  for label,openS,closedS,openDepth,closedDepth in stations:
   a=(1-openS)*M0+openS*outer0;c=(1-closedS)*M1+closedS*outer1;a[:,1]+=openDepth*fade;c[:,1]+=closedDepth*fade;ids=np.arange(newRawStart+len(newP),newRawStart+len(newP)+160,dtype='i4');hi=np.arange(newHelperStart+len(newP),newHelperStart+len(newP)+160,dtype='i4');bands.append(ids);newP.extend(local(a));newKey['Basis'].extend(local(a));newKey['AFN101_Closed_L'].extend(local(c) if side=='L' else local(a));newKey['AFN101_Closed_R'].extend(local(c) if side=='R' else local(a))
   for i,j in zip(ids,hi):hmap[int(i)]=int(j)
   for name in attrs:
    if name=='OriginalCIndex':extra=np.full(160,-1,'i4')
    elif name=='PatchIndex':extra=hi
    elif name=='UnusedCorrespondence':extra=np.zeros(160,bool)
    elif name=='FollowWeight':extra=np.full(160,openS)
    else:extra=attrs[name][margin]
    newData[name].extend(extra)
   for name in UV:
    outerUV=interpolate(np.array([patchUV[name][int(i)] for i in loop]));marginUV=np.array([patchUV[name][int(i)] for i in margin]);newPointUV[name].extend((1-openS)*marginUV+openS*outerUV)
   profiles.append({'side':side,'band':label,'openFractionFromMargin':openS,'closedFractionFromMargin':closedS,'openAnteriorPosteriorOffsetM':openDepth,'closedAnteriorPosteriorOffsetM':closedDepth,'upperCornerFade':'sin(central_parameter*pi)^0.6; lower band has no artificial crease','notMeasuredPersonalAnatomy':True})
  fs=stitch(loop,param,bands[-1],t)
  for outerBand,innerBand in zip(bands[:0:-1],bands[-2::-1]):fs+=stitch(outerBand,t,innerBand,t)
  fs+=stitch(bands[0],t,margin,t)
  oldDirected={}
  for tri in T[kept][np.isin(T[kept],loop).sum(1)>=2]:
   for aa,cc in zip(tri,np.roll(tri,-1)):
    if int(aa) in adj and int(cc) in adj:oldDirected[tuple(sorted((int(aa),int(cc))))]=(int(aa),int(cc))
  flip=None
  for tri in fs:
   for aa,cc in zip(tri,tri[1:]+tri[:1]):
    if tuple(sorted((aa,cc))) in oldDirected:flip=(aa,cc)==oldDirected[tuple(sorted((aa,cc)))];break
   if flip is not None:break
  assert flip is not None
  if flip:
   for tri in fs:tri[1],tri[2]=tri[2],tri[1]
  newFaces+=fs
 assert len(newP)==1600;P=np.vstack((P,np.array(newP,'f4')));attrs['UnusedCorrespondence'][midIDs]=True
 for name in attrs:attrs[name]=np.concatenate((attrs[name],np.array(newData[name],dtype=attrs[name].dtype)))
 for name in keys:keys[name]=np.vstack((keys[name],np.array(newKey[name],'f4')))
 newFaces=np.array(newFaces,'i4');NT=np.vstack((T[kept],newFaces));materials=list(raw.materials);mesh=bpy.data.meshes.new('AFN103_COMPLETE_SKIN_WITH_ANATOMICAL_FRONT_BANDS');mesh.from_pydata(P.tolist(),[],NT.tolist());mesh.update()
 for material in materials:mesh.materials.append(material)
 mesh.polygons.foreach_set('material_index',np.r_[mat[kept],np.full(len(newFaces),4)].astype('i4'));mesh.polygons.foreach_set('use_smooth',np.r_[smooth[kept],np.ones(len(newFaces),bool)])
 for name,values in UV.items():
  table=patchUV[name];table.update({int(i):u for i,u in zip(np.arange(newRawStart,len(P)),newPointUV[name])});newUV=np.array([[table[int(i)] for i in tri] for tri in newFaces],'f4');mesh.uv_layers.new(name=name).data.foreach_set('uv',np.concatenate((values[kept],newUV)).ravel())
 mesh.uv_layers.active=mesh.uv_layers['VitruvianUV.UDIM'];mesh.uv_layers['VitruvianUV.UDIM'].active_render=True
 for name,(kind,prop,width) in names.items():mesh.attributes.new('AFN101_'+name,kind,'POINT').data.foreach_set(prop,attrs[name].ravel())
 mesh.attributes.new('AFN102_R101ParentFaceID','INT','FACE').data.foreach_set('value',np.r_[sourceParent[kept],np.full(len(newFaces),-1)].astype('i4'));mesh.attributes.new('AFN103_R102ParentFaceID','INT','FACE').data.foreach_set('value',np.r_[kept,np.full(len(newFaces),-1)].astype('i4'));hm=bpy.data.meshes.new('AFN103_EDITABLE_CORRESPONDING_FRONT_BANDS');patch=NT[np.any(attrs['OriginalCIndex'][NT]<0,axis=1)];hm.from_pydata(keys['Basis'].tolist(),[],[[hmap[int(i)] for i in tri] for tri in patch]);hm.update();reference=helper.copy();reference.data=oldHelper;scene.collection.objects.link(reference);reference.name='AFN103_REFERENCE_R102_INNER_AND_FRONT_SOURCE';reference.hide_render=True;reference.hide_set(True);helper.data=hm
 for name in ['Basis','AFN101_Closed_L','AFN101_Closed_R']:
  key=helper.shape_key_add(name=name);key.data.foreach_set('co',keys[name].ravel())
  if name!='Basis':
   driver=key.driver_add('value').driver;driver.type='SCRIPTED';var=driver.variables.new();var.name='blink';var.targets[0].id=face;var.targets[0].data_path='["blink_'+('left' if name.endswith('_L') else 'right')+'"]';driver.expression='min(1,max(0,blink))'
 skin.data=mesh;skin.update_tag();helper.update_tag();bpy.context.view_layer.update();b.deliver(0);dd,W,TT=b.geom(skin);newOrig=q.arr(dd.attributes['AFN101_OriginalCIndex'].data,'value',len(W),dtype='i4');newPatch=q.arr(dd.attributes['AFN101_PatchIndex'].data,'value',len(W),dtype='i4');newKeys=np.where(newOrig>=0,newOrig,677442+newPatch);sort=np.argsort(newKeys);lookup={int(k):int(i) for i,k in enumerate(newKeys)};mapping=np.array([lookup.get(int(k),-1) for k in oldKeys],'i4');keepOld=mapping>=0;assert (mapping<0).sum()==320;oldError=float(np.linalg.norm(W[mapping[keepOld]]-V0[keepOld],axis=1).max());assert oldError<4e-6
 for j in range(3):
  at=hair.data.attributes['AFN97_ScalpVertex'+str(j)];ids=q.arr(at.data,'value',24800,dtype='i4');assert (mapping[ids]>=0).all();at.data.foreach_set('value',mapping[ids])
 hair.data.update_tag();hair.update_tag();bpy.context.view_layer.update();hairError=float(np.linalg.norm(q.hair(hair)-hair0,axis=1).max());assert hairError<6e-6
 bindings=json.loads((OLD/'a-retained-lash-bindings.json').read_text('utf8'));marginMask=(newOrig<0)&(q.arr(dd.attributes['AFN101_FollowWeight'].data,'value',len(W))==0)&(q.arr(dd.attributes['AFN101_Clearance'].data,'value',len(W))>.0003/A[0,0]);front=q.arr(dd.polygons,'material_index',len(dd.polygons),dtype='i4')==4;chosen=TT[front&(marginMask[TT].sum(1)==2)];edgeThird={tuple(sorted(map(int,tri[marginMask[tri]]))):int(tri[~marginMask[tri]][0]) for tri in chosen};assert len(edgeThird)==320;LA=np.array(lash.matrix_world);LI=np.linalg.inv(LA[:3,:3]);LV=(W-LA[:3,3])@LI.T;HL=(H0-LA[:3,3])@LI.T;offset=np.zeros_like(HL);ids=np.zeros((len(H0),3),'i4')
 for row in bindings:
  pair=mapping[np.array(row['actualSkinTriangle'][:2])];assert (pair>=0).all();tri=np.r_[pair,edgeThird[tuple(sorted(map(int,pair)))]];row['actualSkinTriangle']=tri.tolist();a=LV[tri];tangent=a[1]-a[0];tangent/=np.linalg.norm(tangent);normal=np.cross(a[1]-a[0],a[2]-a[0]);normal/=np.linalg.norm(normal);bitangent=np.cross(normal,tangent);frame=np.column_stack((tangent,bitangent,normal));start=row['pointStart'];end=start+row['points'];offset[start:end]=(HL[start:end]-HL[start])@frame;ids[start:end]=tri
 for j in range(3):lash.data.attributes['AFN101_LashVertex'+str(j)].data.foreach_set('value',ids[:,j])
 lash.data.attributes['AFN101_LashLocalFrameOffset'].data.foreach_set('vector',offset.astype('f4').ravel());lash.data.update_tag();lash.update_tag();bpy.context.view_layer.update();lashMove=float(np.linalg.norm(q.geom(lash)[1]-H0,axis=1).max());save('a-retained-lash-bindings.json',bindings);save('a-authored-front-profiles.json',{'bands':profiles,'referenceURLs':['https://eyewiki.aao.org/Eyelid_Reconstruction','https://eyewiki.aao.org/Single_Fold/Double_Fold_Lid_Surgery'],'noReferenceImagesTextModelsOrClinicalDimensionsCopied':True,'construction':'Replaced original front mid-strip topology; separate pretarsal/crease/fold/preseptal stations with corresponding open/closed shapes. Original anatomical margins and adaptive inner lining unchanged. Artistic approximation, not medical or physiological validation.'});np.savez_compressed(E/'a-front-band-lineage.npz',originalActualToNewActual=mapping,removedR102FaceIDs=np.flatnonzero(remove),newRawVertexIDs=np.arange(newRawStart,len(P)),removedOldMidRawVertexIDs=midIDs,newFaceRawIDs=newFaces)
 save('a-build-summary.json',{'source':str(SRC),'sourceSha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'output':str(OUT),'renderSkin':skin.name,'editableComponent':helper.name,'sourceActualVertices':len(V0),'newActualVertices':len(W),'newActualFaces':len(TT),'removedOldFrontMidControls':320,'addedAnatomicalBandControls':1600,'retainedActualVerticesMaximumWorldDifferenceM':oldError,'allGroomControlsMaximumWorldDifferenceM':hairError,'allLashControlsMaximumWorldMoveAfterActualFrontRebindingM':lashMove,'newPointTopologyAndOpenClosedProfilesAuthored':True,'r102InnerLiningAndOriginalRetainedBodyUVMaterialsRadiiUnedited':True,'completeAppearanceOperationContactRuntimeAccepted':False,'secondsBeforePreview':time.time()-tick})
 for ob in [face,oral]:
  for k,value in props[ob.name].items():ob[k]=value
  if ob.animation_data:ob.animation_data.action=actions[ob.name]
  ob.update_tag()
 scene.frame_set(1);bpy.context.view_layer.update();b.m.m.rig.shade.settings();b.m.m.rig.k.b.camera('face');scene.camera.data.lens=85;scene.render.hair_subdiv=3;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True);views=[]
 for view in ['face','profile','body-face']:views.append(v.image('a-anatomical-bands',view));save('a-view-controls.json',views)
 print('R103_FIRST_COMPLETE_PREVIEW_DONE',time.time()-tick,flush=True)
 for ob in [face,oral]:
  if ob.animation_data:ob.animation_data.action=None
 for label,value in [('half',.5),('closed',1.)]:b.deliver(value);views.append(v.image('a-anatomical-bands-'+label,'face'));save('a-view-controls.json',views)
 print('R103_ANATOMICAL_FRONT_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
