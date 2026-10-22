from pathlib import Path
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158')
for name in ['verify-female-next-r0164-paired-lid-return.py','inspect-female-next-r0164-effective-data.py']:
 p=C/'scripts/character-next'/name;exec(compile(p.read_text(encoding='utf-8'),str(p),'exec'),{'__name__':'__main__','__file__':str(p)})
