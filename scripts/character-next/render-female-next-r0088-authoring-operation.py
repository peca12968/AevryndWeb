"""Actual source-control blink sequence plus one matched alternative light.
Frames are Blender renders, not image warps; no saved source is modified.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
R=Path(r'D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0088-lid-aperture'
sp=importlib.util.spec_from_file_location('r88operation',Path(__file__).with_name('verify-female-next-r0088-lid-aperture.py'));k=importlib.util.module_from_spec(sp);sp.loader.exec_module(k);m=k.m;views=k.k.v;views.E=E
def main():
 tick=time.time();ref=json.loads((E/'b-build-summary.json').read_text());screen=json.loads((E/'b-sampled-blink-contact-screen.json').read_text());assert screen['status']=='NO_STRONG_CROSSING_FOUND_IN_FIVE_TESTED_POSES_STILL_UNACCEPTED';sources=[('baseline-r81',ref['source'],ref['sourceSha256']),('b-supported',ref['output'],ref['outputSha256'])];lighting=[]
 for tag,path,digest in sources:
  assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest;k.prepare(Path(path));lighting.append(views.image(tag,'alternate-oblique'))
 keys=('camera','lights','resolution','samples','seed','exposure','look','hairSubdiv','frame','jawOpen');assert all(lighting[0][a]==lighting[1][a] for a in keys);(E/'b-alternate-light-controls.json').write_text(json.dumps(lighting,indent=2)+'\n')
 k.prepare(Path(ref['output']));s=bpy.context.scene;m.rig.shade.settings();m.rig.k.b.camera('face');s.camera.data.lens=85;s.render.hair_subdiv=3;s.render.resolution_x=s.render.resolution_y=320;s.cycles.samples=8;frames=[]
 for i,value in enumerate((0.,.25,.5,.75,1.,.75,.5,.25,0.)):
  k.controls(value);s.render.filepath=str(E/('b-blink-'+str(i).zfill(2)+'.png'));bpy.ops.render.render(write_still=True);frames.append({'file':s.render.filepath,'sourceSceneFrame':s.frame_current,'blinkLeftRight':value,'sculptEnabled':bpy.data.objects[ref['control']]['sculpt_enabled']});print('R88_ACTUAL_BLINK_RENDER',i,value,flush=True)
 (E/'b-authoring-operation-frames.json').write_text(json.dumps({'source':ref['output'],'sha256':ref['outputSha256'],'frames':frames,'resolution':320,'samples':8,'illustrativeFrameDurationMs':42,'actualSequentialControlEvaluationAndRendering':True,'noImageWarpingOrSavedSourceMutation':True,'noNewSavedTimelineActionClaim':True,'scope':'Manual control exercise of the saved new rest aperture, lash frame follow and source closure/return. Not physiological motion capture or continuous finite contact/physics/runtime proof.','seconds':time.time()-tick},indent=2)+'\n');assert hashlib.sha256(Path(ref['output']).read_bytes()).hexdigest()==ref['outputSha256'];print('R88_AUTHORING_OPERATION_VISUALS_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
