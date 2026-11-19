"""Build the launcher from this checkout with Android SDK 30.0.3 and JDK 8+."""
from pathlib import Path
import argparse
import hashlib
import os
import shutil
import subprocess
import tempfile
import zipfile
import xml.etree.ElementTree as ET

SOURCE = Path(__file__).resolve().parent / 'launcher'


def build(sdk, java_home, output, test=False):
    sdk = Path(sdk).resolve()
    android = sdk / 'platforms/android-30/android.jar'
    tools = sdk / 'build-tools/30.0.3'
    suffix = '.exe' if os.name == 'nt' else ''
    java_bin = Path(java_home).resolve() / 'bin' if java_home else Path(shutil.which('java') or '').resolve().parent
    java = java_bin / ('java' + suffix)
    javac = java_bin / ('javac' + suffix)
    aapt2 = tools / ('aapt2' + suffix)
    zipalign = tools / ('zipalign' + suffix)
    required = [android, java, javac, aapt2, zipalign, tools / 'lib/d8.jar', tools / 'lib/apksigner.jar', tools / 'core-lambda-stubs.jar', SOURCE / 'c30-local.keystore']
    for path in required:
        if not path.is_file():
            raise FileNotFoundError('Missing build input: ' + str(path))
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='c30-launcher-') as temporary:
        work = Path(temporary)
        classes = work / 'classes'
        dex = work / 'dex'
        classes.mkdir()
        dex.mkdir()

        def run(args):
            subprocess.run([str(arg) for arg in args], check=True, cwd=SOURCE)

        base = work / 'base.apk'
        manifest = SOURCE / 'AndroidManifest.xml'
        sources = sorted(SOURCE.rglob('*.java'))
        if test:
            sources.append(SOURCE.parents[1] / 'tests/android/LauncherChecks.java')
            document = ET.parse(manifest)
            ns = 'http://schemas.android.com/apk/res/android'
            ET.register_namespace('android', ns)
            ET.SubElement(document.getroot(), 'instrumentation', {f'{{{ns}}}name': 'com.fundot.p4bu.LauncherChecks', f'{{{ns}}}targetPackage': 'com.fundot.p4bu'})
            manifest = work / 'AndroidManifest.xml'
            document.write(manifest, encoding='utf-8')
        run([aapt2, 'link', '-o', base, '--manifest', manifest, '-I', android])
        run([javac, '-encoding', 'UTF-8', '-source', '8', '-target', '8', '-bootclasspath', os.pathsep.join(map(str, [android, tools / 'core-lambda-stubs.jar'])), '-d', classes, *sources])
        run([java, '-cp', tools / 'lib/d8.jar', 'com.android.tools.r8.D8', '--release', '--min-api', '26', '--lib', android, '--output', dex, *sorted(classes.rglob('*.class'))])
        with zipfile.ZipFile(base, 'a', compression=zipfile.ZIP_STORED) as archive:
            archive.write(dex / 'classes.dex', 'classes.dex')
        aligned = work / 'aligned.apk'
        signed = work / 'signed.apk'
        run([zipalign, '-f', '4', base, aligned])
        # This is the repository's public development key, not a private release key.
        run([java, '-jar', tools / 'lib/apksigner.jar', 'sign', '--ks', SOURCE / 'c30-local.keystore', '--ks-key-alias', 'c30', '--ks-pass', 'pass:c30-local-build', '--key-pass', 'pass:c30-local-build', '--out', signed, aligned])
        run([java, '-jar', tools / 'lib/apksigner.jar', 'verify', '--verbose', signed])
        shutil.copyfile(signed, output)
    print('OUTPUT', output, output.stat().st_size, hashlib.sha256(output.read_bytes()).hexdigest())
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sdk', default=os.environ.get('ANDROID_SDK_ROOT') or os.environ.get('ANDROID_HOME'))
    parser.add_argument('--java-home', default=os.environ.get('JAVA_HOME'))
    parser.add_argument('--output', type=Path, default=SOURCE.parent / 'build/C30CleanLauncher.apk')
    parser.add_argument('--test', action='store_true', help='Include emulator-only launcher instrumentation; never use this APK in firmware')
    args = parser.parse_args()
    if not args.sdk:
        parser.error('Set ANDROID_SDK_ROOT or pass --sdk (platform android-30, build-tools 30.0.3)')
    build(args.sdk, args.java_home, args.output, args.test)
