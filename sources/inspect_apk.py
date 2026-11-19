from pathlib import Path
import struct, zipfile, re, json, sys

def stringpool(b, base=0):
    typ,hs,size=struct.unpack_from('<HHI',b,base)
    assert typ==1
    n,styles,flags,start,style_start=struct.unpack_from('<5I',b,base+8)
    offsets=struct.unpack_from('<'+'I'*n,b,base+hs)
    out=[]
    def length(p,utf8):
        if utf8:
            x=b[p];p+=1
            if x&128:x=((x&127)<<8)|b[p];p+=1
        else:
            x=struct.unpack_from('<H',b,p)[0];p+=2
            if x&32768:x=((x&32767)<<16)|struct.unpack_from('<H',b,p)[0];p+=2
        return x,p
    for off in offsets:
        p=base+start+off
        if flags&256:
            _,p=length(p,True);l,p=length(p,True)
            out.append(b[p:p+l].decode('utf-8',errors='replace'))
        else:
            l,p=length(p,False)
            out.append(b[p:p+2*l].decode('utf-16le',errors='replace'))
    return out

def xml(b):
    strings=[];lines=[];pos=struct.unpack_from('<H',b,2)[0];depth=0
    def st(i): return strings[i] if i!=0xffffffff else ''
    while pos+8<=len(b):
        typ,hs,size=struct.unpack_from('<HHI',b,pos)
        if not size:break
        if typ==1:strings=stringpool(b,pos)
        if typ==0x102:
            ns,name,astart,asz,nattrs=struct.unpack_from('<IIHHH',b,pos+16)
            attrs=[]
            for a in range(nattrs):
                p=pos+16+astart+a*asz
                ans,aname,raw=struct.unpack_from('<III',b,p)
                vsize,res0,vt,vd=struct.unpack_from('<HBBI',b,p+12)
                value=st(raw) if raw!=0xffffffff else st(vd) if vt==3 else f'@0x{vd:08x}' if vt==1 else str(vd)
                attrs.append(st(aname)+'='+json.dumps(value,ensure_ascii=False))
            lines.append('  '*depth+'<'+st(name)+' '+' '.join(attrs)+'>');depth+=1
        if typ==0x103:
            depth-=1
            lines.append('  '*depth+'</'+st(struct.unpack_from('<I',b,pos+20)[0])+'>')
        pos+=size
    return '\n'.join(lines),strings

def dexstrings(b):
    if not b.startswith(b'dex\n'):return []
    n,off=struct.unpack_from('<II',b,56)
    out=[]
    for i in range(n):
        p=struct.unpack_from('<I',b,off+i*4)[0]
        while b[p]&128:p+=1
        p+=1;end=b.index(0,p)
        out.append(b[p:end].decode('utf-8',errors='replace'))
    return out

if __name__=='__main__':
    p=Path(sys.argv[1]);z=zipfile.ZipFile(p)
    manifest,strings=xml(z.read('AndroidManifest.xml'))
    out=Path('work/apk-analysis');out.mkdir(exist_ok=True)
    (out/(p.stem+'-manifest.txt')).write_text(manifest,encoding='utf-8')
    print(manifest[:14000])
    if 'resources.arsc' in z.namelist():
        b=z.read('resources.arsc');strings+=stringpool(b,struct.unpack_from('<H',b,2)[0])
    for n in z.namelist():
        if n.endswith('.dex'):strings+=dexstrings(z.read(n))
    (out/(p.stem+'-strings.txt')).write_text('\n'.join(strings),encoding='utf-8')
    print('\nMATCHED STRINGS\n'+'\n'.join(s for s in strings if re.search('皆成|管控|fundot|jiecheng|17jc|DeviceAdmin|DeviceOwner|HOME|LAUNCHER',s,re.I))[:18000])
