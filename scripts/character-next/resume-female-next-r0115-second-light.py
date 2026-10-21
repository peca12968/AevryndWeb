"""Resume only the failed light metadata/render step; completed saved checks are not repeated."""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,hashlib,ast,time
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0115-native-continuous-neck';PRE=E.parent/'r0113-coherent-head-foundation';BASE=S/'aevrynd-female-next-r0113-b-native-neck-skin.blend';OUT=S/'r0115-source/aevrynd-female-next-r0115-b-continuous-native-neutral.blend'
sp=importlib.util.spec_from_file_location('r115second',Path(__file__).with_name('build-female-next-r0113-native-neck-character.py'));b=importlib.util.module_from_spec(sp);sp.loader.exec_module(b)
def save(n,x):(E/n).write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8',newline='\n')
tick=time.time();digest=hashlib.sha256(OUT.read_bytes()).hexdigest()
# Positive control verifies the unchanged broad/narrow path can report an
# actual static crossing; it does not expand the model test's scope.
code=Path(__file__).with_name('verify-female-next-r0037-eye-margin.py');tree=ast.parse(code.read_text(encoding='utf-8'));ns={'np':np};exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in ['inside','intersections']],type_ignores=[]),str(code),'exec'),ns)
ta=np.array([[-.01,-.01,1.3],[.01,-.01,1.3],[0,.01,1.3]]);tb=np.array([[0,-.005,1.29],[0,-.005,1.31],[0,.01,1.3]]);aa=BVHTree.FromPolygons(ta.tolist(),[[0,1,2]],all_triangles=True,epsilon=0.);bb=BVHTree.FromPolygons(tb.tolist(),[[0,1,2]],all_triangles=True,epsilon=0.);pairs=aa.overlap(bb);points=ns['intersections'](ta,tb);assert pairs and points
save('scoped-neck-contact-interpretation.json',{'positiveControlSameBVHEpsilonAndIntersectionRoutine':{'candidatePairs':len(pairs),'intersectionOrTouchPoints':len(points)},'actualModelTest':'scoped-static-neck-contact.json','actualModelNonNeighbourNarrowTests':0,'actualModelObservation':'All emitted distinct pairs share source vertices and were explicitly excluded. This is a broad-phase nonadjacent observation, not a performed global/finite wall/hair/contact proof.','contactGateStatus':'UNACCEPTED_SCOPED_OBSERVATION_ONLY','noToleranceChange':True})
controls=json.loads((PRE/'b-view-controls.json').read_text(encoding='utf-8'))[0];rows=[]
for tag,path in [('baseline',BASE),('candidate',OUT)]:
    bpy.ops.wm.open_mainfile(filepath=str(path));b.deliver(0);scene=bpy.context.scene;scene.camera.matrix_world=Matrix(controls['camera']);scene.camera.data.lens=controls['lensMM'];scene.render.resolution_x=scene.render.resolution_y=640;scene.render.resolution_percentage=100;scene.cycles.samples=16;scene.cycles.seed=controls['seed'];scene.render.hair_subdiv=3;scene.view_settings.exposure=controls['exposure'];scene.view_settings.look=controls['look'];target=Vector((0,-.04,1.43))
    for name,row in controls['lights'].items():
        ob=bpy.data.objects[name];ob.matrix_world=Matrix(row['matrix']);ob.location.x=-ob.location.x;ob.rotation_euler=(target-ob.location).to_track_quat('-Z','Y').to_euler();ob.data.energy=row['energy'];ob.data.color=row['color']
    bpy.context.view_layer.update();scene.render.filepath=str(E/('second-light-'+tag+'-face.png'));lights={o.name:{'matrix':np.array(o.matrix_world).tolist(),'energy':o.data.energy,'color':list(o.data.color)} for o in scene.objects if o.type=='LIGHT'};record={'file':scene.render.filepath,'camera':np.array(scene.camera.matrix_world).tolist(),'lensMM':scene.camera.data.lens,'lights':lights,'exposure':scene.view_settings.exposure,'look':scene.view_settings.look,'samples':16,'resolution':[640,640],'seed':scene.cycles.seed,'hairSubdiv':3,'neutralInput':0.};bpy.ops.render.render(write_still=True);rows.append(record);save('matched-second-light-controls.json',rows)
assert {k:v for k,v in rows[0].items() if k!='file'}=={k:v for k,v in rows[1].items() if k!='file'}
assert hashlib.sha256(OUT.read_bytes()).hexdigest()==digest;print('R115_MATCHED_SECOND_LIGHT_RESUME_DONE',time.time()-tick,flush=True)
