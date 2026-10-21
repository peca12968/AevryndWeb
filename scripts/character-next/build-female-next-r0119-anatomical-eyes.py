"""Rebuild visible external eye anatomy; one fixed referenced construction, no parameter sweep."""
from pathlib import Path
import bpy,numpy as np,json,time,datetime,importlib.util,hashlib,os
R=Path('D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0119-anatomical-eye-rebuild';SRC=S/'r0117-source/aevrynd-female-next-r0117-a-native-fibre-brows.blend';OUT=S/'r0119-source/aevrynd-female-next-r0119-a-anatomical-eye-assembly.blend'
sp=importlib.util.spec_from_file_location('r119base',Path(__file__).with_name('build-female-next-r0116-native-eye-character.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);b=a.b;q=a.q;b.u.v.E=E
def save(n,j):(E/n).write_text(json.dumps(j,indent=2,default=lambda x:x.tolist() if isinstance(x,np.ndarray) else x.item())+'\n',encoding='utf-8',newline='\n')
N=128;GLOBE=.012;LIMBUS=.006;IRIS=.0055;PUPIL=.0015;IRIS_DEPTH=.0036;IRIS_THICKNESS=.00015
def sag(r,R,Q):return r*r/(R*(1+np.sqrt(1-(1+Q)*r*r/(R*R))))
APEX=float(np.sqrt(GLOBE**2-LIMBUS**2)+sag(LIMBUS,.00772,-.26))
def mesh(name,P,F,root,mats,indices=None,uv=None):
 # Exact authoring coincidences (axis poles / last meridian ring) share IDs.
 # Remove only zero-area index faces; do not leave unwelded touching seams.
 P=np.array(P);lookup={};points=[];first=[];remap=[]
 for i,p in enumerate(P):
  key=tuple(np.round(p,14));j=lookup.get(key)
  if j is None:j=len(points);lookup[key]=j;points.append(p);first.append(i)
  remap.append(j)
 faces=[];kept=[]
 for i,f in enumerate(F):
  row=[remap[v] for v in f];clean=[]
  for v in row:
   if not clean or v!=clean[-1]:clean.append(v)
  if len(clean)>1 and clean[0]==clean[-1]:clean.pop()
  if len(set(clean))>=3:faces.append(clean);kept.append(i)
 F=faces
 if uv is not None:uv=np.array(uv)[first]
 if indices is not None:indices=np.array(indices)[kept]
 me=bpy.data.meshes.new(name);me.from_pydata(np.array(points).tolist(),[],F);me.update();me.polygons.foreach_set('use_smooth',np.ones(len(F),bool));ob=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(ob);ob.parent=root
 for mat in mats:me.materials.append(mat)
 if indices is not None:me.polygons.foreach_set('material_index',np.array(indices,'i4'))
 if uv is not None:me.uv_layers.new(name='EyeSourceUV').data.foreach_set('uv',np.array([uv[v] for f in F for v in f],'f4').ravel())
 return ob
def lathe(profile):
 P=[]
 for r,y in profile:
  for t in np.arange(N)*2*np.pi/N:P.append([r*np.cos(t),y,r*np.sin(t)])
 F=[]
 for i in range(len(profile)-1):
  for j in range(N):k=(j+1)%N;F.append([i*N+j,i*N+k,(i+1)*N+k,(i+1)*N+j])
 return np.array(P),[list(reversed(f)) for f in F]
def opaque(name,image=None,color=(.5,.5,.5,1)):
 mat=bpy.data.materials.new(name);mat.use_nodes=True;nodes=mat.node_tree.nodes;p=next((n for n in nodes if n.bl_idname=='ShaderNodeBsdfPrincipled'),None) or nodes.new('ShaderNodeBsdfPrincipled');out=next((n for n in nodes if n.bl_idname=='ShaderNodeOutputMaterial'),None) or nodes.new('ShaderNodeOutputMaterial');mat.node_tree.links.new(p.outputs['BSDF'],out.inputs['Surface']);p.inputs['Base Color'].default_value=color;p.inputs['Roughness'].default_value=.32
 if image:
  tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image;uv=mat.node_tree.nodes.new('ShaderNodeUVMap');uv.uv_map='EyeSourceUV';mat.node_tree.links.new(uv.outputs['UV'],tex.inputs['Vector']);mat.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color'])
 return mat
def glass(name,ior):
 mat=opaque(name,color=(1,1,1,1));p=next(n for n in mat.node_tree.nodes if n.bl_idname=='ShaderNodeBsdfPrincipled');p.inputs['Roughness'].default_value=.025;p.inputs['Transmission Weight'].default_value=1.;p.inputs['IOR'].default_value=ior;return mat
def main():
 tick=time.time();assert not OUT.exists();firstStart=(E/'eye-authoring-start.json').read_bytes() if (E/'eye-authoring-start.json').exists() else None;save('eye-authoring-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'action':'Direct external eye/finite cap/independent annular iris/pupil aperture reconstruction on same r117 woman. New outer geometry replaces r87 preserved exterior; not inner offset/fold/depth variants.'});
 if firstStart is not None:(E/'eye-authoring-start.json').write_bytes(firstStart)
 digest=a.sha(SRC);bpy.ops.wm.open_mainfile(filepath=str(SRC));b.deliver(0);before=a.protected();oldImages={im:im.filepath for im in bpy.data.images};texture=S/'makehuman-native-eye-textures/brown_eye.png';assert texture.is_file();image=bpy.data.images.load(str(texture),check_existing=True)
 if image in oldImages:image=image.copy()
 image.name='AFN119_NATIVE_BROWN_SOURCE';image.filepath='//../makehuman-native-eye-textures/brown_eye.png';sclera=opaque('AFN119_SOURCE_TEXTURED_SCLERA',image);iris=opaque('AFN119_SOURCE_TEXTURED_IRIS',image);front=glass('AFN119_AIR_TO_CORNEA',1.376);back=glass('AFN119_CORNEA_TO_AQUEOUS',1.376/1.3374);dark=opaque('AFN119_INTERNAL_ABSORBER_APPROX',color=(.0005,.0003,.0002,1));ciliary=opaque('AFN119_CILIARY_BACKING_APPROX',color=(.025,.012,.008,1));centres=json.loads((E.parent/'r0113-coherent-head-foundation/coherent-native-head-b.json').read_text('utf-8'))['nativeEyeCentresWorld'];rows=[];arrays={}
 for side,C in zip(['L','R'],centres):
  root=bpy.data.objects.new('AFN119_'+side+'_EYE_GAZE_CONTROL',None);bpy.context.scene.collection.objects.link(root);root.location=C;root['gaze_yaw']=0.;root['gaze_pitch']=0.;root['scope']='Actual independent eye assembly rotations, radians; neutral sampled tests required, not body/face rig qualification.'
  for axis,expr in [(0,'-pitch'),(2,'yaw')]:
   dr=root.driver_add('rotation_euler',axis).driver;dr.expression=expr;v=dr.variables.new();v.name='pitch' if axis==0 else 'yaw';v.targets[0].id=root;v.targets[0].data_path='["gaze_pitch"]' if axis==0 else '["gaze_yaw"]'
  cu,cv=(.2842,.2451) if side=='L' else (.7041,.7031)
  def uv(P):return np.c_[cu+P[:,0]/IRIS*.115,cv+P[:,2]/IRIS*.115]
  # Finite scleral shell with an actual anterior circular opening. The poles
  # use a tiny explicit authoring ring; no claim of exact biological thickness.
  theta=np.linspace(np.arcsin(LIMBUS/GLOBE),np.pi,48);outer=[(GLOBE*np.sin(t),-GLOBE*np.cos(t)) for t in theta];inner=[((GLOBE-.0005)*np.sin(t),-(GLOBE-.0005)*np.cos(t)) for t in theta[::-1]];profile=outer+inner+[outer[0]];P,F=lathe(profile);sc=mesh('AFN119_'+side+'_FINITE_SCLERA',P,F,root,[sclera],uv=uv(P));parts=[sc]
  # True aspheric front/back cap, not a normal-offset copy of the old sphere.
  r=np.linspace(0,LIMBUS,33);fp=[(rr,-APEX+float(sag(rr,.00772,-.26))) for rr in r];bp=[(rr,-APEX+.00055+float(sag(rr,.0065,0))) for rr in r[::-1]];P,F=lathe(fp+bp+[fp[0]]);mi=[0 if i<32 else 1 for i in range(len(fp)+len(bp)) for j in range(N)];mi=mi[:len(F)];co=mesh('AFN119_'+side+'_FINITE_ASPHERIC_CORNEA',P,F,root,[front,back],indices=mi);parts.append(co)
  # Independent solid annulus with an actual unfilled pupil and finite wall.
  rr=np.linspace(PUPIL,IRIS,12);profile=[(r,-APEX+IRIS_DEPTH) for r in rr]+[(r,-APEX+IRIS_DEPTH+IRIS_THICKNESS) for r in rr[::-1]]+[(PUPIL,-APEX+IRIS_DEPTH)];P,F=lathe(profile);ir=mesh('AFN119_'+side+'_FINITE_IRIS_AND_PUPIL_APERTURE',P,F,root,[iris],uv=uv(P));ir['pupilRadiusM']=PUPIL;ir['apertureIsHoleNotBlackDisk']=True;parts.append(ir)
  # Non-optical dark backing is an explicit art approximation, not a lens or
  # retina simulation and not the r87 displaced irregular pupil well.
  P,F=lathe([(0.,.006),(.008,.006),(.008,.0062),(0.,.0062),(0.,.006)]);parts.append(mesh('AFN119_'+side+'_POSTERIOR_ABSORBER_APPROX',P,F,root,[dark]))
  P,F=lathe([(IRIS,-APEX+IRIS_DEPTH),(LIMBUS,-np.sqrt(GLOBE**2-LIMBUS**2)),(LIMBUS,-np.sqrt(GLOBE**2-LIMBUS**2)+.0002),(IRIS,-APEX+IRIS_DEPTH+.0002),(IRIS,-APEX+IRIS_DEPTH)]);parts.append(mesh('AFN119_'+side+'_CILIARY_BACKING_APPROX',P,F,root,[ciliary]))
  for ob in parts:
   d,P,T=b.u.b.geom(ob);arrays[ob.name+'_world']=P.copy();arrays[ob.name+'_triangles']=T.copy()
  rows.append({'side':side,'centreWorld':C,'gazeRoot':root.name,'parts':[ob.name for ob in parts],'noWholeEyeScaleOrExtraFitting':True})
  for name in ['AFN113_'+side+'_SCLERA','AFN113_'+side+'_IRIS']:ob=bpy.data.objects[name];ob.hide_render=True;ob.hide_set(True)
 bpy.context.view_layer.update();assert a.protected()==before
 for im,path in oldImages.items():assert im.filepath==path
 np.savez_compressed(E/'anatomical-eye-assembly-lineage.npz',**arrays)
 params={'referenceImplementation':'https://www.mathworks.com/help/images/create-human-eye-model-schematic.html','originalPaperMetadataAbstractOnly':'https://opg.optica.org/josaa/abstract.cfm?uri=josaa-2-8-1273','primaryPublicationFullTextAccessNotAvailable':True,'anteriorRadiusM':.00772,'anteriorConic':-.26,'posteriorRadiusM':.0065,'posteriorConic':0,'centralCorneaThicknessM':.00055,'corneaIOR':1.376,'aqueousIOR':1.3374,'limbusRadiusM':LIMBUS,'globeRadiusM':GLOBE,'irisOuterRadiusM':IRIS,'pupilRadiusM':PUPIL,'irisPlaneFromApexM':IRIS_DEPTH,'irisThicknessM':IRIS_THICKNESS,'ownGlobeIrisScleralThicknessStagingAndBackingNotValidatedBiometry':True,'noLensRetinaAccommodationOrFullOpticalSimulation':True,'noMatlabOrExternalRuntimeCodeUsed':True}
 save('anatomical-reference-and-parameters.json',params);save('a-build-summary.json',{'source':str(SRC),'output':str(OUT),'parts':rows,'parameters':params,'allProtectedBodyKeysHairBrowsLashesBefore':before,'allProtectedBodyKeysHairBrowsLashesAfter':a.protected(),'allProtectedGeometryAndRadiiByteExact':True,'oldImagePathsUnchanged':True,'oldOpticsHiddenAndOriginalSourcePreserved':True,'irisUVSourceApproximation':'Original1024px CC0 brown atlas, observed circle centres and115px outer radius; original PNG unchanged, not a captured subject eye.','finiteOccupancyContactGazeAndCompleteAnatomyUnaccepted':True,'secondsBeforePreview':time.time()-tick})
 b.deliver(0);bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=False);assert a.sha(SRC)==digest;views=[]
 for view in ['face','body-face','oblique','profile','back']:views.append(b.u.v.image('a-anatomical-eye-assembly',view));save('a-view-controls.json',views)
 for label,value in [('half',.5),('closed',1.),('restored',0.)]:b.deliver(value);views.append(b.u.v.image('a-anatomical-eye-assembly-'+label,'face'));save('a-view-controls.json',views)
 print('R119_COMPLETE_EXTERNAL_EYE_ASSEMBLY_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
