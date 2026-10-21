"""Direct multi-ring neck surface with native endpoint tangents; same whole woman."""
from pathlib import Path
from collections import defaultdict
import bpy,bmesh,numpy as np,json,time,datetime,importlib.util
from mathutils import Vector
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0114-native-neck-transition';PRE=E.parent/'r0113-coherent-head-foundation';S=R/'engine/assets/characters/female-next/source';SRC=S/'aevrynd-female-next-r0113-b-native-neck-skin.blend';OUT=S/'aevrynd-female-next-r0114-a-native-neck-transition.blend'
sp=importlib.util.spec_from_file_location('r114build',Path(__file__).with_name('build-female-next-r0113-native-neck-character.py'));b=importlib.util.module_from_spec(sp);sp.loader.exec_module(b);q=b.q;b.u.v.E=E
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.item() if isinstance(a,np.generic) else a.tolist())+'\n',encoding='utf8',newline='\n')
def arr3(d):return q.arr(d,'co',len(d),3).copy()
def main():
 tick=time.time();assert not OUT.exists();save('neck-authoring-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'action':'Directly replace one straight bridge by native-tangent multi-ring neck, keeping endpoint coordinates/correspondence and complete woman/own blink/fibres.'});bpy.ops.wm.open_mainfile(filepath=str(SRC));b.deliver(0);ob=bpy.data.objects['AFN113_COMPLETE_WOMAN_COHERENT_HEAD'];mesh=ob.data;original=arr3(mesh.vertices);keys={k.name:arr3(k.data) for k in mesh.shape_keys.key_blocks};d,V,T=b.u.b.geom(ob);V=V.copy();T=T.copy();pf=q.arr(d.loop_triangles,'polygon_index',len(T),dtype='i4');line=np.load(PRE/'whole-head-b-source-correspondence.npz');head=np.zeros(len(V),bool);head[line['sourceHeadToBody']]=True;bridge=np.flatnonzero(np.any(head[T],axis=1)&~np.all(head[T],axis=1));bodyT=T[~np.any(head[T],axis=1)];headT=T[np.all(head[T],axis=1)];bodyLoops=b.oldbuild.loops_from_faces(bodyT);headLoops=b.oldbuild.loops_from_faces(headT);body=min(bodyLoops,key=lambda row:abs(np.mean(V[row,2])-1.31));neck=min(headLoops,key=lambda row:abs(np.mean(V[row,2])-1.345));area=lambda p:np.sum(p[:,0]*np.roll(p[:,1],-1)-np.roll(p[:,0],-1)*p[:,1])
 if area(V[body])*area(V[neck])<0:neck=list(reversed(neck))
 phase=int(np.argmin(np.linalg.norm(V[body]-V[neck[0]],axis=1)));body=body[phase:]+body[:phase]
 def parameter(row):
  P=V[row];length=np.linalg.norm(np.roll(P,-1,axis=0)-P,axis=1);return np.r_[0,np.cumsum(length)/length.sum()]
 bt=parameter(body);ht=parameter(neck);samples=np.unique(np.r_[bt[:-1],ht[:-1]]);N=len(samples)
 # Both original loops and their original phase are kept; union of existing breaks
 # only samples the new interior. No endpoint vertex is moved or resampled away.
 def interpolate(row,param):
  idx=np.searchsorted(param,samples,side='right')-1;idx=np.clip(idx,0,len(row)-1);w=(samples-param[idx])/np.maximum(param[idx+1]-param[idx],1e-30);return V[np.array(row)[idx]]*(1-w[:,None])+V[np.array(row)[(idx+1)%len(row)]]*w[:,None],idx,w
 P0,i0,w0=interpolate(body,bt);P1,i1,w1=interpolate(neck,ht);rawN=np.cross(V[T[:,1]]-V[T[:,0]],V[T[:,2]]-V[T[:,0]]);valid=np.ones(len(T),bool);valid[bridge]=False;VN=np.zeros_like(V)
 for j in range(3):np.add.at(VN,T[valid,j],rawN[valid])
 VN/=np.maximum(np.linalg.norm(VN,axis=1),1e-30)[:,None]
 def cross_tangent(row,param,idx,w,D):
  p=V[row];along=np.roll(p,-1,axis=0)-np.roll(p,1,axis=0);along/=np.maximum(np.linalg.norm(along,axis=1),1e-30)[:,None];n=VN[row];c=np.cross(along,n);c/=np.maximum(np.linalg.norm(c,axis=1),1e-30)[:,None];out=c[idx]*(1-w[:,None])+c[(idx+1)%len(row)]*w[:,None];out/=np.maximum(np.linalg.norm(out,axis=1),1e-30)[:,None];out[np.einsum('ij,ij->i',out,D)<0]*=-1;return out
 D=P1-P0;distance=np.linalg.norm(D,axis=1);C0=cross_tangent(body,bt,i0,w0,D);C1=cross_tangent(neck,ht,i1,w1,D);M0=C0*distance[:,None];M1=C1*distance[:,None];rings=[];ts=np.arange(1,8)/8
 for t in ts:
  rings.append((2*t**3-3*t*t+1)*P0+(t**3-2*t*t+t)*M0+(-2*t**3+3*t*t)*P1+(t**3-t*t)*M1)
 rings=np.array(rings);assert np.isfinite(rings).all();A=np.array(ob.matrix_world);AI=np.linalg.inv(A);local=lambda p:(p-A[:3,3])@AI[:3,:3].T
 hairBefore=q.hair(bpy.data.objects['AFN97_TUCKED_ARTIST_BOB_CHILDREN']).copy();browBefore=q.hair(bpy.data.objects['AFN57_NATIVE_BROWS']).copy();lashBefore=q.hair(bpy.data.objects['AFN57_NATIVE_LASHES']).copy();bm=bmesh.new();bm.from_mesh(mesh);bm.faces.ensure_lookup_table();remove=np.unique(pf[bridge]);bmesh.ops.delete(bm,geom=[bm.faces[int(i)] for i in remove],context='FACES_ONLY');bm.verts.ensure_lookup_table();oldCount=len(bm.verts);shapeLayers=list(bm.verts.layers.shape.values());newRings=[]
 for ring in rings:
  vs=[]
  for p in local(ring):
   v=bm.verts.new(Vector(p))
   for layer in shapeLayers:v[layer]=Vector(p)
   vs.append(v)
  newRings.append(vs)
 bm.verts.index_update();bm.verts.ensure_lookup_table();uvlayers={x.name:bm.loops.layers.uv.get(x.name) for x in mesh.uv_layers};oldLoopUV={name:q.arr(layer.data,'uv',len(mesh.loops),2).copy() for name,layer in [(x.name,x) for x in mesh.uv_layers]};rawLoops=q.arr(mesh.loops,'vertex_index',len(mesh.loops),dtype='i4');uvAt={}
 # Sample the two real surviving interface sides, not the removed bridge chart.
 rawFaceCounts=q.arr(mesh.polygons,'loop_total',len(mesh.polygons),dtype='i4');rawFaceStart=q.arr(mesh.polygons,'loop_start',len(mesh.polygons),dtype='i4');survive=np.ones(len(mesh.polygons),bool);survive[remove]=False
 for name,values in oldLoopUV.items():
  record={}
  for fi in np.flatnonzero(survive):
   start=rawFaceStart[fi];count=rawFaceCounts[fi]
   for li in range(start,start+count):
    vi=int(rawLoops[li])
    if vi in endpointSet:record.setdefault(vi,values[li])
  uvAt[name]=record
 bodyUV={name:np.array([uvAt[name][int(x)] for x in body]) for name in uvlayers};headUV={name:np.array([uvAt[name][int(x)] for x in neck]) for name in uvlayers};uvRing={}
 for name in uvlayers:
  U0=bodyUV[name][i0]*(1-w0[:,None])+bodyUV[name][(i0+1)%len(body)]*w0[:,None];U1=headUV[name][i1]*(1-w1[:,None])+headUV[name][(i1+1)%len(neck)]*w1[:,None];uvRing[name]=np.array([(1-t)*U0+t*U1 for t in ts])
 for ri,row in enumerate(newRings):
  for j,v in enumerate(row):
   for name in uvlayers:pass
 # UV lookup for all old interface and newly authored vertices.
 U={name:dict(uvAt[name]) for name in uvlayers}
 for ri,row in enumerate(newRings):
  for j,v in enumerate(row):
   for name in uvlayers:U[name][v.index]=uvRing[name][ri,j]
 newFaces=[]
 def face(vertices):
  f=bm.faces.new(vertices);f.material_index=8;f.smooth=True;newFaces.append(f)
  for loop in f.loops:
   for name,layer in uvlayers.items():loop[layer].uv=U[name][loop.vert.index]
 def zip_rings(lower,lp,upper,up):
  i=j=0
  while i<len(lower) or j<len(upper):
   a=lower[i%len(lower)];c=upper[j%len(upper)]
   if j==len(upper) or (i<len(lower) and lp[i+1]<=up[j+1]):face([a,c,lower[(i+1)%len(lower)]]);i+=1
   else:face([a,c,upper[(j+1)%len(upper)]]);j+=1
 common=np.r_[samples,1.];zip_rings([bm.verts[int(i)] for i in body],bt,newRings[0],common)
 for low,high in zip(newRings,newRings[1:]):
  for j in range(N):face([low[j],high[j],high[(j+1)%N],low[(j+1)%N]])
 zip_rings(newRings[-1],common,[bm.verts[int(i)] for i in neck],ht);newCount=len(newFaces);bm.to_mesh(mesh);bm.free();mesh.update();ob.data.update_tag();ob.update_tag();b.deliver(0);assert np.array_equal(arr3(mesh.vertices)[:len(original)],original)
 for name,values in keys.items():assert np.array_equal(arr3(mesh.shape_keys.key_blocks[name].data)[:len(values)],values),name
 # Native material blend remains0 in the whole authored neck. Head/body colours
 # and endpoint maps are retained; no darkening or hiding the ledge.
 attr=mesh.attributes['AFN113_NATIVE_COLOR_WEIGHT'];weight=q.arr(attr.data,'value',len(mesh.vertices));assert np.max(abs(weight[oldCount:]))==0
 bpy.context.view_layer.update();gerr=float(np.linalg.norm(q.hair(bpy.data.objects['AFN97_TUCKED_ARTIST_BOB_CHILDREN'])-hairBefore,axis=1).max());berr=float(np.linalg.norm(q.hair(bpy.data.objects['AFN57_NATIVE_BROWS'])-browBefore,axis=1).max());lerr=float(np.linalg.norm(q.hair(bpy.data.objects['AFN57_NATIVE_LASHES'])-lashBefore,axis=1).max());assert max(gerr,berr,lerr)==0
 np.savez_compressed(E/'neck-authoring-lineage.npz',originalBodyLoop=np.array(body),originalHeadLoop=np.array(neck),originalBridgeTriangleIDs=bridge,newWorldRings=rings,ringParameters=ts,circumferenceParameters=samples,endpointBodyWorld=P0,endpointHeadWorld=P1,endpointBodyCrossTangents=C0,endpointHeadCrossTangents=C1,oldVertexCount=np.array(oldCount));save('a-build-summary.json',{'source':str(SRC),'output':str(OUT),'nativeReference':'Original MakeHuman/MPFB CC0 neck/head boundary surface and retained body adjacent triangles, pinned in r113.','construction':'Keep actual endpoint loops/phase; derive cross-boundary tangents from real adjacent surfaces; replace straight strip with one cubic Hermite multi-ring patch and welded zipper end connections.','oldBridgeTriangles':len(bridge),'removedActualPolygons':len(remove),'actualBodyRingVertices':len(body),'actualHeadRingVertices':len(neck),'interiorRings':len(ts),'interiorRingVertices':N,'newVertices':len(mesh.vertices)-oldCount,'newPolygons':newCount,'allOldVertexCoordinatesAndAllOldShapeKeyCoordinatesByteExact':True,'neutralGroomWorldErrorM':gerr,'neutralBrowWorldErrorM':berr,'neutralLashWorldErrorM':lerr,'bodyTangentZRange':[C0[:,2].min(),C0[:,2].max()],'headTangentZRange':[C1[:,2].min(),C1[:,2].max()],'neckWorldZBounds':[rings[:,:,2].min(),rings[:,:,2].max()],'notExactC1FiniteSelfOrCollisionProof':True,'secondsBeforePreview':time.time()-tick})
 bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True);views=[]
 for view in ['face','body-face','profile','back']:views.append(b.u.v.image('a-native-neck-transition',view));save('a-view-controls.json',views)
 motion=[]
 for label,value in [('half',.5),('closed',1.),('restored',0.)]:
  b.deliver(value);views.append(b.u.v.image('a-native-neck-transition-'+label,'face'));motion.append({'state':label,'assignedBlink':value});save('a-preview-motion.json',motion);save('a-view-controls.json',views)
 print('R114_COMPLETE_NATIVE_NECK_TRANSITION_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':
 endpointSet=set()
 # Populated from saved actual diagnostic IDs, not a generic head region.
 z=np.load(E/'actual-neck-interface.npz');endpointSet=set(map(int,np.r_[z['bodyRingVertexIDs'],z['headRingVertexIDs']]))
 main()
