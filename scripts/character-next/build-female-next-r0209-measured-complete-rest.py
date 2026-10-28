
from pathlib import Path
import bpy,numpy as np,json,datetime,time,hashlib,importlib.util,shutil
from mathutils import Matrix
p=json.loads(Path('F:/AevryndStorage/character-development-paths.json').read_text('utf-8'));A=Path(p['directCharacterArchiveAccess']);E=A/'evidence/character-female-next/r0209-native-ponytail-rest-foundation';F=Path('F:/AevryndEvidence/r0209-native-ponytail-rest-foundation');t=json.loads((E/'before.json').read_text('utf-8'));tick=time.time()
def sha(f):return hashlib.file_digest(Path(f).open('rb'),'sha256').hexdigest()
def save(name,d):(E/name).write_bytes((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def digest(x):return hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()
assert sha(t['source'])==t['sourceSha256'];bpy.ops.wm.open_mainfile(filepath=t['source']);s=bpy.context.scene;s.frame_set(1);sp=importlib.util.spec_from_file_location('r209base',A/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;h=m.h;skin=bpy.data.objects[a.FIXED[0]];old=bpy.data.objects[a.FIXED[1]];previous=bpy.data.objects['AFN204_ACTUAL_CURRENT_SKIN_CONNECTED_CROP'];oldBirths=bpy.data.objects['AFN204_CURRENT_SKIN_CONNECTED_BIRTHS'];protected={name:a.rawsig(bpy.data.objects[name]) for name in a.FIXED+a.MOVING};V,T=a.geometry(old);tri=V[T];centre=np.array([0.0,-.025]);levels=np.linspace(float(V[:,2].min())+.0002,float(V[:,2].max())-.0002,64);angles=np.linspace(-np.pi,np.pi,96,endpoint=False);dirs=np.column_stack([np.cos(angles),np.sin(angles)]);radii=np.full((len(levels),len(angles)),np.nan);hits=np.zeros(radii.shape,'i4');segments=[];zmin=tri[:,:,2].min(1);zmax=tri[:,:,2].max(1)
def cross(x,y):return x[...,0]*y[...,1]-x[...,1]*y[...,0]
for iz,z in enumerate(levels):
 ft=tri[(zmin<z)&(zmax>=z)];pairs=[]
 for k,l in [(0,1),(1,2),(2,0)]:
  pa,pb=ft[:,k],ft[:,l];mask=(pa[:,2]<=z)&(pb[:,2]>z)|(pb[:,2]<=z)&(pa[:,2]>z);aa=pa[mask];bb=pb[mask];u=(z-aa[:,2])/(bb[:,2]-aa[:,2]);pairs.append(np.column_stack([np.flatnonzero(mask),aa[:,:2]+u[:,None]*(bb[:,:2]-aa[:,:2])]))
 both=np.vstack(pairs);order=np.argsort(both[:,0],kind='stable');both=both[order];assert len(both)%2==0;assert np.array_equal(both[::2,0],both[1::2,0]);sa=both[::2,1:]-centre;sb=both[1::2,1:]-centre;edge=sb-sa
 for ia,d in enumerate(dirs):
  den=cross(d,edge);good=np.abs(den)>1e-12;rr=np.full(len(den),np.nan);tt=rr.copy();rr[good]=cross(sa[good],edge[good])/den[good];tt[good]=cross(sa[good],d)/den[good];good&=(rr>0)&(tt>=0)&(tt<=1);hits[iz,ia]=good.sum()
  if good.any():radii[iz,ia]=float(rr[good].max())
valid=np.isfinite(radii);assert valid.sum()>1000;gridZ,gridA=np.meshgrid(levels,angles,indexing='ij');sourcePoints=np.column_stack([gridZ[valid],gridA[valid]]);sourceR=radii[valid];filled=radii.copy()
# Only explicit nearest physical-height/angular section interpolation fills measurement gaps.
for iz,ia in np.argwhere(~valid):
 dz=(sourcePoints[:,0]-levels[iz])/.02;da=np.arctan2(np.sin(sourcePoints[:,1]-angles[ia]),np.cos(sourcePoints[:,1]-angles[ia]))/.3;filled[iz,ia]=sourceR[np.argmin(dz*dz+da*da)]
assert np.isfinite(filled).all() and filled.max()<.3
# The lowest supported measured level varies with angular region and is retained.
bottom=np.array([levels[np.flatnonzero(valid[:,ia])[0]] if valid[:,ia].any() else np.nan for ia in range(len(angles))]);available=np.flatnonzero(np.isfinite(bottom));assert len(available)>40
for ia in np.flatnonzero(~np.isfinite(bottom)):
 da=np.arctan2(np.sin(angles[available]-angles[ia]),np.cos(angles[available]-angles[ia]));bottom[ia]=bottom[available[np.argmin(abs(da))]]
cu=previous.data.copy();raw=h.arr(cu.position_data,'vector',len(cu.position_data),3);N=len(cu.curves);assert N==252 and raw.shape==(N*16,3);original=raw.reshape(N,16,3);roots=original[:,0].copy();P=[];endpointAngles=[];endpointZ=[]
def section(z,phi):
 zi=float(np.clip((z-levels[0])/(levels[-1]-levels[0])*(len(levels)-1),0,len(levels)-1));ai=float(((phi+np.pi)%(2*np.pi))/(2*np.pi)*len(angles));i=int(np.floor(zi));j=int(np.floor(ai));u=zi-i;v=ai-j;return (1-u)*((1-v)*filled[i,j%96]+v*filled[i,(j+1)%96])+u*((1-v)*filled[min(i+1,63),j%96]+v*filled[min(i+1,63),(j+1)%96])
for gid,root in enumerate(roots):
 delta=root[:2]-centre;phi0=float(np.arctan2(delta[1],delta[0]));side=1 if root[0]>=0 else -1
 # Select a measured lower-hair ray on the same side; front scalp paths drape toward actual side volume.
 pool=np.flatnonzero((dirs[:,0]*side>0.15)&np.any(valid[:24],axis=0));assert len(pool)>0;da=np.arctan2(np.sin(angles[pool]-phi0),np.cos(angles[pool]-phi0));j=int(pool[np.argmin(abs(da))]);phi1=float(angles[j]);angleDelta=float(np.arctan2(np.sin(phi1-phi0),np.cos(phi1-phi0)));tip=float(bottom[j]+.025*np.clip((1.57-root[2])/.165,0,1));curve=[]
 for k,u in enumerate(np.linspace(0,1,16)):
  w=u*u*(3-2*u);phi=phi0+angleDelta*w;z=float(root[2]+.018*np.sin(np.pi*u)*np.exp(-2*u)-(root[2]-tip)*u**1.5);rad=section(z,phi);target=np.r_[centre+rad*np.array([np.cos(phi),np.sin(phi)]),z];blend=1-np.exp(-u/.10);point=(1-blend)*root+blend*target;curve.append(point)
 curve=np.array(curve);curve[0]=root;P.append(curve);endpointAngles.append(phi1);endpointZ.append(tip)
P=np.array(P,'f4');assert np.isfinite(P).all();cu.position_data.foreach_set('vector',P.ravel());hair=bpy.data.objects.new('AFN209_ACTUAL_MEASURED_WORKING_HAIR_REST_GROOM',cu);s.collection.objects.link(hair);births=oldBirths.copy();births.data=oldBirths.data.copy();births.name='AFN209_CURRENT_SKIN_OWNED_BIRTHS';s.collection.objects.link(births);births.hide_render=True;births.hide_set(True)
for mod in births.modifiers:
 if mod.type=='NODES':mod.node_group=mod.node_group.copy()
for name in ['AFN198_ACTUAL_GUIDE_CAP_BINDING','AFN198_ACTUAL_SURFACE_CHILD_GENERATOR']:
 mod=hair.modifiers.new(name,'NODES');mod.node_group=previous.modifiers[name].node_group.copy()
for node in hair.modifiers['AFN198_ACTUAL_SURFACE_CHILD_GENERATOR'].node_group.nodes:
 if node.bl_idname=='GeometryNodeObjectInfo' and node.inputs['Object'].default_value==oldBirths:node.inputs['Object'].default_value=births
at=cu.attributes.new('AFN209_PERSISTENT_NATIVE_GUIDE_ID','INT','CURVE');at.data.foreach_set('value',np.arange(N,dtype='i4'));previous.hide_render=True;hair.hide_render=False;hair.hide_set(False);old.hide_render=True;bpy.context.view_layer.update();actual,off=m.curveworld(hair);de=hair.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;ids=h.arr(de.attributes['AFN198_PERSISTENT_BIRTH_ID'].data,'value',len(off),dtype='i4');uv=h.arr(de.attributes['surface_uv_coordinate'].data,'vector',len(off),2);assert len(off)==10191 and np.array_equal(np.sort(ids),np.arange(10191));canonical=actual.reshape(10191,16,3)[np.argsort(ids)];orig=np.load(E.parent/'r0198-native-birth-owned-scalp/native-surface-birth-lineage.npz');rootError=float(np.linalg.norm(actual[off]-orig['shaftStartWorld'][ids],axis=1).max());assert rootError<3e-6 and protected=={n:a.rawsig(bpy.data.objects[n]) for n in protected}
np.savez_compressed(E/'measured-volume-unique-construction.npz',centre=centre,levels=levels,angles=angles,actualSectionRadii=radii,actualIntersectionCounts=hits,filledSectionRadii=filled,measuredBottom=bottom,guideIDs=np.arange(N,dtype='i4'),fullRebuiltGuidePaths=P,endpointAngles=endpointAngles,endpointZ=endpointZ,displayBirthIDs=ids,displayBirthUV=uv)
save('complete-measured-rest-construction.json',{'UTC':stamp(),'actualHair':hair.name,'actualBirths':births.name,'actualSkin':skin.name,'actualGuideIDs':N,'rawPoints':len(raw),'actualCurves':len(off),'actualPoints':len(actual),'allSevenRawMeshUVSignaturesUnchanged':protected,'referenceActualWorkingHairGeometry':{'name':old.name,'vertices':len(V),'triangles':len(T),'worldVerticesSHA256':digest(V),'trianglesSHA256':digest(T),'notArtistStrandBirthInference':True},'measuredValidPolarSections':int(valid.sum()),'totalPolarSections':int(valid.size),'interpolatedMissingSections':int((~valid).sum()),'completeFreePathsRebuilt':True,'noFailedFreeLengthsOrSourceCapGraftReused':True,'currentBirthMaximumErrorM':rootError,'canonicalDisplayedFloat32WorldSHA256':digest(canonical),'canonicalUVSHA256':digest(uv[np.argsort(ids)]),'rawGuideSHA256':digest(P),'radiusDensityMaterialLightUnchanged':True,'appearanceContactOperationNaturalMotionRuntimeUnaccepted':True,'constructionSecondsBeforePreview':time.time()-tick})
captures=[]
def capture(scene):
 captures.append({'UTC':stamp(),'source':bpy.data.filepath,'output':scene.render.filepath,'frame':scene.frame_current,'cameraMatrixWorld':[list(x) for x in scene.camera.matrix_world],'lens':scene.camera.data.lens,'cameraType':scene.camera.data.type,'exposure':scene.view_settings.exposure,'viewTransform':scene.view_settings.view_transform,'look':scene.view_settings.look,'samples':scene.cycles.samples,'seed':scene.cycles.seed,'newHairVisible':not hair.hide_render,'originalHairVisible':not old.hide_render,'captureStateNotRenderDepsgraphProof':True});save('actual-render-pre-capture-states.json',captures)
bpy.app.handlers.render_pre.append(capture);a.b.u.v.E=F;hair.hide_render=True;old.hide_render=False
for v in ['face','body-face']:s.camera.data.type='PERSP';a.b.u.v.image('baseline-original-working-hair',v)
old.hide_render=True;hair.hide_render=False
for v in ['face','body-face','oblique','profile','back']:s.camera.data.type='PERSP';a.b.u.v.image('measured-complete-rest-groom',v)
bpy.app.handlers.render_pre.remove(capture);s.camera.matrix_world=Matrix(captures[2]['cameraMatrixWorld']);s.camera.data.lens=captures[2]['lens'];s.camera.data.type='PERSP'
for file in F.glob('*.png'):shutil.copyfile(file,E/file.name)
output=F/'aevrynd-female-next-r0209-measured-complete-rest-groom.blend';out=A/'assets-source/aevrynd-character/female-next/r0209-source'/output.name;out.parent.mkdir(exist_ok=True);assert not out.exists();bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(output),compress=True);assert output.stat().st_size<t['sourceBudgetBytes'];shutil.copyfile(output,out);save('build-summary.json',{'UTC':stamp(),'output':str(out),'userReviewSource':str(output),'sha256':sha(out),'bytes':out.stat().st_size,'actualHair':hair.name,'actualSkin':skin.name,'actualBirths':births.name,'actualCurves':len(off),'actualPoints':len(actual),'oneCompleteCandidate':True,'elapsedJobSeconds':time.time()-tick,'unaccepted':True});print('R209_COMPLETE_CURRENT_MEASURED_REST_GROOM_SAVED',json.dumps({'source':str(output),'curves':len(off),'points':len(actual),'rootErrorM':rootError,'measuredSections':int(valid.sum())}),flush=True)
