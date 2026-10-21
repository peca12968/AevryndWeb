"""Correct a baked closed Basis from the actual original source; preserve failed A separately."""
from pathlib import Path
import bpy,numpy as np,json,hashlib,time,importlib.util,datetime
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0115-native-continuous-neck'
BASE=S/'aevrynd-female-next-r0113-b-native-neck-skin.blend';A=S/'r0115-source/aevrynd-female-next-r0115-a-continuous-native-woman.blend';OUT=A.with_name('aevrynd-female-next-r0115-b-continuous-native-neutral.blend')
sp=importlib.util.spec_from_file_location('r115neutralrepair',Path(__file__).with_name('build-female-next-r0113-native-neck-character.py'));b=importlib.util.module_from_spec(sp);sp.loader.exec_module(b);q=b.q;b.u.v.E=E
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.tolist() if isinstance(a,np.ndarray) else a.item())+'\n',encoding='utf-8',newline='\n')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    tick=time.time();assert not OUT.exists();save('neutral-repair-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'actualFailure':'A neutral differs from actual own original neutral by10.0308mm despite actual driven key values0. Repair original source Basis/keys, not another neck shape method.','originalRoundStartAndDeadlineRetained':True})
    bpy.ops.wm.open_mainfile(filepath=str(BASE));b.deliver(0);oldFibres={n:q.hair(bpy.data.objects[n]).copy() for n in ['AFN97_TUCKED_ARTIST_BOB_CHILDREN','AFN57_NATIVE_BROWS','AFN57_NATIVE_LASHES']};oldHelper=q.geom(bpy.data.objects['AFN59_LASHES_NATIVE_POINT_POSES'])[1].copy();oldRadii={n:q.arr(bpy.data.objects[n].data.attributes['radius'].data,'value',len(bpy.data.objects[n].data.attributes['radius'].data)).copy() for n in oldFibres}
    digest=sha(A);bpy.ops.wm.open_mainfile(filepath=str(A));b.deliver(0);skin=bpy.data.objects['AFN113_COMPLETE_WOMAN_COHERENT_HEAD'];raw=bpy.data.objects['AFN115_EDITABLE_CONNECTED_NATIVE_ADULT_SOURCE'];raw.hide_set(False);raw.hide_render=True;rk=raw.data.shape_keys.key_blocks
    def own(left=0.,right=0.):
        for k in rk:k.value=0.
        rk['AFN115_NATIVE_CLOSED_L'].value=left;rk['AFN115_NATIVE_CLOSED_R'].value=right;raw.data.shape_keys.update_tag();raw.update_tag();bpy.context.view_layer.update();d,V,T=b.u.b.geom(raw);return V.copy(),T.copy()
    neutral,T=own();left,_=own(1.,0.);right,_=own(0.,1.);originalClosed=neutral+(left-neutral)+(right-neutral);own();d,oldBasis,oldT=b.u.b.geom(skin);oldBasis=oldBasis.copy();errorToClosed=float(np.linalg.norm(oldBasis-originalClosed,axis=1).max())
    X=np.array(skin.matrix_world);XI=np.linalg.inv(X[:3,:3]);local=lambda P:(P-X[:3,3])@XI.T;keys=skin.data.shape_keys.key_blocks
    for name,P in [('Basis',neutral),('AFN113_CLOSED_L',left),('AFN113_CLOSED_R',right)]:keys[name].data.foreach_set('co',local(P).astype('f4').ravel())
    skin.data.vertices.foreach_set('co',local(neutral).astype('f4').ravel());skin.data.shape_keys.update_tag();skin.data.update();skin.update_tag();b.deliver(0);d,N,NT=b.u.b.geom(skin);N=N.copy();NT=NT.copy();neutralError=float(np.linalg.norm(N-neutral,axis=1).max());assert neutralError<4e-7
    centre=N[NT].mean(1);headIDs=np.flatnonzero(centre[:,2]>1.39);surface=BVHTree.FromPolygons(N.tolist(),NT[headIDs].tolist(),all_triangles=True,epsilon=0.);fibreRows={}
    for name in ['AFN97_TUCKED_ARTIST_BOB_CHILDREN','AFN57_NATIVE_BROWS']:
        ob=bpy.data.objects[name];data=ob.data;previous=oldFibres[name];counts=np.array([c.points_length for c in data.curves],dtype='i4');starts=np.r_[0,np.cumsum(counts)[:-1]];HA=np.array(ob.matrix_world);HI=np.linalg.inv(HA[:3,:3]);loc=lambda P:(P-HA[:3,3])@HI.T;VL=loc(N);points=loc(previous);newPoints=points.copy();radii=q.arr(data.attributes['radius'].data,'value',len(points));ids=[];weights=[];roots=[];frames=[];changes=[]
        for start,count in zip(starts,counts):
            hit,no,fi,dist=surface.find_nearest(Vector(previous[start]));tri=NT[headIDs[fi]];w=b.u.a.bary(np.array(hit),N[tri]);p=VL[tri];t=p[1]-p[0];t/=np.linalg.norm(t);n=np.cross(p[1]-p[0],p[2]-p[0]);n/=np.linalg.norm(n);root=w@p+n*radii[start];newPoints[start:start+count]+=root-points[start];ids.append(tri);weights.append(w);roots.append(root);frames.append([t,np.cross(n,t),n]);changes.append(np.linalg.norm((root-points[start])@HA[:3,:3].T))
        ids=np.array(ids,dtype='i4');frames=np.array(frames);data.attributes['position'].data.foreach_set('vector',newPoints.astype('f4').ravel())
        for j in range(3):data.attributes['AFN97_ScalpVertex'+str(j)].data.foreach_set('value',ids[:,j])
        for n,val in [('RootBarycentric',weights),('RestRoot',roots),('RestT',frames[:,0]),('RestB',frames[:,1]),('RestN',frames[:,2])]:data.attributes['AFN97_'+n].data.foreach_set('vector',np.array(val,dtype='f4').ravel())
        data.attributes['AFN97_RootRadiusNative'].data.foreach_set('value',radii[starts]);data.update_tag();ob.update_tag();fibreRows[name]={'curves':len(counts),'rootTranslationQuantilesM':np.quantile(changes,[0,.5,.95,1])}
    lash=bpy.data.objects['AFN59_LASHES_NATIVE_POINT_POSES'];LA=np.array(lash.matrix_world);LI=np.linalg.inv(LA[:3,:3]);VL=(N-LA[:3,3])@LI.T;LP=(oldHelper-LA[:3,3])@LI.T;rows=json.loads((E.parent/'r0113-coherent-head-foundation/b-mobile-lash-bindings.json').read_text(encoding='utf-8'));ids=np.empty((len(LP),3),'i4');weights=np.empty_like(LP);offset=np.empty_like(LP);changes=[]
    for row in rows:
        start=row['pointStart'];end=start+row['points'];hit,no,fi,dist=surface.find_nearest(Vector(oldHelper[start]));tri=NT[headIDs[fi]];w=b.u.a.bary(np.array(hit),N[tri]);p=VL[tri];t=p[1]-p[0];t/=np.linalg.norm(t);n=np.cross(p[1]-p[0],p[2]-p[0]);n/=np.linalg.norm(n);frame=np.column_stack((t,np.cross(n,t),n));ids[start:end]=tri;weights[start:end]=w;offset[start:end]=(LP[start:end]-LP[start])@frame;changes.append(dist);row.update(actualR115BTriangle=tri.tolist(),actualR115BBarycentric=w.tolist(),sourceRootReattachmentDistanceM=dist)
    for j in range(3):lash.data.attributes['AFN101_LashVertex'+str(j)].data.foreach_set('value',ids[:,j])
    lash.data.attributes['AFN101_LashBarycentric'].data.foreach_set('vector',weights.astype('f4').ravel());lash.data.attributes['AFN101_LashLocalFrameOffset'].data.foreach_set('vector',offset.astype('f4').ravel());lash.data.update_tag();lash.update_tag();fibreRows['AFN57_NATIVE_LASHES']={'curves':len(rows),'rootTranslationQuantilesM':np.quantile(changes,[0,.5,.95,1])};save('b-actual-lash-rebindings.json',rows)
    raw.hide_set(True);b.deliver(0)
    for name,old in oldFibres.items():
        ob=bpy.data.objects[name];new=q.hair(ob);radii=q.arr(ob.data.attributes['radius'].data,'value',len(oldRadii[name]));assert np.array_equal(radii,oldRadii[name]);fibreRows[name].update(points=len(new),actualWorldAgainstR113BMaxM=float(np.linalg.norm(new-old,axis=1).max()),allRadiiByteExact=True,noFibreDeleted=True)
    b.deliver(0);bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=False);assert sha(A)==digest
    save('b-neutral-repair-summary.json',{'source':str(A),'output':str(OUT),'sourceSha256':sha(OUT),'bytes':OUT.stat().st_size,'AUnchanged':True,'actualABasisAgainstOriginalRawBothClosedMaxErrorM':errorToClosed,'actualBNeutralAgainstOriginalRawNeutralMaxErrorM':neutralError,'actualCompleteVertices':len(N),'actualCompleteTriangles':len(NT),'allFibres':fibreRows,'sameOneConnectedSkinConstructionNoNewNeckShapeMethod':True,'sourceDefaultKeyValuesNotAssumedInRepair':True,'completeAcceptance':False,'secondsBeforePreview':time.time()-tick})
    views=[]
    for view in ['face','body-face','profile','back']:
        views.append(b.u.v.image('b-continuous-native-neutral',view));save('b-view-controls.json',views)
    for label,value in [('half',.5),('closed',1.),('restored',0.)]:
        b.deliver(value);views.append(b.u.v.image('b-continuous-native-neutral-'+label,'face'));save('b-view-controls.json',views)
    print('R115_B_REAL_NATIVE_NEUTRAL_COMPLETE_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
