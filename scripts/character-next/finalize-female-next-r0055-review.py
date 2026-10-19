"""Record the actual visual/contact rejection and deliver labelled full views."""
from pathlib import Path
import json,hashlib,datetime
from PIL import Image,ImageDraw,ImageFont
R=Path(r'D:\Download\Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0055-authored-cc0-bob'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    now=datetime.datetime.now(datetime.timezone.utc).isoformat();reports={tag:read(E/(tag+'-static-body-capsules.json')) for tag in 'abcd'}
    reopened=read(E/'d-reopened-verification.json');build=read(E/'d-build-summary.json');bindings=read(E/'d-root-bindings.json')
    assert [reports[t]['unqualifiedSegments'] for t in 'abcd']==[429,89,147,21]
    assert reopened['reopened'] and reopened['actualBodySourceUVFloat32ExactlyMatches']
    assert sha(Path(build['output']))==build['outputSha256']
    maxRoot=build['rootRegistrationDistanceRangeM'][1];assert maxRoot>.05
    stopped=['Uniform affine whole-style registration as an accepted groom, including measured eye/top alignment. Actual source/target scalp regions differ.',
        'Nearest-body fitted whole-surface Surface Deform: native binding succeeds but ear-region kinks and147unqualified segments reject this construction.',
        'Closest existing scalp-triangle follicle reassignment plus point-projected smooth displacement as full hair fitting: some roots move52.6mm and21finite capsules remain unqualified. No more iterations, margins, density or smoothing sweeps.']
    nextAction=('Keep complete working r51B and scoped r53retained data. R54proxies and r55affine/surface/closest-root fitting are rejected. '
        'The CC0 Bob248source guides may serve as a visual flow reference only; never use the rejected fitted paths/roots as accepted masters. '
        'NEXT establish a target-native guide design directly on the same anatomical scalp with Blender native grooming/sculpting, '
        'using actual front/profile/back reference views and the already retained root-binding tools. First a bounded coarse whole-head '
        'guide layout with readable crown, side and back flow; do not copy oldr48/r53world routes, deform the oldbob, import donor paths '
        'through the stopped fitting methods, or generate children. If actual source/target scalp correspondence is proposed instead, '
        'first independently establish anatomical hairline/ear/nape compatibility, not just eye/top alignment or nearest-point clamping. '
        'Use complete-head/body views to reject early, then certify all finite paths/body/self and affected optics before children. '
        'Contact algorithms must cover full segments, not only projected CVs. Whole appearance, oral/clothes/rig, known source-body '
        'self failures, natural full hair/self/continuous dynamics and actual engine performance remain incomplete.')
    research={'purpose':'License-verified authored3Dhair flow reference and exact rejected fitting/solver evidence; serialization/UV tools only.',
        'scope':'CC0 Bob248source guides; D actual body barycentric/UV readback only, not anatomically accepted follicles or a collision-safe groom.',
        'blockingEvidence':'Root registration correction reaches52.6mm; ear/back path bends and21unqualified finite capsules. Self/other optics/dynamics not run after rejection.',
        'minimumIntegrationStep':'None for rejected fitted geometry. Use source as visual reference during genuinely target-native authoring; only independent complete form/contact acceptance could establish a new groom.'}
    audit={'revision':'female-next-r0055','decision':'REJECT_DIRECT_CC0_GUIDE_FITS_RETAIN_REFERENCE_ONLY','reviewUTC':now,
        'appearance':{'status':'NOT_ACCEPTED','appearanceImprovement':False,'wholeCharacterScore':None,
            'observations':['Authored B flow is more readable than prior synthetic mass trials but sparse pilot is not an accepted complete hairstyle.',
                'C whole-surface deformation introduces sharp ear-region bends.',
                'D retains ear/back zigzags and redistributes some source roots far from their original design location; no convincing complete character appearance gain.',
                'Actual55um-to9um fibres and0.5mmthick diagnostic paths are shown separately. The thick paths are never final hair or collision geometry.'],
            'actualHeadBodyMultiangleAndSecondLight':True,'childrenGenerated':False,'diagnosticRadiusM':.0005},
        'function':{'status':'REJECT_FITTED_GROOM_RETAIN_SOURCE_REFERENCE','reopenedData':reopened,'research':research,
            'rootRegistrationDistanceRangeM':build['rootRegistrationDistanceRangeM'],'maximumBvhFloat32FootVsConstrainedDoubleFootDifferenceM':bindings['maximumBvhFloat32FootVsConstrainedDoubleFootDifferenceM'],
            'barycentricScope':'Exact body triangle/float32 UV serialization is verified; anatomical follicle placement is NOT accepted. Float32 BVH feet are only triangle locators; constrained double projection defines root data.'},
        'contact':{'status':'FAIL_OR_UNRESOLVED','unqualifiedSegmentsByCandidate':{t:reports[t]['unqualifiedSegments'] for t in 'abcd'},
            'rootFailuresByCandidate':{t:len(reports[t]['rootFailures']) for t in 'abcd'},
            'dFiniteSegments':reports['d']['segments'],'dSampledCVMinimumUnsignedSurfaceGapM':reports['d']['minimumSampledCVSurfaceGapM'],
            'dMinimumCertifiedClearanceLowerBoundM':reports['d']['minimumCertifiedClearanceLowerBoundM'],
            'interpretation':'21segments fail the finite-capsule gate although sampled CVs are outside. Unqualified includes crossing/uncertified states, not21proven penetration depths. Lower bound is not an exact global signed distance.',
            'masterSelfOtherOpticsClothingContinuousDynamics':'NOT_RUN_AFTER_FORM_AND_BODY_FAILURE',
            'sourceBody':'Unchanged r51 body; known839other nonocular tested self pairs remain, no whole-body pass.'},
        'runtime':{'status':'NOT_TESTED_NOT_PROMOTED','cpuGpuTimeMemory':None},
        'retainedReference':{'repository':'https://github.com/Upliner/CharMorph-Vitruvian','commit':'c252d1fc7f00ba59d87b66b3d32fa3471fc6ee44','licenseDeclaration':'config.yaml: CC0',
            'authors':'Sean Buckley, Olaf Delgado-Friedrichs; additional contributors in retained config.yaml','noAddonOrToolCodeImported':True,
            'originalBlend':'Local reference only; autoexec disabled; embedded rig texts not imported or published as engine code.'},
        'stoppedMethods':stopped,'usefulResearch':research,'nextAction':nextAction}
    write(E/'female-next-r0055.visual-audit.json',audit)
    write(E/'continuation.json',{'stage':'B_COMPLETE_HEAD_IN_PROGRESS','previousGoalTurnClassification':'progress: v15 prompt/entry changes completed and pushed5dc7d3c; no model appearance progress.',
        'lastGoalTurnClassification':'progress','progressKind':'RECONCILED_R54_AND_FALSIFIED_THREE_AUTHORED_GUIDE_FITTING_METHODS','appearanceImprovement':False,
        'functionalUnblocking':'Source data/UV serialization and contact-repair implementation only; not a qualified new groom or completed character feature.',
        'workingReviewSource':str(S/'aevrynd-female-next-r0051-b-integrated-eye-wall.blend'),'workingReviewSha256':'b86f7eeedf6fd6a4d9a7f13ff42dc4051907516bc90be8261f02e7678242a3ff',
        'latestEvidence':str(E/'female-next-r0055.visual-audit.json'),'unregisteredR54':'All5snapshots reconciled, rejected and included in this history package.',
        'liveJobHandles':[],'stoppedMethods':stopped,'usefulResearch':research,'nextAction':nextAction,'wholeCharacterScore':None,
        'resources':{'reviewUTC':now,'blenderThreadsLimit':4,'heavyJobsAtOnce':1,'newNodeServers':0,'remoteJobs':0,
            'observedWorkingSetMB':{'affinePilot':2412,'boundSolver':1323},'measurement':'Sampled process working sets, not instrumented peaks or runtime benchmarks.','goal':'ACTIVE_NOT_COMPLETE'},
        'remainingGates':['Credible complete appearance','Full oral/clothing/body rig','Known nonocular body contacts','Natural hair/full self/continuous contact','Actual engine/LOD/performance','Weighted85each80 and explicit female acceptance']})
    font=ImageFont.truetype('C:/Windows/Fonts/msjh.ttc',18);small=ImageFont.truetype('C:/Windows/Fonts/msjh.ttc',16)
    def board(name,views,w):
        h=w+40;out=Image.new('RGB',(3*w,len(views)*h+110),'#181c21');draw=ImageDraw.Draw(out)
        columns=[(R/'Evidence/character-female-next/r0053-new-primary-groom','before','保留工作角色 r51'),(E,'d-actual-fibres','r55 D 實際248條／判退'),(E,'d-path-diagnostic','r55 D 加粗診斷／非成品')]
        for row,view in enumerate(views):
            for col,(folder,tag,label) in enumerate(columns):
                draw.text((col*w+7,row*h+7),label+' / '+view,font=font,fill='white');out.paste(Image.open(folder/(tag+'-'+view+'.png')).convert('RGB').resize((w,w)),(col*w,row*h+36))
        notes=['沒有新的可採用外觀改善；主線與網站保持原版。',
            '21個完整線段未通過人體接觸；部分根部改位52.6毫米，不能採用。',
            '右欄半徑0.5毫米只供看路徑；實際半徑9–55微米，無子髮／動態／引擎驗收。']
        for j,n in enumerate(notes):draw.text((8,len(views)*h+7+j*32),n,font=small,fill='#e6c58a' if j==0 else '#d0d5df')
        out.save(E/name)
    board('r0055-complete-review.png',('face','body-face'),500);board('r0055-angle-review.png',('profile','back','alternate-oblique'),440)
    print('R55_REVIEW_FINALIZED_REJECTED',reports['d']['unqualifiedSegments'],maxRoot)

if __name__=='__main__':main()
