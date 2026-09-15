# v249r1028 interpolated lash density

`contact-sheet-r1028.jpg` compares half-gap, every-gap and double-fill interpolation on the root-fixed r1027 paths.

The selected every-gap bound contains 91 upper lashes per eye and 43 left/42 right lower lashes. One unsafe right-lower candidate is pruned before assembly. New-vs-original, new-vs-new and four-frame body/eye/lash overlaps are all zero.

The four existing lash object-material pairs are unchanged. Geometry increases by 2,751 vertices and 2,358 polygons, while the compressed Blend grows by 10,296 bytes. Double-fill is rejected for self-overlap and excessive weight.

Strict scores: lashes 61/100, full face 48/100. This is a local technical candidate and is not approved for the website.
