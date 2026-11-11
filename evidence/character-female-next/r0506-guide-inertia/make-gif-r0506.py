"""Combine palette-encoded comparisons into one correctly timed looping GIF."""
from pathlib import Path
import json
import struct

ROOT=Path(__file__).resolve().parent


def image_blocks(data):
    assert data[:6] in (b'GIF87a',b'GIF89a')
    screen=data[6:13]
    packed=screen[4]
    size=3*(2**((packed&7)+1)) if packed&128 else 0
    global_table=data[13:13+size]
    pos=13+size

    def end_of_subblocks(pos):
        while data[pos]:
            pos+=data[pos]+1
        return pos+1

    while data[pos]==0x21:
        pos=end_of_subblocks(pos+2)
    assert data[pos]==0x2c
    desc=bytearray(data[pos:pos+10])
    pos+=10
    if desc[9]&128:
        depth=desc[9]&7
        size=3*(2**(depth+1))
        table=data[pos:pos+size]
        pos+=size
    else:
        depth=packed&7
        table=global_table
    assert len(table)==3*(2**(depth+1))
    desc[9]=(desc[9]&0x78)|0x80|depth
    end=end_of_subblocks(pos+1)
    assert data[end]==0x3b
    return screen,global_table,bytes(desc)+table+data[pos:end]


def main():
    receipt=json.loads((ROOT/'preview-receipt.json').read_bytes())
    frames=receipt['motionFrames']
    fps=receipt['fps']
    clips=[image_blocks((ROOT/'gif-frames'/f'f{frame:02}.gif').read_bytes()) for frame in frames]
    screen,palette=clips[0][:2]
    result=bytearray(b'GIF89a'+screen+palette+b'\x21\xff\x0bNETSCAPE2.0\x03\x01\x00\x00\x00')
    for i,(_,_,image) in enumerate(clips):
        delay=round((frames[i+1]-frames[i])*100/fps) if i+1<len(frames) else 65
        result+=b'\x21\xf9\x04\x04'+struct.pack('<H',max(2,delay))+b'\x00\x00'+image
    (ROOT/'r0506-hair-motion.gif').write_bytes(result+b'\x3b')


if __name__=='__main__':
    main()

