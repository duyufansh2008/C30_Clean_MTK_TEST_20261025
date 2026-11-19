"""Verify a locally extracted C30 stock backup without preparing or writing a device."""
from pathlib import Path
import argparse
import json
import re

from verify_files import digest, root


ORIGINAL_FILES = {
    'super.img': 'rollback/super.img',
    'vbmeta.img': 'rollback/vbmeta.img',
    'preloader_tb8788p1_64_bsp.bin': 'tools/device_preloader.bin',
}
SCATTER_NAME = 'MT6771_Android_scatter.txt'


def check_scatter(scatter_path, expected_layout):
    """Check the GeekFlashTool records for the user-area partitions in expected_layout."""
    text = scatter_path.read_text(encoding='utf-8-sig')
    records = re.split(r'(?m)^[ \t]*-[ \t]+partition_index[ \t]*:', text)[1:]
    partitions = {}
    for record in records:
        fields = {}
        for key, value in re.findall(r'(?m)^[ \t]*([A-Za-z_][\w]*)[ \t]*:[ \t]*([^\n]*)', record):
            if key in fields:
                raise ValueError(f'{SCATTER_NAME}: duplicate field {key}')
            fields[key] = value.strip()
        name = fields.get('partition_name')
        if name not in expected_layout:
            continue
        if name in partitions:
            raise ValueError(f'{SCATTER_NAME}: duplicate partition {name}')
        partitions[name] = fields

    for name, expected in expected_layout.items():
        fields = partitions.get(name)
        if fields is None:
            raise ValueError(f'{SCATTER_NAME}: missing partition {name}')
        if (fields.get('region'), fields.get('storage')) != ('UFS_LU2', 'HW_STORAGE_UFS'):
            raise ValueError(f'{SCATTER_NAME}: {name} is outside the expected UFS user area')
        for field, expected_value in (
            ('linear_start_addr', expected['offset']),
            ('physical_start_addr', expected['offset']),
            ('partition_size', expected['size']),
        ):
            try:
                actual = int(fields.get(field, ''), 0)
            except ValueError as error:
                raise ValueError(f'{SCATTER_NAME}: invalid {name}.{field}') from error
            if actual != expected_value:
                raise ValueError(f'{SCATTER_NAME}: mismatch in {name}.{field}')


def check_backup(directory, package_root=root):
    manifest = json.loads((package_root / 'SHA256SUMS.json').read_text(encoding='utf-8'))
    layout = json.loads((package_root / 'tools/expected_layout.json').read_text(encoding='utf-8'))
    for filename, manifest_entry in ORIGINAL_FILES.items():
        if manifest_entry not in manifest:
            raise ValueError(f'Manifest omits {manifest_entry}')
        if not (directory / filename).is_file():
            raise ValueError(f'Missing backup file: {filename}')
    check_scatter(directory / SCATTER_NAME, layout)
    for filename, manifest_entry in ORIGINAL_FILES.items():
        if digest(directory / filename) != manifest[manifest_entry]:
            raise ValueError(f'SHA256 mismatch: {filename}')
    return len(layout)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path, help='Extracted GeekFlashTool readback directory')
    args = parser.parse_args()
    try:
        count = check_backup(args.directory)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f'STOP: {error}\n')
    print(f'PASS STOCK BACKUP: {len(ORIGINAL_FILES)} files and {count} scatter partitions matched offline.')


if __name__ == '__main__':
    main()
