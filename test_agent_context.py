import tempfile
import unittest
from pathlib import Path
from agent_context import ReadContext

class ContextTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'sample.py').write_text('print(1)')
        self.ctx = ReadContext()
        self.calls = 0
    def reader(self, root, name):
        self.calls += 1
        return (root / name).read_text()
    def allowed(self, root, name):
        return name == 'sample.py'
    def test_first_read(self):
        self.assertEqual(self.ctx.read(self.root, 'sample.py', self.reader, self.allowed), 'print(1)')
    def test_repeat_suppressed(self):
        self.ctx.read(self.root, 'sample.py', self.reader, self.allowed)
        self.assertIn('ALREADY_READ_THIS_TURN', self.ctx.read(self.root, 'sample.py', self.reader, self.allowed))
        self.assertEqual(self.calls, 1)
    def test_modified_content_returned(self):
        self.ctx.read(self.root, 'sample.py', self.reader, self.allowed)
        (self.root / 'sample.py').write_text('print(2)')
        self.assertEqual(self.ctx.read(self.root, 'sample.py', self.reader, self.allowed), 'print(2)')
    def test_invalidate(self):
        self.ctx.read(self.root, 'sample.py', self.reader, self.allowed)
        self.ctx.invalidate()
        self.assertEqual(self.ctx.read(self.root, 'sample.py', self.reader, self.allowed), 'print(1)')
        self.assertEqual(self.calls, 2)
    def test_disallowed_always_uses_reader(self):
        self.assertEqual(self.ctx.read(self.root, 'sample.py', self.reader, lambda *_: False), 'print(1)')
        self.assertEqual(self.ctx.read(self.root, 'sample.py', self.reader, lambda *_: False), 'print(1)')
        self.assertEqual(self.calls, 2)
    def test_missing_file_uses_reader(self):
        self.assertEqual(self.ctx.read(self.root, 'missing.py', lambda *_: 'Error: File does not exist.', lambda *_: True), 'Error: File does not exist.')

if __name__ == '__main__':
    unittest.main()
