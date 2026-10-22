"""Actual native lamellar morph path from the unchanged aspherical inner surface.
Stop failed native field raycasting, preserve A, and author real editable key shapes.
"""
from pathlib import Path
import bpy,numpy as np,json,time,datetime,importlib.util
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0145-aspherical-lid-wall';S=R/'engine/assets/characters/female-next/source';OUT=S/'r0145-source/aevrynd-female-next-r0145-b-native-lamellar-morph.blend'
sp=importlib.util.spec_from_file_location('r145morph',Path(__file__).with_name('build-female-next-r0145-aspherical-lid-wall.py'));h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h);a=h.a
STEPS=8
def radial_surface(directions,normals,offsets):
    result=np.empty(len(directions))
    for start in range(0,len(directions),2048):
        den=directions[start:start+2048]@normals.T;valid=den>1e-15;dist=np.full_like(den,np.inf);np.divide(offsets[None,:],den,out=dist,where=valid);result[start:start+2048]=dist.min(1)
    assert np.isfinite(result).all() and (result>0).all();return result
def main():
    tick=time.time();assert not OUT.exists() and not (E/'b-build-summary.json').exists();old=json.loads((E/'a-build-summary.json').read_text('utf-8'));src=Path(old['output']);assert a.a.sha(src)==old['sha256'];bpy.ops.wm.open_mainfile(filepath=str(src));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update();rig=bpy.data.objects[old['actualRig']];names=a.FIXED+a.MOVING;before={n:a.geometry(bpy.data.objects[n]) for n in names};raw={n:a.rawsig(bpy.data.objects[n]) for n in names};protected=a.a.protected();affected=[h.h.h.SKIN]+h.h.h.ATTACH;oldClosed={}
    scene.frame_set(9);bpy.context.view_layer.update()
    for n in affected:oldClosed[n]=a.geometry(bpy.data.objects[n])[0]
    scene.frame_set(1);bpy.context.view_layer.update();prior=json.loads((E.parent/'r0144-current-skin-blink/current-skin-blink-construction.json').read_text('utf-8'));surfaces={};reports={};lineage={}
    h.save('native-lamellar-morph-authoring-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originalStartedUTC':'2026-10-22T01:14:55+00:00','failedNativeRayRepairHandle':67964,'failedPremise':'Unit forward capability succeeds, but production direction fields still fail after explicit normalization. Cause unresolved; do not claim normalization repaired the field or reuse fallback images as path improvement.','changedMethod':'Compute actual aspherical radial lamellar paths from original cavity planes and author native editable shape keys, with standard rig-property drivers. No native field raycast/fallback remains on displayed affected layers.','sameOriginalAnatomicalConstructionPremise':'Original angular closure, source radial inner/outer gap, source cavity and actual ocular meshes unchanged; fixed8 interval morph representation, not a radius/angle/clearance sweep.','originalAAndAllFailedAttemptsPreserved':True})
    for side in ['L','R']:
        C=np.array(prior['actualNativeDomains'][side]['actualOpticalCentreWorld']);axis=np.array(prior['actualNativeDomains'][side]['axisWorld']);V,F=a.geometry(bpy.data.objects['AFN138_'+side+'_ANATOMICAL_SOCKET_CONSTRUCTION']);tri=V[F]-C;normals=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);length=np.linalg.norm(normals,axis=1);valid=length>1e-20;normals=normals[valid]/length[valid,None];offsets=np.einsum('ij,ij->i',normals,tri[valid,0]);flip=offsets<0;normals[flip]*=-1;offsets[flip]*=-1;assert offsets.min()>0
        convexResidual=float(((V-C)@normals.T-offsets).max());assert convexResidual<2e-7,('Original cavity is not the recorded convex surface',side,convexResidual);surfaces[side]=(C,axis,normals,offsets);reports[side]={'constructionObject':'AFN138_'+side+'_ANATOMICAL_SOCKET_CONSTRUCTION','originalCavityVertices':len(V),'originalCavityTriangles':len(F),'derivedPlaneCount':len(normals),'zeroAreaConstructionTrianglesNotUsedAsPlanes':int((~valid).sum()),'convexPlaneNumericResidualM':convexResidual,'planeResidualIsConstructionNumericCheckNotContactTolerance':True,'addedPhysicalClearanceM':0.,'originalAngularFieldAndOpticalGeometryUnchanged':True}
    shapes={}
    for name in affected:
        ob=bpy.data.objects[name];assert ob.data.shape_keys is None and ob.modifiers[0].type=='NODES';ob.modifiers.remove(ob.modifiers[0]);A=np.array(ob.matrix_world);inv=np.linalg.inv(A);rawP=np.empty((len(ob.data.vertices),3),dtype='f4');ob.data.vertices.foreach_get('co',rawP.ravel());P=np.c_[rawP,np.ones(len(rawP))]@A.T;P=P[:,:3];angles={s:h.attr_array(ob.data,'AFN144_Angle_'+s).astype('f8') for s in ['L','R']};assert not ((angles['L']!=0)&(angles['R']!=0)).any();basis=ob.shape_key_add(name='Basis');shapeRows=[]
        for side in ['L','R']:
            ids=np.flatnonzero(angles[side]!=0);C,axis,N,D=surfaces[side];rel=P[ids]-C;r0=np.linalg.norm(rel,axis=1);u0=rel/r0[:,None];inner0=radial_surface(u0,N,D);gap=r0-inner0
            lineage[name+'-'+side+'-activeIds']=ids;lineage[name+'-'+side+'-originalRadialGap']=gap
            for k in range(1,STEPS+1):
                alpha=k/STEPS;t=angles[side][ids]*alpha;c=np.cos(t)[:,None];s=np.sin(t)[:,None];rotated=rel*c+np.cross(np.broadcast_to(axis,rel.shape),rel)*s+axis[None,:]*((rel@axis)[:,None]*(1-c));u=rotated/np.linalg.norm(rotated,axis=1)[:,None];inner=radial_surface(u,N,D);Q=P.copy();Q[ids]=C+u*(inner+gap)[:,None];local=(np.c_[Q,np.ones(len(Q))]@inv.T)[:,:3];key=ob.shape_key_add(name='AFN145_'+side+'_LAMELLAR_%02d'%k);key.relative_key=basis;key.data.foreach_set('co',local.astype('f4').ravel());fc=key.driver_add('value');d=fc.driver;d.type='SCRIPTED';v=d.variables.new();v.name='blink';v.type='SINGLE_PROP';v.targets[0].id=rig;v.targets[0].data_path='["'+h.PROPS[side]+'"]';d.expression='max(0.0,1.0-abs(blink*8.0-%d.0))'%k
                shapeRows.append({'side':side,'alpha':alpha,'key':key.name,'actualEditablePoints':len(local),'activeMovedPoints':len(ids),'largestAuthoredWorldDisplacementM':float(np.linalg.norm(Q-P,axis=1).max()),'minimumOriginalRadialGapM':float(gap.min()),'maximumOriginalRadialGapM':float(gap.max())})
        shapes[name]=shapeRows
    operations=[]
    for f in [1,2,5,9,17]:
        scene.frame_set(f);rig.update_tag();bpy.context.view_layer.update();row={'frame':f,'actualControls':{s:float(rig[p]) for s,p in h.PROPS.items()},'actualDisplayedMovementM':{},'actualNonzeroNativeKeys':{}}
        for name in affected:
            W,T=a.geometry(bpy.data.objects[name]);assert np.isfinite(W).all();row['actualDisplayedMovementM'][name]=float(np.linalg.norm(W-before[name][0],axis=1).max());row['actualNonzeroNativeKeys'][name]={k.name:float(k.value) for k in bpy.data.objects[name].data.shape_keys.key_blocks if k.value!=0}
            if f==9:row.setdefault('actualDifferenceFromFailedAClosedM',{})[name]=float(np.linalg.norm(W-oldClosed[name],axis=1).max())
        operations.append(row)
    assert max(operations[0]['actualDisplayedMovementM'].values())<2e-6 and max(operations[-1]['actualDisplayedMovementM'].values())<2e-6 and max(operations[3]['actualDifferenceFromFailedAClosedM'].values())>.0001
    scene.frame_set(1);rig.update_tag();bpy.context.view_layer.update();assert all(a.rawsig(bpy.data.objects[n])==raw[n] for n in names) and a.a.protected()==protected
    rig['AFN145_native_morph_scope']='Actual displayed native shape-key lamellar path on same current Skin/lashes/wet-line;8 fixed path intervals per side driven by existing blink properties. Aspherical inner construction and original radial lamellar gap. Not full anatomy, physiological blink, combined gaze/blink, finite/self/continuous contacts or runtime acceptance.'
    bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=False);np.savez_compressed(E/'b-native-lamellar-path-lineage.npz',**lineage)
    h.save('b-native-lamellar-morph-construction.json',{'source':str(src),'actualControllers':h.PROPS,'actualRig':rig.name,'actualSkin':old['actualSkin'],'nativeEditableKeyShapes':shapes,'originalAsphericalConstruction':reports,'fixedPathIntervalsPerSide':STEPS,'interpolation':'Native piecewise linear relative-key basis in control alpha; geometric path knots are authored against actual original cavity. Not exact continuous collision or physiological tissue simulation.','oldFailedFieldModifiersRemovedFromActualLayers':affected,'noFallbackOrInvisibleProxyUsedAsOperationProof':True,'actualAuthoringOperations':operations,'originalRawMeshesUVMaterialsAndAllOriginalVerticesRetained':True,'allContactClaimsNeedIndependentActualGeometryRetest':True,'appearanceFunctionContactRuntimeAccepted':False,'secondsBeforePreview':time.time()-tick})
    h.save('b-build-summary.json',dict(old,source=str(src),output=str(OUT),sha256=a.a.sha(OUT),bytes=OUT.stat().st_size,oneCompleteCandidate=False,twoFullSavedCandidateStatesInOneOriginalRound=True,originalAAndItsKnownRayFailurePreserved=True,normalizedNativeRayDirections=False,nativeLamellarMorphPath=True,secondsBeforePreview=time.time()-tick));views=[]
    for v in ['face','body-face','profile','oblique','back']:views.append(a.b.u.v.image('b-native-lamellar-morph',v));h.save('b-view-controls.json',views)
    motion=[]
    for f in [5,9,13,17]:
        scene.frame_set(f);bpy.context.view_layer.update()
        for v in ['face','body-face']:
            row=a.b.u.v.image('b-blink-%03d'%f,v);row['actualBlink']={s:float(rig[p]) for s,p in h.PROPS.items()};motion.append(row);h.save('b-actual-blink-motion-controls.json',motion)
    scene.frame_set(9);bpy.context.view_layer.update();h.save('b-actual-closed-profile-control.json',a.b.u.v.image('b-closed-blink','profile'));scene.frame_set(1);bpy.context.view_layer.update();assert a.a.protected()==protected and a.a.sha(src)==old['sha256'];print('R145_B_ACTUAL_NATIVE_LAMELLAR_MORPH_COMPLETE_HEAD_BODY_BLINK_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
