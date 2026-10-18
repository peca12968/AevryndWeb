"""Verify the baked source with factory Blender, without MPFB imports or autoexec."""
import bpy, json, hashlib, math
from pathlib import Path
from collections import Counter
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0005-native-source'
P=R/'engine/assets/characters/female-next/source/aevrynd-female-next-r0005-native-source.blend'
bpy.ops.wm.open_mainfile(filepath=str(P));scene=bpy.context.scene;scene.frame_set(1)
body=bpy.data.objects['AFN_R0005_Body'];rig=bpy.data.objects['AFN_R0005_Rig'];mesh=body.data
dg=bpy.context.evaluated_depsgraph_get();dg.update();ev=body.evaluated_get(dg);m=ev.to_mesh();m.calc_loop_triangles();v=[ev.matrix_world@x.co for x in m.vertices];t=[tuple(x.vertices) for x in m.loop_triangles]
tree=BVHTree.FromPolygons(v,t,all_triangles=True)
pairs=[(a,b) for a,b in tree.overlap(tree) if a<b and set(t[a]).isdisjoint(t[b])]
finite=sum(any(not math.isfinite(c) for c in p) for p in v)
evaluated={'vertices':len(v),'triangles':len(t),'nonAdjacentSelfIntersectionPairs':len(pairs),'samplePairs':[{'triangles':[a,b],'centroids':[list(sum((v[i] for i in t[k]),Vector())/3) for k in (a,b)]} for a,b in pairs[:12]],'nonFiniteVertices':finite}
ev.to_mesh_clear()
weights=[sum(g.weight for g in x.groups) for x in mesh.vertices]
missing=[x.index for x,total in zip(mesh.vertices,weights) if total<1e-6]
deform_names={b.name for b in rig.data.bones if b.use_deform}
invalid_groups=[g.name for g in body.vertex_groups if g.name not in deform_names]
files=[]
for image in bpy.data.images:
 if image.source=='FILE' and not image.packed_file:files.append({'image':image.name,'path':bpy.path.abspath(image.filepath),'exists':Path(bpy.path.abspath(image.filepath)).exists()})
h=max(x.co.z for x in mesh.vertices)-min(x.co.z for x in mesh.vertices);target=(0.,-.02,h*.91);camera=scene.camera;camera.location=(0.,-.82,target[2]+.015);camera.data.lens=100;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();scene.render.resolution_x=scene.render.resolution_y=1100;scene.render.resolution_percentage=100;scene.render.filepath=str(E/'factory-no-addons-face.png');bpy.ops.render.render(write_still=True)
result={'revision':'female-next-r0005','file':str(P),'fileSha256':hashlib.sha256(P.read_bytes()).hexdigest(),'factoryStartup':True,'autoexecDisabled':not bpy.context.preferences.filepaths.use_scripts_auto_execute,'mpfbImportsInVerifier':False,'enabledAddons':list(bpy.context.preferences.addons.keys()),'bodyObjects':[o.name for o in bpy.data.objects if not o.hide_render and o.type=='MESH'],'bakedBodyShapeKeys':0 if not mesh.shape_keys else len(mesh.shape_keys.key_blocks),'bones':len(rig.data.bones),'boneNames':[b.name for b in rig.data.bones],'bodyVertices':len(mesh.vertices),'bodyPolygons':len(mesh.polygons),'allBodyPolygonsQuads':all(len(p.vertices)==4 for p in mesh.polygons),'evaluatedBody':evaluated,'missingDeformWeights':len(missing),'maximumWeightSumError':max(abs(s-1.) for s in weights),'nonBoneWeightGroups':invalid_groups,'externalLibraries':[l.filepath for l in bpy.data.libraries],'externalImages':files,'rigPoseScope':'Neutral only. Walking, running, crouching, expressions, clothing and hair are not yet qualified.','runtimeExportGenerated':False,'enginePerformance':'NOT_TESTED','status':'FOUNDATION_INTEGRITY_REVIEW_ONLY'}
(E/'factory-verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:result[k] for k in ('factoryStartup','autoexecDisabled','enabledAddons','bodyVertices','bodyPolygons','bones','allBodyPolygonsQuads','missingDeformWeights','maximumWeightSumError','externalLibraries','externalImages')},indent=2));print('NATIVE_NEUTRAL_SELF_PAIRS='+str(len(pairs)))
