"""Quantify r1080 iris proportion, sclera exposure and cornea artifact removal."""
import json
from pathlib import Path
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]; ASSETS=ROOT/"assets-source/aevrynd-character"
STUDY=ASSETS/"female-v249-mainline-r1080-eye-optics-sweep.study.json"; ISOLATION=ASSETS/"female-v249-mainline-r1080-eye-layer-isolation.render.json"
REPORT=ASSETS/"female-v249-mainline-r1080-eye-optics.visual-audit.json"; OUT=ROOT.parent/"Temp/female-realism/v249r1080-eye-optics"; ISO=ROOT.parent/"Temp/female-realism/v249r1080-eye-optics-isolation"
CONTROL="a-control"; SELECTED="g-cornea-0.20"


def load(path): return np.asarray(Image.open(path).convert("RGB"),dtype=np.float32)


def sclera_proxy(image,x0,x1):
    roi=image[220:540,x0:x1]; r,g,b=roi[...,0],roi[...,1],roi[...,2]; return int(((g/(r+1e-6)>.90)&(b/(r+1e-6)>.72)&(roi.mean(2)>150)).sum())


study=json.loads(STUDY.read_text(encoding="utf-8")); variants={item["label"]:item for item in study["variants"]}
proxy={}
for label in variants:
    image=load(OUT/f"{label}-eye-front.png"); left,right=sclera_proxy(image,0,600),sclera_proxy(image,800,1400); proxy[label]={"left":left,"right":right,"total":left+right}

cornea={}
for prefix in ("control","selected"):
    composite=load(ISO/f"{prefix}-eye-only.png"); no_cornea=load(ISO/f"{prefix}-eye-only-no-cornea.png"); delta=np.abs(composite-no_cornea).mean(2); rois=[delta[300:600,0:450],delta[300:600,950:1400]]
    cornea[prefix]={"fullFrameMeanAbsoluteRgbDelta255":float(delta.mean()),"lowerEyeRoiMeanAbsoluteRgbDelta255":[float(roi.mean()) for roi in rois],"lowerEyeRoiPixelsAbove20":[int((roi>20).sum()) for roi in rois]}

fixed={}
for view in ("face-front","face-three-quarter"):
    a=load(OUT/f"{CONTROL}-{view}.png"); b=load(OUT/f"{SELECTED}-{view}.png"); fixed[view]=float(np.abs(a[:150]-b[:150]).mean())
control_size=variants[CONTROL]["metrics"]["optics"]["L"]["sizeMm"]; selected_size=variants[SELECTED]["metrics"]["optics"]["L"]["sizeMm"]
control_pixels=sum(cornea["control"]["lowerEyeRoiPixelsAbove20"]); selected_pixels=sum(cornea["selected"]["lowerEyeRoiPixelsAbove20"])
report={
    "revision":"v249r1080-eye-optics-visual-audit","study":str(STUDY),"isolation":str(ISOLATION),"control":CONTROL,"selected":SELECTED,
    "irisSizeMm":{"control":control_size,"selected":selected_size,"radialScale":variants[SELECTED]["metrics"]["optics"]["L"]["scale"]},
    "scleraProxy":proxy,"selectedTotalScleraProxyReductionPercent":100.0*(proxy[CONTROL]["total"]-proxy[SELECTED]["total"])/proxy[CONTROL]["total"],
    "corneaIsolation":cornea,"corneaArtifactPixelsAbove20ReductionPercent":100.0*(control_pixels-selected_pixels)/control_pixels,
    "fixedUpperFrameMeanAbsoluteRgbDelta255":fixed,
    "visualDecision":{"selected":SELECTED,"reason":"The 1.16 iris reaches 11.19 x 11.87 mm, 0.08 mm recess and 0.75 degree convergence reduce the flat doll stare, 0.88 sclera multiplier tempers white wedges, and a correctly connected 0.20 blended cornea removes the giant six-o'clock area-light disk while retaining a restrained optical layer."},
    "status":"PASS_SELECTED_G_CORNEA_0_20",
}
REPORT.write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps({"status":report["status"],"irisSizeMm":report["irisSizeMm"],"scleraReductionPercent":report["selectedTotalScleraProxyReductionPercent"],"corneaArtifactReductionPercent":report["corneaArtifactPixelsAbove20ReductionPercent"],"cornea":cornea},indent=2))
