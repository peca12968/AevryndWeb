"""Matched full head/body and affected hairstyle views; no new lighting or model edit."""
from pathlib import Path
import json,datetime,importlib.util
sp=importlib.util.spec_from_file_location('r143viewhelpers',Path(__file__).with_name('review-female-next-r0139-views.py'));s=importlib.util.module_from_spec(sp);sp.loader.exec_module(s)
E=s.E.parent/'r0143-authored-section-volumes';BASE=E.parent/'r0139-native-lid-follow'
def main():
 s.E=E;old=json.loads((BASE/'a-view-controls.json').read_text('utf-8'));new=json.loads((E/'a-view-controls.json').read_text('utf-8'));clean=lambda x:{k:v for k,v in x.items() if k not in ['file','capture']};assert [clean(x) for x in old]==[clean(x) for x in new]
 def row(v):return [('r139 adopted working woman / '+v,BASE/('matched-a-native-lid-follow-'+v+'.png')),('r143 unaccepted section volumes / '+v,E/('matched-a-section-volumes-'+v+'.png'))]
 s.sheet('r0143-complete-head-body-comparison.png',[row('face'),row('body-face')],'Same actual full woman and matched camera/light/exposure/pose. Judge full shape before detail or audit.')
 s.sheet('r0143-profile-back-comparison.png',[row('profile'),row('back')],'Original card surface hidden; new current-scalp hair is the actual rendered geometry, not guide-only preview.')
 s.sheet('r0143-oblique-comparison.png',[row('oblique')],'Original current-root anatomical section volumes; no new complete hair operation, contact or engine claim.')
 window=[('r141 / authored flow rejected',E.parent/'r0141-authored-parting-flow','a-authored-parting'),('r142 / scalp-flow rejected',E.parent/'r0142-scalp-adjacent-flow','a-scalp-adjacent'),('r143 / section volumes unaccepted',E,'a-section-volumes')]
 s.sheet('whole-review-141-142-143-head-body.png',[[(' '+label+' / '+v,ep/('matched-'+tag+'-'+v+'.png')) for v in ['face','body-face']] for label,ep,tag in window],'Three actual rounds. R142 original failed part-end classification attempt retained separately; not an extra complete woman candidate.')
 s.sheet('whole-review-141-142-143-profile-back.png',[[(' '+label+' / '+v,ep/('matched-'+tag+'-'+v+'.png')) for v in ['profile','back']] for label,ep,tag in window],'Judge actual full woman and rest-shape volume. Guide/root correctness is not appearance, natural dynamics or full contact proof.')
 first=datetime.datetime.fromtimestamp(max((E/('matched-a-section-volumes-'+v+'.png')).stat().st_mtime for v in ['face','body-face','profile','oblique','back']),datetime.timezone.utc).isoformat()
 (E/'matched-view-verification.json').write_bytes((json.dumps({'allActualFiveViewControlsExactlyMatchR139':True,'onlyExcludedMetadata':['file','capture'],'firstCompleteFiveViewUTC':first,'actualCompleteHeadBodyAndAffectedHairAngles':True,'noDifferentLightingOrExposureForCandidate':True},indent=2)+'\n').encode())
 print('R143_ACTUAL_MATCHED_COMPLETE_HEAD_BODY_AND_HAIR_VIEWS_READY',first,flush=True)
if __name__=='__main__':main()
