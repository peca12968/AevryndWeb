"""Minimum independent reopen, effective control restoration and Skin locators.
Rejected complete appearance: no new render, candidate or global contact claim.
"""
from pathlib import Path
import bpy, numpy as np, importlib.util, json, hashlib, datetime, time
from mathutils import Vector
from mathutils.bvhtree import BVHTree

C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158')
E=C/'evidence/character-female-next/r0200-native-curve-sculpt'
sp=importlib.util.spec_from_file_location('r198verifybase',C/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py')
m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;h=m.h

def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):return hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
def save(n,x):(E/n).write_bytes((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())

def output(hair):
    P,off=m.curveworld(hair)
    data=hair.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
    ids=h.arr(data.attributes['AFN198_PERSISTENT_BIRTH_ID'].data,'value',len(off),dtype='i4')
    lengths=np.diff(np.r_[off,len(P)])
    assert len(ids)==10191 and np.array_equal(np.sort(ids),np.arange(10191))
    assert np.all(lengths==16) and np.isfinite(P).all()
    canonical=np.empty((10191,16,3));canonical[ids]=P.reshape(10191,16,3)
    uv=h.arr(data.attributes['surface_uv_coordinate'].data,'vector',10191,2)
    canonicalUV=np.empty_like(uv);canonicalUV[ids]=uv
    return canonical,canonicalUV,ids

def update(hair):
    hair.data.update_tag();hair.update_tag();bpy.context.view_layer.update()

def main():
    tick=time.time();b=json.loads((E/'a-build-summary.json').read_text('utf-8'))
    p=json.loads((E/'native-brush-construction-summary.json').read_text('utf-8'));p['logicalBirthToShaftCentreLiftM']=.000102
    assert sha(b['output'])==b['sha256']
    bpy.ops.wm.open_mainfile(filepath=b['output']);s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update()
    hair=bpy.data.objects[b['actualHair']];births=bpy.data.objects[b['actualBirths']];skin=bpy.data.objects[b['actualSkin']]
    z=np.load(E.parent/'r0198-native-birth-owned-scalp/native-surface-birth-lineage.npz');base,uv,ids=output(hair);new=np.load(E/'resumed-native-editor-latest.npz');rawActual=h.arr(hair.data.position_data,'vector',len(hair.data.position_data),3);rawExpected=new['guideWorld'].reshape(-1,3);authoredError=float(np.linalg.norm(rawActual-rawExpected,axis=1).max());assert authoredError<3e-6
    rawsig={n:a.rawsig(bpy.data.objects[n]) for n in a.FIXED+a.MOVING}
    assert rawsig==p['allOldOriginalRawMeshUVSignaturesUnchanged']
    W,T=a.geometry(skin);tri=z['childBirthActualSkinTriangles'];faces=z['childBirthActualSkinFaces'];bc=z['childBirthBC']
    assert np.array_equal(T[faces],tri) and np.isin(faces,z['actualCurrentScalpFaces']).all()
    logical=np.einsum('ni,nij->nj',bc,W[tri]);normal=np.cross(W[tri[:,1]]-W[tri[:,0]],W[tri[:,2]]-W[tri[:,0]])
    normal/=np.linalg.norm(normal,axis=1)[:,None]
    shaft=logical+normal*p['logicalBirthToShaftCentreLiftM']
    rootError=float(np.linalg.norm(base[:,0]-shaft,axis=1).max());uvError=float(np.abs(uv-z['actualSkinUV']).max())
    assert rootError<3e-6 and uvError<1e-6
    d=hair.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
    radius=h.arr(d.attributes['radius'].data,'value',len(d.position_data))
    effectiveMaterials=[x.name if x else None for x in d.materials]
    closest=h.arr(d.attributes['AFN198_ACTUAL_CLOSEST_GUIDE_ID'].data,'value',10191,dtype='i4')
    guideID=int(np.bincount(closest).argmax());pointID=guideID*16+8;rawPoint=hair.data.position_data[pointID]
    old=np.array(rawPoint.vector);rawPoint.vector=Vector(old+np.array([.001,0,0]));update(hair)
    moved,movedUV,movedIDs=output(hair);delta=np.linalg.norm(moved-base,axis=2)
    edit={'actualGuideID':guideID,'actualGuidePointID':pointID,'rawPositionDeltaM':[.001,0,0],
          'identity':'Complete10191 persistent birth IDs, each16 points; geometry canonicalized by birth ID in every state.',
          'displayedPointMaximumMovementM':float(delta.max()),'displayedPointsMovedAbove1e8M':int((delta>1e-8).sum()),
          'displayedBirthRootMaximumMovementM':float(delta[:,0].max()),'canonicalBirthUVMaximumChange':float(np.abs(movedUV-uv).max())}
    rawPoint.vector=Vector(old);update(hair);restored,restoredUV,restoredIDs=output(hair)
    restore=float(np.linalg.norm(restored-base,axis=2).max());edit['displayedCompleteRestorationMaximumM']=restore
    edit['canonicalUVRestorationMaximum']=float(np.abs(restoredUV-uv).max())
    save('actual-guide-operation-restoration.json',{'UTC':stamp(),**edit,'newCompleteCharacterOperationAccepted':False})
    assert edit['displayedPointMaximumMovementM']>1e-7 and restore<3e-6
    assert rawsig=={n:a.rawsig(bpy.data.objects[n]) for n in rawsig}
    tree=BVHTree.FromPolygons(W.tolist(),T.tolist(),all_triangles=True)
    gaps=np.array([tree.find_nearest(Vector(v))[3] for v in base[:,0]])
    sampled=np.unique(np.linspace(0,10190,256,dtype=int));hits=[];total=0
    for cid in sampled:
        for k in range(15):
            v=base[cid,k];step=base[cid,k+1]-v;length=float(np.linalg.norm(step))
            if length<=1e-10:continue
            hit,no,fi,gap=tree.ray_cast(Vector(v),Vector(step/length),length)
            if hit is not None:
                total+=1
                if len(hits)<32:hits.append({'birthID':int(cid),'controlSegment':k,'skinTriangle':int(fi),'worldPoint':list(hit),'distanceAlongChordM':float(gap)})
    deps=[{'library':x.name,'resolvedPath':bpy.path.abspath(x.filepath),'exists':Path(bpy.path.abspath(x.filepath)).exists()} for x in bpy.data.libraries]
    result={'UTC':stamp(),'loadedSource':bpy.data.filepath,'sourceSHA256':sha(b['output']),'actualSkin':skin.name,'actualHair':hair.name,'actualBirths':births.name,
        'frame':s.frame_current,'independentReopen':True,'rawGuides':len(hair.data.curves),'rawGuidePoints':len(hair.data.position_data),
        'actualCurves':10191,'actualPoints':int(base.size//3),'completePersistentBirthIdentity':True,'allCurveLengths':16,
        'currentSkinTriangleOwnershipQualified':True,'actualCurrentScalpTriangles':len(z['actualCurrentScalpFaces']),
        'actualCurrentSurfaceBirthCentreMaximumErrorM':rootError,'actualCanonicalBirthUVMaximumError':uvError,
        'allSevenRawMeshAndUVSignaturesEqual':True,'actualAuthoredGuideReopenMaximumErrorM':authoredError,'effectiveMaterials':effectiveMaterials,'rawMaterialSlotCount':len(hair.data.materials),
        'materialNodesInstalledByActualGenerator':'AFN198_OWN_NATIVE_HAIR_FIXED_MELANIN',
        'evaluatedRadiusRangeM':[float(radius.min()),float(radius.max())],'radiusNotFullRenderedThicknessProof':True,
        'displayedHairVisible':not hair.hide_render,'retainedOriginalHairHiddenRollback':bpy.data.objects[a.FIXED[1]].hide_render,
        'actualModifiers':[{'name':m.name,'type':m.type,'viewport':m.show_viewport,'render':m.show_render} for m in hair.modifiers],
        'skinModifiers':[{'name':m.name,'type':m.type,'viewport':m.show_viewport,'render':m.show_render} for m in skin.modifiers],
        'actualGuideEditAndRestore':edit,'neutralSkinControlChordSubset':{'sampledCurves':len(sampled),'sampledChords':len(sampled)*15,'skinTriangleLocators':total,'firstLocators':hits,'scope':'Control chords versus actual evaluated Skin at frame1 only. Not rendered fibre intersection totals, signed/global/finite/self/continuous acceptance.'},
        'unsignedBirthCentreSurfaceDistanceM':{'min':float(gaps.min()),'median':float(np.median(gaps)),'max':float(gaps.max()),'scope':'Unsigned point-to-triangle distances only; do not subtract radii to claim finite rendered clearance.'},
        'globalSignedSurfaceMinimumM':None,'finiteSelfContinuousAccepted':False,'appearanceAccepted':False,'newCompleteOperationAccepted':False,'naturalMotionAccepted':False,'engineRuntimeAccepted':False,
        'libraries':deps,'elapsedSeconds':time.time()-tick,'sourceNotResaved':True}
    save('independent-native-sculpt-readback.json',result)
    assert sha(b['output'])==b['sha256']
    print('R200_INDEPENDENT_REOPEN_NATIVE_UI_GUIDE_EDIT_RESTORE_AND_LOCATORS_DONE',json.dumps({'maxEditM':edit['displayedPointMaximumMovementM'],'restoreM':restore,'skinChordLocators':total}),flush=True)

if __name__=='__main__':main()
