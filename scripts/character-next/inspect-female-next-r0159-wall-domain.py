from pathlib import Path
import bpy,numpy as np,json,importlib.util,collections
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');E=C/'evidence/character-female-next/r0159-native-lid-wall'
sp=importlib.util.spec_from_file_location('r159base',C/'scripts/character-next/build-female-next-r0158-shared-native-skin.py');h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h);a=h.a;h.E=E
b=json.loads((E/'before.json').read_text());bpy.ops.wm.open_mainfile(filepath=b['source']);skin=bpy.data.objects['AFN126_COMPLETE_WOMAN_BODY_AND_ARTIST_HEAD'];rig=bpy.data.objects['AFN138_ACTUAL_CURRENT_GAZE_RIG'];wall=187115;ids=list(skin.data.polygons[wall].vertices);neighbours=[f.index for f in skin.data.polygons if set(f.vertices)&set(ids)];reports=[];arrays={}
for frame in [1,9,11]:
 bpy.context.scene.frame_set(frame);bpy.context.view_layer.update();V,T=a.geometry(skin);eyes={n:a.geometry(bpy.data.objects[n]) for n in a.MOVING};arrays['skin'+str(frame)]=V;arrays['triangles']=T
 reports.append({'frame':frame,'wallVertexIds':ids,'wallVertices':V[ids].tolist(),'adjacentFaces':[{'index':fi,'vertices':list(skin.data.polygons[fi].vertices),'material':skin.data.polygons[fi].material_index} for fi in neighbours],'eyeBounds':{n:{'min':W.min(0).tolist(),'max':W.max(0).tolist(),'center':((W.min(0)+W.max(0))*.5).tolist()} for n,(W,F) in eyes.items()}})
 for n,(W,F) in eyes.items():arrays[n+str(frame)]=W;arrays[n+'triangles']=F
att=[]
for name in a.FIXED[2:4]:
 ob=bpy.data.objects[name];g=next(m.node_group for m in ob.modifiers if m.type=='NODES');tables=[n.inputs['Object'].default_value for n in g.nodes if n.bl_idname=='GeometryNodeObjectInfo'];att.append({'object':name,'sourceObjects':[o.name for o in tables],'attributes':[x.name for o in tables if 'ATTACHMENT' in o.name for x in o.data.attributes]})
h.save('actual-wall-domain.json',{'wall':wall,'materialSlots':[m.name if m else None for m in skin.data.materials],'reports':reports,'attachments':att,'allExistingAttributes':[(x.name,x.domain,x.data_type) for x in skin.data.attributes]});np.savez_compressed(E/'actual-wall-domain.npz',**arrays);print('R159_ACTUAL_FAILED_WALL_DOMAIN_INSPECTED',json.dumps({'wallVertices':ids,'neighbourCount':len(neighbours),'closedWall':reports[-1]['wallVertices']}),flush=True)
