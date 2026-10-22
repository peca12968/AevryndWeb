"""Locate true failed ocular faces in current and pre-cavity artist skin."""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,datetime
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0156-anatomical-blink';E.mkdir(exist_ok=True);old=E.parent/'r0155-native-blink'
s=importlib.util.spec_from_file_location('r156lineage',Path(__file__).with_name('build-female-next-r0155-margin-blink.py'));h=importlib.util.module_from_spec(s);s.loader.exec_module(h);a=h.a
before=json.loads((old/'manifest-before.json').read_text());b=json.loads((old/'b-build-summary.json').read_text());bpy.ops.wm.open_mainfile(filepath=b['output']);scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update();skin=bpy.data.objects[b['actualSkin']];V,T=a.geometry(skin);w=json.loads((old/'b-independent-crossing-location-witness.json').read_text());faces=sorted(set(p['evaluatedSkinTriangle'] for p in w['pairs']));ids=np.unique(T[faces]);rest=V[ids].copy();data=skin.data;data.calc_loop_triangles();rows=[];centers={side:np.array(bpy.data.objects[b['actualRig']].data.bones[name].head_local) for side,name in a.bone_names().items()}
for fi in faces:
 tri=data.loop_triangles[fi];poly=data.polygons[tri.polygon_index];rows.append({'evaluatedTriangle':fi,'rawTriangleVertices':list(tri.vertices),'polygonIndex':tri.polygon_index,'polygonVertexCount':len(poly.vertices),'materialIndex':poly.material_index,'materialName':skin.material_slots[poly.material_index].name,'restWorldTriangle':V[T[fi]].tolist(),'closedWorldTriangle':next(x['skinWorldTriangle'] for x in w['pairs'] if x['evaluatedSkinTriangle']==fi),'localRestNormal':list(poly.normal)})
# Preserved source126 head/body, before native138 cavity Boolean. No source write.
source=R/'engine/assets/characters/female-next/source/r0126-source/aevrynd-female-next-r0126-b-source-section-neck.blend';bpy.ops.wm.open_mainfile(filepath=str(source));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();P,F=a.geometry(bpy.data.objects[b['actualSkin']]);vertexRows=[]
for vi,point in zip(ids,rest):
 ds=np.linalg.norm(P-point,axis=1);nearest=int(ds.argmin());vertexRows.append({'currentVertex':int(vi),'restWorld':point.tolist(),'nearestPreCavityVertex':nearest,'preCavityVertexDistanceM':float(ds[nearest]),'sameSourceCoordinateWithin1e7M':bool(ds[nearest]<1e-7)})
sourceFaces=[]
for row in rows:
 tri=np.array(row['restWorldTriangle']);near=np.array([int(np.linalg.norm(P-p,axis=1).argmin()) for p in tri]);match=np.flatnonzero(np.all(np.sort(F,axis=1)==np.sort(near),axis=1));sourceFaces.append({'currentTriangle':row['evaluatedTriangle'],'preCavityTriangleExactVertexSetMatches':match.tolist(),'allOriginalCoordinatesMatch':bool(max(np.linalg.norm(P[near]-tri,axis=1))<1e-7)})
out={'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'currentSource':b['output'],'preCavitySource':str(source),'failedTriangles':rows,'failedVertices':vertexRows,'exactPreCavityFaceMatches':sourceFaces,'actualEyeCenters':{k:v.tolist() for k,v in centers.items()},'noSourceChanged':True,'anatomicalInterpretationRequiresActualGeometryNotIndexHeuristic':True}
(E/'actual-failed-face-lineage.json').write_bytes((json.dumps(out,indent=2)+'\n').encode());print('R156_ACTUAL_FAILED_FACE_LINEAGE_DONE',json.dumps(out),flush=True)
