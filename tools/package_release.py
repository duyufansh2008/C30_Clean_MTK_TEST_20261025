"""Package verified files only; missing firmware must never produce a release ZIP."""
from pathlib import Path
import argparse
import json
import os
import tempfile
import zipfile

from verify_files import root, verify


def package(output, package_root=root):
    verify(package_root)
    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError('Refusing to overwrite an existing release: ' + str(output))
    manifest = json.loads((package_root / 'SHA256SUMS.json').read_text(encoding='utf-8'))
    with tempfile.NamedTemporaryFile(prefix='c30-release-', suffix='.tmp', dir=output.parent, delete=False) as stream:
        temporary = Path(stream.name)
    try:
        with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED, allowZip64=True) as archive:
            for name in [*manifest, 'SHA256SUMS.json']:
                archive.write(package_root / name, name)
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    print('PACKAGED:', package(parser.parse_args().output))
