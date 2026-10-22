"""One actual current-head hairline candidate with shared immutable mesh library."""
from pathlib import Path
import bpy,numpy as np,json,datetime,time,importlib.util,hashlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0153-current-hairline';S=R/'engine/assets/characters/female-next/source';SRC=S/'r0152-source/aevrynd-female-next-r0152-a-layered-native-groom.blend';OUT=S/'r0153-source/aevrynd-female-next-r0153-a-current-hairline.blend'
sp=importlib.util.spec_from_file_location('r153buildbase',Path(__file__).with_name('build-female-next-r0149-native-physical-groom.py'));base=importlib.util.module_from_spec(sp);sp.loader.exec_module(base);a=base.a;a.b.u.v.E=E
def save(n,x):(E/n).write_bytes((json.dumps(x,indent=2,ensure_ascii=False,default=lambda q:q.tolist() if isinstance(q,np.ndarray) else q.item() if isinstance(q,np.generic) else str(q))+'\n').encode())
def main():
 tick=time.time();assert not OUT.exists();assert a.a.sha(SRC)=='6d14dcca0c0a3dc2a8be613d92377a663522dbb8d31a3f26ec894132723f1480'
 # Append source scene into an empty main file, then reference the exact old mesh
 # data as a library. Actual objects, native rig and new hair remain local.
 bpy.ops.wm.read_factory_settings(use_empty=True)
 with bpy.data.libraries.load(str(SRC),link=False) as (fr,to):to.scenes=[fr.scenes[0]]
 scene=to.scenes[0];bpy.context.window.scene=scene;scene.frame_set(1);bpy.context.view_layer.update();names=a.FIXED+a.MOVING;raw={n:a.rawsig(bpy.data.objects[n]) for n in names};world={n:[a.a.hasharray(x) for x in a.geometry(bpy.data.objects[n])] for n in names};meshNames=[bpy.data.objects[n].data.name for n in names]
 with bpy.data.libraries.load(str(SRC),link=True) as (fr,to):to.meshes=meshNames
 for n,data in zip(names,to.meshes):assert data.library is not None;bpy.data.objects[n].data=data
 bpy.data.batch_remove(ids=[o for o in bpy.data.objects if o.name in ['AFN152_ACTUAL_NATIVE_NEIGHBOUR_GROOM','AFN152_LIVE_NATIVE_NEIGHBOUR_GUIDES','AFN152_ACTUAL_SCALP_ROOT_POINTS']])
 for o in bpy.data.objects:
  if o.type=='MESH' and o.name in names:o.hide_render=False;o.hide_set(False)
 for coll in [bpy.data.meshes,bpy.data.materials,bpy.data.images,bpy.data.node_groups,bpy.data.hair_curves]:
  for d in coll:
   if not d.library:d.use_fake_user=False
 bpy.data.orphans_purge(do_local_ids=True,do_linked_ids=True,do_recursive=True);bpy.context.view_layer.update();assert raw=={n:a.rawsig(bpy.data.objects[n]) for n in names};assert world=={n:[a.a.hasharray(x) for x in a.geometry(bpy.data.objects[n])] for n in names}
 skin=bpy.data.objects[names[0]];V,T=a.geometry(skin);cache=np.load(E.parent/'r0150-authored-rooted-locks/actual-current-scalp.npz');scalpFaces=cache['scalpFaces'];scalpTree=BVHTree.FromPolygons([Vector(x) for x in V],T[scalpFaces].tolist(),all_triangles=True)
 # Explicit artist-sized frontal/temporal sections. These describe SHORT root
 # transitions, never a whole-head rest hairstyle or an imported guide fit.
 anchors=np.array([[-.064,-.080,1.494],[-.052,-.096,1.517],[-.035,-.110,1.532],[-.015,-.118,1.538],[0,-.118,1.540],[.015,-.118,1.538],[.035,-.110,1.532],[.052,-.096,1.517],[.064,-.080,1.494]])
 snapped=np.array([scalpTree.find_nearest(Vector(p))[0][:] for p in anchors]);tri=T[scalpFaces];center=V[tri].mean(1);distance=np.linalg.norm(center[:,None,:]-snapped[None,:,:],axis=2).min(1);selected=np.flatnonzero((distance<.009)&(center[:,1]<-.065));assert len(selected)>20
 area=np.linalg.norm(np.cross(V[tri[selected,1]]-V[tri[selected,0]],V[tri[selected,2]]-V[tri[selected,0]]),axis=1)*.5;rng=np.random.default_rng(1531128);count=1300;stations=13;owner=rng.choice(selected,count,p=area/area.sum());rt=tri[owner];rr=rng.random((count,2));ss=np.sqrt(rr[:,0]);bc=np.c_[1-ss,ss*(1-rr[:,1]),ss*rr[:,1]];roots=(V[rt]*bc[:,:,None]).sum(1);normal=np.cross(V[rt[:,1]]-V[rt[:,0]],V[rt[:,2]]-V[rt[:,0]]);normal/=np.linalg.norm(normal,axis=1,keepdims=True)
 P=[];lengths=rng.uniform(.006,.022,count);lift=rng.uniform(.0004,.0018,count)
 for i,(root,n) in enumerate(zip(roots,normal)):
  side=-1 if root[0]<-.001 else 1;direction=np.array([side*.48,.80,.28]);direction-=n*np.dot(direction,n);direction/=np.linalg.norm(direction);points=[]
  for j,t in enumerate(np.linspace(0,1,stations)):
   if j==0:points.append(root);continue
   q,nn,_,_=scalpTree.find_nearest(Vector(root+direction*(lengths[i]*t)));points.append(np.array(q)+np.array(nn)*(.00012+lift[i]*np.sin(np.pi*t*.8)))
  P.append(points)
 P=np.asarray(P,'f4');d=bpy.data.hair_curves.new('AFN153_ACTUAL_SHORT_HAIRLINE_DATA');d.add_curves([stations]*count);d.position_data.foreach_set('vector',P.ravel());hair=bpy.data.objects.new('AFN153_ACTUAL_CURRENT_SCALP_SHORT_HAIRLINE',d);scene.collection.objects.link(hair);d.surface=skin;d.surface_uv_map='AngelicaOriginalUV'
 skin.data.calc_loop_triangles();uv=skin.data.uv_layers['AngelicaOriginalUV'];rootUV=[]
 for face,bary in zip(scalpFaces[owner],bc):
  lt=skin.data.loop_triangles[int(face)];rootUV.append((np.array([uv.data[k].uv[:] for k in lt.loops])*bary[:,None]).sum(0))
 d.attributes.new('surface_uv_coordinate','FLOAT2','CURVE').data.foreach_set('vector',np.asarray(rootUV,'f4').ravel());radii=np.tile(np.linspace(.00003,.000004,stations),count).astype('f4');d.attributes['radius'].data.foreach_set('value',radii)
 A=V[rt[:,0]];ax=V[rt[:,1]]-A;ax/=np.linalg.norm(ax,axis=1,keepdims=True);az=normal;ay=np.cross(az,ax);delta=P-P[:,0,None];local=np.stack([(delta*ax[:,None]).sum(2),(delta*ay[:,None]).sum(2),(delta*az[:,None]).sum(2)],axis=2);base.bind(hair,skin,rt,bc,local,P)
 mat=bpy.data.materials.new('AFN153_SHORT_HAIRLINE_CHIANG');mat.use_nodes=True;n=mat.node_tree.nodes;n.clear();bs=n.new('ShaderNodeBsdfHairPrincipled');bs.parametrization='MELANIN';bs.inputs['Melanin'].default_value=.95;bs.inputs['Melanin Redness'].default_value=.15;bs.inputs['Roughness'].default_value=.35;bs.inputs['Radial Roughness'].default_value=.45;out=n.new('ShaderNodeOutputMaterial');mat.node_tree.links.new(bs.outputs[0],out.inputs['Surface']);d.materials.append(mat);bpy.context.view_layer.update();actual=a.q.hair(hair);assert len(actual)==count*stations and np.isfinite(actual).all();rootError=float(np.linalg.norm(actual.reshape(count,stations,3)[:,0]-roots,axis=1).max());assert rootError<3e-6
 save('direct-current-native-hairline-integration.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'nativeCurves':count,'nativePoints':len(actual),'actualRootMaximumErrorM':rootError,'actualDisplayedHair':hair.name,'actualCurrentSkin':skin.name,'realSurfaceUVAttribute':True,'originalSevenMeshesUVAndNeutralGeometryExact':True,'localObjectsRigAndActionWithSharedImmutableMeshData':True,'scopedShortHairlineOnlyNotWholeGroomSolution':True,'anchors':snapped,'existingLongHairAndItsKnownDefectsRetainedNotHidden':True})
 np.savez_compressed(E/'hairline-authoring.npz',points=P,rootTriangles=rt,rootBarycentric=bc,rootFaceIds=scalpFaces[owner],rootUV=np.asarray(rootUV),radii=radii)
 scene.render.threads_mode='FIXED';scene.render.threads=4;scene.render.hair_type='STRIP';bpy.context.preferences.filepaths.save_version=0;OUT.parent.mkdir(exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=True);assert OUT.stat().st_size<14000000
 save('a-build-summary.json',{'source':str(SRC),'sourceSha256':a.a.sha(SRC),'output':str(OUT),'sha256':a.a.sha(OUT),'bytes':OUT.stat().st_size,'actualHair':hair.name,'actualSkin':skin.name,'sharedImmutableLibrary':str(SRC),'libraryRelativePath':bpy.data.libraries[0].filepath,'standaloneReopenNeedsPreservedExistingLibraryAndTextures':True,'meshDataEditableViaBlenderMakeLocalOrSourceWorkflowNotYetVerified':True,'newCharacterOperationAccepted':False,'originalStartedUTC':'2026-10-22T06:35:30+00:00','secondsBeforePreview':time.time()-tick})
 views=[]
 for view in ['face','body-face','profile','oblique','back']:views.append(a.b.u.v.image('a-current-hairline',view));save('a-view-controls.json',views)
 assert a.a.sha(SRC)=='6d14dcca0c0a3dc2a8be613d92377a663522dbb8d31a3f26ec894132723f1480';print('R153_COMPLETE_CURRENT_WOMAN_SHORT_HAIRLINE_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
