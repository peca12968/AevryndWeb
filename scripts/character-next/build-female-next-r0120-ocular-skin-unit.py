"""One coupled native ocular skin/inner-wall/blink construction around fixed eye anatomy."""
from pathlib import Path
import bpy,numpy as np,json,time,datetime,hashlib,importlib.util
R=Path('D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0120-ocular-socket-construction';SRC=S/'r0119-source/aevrynd-female-next-r0119-b-native-iris-landmark-eyes.blend';OUT=S/'r0120-source/aevrynd-female-next-r0120-a-coupled-ocular-skin.blend'
sp=importlib.util.spec_from_file_location('r120base',Path(__file__).with_name('build-female-next-r0119-anatomical-eyes.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);b=a.b;q=a.q;b.u.v.E=E
def save(n,j):(E/n).write_text(json.dumps(j,indent=2,default=lambda x:x.tolist() if isinstance(x,np.ndarray) else x.item())+'\n',encoding='utf-8',newline='\n')
def normals(P,T):
 n=np.zeros_like(P);f=np.cross(P[T[:,1]]-P[T[:,0]],P[T[:,2]]-P[T[:,0]])
 for j in range(3):np.add.at(n,T[:,j],f)
 return n/np.maximum(np.linalg.norm(n,axis=1),1e-30)[:,None]
def unit(P,normalY,centres):
 out=P.copy();changes=[]
 for C in centres:
  D=out-C;r=np.hypot(D[:,0],D[:,2]);insideXZ=r<a.GLOBE;z=np.sqrt(np.maximum(a.GLOBE*a.GLOBE-r*r,0));front=-z;co=r<=a.LIMBUS;front[co]=-a.APEX+a.sag(r[co],.00772,-.26)
  # Source anterior/posterior orientation is retained as a layer label. The
  # fixed 0.8mm separation / 0.1mm support gap is an authoring approximation,
  # not measured tear film/tissue thickness or a global contact certificate.
  layer=.0008*np.clip((1-normalY)/2,0,1);gap=.0001+layer
  anterior=insideXZ&(D[:,1]<=0)&(D[:,1]>=front-gap)&(D[:,1]<=z)
  out[anterior,1]=C[1]+front[anterior]-gap[anterior]
  distance=np.linalg.norm(D,axis=1);posterior=(D[:,1]>0)&(distance<a.GLOBE+gap);target=(a.GLOBE+gap[posterior])/np.maximum(distance[posterior],1e-30);out[posterior]=C+D[posterior]*target[:,None]
  changes.append({'frontVertices':int(anterior.sum()),'posteriorVertices':int(posterior.sum())})
 return out,changes
def main():
 tick=time.time();assert not OUT.exists();save('ocular-authoring-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'action':'Rebuild the actual complete skin and all own closure states as a coupled ocular support unit. Preserve native anterior/posterior source orientation, actual fixed r119 eye exterior, all source IDs/UV and lash surface attachments. Not isolated eye movement or a donor patch.'});digest=a.a.sha(SRC);bpy.ops.wm.open_mainfile(filepath=str(SRC));b.deliver(0);skin=bpy.data.objects['AFN113_COMPLETE_WOMAN_COHERENT_HEAD'];old=skin.data;d,W,T=b.u.b.geom(skin);W=W.copy();T=T.copy();A=np.array(skin.matrix_world);AI=np.linalg.inv(A[:3,:3]);oldKeys={k.name:q.arr(k.data,'co',len(k.data),3).copy() for k in old.shape_keys.key_blocks};assert list(oldKeys)==['Basis','AFN113_CLOSED_L','AFN113_CLOSED_R'];assert not any(len(v.groups) for v in old.vertices),'Do not silently drop any existing weights';loop=q.arr(d.loop_triangles,'loops',len(T),3,dtype='i4');polys=q.arr(d.loop_triangles,'polygon_index',len(T),dtype='i4');uvs={uv.name:q.arr(uv.data,'uv',len(d.loops),2)[loop].copy() for uv in d.uv_layers};mats=q.arr(d.polygons,'material_index',len(d.polygons),dtype='i4')[polys];sourceParent=q.arr(d.attributes['AFN117_NATIVE_PARENT_FACE'].data,'value',len(d.polygons),dtype='i4')[polys];centres=np.array([bpy.data.objects['AFN119_'+s+'_EYE_GAZE_CONTROL'].matrix_world.translation[:] for s in ['L','R']]);ny=normals(W,T)[:,1]
 fibres={n:q.hair(bpy.data.objects[n]).copy() for n in ['AFN97_TUCKED_ARTIST_BOB_CHILDREN','AFN57_NATIVE_BROWS','AFN57_NATIVE_LASHES']};radii={n:q.arr(bpy.data.objects[n].data.attributes['radius'].data,'value',len(p)).copy() for n,p in fibres.items()};poses={};records={};changed=set()
 for name,V in oldKeys.items():
  world=V@A[:3,:3].T+A[:3,3];authored,counts=unit(world,ny,centres);mask=np.linalg.norm(authored-world,axis=1)>1e-12;new=V.copy();new[mask]=((authored[mask]-A[:3,3])@AI.T).astype('f4');assert np.array_equal(new[~mask],V[~mask]);poses[name]=new;changed.update(np.flatnonzero(mask).tolist());records[name]={'changedVertices':int(mask.sum()),'maxAuthoredMoveM':float(np.linalg.norm(authored-world,axis=1).max()),'constructionCounts':counts,'allOtherVertexCoordinatesByteExact':True}
 changed=np.array(sorted(changed),'i4');mesh=bpy.data.meshes.new('AFN120_CONNECTED_OCULAR_LAMELLA_SKIN');mesh.from_pydata(poses['Basis'].tolist(),[],T.tolist());mesh.update();mesh.polygons.foreach_set('use_smooth',np.ones(len(T),bool));mesh.polygons.foreach_set('material_index',mats)
 for mat in old.materials:mesh.materials.append(mat)
 for name,uv in uvs.items():mesh.uv_layers.new(name=name).data.foreach_set('uv',uv.astype('f4').ravel())
 mesh.uv_layers.active=mesh.uv_layers['MakeHumanOriginalUV'];mesh.uv_layers['MakeHumanOriginalUV'].active_render=True
 for name in ['AFN113_NATIVE_COLOR_WEIGHT']:
  attr=old.attributes[name];values=q.arr(attr.data,'value',len(attr.data));mesh.attributes.new(name=name,type='FLOAT',domain='POINT').data.foreach_set('value',values)
 mesh.attributes.new(name='AFN117_NATIVE_PARENT_FACE',type='INT',domain='FACE').data.foreach_set('value',sourceParent);mesh.attributes.new(name='AFN120_SOURCE_ANTERIOR_POSTERIOR',type='FLOAT',domain='POINT').data.foreach_set('value',ny.astype('f4'));skin.data=mesh;basis=skin.shape_key_add(name='Basis');face=bpy.data.objects['AFN59_FACE_CONTROLS']
 for side,prop in [('L','blink_left'),('R','blink_right')]:
  name='AFN113_CLOSED_'+side;key=skin.shape_key_add(name=name);key.relative_key=basis;key.data.foreach_set('co',poses[name].ravel());b.oldbuild.drive(key,face,prop,'v')
 b.deliver(0);after={}
 for n,oldP in fibres.items():
  ob=bpy.data.objects[n];P=q.hair(ob);rad=q.arr(ob.data.attributes['radius'].data,'value',len(P));assert np.array_equal(rad,radii[n]);error=float(np.linalg.norm(P-oldP,axis=1).max());after[n]={'curves':len(ob.data.curves),'points':len(P),'allRadiiExact':True,'maximumWorldChangeM':error,'actualSurfaceAttachmentFollowsChangedDisplayedMesh':n=='AFN57_NATIVE_LASHES'}
  if n!='AFN57_NATIVE_LASHES':assert error==0
 outside=np.ones(len(W),bool);outside[changed]=False;assert np.array_equal(poses['Basis'][outside],oldKeys['Basis'][outside]);np.savez_compressed(E/'ocular-skin-authoring-lineage.npz',changedVertexIDs=changed,neutralSourceWorld=W[changed],sourceNormalY=ny[changed],eyeCentres=centres,**{name+'_oldLocal':V[changed] for name,V in oldKeys.items()},**{name+'_newLocal':V[changed] for name,V in poses.items()});skin['AFN120_scope']='Same connected full-body vertex IDs with stable original neutral triangulation and directly authored coupled ocular skin/posterior support/own closure states. Raw native coarse source retained as reference, not live reconstruction. Fixed support/lamella approximation, no full anatomy or finite/continuous contact acceptance.'
 save('a-build-summary.json',{'source':str(SRC),'output':str(OUT),'changedOriginalVertexIDs':changed,'actualOriginalAndNewVertices':len(W),'stableActualTriangles':len(T),'sourceCompleteSkinGraphPreservedAsNeutralTriangles':True,'originalUVAndMaterialAssignmentsRetained':True,'allOtherBodyVertexCoordinatesByteExact':True,'allNativeEyeGeometryAndPositionsUnchangedFromR119B':True,'allOwnClosureStatesAuthoredTogether':records,'allFibres':after,'originalNativeCoarseBodyRetainedAsReferenceNotLiveWorkingSource':True,'sourceLamellaLabel':'Original neutral anterior/posterior surface orientation; not measured tissue segmentation.','fixedAuthoringApproximation':{'supportGapM':.0001,'lamellaSeparationM':.0008,'notPhysicalTearFilmOrCalibratedGlobalThickness':True},'reference':'https://www.ncbi.nlm.nih.gov/books/NBK482304/','diagnostic':'actual-native-orbital-contact-faces.json','sourceMethodChange':'Full displayed tissue/inner cavity/all closure states and real lashes are coupled to the fixed external globe; not another isolated eye dimension/staging/material variant. No source faces removed or tests excluded.','actualRenderOccupancySelfGlobalContinuousContactsAndFullAnatomyUnaccepted':True,'secondsBeforePreview':time.time()-tick})
 b.deliver(0);bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=False);assert a.a.sha(SRC)==digest;rows=[]
 for view in ['face','body-face','oblique','profile','back']:rows.append(b.u.v.image('a-coupled-ocular-skin',view));save('a-view-controls.json',rows)
 for label,value in [('half',.5),('closed',1.),('restored',0.)]:b.deliver(value);rows.append(b.u.v.image('a-coupled-ocular-skin-'+label,'face'));save('a-view-controls.json',rows)
 print('R120_COMPLETE_COUPLED_OCULAR_SKIN_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
