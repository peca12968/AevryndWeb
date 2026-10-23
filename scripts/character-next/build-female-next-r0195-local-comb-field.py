"""One actual connected scalp-owned 3D growth control volume, coarse first.
No section-exit funnel, source groom transplant, scalar flow or cover surface.
Native Geometry Nodes make the control volume drive displayed Curves.
"""
from pathlib import Path
import bpy,numpy as np,json,datetime,time,hashlib,importlib.util
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');E=C/'evidence/character-female-next/r0195-local-growth-domains';OUT=C/'assets-source/aevrynd-character/female-next/r0195-source/aevrynd-female-next-r0195-coarse-local-comb-field.blend'
sp=importlib.util.spec_from_file_location('r195base',C/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;h=m.h
def save(n,x):(E/n).write_bytes((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
def sha(p):return hashlib.file_digest(open(p,'rb'),'sha256').hexdigest()
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def attr(d,n,typ,domain,values,prop):
 z=d.attributes.new(n,typ,domain);z.data.foreach_set(prop,np.asarray(values).ravel());return z
def main():
 tick=time.time();t=json.loads((E/'before.json').read_text());assert not OUT.exists() and sha(t['source'])==t['sourceSha256'];bpy.ops.wm.open_mainfile(filepath=t['source']);s=bpy.context.scene;s.frame_set(1);s.camera.data.type='PERSP';skin=bpy.data.objects['AFN126_COMPLETE_WOMAN_BODY_AND_ARTIST_HEAD'];old=bpy.data.objects['AFN126_ORIGINAL_Hair_Hair_0'];old.material_slots[0].link='DATA';old.hide_render=True;old.hide_set(True)
 for n,hide in [('AFN184_ACTUAL_NATIVE_DEFORMED_LASHES',True),('AFN126_ORIGINAL_Eyelashes_Eyelashes_0',False)]:bpy.data.objects[n].hide_render=hide;bpy.data.objects[n].hide_set(hide)
 bpy.context.view_layer.update();protected={n:a.rawsig(bpy.data.objects[n]) for n in a.FIXED+a.MOVING};W,T=a.geometry(skin);sf=np.load(E.parent/'r0171-actual-scalp-chart/actual-scalp-groom-lineage.npz')['actualScalpFaces'];tri=T[sf];vid=np.unique(tri);V=W[vid];local=np.searchsorted(vid,tri);cross=np.cross(W[tri[:,1]]-W[tri[:,0]],W[tri[:,2]]-W[tri[:,0]]);vn=np.zeros_like(W)
 for j in range(3):np.add.at(vn,tri[:,j],cross)
 normal=vn[vid]/np.maximum(np.linalg.norm(vn[vid],axis=1)[:,None],1e-20);nv=len(vid);K=49;tt=np.linspace(0,1,K)[:,None,None];master=[];diagnostics=[]
 for side in [-1,1]:
  # Author local comb directions on the actual current scalp vertices.
  # Only directions interpolate on actual triangles; no arbitrary neighbouring
  # free-guide positions, foreign rest paths or old whole-head tip template.
  x,y,z=V.T;back=np.clip((y+.025)/.085,0,1);sidewall=np.clip(np.abs(x)/.065,0,1)
  direction=np.column_stack([side*(.95*(1-back)*(1-sidewall)+.12),.12+.65*back*(1-sidewall),-.25-.9*sidewall-.55*back])
  tangent=direction-normal*np.sum(direction*normal,axis=1)[:,None];tangent/=np.maximum(np.linalg.norm(tangent,axis=1)[:,None],1e-12)
  A=np.empty((K,nv,3),'f8');A[0]=V+normal*.00015
  faceTree=BVHTree.FromPolygons(W.tolist(),tri.tolist(),all_triangles=True)
  # Root territories are preserved; the free-length release is per path and
  # comes from its actual encountered scalp boundary, not a global exit plane.
  release=np.full(nv,-1,'i4');distTravel=np.zeros(nv);lastTan=tangent.copy();localFaceChanges=np.zeros(nv,'i4')
  length=.125+.85*np.clip(z-1.43,0,.15);ds=length/(K-1);surface=V.copy();lastFaces=np.full(nv,-1,'i4')
  for k in range(1,K):
   for i in range(nv):
    u=k/(K-1);distTravel[i]+=ds[i]
    if release[i]<0:
     probe=surface[i]+lastTan[i]*ds[i]
     hit,no,fi,gap=faceTree.find_nearest(Vector(probe));B=W[tri[fi]]
     uv=np.linalg.lstsq(np.column_stack([B[1]-B[0],B[2]-B[0]]),np.array(hit)-B[0],rcond=None)[0];bcv=np.clip(np.array([1-uv.sum(),*uv]),0,1);bcv/=bcv.sum()
     tn=bcv@tangent[local[fi]];nn=bcv@normal[local[fi]];nn/=max(np.linalg.norm(nn),1e-12);tn-=nn*np.dot(tn,nn);tn/=max(np.linalg.norm(tn),1e-12)
     if lastFaces[i]>=0 and fi!=lastFaces[i]:localFaceChanges[i]+=1
     lastFaces[i]=fi;surface[i]=np.array(hit)
     # Local rest loft is part of the new construction, never an after-test
     # blanket surface push; all original roots/radii and strands remain.
     loft=.00015+.012*np.sin(min(distTravel[i]/.08,1)*np.pi/2)*(.45+.55*np.clip((V[i,2]-1.44)/.12,0,1))
     if gap>.0025 or hit.z<1.432 or distTravel[i]>.10:
      release[i]=k;lastTan[i]=tn;A[k,i]=A[k-1,i]+tn*ds[i]
     else:
      lastTan[i]=tn;A[k,i]=surface[i]+nn*loft
    else:
     tau=(k-release[i])*ds[i];bend=1-np.exp(-tau/.025)
     free=(1-bend)*lastTan[i]+bend*np.array([side*.08,.03,-1.]);free/=max(np.linalg.norm(free),1e-12)
     # A cut-layer roll follows each root's local cross section, not the
     # previous volume's waves or an interpolated sparse knot table.
     phase=V[i,1]*75+abs(V[i,0])*23;curl=.20*np.sin(tau*85+phase)*min(tau/.04,1)
     free+=np.array([side*curl,.35*curl,0]);free/=max(np.linalg.norm(free),1e-12);A[k,i]=A[k-1,i]+free*ds[i]
  master.append(A)
  diagnostics.append({'branchSide':side,'actualScalpTriangleLocalDirectionInterpolation':True,'actualRootVertices':nv,'releaseLayerQuantiles':np.quantile(release,[0,.5,1]).tolist(),'actualTriangleTransitionsQuantiles':np.quantile(localFaceChanges,[0,.5,1]).tolist(),'localDirectionsAndFullPathsNew':True,'notFiniteSelfContinuousContactProof':True})
 master=np.array(master,'f4');cv=master.reshape(-1,3);baseedges=np.unique(np.sort(np.vstack([local[:,[0,1]],local[:,[1,2]],local[:,[2,0]]]),axis=1),axis=0);edges=[]
 for branch in range(2):
  offset=branch*K*nv
  for k in range(K):edges.append(baseedges+offset+k*nv)
  for k in range(K-1):edges.append(np.column_stack([np.arange(nv)+offset+k*nv,np.arange(nv)+offset+(k+1)*nv]))
 cageMesh=bpy.data.meshes.new('AFN195_COMPLETE_CURRENT_SCALP_3D_CONTROL_VOLUME');cageMesh.from_pydata(cv.tolist(),np.vstack(edges).tolist(),[]);cageMesh.update();cage=bpy.data.objects.new('AFN195_ACTUAL_EDITABLE_GROWTH_VOLUME',cageMesh);s.collection.objects.link(cage);cage.hide_render=True;cage.hide_set(True)
 roots=np.load(E.parent/'r0190-sectional-growth-chart/sectional-growth-lineage.npz');rootTri=roots['rootTriangles'];bc=roots['rootBC'];birth=np.einsum('ni,nij->nj',bc,W[rootTri]);rootLocal=np.searchsorted(vid,rootTri);branch=(birth[:,0]>=0).astype('i4');N=len(birth);indices=np.empty((N,K,3),'i4')
 for j in range(3):indices[:,:,j]=branch[:,None]*K*nv+np.arange(K)[None]*nv+rootLocal[:,j,None]
 expected=np.einsum('ni,nkij->nkj',bc,cv[indices]);cu=bpy.data.hair_curves.new('AFN195_DISPLAYED_NATIVE_VOLUME_DRIVEN_CURVES');cu.add_curves([K]*N);cu.position_data.foreach_set('vector',expected.astype('f4').ravel());attr(cu,'AFN195_PERSISTENT_ROOT_ID','INT','CURVE',np.arange(N,dtype='i4'),'value');rs=np.tile(.00015*np.maximum(1-np.linspace(0,1,K),.03)**.65,N);attr(cu,'radius','FLOAT','POINT',rs.astype('f4'),'value')
 for j in range(3):attr(cu,f'AFN195_VOLUME_I{j}','INT','POINT',indices[:,:,j],'value');attr(cu,f'AFN195_VOLUME_BC{j}','FLOAT','POINT',np.repeat(bc[:,j],K).astype('f4'),'value')
 hair=bpy.data.objects.new('AFN195_ACTUAL_NATIVE_VOLUME_DRIVEN_GROWTH',cu);s.collection.objects.link(hair);g=bpy.data.node_groups.new('AFN195_REAL_CONTROL_VOLUME_TO_DISPLAYED_HAIR','GeometryNodeTree');g.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');g.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry');nodes=g.nodes;links=g.links;ni=nodes.new('NodeGroupInput');no=nodes.new('NodeGroupOutput');obj=nodes.new('GeometryNodeObjectInfo');obj.transform_space='ORIGINAL';obj.inputs['Object'].default_value=cage;pos=nodes.new('GeometryNodeInputPosition');parts=[]
 for j in range(3):
  ix=nodes.new('GeometryNodeInputNamedAttribute');ix.data_type='INT';ix.inputs['Name'].default_value=f'AFN195_VOLUME_I{j}';weight=nodes.new('GeometryNodeInputNamedAttribute');weight.data_type='FLOAT';weight.inputs['Name'].default_value=f'AFN195_VOLUME_BC{j}';sample=nodes.new('GeometryNodeSampleIndex');sample.data_type='FLOAT_VECTOR';sample.domain='POINT';links.new(obj.outputs['Geometry'],sample.inputs['Geometry']);links.new(pos.outputs['Position'],sample.inputs['Value']);links.new(ix.outputs['Attribute'],sample.inputs['Index']);scale=nodes.new('ShaderNodeVectorMath');scale.operation='SCALE';links.new(sample.outputs['Value'],scale.inputs[0]);links.new(weight.outputs['Attribute'],scale.inputs['Scale']);parts.append(scale.outputs['Vector'])
 add=nodes.new('ShaderNodeVectorMath');add.operation='ADD';links.new(parts[0],add.inputs[0]);links.new(parts[1],add.inputs[1]);add2=nodes.new('ShaderNodeVectorMath');add2.operation='ADD';links.new(add.outputs['Vector'],add2.inputs[0]);links.new(parts[2],add2.inputs[1]);setpos=nodes.new('GeometryNodeSetPosition');links.new(ni.outputs[0],setpos.inputs['Geometry']);links.new(add2.outputs['Vector'],setpos.inputs['Position']);links.new(setpos.outputs[0],no.inputs[0]);hair.modifiers.new('AFN195_ACTUAL_FULL_GROWTH_VOLUME_DRIVER','NODES').node_group=g
 mat=bpy.data.materials.new('AFN195_OWN_COARSE_HAIR_SAME_FIXED_MELANIN');mat.use_nodes=True;ns=mat.node_tree.nodes;ns.clear();bs=ns.new('ShaderNodeBsdfHairPrincipled');bs.parametrization='MELANIN';bs.inputs['Melanin'].default_value=.75;bs.inputs['Melanin Redness'].default_value=.15;bs.inputs['Roughness'].default_value=.35;bs.inputs['Radial Roughness'].default_value=.45;out=ns.new('ShaderNodeOutputMaterial');mat.node_tree.links.new(bs.outputs[0],out.inputs[0]);cu.materials.append(mat);bpy.context.view_layer.update();actual,off=m.curveworld(hair);nativeError=float(np.linalg.norm(actual-expected.reshape(-1,3),axis=1).max());assert nativeError<3e-6 and protected=={n:a.rawsig(bpy.data.objects[n]) for n in protected}
 np.savez_compressed(E/'native-growth-volume-lineage.npz',currentScalpFaces=sf,currentScalpVertexIDs=vid,rootTriangles=rootTri,rootBC=bc,rootWorld=birth.astype('f4'),rootBranch=branch,rootLocalTriangle=rootLocal,cageVertexCountPerLayer=nv,layerCount=K,branchCount=2)
 save('coarse-construction-summary.json',{'UTC':stamp(),'actualSkin':skin.name,'actualHair':hair.name,'actualCage':cage.name,'nativeCurves':N,'pointsPerCurve':K,'currentScalpVertices':nv,'actualCageVertices':len(cv),'actualCageEdges':len(cageMesh.edges),'allActualBirthsRetained':True,'newCompleteGuideGeometryNoRetainedFailedFreePaths':True,'actualGeometryNodesDriveMaximumErrorM':nativeError,'currentRootToTipVolumeRepresentation':'Actual per-vertex authored local comb-direction field on current scalp triangles. Each root traces local tangent directions until its encountered scalp boundary and continues in full free space; no sparse guide-position interpolation. Native per-triangle layered control drive reused only; all full rest paths new.','measured3DVolumeCornerDiagnostics':diagnostics,'coarseOnlyNotFinalHairOrCompleteOperationContactProof':True,'sameCoarseRadiusAndMaterialAs190NoOpticsDensitySweep':True,'protectedRawMeshUVSignatures':protected,'secondsBeforePreview':time.time()-tick})
 captures=[]
 def capture(scene):
  captures.append({'UTC':stamp(),'loadedSourceAtCapture':bpy.data.filepath,'plannedSavedCandidate':str(OUT),'output':scene.render.filepath,'frame':scene.frame_current,'camera':scene.camera.name,'cameraMatrixWorld':[list(x) for x in scene.camera.matrix_world],'lens':scene.camera.data.lens,'cameraType':scene.camera.data.type,'viewTransform':scene.view_settings.view_transform,'look':scene.view_settings.look,'exposure':scene.view_settings.exposure,'resolution':[scene.render.resolution_x,scene.render.resolution_y,scene.render.resolution_percentage],'cyclesSamples':scene.cycles.samples,'cyclesSeed':scene.cycles.seed,'actualHair':hair.name,'viewportEvaluatedGeometryPreviouslyCheckedNotRenderDepsgraphProof':True});save('actual-render-pre-capture-states.json',captures)
 bpy.app.handlers.render_pre.append(capture);a.b.u.v.E=E
 hair.hide_render=True;old.hide_render=False
 for view in ['face','body-face']:s.camera.data.type='PERSP';a.b.u.v.image('baseline-original-working-hair',view)
 old.hide_render=True;hair.hide_render=False
 for view in ['face','body-face','oblique','profile','back']:s.camera.data.type='PERSP';a.b.u.v.image('coarse-local-comb-field',view)
 bpy.app.handlers.render_pre.remove(capture);s.camera.matrix_world=Matrix(captures[2]['cameraMatrixWorld']);s.camera.data.lens=captures[2]['lens'];s.camera.data.type='PERSP';OUT.parent.mkdir(parents=True,exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True);save('a-build-summary.json',{'UTC':stamp(),'output':str(OUT),'sha256':sha(OUT),'bytes':OUT.stat().st_size,'actualHair':hair.name,'actualCage':cage.name,'coarseOnly':True,'completeFineCandidates':0,'oneConstructionOneMethod':True,'elapsedJobSeconds':time.time()-tick,'appearanceCompleteOperationContactRuntimeUnaccepted':True});print('R195_ONE_COMPLETE_LOCAL_COMB_FIELD_COARSE_SAVED',flush=True)
if __name__=='__main__':main()
