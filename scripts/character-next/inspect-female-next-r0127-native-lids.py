"""Inspect actual artist native boundary loops, not an assumed eye aperture."""
from pathlib import Path
import bpy,bmesh,numpy as np,json,datetime
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0127-native-lid-closure';S=R/'engine/assets/characters/female-next/source'
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.tolist() if isinstance(a,np.ndarray) else a.item())+'\n',encoding='utf-8')
def world(ob):return np.array([ob.matrix_world@v.co for v in ob.data.vertices],dtype=float)
def main():
 bpy.ops.wm.open_mainfile(filepath=str(S/'r0126-source/aevrynd-female-next-r0126-b-source-section-neck.blend'))
 ob=bpy.data.objects['AFN126_ORIGINAL_Head_Head_0'];bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7);bm.verts.ensure_lookup_table();bm.verts.index_update();bm.faces.ensure_lookup_table();P=np.array([ob.matrix_world@v.co for v in bm.verts]);edges=np.array([[v.index for v in e.verts] for e in bm.edges]);unseen={v for e in bm.edges if len(e.link_faces)==1 for v in e.verts};loops=[]
 while unseen:
  seed=next(iter(unseen));comp={seed};stack=[seed]
  while stack:
   v=stack.pop()
   for edge in v.link_edges:
    if len(edge.link_faces)!=1:continue
    for w in edge.verts:
     if w not in comp:comp.add(w);stack.append(w)
  unseen-=comp;ids=sorted(v.index for v in comp);W=P[ids];loop={'vertices':len(ids),'ids':ids,'center':W.mean(0),'bounds':[W.min(0),W.max(0)],'allBoundaryDegree2':all(sum(len(e.link_faces)==1 for e in v.link_edges)==2 for v in comp)}
  if loop['allBoundaryDegree2']:
   cur=seed;prev=None;order=[]
   while True:
    order.append(cur.index);nxt=next(w for e in cur.link_edges if len(e.link_faces)==1 for w in e.verts if w!=cur and w!=prev)
    if nxt==seed:break
    prev,cur=cur,nxt
   loop['orderedIds']=order
  loops.append(loop)
 polygons=[[v.index for v in f.verts] for f in bm.faces];tri=[]
 for face in polygons:
  for i in range(1,len(face)-1):tri.append([face[0],face[i],face[i+1]])
 np.savez_compressed(E/'native-head-topology.npz',world=P,edges=edges,triangles=np.array(tri),rawWorld=world(ob))
 parts={}
 for name in ['Eye_Eye_0','EyeScleraReflect_EyeScleraReflect_0','Eyelashes_Eyelashes_0','MeniscusEyeSpec_MeniscusEye_0']:
  o=bpy.data.objects['AFN126_ORIGINAL_'+name];W=world(o);parts[o.name]={'vertices':len(W),'bounds':[W.min(0),W.max(0)],'modifiers':[(x.name,x.type) for x in o.modifiers]};np.savez_compressed(E/(name+'-native.npz'),world=W,edges=np.array([[v for v in e.vertices] for e in o.data.edges]))
 save('native-lid-inspection.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'headUniqueVertices':len(P),'boundaryLoops':loops,'nativeParts':parts,'actualVisibleObject':'AFN126_COMPLETE_WOMAN_BODY_AND_ARTIST_HEAD','scope':'Geometric weld analysis only, actual source/UV and displayed skin untouched. Native eye margins must be identified from actual topology and views; no ellipse or old foreign pose assumptions.'});bm.free();print('R127_NATIVE_LID_INSPECTION_DONE',len(loops),flush=True)
if __name__=='__main__':main()
