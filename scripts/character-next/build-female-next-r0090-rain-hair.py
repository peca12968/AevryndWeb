"""Second r90 construction: attributed professionally authored polygonal hair.
Only hair component data/UV/materials/maps are used on the same complete woman.
No Rain body/face/rig/tool code is integrated. Static art fit, not a solver.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
from mathutils import Matrix
R=Path(r'D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0090-native-scalp-groom';REF=R/'Reference/character/blender-studio-rain-v3-cc-by4';RAIN=REF/'Rain v3.3/rain_v3.2.blend';SRC=S/'aevrynd-female-next-r0088-b-supported-lid-aperture.blend';OUT=S/'aevrynd-female-next-r0090-b-rain-hair-shape-study.blend'
def mod(n,f):
 sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(f));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
m=mod('r90rainsource','build-female-next-r0081-editable-curly.py');q=m.q;v=mod('r90rainviews','render-female-next-r0081-retained-study.py');v.E=E
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x):(E/n).write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def native_mesh(o):
 P=q.arr(o.data.vertices,'co',len(o.data.vertices),3).astype('f8');A=np.array(o.matrix_world);return P@A[:3,:3].T+A[:3,3]
def main():
 tick=time.time();assert not OUT.exists() and sha(SRC)=='72435890a03cab26ff2f3e238060daf2b2cf797f85543d8fd6182583cc1101a7';assert sha(REF/'Rain-v3.3.zip')=='80217f163f6392dc829233d63c2cfb5e1376775bc34101ad14f39631fea70d24';bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();beforeObjects=set(bpy.data.objects);beforeTexts=set(bpy.data.texts);beforeImages=set(bpy.data.images);beforeMaterials=set(bpy.data.materials);beforeCollections={n:set(getattr(bpy.data,n)) for n in ('meshes','armatures','lattices','materials')};mats={x.name:m.rig.k.f.v.v32.material_signature(x) for x in beforeMaterials if x.use_nodes};lights=m.m.q.lights();targetEyes=[]
 for n in ('AFN60_L_EYE_OUTER_SHELL_APPROX','AFN60_R_EYE_OUTER_SHELL_APPROX'):
  P=q.geom(bpy.data.objects[n])[1];targetEyes.append((P.min(0)+P.max(0))*.5)
 targetEyes=np.array(sorted(targetEyes,key=lambda p:p[0]));targetEye=targetEyes.mean(0);head=np.load(E/'actual-head-surface.npz')['world'];targetTop=float(head[:,2].max());targetBack=float(head[head[:,2]>=targetEye[2],1].max())
 names=['GEO-rain-head','GEO-rain-eyes','GEO-rain-hair_main','GEO-rain-hair_ponytail','GEO-rain-hair_strand','GEO-rain-hairband']
 with bpy.data.libraries.load(str(RAIN),link=False) as (src,dst):dst.objects=names;dst.texts=['ReadMe.txt']
 donorHead,donorEyes,*hair=dst.objects;readme=dst.texts[0].as_string();assert 'https://creativecommons.org/licenses/by/4.0/' in readme;(E/'rain-embedded-ReadMe.txt').write_text(readme,encoding='utf-8');HP=native_mesh(donorHead);EP=native_mesh(donorEyes);sourceEyes=np.array([(EP[EP[:,0]<0].min(0)+EP[EP[:,0]<0].max(0))*.5,(EP[EP[:,0]>0].min(0)+EP[EP[:,0]>0].max(0))*.5]);sourceEye=sourceEyes.mean(0);sourceTop=float(HP[:,2].max());sourceBack=float(HP[HP[:,2]>=sourceEye[2],1].max());scale=np.array([(targetEyes[1,0]-targetEyes[0,0])/(sourceEyes[1,0]-sourceEyes[0,0]),(targetBack-targetEye[1])/(sourceBack-sourceEye[1]),(targetTop-targetEye[2])/(sourceTop-sourceEye[2])]);shift=targetEye-sourceEye*scale;assert np.all(scale>.25) and np.all(scale<1.5);sourceGeometry={o.name:native_mesh(o) for o in hair};sourceUV={o.name:{uv.name:q.arr(uv.data,'uv',len(o.data.loops),2).copy() for uv in o.data.uv_layers} for o in hair};bandCenter=sourceGeometry['GEO-rain-hairband'].mean(0);angle=np.deg2rad(-80.);RX=np.array([[1,0,0],[0,np.cos(angle),-np.sin(angle)],[0,np.sin(angle),np.cos(angle)]]);rows=[];expected={};oldNames={}
 for o in hair:
  originalName=o.name;P=sourceGeometry[originalName].copy();tail=originalName=='GEO-rain-hair_ponytail'
  if tail:P=(P-bandCenter)@RX.T+bandCenter
  Q=P*scale+shift;o.data=o.data.copy();o.parent=None;o.animation_data_clear()
  for con in list(o.constraints):o.constraints.remove(con)
  for md in list(o.modifiers):
   if md.type!='SUBSURF':o.modifiers.remove(md)
  if o.data.shape_keys:o.shape_key_clear()
  o.vertex_groups.clear();o.data.vertices.foreach_set('co',Q.astype('f4').ravel());o.matrix_world=Matrix.Identity(4);o.name='AFN90_RAIN_'+originalName.removeprefix('GEO-rain-').upper();s.collection.objects.link(o);o.hide_render=False;o.hide_set(False)
  for face in o.data.polygons:face.use_smooth=True
  for md in o.modifiers:
   if md.type=='SUBSURF':md.levels=md.render_levels=min(2,md.render_levels)
  o['source']='Rain Rig (CC) Blender Foundation | studio.blender.org';o['sourceLicense']='CC-BY4.0';o['scope']='Attributed editable textured polygonal hair component only, no individual physical strands. Landmark affine art fit; tail posed once toward gravity, not simulated. No source rig/lattice/tool scripts. Contact, deformation and Aevrynd runtime unaccepted.';expected[o.name]=Q;oldNames[o.name]=originalName
  for uv in o.data.uv_layers:assert np.array_equal(q.arr(uv.data,'uv',len(o.data.loops),2),sourceUV[originalName][uv.name])
  rows.append({'object':o.name,'publisherObject':originalName,'nativeVertices':len(Q),'nativeFaces':len(o.data.polygons),'UVLayers':list(sourceUV[originalName]),'tailStaticPoseDegrees':-80 if tail else None,'worldBounds':[Q.min(0).tolist(),Q.max(0).tolist()],'materials':[a.name if a else None for a in o.data.materials]})
 # Strip only newly imported rig/UI data. Existing woman's data are protected.
 keep=set(hair)
 for o in list(bpy.data.objects):
  if o not in beforeObjects and o not in keep:bpy.data.objects.remove(o,do_unlink=True)
 removedTexts=[]
 for text in list(bpy.data.texts):
  if text not in beforeTexts:removedTexts.append(text.name);bpy.data.texts.remove(text)
 # Remove orphan imported component data before packing only used hair maps.
 for name in ('meshes','armatures','lattices','materials'):
  collection=getattr(bpy.data,name)
  for d in list(collection):
   if d not in beforeCollections[name] and d.users==0:collection.remove(d)
 packed=[]
 for im in list(bpy.data.images):
  if im in beforeImages:continue
  if im.users==0:bpy.data.images.remove(im);continue
  name=Path(im.filepath.replace('\\','/')).name;path=RAIN.parent/'textures'/name
  assert name.startswith('TEX-rain_hair_') and path.is_file(),(im.name,name)
  im.filepath=str(path);im.pack();packed.append({'name':im.name,'source':str(path),'sha256':sha(path),'packed':bool(im.packed_file)})
 assert len(packed)==3;old=bpy.data.objects['AFN81_EDITABLE_CURLY_GUIDES'];old.hide_render=True;old.hide_set(True);assert {n:m.rig.k.f.v.v32.material_signature(bpy.data.materials[n]) for n in mats}==mats and m.m.q.lights()==lights;bpy.context.view_layer.update();nativeErrors={o.name:float(np.linalg.norm(native_mesh(o)-expected[o.name],axis=1).max()) for o in hair};assert max(nativeErrors.values())<2e-6;s['AFN90_RAIN_scope']='Four attributed static polygonal hair components on unchanged existing woman. Rain body/face/rig and Python texts removed. Original source zip+CC-BY4 notice retained. No natural hair dynamics or full contacts/runtime acceptance.';m.rig.shade.settings();m.rig.k.b.camera('face');s.camera.data.lens=85;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
 arrays={}
 for o in hair:arrays[o.name+'_sourceWorld']=sourceGeometry[oldNames[o.name]];arrays[o.name+'_targetWorld']=expected[o.name]
 np.savez_compressed(E/'b-rain-hair-lineage.npz',**arrays,scale=scale,shift=shift,sourceEyes=sourceEyes,targetEyes=targetEyes,bandCentre=bandCenter,tailPoseRotation=RX)
 save('b-build-summary.json',{'source':str(SRC),'sourceSha256':sha(SRC),'publisherBlend':str(RAIN),'publisherBlendSha256':sha(RAIN),'publisherZipSha256':sha(REF/'Rain-v3.3.zip'),'output':str(OUT),'outputSha256':sha(OUT),'outputBytes':OUT.stat().st_size,'construction':'Professionally authored complete four-component polygonal hairstyle/material/UV/maps from Rain, on the same existing woman. This is a new authored mesh/texture basis, not a density/radius/shader variant of failed guide formulas.','components':rows,'scale':scale.tolist(),'shift':shift.tolist(),'registrationLandmarks':{'sourceEyeAABBCentres':sourceEyes.tolist(),'targetEyeAABBCentres':targetEyes.tolist(),'sourceSkullTop':sourceTop,'targetSkullTop':targetTop,'sourcePosteriorAboveEyePlane':sourceBack,'targetPosteriorAboveEyePlane':targetBack},'artFitNotAnatomicalAttachmentOrClearanceProof':True,'staticTailPoseDegrees':-80,'nativeVertexMaximumWorldErrorsM':nativeErrors,'packedHairMaps':packed,'removedImportedTexts':removedTexts,'sourceRigLatticeToolScriptsRequiredInOutput':False,'sourceBodyFaceNotTransferred':True,'originalWomanCagesMaterialTreesLightsUnedited':True,'physicalStrandsNaturalDynamicsContactOrRuntimeAccepted':False,'secondsBeforePreview':time.time()-tick})
 rows=[]
 for view in ('back','face','body-face'):rows.append(v.image('b-rain-hair',view));save('b-rain-view-controls.json',rows)
 print('R90_RAIN_HAIR_PILOT_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
