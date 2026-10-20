"""Close unregistered r62 trials without promoting their failed motion."""
from pathlib import Path
import json,hashlib,datetime
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0062-packed-bundle';S=R/'engine/assets/characters/female-next/source'
def read(n):return json.loads((E/n).read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    a=read('a-build-summary.json');source=Path(a['output']);assert source.exists() and sha(source)==a['outputSha256']
    assert not (S/'aevrynd-female-next-r0062-b-cached-packed-wind-study.blend').exists()
    static=read('a-static-self-verification.json');body=read('a-static-body-verification.json');guide=read('b-motion-static-self-falsification.json');continuous=read('c-early-continuous-self-audit.json');native=read('native-kernel-verification.json')
    cpp=R/'engine/character/physics/shaft_contacts.cpp';dll=E/'native/aevrynd_shaft_contacts.dll'
    result={'revision':'female-next-r0062','reviewUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),
      'decision':'RETAIN_STATIC_UNIT_REJECT_GUIDE_FOLLOW_AND_DISCRETE_MOTION_NO_FULL_HAIRSTYLE',
      'source':str(source),'sourceSha256':sha(source),'actualFibres':a['actualFibres'],'pointsPerFibre':a['pointsPerFibre'],
      'appearance':{'completeCharacterImprovement':False,'wholeCharacterScore':None,'reason':'61 fibres form an isolated antenna-like bundle on an otherwise near-bald head. This is not a complete hairstyle.'},
      'function':{'staticEditableCurvesCreated':True,'restFollicleAttributeFormatRetained':True,'completeFunctionalHairDelivered':False,'nativeMotionBlendCreated':False},
      'contact':{'staticSelfEvidence':static,'staticFreeBodyEvidence':body,'guideFollow':'Actual displayed finite shafts fail self separation despite stable guide; see b-motion-static-self-falsification.json.','independentDiscrete':'Published initial state passes static self, but first tested interpolation interval fails robust continuous numerical clearance. Do not resume or publish it as qualified motion.','continuousAudit':continuous,'exactGlobalSignedMinimumM':None,'noBlanketPhysicalOverlapClaim':'Positive gaps below1um and unresolved bounds do not by themselves prove negative physical distance. Gate remains failed without changing tolerance.'},
      'runtime':{'status':'NOT_TESTED_NOT_PROMOTED','completeEngineCapabilityDelivered':False},
      'nativePrototype':{'location':str(cpp),'currentCPPSha256':sha(cpp),'currentDLLSha256':sha(dll) if dll.exists() else None,'oldEquivalenceCPP':native['sourceCPPSha256'],'oldEquivalenceDLL':native['dllSha256'],'oldEquivalenceAppliesToCurrentBuild':False,'reason':'An additional speculative swept-contact API was appended after instantaneous API comparison. Current build/sweep path was not independently qualified or integrated with a saved animation. Compilation is not a collision pass.','oldReceipt':'native-kernel-verification.json','engineBenchmarkPassed':False},
      'retainedResearch':{'purpose':'Ordered actual finite-shaft rest geometry and native follicle lineage format; isolated contact-kernel study only.','scope':'61-shaft static unit and exact old instantaneous-kernel/reference comparison versions; not full natural hair.','blocker':'Guide display self collisions, discrete motion continuous-clearance failure, untested new sweep API, no complete hairstyle.','minimumIntegrationStep':'Use validated rest-lineage format and finite-shaft acceptance on an authored complete hairstyle; do not make another isolated bundle the production mainline.'},
      'stoppedMethods':['Guide-only stable motion followed by rotation-minimizing packed display: actual free shafts cross.','Discrete-only self-contact projection as evidence for continuous no-penetration: first published interval fails numerical gate.','Repeated local XPBD/solver optimization without a complete visible hairstyle: no appearance credit.'],
      'liveJobHandles':[],'sourceOfTruthCompleteCharacter':'aevrynd-female-next-r0060-b-limit-surface-assembly-study.blend',
      'nextAction':'Return to actual complete-head/body views under v17; author a complete usable hairstyle or choose another major visible defect. Do not automatically resume old local solver nextAction.',
      'goal':'ACTIVE_NOT_COMPLETE','manifestAdoptionChangedByThisScript':False}
    (E/'reconciled-study-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print('R62_RECONCILED_STATIC_UNIT_ONLY_NO_MOTION_PROMOTION',sha(source))
if __name__=='__main__':main()
