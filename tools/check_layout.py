from pathlib import Path
import json
import struct
import sys
import zlib

root = Path(__file__).resolve().parent.parent


def check_bytes(data, expected):
    matches = []
    for bs in (512, 4096):
        if data[bs:bs + 8] != b'EFI PART':
            continue
        if len(data) < bs + 92:
            raise ValueError('Incomplete GPT header')
        hs = struct.unpack_from('<I', data, bs + 12)[0]
        if not 92 <= hs <= bs or len(data) < bs + hs:
            raise ValueError('Invalid GPT header size')
        header = bytearray(data[bs:bs + hs])
        crc = struct.unpack_from('<I', header, 16)[0]
        header[16:20] = bytes(4)
        if zlib.crc32(header) & 0xffffffff != crc:
            raise ValueError('GPT header CRC mismatch')
        if struct.unpack_from('<Q', header, 24)[0] != 1:
            raise ValueError('Expected primary GPT at LBA 1')
        lba, count, size, entries_crc = struct.unpack_from('<QIII', header, 72)
        if not (lba >= 2 and 0 < count <= 4096 and 128 <= size <= 1024 and size % 8 == 0):
            raise ValueError('Invalid GPT partition table dimensions')
        entries = data[lba * bs:lba * bs + count * size]
        if len(entries) != count * size:
            raise ValueError('Incomplete GPT partition table')
        if zlib.crc32(entries) & 0xffffffff != entries_crc:
            raise ValueError('GPT partition table CRC mismatch')
        actual = {}
        for i in range(count):
            entry = entries[i * size:(i + 1) * size]
            if entry[:16] == bytes(16):
                continue
            first, last = struct.unpack_from('<QQ', entry, 32)
            name = entry[56:128].decode('utf-16le').split('\0', 1)[0]
            if first > last or not name or name in actual:
                raise ValueError('Invalid or duplicate GPT partition: ' + name)
            actual[name] = {'offset': first * bs, 'size': (last - first + 1) * bs}
        for name, want in expected.items():
            if name not in actual:
                raise ValueError('Missing partition: ' + name)
            if actual[name] != want:
                raise ValueError(f'Partition mismatch: {name}: {actual[name]} != {want}')
        matches.append(bs)
    if len(matches) != 1:
        raise ValueError('No unambiguous valid GPT with the required C30 layout was found')
    return matches[0]


def check(path, expected):
    return check_bytes(path.read_bytes(), expected)


if __name__ == '__main__':
    try:
        path = Path(sys.argv[1]) if len(sys.argv) > 1 else root / 'backup/gpt.bin'
        expected = json.loads((root / 'tools/expected_layout.json').read_text())
        bs = check(path, expected)
        print(f'PASS: GPT CRC and {len(expected)} required partition offsets/sizes match. Sector size: {bs}.')
    except Exception as error:
        print('STOP: ' + str(error))
        sys.exit(1)
