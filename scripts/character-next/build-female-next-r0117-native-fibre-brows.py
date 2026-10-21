"""One2140-fibre authoring pass from native brow shape/flow and actual forehead ancestry."""
from pathlib import Path
import bpy,numpy as np,json,time,datetime,hashlib,os,importlib.util
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0117-native-fibre-brows';D=R/'Reference/character/makehuman-core-cc0/system-brows';SRC=S/'r0115-source/aevrynd-female-next-r0115-b-continuous-native-neutral.blend';OUT=S/'r0117-source/aevrynd-female-next-r0117-a-native-fibre-brows.blend'
sp=importlib.util.spec_from_file_location('r117base',Path(__file__).with_name('build-female-next-r0116-native-eye-character.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);b=a.b;q=a.q;b.u.v.E=E
def save(n,o):(E/n).write_text(json.dumps(o,indent=2,default=lambda x:x.tolist() if isinstance(x,np.ndarray) else x.item())+'\n',encoding='utf-8',newline='\n')
def protected():
    x=a.protected();x['allOriginalFibres'].pop('AFN57_NATIVE_BROWS');return x
def graph(mesh):return np.r_[q.arr(mesh.polygons,'loop_total',len(mesh.polygons),dtype='i4'),q.arr(mesh.loops,'vertex_index',len(mesh.loops),dtype='i4')]
def box(x,r=3):
    z=np.pad(x,((r,r),(r,r)),mode='edge');z=np.pad(z,((1,0),(1,0)));v=z.cumsum(0).cumsum(1);k=2*r+1;return (v[k:,k:]-v[:-k,k:]-v[k:,:-k]+v[:-k,:-k])/(k*k)
def main():
    tick=time.time();assert not OUT.exists();save('fibre-character-authoring-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'action':'Directly reconstruct all2140 brow fibres using inspected native eyebrow001 shape/texture flow, original radii, actual evaluated forehead surface and source parent-face lineage. No generic source-head mask or nearest fallback.'});digest=a.sha(SRC);bpy.ops.wm.open_mainfile(filepath=str(SRC));b.deliver(0);before=protected();skin=bpy.data.objects['AFN113_COMPLETE_WOMAN_COHERENT_HEAD'];raw=bpy.data.objects['AFN115_EDITABLE_CONNECTED_NATIVE_ADULT_SOURCE'];ob=bpy.data.objects['AFN57_NATIVE_BROWS'];data=ob.data;counts=np.array([c.points_length for c in data.curves],dtype='i4');starts=np.r_[0,np.cumsum(counts)[:-1]];oldWorld=q.hair(ob).copy();radii=q.arr(data.attributes['radius'].data,'value',len(oldWorld)).copy();assert len(counts)==2140 and len(radii)==len(oldWorld)
    # Propagate actual coarse FACE IDs through the exact same subdivision that
    # produced the displayed native skin. Graph identity, not coordinate guesses.
    tag='AFN117_NATIVE_PARENT_FACE';at=raw.data.attributes.get(tag) or raw.data.attributes.new(name=tag,type='INT',domain='FACE');at.data.foreach_set('value',np.arange(len(raw.data.polygons),dtype='i4'));raw.hide_set(False);raw.hide_render=True;raw.data.update();raw.data.update_tag();raw.update_tag();bpy.context.view_layer.update();rd=raw.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;assert np.array_equal(graph(rd),graph(skin.data));parent=q.arr(rd.attributes[tag].data,'value',len(rd.polygons),dtype='i4').copy();at=skin.data.attributes.get(tag) or skin.data.attributes.new(name=tag,type='INT',domain='FACE');at.data.foreach_set('value',parent)
    raw.data.calc_loop_triangles();RT=q.arr(raw.data.loop_triangles,'vertices',len(raw.data.loop_triangles),3,dtype='i4');RV=q.arr(raw.data.vertices,'co',len(raw.data.vertices),3).astype('f8');RN=np.zeros_like(RV);fn=np.cross(RV[RT[:,1]]-RV[RT[:,0]],RV[RT[:,2]]-RV[RT[:,0]]);np.add.at(RN,RT.ravel(),np.repeat(fn,3,axis=0));RN/=np.maximum(np.linalg.norm(RN,axis=1),1e-30)[:,None]
    line=np.load(E/'native-brow-source-lineage.npz');PW=line['actualNativeWorld'];UV=line['sourceUV'];F=line['sourceFaces'];FU=line['sourceFaceUV'];parents=line['nativeBodyParentVertexIDs'];weights=line['nativeBodyParentWeights'];assert parents.max()<len(RV);RA=np.array(raw.matrix_world);normals=(RN[parents]*weights[:,:,None]).sum(1)@np.linalg.inv(RA[:3,:3]);normals/=np.maximum(np.linalg.norm(normals,axis=1),1e-30)[:,None];sourceParentSet=np.unique(parents);rawLoops=q.arr(raw.data.loops,'vertex_index',len(raw.data.loops),dtype='i4');rawCounts=q.arr(raw.data.polygons,'loop_total',len(raw.data.polygons),dtype='i4');rawStarts=q.arr(raw.data.polygons,'loop_start',len(raw.data.polygons),dtype='i4');incident=np.array([i for i,(st,n) in enumerate(zip(rawStarts,rawCounts)) if np.isin(rawLoops[st:st+n],sourceParentSet).any()],dtype='i4')
    raw.hide_set(True);b.deliver(0);dd,W,T=b.u.b.geom(skin);W=W.copy();T=T.copy();poly=q.arr(dd.loop_triangles,'polygon_index',len(T),dtype='i4');triParent=parent[poly];tree=BVHTree.FromPolygons(W.tolist(),T.tolist(),all_triangles=True,epsilon=0.)
    # Source RGBA structure tensor supplies stroke axes; author only their
    # outward/upward sign. All root/width counts are fixed before preview.
    im=bpy.data.images.load(str(D/'eyebrow001.png'),check_existing=True);width,height=im.size;buf=np.empty(width*height*4,'f4');im.pixels.foreach_get(buf);pix=buf.reshape(height,width,4).astype('f8');gy,gx=np.gradient(pix,axis=(0,1));xx=box((gx*gx).sum(2));xy=box((gx*gy).sum(2));yy=box((gy*gy).sum(2));angle=.5*np.arctan2(2*xy,xx-yy);field=np.stack([-np.sin(angle),np.cos(angle)],axis=2);alpha=pix[:,:,3];trace=xx+yy
    triangles=np.array([[f[0],f[j],f[j+1]] for f in F for j in range(1,len(f)-1)],dtype='i4');tu=np.array([[f[0],f[j],f[j+1]] for f in FU for j in range(1,len(f)-1)],dtype='i4');areas=np.linalg.norm(np.cross(PW[triangles[:,1]]-PW[triangles[:,0]],PW[triangles[:,2]]-PW[triangles[:,0]]),axis=1)*.5;side=np.where(PW[triangles].mean(1)[:,0]>=0,1,-1);rng=np.random.default_rng(117031);HA=np.array(ob.matrix_world);HI=np.linalg.inv(HA[:3,:3]);loc=lambda P:(P-HA[:3,3])@HI.T;VL=loc(W);sv=np.linalg.svd(HA[:3,:3],compute_uv=False);maxScale=float(sv.max());newLocal=np.empty((len(oldWorld),3),'f8');ids=[];barys=[];roots=[];frames=[];records=[];misses=[];directionFallbacks=0;shaftMisses=0;sampleAttempts=0
    for ci,(start,n) in enumerate(zip(starts,counts)):
        sign=1 if oldWorld[start,0]>=0 else -1;choices=np.flatnonzero(side==sign);probs=areas[choices]/areas[choices].sum()
        while True:
            sampleAttempts+=1;assert sampleAttempts<200000,'Original source alpha did not furnish fixed2140 roots.';ti=int(rng.choice(choices,p=probs));x,y=rng.random(2);w=np.array([1-np.sqrt(x),np.sqrt(x)*(1-y),np.sqrt(x)*y]);uv=w@UV[tu[ti]];px=int(np.clip(round(uv[0]*(width-1)),0,width-1));py=int(np.clip(round(uv[1]*(height-1)),0,height-1))
            if rng.random()<alpha[py,px]:break
        desired=w@PW[triangles[ti]];pn=w@normals[triangles[ti]];pn/=np.linalg.norm(pn);hit,no,fi,dist=tree.ray_cast(Vector(desired+pn*.01),Vector(-pn),.03)
        if hit is None:misses.append(ci);continue
        tri=T[fi];parentFace=int(triParent[fi]);assert parentFace in incident,('Native source ancestry mismatch; no fallback',ci,parentFace);hit=np.array(hit);bary=b.u.a.bary(hit,W[tri]);P=VL[tri];t=P[1]-P[0];t/=np.linalg.norm(t);normal=np.cross(P[1]-P[0],P[2]-P[0]);normal/=np.linalg.norm(normal);worldN=np.cross(W[tri[1]]-W[tri[0]],W[tri[2]]-W[tri[0]]);worldN/=np.linalg.norm(worldN);root=bary@P+normal*radii[start];frame=np.array([t,np.cross(normal,t),normal]);duv=field[py,px];u=UV[tu[ti]];U=np.array([u[1]-u[0],u[2]-u[0]]);Dworld=np.array([PW[triangles[ti,1]]-PW[triangles[ti,0]],PW[triangles[ti,2]]-PW[triangles[ti,0]]]);growth=duv@np.linalg.inv(U)@Dworld;growth-=worldN*(growth@worldN)
        if trace[py,px]<1e-12 or np.linalg.norm(growth)<1e-12:growth=np.array([sign,0,.5]);growth-=worldN*(growth@worldN);directionFallbacks+=1
        growth/=np.linalg.norm(growth)
        if growth@np.array([sign,0,.5])<0:growth=-growth
        length=.0032+.0016*rng.random();ss=np.linspace(0,1,int(n));points=[]
        for j,f in enumerate(ss):
            if j==0:points.append(root);continue
            desired=hit+growth*length*f;hp,hn,hfi,hd=tree.ray_cast(Vector(desired+worldN*.01),Vector(-worldN),.03)
            if hp is None:shaftMisses+=1;points.append(root);continue
            tr=T[hfi];nn=np.cross(W[tr[1]]-W[tr[0]],W[tr[2]]-W[tr[0]]);nn/=np.linalg.norm(nn);lift=.00025*np.sin(np.pi*f)+.00008*f;centre=np.array(hp)+nn*(radii[start+j]*maxScale+lift);points.append(loc(centre[None,:])[0])
        newLocal[start:start+n]=points;ids.append(tri);barys.append(bary);roots.append(root);frames.append(frame);records.append({'curve':ci,'sourceShapeTriangle':ti,'sourceBarycentric':w,'sourceUV':uv,'nativeParentFace':parentFace,'actualSkinTriangle':tri,'actualSkinBarycentric':bary,'sourceRayDistanceM':dist,'growthWorld':growth,'authoredLengthM':length})
    save('native-fibre-authoring-checkpoint.json',{'allOriginalCurves':len(counts),'sourceRootSamplingAttempts':sampleAttempts,'rootRayMisses':misses,'shaftRayMisses':shaftMisses,'sourceDirectionFallbacks':directionFallbacks,'nativeParentFaces':incident,'noNearestFallbackUsed':True});assert not misses and shaftMisses==0
    ids=np.array(ids,'i4');frames=np.array(frames);data.attributes['position'].data.foreach_set('vector',newLocal.astype('f4').ravel())
    for j in range(3):data.attributes['AFN97_ScalpVertex'+str(j)].data.foreach_set('value',ids[:,j])
    for name,value in [('RootBarycentric',barys),('RestRoot',roots),('RestT',frames[:,0]),('RestB',frames[:,1]),('RestN',frames[:,2])]:data.attributes['AFN97_'+name].data.foreach_set('vector',np.array(value,'f4').ravel())
    data.attributes['AFN97_RootRadiusNative'].data.foreach_set('value',radii[starts])
    for md in list(ob.modifiers):ob.modifiers.remove(md)
    b.u.root_modifier(ob,skin);data.update_tag();ob.update_tag();b.deliver(0);actual=q.hair(ob);expected=newLocal@HA[:3,:3].T+HA[:3,3];error=float(np.linalg.norm(actual-expected,axis=1).max());assert error<2e-6;assert np.array_equal(q.arr(data.attributes['radius'].data,'value',len(radii)),radii);after=protected();assert before==after
    # Editable original source stays hidden and separate from rendered fibres.
    oldImages={im:im.filepath for im in bpy.data.images};texture=S/'makehuman-native-brow-textures/eyebrow001.png';texture.parent.mkdir(exist_ok=True)
    if not texture.exists():os.link(D/'eyebrow001.png',texture)
    with bpy.data.libraries.load(str(E/'native-brow-source-authoring.blend'),link=False) as (aa,bb):bb.objects=['AFN117_NATIVE_BROW_SHAPE_REFERENCE']
    reference=bb.objects[0];bpy.context.scene.collection.objects.link(reference);reference.hide_render=True;reference.hide_set(True)
    for mat in reference.data.materials:
        for node in mat.node_tree.nodes:
            if node.bl_idname=='ShaderNodeTexImage' and node.image:
                if node.image in oldImages:node.image=node.image.copy()
                node.image.name='AFN117_NATIVE_BROW_REFERENCE_TEXTURE';node.image.filepath='//../makehuman-native-brow-textures/eyebrow001.png'
    for im,path in oldImages.items():assert im.filepath==path
    save('actual-native-brow-bindings.json',records);np.savez_compressed(E/'native-fibre-authoring-lineage.npz',originalWorld=oldWorld,newAuthoredLocal=newLocal,newAuthoredWorld=expected,actualNewWorld=actual,counts=counts,originalRadii=radii,actualRootSkinTriangles=ids,actualRootBarycentric=np.array(barys),nativeParentFaces=incident,actualSkinParentFaceIDs=parent)
    save('a-build-summary.json',{'source':str(SRC),'output':str(OUT),'originalAllCurves':len(counts),'originalAndNewPointCount':len(oldWorld),'allRadiiByteExact':True,'allOriginalFibresRetained':True,'sourceReference':'reference-native-brow-source-3d.png','publisherReference':'reference-publisher-brow001.png','sourceForeheadParentCorrespondence':'native-brow-source-lineage.npz','allRootsHitActualSkinWithVerifiedNativeFaceAncestry':True,'nearestFallbacks':0,'genericHeightMaskNotUsed':True,'actualNewFibreAgainstAuthoredMaxErrorM':error,'beforeProtectedBodyAllKeysHairLashes':before,'afterProtectedBodyAllKeysHairLashes':after,'bodyHairLashAllKeysByteExact':True,'originalBrowMaterialUnchanged':True,'sourceAlphaCardHiddenReferenceOnly':True,'fixedFibreAuthoringChoice':{'lengthM':[.0032,.0048],'surfaceFollowArchM':.00025,'tipLiftM':.00008,'seed':117031,'notParameterSweepOrBiologicalCalibration':True},'browObjectSingularValues':sv,'finiteSweptRenderedOccupancyAndContinuousContactUnaccepted':True,'secondsBeforePreview':time.time()-tick})
    b.deliver(0);bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=False);assert a.sha(SRC)==digest;views=[]
    for view in ['face','body-face','oblique','profile','back']:
        views.append(b.u.v.image('a-native-fibre-brows',view));save('a-view-controls.json',views)
    for label,value in [('half',.5),('closed',1.),('restored',0.)]:
        b.deliver(value);views.append(b.u.v.image('a-native-fibre-brows-'+label,'face'));save('a-view-controls.json',views)
    print('R117_COMPLETE_NATIVE_FIBRE_BROWS_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
