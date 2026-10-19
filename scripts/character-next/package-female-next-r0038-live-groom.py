"""Package r38 honestly: keep live-authoring repair; reject both style candidates."""
import json,hashlib,shutil
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(r'D:\Download\Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0038-volume-flow'
REPO=R/'sites-engine-journey';M=REPO/'assets-source/aevrynd-character/female-next'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def font(n):return ImageFont.truetype('C:/Windows/Fonts/msjh.ttc',n)
def layout(name,left,right,titles,views,footer):
    out=Image.new('RGB',(1200,660*len(views)+95),(22,25,30));d=ImageDraw.Draw(out)
    for row,view in enumerate(views):
        for col,(prefix,title) in enumerate(zip((left,right),titles)):
            x=col*600;y=row*660;d.text((x+12,y+8),title,font=font(20),fill='white');d.text((x+12,y+36),view,font=font(16),fill=(185,195,207))
            out.paste(Image.open(E/f'{prefix}-{view}.png').convert('RGB').resize((600,600),Image.Resampling.LANCZOS),(x,y+60))
    d.text((12,660*len(views)+10),footer,font=font(18),fill=(240,207,153))
    d.text((12,660*len(views)+43),'實際 Blender 渲染；固定相機／曝光／光線。未完成自然毛髮、動態與引擎驗收。',font=font(17),fill=(190,200,210))
    out.save(E/name)
def pictures():
    layout('r0038-function-head-comparison.png','before','b-rest',('r37 C／原完整工作人物','r38 B／保留：即時梳理控制'),('face','oblique','profile'),'外觀與原版保持一致；本輪保留功能修復，不提高外觀分數。')
    layout('r0038-a-rejected-head-comparison.png','before','a-after',('原完整工作人物','r38 A／判退：全局流場'),('face','oblique','profile'),'判退：兩側鼓出、同步波紋與髮片感；不升為工作髮型。')
    layout('r0038-c-rejected-head-comparison.png','before','c-after',('原完整工作人物','r38 C／判退：分區導引筆觸'),('face','oblique','profile'),'判退：仍像圓滑髮帽和髮簾，整體可信度沒有足夠改善。')
    layout('r0038-function-additional-comparison.png','before','b-rest',('r37 C／原完整工作人物','r38 B／保留功能；外觀不變'),('opposite-oblique','alternate-oblique','body-face','back'),'完整人物、其他角度與第二種照明；全身僅為來源檢視，非全身驗收。')
    layout('r0038-c-additional-comparison.png','before','c-after',('原完整工作人物','r38 C／已判退研究'),('opposite-oblique','alternate-oblique','body-face','back'),'此候選已判退，完整子髮／自碰撞／動態／引擎未驗收。')
    frames=[]
    for k in range(7):
        canvas=Image.new('RGB',(640,705),(22,25,30));d=ImageDraw.Draw(canvas)
        d.text((12,8),'r38 B｜實際導引編輯示範',font=font(21),fill='white')
        canvas.paste(Image.open(E/f'b-edit-frame-{k:02d}.png').convert('RGB').resize((640,640),Image.Resampling.LANCZOS),(0,38))
        d.text((12,681),'非物理模擬；編輯姿勢接觸未驗收',font=font(16),fill=(240,207,153));frames.append(canvas)
    frames[0].save(E/'r0038-live-guide-edit-demo.gif',save_all=True,append_images=frames[1:],duration=[650,180,180,650,180,180,650],loop=0)
    equality={}
    for view in ('face','oblique','profile','opposite-oblique','alternate-oblique','body-face','back'):
        aa=np.asarray(Image.open(E/f'before-{view}.png').convert('RGBA'))
        bb=np.asarray(Image.open(E/f'b-rest-{view}.png').convert('RGBA'))
        equality[view]={'differentPixels':int(np.any(aa!=bb,axis=2).sum()),'maxChannelDifference':int(np.max(np.abs(aa.astype('i2')-bb.astype('i2'))))}
    save(E/'b-neutral-image-comparison.json',{'views':equality,'scope':'Actual source/rest PNG pixel comparison; no image correction. This is no-regression evidence, not improved realism.'})
    return equality
def main():
    proof=read(E/'b-reopened-verification.json');assert proof['status']=='PASS_REOPENED_LIVE_AUTHORING_REST_EXACT_SCOPE'
    modes=read(E/'b-edit-mode-proof.json');assert modes['modes']['EDIT']['result']==['FINISHED']
    build=read(E/'b-build.json');source=Path(proof['source']);assert sha(source)==proof['sourceSha256']
    previous=Path(proof['baseline']);assert sha(previous)==proof['baselineSha256']
    for lab in ('a','c'):
        report=read(E/(lab+'-build.json'));assert sha(Path(report['output']))==report['outputSha256']
    equality=pictures()
    decision='RETAIN_LIVE_GROOM_AUTHORING_NEUTRAL_REST_EXACT'
    next_action=('Use r38B live-groom-authoring as the ONE complete working female source; r37C is immediate fallback. '
      'Appearance is unchanged. The new native256guide/3neighbor delta modifier preserves all12000 evaluated hairs, roots, radii, types, materials and full body/eye/brow/lash/skin/stage exactly at rest. '
      'Both A global spatial-flow waves and C regional Gaussian guide-offset strokes are visually REJECTED: coherent sheets, inflated wings or rounded cap; do not tune those methods again. '
      'Next production must re-author COMPLETE independent3D guide paths from root to tip on this live basis, with separately planned crown/front/temple/ear/back inner and outer layers and individual free silhouettes; do not just offset the old curtain paths. '
      'Start with a small clearly readable set of absolute guide controls and actual full-head12k preview before expansion; use existing reference-only artist previews for flow observations without copying unresolved-license groom data. '
      'No further tool-only or vendor-search round: live authoring is now available. Reject any cap/sheet/funnel or detached/symmetric wing silhouette. '
      'Retained guide edits require all affected actual displayed full-fibre/body/8optics/eye-tissues/lashes/brows/self checks, not256representatives. '
      'Edited controls do not enforce collisions or deforming scalp attachment. Natural hair dynamics, face/oral/body/clothes rig, continuous contacts, rebuildable engine/LOD/performance and explicit female acceptance remain unqualified. No runtime/website promotion or male work.')
    descriptor={'revision':'female-next-r0038-b','source':str(source),'sourceSha256':sha(source),'baseline':str(previous),'baselineSha256':sha(previous),
      'decision':decision,'appearance':'UNCHANGED_NO_SCORE_INCREASE','authoring':{
      'displayObject':'AFN33_C_BODY_BOUND_FIBRES','editableGuideObject':'AFN38_B_EDIT_SCALP_GUIDES','restObject':'AFN38_B_GUIDE_REST',
      'modifier':'AFN38_LiveEditableGuideDelta','nodeGroup':'AFN38_B_NATIVE_GUIDE_DELTAS','nodes':40,'guideCount':256,
      'guidesPerPart':128,'displayFibres':12000,'pointsPerFibre':128,'neighbors':3,
      'weights':'Nonnegative inverse-squared actual-root distances, normalized, same original scalp part; static authoring weights',
      'equation':'P(c,j)=P_rest(c,j)+sum_k w(c,k)*(G_edit(g(c,k),j)-G_rest(g(c,k),j)); displayed j=0 forced to P_rest(c,0)',
      'cache':'aevrynd-female-next-r0038-b-live-guide-bindings.npz',
      'editModes':modes['modes'],'workflow':'Select AFN38_B_EDIT_SCALP_GUIDES, enter Edit or Sculpt Curves; edit complete guide paths after follicle. Native node graph updates followers live. Modified grooms require revalidation.',
      'limits':['Mode entry is tested, interactive brush ergonomics/performance are not benchmarked','Not a physics solver or collision-safe edit','Not deforming scalp binding or a face/body rig','Own Blender authoring graph/data; engine exporter/runtime port not implemented']},
      'preservedLayers':'All r37C source layers and material/UV/skin data retained; new hidden-for-render guides/rest and one own scalp authoring modifier only.',
      'retainedContactScope':'Only exact unchanged neutral geometry/pose inherits its old version-specific static evidence. Old scalp self/dynamics were not qualified and remain unqualified.',
      'nextAction':next_action}
    save(S/'aevrynd-female-next-r0038-authoring.json',descriptor)
    audit={'revision':'female-next-r0038','workingDecision':decision,'workingSource':str(source),'workingSourceSha256':sha(source),
      'candidateDecisions':{
        'A':{'decision':'VISUALLY_REJECTED_GLOBAL_FLOW','reason':['Large symmetric lateral bulges','Synchronized S-wave yields continuous sheets','No convincing natural full-head hair structure'],'source':read(E/'a-build.json')['output']},
        'B':{'decision':decision,'reason':'Necessary local-authoring blocker repaired; exact neutral whole-character rest and actual guide responsiveness verified. No appearance improvement claimed.'},
        'C':{'decision':'VISUALLY_REJECTED_REGIONAL_OFFSETS','reason':['Round helmet/cap remains','Free hair remains broad curtains rather than natural independent lock structure','Local contour change does not establish a convincing whole-head gain'],'source':read(E/'c-build.json')['output']}},
      'appearance':{'result':'NO_ACCEPTED_APPEARANCE_GAIN','overallCharacterScore':None,'newHairScore':None,'neutralImageEquality':equality,
       'remaining':['Mannequin-like full face and large simple eye catchlights','Rejected thin scalp hairstyle','Natural independently structured full hair and dynamics']},
      'function':{'result':'PASS_REOPENED_NEUTRAL_LIVE_AUTHORING','proof':'b-reopened-verification.json','modeProof':'b-edit-mode-proof.json','singleGuideMovedFollowers':build['controlTest']['affectedFibres'],'rootsFixed':True,'oppositePartUnchanged':True,'formulaErrorM':proof['localDeltaFormulaMaximumPointErrorM']},
      'contact':{'B':'Exact prior neutral rest only; no new self/dynamic qualification','A':read(E/'a-pilot-body-contact.json'),'C':read(E/'c-representative-body-contact.json'),
        'limits':['A/C pilot256fibres only, not full12000children or self proof','Rejected styles did not receive unnecessary complete contact expansion','Authoring demonstration poses are unqualified, not retained grooms','No natural motion/continuous/contact-safe controller claim']},
      'runtime':{'status':'NOT_IMPLEMENTED_NOT_PROMOTED','performance':'NOT_MEASURED','exporter':'NOT_IMPLEMENTED'},
      'femaleAccepted':False,'maleStarted':False,'nextAction':next_action}
    save(E/'female-next-r0038.visual-audit.json',audit)
    research={'primarySources':[
      {'url':'https://research.dreamworks.com/wp-content/uploads/2018/07/a36-somasundaram-Edited.pdf','finding':'Guide interpolation can give artificial sheets; child contacts need independent testing. Read primary talk, no code/data copied.'},
      {'url':'https://www.cemyuksel.com/research/hairmodels/','finding':'Published model terms cover personal/research projects; not selected for engine asset redistribution. No model downloaded.'},
      {'url':'https://huliwenkidkid.github.io/liwenhu.github.io/','finding':'USC-HairSalon is research/non-commercial; not selected. No model downloaded.'},
      {'url':'https://www.cemyuksel.com/research/hairmeshes/','finding':'Author requests contact for using the patented hair-mesh method; not adopted as an engine implementation. No source/model copied.'},
      {'url':'https://github.com/GPUOpen-Effects/TressFX','commit':'ba0bdacdfb964e38522fda812bf23169bc5fa603','finding':'Current repository contains Ratboy short/mohawk fur data, not a suitable adult female groom; no asset downloaded/adopted.'}],
      'alreadyLocalAssets':'Selected4CC0Hair01 meshes and CC0HairEditor already studied/rejected. Not reimported as candidates.',
      'artistNoticeInspection':{'author':'Daniel Bystedt','localFileSha256':'1ad6202095c1793678fee7d69a7e9f8b5fdb6e5c293d300eb1062d2d437e8d48','inFileLicenseNotice':'CC BY-SA license','exactVersion':'UNRESOLVED','adoption':False,'boundary':'Read-only notice/raw inventory; no geometry/node adoption or private inventory/text redistribution.'},
      'api':'Official manual full-page fetches failed. Installed Blender5.2.2RNA and reopened evaluator/mode tests verified own native graph.',
      'newSoftwareInstalled':False}
    save(E/'references-and-rights.json',research)
    manifest_path=S.parent/'female-next.asset.json';manifest=read(manifest_path)
    assert manifest['workingReviewRevision']=='female-next-r0037-c'
    formal={k:manifest.get(k) for k in ('currentSourceRevision','currentSource','sourceSha256','strictOverallScore','strictScoreAppliesTo','runtimeAsset','runtimeStatus','enginePromotionApproved','websitePromotionApproved')}
    manifest.update({'workingReviewRevision':'female-next-r0038-b','workingReviewSource':'source/'+source.name,'workingReviewSha256':sha(source),
      'workingReviewStatus':decision,'workingReviewScope':'r37C complete neutral character retained exactly with own native256guide/3same-part-neighbor live sculpt/edit delta modifier. No appearance increase; no new hairstyle/contact/dynamics/runtime qualification.',
      'workingReviewFallbackBeforeLiveGroom':{'source':str(previous),'sha256':sha(previous)},
      'latestStudyRevision':'female-next-r0038-c','latestStudyStatus':'VISUALLY_REJECTED_REGIONAL_GUIDE_OFFSETS_FUNCTION_B_RETAINED',
      'latestStudyEvidence':str(E/'female-next-r0038.visual-audit.json'),'latestContinuation':str(E/'continuation.json'),
      'newHeadFunctionalReviewSource':'source/'+source.name,'newHeadFunctionalReviewSha256':sha(source),
      'newHeadFunctionalReviewScope':descriptor['preservedLayers']+' Exact neutral/rest live authoring only; old r37ocular contact scope unchanged.',
      'characterAuthoringDescriptorR38':'source/aevrynd-female-next-r0038-authoring.json',
      'liveGroomAuthoringEvidence':str(E/'b-reopened-verification.json'),'liveGroomAuthoringBindings':'source/aevrynd-female-next-r0038-b-live-guide-bindings.npz',
      'rejectedHairStudiesR38':[{'source':read(E/(lab+'-build.json'))['output'],'sha256':read(E/(lab+'-build.json'))['outputSha256'],'decision':audit['candidateDecisions'][lab.upper()]['decision']} for lab in ('a','c')],
      'nextRequiredWork':next_action})
    assert {k:manifest.get(k) for k in formal}==formal
    save(manifest_path,manifest)
    save(E/'continuation.json',{'stage':'B_COMPLETE_HEAD_IN_PROGRESS','lastGoalTurnClassification':'progress',
      'classificationReason':'One integrated neutral complete character gains verified live native guide authoring. Actual A/C full-head styles were produced and visibly rejected; shape methods stopped, no appearance score increase.',
      'previousGoalTurnClassification':'progress: user-requested v9 goal/entry maintenance, not model progress',
      'workingReviewSource':str(source),'workingReviewSha256':sha(source),'workingReviewStatus':decision,
      'immediateFallback':str(previous),'immediateFallbackSha256':sha(previous),'latestEvidence':str(E/'female-next-r0038.visual-audit.json'),
      'liveJobHandles':[],'candidateDecisions':audit['candidateDecisions'],'nextAction':next_action,
      'doNotRepeat':['Autonomous whole-head spatial flow with synchronized wave/bulge','Broad Gaussian regional offsets applied to old curtains','Old fixed-exit/13-16mmloft/funnel/ring/analytic-sheet generation','More tooling or inaccessible vendor-search rounds instead of full guide reauthoring','Density/shader/exposure changes used to conceal failed shape','Claims that256representatives/unchanged neutral rest qualify all edited children/self/motion/runtime'],
      'remainingGates':['Complete believable full-head hair/face','Natural hair dynamics/self and continuous contacts','Eye tear-fluid/optics, blink/gaze and complete facial/oral rig','Full body/clothing/anatomy rig and all specified motions','Rebuildable engine integration, LOD, real CPU/GPU/memory budgets','Weighted85each80 final gates and explicit female acceptance'],
      'overallCharacterScore':None,'resources':{'startUTC':'2026-10-19 11:26:41 UTC','checkpointUTC':'2026-10-19 12:11:41 UTC','heavyJobsAtOnce':1,'blenderThreads':4,'initialFreeGiB':14.12,'peakMemory':'NOT_MEASURED','newNodeServers':0,'remoteJobs':0,'newSoftware':0},
      'history':'Exact-file archive/push verification follows; do not claim pushed before matching remote HEAD.'})
    entries=[]
    def archive(src,dst):
        dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst);assert sha(src)==sha(dst)
        entries.append({'source':str(src),'archive':str(dst),'sha256':sha(dst),'bytes':dst.stat().st_size})
    for name in [source.name,'aevrynd-female-next-r0038-a-root-volume-flow.blend','aevrynd-female-next-r0038-c-regional-guide-sculpt.blend',
      'aevrynd-female-next-r0038-a-pilot.npz','aevrynd-female-next-r0038-b-live-guide-bindings.npz','aevrynd-female-next-r0038-c-guide-edits.npz','aevrynd-female-next-r0038-authoring.json']:
        archive(S/name,M/name)
    for p in sorted((R/'scripts/character-next').glob('*r0038*.py')):archive(p,REPO/'scripts/character-next'/p.name)
    excluded={'original-artist-infile-inventory.json','tressfx-upstream-tree.json','history-file-manifest.json','git-paths.json'}
    for p in sorted(E.iterdir()):
        if p.is_file() and p.suffix in ('.json','.png','.gif') and p.name not in excluded:
            archive(p,M/(p.name if p.name.startswith('r0038-') else 'r0038-'+p.name))
    for lab in ('build','live','verify','regional','supplement'):
        p=R/f'Evidence/character-female-next-r0038-{lab}.log';archive(p,M/f'r0038-{lab}.log')
    archive(manifest_path,M/'female-next.asset.json')
    save(E/'history-file-manifest.json',{'files':entries,'decision':decision,
        'excluded':'Private artist raw text/inventory and artist stdout not redistributed; fullTressFXmetadata tree omitted. Rebuildable21MB A fibre cache remains local: full positions already retained inA.blend. No external PDFs/images/assets added.'})
    archive(E/'history-file-manifest.json',M/'r0038-history-file-manifest.json')
    paths=sorted({str(Path(x['archive']).relative_to(REPO)).replace('\\','/') for x in entries});save(E/'git-paths.json',paths)
    print(json.dumps({'files':len(paths),'bytes':sum(x['bytes'] for x in entries),'working':str(source),'sha256':sha(source),'decision':decision,'imageEquality':equality},indent=2))
if __name__=='__main__':main()
