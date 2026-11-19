from pathlib import Path
import struct,json,zlib,sys
root=Path(__file__).resolve().parent.parent
def check(path,expected):
    b=path.read_bytes();matches=[]
    for bs in [512,4096]:
        if b[bs:bs+8]!=b'EFI PART':continue
        hs=struct.unpack_from('<I',b,bs+12)[0]
        if not 92<=hs<=bs:continue
        h=bytearray(b[bs:bs+hs]);crc=struct.unpack_from('<I',h,16)[0];h[16:20]=bytes(4)
        if zlib.crc32(h)&0xffffffff!=crc:continue
        if struct.unpack_from('<Q',h,24)[0]!=1:continue
        lba,count,size,crc_entries=struct.unpack_from('<QIII',h,72)
        assert 0<count<=4096 and 128<=size<=1024
        entries=b[lba*bs:lba*bs+count*size]
        assert len(entries)==count*size,'Incomplete GPT partition table'
        assert zlib.crc32(entries)&0xffffffff==crc_entries,'GPT partition table CRC mismatch'
        actual={}
        for i in range(count):
            e=entries[i*size:(i+1)*size]
            if e[:16]==bytes(16):continue
            first,last=struct.unpack_from('<QQ',e,32)
            name=e[56:128].decode('utf-16le').split('\0',1)[0]
            actual[name]={'offset':first*bs,'size':(last-first+1)*bs}
        for name,want in expected.items():
            assert name in actual,f'Missing partition: {name}'
            assert actual[name]==want,f'Partition mismatch: {name}: {actual[name]} != {want}'
        matches.append(bs)
    assert len(matches)==1,'No unambiguous valid GPT with the required C30 layout was found'
    return matches[0]
if __name__=='__main__':
    try:
        path=Path(sys.argv[1]) if len(sys.argv)>1 else root/'backup/gpt.bin'
        expected=json.loads((root/'tools/expected_layout.json').read_text())
        bs=check(path,expected)
        print(f'PASS: GPT CRC and {len(expected)} required partition offsets/sizes match. Sector size: {bs}.')
    except Exception as e:
        print('STOP: '+str(e));sys.exit(1)
