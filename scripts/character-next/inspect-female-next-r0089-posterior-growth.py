"""Bounded actual posterior root/cap coverage and generation-field inspection."""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util
R=Path(r'D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0089-posterior-growth';S=R/'engine/assets/characters/female-next/source/aevrynd-female-next-r0088-b-supported-lid-aperture.blend'
sp=importlib.util.spec_from_file_location('r89source',R/'scripts/character-next/build-female-next-r0081-editable-curly.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);assert hashlib.sha256(S.read_bytes()).hexdigest()=='72435890a03cab26ff2f3e238060daf2b2cf797f85543d8fd6182583cc1101a7';bpy.ops.wm.open_mainfile(filepath=str(S));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();o=bpy.data.objects['AFN81_EDITABLE_CURLY_GUIDES'];cap=o.data.surface;q=m.q;A=np.array(o.matrix_world);P=q.hair(o);d=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;counts=np.array([c.points_length for c in d.curves]);starts=np.r_[0,np.cumsum(counts)[:-1]];roots=P[starts];native=q.arr(o.data.position_data,'vector',len(o.data.position_data),3);nc=np.array([c.points_length for c in o.data.curves]);ns=np.r_[0,np.cumsum(nc)[:-1]];native=native@A[:3,:3].T+A[:3,3];G=q.arr(cap.data.vertices,'co',len(cap.data.vertices),3);B=np.array(cap.matrix_world);GW=G@B[:3,:3].T+B[:3,3];cap.data.calc_loop_triangles();T=np.array([t.vertices[:] for t in cap.data.loop_triangles]);cent=GW[T].mean(1);area=np.linalg.norm(np.cross(GW[T[:,1]]-GW[T[:,0]],GW[T[:,2]]-GW[T[:,0]]),axis=1)/2;attrs=[]
for at in cap.data.attributes:
 if at.data_type in ('FLOAT','INT','BOOLEAN'):
  values=q.arr(at.data,'value',len(at.data),dtype='f4');attrs.append({'name':at.name,'domain':at.domain,'type':at.data_type,'n':len(values),'range':[float(values.min()),float(values.max())],'quantiles':np.quantile(values,[0,.1,.5,.9,1]).tolist()})
program=next(md.node_group for md in o.modifiers if md.type=='NODES' and md.node_group.name.startswith('AFN81_PUBLISHER_CURLY_PROGRAM'))
def socketvalue(s):
 if not hasattr(s,'default_value'):return None
 a=s.default_value
 if isinstance(a,bpy.types.ID):return a.name
 try:return list(a)
 except TypeError:return a if isinstance(a,(str,float,int,bool)) or a is None else str(a)
nodes=[{'name':n.name,'type':n.bl_idname,'group':n.node_tree.name if n.type=='GROUP' else None,'inputs':[{'name':s.name,'value':socketvalue(s),'links':[[l.from_node.name,l.from_socket.name] for l in s.links]} for s in n.inputs]} for n in program.nodes];grid=[]
for z in np.arange(1.46,1.64,.01):
 row={'z0':float(z),'cells':[]}
 for x in np.arange(-.04,.04,.01):
  rm=(roots[:,1]>.02)&(roots[:,0]>=x)&(roots[:,0]<x+.01)&(roots[:,2]>=z)&(roots[:,2]<z+.01);cm=(cent[:,1]>.02)&(cent[:,0]>=x)&(cent[:,0]<x+.01)&(cent[:,2]>=z)&(cent[:,2]<z+.01);nm=(native[ns,1]>.02)&(native[ns,0]>=x)&(native[ns,0]<x+.01)&(native[ns,2]>=z)&(native[ns,2]<z+.01);row['cells'].append({'x0':float(x),'generatedRoots':int(rm.sum()),'nativeGuideRoots':int(nm.sum()),'capTriangleCentroidAreaM2':float(area[cm].sum())})
 grid.append(row)
result={'source':str(S),'cap':cap.name,'nativeGuides':len(nc),'evaluatedCurves':len(counts),'actualWorldRootBounds':[roots.min(0).tolist(),roots.max(0).tolist()],'capWorldBounds':[GW.min(0).tolist(),GW.max(0).tolist()],'capScalarAttributes':attrs,'program':nodes,'posteriorGrid10mm':grid,'sourceVisibleRadiiWorldQuantilesM':np.quantile(q.arr(d.attributes['radius'].data,'value',len(P))*np.linalg.norm(A[:3,:3],ord=2),[0,.25,.5,.75,.99,1]).tolist(),'meaning':'Root/cap bins and source node links only. Empty projection bins do not by themselves establish a density/mask defect or account for covering free shafts. No contact or exact installed render-depsgraph certificate.'};(E/'actual-posterior-growth.json').write_text(json.dumps(result,indent=2)+'\n');np.savez_compressed(E/'actual-root-cap-map.npz',rootsWorld=roots,nativeGuideWorld=native,nativeGuideCounts=nc,capWorld=GW,capTriangles=T);print('R89_POSTERIOR_ROOT_CAP_INSPECT',len(counts),len(nc),cap.name,flush=True)
