from pathlib import Path
import sys,time
root=Path(__file__).resolve().parent.parent
mode=sys.argv[1]
assert mode in ['layout','readback']
folder=root/('backup' if mode=='layout' else 'readback')
folder.mkdir(exist_ok=True)
names=['gpt.bin','gpt_backup.bin'] if mode=='layout' else ['super.img','vbmeta.img']
history=folder/'history'/str(time.time_ns())
for name in names:
    source=folder/name
    assert source.resolve().is_relative_to(root)
    if source.exists():
        history.mkdir(parents=True,exist_ok=True)
        target=history/name
        assert target.resolve().is_relative_to(root)
        source.rename(target)
print('Ready for fresh read: '+mode)
