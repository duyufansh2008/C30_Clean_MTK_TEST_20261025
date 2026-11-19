from pathlib import Path
import sys,time
root=Path(__file__).resolve().parent.parent
mode=sys.argv[1]
if mode not in ['layout','readback']:
    raise ValueError('Expected layout or readback')
folder=root/('backup' if mode=='layout' else 'readback')
folder.mkdir(exist_ok=True)
names=['device.json','gpt.bin','gpt_backup.bin'] if mode=='layout' else ['super.img','vbmeta.img']
history=folder/'history'/str(time.time_ns())
for name in names:
    source=folder/name
    if not source.resolve().is_relative_to(root):
        raise ValueError('Read path escapes package')
    if source.exists():
        target=history/name
        if not target.resolve().is_relative_to(root):
            raise ValueError('History path escapes package')
        history.mkdir(parents=True,exist_ok=True)
        source.rename(target)
print('Ready for fresh read: '+mode)
