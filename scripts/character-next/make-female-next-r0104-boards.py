from pathlib import Path
import importlib.util
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0104-native-artist-ocular-foundation';OLD=E.parent/'r0102-facet-aware-lid-surface'
sp=importlib.util.spec_from_file_location('r104boards',Path(__file__).with_name('make-female-next-r0101-boards.py'));b=importlib.util.module_from_spec(sp);sp.loader.exec_module(b);b.E=E
b.board('r0104-head-and-body-ab.png',[('r102 functional reference / unaccepted',OLD,'matched-a-facet-lining'),('r104 B2 native head art / unaccepted',E,'matched-b2-native-head-material-repair')],['face','body-face'],'New head/neck/groom placement shown honestly. Mouth chart, static skin, contacts and runtime remain unaccepted.')
b.board('r0104-profile-ab.png',[('r102',OLD,'matched-a-facet-lining'),('r104 B2',E,'matched-b2-native-head-material-repair')],['profile'],'Actual whole source profile; original body below the neck retained. Native neck transition is new geometry.')
b.board('r0104-three-round-whole-woman.png',[('r102 finite lining / local only',OLD,'matched-a-facet-lining'),('r103 front bands / rejected',E.parent/'r0103-anatomical-front-lid-bands','matched-a-anatomical-bands'),('r104 native head / local art only',E,'matched-b2-native-head-material-repair')],['face','body-face'],'Three actual production rounds, including failures/repairs. No adopted complete appearance or complete operation.')
b.board('r0104-mouth-domain-ab.png',[('B2 material indices restored',E,'matched-b2-native-head-material-repair'),('B3 skin-domain hypothesis ineffective',E,'matched-b3-native-head-skin-domain')],['face'],'Geometry identical. Canonical skin-only domain resampling does not resolve the visible lip artifact.')
print('R104_ACTUAL_COMPLETE_BOARDS_DONE')
