"""Finite shadow integration convergence on the retained owned full model.
No light-size/filter/energy/material/geometry changes. No engine performance
claim. Sample budget changes are explicitly recorded, not disguised as sculpt.
"""
import bpy,importlib.util,time,json
from pathlib import Path
sp=importlib.util.spec_from_file_location('build42a',Path(__file__).with_name('build-female-next-r0042-shadow-integration.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a)
f=a.f;b=a.b;E=a.E;v=a.v
SRC=a.OUT;OUT=b.S/'aevrynd-female-next-r0042-b-shadow-quality-review.blend'

def main():
    start=time.time();bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;original=f.state();cfg=b.config(s);lights=[a.light(o) for o in s.objects if o.type=='LIGHT'];s.eevee.taa_render_samples=256;s.eevee.use_shadow_jitter_viewport=True
    a.save('b-quality-contract.json',{'source':str(SRC),'sha256':b.sha(SRC),'purpose':'Reduce stochastic grain from the same physically sized area-light shadow integration; not a new hairstyle or anatomy','changes':{'taa_render_samples':[64,256],'use_shadow_jitter_viewport':[False,True]},'unchanged':['Light position,color,energy,size,filter,overblur and shadow enable','Shadow ray/step count','All mesh,curve,skin,optical,brow/lash materials','Camera,exposure,color management and pose'],'reject':'Residual banding or no useful noise convergence, excessive runtime or appearance regression','samplesAreBlenderOnly':True,'resources':{'threads':4,'heavyJobsAtOnce':1,'checkpointUTC':'2026-10-19 14:10:07 UTC'}})
    f.E=E;timings=[];renderRows=[]
    for view in ('face','oblique','profile'):
        tick=time.perf_counter();f.render('b-after',(view,));renderRows.extend(json.loads((E/'b-after-renders.json').read_text()));timings.append({'view':view,'wallSeconds':time.perf_counter()-tick,'resolution':[800,800]})
    a.save('b-after-renders.json',renderRows)
    additional=a.i.i.ch.review.extras('b-after',E)
    assert [a.light(o) for o in s.objects if o.type=='LIGHT']==lights
    s.eevee.taa_render_samples=cfg['eevee']['taa_render_samples'];s.eevee.use_shadow_jitter_viewport=cfg['eevee']['use_shadow_jitter_viewport'];assert f.state()==original and b.config(s)==cfg
    s.eevee.taa_render_samples=256;s.eevee.use_shadow_jitter_viewport=True;b.camera('face');s.camera.data.lens=85;s['AFN42_status']='OWNED_COMPLETE_REVIEW_SHADOW_INTEGRATION_FIX_ONLY';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    a.save('b-build-summary.json',{'source':str(SRC),'sourceSha256':b.sha(SRC),'output':str(OUT),'outputSha256':b.sha(OUT),'onlyNewChanges':{'taa_render_samples':256,'use_shadow_jitter_viewport':True},'originalStateExactWhenQualityFlagsRestored':True,'lightPhysicalStateAndMaterialsExact':True,'fullCharacterLayersAndPhysicalHairExact':True,'timingsBlenderPreviewOnly':timings,'matchedAdditionalViews':additional,'seconds':time.time()-start,'decision':'REOPEN_AND_VISUAL_REVIEW_REQUIRED','runtime':'NOT_ENGINE_QUALIFIED'})
    print('R42_B_QUALITY_DONE',time.time()-start,flush=True)

if __name__=='__main__':main()
