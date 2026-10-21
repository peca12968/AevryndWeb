"""Reopen whole-head B, matched own-source motion and bounded actual optical witnesses."""
from pathlib import Path
import bpy,numpy as np,json,time,hashlib,ast,importlib.util
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0113-coherent-head-foundation';S=R/'engine/assets/characters/female-next/source'
def mod(n,p):
 sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(p));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
b=mod('r113verifybuild','build-female-next-r0113-native-neck-character.py');v=mod('r113verifysign','verify-female-next-r0105-saved-chart.py');q=b.q
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def graph(d):return v.hasharray(np.r_[q.arr(d.polygons,'loop_total',len(d.polygons),dtype='i4'),q.arr(d.loops,'vertex_index',len(d.loops),dtype='i4')])
def main():
 tick=time.time();out=S/'aevrynd-female-next-r0113-b-native-neck-skin.blend';digest=sha(out);line=np.load(E/'whole-head-b-source-correspondence.npz');brow=np.load(E/'b-brow-source-correspondence.npz');bpy.ops.wm.open_mainfile(filepath=str(out));skin=bpy.data.objects['AFN113_COMPLETE_WOMAN_COHERENT_HEAD'];dd,N,T=b.u.b.geom(skin);N=N.copy();T=T.copy();G=graph(dd);ids=line['sourceHeadToBody'];neutral=line['sourceNeutralWorld'];headMask=np.all(np.isin(T,ids),axis=1);states=[];contact=[]
 code=Path(__file__).with_name('verify-female-next-r0037-eye-margin.py');tree=ast.parse(code.read_text('utf8'));defs=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in ['inside','intersections']];ns={'np':np};exec(compile(ast.Module(body=defs,type_ignores=[]),str(code),'exec'),ns);intersections=ns['intersections'];neutralBad=False
 for label,value in [('neutral',0.),('half',.5),('closed',1.),('restored',0.)]:
  b.deliver(value);d,P,PT=b.u.b.geom(skin);P=P.copy();assert np.isfinite(P).all();expected=neutral+value*((line['sourceClosedL']-neutral)+(line['sourceClosedR']-neutral));err=float(np.linalg.norm(P[ids]-expected,axis=1).max());assert err<4e-6;states.append({'state':label,'assignedBlink':value,'actualSkinMaximumMoveM':float(np.linalg.norm(P-N,axis=1).max()),'actualNativeHeadAgainstOwnSourceMaxErrorM':err,'evaluatedPolygonLoopGraphEqualsNeutral':graph(d)==G,'keys':{k.name:k.value for k in skin.data.shape_keys.key_blocks if k.name!='Basis'}})
  if label in ['neutral','closed'] and not neutralBad:
   H=PT[headMask];full=BVHTree.FromPolygons(P.tolist(),H.tolist(),all_triangles=True,epsilon=0.)
   for side in ['L','R']:
    ob=bpy.data.objects['AFN113_'+side+'_SCLERA'];od,O,OT=b.u.b.geom(ob);O=O.copy();OT=OT.copy();other=BVHTree.FromPolygons(O.tolist(),OT.tolist(),all_triangles=True,epsilon=0.);pairs=full.overlap(other);hits=[];tested=0
    for x,y in pairs:
     points=intersections(P[H[x]],O[OT[y]]);tested+=1
     if points:hits.append({'skinTriangle':int(np.flatnonzero(headMask)[x]),'opticTriangle':int(y),'worldPointsM':[p.tolist() for p in points[:4]]})
     if len(hits)>=16:break
    contact.append({'state':label,'pair':'actual new complete skin/head vs '+ob.name,'bvhCandidatePairs':len(pairs),'candidatePairsExaminedUntilWitnessCap':tested,'storedIntersectionOrTouchWitnesses':len(hits),'witnesses':hits,'notGlobalIntersectionTotalOrSignedMinimum':True});neutralBad|=label=='neutral' and bool(hits)
  if label=='restored':assert states[-1]['actualSkinMaximumMoveM']==0
 groom=q.hair(bpy.data.objects['AFN97_TUCKED_ARTIST_BOB_CHILDREN']).reshape(line['newGroomWorld'].shape);gerr=float(np.linalg.norm(groom-line['newGroomWorld'],axis=2).max());assert gerr<4e-6;bro=q.hair(bpy.data.objects['AFN57_NATIVE_BROWS']);berr=float(np.linalg.norm(bro-brow['newWorld'],axis=1).max());assert berr<4e-6
 lashRows=json.loads((E/'b-mobile-lash-bindings.json').read_text('utf8'));lookup={tuple(sorted(map(int,t))):t for t in T};frames={'curves':len(lashRows),'actualWindingConsistent':0,'reversed':0,'notActualTriangle':0}
 for row in lashRows:
  t=np.array(row['actualNewUnifiedSkinTriangle']);actual=lookup.get(tuple(sorted(map(int,t))))
  if actual is None:frames['notActualTriangle']+=1;continue
  x=np.cross(N[t[1]]-N[t[0]],N[t[2]]-N[t[0]]);y=np.cross(N[actual[1]]-N[actual[0]],N[actual[2]]-N[actual[0]]);frames['reversed' if x@y<0 else 'actualWindingConsistent']+=1
 assert frames['curves']==412
 textures=[]
 for im in bpy.data.images:
  if im.source=='FILE' and not im.packed_file and im.filepath:
   p=Path(bpy.path.abspath(im.filepath));assert p.is_file(),str(p);textures.append({'name':im.name,'relative':im.filepath,'absolute':str(p),'sha256':sha(p),'bytes':p.stat().st_size})
 assert sha(out)==digest;result={'status':'REOPENED_ACTUAL_NATIVE_HEAD_MOTION_AND_RESTORE_NOT_COMPLETE_ACCEPTANCE','candidate':{'source':str(out),'sourceSha256':digest,'sourceBytes':out.stat().st_size,'vertices':len(N),'triangles':len(T),'externalTextures':textures},'states':states,'newGroomAgainstAuthoredRestMaxM':gerr,'newBrowsAgainstAuthoredRestMaxM':berr,'allGroomCurves':24800,'allBrowCurves':len(brow['counts']),'allLashFrames':frames,'sourceUnchangedDuringVerification':True,'contact':{'status':'UNACCEPTED','actualSurfaceWitnesses':contact,'neutralFailureStoppedClosedContactExpansion':neutralBad,'intersectionRoutine':str(code),'intersectionRoutineFileSha256':sha(code),'existingInsideAndIntersectionsFunctionsUsedUnchanged':True,'globalSignedMinimumM':None,'finiteWallSelfHairClothContinuousAndNaturalDynamicsProved':False,'proxyHelperWasOnlyInitialEyeSizingNotProof':True},'wholeBodyRigGuidesOralBrowControlsAndRuntimeUnaccepted':True,'completeAppearanceOrOperationAccepted':False,'seconds':time.time()-tick};(E/'minimum-saved-coherent-readback.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print('R113_COHERENT_SOURCE_READBACK_DONE',frames,'neutralOpticalWitness',neutralBad,time.time()-tick,flush=True)
 # Directional views only, no source/model changes; actual complete woman remains visible.
 views=[]
 for view in ['oblique','profile']:views.append(b.u.v.image('b-coherent-native-character',view))
 b.u.m.m.rig.k.b.camera('face');scene=bpy.context.scene;target=Vector((0,-.04,1.43));lights=[]
 for ob in scene.objects:
  if ob.type=='LIGHT':
   ob.location.x=-ob.location.x;ob.rotation_euler=(target-ob.location).to_track_quat('-Z','Y').to_euler();lights.append({'name':ob.name,'location':list(ob.location),'energy':ob.data.energy,'colour':list(ob.data.color)})
 bpy.context.view_layer.update();scene.render.filepath=str(E/'b-second-light-face.png');bpy.ops.render.render(write_still=True);(E/'b-directional-view-controls.json').write_text(json.dumps({'samePrimaryControlsForObliqueProfile':views,'secondLighting':{'file':scene.render.filepath,'camera':np.array(scene.camera.matrix_world).tolist(),'exposure':scene.view_settings.exposure,'lights':lights},'sourceNotSavedOrChanged':sha(out)==digest},indent=2)+'\n',encoding='utf8');print('R113_COHERENT_DIRECTIONAL_VIEWS_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
