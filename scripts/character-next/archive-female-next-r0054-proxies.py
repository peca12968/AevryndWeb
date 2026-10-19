"""Reconcile the previously unregistered r54 proxies without adopting them."""
from pathlib import Path
import json,hashlib,datetime
from PIL import Image,ImageDraw,ImageFont
R=Path(r'D:\Download\Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0054-clump-volume'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    snapshots=[]
    for tag in 'abcde':
        report=read(E/(tag+'-build-summary.json'));p=Path(report['output']);assert sha(p)==report['outputSha256']
        snapshots.append({'source':str(p),'sha256':sha(p),'role':'REJECTED_DESIGN_PROXY_NOT_HAIR'})
    audit={'revision':'female-next-r0054','decision':'REJECT_SKIN_CLUMP_AND_CONCEPT_HULL_PROXY_METHODS',
        'appearance':{'status':'FAIL','appearanceImprovement':False,'wholeCharacterScore':None,
            'observations':['A/B/C quad Skin clumps form tubes and hard plates rather than natural locks; posterior filling does not fix the construction.',
                'D visual hull has strong horizontal bands; E closed/smoothed masks still show horizontal extrusion bands, crown/side holes and hard helmet/bang edges.',
                'Actual full head/body, front/profile/back/oblique and second-light views were rendered; E face/profile/back/body were explicitly reviewed on continuation.'],
            'conceptImageIsReferenceOnly':True,'newFinalHairStrands':0},
        'function':{'status':'EDITABLE_PROXIES_SAVED_NOT_ACCEPTED_HAIR','snapshots':snapshots,'originalCharacterUnchangedAtBuild':True,
            'scope':'Separate mesh design studies; neither follicle maps nor simulation/collision representations.'},
        'contact':{'status':'NOT_QUALIFIED_DESIGN_PROXIES','reason':'Not expanded after complete-form rejection. Projected depth intervals are not full geometry or continuous collision proof.'},
        'runtime':{'status':'NOT_TESTED_NOT_PROMOTED','cpuGpuTimeMemory':None},
        'stoppedMethods':['Native Skin station chains as the complete natural bob mass; no more width/density/coverage edits.',
            'Three-view concept mask visual hull as hair shape; one mask cleanup already failed. No threshold/voxel/smoothing sweep.'],
        'retention':'Rejected method evidence and scripts only; no proxy integrated into complete working r51 or formal assets.',
        'nextAction':'Evaluate a separately authored, license-verified real 3D guide source with a bounded full-head/body and actual finite-contact pilot. Do not derive fibres from these rejected proxies.',
        'reviewUTC':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    write(E/'female-next-r0054.visual-audit.json',audit)
    write(S/'aevrynd-female-next-r0054-authoring.json',audit)
    write(E/'continuation.json',{'lastGoalTurnClassification':'progress','progressKind':'RECONCILE_AND_REJECT_UNREGISTERED_PROXIES',
        'appearanceImprovement':False,'workingReviewSource':str(S/'aevrynd-female-next-r0051-b-integrated-eye-wall.blend'),
        'workingReviewSha256':'b86f7eeedf6fd6a4d9a7f13ff42dc4051907516bc90be8261f02e7678242a3ff',
        'latestEvidence':str(E/'female-next-r0054.visual-audit.json'),'stoppedMethods':audit['stoppedMethods'],
        'nextAction':audit['nextAction'],'liveJobHandles':[],'goal':'ACTIVE_NOT_COMPLETE','wholeCharacterScore':None})
    write(E/'design-concept-provenance.json',{'type':'GENERATED_BITMAP_REFERENCE_ONLY_NOT_3D_RESULT','image':'design-concept-reference-only.png',
        'sha256':sha(E/'design-concept-reference-only.png'),'tool':'built-in image_gen.imagegen','mode':'edit from two actual source-head review images',
        'referencedImages':[str(R/'Evidence/character-female-next/r0053-new-primary-groom'/('grown-fixed-actual-fibres-'+v+'.png')) for v in ('face','profile')],
        'prompt':"Use case: stylized-concept. Asset type: HAIRSTYLE DESIGN REFERENCE ONLY, not evidence of a completed 3D asset. Make a clean orthographic character hairstyle turnaround sheet, three equally sized columns labelled FRONT, LEFT PROFILE, BACK. Use the supplied images only as reference for the SAME adult female CG head's skull shape, large eyes, face proportions, ears, jaw and neck. Ignore/remove every existing thin stray guide line. Do not beautify, change face anatomy or invent a different person. Design one coherent realistic natural chin-length brown bob without bangs: slightly off-centre part, hair lying smoothly over the crown with restrained lift, soft grouped locks and fine realistic fibres, ears mostly covered, a full continuous occipital/back mass, gentle inward-curving ends near the jaw. No long bald rear slit. Width only modestly wider than the skull, no exaggerated puff or roof, no hard plate seams, no floating root arches, no dreadlocks/tubes. Hair should have natural depth and softly overlapping layers, not a thin plastic helmet or straight flat curtains. Precisely consistent hairstyle and scale across all three orthographic views, crowns and jaw levels aligned. Plain white background, neutral soft studio illumination, head and upper shoulders only, no jewellery or accessories. Top heading verbatim: 'HAIR DESIGN CONCEPT'. Bottom footer verbatim: 'REFERENCE ONLY - NOT A 3D MODEL RESULT'. This image will guide subsequent real Blender mesh authoring; it must not imply that our existing 3D mesh has already been improved.",
        'scope':'Concept only. No measured photographic alignment. Actual mesh renders are separate and visually rejected.'})
    font=ImageFont.truetype('C:/Windows/Fonts/msjh.ttc',18);small=ImageFont.truetype('C:/Windows/Fonts/msjh.ttc',16)
    w=440;h=480;board=Image.new('RGB',(w*3,h*2+88),'#181c21');draw=ImageDraw.Draw(board)
    baseline=R/'Evidence/character-female-next/r0053-new-primary-groom'
    for row,view in enumerate(('face','body-face')):
        for col,(folder,tag,label) in enumerate([(baseline,'before','保留完整工作角色 r51'),(E,'c-proxy','r54 C：髮束代理／判退'),(E,'e-proxy','r54 E：圖像體積代理／判退')]):
            draw.text((col*w+8,row*h+8),label,font=font,fill='white');board.paste(Image.open(folder/(tag+'-'+view+'.png')).convert('RGB').resize((w,w)),(col*w,row*h+36))
    draw.text((8,h*2+8),'全部為實際 Blender 畫面。後兩欄是設計代理，不是完成毛髮。',font=small,fill='#e6c58a')
    draw.text((8,h*2+39),'未採用；沒有完整人物外觀進步、接觸、動態或引擎通過聲稱。',font=small,fill='#d0d5df')
    board.save(E/'r0054-complete-review.png')
    print('R54_RECONCILED_REJECTED',len(snapshots))

if __name__=='__main__':main()
