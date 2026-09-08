# Aevrynd character quality gate

The final score is out of 100. A candidate is eligible for user review only at
90 or above, with every category at 75% of its own maximum and every blocking
gate passing. Scores describe visible evidence, not implementation effort.

| Category | Points | Required evidence |
| --- | ---: | --- |
| Anatomy and silhouette | 16 | Neutral front, side, and back renders; landmark and proportion review |
| Face identity and forms | 16 | Neutral close-up plus three-quarter view; skull, eyelids, nose, lips, ears and asymmetry review |
| Skin, eyes, mouth and nails | 12 | PBR maps at native resolution; close-ups under neutral and grazing light |
| Hair and hairline | 14 | Front, side, crown and back renders; root coverage, clumps, breakup and motion review |
| Topology, UV and LODs | 8 | Manifold audit, deformation loops, texel density, tangent basis and measured LOD error |
| Clothing and layer construction | 10 | Isolated layer renders, seams, thickness, folds and material response |
| Rig and deformation | 8 | Standard pose suite including shoulders, elbows, wrists, spine, hips, knees and face |
| Collision integrity | 10 | Zero inter-layer triangle intersections and zero penetrating samples in neutral and pose suite |
| Runtime performance | 6 | Measured GLB size, triangles, textures, draw calls, frame time and memory |

## Blocking gates

- Source version, origin, license and digest are recorded.
- Body, eyes, mouth, hair, inner clothing and outer clothing have explicit roles.
- No static or posed body/clothing/hair penetration is detected.
- Eyes remain seated in the lids and teeth remain inside the mouth in every test pose.
- No visible seam, inverted normal, broken tangent, floating root or detached garment.
- The review renderer uses fixed camera, exposure and light presets.
- Runtime assets contain no Blender, Unreal, MetaHuman or cloud-service dependency.
- The previous accepted preview remains available until the candidate passes.

## Review states

- `SOURCE`: licensed authoring reference; not an engine-ready character.
- `BLOCKOUT`: broad proportions and silhouette; no detail score claimed.
- `AUTHORING`: sculpt, topology, UV, rig and layers are still changing.
- `CANDIDATE`: all automatic gates pass and the score is at least 90.
- `ACCEPTED`: the user approves the candidate for use in Aevrynd.

