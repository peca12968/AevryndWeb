"""Observe the independent readback mismatch; no source/model modification."""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,time
sp=importlib.util.spec_from_file_location('r144diag',Path(__file__).with_name('build-female-next-r0144-current-skin-blink.py'));h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h);a=h.a;E=h.E
def polygons(ob):
 ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.data;v=np.empty(len(m.loops),dtype='i4');m.loops.foreach_get('vertex_index',v);counts=np.empty(len(m.polygons),dtype='i4');m.polygons.foreach_get('loop_total',counts);return {'loopVertexHash':a.a.hasharray(v),'faceLoopCountsHash':a.a.hasharray(counts),'polygons':len(m.polygons),'nonTriangles':int((counts!=3).sum())}
def main():
 tick=time.time();b=json.loads((E/'a-build-summary.json').read_text('utf-8'));bpy.ops.wm.open_mainfile(filepath=str(h.SRC));scene=bpy.context.scene;names=[h.h.SKIN]+h.h.ATTACH+a.MOVING;ref={}
 for f in [1,9,25,37,49]:
  scene.frame_set(f);bpy.context.view_layer.update();ref[f]={n:(a.geometry(bpy.data.objects[n]),polygons(bpy.data.objects[n])) for n in names}
 bpy.ops.wm.open_mainfile(filepath=b['output']);rig=bpy.data.objects[b['actualRig']];rig.animation_data.action=bpy.data.actions[b['originalGazeAction']]
 for p in h.PROPS.values():rig[p]=0.
 rig.update_tag();rows=[]
 for f in [1,9,25,37,49]:
  bpy.context.scene.frame_set(f);bpy.context.view_layer.update()
  for n in names:
   W,T=a.geometry(bpy.data.objects[n]);(V,F),poly=ref[f][n];npPoly=polygons(bpy.data.objects[n]);sameShape=W.shape==V.shape;diff=int(np.any(T!=F,axis=1).sum()) if T.shape==F.shape else None
   rows.append({'frame':f,'object':n,'actualBlinkControls':{s:float(rig[p]) for s,p in h.PROPS.items()},'pointCountOriginal':len(V),'pointCountCandidate':len(W),'maxActualVertexDifferenceM':float(np.linalg.norm(W-V,axis=1).max()) if sameShape else None,'evaluatedTriangleRowsDifferent':diff,'originalEvaluatedPolygons':poly,'candidateEvaluatedPolygons':npPoly,'exactUnderlyingEvaluatedPolygonLoopsAndCounts':poly==npPoly})
 h.save('gaze-topology-mismatch-diagnostic.json',{'source':str(h.SRC),'candidate':b['output'],'observations':rows,'modelOrSourceSavedChanged':False,'scope':'Determine exact evaluated polygon topology vs numerical triangulation or actual deformation changes; no changed acceptance/contact/numerical bound.','seconds':time.time()-tick});print('R144_GAZE_TOPOLOGY_MISMATCH_DIAGNOSTIC_DONE',[(x['frame'],x['object'],x['maxActualVertexDifferenceM'],x['evaluatedTriangleRowsDifferent'],x['exactUnderlyingEvaluatedPolygonLoopsAndCounts']) for x in rows],flush=True)
if __name__=='__main__':main()
