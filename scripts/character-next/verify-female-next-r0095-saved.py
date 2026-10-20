"""Independent complete-source reopen and scoped live-guide/control-point checks.
Local edit/restore proves only data coupling, not realism or natural motion.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0095-authored-layered-groom';S=R/'engine/assets/characters/female-next/source'
def mod(n,f):
 sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(f));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);return a
h=mod('r95independent','verify-female-next-r0090-rain-and-flow.py');p=mod('r95parity','verify-female-next-r0081-curly.py');m=h.m;q=h.q
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.item() if isinstance(a,np.generic) else a.tolist())+'\n',encoding='utf8')
def main():
 tick=time.time();h.open_file(S/'aevrynd-female-next-r0094-b-source-width-growth-volume.blend');names=m.rig.native_names()+['AFN59_LASHES_NATIVE_POINT_POSES'];sig={n:h.native.signature(bpy.data.objects[n]) for n in names};rig=h.rig_signature();lights=m.m.q.lights();mats={x.name:m.rig.k.f.v.v32.material_signature(x) for x in bpy.data.materials if x.use_nodes and (x.users or x.use_fake_user)};face={n:q.hair(bpy.data.objects[n]).copy() for n in ['AFN57_NATIVE_BROWS','AFN57_NATIVE_LASHES']};caps={n:h.helpers.cap_signature(bpy.data.objects[n]) for n in ['AFN74_UPPER_TEETH_RIGID','AFN74_LOWER_TEETH_RIGID','AFN81_NEUTRAL_EDITABLE_GROWTH_SURFACE']};sourceHair=bpy.data.objects['AFN94_SOURCE_WIDTH_RENDER_FIBRES'];sourceP=q.hair(sourceHair).reshape(-1,33,3);sourceRad=q.arr(sourceHair.data.attributes['radius'].data,'value',sourceP.size//3);body=m.rig.k.mesh(bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING']);V,T=body['V'],body['T'];edges=np.sort(np.concatenate([T[:,[0,1]],T[:,[1,2]],T[:,[2,0]]]),axis=1);_,inc=np.unique(edges[:,0].astype('u8')*len(V)+edges[:,1],return_counts=True);closed=bool(np.all(inc==2));tree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True);skin=m.rig.k.mesh(bpy.data.objects['AFN74_SKIN_AND_EXISTING_OCULAR_LINING']);st=BVHTree.FromPolygons(skin['V'].tolist(),skin['T'].tolist(),all_triangles=True);out={}
 for tag in ['a','b','c']:
  ref=json.loads((E/(tag+'-build-summary.json')).read_text('utf8'));src=Path(ref['output']);assert sha(src)==ref['outputSha256'];h.open_file(src);assert sig=={n:h.native.signature(bpy.data.objects[n]) for n in names};assert rig==h.rig_signature() and lights==m.m.q.lights();assert mats=={n:m.rig.k.f.v.v32.material_signature(bpy.data.materials[n]) for n in mats};assert caps=={n:h.helpers.cap_signature(bpy.data.objects[n]) for n in caps}
  for n,x in face.items():assert np.array_equal(q.hair(bpy.data.objects[n]),x)
  actualBody=m.rig.k.mesh(bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING']);assert np.array_equal(actualBody['V'],V) and np.array_equal(actualBody['T'],T);z=np.load(E/(tag+'-authored-groom-lineage.npz'));o=bpy.data.objects[ref['curveObject']];guide=bpy.data.objects[ref['guideObject']];P=q.hair(o).reshape(-1,33,3);err=float(np.linalg.norm(P-z['actualWorld'],axis=2).max());rootErr=float(np.linalg.norm(P[:,0]-sourceP[:,0],axis=1).max());d=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;rad=q.arr(d.attributes['radius'].data,'value',P.size//3);types=q.arr(d.attributes['curve_type'].data,'value',28002,dtype='i4');assert P.shape==(28002,33,3) and err<3e-6 and rootErr<3e-6 and np.isfinite(P).all();assert np.array_equal(rad,sourceRad) and np.all(types==0);assert len(guide.data.vertices)==1077*33 and len(guide.data.edges)==1077*32
  idx=z['guideIndices'];weights=z['guideWeights'];assert idx.min()>=0 and idx.max()<1077 and np.max(abs(weights.sum(1)-1))<2e-7;A=np.array(guide.matrix_world);gp=q.arr(guide.data.vertices,'co',len(guide.data.vertices),3).astype('f8')@A[:3,:3].T+A[:3,3];guideErr=float(np.linalg.norm(gp.reshape(-1,33,3)-z['guideWorld'],axis=2).max());assert guideErr<3e-6
  # One neutral edit/restore probe, not an animation or a complete operation.
  vertex=guide.data.vertices[31];original=vertex.co.copy();vertex.co.x+=.004/np.linalg.norm(A[:3,0]);guide.data.update();bpy.context.view_layer.update();changed=q.hair(o).reshape(P.shape);expected=np.zeros_like(P);expected[:,31,0]=np.sum(weights*(idx==0),axis=1)*.004;editError=float(np.linalg.norm(changed-P-expected,axis=2).max());assert editError<3e-6;vertex.co=original;guide.data.update();bpy.context.view_layer.update();restored=q.hair(o).reshape(P.shape);assert np.array_equal(restored,P)
  sample=np.linspace(0,P.size//3-1,2048,dtype=int);witness=[];inspected=0;minimum=float('inf');radiusWorld=float(rad.max())*np.linalg.norm(np.array(o.matrix_world)[:3,0])
  for index in sample:
   pt=P.reshape(-1,3)[index];co,no,faceID,dist=tree.find_nearest(Vector(pt));minimum=min(minimum,dist);inspected+=1
   if dist<=radiusWorld+1e-6:continue
   inside=[p.parity(tree,pt,direction) for direction in [(1.,.321,.173),(-.137,1.,.297),(.311,-.197,1.)]]
   if closed and all(v is True for v in inside):
    sco,_,sf,sd=st.find_nearest(Vector(pt))
    if np.linalg.norm(np.array(sco)-np.array(co))<1e-6:witness.append({'curve':int(index//33),'point':int(index%33),'world':pt,'unsignedBodyDistanceM':dist,'unsignedVisibleSkinDistanceM':sd,'threeRayInside':inside})
    if len(witness)>=8:break
  textures=[]
  for im in bpy.data.images:
   if im.source=='FILE' and not im.packed_file:
    path=Path(bpy.path.abspath(im.filepath));assert im.filepath.startswith('//') and path.is_file();textures.append({'relative':im.filepath,'sha256':sha(path)})
  assert len(textures)==15 and not bpy.data.libraries;out[tag]={'source':str(src),'sha256':sha(src),'status':'REOPEN_AND_LIVE_GUIDE_DATA_ONLY_NOT_COMPLETE_OPERATION','allUnrelatedBodyFaceRig52UVKeysWeightsDriversTeethBrowsLashesMaterialsLightsPreserved':True,'actualStrands':28002,'editableParentGuides':1077,'pointsEach':33,'CatmullRomControlType0':True,'correctSourceRadiusAndCloseTipUnchanged':True,'savedControlMaximumWorldErrorM':err,'allOriginalRootMaximumWorldErrorM':rootErr,'savedGuideMaximumWorldErrorM':guideErr,'guideIndexAndWeightsValid':True,'localGuideEditProbe':{'editedGuide':0,'point':31,'worldDeltaM':.004,'maximumExpectedOutputControlErrorM':editError,'exactNeutralRestore':True,'onlyLocalCouplingNotRealismFullOperationOrNaturalMotion':True},'scopedStaticContact':{'bodyClosedTwoIncidentEdges':closed,'nativeCurveControlKnotsPlanned':2048,'inspected':inspected,'strongAuthoringControlPointInteriorWitnesses':witness,'countsAreNotGlobalTotals':True,'minimumSampledUnsignedDistanceM':minimum,'globalSignedMinimumM':None,'actualCyclesSplineOccupancySelfRootsFiniteShaftCCDOrNaturalMotionCertified':False},'externalTextures':textures,'completeAppearanceOperationContactRuntimeAccepted':False,'seconds':time.time()-tick};save('minimum-saved-readback.json',out);print('R95_INDEPENDENT',tag,err,editError,len(witness),time.time()-tick,flush=True)
 print('R95_READBACK_DONE',flush=True)
if __name__=='__main__':main()
