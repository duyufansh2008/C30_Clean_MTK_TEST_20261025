"""Checks run inside the connected DA session, before a C30 command executes."""
from pathlib import Path
import hashlib
import json
import struct

from check_layout import check_bytes


def read_gpt(mtk):
    def read(length):
        data = mtk.daloader.readflash(addr=0, length=length, filename='', parttype='user', display=False)
        if not isinstance(data, (bytes, bytearray)) or len(data) != length:
            raise RuntimeError('Could not read the current device GPT')
        return data

    header = read(8192)
    sectors = [bs for bs in (512, 4096) if header[bs:bs + 8] == b'EFI PART']
    if len(sectors) != 1:
        raise ValueError('Current device has no unambiguous primary GPT')
    bs = sectors[0]
    lba, count, size = struct.unpack_from('<QII', header, bs + 72)
    if not (lba >= 2 and 0 < count <= 4096 and 128 <= size <= 1024):
        raise ValueError('Invalid live GPT dimensions')
    length = max(8192, ((lba * bs + count * size + bs - 1) // bs) * bs)
    if length > 8 * 1024 * 1024:
        raise ValueError('Live GPT exceeds the supported size')
    return read(length)


def identity(mtk):
    address = mtk.config.chipconfig.meid_addr
    if address is None:
        raise RuntimeError('No supported live device identifier; refusing to write or erase')
    # Read through this DA connection. Cached .state identifiers cannot bind a device.
    meid = mtk.daloader.peek(address, 16)
    if not isinstance(meid, (bytes, bytearray)) or len(meid) != 16 or bytes(meid) in (bytes(16), b'\xff' * 16):
        raise RuntimeError('Could not read a live device identifier; refusing to write or erase')
    return hashlib.sha256(meid).hexdigest()


def guard_command(mtk, command, args, package_root, confirm=input):
    package_root = Path(package_root)
    if command not in ('gpt', 'r', 'w', 'e'):
        return False
    if getattr(args, 'parttype', None) not in (None, 'user') or getattr(args, 'gpt_file', None):
        raise ValueError('C30 checks require the live user-area GPT without overrides')
    expected = json.loads((package_root / 'tools/expected_layout.json').read_text())
    data = read_gpt(mtk)
    sector_size = check_bytes(data, expected)
    if sector_size != mtk.config.pagesize:
        raise ValueError('DA sector size does not match the live GPT')
    binding = {'device_sha256': identity(mtk), 'gpt_sha256': hashlib.sha256(data).hexdigest()}
    backup = package_root / 'backup'
    device_file = backup / 'device.json'
    if command == 'gpt':
        if Path(args.directory).resolve() != backup.resolve():
            raise ValueError('C30 layout must be read into the package backup directory')
        backup.mkdir(exist_ok=True)
        # Invalidate the previous enrollment before replacing either file.
        device_file.unlink(missing_ok=True)
        (backup / 'gpt.bin').write_bytes(data)
        temporary = backup / 'device.json.tmp'
        temporary.write_text(json.dumps(binding, indent=2), encoding='utf-8')
        temporary.replace(device_file)
        print('PASS: live GPT checked; device fingerprint ' + binding['device_sha256'][:12])
        return True
    if not device_file.is_file() or json.loads(device_file.read_text(encoding='utf-8')) != binding:
        raise ValueError('Device or GPT differs from 02_Read_Layout; reconnect the original device')
    print('PASS: current device and GPT match enrollment ' + binding['device_sha256'][:12])
    if command == 'w':
        if args.partitionname != 'super,vbmeta':
            raise ValueError('C30 writes are limited to super,vbmeta')
        files = [Path(name).resolve() for name in args.filename.split(',')]
        allowed = [[(package_root / folder / name).resolve() for name in ('super.img', 'vbmeta.img')]
                   for folder in ('images', 'rollback')]
        if files not in allowed:
            raise ValueError('C30 writes require the packaged clean or rollback images')
    if command == 'e':
        if args.partitionname != 'userdata,metadata,md_udc,cache':
            raise ValueError('C30 erases are limited to userdata,metadata,md_udc,cache')
        phrase = 'ERASE ' + binding['device_sha256'][:12]
        print('WARNING: userdata, metadata, md_udc and cache will be erased. Personal data cannot be recovered.')
        if confirm('Type ' + phrase + ' to continue: ').strip() != phrase:
            raise RuntimeError('Erase cancelled; no partitions were erased')
    return False
