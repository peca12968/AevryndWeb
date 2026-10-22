"""Reconnect explicit posterior strips and author the actual eye-aperture closure.
Replaces the complete old lining region with covered, positive-area topology;
never omits failed triangles or adds an external closing cap.
"""
from pathlib import Path
import bpy,numpy as np,json,time,datetime,importlib.util,collections
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0146-connected-palpebral-lining';S=R/'engine/assets/characters/female-next/source';SRC=S/'r0144-source/aevrynd-female-next-r0144-a-current-skin-blink.blend';OUT=S/'r0146-source/aevrynd-female-next-r0146-a-connected-palpebral-lining.blend'
def module(name,file):
    sp=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
c=module('r146base','build-female-next-r0144-current-skin-blink.py');a=c.a;native=module('r146morph','build-female-next-r0145-native-lamellar-morph.py');a.b.u.v.E=E;PROPS=c.PROPS
def save(n,x):(E/n).write_bytes((json.dumps(x,indent=2,default=lambda q:q.tolist() if isinstance(q,np.ndarray) else q.item() if isinstance(q,np.generic) else str(q))+'\n').encode())
def values(data,prop,n,k=1,dtype='f4'):
    x=np.empty((n,k),dtype=dtype) if k!=1 else np.empty(n,dtype=dtype);data.foreach_get(prop,x.ravel());return x
def attr(mesh,name,t,data):
    p=mesh.attributes.new(name,t,'POINT');p.data.foreach_set('value',np.asarray(data,dtype='i4' if t=='INT' else 'f4').ravel())
def vertex_weights(ob):
    x=np.zeros((len(ob.data.vertices),len(ob.vertex_groups)))
    for v in ob.data.vertices:
        for g in v.groups:x[v.index,g.group]=g.weight
    return x
