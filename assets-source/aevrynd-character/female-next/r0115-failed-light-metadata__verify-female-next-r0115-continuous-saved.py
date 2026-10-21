"""Saved original-source pose identity, scoped neck geometry and matched second light."""
from pathlib import Path
import bpy,numpy as np,json,hashlib,ast,time,importlib.util,os
from mathutils import Vector,Matrix
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0115-native-continuous-neck';PRE=E.parent/'r0113-coherent-head-foundation';BASE=S/'aevrynd-female-next-r0113-b-native-neck-skin.blend';OUT=S/'r0115-source/aevrynd-female-next-r0115-b-continuous-native-neutral.blend'
sp=importlib.util.spec_from_file_location('r115saved',Path(__file__).with_name('build-female-next-r0113-native-neck-character.py'));b=importlib.util.module_from_spec(sp);sp.loader.exec_module(b);q=b.q
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.tolist() if isinstance(a,np.ndarray) else a.item())+'\n',encoding='utf-8',newline='\n')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def topo(V,T):
    edges=np.concatenate([T[:,[0,1]],T[:,[1,2]],T[:,[2,0]]]);direction=np.where(edges[:,0]<edges[:,1],1,-1);edges.sort(axis=1);key=edges[:,0].astype('i8')*len(V)+edges[:,1];order=np.argsort(key);_,starts,counts=np.unique(key[order],return_index=True,return_counts=True);sign=np.add.reduceat(direction[order],starts)
    return {'vertices':len(V),'triangles':len(T),'uniqueEdges':len(counts),'edgesWithIncidenceNotTwo':int(np.count_nonzero(counts!=2)),'edgesWithSameOrientationTwice':int(np.count_nonzero(sign)),'eulerCharacteristic':int(len(V)-len(counts)+len(T)),'signedExternalSurfaceVolumeM3':float(np.einsum('ij,ij->i',V[T[:,0]],np.cross(V[T[:,1]],V[T[:,2]])).sum()/6),'notASelfIntersectionOrSkinWallThicknessProof':True}
