"""Owned complete-character shadow integration correction, no geometry edits.
Hair remains visible and casts shadows. Light geometry/energy/size, skin/hair
materials, physical hair widths and all actual character layers stay exact.
"""
import bpy,importlib.util,json,time
from pathlib import Path
sp=importlib.util.spec_from_file_location('shadow42i',Path(__file__).with_name('inspect-female-next-r0042-shadow-normal.py'));i=importlib.util.module_from_spec(sp);sp.loader.exec_module(i)
f=i.f;b=i.b;E=i.E;v=i.v;SRC=i.i.SRC;S=b.S
OUT=S/'aevrynd-female-next-r0042-a-jittered-hair-shadows.blend'
def save(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def light(o):
    return {'name':o.name,'type':o.data.type,'matrix':b.matrix(o.matrix_world),'energy':o.data.energy,'color':list(o.data.color),'size':getattr(o.data,'size',None),'sizeY':getattr(o.data,'size_y',None),'shape':getattr(o.data,'shape',None),'shadow':o.data.use_shadow,'jitter':o.data.use_shadow_jitter,'overblur':o.data.shadow_jitter_overblur,'filter':o.data.shadow_filter_radius,'maximumResolution':o.data.shadow_maximum_resolution}

def main():
    start=time.time();assert b.sha(SRC)=='0f8707b92196bc58e158b997a9170f22708d5ddeb2c2e0d95856cbfd00bb4c04';bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;before=f.state();lights=[o for o in s.objects if o.type=='LIGHT'];old=[light(o) for o in lights];cfg=b.config(s)
    save('a-round-contract.json',{'revision':'female-next-r0042-a','source':str(SRC),'sourceSha256':b.sha(SRC),'defect':'False vertical hair-shadow bands over face-side and neck in complete owned character','evidence':'Pigment-only has no neck bands; constant reflectance,zero microbump,andzeroSSS preserve bands; hair-hidden removes them. Geometry/material hypothesis rejected.','method':'Enable area-light shadow jitter ONLY, original64render samples and shadowray/step counts unchanged. Preserve all light geometry,energy,color,size,filter,overblur,resolution,all materials,actual geometry and physical widths. Hair remains visible and shadow-enabled.','expectedVisibleChange':'Replace alias-like neck/face streaks by integrated area-light hair shadow, without facial silhouette or pigment changes','reject':['Bands unchanged or replaced by excessive noise','Loss of meaningful shadow/overblur,head/body appearance regression','Any character/light physical change or geometry-collision inference'],'resource':{'startUTC':'2026-10-19 13:25:07 UTC','checkpointUTC':'2026-10-19 14:10:07 UTC','threads':4,'heavyJobsAtOnce':1},'scope':'Blender EEVEE shadow integration correction only. No new anatomy,hair shape,contact,natural dynamics,engine renderer or performance qualification.'})
    for o in lights:o.data.use_shadow_jitter=True
    f.E=E;f.render('a-after');additional=i.i.ch.review.extras('a-after',E)
    #Only this rendering flag may change. Restore for exact original-state proof.
    new=[light(o) for o in lights]
    for oldrow,newrow in zip(old,new):assert {k:x for k,x in oldrow.items() if k!='jitter'}=={k:x for k,x in newrow.items() if k!='jitter'}
    for o,row in zip(lights,old):o.data.use_shadow_jitter=row['jitter']
    assert f.state()==before and b.config(s)==cfg
    for o in lights:o.data.use_shadow_jitter=True
    b.camera('face');s.camera.data.lens=85;s['AFN42_status']='OWNED_SHADOW_INTEGRATION_REVIEW_NO_GEOMETRY_CHANGE';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    save('a-build-summary.json',{'source':str(SRC),'sourceSha256':b.sha(SRC),'output':str(OUT),'outputSha256':b.sha(OUT),'originalStateExactWhenOnlyJitterRestored':True,'originalLights':old,'newLights':new,'originalRenderConfig':cfg,'matchedAdditionalViews':additional,'allGeometryMaterialsSkinFieldsHairPhysicalWidthsExact':True,'hairVisibleAndShadowsEnabled':True,'onlyIntentionalChange':'3areaLight.use_shadow_jitter=False->True','seconds':time.time()-start,'runtime':'Blender preview only; no engine perf inference','decision':'VISUAL_REVIEW_REQUIRED'})
    print('R42_SHADOW_CANDIDATE_DONE',time.time()-start,flush=True)

if __name__=='__main__':main()
