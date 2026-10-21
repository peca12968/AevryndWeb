"""Actual complete woman and due three-round review, including failed candidates."""
from pathlib import Path
import json,datetime,importlib.util
sp=importlib.util.spec_from_file_location('r140viewhelpers',Path(__file__).with_name('review-female-next-r0139-views.py'));s=importlib.util.module_from_spec(sp);sp.loader.exec_module(s)
E=s.E.parent/'r0140-native-clump-roots';BASE=E.parent/'r0139-native-lid-follow'
def main():
 s.E=E;old=json.loads((BASE/'a-view-controls.json').read_text('utf-8'));new=json.loads((E/'a-view-controls.json').read_text('utf-8'));clean=lambda row:{k:v for k,v in row.items() if k not in ['file','capture']};assert [clean(r) for r in old]==[clean(r) for r in new]
 def row(v):return [('r139 adopted working woman / '+v,BASE/('matched-a-native-lid-follow-'+v+'.png')),('r140 unaccepted groom / '+v,E/('matched-a-native-rooted-groom-'+v+'.png'))]
 s.sheet('r0140-complete-head-body-comparison.png',[row('face'),row('body-face')],'Actual matched camera/light/exposure/pose; source counts and editable controls do not establish realism.')
 s.sheet('r0140-profile-back-comparison.png',[row('profile'),row('back')],'Actual complete hairstyle; old coarse surface is hidden, no opaque underlay, no appearance adoption.')
 s.sheet('r0140-oblique-comparison.png',[row('oblique')],'Do not tune shader, density, radius or station count after complete visible failure.')
 window=[('r138 A / partial eye control',E.parent/'r0138-native-current-gaze','a-native-current-gaze'),('r138 B / static-lid failure',E.parent/'r0138-native-current-gaze','b-native-socket-walls'),('r139 / scoped gaze adopted',BASE,'a-native-lid-follow'),('r140 / failed whole hairstyle',E,'a-native-rooted-groom')]
 s.sheet('whole-review-138-139-140-head-body.png',[[(' '+label+' / '+v,ep/('matched-'+tag+'-'+v+'.png')) for v in ['face','body-face']] for label,ep,tag in window],'Three actual rounds, four complete candidate states; r139 function adoption does not reset appearance stagnation.')
 s.sheet('whole-review-138-139-140-profile-back.png',[[(' '+label+' / '+v,ep/('matched-'+tag+'-'+v+'.png')) for v in ['profile','back']] for label,ep,tag in window],'Original geometry/rights/rollback retained; no new whole appearance gain in this window.')
 first=datetime.datetime.fromtimestamp(max((E/('matched-a-native-rooted-groom-'+v+'.png')).stat().st_mtime for v in ['face','body-face','profile','oblique','back']),datetime.timezone.utc).isoformat();(E/'matched-view-verification.json').write_text(json.dumps({'allActualFiveViewControlsExactlyMatchR139':True,'onlyExcludedMetadata':['file','capture'],'firstCompleteFiveViewUTC':first,'originalMtimePreservedAfterLocationCorrection':True,'noRerenderOrRoundRestartForOutputPathCorrection':True,'actualCompleteHeadBodyAndAffectedHairAngles':True},indent=2)+'\n',encoding='utf-8');print('R140_ACTUAL_COMPLETE_AND_DUE_WHOLE_REVIEW_BOARDS_READY',first)
if __name__=='__main__':main()
