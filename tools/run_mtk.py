from pathlib import Path
import sys,runpy,os
from check_runtime import check
check()
root=Path(__file__).resolve().parent.parent
source=root/'tools/mtkclient'
sys.path[:0]=[str(root/'tools/python-packages'),str(source)]
os.chdir(root)
os.environ['C30_PACKAGE_ROOT']=str(root)
script=source/'mtk.py'
sys.argv=[str(script),'--preloader',str(root/'tools/device_preloader.bin'),'--loader',str(source/'mtkclient/Loader/MTK_DA_V5.bin')]+sys.argv[1:]
try:
    runpy.run_path(str(script),run_name='__main__')
except Exception as error:
    print('STOP: '+str(error));sys.exit(1)
