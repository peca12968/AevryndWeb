"""Rebuild complete native guide rest geometry in the current woman's space.
Same actual surface births, identities, count, radius and material as198.
The original current Hair is an inspected volume reference, never a root owner,
UV direction field, underlay, copied ribbon or imported foreign scalp.
"""
from pathlib import Path
import bpy,numpy as np,json,datetime,hashlib,time,importlib.util
from mathutils import Matrix

C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');R=Path('D:/Download/Aevrynd')
E=C/'evidence/character-female-next/r0199-current-space-rest-sculpt'
OUT=C/'assets-source/aevrynd-character/female-next/r0199-source/aevrynd-female-next-r0199-current-space-rest-sculpt.blend'
sp=importlib.util.spec_from_file_location('r199base',C/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;h=m.h
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(n,x):(E/n).write_bytes((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
def sha(p):return hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()

def cubic(K,t):
    # Interpolating Hermite segments, no smoothing of roots or geometric rescue.
    K=np.asarray(K);n=len(K);u=t*(n-1);i=min(int(u),n-2);v=u-i
    left=(K[min(i+1,n-1)]-K[max(i-1,0)])/2
    right=(K[min(i+2,n-1)]-K[i])/2
    return (2*v**3-3*v*v+1)*K[i]+(v**3-2*v*v+v)*left+(-2*v**3+3*v*v)*K[i+1]+(v**3-v*v)*right

def main():
    tick=time.time();t=json.loads((E/'before.json').read_text('utf-8'));assert not OUT.exists() and sha(t['source'])==t['sourceSha256']
    bpy.ops.wm.open_mainfile(filepath=t['source']);s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update()
    hair=bpy.data.objects['AFN198_ACTUAL_SURFACE_BORN_NATIVE_GROOM'];skin=bpy.data.objects[a.FIXED[0]];old=bpy.data.objects[a.FIXED[1]]
    protected={n:a.rawsig(bpy.data.objects[n]) for n in a.FIXED+a.MOVING}
    W,T=a.geometry(skin);V,HT=a.geometry(old)
    assert len(V)==57424 and len(HT)==81789
    # Measured current artist volume sections. These are form bounds only,
    # explicitly not follicles, tangent directions or nearest-root assignments.
    sections=[]
    for z in [1.38,1.40,1.43,1.46,1.49,1.52,1.55,1.58]:
        band=V[np.abs(V[:,2]-z)<.008]
        assert len(band)>15
        sections.append({'z':z,'vertices':len(band),'min':band.min(0).tolist(),'median':np.median(band,axis=0).tolist(),'max':band.max(0).tolist()})
    prior=np.load(E.parent/'r0198-native-birth-owned-scalp/native-surface-birth-lineage.npz')
    roots=prior['guideLogicalBirthWorld'].astype('f8');tri=prior['guideActualSkinTriangles'];normal=np.cross(W[tri[:,1]]-W[tri[:,0]],W[tri[:,2]]-W[tri[:,0]])
    normal/=np.linalg.norm(normal,axis=1)[:,None]
    raw=h.arr(hair.data.position_data,'vector',len(hair.data.position_data),3).astype('f8').reshape(252,16,3)
    authored=np.empty_like(raw);allKnots=[];regional=[]
    # Eight explicit current-space sculpt stations: root, lift, crown sweep,
    # temple/back clearance, side volume, lower curl, return and staggered tip.
    # Each of252 guides has its own root, section coordinate and full new shape.
    for gi,(root,no) in enumerate(zip(roots,normal)):
        sign=1 if root[0]>=0 else -1
        rx=abs(root[0]);front=np.clip((-root[1]+.005)/.095,0,1)
        back=np.clip((root[1]+.025)/.080,0,1)
        side=np.clip(rx/.074,0,1)
        high=np.clip((root[2]-1.455)/.115,0,1)
        # Form comes from measured original current Hair bounds, while control
        # stations are directly authored in this character's coordinates.
        band=V[np.abs(V[:,2]-1.46)<.012]
        same=band[(band[:,0]*sign>0)&(np.abs(band[:,1]-root[1])<.045)]
        assert len(same)>0,('unmeasured actual reference section',gi)
        width=float(np.quantile(np.abs(same[:,0]),.72))
        targetX=sign*(width*(.74+.26*side))
        # Back roots retain a complete rear layer; front sections swing away
        # from the cheek into the artist's side volume, rather than falling
        # straight across face/jaw as198. No source free point is retained.
        targetY=(-.047*(1-back)+.067*back)
        if rx<.025 and back>.35:targetX=sign*(.020+.055*side)
        curlZ=1.405-.025*back+.009*np.sin(gi*.63)
        crownZ=max(root[2]+.012*high,1.505+.057*high)
        if high<.25:crownZ=root[2]+.003
        lift=root+no*(.009+.005*high)
        K=np.array([
            raw[gi,0],
            lift,
            [root[0]+sign*(.022+.011*front)*high,root[1]+.004*back,crownZ],
            [targetX*.91,targetY-.010*front,min(crownZ-.025,root[2]-.010)],
            [targetX*1.06,targetY+.008*np.sin(gi*.27),max(curlZ+.050,root[2]-.090)],
            [targetX*1.02,targetY+.015,curlZ+.018],
            [targetX*.84,targetY+.008,curlZ-.007],
            [targetX*.80,targetY-.002,curlZ+.008]
        ])
        # Low nape roots use actual posterior volume, not the crown/temple arch.
        if root[2]<1.465:
            K[2]=lift+np.array([sign*.009,.008,-.012])
            K[3]=[targetX*.88,max(targetY,.045),root[2]-.025]
            K[4]=[targetX,max(targetY,.055),curlZ+.040]
            K[5:,1]=np.maximum(K[5:,1],.050)
        path=np.array([cubic(K,u) for u in np.linspace(0,1,16)])
        path[0]=raw[gi,0];path[1]=raw[gi,0]+no*.004
        authored[gi]=path;allKnots.append(K);regional.append({'guideID':gi,'actualBirthWorld':root.tolist(),'region':'nape' if root[2]<1.465 else ('rear' if back>.6 else 'temple/crown'),'referenceSectionWidthM':width})
    hair.data.position_data.foreach_set('vector',authored.astype('f4').ravel());hair.data.update_tag();hair.update_tag();bpy.context.view_layer.update()
    P,off=m.curveworld(hair);data=hair.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
    ids=h.arr(data.attributes['AFN198_PERSISTENT_BIRTH_ID'].data,'value',len(off),dtype='i4')
    assert len(off)==10191 and np.array_equal(np.sort(ids),np.arange(10191)) and np.isfinite(P).all()
    error=float(np.linalg.norm(P[off]-prior['shaftStartWorld'][ids],axis=1).max());assert error<3e-6
    assert protected=={n:a.rawsig(bpy.data.objects[n]) for n in protected}
    np.savez_compressed(E/'current-space-rest-sculpt-lineage.npz',previousGuideWorld=raw.astype('f4'),authoredGuideWorld=authored.astype('f4'),actualSculptStations=np.array(allKnots,'f4'),guideLogicalBirthWorld=roots.astype('f4'),guideActualSkinTriangles=tri,guideBirthBC=prior['guideBirthBC'],guideNormals=normal.astype('f4'),childBirthActualSkinTriangles=prior['childBirthActualSkinTriangles'],childBirthBC=prior['childBirthBC'],logicalBirthWorld=prior['logicalBirthWorld'],shaftStartWorld=prior['shaftStartWorld'],actualSkinUV=prior['actualSkinUV'])
    save('rest-sculpt-construction-summary.json',{'UTC':stamp(),'actualHair':hair.name,'actualSkin':skin.name,'actualControl':'All252 raw native guide positions through unchanged198 actual Skin root-displacement driver. All complete free paths rebuilt; no source-rest paths preserved.','actualGuides':252,'actualCurves':len(off),'actualPoints':len(P),'rawGuideMaximumChangeM':float(np.linalg.norm(authored-raw,axis=2).max()),'rawGuideRootMaximumChangeM':float(np.linalg.norm(authored[:,0]-raw[:,0],axis=1).max()),'actualNativeBirthCentreMaximumErrorM':error,'measuredOriginalCurrentHairVolumeSections':sections,'regionalAuthoring':regional,'actualOriginalHairRawSignature':protected[a.FIXED[1]],'allOldOriginalRawMeshUVSignaturesUnchanged':protected,'sameBirthIDsUVCountRadiusMaterialAndGenerator':True,'sourceHairUsedAsVolumeReferenceNotRootOwnerOrUVFlow':True,'notOriginal191CageOr193SparseGuideBlend':True,'appearanceFunctionContactRuntimeUnaccepted':True})
    captures=[]
    def capture(scene):
        captures.append({'UTC':stamp(),'loadedSource':bpy.data.filepath,'plannedCandidate':str(OUT),'output':scene.render.filepath,'frame':scene.frame_current,'cameraMatrixWorld':[list(v) for v in scene.camera.matrix_world],'lens':scene.camera.data.lens,'cameraType':scene.camera.data.type,'viewTransform':scene.view_settings.view_transform,'look':scene.view_settings.look,'exposure':scene.view_settings.exposure,'cyclesSamples':scene.cycles.samples,'seed':scene.cycles.seed,'hairType':scene.render.hair_type,'resolution':[scene.render.resolution_x,scene.render.resolution_y,scene.render.resolution_percentage],'newGroomVisible':not hair.hide_render,'originalHairVisible':not old.hide_render,'captureStateNotRenderGeometryDepsgraphProof':True});save('actual-render-pre-capture-states.json',captures)
    bpy.app.handlers.render_pre.append(capture);a.b.u.v.E=E
    hair.hide_render=True;old.hide_render=False
    for v in ['face','body-face']:s.camera.data.type='PERSP';a.b.u.v.image('baseline-original-working-hair',v)
    old.hide_render=True;hair.hide_render=False
    for v in ['face','body-face','oblique','profile','back']:s.camera.data.type='PERSP';a.b.u.v.image('a-current-space-rest-sculpt',v)
    bpy.app.handlers.render_pre.remove(capture);s.camera.matrix_world=Matrix(captures[2]['cameraMatrixWorld']);s.camera.data.lens=captures[2]['lens'];s.camera.data.type='PERSP'
    OUT.parent.mkdir(parents=True,exist_ok=True);bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    save('a-build-summary.json',{'UTC':stamp(),'output':str(OUT),'sha256':sha(OUT),'bytes':OUT.stat().st_size,'actualHair':hair.name,'actualSkin':skin.name,'actualBirths':'AFN198_ACTUAL_EDITABLE_SURFACE_BIRTHS','oneCandidate':True,'elapsedJobSeconds':time.time()-tick,'actualCurves':len(off),'actualPoints':len(P),'unaccepted':True})
    print('R199_ONE_COMPLETE_CURRENT_SPACE_REST_SCULPT_SAVED',flush=True)

if __name__=='__main__':main()
