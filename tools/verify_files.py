from pathlib import Path
import json,hashlib,sys
root=Path(__file__).resolve().parent.parent
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
try:
    if len(sys.argv)>1 and sys.argv[1]=='--readback':
        folder='rollback' if len(sys.argv)>2 and sys.argv[2]=='original' else 'images'
        for name in ['super.img','vbmeta.img']:
            actual=root/'readback'/name;target=root/folder/name
            assert actual.stat().st_size==target.stat().st_size,f'{name}: size mismatch'
            assert digest(actual)==digest(target),f'{name}: SHA256 mismatch'
            print('PASS readback: '+name)
    else:
        manifest=json.loads((root/'SHA256SUMS.json').read_text(encoding='utf-8'))
        for name,expected in manifest.items():
            assert digest(root/name)==expected,'Hash mismatch: '+name
        print(f'PASS: {len(manifest)} packaged files verified by SHA256.')
except Exception as e:
    print('STOP: '+str(e));sys.exit(1)
