"""Offline regression tests for Lesson 30; no API calls."""
import tempfile
import unittest
from pathlib import Path
from agent_cache_hardening import FileAwareToolCallOptimizer


class CacheTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'a.py').write_text('x = 1\n', encoding='utf-8')
        self.opt = FileAwareToolCallOptimizer(self.root)

    def record(self, tool='trace_python_calls', args=None, result=None):
        args = args or {'filename': 'a.py'}
        result = result or {'status': 'OK', 'calls': [], 'truncated': False}
        self.opt.record(tool, args, result)
        return args, result

    def test_unchanged_file_reused(self):
        args, result = self.record()
        self.assertEqual(self.opt.evaluate('trace_python_calls', args), result)

    def test_changed_same_size_file_invalidates(self):
        args, _ = self.record()
        (self.root / 'a.py').write_text('x = 2\n', encoding='utf-8')
        self.assertIsNone(self.opt.evaluate('trace_python_calls', args))

    def test_file_deleted_invalidates(self):
        args, _ = self.record()
        (self.root / 'a.py').unlink()
        self.assertIsNone(self.opt.evaluate('trace_python_calls', args))

    def test_project_file_added_invalidates(self):
        args, result = self.record('trace_local_imports', {}, {'status': 'OK', 'dependencies': [], 'truncated': False})
        self.assertEqual(self.opt.evaluate('trace_local_imports', args), result)
        (self.root / 'b.py').write_text('import a\n', encoding='utf-8')
        self.assertIsNone(self.opt.evaluate('trace_local_imports', args))

    def test_project_file_changed_invalidates(self):
        args, _ = self.record('find_python_symbols', {'query': 'x'}, {'status': 'OK', 'matches': [], 'truncated': False})
        (self.root / 'a.py').write_text('y = 1\n', encoding='utf-8')
        self.assertIsNone(self.opt.evaluate('find_python_symbols', args))

    def test_failed_not_cached(self):
        args, _ = self.record(result={'status': 'BLOCKED', 'truncated': False})
        self.assertIsNone(self.opt.evaluate('trace_python_calls', args))

    def test_truncated_not_cached(self):
        args, _ = self.record(result={'status': 'OK', 'truncated': True})
        self.assertIsNone(self.opt.evaluate('trace_python_calls', args))

    def test_missing_truncation_not_cached(self):
        args, _ = self.record(result={'status': 'OK'})
        self.assertIsNone(self.opt.evaluate('trace_python_calls', args))

    def test_read_file_not_cached(self):
        self.opt.record('read_file', {'filename': 'a.py'}, 'x = 1')
        self.assertIsNone(self.opt.evaluate('read_file', {'filename': 'a.py'}))

    def test_approval_sensitive_not_cached(self):
        self.opt.record('propose_edit', {'filename': 'a.py'}, {'status': 'APPLIED'})
        self.assertIsNone(self.opt.evaluate('propose_edit', {'filename': 'a.py'}))

    def test_directory_argument_rejected(self):
        result = self.opt.evaluate('trace_python_calls', {'filename': '.'})
        self.assertEqual(result['status'], 'BLOCKED')

    def test_reset_invalidates(self):
        args, _ = self.record()
        self.opt.reset()
        self.assertIsNone(self.opt.evaluate('trace_python_calls', args))

    def test_oversized_file_not_cached(self):
        (self.root / 'a.py').write_text('a' * 100001, encoding='utf-8')
        args, _ = self.record()
        self.assertIsNone(self.opt.evaluate('trace_python_calls', args))


if __name__ == '__main__':
    unittest.main()
