from pathlib import Path
import subprocess,os,zipfile,sys,hashlib
sys.stdout.reconfigure(encoding='utf-8',errors='replace')
root=Path('work/clean_launcher').resolve();build=root/'build';build.mkdir(exist_ok=True)
sdk=Path('work/tools/android-build/android-11').resolve()
android=Path('work/tools/android-platform/android-11/android.jar').resolve()
jdk=Path('C:/Program Files/Java/jdk1.8.0_341/bin')
env=os.environ.copy();env['JAVA_HOME']=str(jdk.parent)
def run(args):
    print('RUN',args[0],flush=True)
    subprocess.run([str(a) for a in args],check=True,env=env,cwd=root)
run([sdk/'aapt2.exe','link','-o',build/'base.apk','--manifest',root/'AndroidManifest.xml','-I',android])
classes=build/'classes';classes.mkdir(exist_ok=True)
sources=list((root/'src').rglob('*.java'))
run([jdk/'javac.exe','-encoding','UTF-8','-source','8','-target','8','-bootclasspath',str(android)+';'+str(sdk/'core-lambda-stubs.jar'),'-d',classes]+sources)
dex=build/'dex';dex.mkdir(exist_ok=True)
run([jdk/'java.exe','-cp',sdk/'lib/d8.jar','com.android.tools.r8.D8','--release','--min-api','26','--lib',android,'--output',dex]+list(classes.rglob('*.class')))
with zipfile.ZipFile(build/'base.apk','a',compression=zipfile.ZIP_STORED) as z:z.write(dex/'classes.dex','classes.dex')
run([sdk/'zipalign.exe','-f','4',build/'base.apk',build/'aligned.apk'])
keystore=root/'c30-local.keystore'
if not keystore.exists():
    run([jdk/'keytool.exe','-genkeypair','-keystore',keystore,'-storepass','c30-local-build','-keypass','c30-local-build','-alias','c30','-keyalg','RSA','-keysize','2048','-validity','10000','-dname','CN=C30 Local Clean Build,OU=Personal Firmware,O=Local,C=CN','-noprompt'])
apk=build/'C30CleanLauncher.apk'
run([jdk/'java.exe','-jar',sdk/'lib/apksigner.jar','sign','--ks',keystore,'--ks-key-alias','c30','--ks-pass','pass:c30-local-build','--key-pass','pass:c30-local-build','--out',apk,build/'aligned.apk'])
run([jdk/'java.exe','-jar',sdk/'lib/apksigner.jar','verify','--verbose','--print-certs',apk])
print('OUTPUT',apk,apk.stat().st_size,hashlib.sha256(apk.read_bytes()).hexdigest())
