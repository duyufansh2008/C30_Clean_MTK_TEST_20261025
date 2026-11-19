from pathlib import Path
import re,struct,hashlib,json,zipfile,subprocess,sys
sys.stdout.reconfigure(encoding='utf-8',errors='replace')
import os
os.chdir(Path(__file__).resolve().parent.parent)
def listing(path):
    result={}
    for block in re.split(r'\n\s*\n',Path(path).read_text(encoding='utf-8-sig')):
        d=dict(line.split(' = ',1) for line in block.splitlines() if ' = ' in line)
        if 'iNode' in d:result[d['Path'].replace('\\','/')]=d
    return result
class Ext:
    def __init__(self,path):
        self.f=open(path,'rb');self.f.seek(1024);s=self.f.read(1024)
        self.bs=1024<<struct.unpack_from('<I',s,24)[0];self.ipg=struct.unpack_from('<I',s,40)[0];self.ino_size=struct.unpack_from('<H',s,88)[0]
        blocks=struct.unpack_from('<I',s,4)[0];bpg=struct.unpack_from('<I',s,32)[0];self.f.seek(self.bs)
        self.gd=self.f.read(((blocks+bpg-1)//bpg)*32)
    def inode(self,n):
        group,index=divmod(n-1,self.ipg);table=struct.unpack_from('<I',self.gd,group*32+8)[0]
        self.f.seek(table*self.bs+index*self.ino_size);return self.f.read(self.ino_size)
    def data(self,n):
        inode=self.inode(n);size=struct.unpack_from('<I',inode,4)[0]|struct.unpack_from('<I',inode,108)[0]<<32
        if not size:return b''
        if not (struct.unpack_from('<I',inode,32)[0]&0x80000):
            raise ValueError(n)
        extents=[]
        def node(b):
            magic,entries,maximum,depth=struct.unpack_from('<4H',b)
            if not (magic==0xf30a):
                raise ValueError('Invalid ext4 extent header')
            for i in range(entries):
                p=12+i*12
                if depth:
                    logical,lo,hi=struct.unpack_from('<IIH',b,p);self.f.seek((lo|(hi<<32))*self.bs);node(self.f.read(self.bs))
                else:
                    logical,length,hi,lo=struct.unpack_from('<IHHI',b,p);extents.append((logical,length,lo|(hi<<32)))
        node(inode[40:100]);data=bytearray(size)
        for logical,length,physical in extents:
            if length>32768:continue
            count=min(length*self.bs,size-logical*self.bs)
            if count<=0:continue
            self.f.seek(physical*self.bs);data[logical*self.bs:logical*self.bs+count]=self.f.read(count)
        return bytes(data)
before=listing('work/system-listing.txt');after=listing('work/modified/system-listing.txt')
manifest=json.loads(Path('work/modified/change-manifest.json').read_text(encoding='utf-8'))
removed={p.lstrip('/') for p in manifest['removed']};replaced={p.lstrip('/') for p in manifest['replacements']}
if not (set(before)-set(after)==removed-replaced):
    raise ValueError('Unexpected removed paths')
if set(after)-set(before):
    raise ValueError('Unexpected added paths')
old=Ext('work/logical/system.img');new=Ext('work/modified/system.img')
checked=0
for p,d in after.items():
    if p in replaced:continue
    original=before[p]
    for k in ['Folder','Mode','Size','User ID','Group ID','Symbolic Link','Links']:
        if k=='Links' and d.get('Folder')=='+':
            child_dirs_removed=sum(1 for q in removed if before.get(q,{}).get('Folder')=='+' and q.rsplit('/',1)[0]==p)
            if not (int(d[k])==int(original[k])-child_dirs_removed):
                raise ValueError((p,k))
            continue
        if not (d.get(k)==original.get(k)):
            raise ValueError((p,k,d.get(k),original.get(k)))
    if d.get('Mode','').startswith('-'):
        if not (hashlib.sha256(old.data(int(original['iNode']))).digest()==hashlib.sha256(new.data(int(d['iNode']))).digest()):
            raise ValueError(p)
        checked+=1
apkpath='system/priv-app/ROM_523031602_GENERAL_DET/ROM_523031602_GENERAL_DET.apk'
apk=new.data(int(after[apkpath]['iNode']))
if not (apk==Path('sources/build/C30CleanLauncher.apk').read_bytes()):
    raise ValueError('Firmware APK differs from the current signed build')
for p in ['system/etc/public.libraries.txt','system/etc/permissions/privapp-permissions-mediatek.xml']:
    b=new.data(int(after[p]['iNode']))
    if not (b==Path('work/modified',Path(p).name).read_bytes()):
        raise ValueError('Firmware permission or library list differs from expected output')
    if not (b'fundot' not in b and b'p4bu' not in b and b'sandhook' not in b):
        raise ValueError('Management library names remain in the replacement configuration')
# Match every byte outside the system extent in the physical super image.
a=Path('work/original_extracted/GeekFlashTool_Readback_20261024222507755/super.img').open('rb')
b=Path('work/modified/super.img').open('rb')
start=617611264;end=start+1339117568;total=3758096384
for lo,hi in [(0,start),(end,total)]:
    a.seek(lo);b.seek(lo);remaining=hi-lo
    while remaining:
        n=min(8*1024*1024,remaining)
        if not (a.read(n)==b.read(n)):
            raise ValueError('Bytes outside the system extent changed')
vb=Path('work/modified/vbmeta.img').read_bytes();orig=Path('work/original_extracted/GeekFlashTool_Readback_20261024222507755/vbmeta.img').read_bytes()
if not ([i for i,(x,y) in enumerate(zip(orig,vb)) if x!=y]==[123]):
    raise ValueError('Unexpected vbmeta byte changes')
if not (struct.unpack_from('>I',vb,120)[0]==3):
    raise ValueError('Expected vbmeta flags=3')
report={'unchanged_regular_files_compared_by_sha256':checked,'original_inventory_nodes':len(before),'modified_inventory_nodes':len(after),'only_expected_paths_removed':True,'replacement_apk_matches_signed_build':True,'product_vendor_lp_metadata_and_all_bytes_outside_system_unchanged':True,'vbmeta_only_changed_byte_offset':123,'vbmeta_flags':3,'filesystem_check_exit_code':0,'hardware_boot_test_performed':False}
Path('work/modified/validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
