"""Minimum independent saved-source readback after visible neck rejection; no broad audit."""
from pathlib import Path
import bpy, numpy as np, json, hashlib, time, importlib.util

R=Path('D:/Download/Aevrynd')
E=R/'Evidence/character-female-next/r0114-native-neck-transition'
S=R/'engine/assets/characters/female-next/source'
BASE=S/'aevrynd-female-next-r0113-b-native-neck-skin.blend'
OUT=S/'aevrynd-female-next-r0114-a-native-neck-transition.blend'
sp=importlib.util.spec_from_file_location('r114readback',Path(__file__).with_name('build-female-next-r0113-native-neck-character.py'))
b=importlib.util.module_from_spec(sp);sp.loader.exec_module(b);q=b.q

def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def raw_keys(ob):
    return {k.name:q.arr(k.data,'co',len(k.data),3).copy() for k in ob.data.shape_keys.key_blocks}

def radius(ob):
    a=ob.data.attributes.get('radius')
    return None if a is None else hashlib.sha256(q.arr(a.data,'value',len(a.data)).tobytes()).hexdigest()

def fibres():
    return {n:{'world':q.hair(bpy.data.objects[n]).copy(),'curves':len(bpy.data.objects[n].data.curves),'radiusSha256':radius(bpy.data.objects[n])} for n in ['AFN97_TUCKED_ARTIST_BOB_CHILDREN','AFN57_NATIVE_BROWS','AFN57_NATIVE_LASHES']}

def main():
    tick=time.time();digests={str(p):sha(p) for p in [BASE,OUT]}
    bpy.ops.wm.open_mainfile(filepath=str(BASE));b.deliver(0)
    ob=bpy.data.objects['AFN113_COMPLETE_WOMAN_COHERENT_HEAD'];keys=raw_keys(ob);oldCount=len(ob.data.vertices)
    baseline={};fibreBaseline=None
    for label,value in [('neutral',0.),('half',.5),('closed',1.),('restored',0.)]:
        b.deliver(value);d,V,T=b.u.b.geom(ob);baseline[label]=V.copy()
        if label=='neutral':fibreBaseline=fibres()
    bpy.ops.wm.open_mainfile(filepath=str(OUT));b.deliver(0)
    ob=bpy.data.objects['AFN113_COMPLETE_WOMAN_COHERENT_HEAD'];newKeys=raw_keys(ob)
    assert set(keys)==set(newKeys)
    exact={n:np.array_equal(v,newKeys[n][:oldCount]) for n,v in keys.items()};assert all(exact.values())
    states=[];neutral=None
    for label,value in [('neutral',0.),('half',.5),('closed',1.),('restored',0.)]:
        b.deliver(value);d,V,T=b.u.b.geom(ob);V=V.copy();assert np.isfinite(V).all()
        if neutral is None:neutral=V.copy()
        error=float(np.linalg.norm(V[:oldCount]-baseline[label],axis=1).max());assert error<1e-7
        states.append({'state':label,'assignedBlink':value,'oldActualDisplayedVerticesAgainstR113BMaxErrorM':error,'actualSkinMaximumMoveM':float(np.linalg.norm(V-neutral,axis=1).max()),'newNeckVerticesMaximumMoveM':float(np.linalg.norm(V[oldCount:]-neutral[oldCount:],axis=1).max()),'evaluatedVertices':len(V),'evaluatedTriangles':len(T)})
    assert states[-1]['actualSkinMaximumMoveM']==0
    assert states[2]['actualSkinMaximumMoveM']>0
    current=fibres();fibreRecords={}
    for n,base in fibreBaseline.items():
        row=current[n];err=float(np.linalg.norm(row['world']-base['world'],axis=1).max())
        assert err==0 and row['curves']==base['curves'] and row['radiusSha256']==base['radiusSha256']
        fibreRecords[n]={'curves':row['curves'],'actualNeutralPoints':len(row['world']),'againstR113BMaxWorldErrorM':err,'radiusSha256':row['radiusSha256'],'radiusEqualR113B':True}
    textures=[]
    for im in bpy.data.images:
        if im.source=='FILE' and not im.packed_file and im.filepath:
            p=Path(bpy.path.abspath(im.filepath));assert p.is_file(),str(p)
            textures.append({'name':im.name,'relative':im.filepath,'absolute':str(p),'sha256':sha(p),'bytes':p.stat().st_size})
    assert all(sha(Path(p))==v for p,v in digests.items())
    result={'status':'SAVED_COMPLETE_SOURCE_REOPENS_VISIBLE_NECK_CONSTRUCTION_REJECTED','candidate':{'source':str(OUT),'sourceSha256':digests[str(OUT)],'sourceBytes':OUT.stat().st_size,'vertices':len(neutral),'triangles':states[0]['evaluatedTriangles'],'externalTextures':textures},'baselineSource':{'source':str(BASE),'sha256':digests[str(BASE)],'bytes':BASE.stat().st_size},'oldRawNeutralAndAllShapeKeysByteExact':exact,'oldVertices':oldCount,'newVertices':len(neutral)-oldCount,'actualPoseStates':states,'allOriginalFibresAndRadiiPreserved':fibreRecords,'sourceFilesUnchangedDuringVerification':True,'contact':{'status':'UNACCEPTED_NOT_RETESTED_AFTER_VISIBLE_FAILURE','newNeckFiniteSelfBodyHairAndContinuousProved':False,'globalSignedMinimumM':None,'previousR113OpticalWitnessesRemainAnUnacceptedBaselineNotANewR114Test':True,'sourceReference':'../r0113-coherent-head-foundation/minimum-saved-coherent-readback.json'},'wholeBodyRigOralGuideEditingNaturalHairClothesRuntimeNotProved':True,'completeAppearanceOrUsableOperationAccepted':False,'seconds':time.time()-tick}
    (E/'minimum-saved-neck-readback.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('R114_MINIMUM_REOPEN_AND_PRESERVED_ACTUAL_POSES_DONE',len(neutral),states[2]['actualSkinMaximumMoveM'],time.time()-tick,flush=True)

if __name__=='__main__':main()