def main():
    tick=time.time();digest=sha(OUT);bpy.ops.wm.open_mainfile(filepath=str(OUT));skin=bpy.data.objects['AFN113_COMPLETE_WOMAN_COHERENT_HEAD'];raw=bpy.data.objects['AFN115_EDITABLE_CONNECTED_NATIVE_ADULT_SOURCE'];raw.hide_set(False);raw.hide_render=True;states=[];neutral=None
    for label,value in [('neutral',0.),('half',.5),('closed',1.),('restored',0.)]:
        for k in raw.data.shape_keys.key_blocks:k.value=0.
        for side in ['L','R']:raw.data.shape_keys.key_blocks['AFN115_NATIVE_CLOSED_'+side].value=value
        raw.data.shape_keys.update_tag();raw.update_tag();b.deliver(value);rd,expected,RT=b.u.b.geom(raw);expected=expected.copy();d,V,T=b.u.b.geom(skin);V=V.copy();T=T.copy();assert np.isfinite(V).all()
        if neutral is None:neutral=V.copy();triangles=T.copy()
        err=float(np.linalg.norm(V-expected,axis=1).max());assert err<5e-7
        states.append({'state':label,'assignedBlink':value,'actualSkinAgainstOriginalOwnSourceMaxM':err,'actualSkinMaximumMoveM':float(np.linalg.norm(V-neutral,axis=1).max()),'actualKeyValues':{k.name:k.value for k in skin.data.shape_keys.key_blocks},'evaluatedVertices':len(V),'evaluatedTriangles':len(T)})
    assert states[-1]['actualSkinMaximumMoveM']==0 and states[2]['actualSkinMaximumMoveM']>.009
    for k in raw.data.shape_keys.key_blocks:k.value=0.
    raw.data.shape_keys.update_tag();raw.update_tag();raw.hide_set(True);b.deliver(0)
    fibres={}
    for n in ['AFN97_TUCKED_ARTIST_BOB_CHILDREN','AFN57_NATIVE_BROWS','AFN57_NATIVE_LASHES']:
        ob=bpy.data.objects[n];P=q.hair(ob);rad=q.arr(ob.data.attributes['radius'].data,'value',len(ob.data.attributes['radius'].data));assert np.isfinite(P).all();fibres[n]={'curves':len(ob.data.curves),'actualEvaluatedPoints':len(P),'radiusSha256':hashlib.sha256(rad.tobytes()).hexdigest(),'radiusPositive':bool((rad>0).all()),'notRenderedSweptFiniteCurveOccupancyProof':True}
    oldRequested=np.load(E/'continuous-source-lineage.npz')['oldRequestedWorld'];tree=KDTree(len(neutral))
    for i,p in enumerate(neutral):tree.insert(Vector(p),i)
    tree.balance();errors=np.array([tree.find(Vector(p))[2] for p in oldRequested]);identity={'oldRequestedPoints':len(oldRequested),'maxSameSourceHeadCoordinateErrorM':float(errors.max()),'quantilesM':np.quantile(errors,[0,.5,.95,1]),'previousCutBoundaryCausalHypothesisWithdrawn':True,'reason':'A baked closed Basis invalidated neutral identity. B restores original actual neutral. The initial1.536mm mismatch is not evidence that an old neck cut changed the requested root vertices.'};assert errors.max()<5e-6
    textures=[]
    for im in bpy.data.images:
        if im.source=='FILE' and not im.packed_file and im.filepath:
            p=Path(bpy.path.abspath(im.filepath));assert p.is_file(),str(p);textures.append({'name':im.name,'relative':im.filepath,'absolute':str(p),'sha256':sha(p),'bytes':p.stat().st_size})
    source=Path('C:/Users/USER/.cache/aevrynd-character-source/r0115')/OUT.name;archive=R/'sites-engine-journey/assets-source/aevrynd-character/female-next/r0115-source'/OUT.name;assert os.path.samefile(OUT,source) and os.path.samefile(OUT,archive)
    top=topo(neutral,triangles);save('minimum-saved-continuous-readback.json',{'status':'INDEPENDENT_COMPLETE_SOURCE_REOPENS_OWN_NEUTRAL_HALF_CLOSED_RESTORE_MATCH','candidate':{'source':str(OUT),'sha256':digest,'bytes':OUT.stat().st_size,'physicalSource':str(source),'archivePath':str(archive)},'actualPoseStates':states,'originalSourceHeadIdentity':identity,'actualSkinTopology':top,'allFibres':fibres,'externalTextures':textures,'canonicalArchiveAndPhysicalFullSourceSameFile':True,'functionScope':'Own native blink source/delivery/restore and saved geometry only; natural complete blink/body rig/oral/guide/cloth/runtime not proved.','sourceUnchangedDuringInspection':sha(OUT)==digest,'seconds':time.time()-tick})
    # Cheap scoped disproof on the changed neck/shoulder area. Exclude shared
    # source vertex neighbourhoods explicitly; never call it a global proof.
    code=Path(__file__).with_name('verify-female-next-r0037-eye-margin.py');parsed=ast.parse(code.read_text(encoding='utf-8'));defs=[x for x in parsed.body if isinstance(x,ast.FunctionDef) and x.name in ['inside','intersections']];ns={'np':np};exec(compile(ast.Module(body=defs,type_ignores=[]),str(code),'exec'),ns);intersections=ns['intersections'];centres=neutral[triangles].mean(1);region=np.flatnonzero((centres[:,2]>1.20)&(centres[:,2]<1.445)&(abs(centres[:,0])<.24));full=BVHTree.FromPolygons(neutral.tolist(),triangles.tolist(),all_triangles=True,epsilon=0.);part=BVHTree.FromPolygons(neutral.tolist(),triangles[region].tolist(),all_triangles=True,epsilon=0.);pairs=full.overlap(part);seen=set();excluded=0;tested=0;hits=[]
    for ai,bj in pairs:
        bi=int(region[bj]);a,c=sorted((int(ai),bi))
        if a==c or (a,c) in seen:continue
        seen.add((a,c));ta=triangles[a];tc=triangles[c]
        if np.intersect1d(ta,tc).size:excluded+=1;continue
        tested+=1;pts=intersections(neutral[ta],neutral[tc])
        if pts:hits.append({'triangles':[a,c],'intersectionOrTouchWorldPointsM':[p.tolist() for p in pts[:4]]})
        if len(hits)>=16:break
    contact={'status':'SCOPED_STATIC_NONADJACENT_NECK_TEST_ONLY','representation':'Actual baked displayed skin loop triangles, unchanged neutral. Closed external surface; no explicit finite skin-wall thickness or hair sweep certification.','regionCentroidBounds':{'worldZ':[1.20,1.445],'absWorldXBelow':.24},'regionTriangles':len(region),'BVHCandidatePairs':len(pairs),'uniquePairsSeen':len(seen),'sharedSourceVertexNeighbourPairsExcluded':excluded,'nonNeighbourPairsActuallyTested':tested,'storedIntersectionOrTouchWitnesses':len(hits),'witnesses':hits,'witnessCap':16,'notGlobalTotalMinimumOrContinuousProof':True,'globalSignedMinimumM':None,'adjacentFoldSkinWallHairBodyEyeClothContinuousUnaccepted':True,'existingUnchangedIntersectionRoutine':str(code),'routineSha256':sha(code)};save('scoped-static-neck-contact.json',contact);print('R115_SCOPED_SAVED_NECK_CHECK_DONE',len(region),tested,len(hits),time.time()-tick,flush=True)
    # Same new light arrangement for baseline and B; exact camera/lens/exposure.
    controls=json.loads((PRE/'b-view-controls.json').read_text(encoding='utf-8'))[0];lightRows=[]
    for tag,path in [('baseline',BASE),('candidate',OUT)]:
        bpy.ops.wm.open_mainfile(filepath=str(path));b.deliver(0);scene=bpy.context.scene;scene.camera.matrix_world=Matrix(controls['camera']);scene.camera.data.lens=controls['lensMM'];scene.render.resolution_x=scene.render.resolution_y=640;scene.render.resolution_percentage=100;scene.cycles.samples=16;scene.cycles.seed=controls['seed'];scene.render.hair_subdiv=3;scene.view_settings.exposure=controls['exposure'];scene.view_settings.look=controls['look'];target=Vector((0,-.04,1.43))
        for name,row in controls['lights'].items():
            ob=bpy.data.objects[name];ob.matrix_world=Matrix(row['matrix']);ob.location.x=-ob.location.x;ob.rotation_euler=(target-ob.location).to_track_quat('-Z','Y').to_euler();ob.data.energy=row['energy'];ob.data.color=row['color']
        bpy.context.view_layer.update();scene.render.filepath=str(E/('second-light-'+tag+'-face.png'));record={'file':scene.render.filepath,'camera':np.array(scene.camera.matrix_world).tolist(),'lensMM':scene.camera.data.lens,'lights':b.u.m.m.q.lights(),'exposure':scene.view_settings.exposure,'look':scene.view_settings.look,'samples':scene.cycles.samples,'resolution':[640,640],'seed':scene.cycles.seed,'hairSubdiv':3,'neutralInput':0.};bpy.ops.render.render(write_still=True);lightRows.append(record);save('matched-second-light-controls.json',lightRows)
    assert {k:v for k,v in lightRows[0].items() if k!='file'}=={k:v for k,v in lightRows[1].items() if k!='file'}
    assert sha(OUT)==digest;print('R115_SAVED_SOURCE_AND_MATCHED_SECOND_LIGHT_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
