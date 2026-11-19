from pathlib import Path
import shutil,subprocess,os,re,struct,json,hashlib,sys
sys.stdout.reconfigure(encoding='utf-8',errors='replace')
base=Path.cwd();mod=Path('work/modified');mod.mkdir(exist_ok=True)
image=mod/'system.img'
shutil.copyfile('work/logical/system.img',image)
original=Path('work/system-files/system')
libraries=(original/'etc/public.libraries.txt').read_text(encoding='utf-8')
remove_names={'libp4bu.so','libsandhook.so','libsandhook-native.so'}
(mod/'public.libraries.txt').write_text('\n'.join(s for s in libraries.splitlines() if s.strip() not in remove_names)+'\n',encoding='utf-8')
permissions=(original/'etc/permissions/privapp-permissions-mediatek.xml').read_text(encoding='utf-8')
permissions,count=re.subn(r'\s*<privapp-permissions package="com\.fundot\.p4bu">.*?</privapp-permissions>','',permissions,flags=re.S)
assert count==1
(mod/'privapp-permissions-mediatek.xml').write_text(permissions,encoding='utf-8')
(mod/'system_file_label.bin').write_bytes(b'u:object_r:system_file:s0\0')
txt=Path('work/system-listing.txt').read_text(encoding='utf-8-sig')
entries=[]
for block in re.split(r'\n\s*\n',txt):
    entry=dict(line.split(' = ',1) for line in block.splitlines() if ' = ' in line)
    p=entry.get('Path','').replace('\\','/')
    if p.startswith('system/priv-app/ROM_523031602_GENERAL_DET/'):
        entries.append((p,entry.get('Folder')=='+'))
commands=[];removed=[]
for p,isdir in sorted(entries,key=lambda x:(x[1],-x[0].count('/'))):
    commands.append(('rmdir ' if isdir else 'rm ')+'/'+p);removed.append('/'+p)
for abi in ['lib','lib64']:
    for name in sorted(remove_names):
        p=f'/system/{abi}/{name}';commands.append('rm '+p);removed.append(p)
replacements=[('work/clean_launcher/build/C30CleanLauncher.apk','/system/priv-app/ROM_523031602_GENERAL_DET/ROM_523031602_GENERAL_DET.apk'),
 ('work/modified/public.libraries.txt','/system/etc/public.libraries.txt'),
 ('work/modified/privapp-permissions-mediatek.xml','/system/etc/permissions/privapp-permissions-mediatek.xml')]
for src,dst in replacements:
    if dst.startswith('/system/etc/'):commands.append('rm '+dst)
    parent,name=dst.rsplit('/',1)
    commands.append('cd '+parent)
    commands.append(f'write {src} {name}')
    commands.append('cd /')
    commands.append(f'set_inode_field {dst} mode 0100644')
    commands.append(f'set_inode_field {dst} uid 0')
    commands.append(f'set_inode_field {dst} gid 0')
    commands.append(f'ea_set -f work/modified/system_file_label.bin {dst} security.selinux')
script=mod/'debugfs.commands';script.write_text('\n'.join(commands)+'\n',encoding='utf-8',newline='\n')
env=os.environ.copy();env['PATH']=str((base/'work/tools/cygwin/usr/bin'))+os.pathsep+env['PATH']
debugfs=base/'work/tools/cygwin/usr/sbin/debugfs.exe'
r=subprocess.run([str(debugfs),'-w','-f',str(script),str(image)],env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
(mod/'debugfs.log').write_bytes(r.stdout);print(r.stdout.decode('utf-8',errors='replace'))
assert r.returncode==0
for bad in ['not found','File exists','Could not','Usage:','not a directory','Filesystem not open']:
    assert bad not in r.stdout.decode('utf-8',errors='replace'),bad
e2fsck=base/'work/tools/cygwin/usr/sbin/e2fsck.exe'
r=subprocess.run([str(e2fsck),'-f','-n',str(image)],env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
(mod/'e2fsck-before-zero.log').write_bytes(r.stdout);print(r.stdout.decode())
assert r.returncode==0
# Clear only blocks marked free in this filesystem's allocation bitmaps. This
# removes the old APK and native library bytes from unallocated space as well.
with image.open('r+b') as f:
    f.seek(1024);s=f.read(1024)
    n=struct.unpack_from('<I',s,4)[0];bs=1024<<struct.unpack_from('<I',s,24)[0]
    first=struct.unpack_from('<I',s,20)[0];bpg=struct.unpack_from('<I',s,32)[0]
    incompat=struct.unpack_from('<I',s,96)[0]
    assert incompat==0x42 and bs==4096 and first==0
    groups=(n-first+bpg-1)//bpg
    f.seek((first+1)*bs);gd=f.read(groups*32)
    free=[]
    for g in range(groups):
        bitmap=struct.unpack_from('<I',gd,g*32)[0]
        assert not struct.unpack_from('<H',gd,g*32+18)[0]&2
        f.seek(bitmap*bs);bits=f.read(bs)
        for j in range(min(bpg,n-first-g*bpg)):
            if not bits[j//8]&(1<<(j%8)):free.append(first+g*bpg+j)
    assert len(free)==struct.unpack_from('<I',s,12)[0],(len(free),struct.unpack_from('<I',s,12)[0])
    for block in free:f.seek(block*bs);f.write(bytes(bs))
print('ZEROED_FREE_BLOCKS',len(free))
r=subprocess.run([str(e2fsck),'-f','-n',str(image)],env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
(mod/'e2fsck-final.log').write_bytes(r.stdout);print(r.stdout.decode());assert r.returncode==0
# Keep every LP metadata byte, alignment, and unmodified logical partition.
super_out=mod/'super.img';shutil.copyfile('work/original_extracted/GeekFlashTool_Readback_20261024222507755/super.img',super_out)
assert image.stat().st_size==1339117568
with super_out.open('r+b') as dest,image.open('rb') as src:
    dest.seek(617611264);shutil.copyfileobj(src,dest,8*1024*1024)
assert super_out.stat().st_size==3758096384
vb=bytearray(Path('work/original_extracted/GeekFlashTool_Readback_20261024222507755/vbmeta.img').read_bytes())
assert vb[:4]==b'AVB0' and struct.unpack_from('>I',vb,120)[0]==0
struct.pack_into('>I',vb,120,3)
(mod/'vbmeta.img').write_bytes(vb)
manifest={'strategy':'replace management implementation with an offline launcher and no-op framework compatibility endpoints; original framework jars are unchanged','removed':removed,'replacements':[dst for _,dst in replacements],'zeroed_free_blocks':len(free),'vbmeta_flags':3,'system_offset_in_super':617611264,'hardware_tested':False}
(mod/'change-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print('BUILT',super_out)