def main():
    tick=time.time();assert not OUT.exists();patch=np.load(E/'posterior-patch-geometry.npz');bpy.ops.wm.open_mainfile(filepath=str(SRC));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update();skin=bpy.data.objects[c.h.SKIN];rig=bpy.data.objects['AFN138_ACTUAL_CURRENT_GAZE_RIG'];protected=a.a.protected();names=a.FIXED+a.MOVING;otherRaw={n:a.rawsig(bpy.data.objects[n]) for n in names if n!=skin.name};otherWorld={n:a.geometry(bpy.data.objects[n])[0] for n in names if n!=skin.name};old=skin.data;A=np.array(skin.matrix_world);inv=np.linalg.inv(A);oldLocal=values(old.vertices,'co',len(old.vertices),3);W=(np.c_[oldLocal,np.ones(len(oldLocal))]@A.T)[:,:3];oldWeights=vertex_weights(skin);oldFaces=[tuple(p.vertices) for p in old.polygons];oldMats=list(old.materials);oldUV={u.name:values(u.data,'uv',len(u.data),2) for u in old.uv_layers};oldNormals=values(old.corner_normals,'vector',len(old.loops),3) if old.has_custom_normals else None
    removed=set(int(i) for s in ['L','R'] for i in patch[s+'-replacedOriginalPolygons']);keepFaces=[i for i in range(len(oldFaces)) if i not in removed];keepIds=np.unique(np.array([v for i in keepFaces for v in oldFaces[i]],dtype='i4'));oldToNew=np.full(len(W),-1,dtype='i4');oldToNew[keepIds]=np.arange(len(keepIds));originalFaceEdges=collections.Counter(tuple(sorted(e)) for p in oldFaces for e in zip(p,p[1:]+p[:1]))
    for s in ['L','R']:
        ids=patch[s+'-boundaryOriginalIds'];assert (oldToNew[ids]>=0).all(),'Posterior lining is not attached to retained outer Skin'
        assert all(originalFaceEdges[tuple(sorted((int(x),int(y))))]==2 for x,y in zip(ids,np.roll(ids,-1))),('Source rim must be a shared native manifold boundary',s)
    save('connected-lining-authoring-start.json' if not (E/'connected-lining-authoring-start.json').exists() else 'weight-transfer-repair-authoring-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originalStartedUTC':'2026-10-22T02:06:15+00:00','action':'Replace the whole old posterior lining domain with authored boundary strips, retain actual shared outer Skin boundaries, derive common closed seam from the true aperture and use native morphs. No automatic subdivision or bad-face omission.'})
    old.calc_loop_triangles();oldTris=values(old.loop_triangles,'vertices',len(old.loop_triangles),3,'i4');oldTriPoly=values(old.loop_triangles,'polygon_index',len(old.loop_triangles),dtype='i4');oldInnerTris=oldTris[np.isin(oldTriPoly,list(removed))];oldInnerTree=BVHTree.FromPolygons([Vector(p) for p in W],oldInnerTris.tolist(),all_triangles=True)
    outerEdges=np.unique(np.sort(np.array([edge for i in keepFaces for edge in zip(oldFaces[i],oldFaces[i][1:]+oldFaces[i][:1])],dtype='i4'),axis=1),axis=0);graph=c.h.graph(W,outerEdges);oldAngles={s:np.zeros(len(W)) for s in ['L','R']};points=[W[keepIds]];weights=[oldWeights[keepIds]];lineage=[keepIds];patchMaps={};faceRoles=[0]*len(keepFaces);faces=[tuple(oldToNew[list(oldFaces[i])]) for i in keepFaces];patchCornerUV=[];patchFaceSides=[];patchReports={};oldConstruct=json.loads((E.parent/'r0144-current-skin-blink/current-skin-blink-construction.json').read_text('utf-8'));surface={}
    for side in ['L','R']:
        ids=patch[side+'-boundaryOriginalIds'];P=W[ids];C=np.array(oldConstruct['actualNativeDomains'][side]['actualOpticalCentreWorld']);bone=rig.data.bones[a.bone_names()[side]];B=np.array(rig.matrix_world@bone.matrix_local)[:3,:3];B/=np.linalg.norm(B,axis=0)[None,:];Q=(P-C)@B;x=Q[:,0];theta=np.mod(np.arctan2(Q[:,2],Q[:,1]),2*np.pi);left=int(x.argmin());right=int(x.argmax());N=len(ids)
        def path(step):
            out=[left]
            while out[-1]!=right:out.append((out[-1]+step)%N);assert len(out)<=N
            return np.array(out,dtype='i4')
        p1,p2=path(1),path(-1);upper,lower=(p1,p2) if Q[p1,2].mean()>Q[p2,2].mean() else (p2,p1)
        def theta_at(path,z):
            order=path[np.argsort(x[path])];xx,index=np.unique(x[order],return_index=True);return np.interp(z,xx,theta[order[index]])
        seam=.2*theta_at(upper,x)+.8*theta_at(lower,x);boundaryAngle=seam-theta;assert np.max(abs(boundaryAngle))<1.;boundaryAngle[left]=boundaryAngle[right]=0.;dist={};owner={}
        for kind,pathIds,support in [('UPPER',upper,.012),('LOWER',lower,.008)]:dist[kind],owner[kind]=c.h.geodesic(graph,ids[pathIds],support)
        for kind,pathIds,support,other in [('UPPER',upper,.012,'LOWER'),('LOWER',lower,.008,'UPPER')]:
            use=np.isfinite(dist[kind])&(dist[kind]<=dist[other]);ii=np.flatnonzero(use);t=np.clip(1-dist[kind][ii]/support,0,1);oldAngles[side][ii]=boundaryAngle[pathIds[owner[kind][ii]]]*t*t*(3-2*t)
        oldAngles[side][ids]=boundaryAngle;newP=patch[side+'-world'];parameters=patch[side+'-parameters'];boundaryColumn=parameters[:,0].astype('i4');depth=parameters[:,1];rel=P-C;thetaBack=np.arccos(np.clip((rel/np.linalg.norm(rel,axis=1)[:,None])@np.array([0,1,0]),-1,1));lengths=thetaBack*np.linalg.norm(rel,axis=1);isUpper=np.zeros(N,bool);isUpper[upper]=True;band=np.where(isUpper,.010,.005);fade=np.clip(1-depth*lengths[boundaryColumn]/band[boundaryColumn],0,1);newAngle=boundaryAngle[boundaryColumn]*fade*fade*(3-2*fade);newAngle[-1]=0
        count=sum(len(p) for p in points);mapping=np.r_[oldToNew[ids],np.arange(count,count+len(newP)-N)];patchMaps[side]=mapping;points.append(newP[N:]);lineage.append(np.full(len(newP)-N,-1,dtype='i4'));pw=[];gaps=[]
        for p in newP[N:]:
            nearest=oldInnerTree.find_nearest(Vector(p));fi=int(nearest[2]);closest,bc=c.h.actual_triangle_anchor(p,W[oldInnerTris[fi]]);ww=bc@oldWeights[oldInnerTris[fi]];ww=np.maximum(ww,0);ww/=ww.sum();pw.append(ww);gaps.append(float(np.linalg.norm(closest-p)))
        weights.append(np.array(pw));triangles=patch[side+'-triangles'];faces.extend(tuple(mapping[tri]) for tri in triangles);faceRoles.extend([1 if side=='L' else 2]*len(triangles))
        for tri in triangles:
            uv=np.c_[.02+.46*(parameters[tri,0]/N)+(.5 if side=='R' else 0),.02+.96*parameters[tri,1]];patchCornerUV.append(uv);patchFaceSides.append(side)
        V,F=a.geometry(bpy.data.objects['AFN138_'+side+'_ANATOMICAL_SOCKET_CONSTRUCTION']);tree=BVHTree.FromPolygons([Vector(p) for p in V],F.tolist(),all_triangles=True);surface[side]=(C,B[:,0],tree);patchReports[side]={'boundaryOriginalIds':ids,'upperBoundaryPathColumns':upper,'lowerBoundaryPathColumns':lower,'commonSeamOpticalTheta':seam,'boundaryBlinkAnglesRadians':boundaryAngle,'newPatchAngles':newAngle,'newPatchMap':mapping,'newPosteriorVertexWeightAnchorDistanceMaxM':max(gaps),'oldPosteriorPolygonsReplacedCompletely':patch[side+'-replacedOriginalPolygons'],'fullBoundarySharedWithOuterSkin':True,'canthiAnchored':True,'sourceCavityUsedAsRestAndSlideReferenceNotCollisionProof':True}
    world=np.concatenate(points);bindWeights=np.concatenate(weights);originalId=np.concatenate(lineage);newMesh=bpy.data.meshes.new('AFN146_COMPLETE_SKIN_WITH_CONNECTED_PALPEBRAL_LINING');local=(np.c_[world,np.ones(len(world))]@inv.T)[:,:3];newMesh.from_pydata(local.tolist(),[],faces);newMesh.update()
    lining=bpy.data.materials.new('AFN146_ANATOMICAL_POSTERIOR_LID_LINING');lining.use_nodes=True;bs=next(n for n in lining.node_tree.nodes if n.bl_idname=='ShaderNodeBsdfPrincipled');bs.inputs['Base Color'].default_value=(.58,.37,.33,1);bs.inputs['Roughness'].default_value=.32;lining['scope']='Engineering warm posterior lining material on explicitly rebuilt inner faces only; original outer face/body materials and exposure unchanged. Not calibrated tissue optics or material-only collision rescue.'
    for i,mat in enumerate(oldMats):
        newMesh.materials.append(mat if mat is not None else lining)
        if mat is None:newMesh.materials[i]=None
    newMesh.materials.append(lining);liningIndex=len(oldMats)
    for j,i in enumerate(keepFaces):newMesh.polygons[j].material_index=old.polygons[i].material_index;newMesh.polygons[j].use_smooth=old.polygons[i].use_smooth
    for p in list(newMesh.polygons)[len(keepFaces):]:p.material_index=liningIndex;p.use_smooth=True
    newUVRows=sum(len(oldFaces[i]) for i in keepFaces);newUVPatch=np.concatenate(patchCornerUV)
    for name,uv in oldUV.items():
        layer=newMesh.uv_layers.new(name=name);data=np.empty((len(newMesh.loops),2),dtype='f4');at=0
        for i in keepFaces:
            p=old.polygons[i];data[at:at+p.loop_total]=uv[p.loop_start:p.loop_start+p.loop_total];at+=p.loop_total
        data[at:]=newUVPatch;layer.data.foreach_set('uv',data.ravel());assert at==newUVRows
    if oldNormals is not None:
        normal=values(newMesh.corner_normals,'vector',len(newMesh.loops),3);at=0
        for i in keepFaces:
            p=old.polygons[i];normal[at:at+p.loop_total]=oldNormals[p.loop_start:p.loop_start+p.loop_total];at+=p.loop_total
        newMesh.normals_split_custom_set(normal.tolist())
    copiedAttributes=[];unmapped=[]
    for p in old.attributes:
        if p.name.startswith('.') or p.name in {'position','material_index','sharp_face','sharp_edge',*oldUV.keys(),'AFN144_Angle_L','AFN144_Angle_R'}:continue
        if p.domain=='POINT' and p.data_type in ['FLOAT','INT','BOOLEAN','FLOAT_VECTOR','FLOAT_COLOR','BYTE_COLOR']:
            prop,k=('vector',3) if p.data_type=='FLOAT_VECTOR' else ('color',4) if p.data_type in ['FLOAT_COLOR','BYTE_COLOR'] else ('value',1);typ='i4' if p.data_type=='INT' else 'bool' if p.data_type=='BOOLEAN' else 'f4';data=values(p.data,prop,len(p.data),k,typ);q=newMesh.attributes.new(p.name,p.data_type,'POINT');out=np.zeros((len(world),k),dtype=typ) if k!=1 else np.zeros(len(world),dtype=typ);out[:len(keepIds)]=data[keepIds];q.data.foreach_set(prop,out.ravel());copiedAttributes.append(p.name)
        else:unmapped.append((p.name,p.domain,p.data_type))
    angleFields={s:np.zeros(len(world)) for s in ['L','R']}
    for side in ['L','R']:angleFields[side][:len(keepIds)]=oldAngles[side][keepIds];angleFields[side][patchMaps[side]]=patchReports[side]['newPatchAngles']
    assert not ((angleFields['L']!=0)&(angleFields['R']!=0)).any()
    attr(newMesh,'AFN146_ORIGINAL_VERTEX_ID','INT',originalId)
    for s in ['L','R']:attr(newMesh,'AFN146_BlinkAngle_'+s,'FLOAT',angleFields[s])
    domain=newMesh.attributes.new('AFN146_POSTERIOR_LINING_SIDE','INT','FACE');domain.data.foreach_set('value',np.array(faceRoles,dtype='i4'));skin.data=newMesh
    for column,g in enumerate(skin.vertex_groups):
        active=np.flatnonzero(bindWeights[:,column]>0);unique=np.unique(bindWeights[active,column])
        for weight in unique:g.add(active[bindWeights[active,column]==weight].tolist(),float(weight),'REPLACE')
    observed=vertex_weights(skin)[:len(keepIds)];expected=oldWeights[keepIds];mismatch=np.argwhere(observed!=expected);report={'initialMismatchValues':len(mismatch),'initialMaximumWeightDifference':float(abs(observed-expected).max()),'groupNames':[g.name for g in skin.vertex_groups],'firstMismatches':[{'newVertex':int(i),'originalVertex':int(keepIds[i]),'group':int(j),'expected':float(expected[i,j]),'observed':float(observed[i,j])} for i,j in mismatch[:20]],'originalExactWeightGateRetained':True}
    save('original-weight-transfer-readback-and-repair.json',report)
    if len(mismatch):
        groupSpec=[(g.name,g.lock_weight) for g in skin.vertex_groups];skin.vertex_groups.clear()
        for name,locked in groupSpec:group=skin.vertex_groups.new(name=name);group.lock_weight=locked
        for column,group in enumerate(skin.vertex_groups):
            active=np.flatnonzero(bindWeights[:,column]>0)
            for weight in np.unique(bindWeights[active,column]):group.add(active[bindWeights[active,column]==weight].tolist(),float(weight),'REPLACE')
        observed=vertex_weights(skin)[:len(keepIds)];report['exactAfterNativeGroupClearRecreate']=bool(np.array_equal(observed,expected));report['maximumWeightDifferenceAfterClearRecreate']=float(abs(observed-expected).max());save('original-weight-transfer-readback-and-repair.json',report)
    assert np.array_equal(observed,expected),report
    skin.modifiers.remove(skin.modifiers[0]);scene.frame_set(1);rig.update_tag();bpy.context.view_layer.update();newW,newT=a.geometry(skin);areas=np.linalg.norm(np.cross(newW[newT[:,1]]-newW[newT[:,0]],newW[newT[:,2]]-newW[newT[:,0]]),axis=1);assert (areas>0).all(),('Actual reconstructed rest Skin has degenerate faces',int((areas==0).sum()))
    currentSkinTree=BVHTree.FromPolygons([Vector(p) for p in newW],newT.tolist(),all_triangles=True);attachmentAngles={};attachmentReports={};anchors=json.loads((E.parent/'r0139-native-lid-follow/native-lid-follow-construction.json').read_text('utf-8'))['actualAttachments']
    for name in c.h.ATTACH:
        ob=bpy.data.objects[name];ob.modifiers.remove(ob.modifiers[0]);P=a.geometry(ob)[0];fields={s:np.zeros(len(P)) for s in ['L','R']};records=[]
        for rec in anchors[name]['anchors']:
            verts=np.array(rec['vertices'],dtype='i4');root=int(rec['rootVertex']);hit=currentSkinTree.find_nearest(Vector(P[root]));tri=newT[int(hit[2])];closest,bc=c.h.actual_triangle_anchor(P[root],newW[tri])
            for s in ['L','R']:fields[s][verts]=bc@angleFields[s][tri]
            records.append({'vertices':verts,'rootVertex':root,'actualNewSkinTriangleVertices':tri,'barycentric':bc,'restSourceAttachmentDistanceM':float(np.linalg.norm(closest-P[root]))})
        assert not ((fields['L']!=0)&(fields['R']!=0)).any();attachmentAngles[name]=fields;attachmentReports[name]={'anchors':records,'sourceRootPositionsUnchanged':True,'restGapIsNotBiologicalRootOrContactAcceptance':True}
    allFields={skin.name:angleFields,**attachmentAngles};shapes={}
    for name,fields in allFields.items():
        ob=bpy.data.objects[name];assert ob.data.shape_keys is None;B=np.array(ob.matrix_world);bi=np.linalg.inv(B);rawP=values(ob.data.vertices,'co',len(ob.data.vertices),3);P=(np.c_[rawP,np.ones(len(rawP))]@B.T)[:,:3];basis=ob.shape_key_add(name='Basis');entries=[]
        for side in ['L','R']:
            ids=np.flatnonzero(fields[side]!=0);C,axis,tree=surface[side];rel=P[ids]-C;r=np.linalg.norm(rel,axis=1);gap=r-native.radial_surface(rel/r[:,None],tree,C)
            for k in range(1,9):
                alpha=k/8;t=fields[side][ids]*alpha;co=np.cos(t)[:,None];si=np.sin(t)[:,None];rot=rel*co+np.cross(np.broadcast_to(axis,rel.shape),rel)*si+axis[None,:]*((rel@axis)[:,None]*(1-co));u=rot/np.linalg.norm(rot,axis=1)[:,None];Q=P.copy();Q[ids]=C+u*(native.radial_surface(u,tree,C)+gap)[:,None];target=(np.c_[Q,np.ones(len(Q))]@bi.T)[:,:3];key=ob.shape_key_add(name='AFN146_'+side+'_LAMELLAR_%02d'%k);key.relative_key=basis;key.data.foreach_set('co',target.astype('f4').ravel());d=key.driver_add('value').driver;d.type='SCRIPTED';v=d.variables.new();v.name='blink';v.type='SINGLE_PROP';v.targets[0].id=rig;v.targets[0].data_path='["'+PROPS[side]+'"]';d.expression='max(0.0,1.0-abs(blink*8.0-%d.0))'%k;entries.append({'side':side,'alpha':alpha,'key':key.name,'activePoints':len(ids)})
        shapes[name]=entries
    checks=[]
    for f in range(1,18):
        scene.frame_set(f);rig.update_tag();bpy.context.view_layer.update();Wnow,Tnow=a.geometry(skin);area=np.linalg.norm(np.cross(Wnow[Tnow[:,1]]-Wnow[Tnow[:,0]],Wnow[Tnow[:,2]]-Wnow[Tnow[:,0]]),axis=1);row={'frame':f,'actualControls':{s:float(rig[p]) for s,p in PROPS.items()},'actualSkinZeroAreaTriangles':int((area==0).sum()),'actualSkinMinimumTwiceAreaM2':float(area.min()),'allActualSkinFinite':bool(np.isfinite(Wnow).all())};checks.append(row);save('actual-before-save-connected-lining-poses.json',checks);assert row['allActualSkinFinite'] and row['actualSkinZeroAreaTriangles']==0,('Authored actual moving lining degenerates before any source save',row)
    scene.frame_set(1);rig.update_tag();bpy.context.view_layer.update();returned=a.geometry(skin)[0];assert np.linalg.norm(returned[:len(keepIds)]-W[keepIds],axis=1).max()<2e-6 and a.a.protected()==protected
    for name in otherRaw:assert a.rawsig(bpy.data.objects[name])==otherRaw[name] and np.linalg.norm(a.geometry(bpy.data.objects[name])[0]-otherWorld[name],axis=1).max()<2e-6
    rig['AFN146_scope']='Actual connected posterior lining, shared true-aperture closure boundary and native editable lamellar morphs. Source aspherical construction is not contact proof. Unaccepted until complete matched head/body, independent operation/restoration and actual lining/ocular/contact checks. No full physiological/finite/self/continuous/runtime acceptance.';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=False)
    np.savez_compressed(E/'connected-skin-lineage.npz',retainedOriginalSkinIds=keepIds,originalId=originalId,oldToNew=oldToNew,replacedOriginalPolygons=np.array(sorted(removed)),newSkinWorld=newW,newSkinTriangles=newT,liningFaceSide=np.array(faceRoles),leftAngles=angleFields['L'],rightAngles=angleFields['R'])
    save('connected-palpebral-lining-construction.json',{'source':str(SRC),'actualSkin':skin.name,'actualRig':rig.name,'actualControllers':PROPS,'originalSkinVertices':len(W),'retainedOriginalOuterVertices':len(keepIds),'newSkinVertices':len(world),'newSkinTriangles':len(newT),'replacedOldLiningPolygons':sorted(removed),'originalOuterUVAndMaterialSlotsPreserved':True,'retainedOriginalVertexWeightsExact':True,'originalCustomCornerNormalsCopied':oldNormals is not None,'copiedOriginalPointAttributes':copiedAttributes,'unmappedOriginalAttributes':unmapped,'newLiningMaterial':lining.name,'newLiningMaterialOnlyOnActualNewPosteriorFaces':True,'originalOuterFaceBodySkinMaterialsExposureNotDarkened':True,'explicitBoundaryAndLining':patchReports,'nativeShapes':shapes,'actualAttachments':attachmentReports,'preSave17ActualSkinPoseChecks':checks,'scope':'Whole original lining domains replaced with connected covered patches. No omitted failed faces/external cap/eye scaling/extra clearance/tolerance relaxation. Native morphs use actual source cavity plus original radial gap; no collision/complete operation adoption inferred.','secondsBeforePreview':time.time()-tick})
    save('a-build-summary.json',{'source':str(SRC),'comparisonBaseline':str(c.SRC),'output':str(OUT),'sha256':a.a.sha(OUT),'bytes':OUT.stat().st_size,'actualSkin':skin.name,'actualRig':rig.name,'actualControllers':PROPS,'originalGazeAction':'AFN138_NATIVE_CURRENT_GAZE_DEMO','newBlinkDemoAction':'AFN144_ACTUAL_CURRENT_SKIN_BLINK_DEMO','oneCompleteCandidate':True,'completeAppearanceOperationContactRuntimeUnaccepted':True,'secondsBeforePreview':time.time()-tick});views=[]
    for v in ['face','body-face','profile','oblique','back']:views.append(a.b.u.v.image('a-connected-palpebral-lining',v));save('a-view-controls.json',views)
    motion=[]
    for f in [5,9,13,17]:
        scene.frame_set(f);bpy.context.view_layer.update()
        for v in ['face','body-face']:
            row=a.b.u.v.image('blink-%03d'%f,v);row['actualBlink']={s:float(rig[p]) for s,p in PROPS.items()};motion.append(row);save('actual-blink-motion-controls.json',motion)
    scene.frame_set(9);bpy.context.view_layer.update();save('actual-closed-profile-control.json',a.b.u.v.image('closed-blink','profile'));scene.frame_set(1);bpy.context.view_layer.update();assert a.a.protected()==protected;print('R146_CONNECTED_ACTUAL_LINING_COMPLETE_HEAD_BODY_BLINK_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
