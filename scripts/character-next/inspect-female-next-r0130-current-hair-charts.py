"""Inspect the actual current artist hair, original triangle UV charts and packed textures."""
from pathlib import Path
import bpy,numpy as np,json,hashlib,time
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0130-artist-native-groom';S=R/'engine/assets/characters/female-next/source/r0126-source/aevrynd-female-next-r0126-b-source-section-neck.blend'
bpy.ops.wm.open_mainfile(filepath=str(S));o=bpy.data.objects['AFN126_ORIGINAL_Hair_Hair_0'];d=o.data
def arr(c,k,n,w,dt):
 a=np.empty((n,w),dt);c.foreach_get(k,a.ravel());return a
V=arr(d.vertices,'co',len(d.vertices),3,'f4');A=np.array(o.matrix_world);V=V@A[:3,:3].T+A[:3,3];d.calc_loop_triangles();T=arr(d.loop_triangles,'vertices',len(d.loop_triangles),3,'i4');L=arr(d.loop_triangles,'loops',len(d.loop_triangles),3,'i4');uv=arr(d.uv_layers.active.data,'uv',len(d.loops),2,'f4');UV=uv[L];parent=np.arange(len(V),dtype='i4')
def find(i):
 while parent[i]!=i:parent[i]=parent[parent[i]];i=int(parent[i])
 return i
for a,b,c in T:
 x=find(int(a))
 for y in (b,c):
  y=find(int(y))
  if x!=y:parent[y]=x
labels=np.array([find(i) for i in range(len(V))]);ids,count=np.unique(labels,return_counts=True);components=[]
for i,n in zip(ids,count):
 ix=np.where(labels==i)[0];faces=np.where(labels[T[:,0]]==i)[0];components.append({'id':int(i),'vertices':int(n),'faces':len(faces),'bounds':[V[ix].min(0).tolist(),V[ix].max(0).tolist()],'uvBounds':[UV[faces].reshape(-1,2).min(0).tolist(),UV[faces].reshape(-1,2).max(0).tolist()]})
imgs=[];mats=[]
for m in d.materials:
 mats.append({'name':m.name,'nodes':[{'type':n.bl_idname,'image':n.image.name if n.type=='TEX_IMAGE' and n.image else None,'label':n.label} for n in m.node_tree.nodes]})
 for n in m.node_tree.nodes:
  if n.type=='TEX_IMAGE' and n.image and n.image.name not in [x['name'] for x in imgs]:
   im=n.image;row={'name':im.name,'filepath':im.filepath,'size':list(im.size),'channels':im.channels,'packed':bool(im.packed_file)}
   if im.packed_file:
    p=E/('current-hair-original-texture-'+str(len(imgs))+'.png');p.write_bytes(im.packed_file.data);row['savedPackedOriginalBytes']=str(p);row['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
   imgs.append(row)
np.savez_compressed(E/'current-hair-native-triangle-charts.npz',world=V,triangles=T,triangleUV=UV,componentLabels=labels)
(E/'current-hair-chart-inspection.json').write_text(json.dumps({'source':str(S),'object':o.name,'components':components,'componentCount':len(ids),'images':imgs,'materials':mats,'originalSourceNotSaved':True},indent=2)+'\n',encoding='utf-8');print('R130_CURRENT_SOURCE_NATIVE_CHARTS_READ',len(ids),len(T),flush=True)
