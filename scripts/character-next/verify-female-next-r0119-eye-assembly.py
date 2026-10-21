"""Independent assembly recovery, actual gaze/restore and capped neutral surface witnesses."""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time,os,ast
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0119-anatomical-eye-rebuild'
sp=importlib.util.spec_from_file_location('r119saved',Path(__file__).with_name('build-female-next-r0119-anatomical-eyes.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);b=a.b;q=a.q
def main():
 tick=time.time();allrows={};names=[n for row in json.loads((E/'a-build-summary.json').read_text('utf-8'))['parts'] for n in row['parts']];before=json.loads((E/'a-build-summary.json').read_text('utf-8'))['allProtectedBodyKeysHairBrowsLashesBefore']
 parsed=ast.parse(Path(__file__).with_name('verify-female-next-r0037-eye-margin.py').read_text('utf-8'));ns={'np':np};exec(compile(ast.Module(body=[n for n in parsed.body if isinstance(n,ast.FunctionDef) and n.name in ['inside','intersections']],type_ignores=[]),'unchanged-r37-intersections','exec'),ns);intersections=ns['intersections']
 for tag,filename,line in [('a','a-anatomical-eye-assembly','anatomical-eye-assembly-lineage.npz'),('b','b-native-iris-landmark-eyes','b-anatomical-eye-assembly-lineage.npz')]:
  path=S/'r0119-source'/('aevrynd-female-next-r0119-'+filename+'.blend');digest=a.a.sha(path);bpy.ops.wm.open_mainfile(filepath=str(path));b.deliver(0);assert a.a.protected()==before;z=np.load(E/line);parts=[];neutral={}
  for name in names:
   ob=bpy.data.objects[name];d,P,T=b.u.b.geom(ob);P=P.copy();T=T.copy();error=float(np.linalg.norm(P-z[name+'_world'],axis=1).max());assert error<2e-6;assert np.array_equal(T,z[name+'_triangles']);assert np.isfinite(P).all();edges=np.sort(np.r_[T[:,[0,1]],T[:,[1,2]],T[:,[2,0]]],axis=1);_,inc=np.unique(edges,axis=0,return_counts=True);volume=float(np.einsum('ij,ij->i',P[T[:,0]],np.cross(P[T[:,1]],P[T[:,2]])).sum()/6);parts.append({'name':name,'vertices':len(P),'triangles':len(T),'savedMaximumWorldErrorM':error,'allEdgesTwoIncident':bool(np.all(inc==2)),'signedVolumeM3':volume,'topologyAndVolumeNotSelfOrContactProof':True});neutral[name]=P
  gaze=None;contacts=[]
  if tag=='b':
   root=bpy.data.objects['AFN119_L_EYE_GAZE_CONTROL'];root['gaze_yaw']=.1;root['gaze_pitch']=.05;root.update_tag();bpy.context.view_layer.update();moves=[]
   for name in names:
    if '_L_' in name:d,P,T=b.u.b.geom(bpy.data.objects[name]);moves.append(float(np.linalg.norm(P-neutral[name],axis=1).max()))
   assert max(moves)>0;root['gaze_yaw']=root['gaze_pitch']=0.;root.update_tag();bpy.context.view_layer.update();restore=max(float(np.linalg.norm(b.u.b.geom(bpy.data.objects[n])[1]-neutral[n],axis=1).max()) for n in names);assert restore==0;gaze={'assignedRadians':{'yaw':.1,'pitch':.05},'actualPartMaximumWorldMovesM':moves,'actualAllPartsNeutralRestoreErrorM':restore,'scope':'Actual component assembly control only, not a qualified complete gaze/blink/contact operation.'}
   skin=bpy.data.objects['AFN113_COMPLETE_WOMAN_COHERENT_HEAD'];d,V,T=b.u.b.geom(skin);V=V.copy();T=T.copy();tree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True,epsilon=0.)
   for name in names:
    d,P,OT=b.u.b.geom(bpy.data.objects[name]);P=P.copy();OT=OT.copy();other=BVHTree.FromPolygons(P.tolist(),OT.tolist(),all_triangles=True,epsilon=0.);pairs=tree.overlap(other);hits=[];tested=0
    for i,j in pairs:
     points=intersections(V[T[i]],P[OT[j]]);tested+=1
     if points:hits.append({'skinTriangle':int(i),'eyeTriangle':int(j),'worldIntersectionOrTouchPointsM':[p.tolist() for p in points[:4]]})
     if len(hits)>=8:break
    contacts.append({'state':'neutral','pair':'actual complete skin vs '+name,'BVHCandidatePairs':len(pairs),'candidatePairsTestedUntilCap':tested,'storedIntersectionOrTouchWitnesses':len(hits),'cap':8,'witnesses':hits,'noRegionExclusion':True,'notCertifiedPenetrationCountGlobalSignedMinimumOrFiniteOccupancy':True})
  textures=[]
  for im in bpy.data.images:
   if im.source=='FILE' and not im.packed_file and im.filepath and im.users>0:
    p=Path(bpy.path.abspath(im.filepath));assert p.is_file(),str(p);textures.append({'name':im.name,'relative':im.filepath,'absolute':str(p),'sha256':a.a.sha(p),'bytes':p.stat().st_size})
  physical=Path('C:/Users/USER/AevryndCharacterSources/r0119')/path.name;archive=R/'sites-engine-journey/assets-source/aevrynd-character/female-next/r0119-source'/path.name;assert os.path.samefile(path,physical) and os.path.samefile(path,archive);assert a.a.sha(path)==digest;allrows[tag]={'candidate':{'source':str(path),'sha256':digest,'bytes':path.stat().st_size,'physicalSource':str(physical),'archivePath':str(archive)},'allProtectedBodyKeysHairBrowsLashesExact':True,'parts':parts,'actualComponentGaze':gaze,'allReferencedExternalTextures':textures,'sourceUnchangedDuringReadback':True,'contact':{'status':'UNACCEPTED_NEUTRAL_CAPPED_WITNESSES_ONLY','actualSurfaceWitnesses':contacts,'globalSignedMinimumM':None,'continuousFullFiniteContainmentOpticalInterfacesSelfAndClosedContactNotProved':True}}
 a.save('minimum-saved-eye-assembly-readback.json',{'sources':allrows,'scope':'Recoverable independent eye construction/actual component controls only; no complete character appearance/operation/contact/runtime adoption.','seconds':time.time()-tick});print('R119_ASSEMBLIES_INDEPENDENTLY_REOPENED',[(k,len(v['parts'])) for k,v in allrows.items()],time.time()-tick,flush=True)
if __name__=='__main__':main()
