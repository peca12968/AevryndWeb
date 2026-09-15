# v249r1020–r1022 dense eyelid patch review

- `contact-sheet-r1020.jpg`: 48-edge visible margin plus two attached support rings. Only `a-shallow` passes collision at frames 1/20/33/61; deeper bounds intersect both corneas.
- `contact-sheet-r1021.jpg`: canthus-ring closure remains collision-free but the coated rose margin looks like bright pink plastic. All bounds are rejected.
- `contact-sheet-r1022.jpg`: no-coat, low-IOR wetline study. `a-dry-rose` is retained only as a local optical candidate.
- `contact-sheet-r1022-integrated.jpg`: brows and lashes restored. Strict scores remain face 48, eyes/lids 52 and brows/lashes 54. The canthi, upper-lid volume and overall identity still fail hero quality.

The selected local stack is r1020a geometry plus r1022a dry-rose wetline. It preserves 30 shape keys, weights every new patch vertex and has zero body/eye/lash overlap across four frames. It is not approved for the website.

Fixed-tone drift from r1020a to r1022a is below 0.0005% in all measured forehead and cheek regions, so this work does not progressively darken the character.
