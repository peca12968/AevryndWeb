"""Resume only missing r117 light capture; preserve the first strict-equality failure."""
from pathlib import Path
import bpy,numpy as np,json,time,importlib.util,hashlib
from mathutils import Matrix,Vector
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0117-native-fibre-brows';PRE=E.parent/'r0116-native-compatible-eyes'
sp=importlib.util.spec_from_file_location('r117light',Path(__file__).with_name('build-female-next-r0117-native-fibre-brows.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a)
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 tick=time.time();assert not (E/'second-light-candidate-face.png').exists();v=json.loads((E/'minimum-saved-native-brow-readback.json').read_text('utf-8'));source=Path(v['candidate']['source']);before=digest(source);bpy.ops.wm.open_mainfile(filepath=str(source));a.b.deliver(0)
 # Repeat the actual r116 baseline's construction from its original PRIMARY
 # controls, rather than assigning an already decomposed/recomposed matrix.
 controls=json.loads((PRE/'a-view-controls.json').read_text('utf-8'))[0];expected=json.loads((PRE/'matched-second-light-controls.json').read_text('utf-8'))[0];scene=bpy.context.scene
 scene.camera.matrix_world=Matrix(controls['camera']);scene.camera.data.lens=controls['lensMM'];scene.render.resolution_x=scene.render.resolution_y=640;scene.render.resolution_percentage=100;scene.cycles.samples=16;scene.cycles.seed=controls['seed'];scene.render.hair_subdiv=3;scene.view_settings.exposure=controls['exposure'];scene.view_settings.look=controls['look'];target=Vector((0,-.04,1.43))
 for name,row in controls['lights'].items():
  ob=bpy.data.objects[name];ob.matrix_world=Matrix(row['matrix']);ob.location.x=-ob.location.x;ob.rotation_euler=(target-ob.location).to_track_quat('-Z','Y').to_euler();ob.data.energy=row['energy'];ob.data.color=row['color']
 bpy.context.view_layer.update();scene.render.filepath=str(E/'second-light-candidate-face.png');actual={'file':scene.render.filepath,'camera':np.array(scene.camera.matrix_world).tolist(),'lensMM':scene.camera.data.lens,'lights':{o.name:{'matrix':np.array(o.matrix_world).tolist(),'energy':o.data.energy,'color':list(o.data.color)} for o in scene.objects if o.type=='LIGHT'},'exposure':scene.view_settings.exposure,'look':scene.view_settings.look,'samples':16,'resolution':[640,640],'seed':scene.cycles.seed,'hairSubdiv':3,'neutralInput':0.}
 mismatches={k:{'expected':expected.get(k),'actual':actual.get(k)} for k in set(expected)|set(actual) if k!='file' and expected.get(k)!=actual.get(k)}
 a.save('second-light-resume-controls.json',{'originalFailureLog':'minimum-saved-native-brow-readback.log','reuseCompletedReadback':True,'originalSecondMatrixAssignmentNotRepeated':True,'construction':'Exact original r116 primary-input mirrored-light/target-quaternion construction; no numeric tolerance added.','strictControlMismatches':mismatches,'actualCandidateControls':actual})
 assert not mismatches,mismatches
 bpy.ops.render.render(write_still=True);assert digest(source)==before==v['candidate']['sha256']
 a.save('matched-second-light-controls.json',{'reusedBaseline':expected,'candidate':actual,'baselineSource':str(a.SRC),'baselineSourceSha256':digest(a.SRC),'existingBaselineNotRerendered':True,'controlsStrictlyEqualExceptFilename':True,'seconds':time.time()-tick});print('R117_MATCHED_SECOND_LIGHT_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
