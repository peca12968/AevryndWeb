"""Inspect the actual rendered neck partition, not an old closed-head proxy."""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,time
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0099-continuous-head-neck';S=R/'engine/assets/characters/female-next/source'
sp=importlib.util.spec_from_file_location('r99head',Path(__file__).with_name('build-female-next-r0098-native-head.py'));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);q=m.q
def boundaries(V,T):
 edges=np.sort(np.concatenate([T[:,[0,1]],T[:,[1,2]],T[:,[2,0]]]),axis=1);edges,count=np.unique(edges,axis=0,return_counts=True);B=edges[count==1];adj={}
 for a,b in B:adj.setdefault(int(a),[]).append(int(b));adj.setdefault(int(b),[]).append(int(a))
 remaining=set(adj);out=[]
 while remaining:
  start=min(remaining);todo=[start];comp=set()
  while todo:
   v=todo.pop()
   if v in comp:continue
   comp.add(v);todo.extend(x for x in adj[v] if x not in comp)
  remaining-=comp;ids=np.array(sorted(comp));P=V[ids];out.append({'vertices':len(ids),'degree2':all(len(adj[x])==2 for x in comp),'min':P.min(0).tolist(),'max':P.max(0).tolist(),'mean':P.mean(0).tolist()})
 return out
def main():
 tick=time.time();bpy.ops.wm.open_mainfile(filepath=str(S/'aevrynd-female-next-r0098-b-native-artist-head.blend'));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();out={};arrays={}
 for tag,name in [('skin','AFN74_SKIN_AND_EXISTING_OCULAR_LINING'),('head','AFN98_ORIGINAL_ARTIST_HEAD_AND_NECK_COLLAR')]:
  ob=bpy.data.objects[name];d,V=q.geom(ob);d.calc_loop_triangles();T=q.arr(d.loop_triangles,'vertices',len(d.loop_triangles),3,dtype='i4');loops=q.arr(d.loop_triangles,'loops',len(d.loop_triangles),3,dtype='i4');arrays[tag+'V']=V;arrays[tag+'T']=T;arrays[tag+'Loops']=loops
  arrays[tag+'Material']=np.array([d.polygons[t.polygon_index].material_index for t in d.loop_triangles],'i4')
  for i,uv in enumerate(d.uv_layers):arrays[tag+'UV'+str(i)]=q.arr(uv.data,'uv',len(d.loops),2)
  out[tag]={'vertices':len(V),'triangles':len(T),'boundaries':boundaries(V,T),'uvNames':[x.name for x in d.uv_layers],'modifiers':[(x.name,x.type) for x in ob.modifiers]}
  if tag=='skin':
   a=d.attributes.get('AFN60_NativeFaceID');out[tag]['nativeFaceAttribute']=None if a is None else [a.domain,a.data_type];arrays['skinNativeFace']=q.arr(a.data,'value',len(a.data),dtype='i4') if a else np.array([])
 line=np.load(R/'Evidence/character-female-next/r0098-whole-head-foundation/b-native-head-lineage.npz');headV=arrays['headV'];neck=line['neckHeadVertexIDs'];originalT=line['sourceHeadOriginalTriangles'];upper,_=m.loop_low(headV,originalT);out['rings']={'body':{'count':len(neck),'min':headV[neck].min(0).tolist(),'max':headV[neck].max(0).tolist()},'head':{'count':len(upper),'min':headV[upper].min(0).tolist(),'max':headV[upper].max(0).tolist()}}
 arrays['headUpperLoop']=upper;arrays['headBottomLoop']=neck;np.savez_compressed(E/'actual-interface-input.npz',**arrays);out['seconds']=time.time()-tick;(E/'actual-interface-input.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps(out,indent=2),flush=True)
if __name__=='__main__':main()
