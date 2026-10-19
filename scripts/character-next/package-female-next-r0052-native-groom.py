"""Archive failed complete native sculpt styles; retain authoring workflow only."""
from pathlib import Path
import json,hashlib,shutil,datetime
from PIL import Image,ImageDraw,ImageFont

R=Path(r'D:\Download\Aevrynd');S=R/'engine/assets/characters/female-next/source'
E=R/'Evidence/character-female-next/r0052-native-groom';PREV=R/'Evidence/character-female-next/r0051-eye-wall'
REPO=R/'sites-engine-journey';M=REPO/'assets-source/aevrynd-character/female-next'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    now=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    mp=R/'engine/assets/characters/female-next/female-next.asset.json';m=read(mp)
    preserved={k:m[k] for k in ['workingReviewRevision','workingReviewSource','workingReviewSha256','workingReviewStatus',
        'currentSourceRevision','currentSource','strictOverallScore','strictScoreAppliesTo','runtimeAsset','runtimeStatus',
        'enginePromotionApproved','websitePromotionApproved']}
    working=S/Path(m['workingReviewSource']).name
    assert m['workingReviewRevision']=='female-next-r0051-b-integrated'
    assert sha(working)==m['workingReviewSha256']=='b86f7eeedf6fd6a4d9a7f13ff42dc4051907516bc90be8261f02e7678242a3ff'
    rows=read(E/'saved-native-readback.json')['rows']+read(E/'b-fixed-saved-native-readback.json')['rows']
    assert [r['tag'] for r in rows]==['a','b','b-fixed']
    for row in rows:
        assert sha(Path(row['source']))==row['sourceSha256']
        assert row['bodyAllOtherMeshesMaterialsFieldsAndStageExact'] and row['nativeRootsRadiiPointCountsCurveTypesExact']
        assert row['nativeVsEvaluatedMaximumM']==0 and row['nativeVsEvaluatedRadiiExact']
    assert rows[-1]['savedUnifiedPaintSettings']['use_unified_size'] is False
    pilots={tag:read(E/name) for tag,name in [('a','native-comb-pilot.json'),('b','b-native-comb-pilot.json'),('b-fixed','b-fixed-native-comb-pilot.json')]}
    assert all(row['status']=='PASS_NATIVE_STROKE_PILOT_STATIC_SCOPE' for row in pilots.values())
    views=['face','oblique','profile','opposite-oblique','alternate-oblique','body-face','back','eyes']
    assert read(PREV/'b-integrated-static-verification.json')['sourceSha256']==sha(working)
    for view in views:shutil.copy2(PREV/f'b-integrated-{view}.png',E/f'before-{view}.png')
    shutil.copy2(PREV/'b-integrated-renders.json',E/'before-renders.json')
    strip=lambda x:[{k:v for k,v in row.items() if k!='path'} for row in x]
    for tag in ['a-after','b-after','b-fixed-after']:
        assert strip(read(E/(tag+'-renders.json')))==strip(read(E/'before-renders.json'))
    font=ImageFont.truetype('C:/Windows/Fonts/msjh.ttc',19);small=ImageFont.truetype('C:/Windows/Fonts/msjh.ttc',17)
    def board(name,columns,chosen,width=600):
        out=Image.new('RGB',(width*len(columns),(width+40)*len(chosen)+108),'#171b20');d=ImageDraw.Draw(out)
        for ri,view in enumerate(chosen):
            for ci,(tag,label) in enumerate(columns):
                d.text((width*ci+9,(width+40)*ri+8),label+' / '+view,font=font,fill='white')
                out.paste(Image.open(E/f'{tag}-{view}.png').convert('RGB').resize((width,width)),(width*ci,(width+40)*ri+38))
        y=(width+40)*len(chosen)
        d.text((10,y+10),'實際完整人物，相同鏡位／光線／曝光／材質；帽殼與片簾仍明顯，原生梳理試驗判退。',font=small,fill='#edc889')
        d.text((10,y+40),'修正版有效筆刷145px、9,767條有變化；髮根／半徑／頭身資料不變，仍不是可採用的外觀改善。',font=small,fill='#d0d3d8')
        d.text((10,y+70),'只有160條代表路徑接觸通過；完整新髮型／自碰撞／動態未驗收，主線仍r51 B。',font=small,fill='#d0d3d8')
        out.save(E/name)
    board('r0052-delivery-comparison.png',[('before','完整工作模型／保留 r51 B'),('b-fixed-after','B 控制修正版／判退')],['face','body-face'])
    board('r0052-angle-comparison.png',[('before','保留 r51 B'),('b-fixed-after','B 控制修正版／判退')],['oblique','profile','back'])
    board('r0052-method-comparison.png',[('a-after','A 局部梳理／判退'),('b-after','B 分區梳理／判退'),('b-fixed-after','B 控制修正／仍判退')],['face','oblique','back'],width=500)
    # Publish interface facts, not a copy of Blender's bundled node graphs.
    interfaces=read(E/'installed-native-interfaces.json')
    write(E/'native-workflow-reference.json',{
        'installedBlender':interfaces['installedBlender'],'bundledLibrarySha256':interfaces['librarySha256'],
        'nodeInterfaceNames':{name:[s['name'] for s in group['sockets']] for name,group in interfaces['groups'].items()},
        'bundledNodeGraphsCopiedToHistory':False,'engineCodeImportedFromBlender':False,
        'primarySource':'https://raw.githubusercontent.com/blender/blender/main/source/blender/editors/sculpt_paint/curves/sculpt_ops.cc',
        'sourceObservation':'Official source registers invoke/modal/cancel, no execute callback for the Curves stroke operator. Installed5.2.2 execution independently demonstrated the same restriction.',
        'workingWorkflow':'One hidden native Blender session, preloaded pinned source, --enable-event-simulate, internal Window.event_simulate with recorded world/view/pixel routes. No OS desktop mouse injection, add-on, new app or service.',
        'fixedImplementationErrors':['Background RegionView3D.update lacks GPU context; do not replay.',
            'Do not reload the main file halfway through a GUI timer context.',
            'Do not invoke the modal-only Curves stroke using EXEC_DEFAULT.',
            'Disable unified size override when honoring explicit Brush.size; independently reopen/read settings.'],
        'privateDonorPolicy':'No donor geometry/images imported or republished. Official demo page was fetched as public HTML and still labels Hair Styles only CC-BY-SA without an exact version link in that card; prior version ambiguity remains unresolved.',
        'demoPage':'https://www.blender.org/download/demo-files/',
        'toolAssetPolicy':'Native Comb is a production tool; B and B-fixed remove the activated Brush datablock before saving baked curve output. No bundled native node asset graphs are distributed.'})
    nextAction=(
        'Keep r51 B integrated as the single complete working character; r52 local Comb and retained-guide-directed '
        'sectional Comb of the existing r33 body-hugging bob fail complete-head realism even after fixing actual '
        'unified brush size. Stop this existing-bob sculpt route as a complete-hairstyle solution; no further '
        'strength/radius/stroke-count/density sweeps and no revived root-frame/radial/world-knot/global-wave methods. '
        'The native modal authoring driver is useful only as a tool for a new foundation, not an accepted groom. '
        'NEXT one production theme: replace the scalp-cover/free-fall bob foundation with an anatomically segmented '
        'new primary groom. First establish actual-skin forehead/temple/ear/nape boundary coverage (r48 initial '
        'mask is incomplete), then author a small full-head set of newly rooted normal-grown native master '
        'curves with explicit length/section controls and sculpt whole root-to-tip flow. Use actual surface/UV '
        'bindings and physical root spacing; root redesign must have anatomical purpose, not hide failed roots. '
        'Use r48 own full-path guides as visual design references, not copied/rotated follower paths. Prove '
        'whole-head silhouette and actual finite guide/body/optical contact before dense children. Validate '
        'all generated paths independently; native point collision is not a full capsule/self/dynamic guarantee. '
        'Prefer one bounded prototype with visible complete-head/body evidence by45minutes; if its large form '
        'is wrong, reject before density and shader detail. Do not import private donor derivatives or call '
        'tool completion a character appearance improvement. Keep r51 ocular repair, body/skin/material/stage '
        'and historical source intact. Full appearance, layered oral/body/clothes rig, existing839nonocular '
        'tested source self pairs, natural hair physics/self/continuous contacts, actual engine/LOD/CPU/GPU/memory, '
        'weighted85each80 and explicit female acceptance remain incomplete.'
    )
    audit={'revision':'female-next-r0052','decision':'REJECT_EXISTING_BOB_NATIVE_SCULPT_RETAIN_AUTHORING_WORKFLOW_ONLY',
        'appearance':{'status':'NO_ADOPTABLE_COMPLETE_CHARACTER_GAIN','appearanceImprovement':False,
            'matchedCompleteHeadBodyAB':True,'multiangleSecondLight':True,
            'A':'Only isolated edge perturbations; cap/sheet structure unchanged.',
            'B_raw':'Broader source-guide-directed edits add local puckers/ridges to the same cap/curtain structure, insufficient complete-head gain.',
            'B_fixed':'Effective radius confirmed145px with override off; still a cap and disconnected curtains, visible lower-side bumps. Reject rather than increasing strength/count.',
            'wholeCharacterScore':None},
        'function':{'status':'NATIVE_AUTHORING_TOOL_PROVED_NOT_COMPLETED_CHARACTER_FEATURE',
            'savedReadbacks':rows,'sourceGuideUsage':'29own existing guide objects supply sectional artist stroke targets; no child path copying/interpolation.',
            'effectiveControlBug':'RawA/B use unified100px even though script sets Brush.size. B-fixed disables override and records actual145px settings. This is one implementation correction, not evidence of realism.'},
        'contact':{'status':'PILOTS_ONLY_FULL_NEW_GROOM_NOT_ACCEPTED',
            'pilots':{tag:{'curves':p['curveCount'],'changedCurves':p['changedCurves'],
                'maximumLocalDisplacementM':p['maximumLocalDisplacementM'],
                'finiteSegments':p['actualFiniteBodyCapsules']['segments'],
                'unqualifiedSegments':p['actualFiniteBodyCapsules']['unqualifiedSegments'],
                'rootFailures':p['actualFiniteBodyCapsules']['rootFailures']} for tag,p in pilots.items()},
            'fullCandidateContactVerification':'Stopped at visual rejection; do not infer12kcurve or self/continuous pass from160curve pilots.',
            'unchangedBody':'Existing r51 ocular repair/body evidence inherited only for identical nonhair geometry; original nonocular failures remain.'},
        'runtime':{'status':'NOT_TESTED_NOT_PROMOTED','cpuGpuMemory':None},
        'stoppedMethod':'Local and sectional native Comb deformation of current scalp-cover/free-fall bob as a route to natural complete hair, including effective-size-corrected version.',
        'usefulResearch':{'purpose':'Native modal artist sculpt, per-curve soft sectional selection, actual brush-control readback, reproducible saved native/evaluated curve data.',
            'scope':'Authoring workflow on complete character, no appearance or dynamics acceptance.',
            'minimumIntegrationStep':'Use the driver on newly rooted normal-grown master curves from a corrected anatomical scalp, inspect full-head form, and independently test full paths before followers; do not apply more strokes to the failed bob.'},
        'nextAction':nextAction}
    write(E/'female-next-r0052.visual-audit.json',audit)
    contract=read(E/'round-contract.json');contract.update(candidateCount=2,
        savedFullSnapshots=3,implementationCorrection='B effective-size snapshot retained separately after evidence of unified100px override; originalA/B preserved.',
        reviewUTC=now,decision=audit['decision']);write(E/'round-contract.json',contract)
    write(E/'continuation.json',{'stage':'B_COMPLETE_HEAD_IN_PROGRESS',
        'previousGoalTurnClassification':'progress: r51 B complete-character ocular repair integrated and pushed28e9b90; no appearance-score gain',
        'lastGoalTurnClassification':'progress','progressKind':'REJECT_TWO_NATIVE_SCULPT_BASES_AND_CONTROL_CORRECTION_WITH_ACTUAL_COMPLETE_VIEWS',
        'classificationReason':'Native modal workflow and independent saved/evaluated data proven; complete local and sectional hair styles and one actual-control repair still visually fail. Stop existing bob foundation and replace master-groom/root architecture.',
        'appearanceImprovement':False,'functionalUnblocking':'Native authoring tool only; no completed new character function or adopted hair.',
        'workingReviewSource':str(working),'workingReviewSha256':sha(working),
        'latestEvidence':str(E/'female-next-r0052.visual-audit.json'),'latestSources':[r['source'] for r in rows],
        'usefulResearch':audit['usefulResearch'],'stoppedMethods':[audit['stoppedMethod']],
        'liveJobHandles':[],'nextAction':nextAction,'wholeCharacterScore':None,
        'resources':{'startUTC':'2026-10-19 17:52:03 UTC','checkpointUTC':'2026-10-19 18:37:03 UTC','reviewUTC':now,
            'blenderThreads':4,'heavyJobsAtOnce':1,'newNodeServers':0,'remoteJobs':0,
            'hiddenNativeBrushSessions':True,'observedMaximumBlenderWorkingSetBytes':2193518592,
            'memoryMeaning':'Sampled process working set, not an instrumented peak or engine memory budget.',
            'goal':'ACTIVE_NOT_COMPLETE'},
        'remainingGates':['Credible full character appearance','Complete layered oral/clothes/body rig','Natural hair/self/continuous dynamics',
            'Existing nonocular source self contacts','Actual Aevrynd runtime/LOD/performance','Weighted85each80 and female acceptance']})
    desc=S/'aevrynd-female-next-r0052-authoring.json'
    write(desc,{'revision':'female-next-r0052','status':audit['decision'],'source':str(working),'sourceSha256':sha(working),
        'snapshots':[{'source':r['source'],'sha256':r['sourceSha256'],'decision':'VISUALLY_REJECTED'} for r in rows],
        'rebuild':'Installed Blender5.2.2 hidden GUI, --factory-startup --enable-event-simulate --disable-autoexec --threads4, pinnedsource51 as startupfile, --python run52native-events.py. No trailingflags=>A160pilot; --full=>Afull; --sectioned=>Bpilot, add--full=>Bfull; --sectioned --effective-settings=>Bfixedpilot, add--full=>Bfixedfull. Eventloop script quits its own session. Do not use the obsolete direct/background execute entrypoint. Reopen with verify52native-readback; --fixed-only forBfixed. Package with bundled Python/Pillow.',
        'workflow':audit['usefulResearch'],'referenceFile':'r0052-native-workflow-reference.json',
        'provenance':'Existing owned authoring/CC0body-texture provenance unchanged. Only native production-tool APIs used; no donor model, third-party node graph, code module, add-on or service imported into engine.',
        'limits':['No adopted appearance/function gain','Only160curve body-contact pilots','Full new hair/self/dynamic/continuous contact unqualified','No runtime/LOD/performance or female acceptance']})
    m.update(latestStudyRevision='female-next-r0052',latestStudyStatus=audit['decision'],
        latestStudyEvidence=str(E/'female-next-r0052.visual-audit.json'),latestContinuation=str(E/'continuation.json'),
        nextRequiredWork=nextAction,characterAuthoringDescriptorR52='source/'+desc.name,
        nativeGroomWorkflowResearchScope='Native modal authoring driver and actual-control readback only. Existing-bob styles visually rejected, no main/runtime promotion.')
    assert all(m[k]==v for k,v in preserved.items());write(mp,m)
    job=read(E/'native-session-job.json');job.update(status='TERMINAL_PROCESS_ABSENT_VERIFIED_BEFORE_PACKAGE',reviewUTC=now)
    write(E/'native-session-terminal.json',job)
    files=[]
    def cp(src,dst):
        dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);assert sha(src)==sha(dst);files.append(dst)
    for r in rows:cp(Path(r['source']),M/Path(r['source']).name)
    cp(desc,M/desc.name);cp(mp,M/'female-next.asset.json')
    reports=['round-contract.json','native-workflow-reference.json','native-sculpt-context.json',
        'native-comb-pilot.json','b-native-comb-pilot.json','b-fixed-native-comb-pilot.json',
        'a-build-summary.json','b-build-summary.json','b-fixed-build-summary.json',
        'saved-native-readback.json','b-fixed-saved-native-readback.json','female-next-r0052.visual-audit.json',
        'continuation.json','native-session-terminal.json']
    for name in reports:cp(E/name,M/('r0052-'+name))
    for name in ('native-comb-pilot.npz','b-native-comb-pilot.npz','b-fixed-native-comb-pilot.npz'):cp(E/name,M/('r0052-'+name))
    for tag in ('before','a-after','b-after','b-fixed-after'):
        cp(E/f'{tag}-renders.json',M/f'r0052-{tag}-renders.json')
        for view in views:cp(E/f'{tag}-{view}.png',M/f'r0052-{tag}-{view}.png')
    for name in ('r0052-delivery-comparison.png','r0052-angle-comparison.png','r0052-method-comparison.png'):cp(E/name,M/name)
    scripts=['inspect-female-next-r0052-native-groom.py','probe-female-next-r0052-sculpt.py',
        'build-female-next-r0052-combed-bob.py','run-female-next-r0052-native-events.py',
        'plan-female-next-r0052-sectional-sculpt.py','verify-female-next-r0052-native-readback.py',
        'package-female-next-r0052-native-groom.py']
    for name in scripts:cp(R/'scripts/character-next'/name,REPO/'scripts/character-next'/name)
    for tag in ('native-inspection','sculpt-probe','native-pilot','native-gui','native-gui-loaded','native-gui-pilot',
                'native-events-pilot','native-events-full','sectional-pilot','sectional-full','effective-pilot','effective-full','readback','fixed-readback'):
        name=f'character-female-next-r0052-{tag}.log';cp(R/'Evidence'/name,M/name)
    snapshot={'revision':'female-next-r0052','workingSourceUnchanged':True,
        'files':[{'path':str(p.relative_to(REPO)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':sha(p)} for p in files]}
    write(E/'history-file-manifest.json',snapshot);cp(E/'history-file-manifest.json',M/'r0052-history-file-manifest.json')
    write(E/'git-paths.json',sorted(str(p.relative_to(REPO)).replace('\\','/') for p in files))
    print('R52_HISTORY_READY',len(files),sum(p.stat().st_size for p in files))

if __name__=='__main__':main()
