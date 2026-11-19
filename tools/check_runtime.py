import struct
import sys


def check(version=sys.version_info, pointer_size=struct.calcsize('P')):
    if version < (3, 11):
        raise RuntimeError('64-bit Python 3.11 or newer is required')
    if pointer_size != 8:
        raise RuntimeError('64-bit Python is required by the bundled native dependencies')


if __name__ == '__main__':
    try:
        check()
    except RuntimeError as error:
        print('STOP: ' + str(error))
        sys.exit(1)
