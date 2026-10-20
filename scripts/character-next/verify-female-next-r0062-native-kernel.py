"""Compare independent native code with the exact frozen Python reference.

Includes the real complete61-fibre rest and saved warm-up checkpoint, plus
analytic crossed/coincident cases. No body or physical acceptance is inferred
from implementation equivalence or kernel timing.
"""
from pathlib import Path
import ast,types,numpy as np,importlib.util,json,time,hashlib
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0062-packed-bundle'
def load(name,file):
    sp=importlib.util.spec_from_file_location(name,R/'scripts/character-next'/file);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
pair=load('nativePairTest62','hair-female-next-r0062-finite-pairs.py');native=load('nativeAPI62','native-female-next-r0062-contacts.py')
def main():
    source=E/'numpy-residual-source.py';tree=ast.parse(source.read_text(encoding='utf8'));function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='self_project');module=ast.Module(body=[function],type_ignores=[]);scope={'np':np,'m':types.SimpleNamespace(pair=pair),'SELF_GAP':3e-6,'SOLVE_RESIDUAL':1e-7};exec(compile(module,str(source),'exec'),scope);reference=scope['self_project'];raw=np.load(E/'a-packed-bundle-authoring.npz');rest=raw['positions'].astype('f8');radii=raw['radii'].astype('f8');ds=np.linalg.norm(np.diff(rest,axis=1),axis=2);w=1/(1300*mathPi()*35e-6**2*np.concatenate((ds,ds[:,-1:]),axis=1));w[:,:3]=0;cp=np.load(E/'c-independent-checkpoint.npz');assert str(cp['codeSha'])==sha(source)
    crossed=np.array([[[-.001,0,0],[.001,0,0]],[[0,-.001,0],[0,.001,0]]]);coincident=np.array([[[0,0,0],[.01,0,0]],[[0,0,0],[.01,0,0]]]);cases=[('complete61rest',rest,radii,w),('actualWarmCheckpoint',cp['x'],radii,w),('crossed',crossed,np.full((2,2),35e-6),np.ones((2,2))),('coincident',coincident,np.full((2,2),35e-6),np.ones((2,2)))];rows=[]
    for label,x,r,mass in cases:
        py=x.copy();cpp=x.copy();start=time.perf_counter();a,g=reference(py,r,mass);pyTime=time.perf_counter()-start;start=time.perf_counter();b,gg,stats=native.project(cpp,r,mass);cppTime=time.perf_counter()-start;error=float(np.linalg.norm(py-cpp,axis=2).max());assert error<1e-10,(label,error);assert a==b,(label,a,b)
        rows.append({'case':label,'positionMaximumErrorM':error,'referenceCorrections':a,'nativeCorrections':b,'nativeCandidatePairs':stats.candidates,'nativeConflictFreeColours':stats.colours,'pythonSeconds':pyTime,'nativeSeconds':cppTime})
    report={'status':'PASS_NATIVE_REFERENCE_EQUIVALENCE','sourceCPP':str(R/'engine/character/physics/shaft_contacts.cpp'),'sourceCPPSha256':sha(R/'engine/character/physics/shaft_contacts.cpp'),'dllSha256':sha(native.DLL),'pythonReferenceSha256':sha(source),'checkpointNextStep':int(cp['nextStep']),'ABIBytes':40,'compilerFlags':['MSVC x64','C++20','O2','MT','fp:strict'],'caseResults':rows,'maxErrorGateM':1e-10,'physicalCollisionAcceptance':'NOT_IMPLIED; actual saved motion/body/self/continuous tests remain required.','timingIsEngineBenchmark':False,'noNewSoftwareInstalled':True};(E/'native-kernel-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print(json.dumps(report,ensure_ascii=False))
def mathPi():return np.pi
if __name__=='__main__':main()
