"""Final matched full-character review; private donor data stays private."""
import bpy,importlib.util,json,time
from pathlib import Path
import numpy as np
from mathutils import Vector
sp=importlib.util.spec_from_file_location('a39review',Path(__file__).with_name('build-female-next-r0039-complete-guides.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a)
m=a.m;f=a.f;b=a.b;v=a.v;E=a.E;PVT=E/'private'
def extras(label,folder):
    s=bpy.context.scene;rows=[];lights=[(o,list(o.location),list(o.rotation_euler),list(o.scale)) for o in s.objects if o.type=='LIGHT']
    for view in ('opposite-oblique','alternate-oblique','body-face','back'):
        b.camera('body-face' if view=='body-face' else 'oblique');s.camera.data.lens=85
        if view=='opposite-oblique':s.camera.location.x=-s.camera.location.x;s.camera.rotation_euler=(Vector(b.TARGET)-s.camera.location).to_track_quat('-Z','Y').to_euler()
        if view=='back':s.camera.location=(0,.80,1.47);s.camera.rotation_euler=(Vector(b.TARGET)-s.camera.location).to_track_quat('-Z','Y').to_euler()
        if view=='alternate-oblique':
            for o,loc,rot,scale in lights:o.location.x=-o.location.x;o.rotation_euler=(Vector(b.TARGET)-o.location).to_track_quat('-Z','Y').to_euler()
        bpy.context.view_layer.update();s.render.resolution_x=s.render.resolution_y=800;s.render.filepath=str(folder/f'{label}-{view}.png')
        bpy.ops.render.render(write_still=True);rows.append({'view':view,'camera':b.matrix(s.camera.matrix_world),'lens':85,'stage':v.stage(),'resolution':[800,800]})
        for o,loc,rot,scale in lights:o.location=loc;o.rotation_euler=rot;o.scale=scale
        bpy.context.view_layer.update()
    return rows
def main():
    start=time.time();rows=[]
    for label,path in [('before',a.SRC),('a-after',a.OUT),('b-after',a.S/'aevrynd-female-next-r0039-b-patch-local-locks.blend')]:
        bpy.ops.wm.open_mainfile(filepath=str(path));rows.append({'label':label,'source':str(path),'sourceSha256':b.sha(path),'views':extras(label,E)})
    assert rows[0]['views']==rows[1]['views']==rows[2]['views'];a.save('matched-additional-views.json',{'rows':rows,'matched':True,'scope':'Neutral static complete source body/head only; both own hairstyles rejected.'})
    # Reopen the matched11223fibre private baseline from C0.
    cp=PVT/'aevrynd-female-next-r0039-c-artist-transfer-study.blend';bpy.ops.wm.open_mainfile(filepath=str(cp))
    bpy.data.objects['AFN39_C_PRIVATE_ARTIST_FIBRES'].hide_render=True;bpy.data.objects['AFN39_C_PRIVATE_MATCHED_BEFORE'].hide_render=False
    private_before=extras('c-private-before',PVT)
    source=PVT/'aevrynd-female-next-r0039-c1-surface-transfer-study.blend';proof=json.loads((PVT/'c1-private-build.json').read_text());assert b.sha(source)==proof['outputSha256']
    bpy.ops.wm.open_mainfile(filepath=str(source));o=bpy.data.objects['AFN39_C1_PRIVATE_SURFACE_TRANSFER'];p,r=v.hair_arrays(o);mx=np.array(o.matrix_world);world=p.astype('f8')@mx[:3,:3].T+mx[:3,3]
    V,T=b.evaluated(bpy.data.objects[b.BODY],True);bind=np.load(PVT/'c1-private-surface-transfer.npz');tri=V[T[bind['rootTriangles']]];bc=bind['rootBarycentric']
    assert np.all(bc>=0) and np.max(np.abs(bc.sum(1)-1))<1e-12
    foot=np.einsum('ij,ijk->ik',bc,tri);n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);n/=np.linalg.norm(n,axis=1)[:,None]
    expected=foot+n*.00018;error=np.linalg.norm(world[:,0]-expected,axis=1)
    assert error.max()<1.5e-7
    after=extras('c1-private',PVT);assert private_before==after
    # The private groom is the ONLY intentional geometry change from working
    # source. Original body/eye/lash/brow/skin fields and stage stay exact.
    o.hide_render=True;retained=f.state();bpy.ops.wm.open_mainfile(filepath=str(a.SRC));assert f.state()==retained
    a.save('private-study-summary.json',{'sourceAuthor':'Daniel Bystedt (original Hair Styles demo)','sourcePage':'https://www.blender.org/download/demo-files/','sourceFileSha256':'1ad6202095c1793678fee7d69a7e9f8b5fdb6e5c293d300eb1062d2d437e8d48',
       'rights':'In-file and official page sayCC BY-SA without version; no resolved-version inference or new redistribution grant made. Derived geometry/images/data remain local private study.',
       'C0':{'fibres':11223,'sameCountPrivateBaseline':11223,'representativeFibres':256,'unqualifiedSegments':463,'maxRootRebindM':.022555909723837038},
       'C1':{'path':str(source),'sha256':b.sha(source),'fibres':11223,'representativeFibres':256,'unqualifiedSegments':proof['pilot']['unqualifiedSegments'],'maximumRootRebindM':proof['maximumFinalRootRebindM'],'maximumSurfaceAnchorFitErrorM':proof['maximumAnchorFitErrorM'],'maximumSavedRootBindingReconstructionErrorM':float(error.max())},
       'C2':{'decision':'STOP_OVER12MM_DISPLACEMENT_BUDGET_NO_CORRECTION_APPLIED','requiredMaximumDisplacementM':.027940836093033064,'reason':'Constraint fit needs major complete-path changes; do not silently increase the prior budget or adopt untested geometry.'},
       'originalRawGuides':json.loads((PVT/'raw-guide-contact-cause.json').read_text())['rawGuideAssessment'],
       'appearance':'More natural varied3Dflow, clumps and ends than procedural caps, but still rough/unqualified. This is derivative source research, not an owned accepted character asset.',
       'sourceBodyEyesLashesBrowsSkinStageExact':True,'matchedFullHeadAdditionalLightAndBodyViews':True,'newOverallScore':None,
       'allChildrenBodySelfMotionRuntime':'NOT_QUALIFIED','decision':'PRIVATE_REFERENCE_TRANSFER_RESEARCH_ONLY_NOT_ADOPTED','seconds':time.time()-start})
    print('R39_FINAL_REVIEW_DONE',float(error.max()),time.time()-start,flush=True)
if __name__=='__main__':main()
