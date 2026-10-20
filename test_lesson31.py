"""Offline regression tests for Lesson 31 project investigation."""
import tempfile
import unittest
from pathlib import Path
from agent_project_investigation import investigate_project


def allowed(root, filename):
    path = (Path(root) / filename).resolve()
    return path.is_relative_to(Path(root).resolve()) and path.suffix == '.py'


class InvestigationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'calculator.py').write_text('def multiply_numbers(a, b):\n    return a*b\n', encoding='utf-8')
        (self.root / 'test_calculator.py').write_text('from calculator import multiply_numbers\ndef test_multiply():\n    assert multiply_numbers(2,3)==6\n', encoding='utf-8')

    def test_finds_symbol(self):
        r = investigate_project(self.root, 'multiply_numbers incorrect result', allowed)
        self.assertEqual(r['status'], 'OK')
        self.assertEqual(r['candidates'][0]['file'], 'calculator.py')

    def test_finds_filename(self):
        r = investigate_project(self.root, 'calculator', allowed)
        self.assertEqual(len(r['candidates']), 2)

    def test_no_query_blocked(self):
        self.assertEqual(investigate_project(self.root, ' ', allowed)['status'], 'BLOCKED')

    def test_no_execution(self):
        (self.root / 'evil.py').write_text('raise RuntimeError("executed")\ndef multiply_numbers(): pass\n', encoding='utf-8')
        self.assertEqual(investigate_project(self.root, 'multiply_numbers', allowed)['status'], 'OK')

    def test_ignored_venv(self):
        d = self.root / '.venv'
        d.mkdir()
        (d / 'secret.py').write_text('def multiply_numbers(): pass\n', encoding='utf-8')
        r = investigate_project(self.root, 'multiply_numbers', allowed)
        self.assertNotIn('.venv/secret.py', [x['file'] for x in r['candidates']])

    def test_symlink_not_followed(self):
        p = self.root / 'alias.py'
        try:
            p.symlink_to(self.root / 'calculator.py')
        except (OSError, NotImplementedError):
            self.skipTest('Symlinks unavailable')
        r = investigate_project(self.root, 'calculator', allowed)
        self.assertNotIn('alias.py', [x['file'] for x in r['candidates']])

    def test_invalid_syntax_skipped(self):
        (self.root / 'bad.py').write_text('def broken(:\n', encoding='utf-8')
        r = investigate_project(self.root, 'calculator', allowed)
        self.assertTrue(r['truncated'])

    def test_relevant_limit(self):
        for i in range(20):
            (self.root / f'feature_{i}.py').write_text('def feature(): pass\n', encoding='utf-8')
        r = investigate_project(self.root, 'feature', allowed)
        self.assertEqual(len(r['candidates']), 12)
        self.assertTrue(r['truncated'])


if __name__ == '__main__':
    unittest.main()
