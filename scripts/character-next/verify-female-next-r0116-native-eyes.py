"""Independent actual native geometry/own blink, capped optical surface witnesses and matched lighting."""
from pathlib import Path
import bpy,numpy as np,json,hashlib,ast,time,importlib.util,os
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0116-native-compatible-eyes';PRE=E.parent/'r0115-native-continuous-neck';BASE=S/'r0115-source/aevrynd-female-next-r0115-b-continuous-native-neutral.blend';OUT=S/'r0116-source/aevrynd-female-next-r0116-a-native-paired-eyes.blend'
sp=importlib.util.spec_from_file_location('r116readback',Path(__file__).with_name('build-female-next-r0116-native-eye-character.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);b=a.b;q=a.q
def save(n,o):a.save(n,o)
def main():
    tick=time.time();digest=a.sha(OUT);bpy.ops.wm.open_mainfile(filepath=str(OUT));skin=bpy.data.objects['AFN113_COMPLETE_WOMAN_COHERENT_HEAD'];raw=bpy.data.objects['AFN115_EDITABLE_CONNECTED_NATIVE_ADULT_SOURCE'];raw.hide_set(False);raw.hide_render=True;source=json.loads((E/'native-eye-source-authoring.json').read_text(encoding='utf-8'));line=np.load(E/'native-eye-source-lineage.npz');eyeRows=[]
    for part in source['actualSourceParts']:
        ob=bpy.data.objects[part['name']];d,P,T=b.u.b.geom(ob);err=float(np.linalg.norm(P-line['actualWorld'][part['sourceVertexIDs']],axis=1).max());assert err<3e-7;eyeRows.append({'name':ob.name,'sourceVertices':len(P),'actualTriangles':len(T),'actualWorldAgainstOriginalNativeMappedSourceMaxM':err,'finiteWallThicknessOrIndependentIrisPupilNotProved':True})
    parsed=ast.parse(Path(__file__).with_name('verify-female-next-r0037-eye-margin.py').read_text(encoding='utf-8'));ns={'np':np};exec(compile(ast.Module(body=[n for n in parsed.body if isinstance(n,ast.FunctionDef) and n.name in ['inside','intersections']],type_ignores=[]),'unchanged-r37-surface-intersections','exec'),ns);intersections=ns['intersections'];states=[];contacts=[];neutral=None;neutralBad=False
    for label,value in [('neutral',0.),('half',.5),('closed',1.),('restored',0.)]:
        for k in raw.data.shape_keys.key_blocks:k.value=0.
        for side in ['L','R']:raw.data.shape_keys.key_blocks['AFN115_NATIVE_CLOSED_'+side].value=value
        raw.data.shape_keys.update_tag();raw.update_tag();b.deliver(value);dd,expected,TT=b.u.b.geom(raw);expected=expected.copy();d,V,T=b.u.b.geom(skin);V=V.copy();T=T.copy();assert np.isfinite(V).all()
        if neutral is None:neutral=V.copy()
        err=float(np.linalg.norm(V-expected,axis=1).max());assert err<5e-7;states.append({'state':label,'assignedBlink':value,'actualSkinAgainstOwnOriginalNativeSourceMaxM':err,'actualSkinMaximumMoveM':float(np.linalg.norm(V-neutral,axis=1).max())})
        if label in ['neutral','closed'] and not neutralBad:
            bodyTree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True,epsilon=0.)
            for part in source['actualSourceParts']:
                ob=bpy.data.objects[part['name']];od,P,OT=b.u.b.geom(ob);P=P.copy();OT=OT.copy();other=BVHTree.FromPolygons(P.tolist(),OT.tolist(),all_triangles=True,epsilon=0.);pairs=bodyTree.overlap(other);hits=[];tested=0
                for i,j in pairs:
                    pts=intersections(V[T[i]],P[OT[j]]);tested+=1
                    if pts:hits.append({'actualSkinTriangle':int(i),'actualEyeTriangle':int(j),'worldIntersectionOrTouchPointsM':[p.tolist() for p in pts[:4]]})
                    if len(hits)>=16:break
                contacts.append({'state':label,'pair':'actual complete skin vs '+ob.name,'BVHCandidatePairs':len(pairs),'candidatePairsTestedUntilWitnessCap':tested,'storedIntersectionOrTouchWitnesses':len(hits),'witnessCap':16,'witnesses':hits,'noBodyRegionOrRootExclusions':True,'notGlobalTotalSignedMinimumOrFiniteProof':True});neutralBad|=label=='neutral' and bool(hits)
    assert states[-1]['actualSkinMaximumMoveM']==0
    for k in raw.data.shape_keys.key_blocks:k.value=0.
    raw.data.shape_keys.update_tag();raw.update_tag();raw.hide_set(True);b.deliver(0);textures=[]
    for im in bpy.data.images:
        if im.source=='FILE' and not im.packed_file and im.filepath:
            p=Path(bpy.path.abspath(im.filepath));assert p.is_file(),str(p);textures.append({'name':im.name,'relative':im.filepath,'absolute':str(p),'bytes':p.stat().st_size,'sha256':a.sha(p)})
    phys=Path('C:/Users/USER/AevryndCharacterSources/r0116')/OUT.name;archive=R/'sites-engine-journey/assets-source/aevrynd-character/female-next/r0116-source'/OUT.name;assert os.path.samefile(OUT,phys) and os.path.samefile(OUT,archive);assert a.sha(OUT)==digest
    save('minimum-saved-native-eye-readback.json',{'status':'INDEPENDENT_COMPLETE_SOURCE_REOPEN_NATIVE_GEOMETRY_OWN_BLINK_RESTORE','candidate':{'source':str(OUT),'sha256':digest,'bytes':OUT.stat().st_size,'physicalSource':str(phys),'archivePath':str(archive)},'actualEyeParts':eyeRows,'actualPoseStates':states,'allProtectedBodyKeysFibresAndRadiiAgainstWorkingBaseline':'a-build-summary.json','allExternalTextures':textures,'sourceAndArchiveSameCompleteFile':True,'contact':{'status':'UNACCEPTED','actualSurfaceWitnesses':contacts,'neutralWitnessStoppedClosedContactExpansion':neutralBad,'intersectionOrTouchNotAutomaticallyAnatomicalPenetrationClassification':True,'globalSignedMinimumM':None,'finiteWallContainedVolumeSelfHairClothContinuousAndNaturalDynamicsNotProved':True,'sourceCompatibilityNotContactAcceptance':True},'bodyRigOralGuideNaturalHairGazeIndependentIrisPupilRuntimeNotProved':True,'sourceUnchangedDuringVerification':True,'seconds':time.time()-tick});print('R116_INDEPENDENT_NATIVE_GEOMETRY_AND_BLINK_DONE',neutralBad,time.time()-tick,flush=True)
    controls=json.loads((PRE/'b-view-controls.json').read_text(encoding='utf-8'))[0];rows=[]
    for tag,path in [('baseline',BASE),('candidate',OUT)]:
        bpy.ops.wm.open_mainfile(filepath=str(path));b.deliver(0)
        if tag=='baseline':save('baseline-oblique-view-controls.json',b.u.v.image('baseline-r0115','oblique'))
        scene=bpy.context.scene;scene.camera.matrix_world=Matrix(controls['camera']);scene.camera.data.lens=controls['lensMM'];scene.render.resolution_x=scene.render.resolution_y=640;scene.render.resolution_percentage=100;scene.cycles.samples=16;scene.cycles.seed=controls['seed'];scene.render.hair_subdiv=3;scene.view_settings.exposure=controls['exposure'];scene.view_settings.look=controls['look'];target=Vector((0,-.04,1.43))
        for name,row in controls['lights'].items():
            ob=bpy.data.objects[name];ob.matrix_world=Matrix(row['matrix']);ob.location.x=-ob.location.x;ob.rotation_euler=(target-ob.location).to_track_quat('-Z','Y').to_euler();ob.data.energy=row['energy'];ob.data.color=row['color']
        bpy.context.view_layer.update();scene.render.filepath=str(E/('second-light-'+tag+'-face.png'));row={'file':scene.render.filepath,'camera':np.array(scene.camera.matrix_world).tolist(),'lensMM':scene.camera.data.lens,'lights':{o.name:{'matrix':np.array(o.matrix_world).tolist(),'energy':o.data.energy,'color':list(o.data.color)} for o in scene.objects if o.type=='LIGHT'},'exposure':scene.view_settings.exposure,'look':scene.view_settings.look,'samples':16,'resolution':[640,640],'seed':scene.cycles.seed,'hairSubdiv':3,'neutralInput':0.};bpy.ops.render.render(write_still=True);rows.append(row);save('matched-second-light-controls.json',rows)
    assert {k:v for k,v in rows[0].items() if k!='file'}=={k:v for k,v in rows[1].items() if k!='file'};assert a.sha(OUT)==digest;print('R116_MATCHED_OBLIQUE_AND_SECOND_LIGHT_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
