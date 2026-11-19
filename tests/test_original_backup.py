"""Exercise the stock backup checker with a small, synthetic readback directory."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from check_original_backup import ORIGINAL_FILES, SCATTER_NAME


SCATTER = '''- partition_index: SYS1
  partition_name: super
  region: UFS_LU2
  storage: HW_STORAGE_UFS
  physical_start_addr: 0x1000
  linear_start_addr: 0x1000
  partition_size: 8192
'''


class OriginalBackupTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.repo = Path(temporary.name)
        self.backup = self.repo / 'stock readback'
        self.backup.mkdir()
        (self.repo / 'tools').mkdir()
        (self.repo / 'tools/expected_layout.json').write_text(json.dumps({
            'super': {'offset': 4096, 'size': 8192},
        }))
        manifest = {}
        for filename, entry in ORIGINAL_FILES.items():
            data = filename.encode('utf-8')
            (self.backup / filename).write_bytes(data)
            manifest[entry] = hashlib.sha256(data).hexdigest()
        (self.repo / 'SHA256SUMS.json').write_text(json.dumps(manifest))
        for name in ('check_original_backup.py', 'verify_files.py'):
            (self.repo / 'tools' / name).write_bytes((ROOT / 'tools' / name).read_bytes())
        self.scatter = self.backup / SCATTER_NAME
        self.scatter.write_text(SCATTER, encoding='utf-8-sig')

    def run_check(self):
        return subprocess.run(
            [sys.executable, '-O', str(self.repo / 'tools/check_original_backup.py'), str(self.backup)],
            cwd=self.backup, capture_output=True, text=True, timeout=10,
        )

    def test_correct_backup(self):
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('PASS STOCK BACKUP', result.stdout)

    def test_rejects_image_hash_mismatch(self):
        (self.backup / 'super.img').write_bytes(b'wrong image')
        result = self.run_check()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn('SHA256 mismatch: super.img', result.stderr)

    def test_rejects_missing_file(self):
        (self.backup / 'vbmeta.img').unlink()
        result = self.run_check()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn('Missing backup file: vbmeta.img', result.stderr)

    def test_rejects_unsafe_scatter(self):
        cases = {
            'mismatch in super.physical_start_addr': SCATTER.replace('physical_start_addr: 0x1000', 'physical_start_addr: 0x2000'),
            'outside the expected UFS user area': SCATTER.replace('UFS_LU2', 'UFS_LU1'),
            'duplicate partition super': SCATTER + SCATTER.replace('SYS1', 'SYS2'),
        }
        for message, text in cases.items():
            with self.subTest(message=message):
                self.scatter.write_text(text, encoding='utf-8-sig')
                result = self.run_check()
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertIn(message, result.stderr)
